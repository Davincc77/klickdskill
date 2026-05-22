/**
 * verify_vectors.mjs — .klickd multi-version cross-impl JS test runner
 *
 * Runs all four suites:
 *   • v2.5 positive  (tests/vectors_v25.json)        — PBKDF2, Web Crypto
 *   • v2.5 negative  (tests/negative_vectors_v25.json)
 *   • v3.0 positive  (tests/vectors_v30.json)        — Argon2id via hash-wasm
 *   • v3.0 negative  (tests/negative_vectors_v30.json)
 *
 * Argon2id is provided by the hash-wasm package (WASM, no native binding needed).
 * Install: npm install hash-wasm
 * If hash-wasm is not installed, v3.0 Argon2id vectors are skipped with a clear message.
 *
 * Error code mapping (mirrors Python load_klickd.py):
 *   KlickdAuthError           → thrown Error containing "KLICKD_E_AUTH"
 *   KlickdVersionError        → thrown Error containing "KLICKD_E_VERSION"
 *   KlickdFormatError         → thrown Error containing "KLICKD_E_FORMAT"
 *   KlickdWeakPassphraseError → thrown Error containing "KLICKD_E_WEAK_PASS"
 *   KlickdKdfError            → thrown Error containing "KLICKD_E_KDF"
 *   decrypt_success           → no throw
 */

import { webcrypto } from 'crypto';
import { readFileSync, existsSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __dir = dirname(fileURLToPath(import.meta.url));
const enc = new TextEncoder();
const dec = new TextDecoder();

// ── hash-wasm optional import ─────────────────────────────────────────────────
let argon2id = null;
try {
  const hw = await import('hash-wasm');
  argon2id = hw.argon2id;
} catch {
  // hash-wasm not installed — v3.0 Argon2id vectors will be skipped
}

// ── Constants ─────────────────────────────────────────────────────────────────
const MIN_PASSPHRASE_LEN      = 8;
const WARN_PASSPHRASE_LEN     = 12;
const GCM_TAG_BYTES           = 16;
const MAX_ENVELOPE_BYTES      = 1 * 1024 * 1024;   // 1 MiB
const MAX_PAYLOAD_BYTES       = 4 * 1024 * 1024;   // 4 MiB
const MAX_AGENT_INSTR_BYTES   = 32 * 1024;          // 32 KiB  (§22 size cap)
const VERSION_RE              = /^\d+\.\d+$/;
const STANDARD_B64_RE         = /^[A-Za-z0-9+/]*={0,2}$/;

// Argon2id parameter floors (§14.1) — Grok Audit 2 P2: aligned with Python decoder
const ARGON2_MIN_M = 65536;  // 64 MiB — was 1024
const ARGON2_MIN_T = 3;      // — was 1
const ARGON2_MIN_P = 1;
// Argon2id parameter ceilings (§14.1) — OOM/DoS guard, matches Python decoder
const ARGON2_MAX_M = 4_194_304;  // 4 GiB
const ARGON2_MAX_T = 999;
const ARGON2_MAX_P = 255;

// PBKDF2 floor (§15.1)
const PBKDF2_MIN_ITERATIONS = 600_000;

// ── Error helpers ─────────────────────────────────────────────────────────────
function KlickdFormatError(msg)         { throw new Error(`KLICKD_E_FORMAT: ${msg}`); }
function KlickdVersionError(msg)        { throw new Error(`KLICKD_E_VERSION: ${msg}`); }
function KlickdAuthError(msg)           { throw new Error(`KLICKD_E_AUTH: ${msg}`); }
function KlickdWeakPassphraseError(msg) { throw new Error(`KLICKD_E_WEAK_PASS: ${msg}`); }
function KlickdKdfError(msg)            { throw new Error(`KLICKD_E_KDF: ${msg}`); }

// ── Strict standard-alphabet base64 decoder ──────────────────────────────────
function b64DecodeStrict(value, fieldName) {
  if (typeof value !== 'string' || !STANDARD_B64_RE.test(value)) {
    KlickdFormatError(`malformed base64 in '${fieldName}'`);
  }
  if (value.length % 4 !== 0) {
    KlickdFormatError(`malformed base64 (bad padding) in '${fieldName}'`);
  }
  return Buffer.from(value, 'base64');
}

// ── JCS canonicalization (RFC 8785, inline — no external dep) ────────────────
// Implements RFC 8785 §3.2.3: sort keys by Unicode code point, no whitespace.
// RFC 8785 §3.2.2.2: strings MUST be NFC-normalised before serialisation.
// This is byte-identical to the Python _jcs_canonicalize() for all .klickd
// AAD field types (strings, booleans, objects, numbers).
// Note: floats with non-zero fractional part diverge from RFC 8785 §3.2.2.3
// but MUST NOT appear in .klickd AAD fields — only strings/bools/ints/objects.
function nfcNormalize(v) {
  // Grok Audit 3 / A1: NFC normalisation per RFC 8785 §3.2.2.2
  if (typeof v === 'string') return v.normalize('NFC');
  if (Array.isArray(v))     return v.map(nfcNormalize);
  if (v !== null && typeof v === 'object') {
    const out = {};
    for (const k of Object.keys(v)) out[k.normalize('NFC')] = nfcNormalize(v[k]);
    return out;
  }
  return v;
}

function jcsCanonicalize(obj) {
  function serializeValue(v) {
    if (v === null) return 'null';
    if (typeof v === 'boolean') return v.toString();
    if (typeof v === 'number') return JSON.stringify(v);
    if (typeof v === 'string') return JSON.stringify(v);  // already NFC via nfcNormalize
    if (Array.isArray(v)) {
      return '[' + v.map(serializeValue).join(',') + ']';
    }
    if (typeof v === 'object') {
      const keys = Object.keys(v).sort();
      return '{' + keys.map(k => JSON.stringify(k) + ':' + serializeValue(v[k])).join(',') + '}';
    }
    throw new Error(`Unsupported JCS type: ${typeof v}`);
  }
  return enc.encode(serializeValue(nfcNormalize(obj)));
}

// ── AAD construction per spec version ────────────────────────────────────────
// v2.x: 4-field object {created_at, domain, encrypted, klickd_version}
//       AAD = Python json.dumps(sort_keys=True, separators) — keys sorted lexicographically
//       (same as JCS for simple string/bool/number types)
// v3.0: 6-field JCS object per §17
//       Algorithm: JCS(envelope minus ciphertext and payload-internal fields)
//       JCS lexicographic order: cipher < created_at < domain < encrypted < kdf < klickd_version
function buildAad(envelope, major) {
  if (major === '2') {
    // v2.x backward-read path: 4-field AAD (klickd_version, encrypted, domain, created_at)
    // JCS of these 4 fields. Lexicographic order: created_at < domain < encrypted < klickd_version
    const fields = {
      created_at:      envelope.created_at,
      domain:          envelope.domain,
      encrypted:       envelope.encrypted,
      klickd_version:  envelope.klickd_version,
    };
    return jcsCanonicalize(fields);
  }
  // v3.0: 6-field JCS AAD per §17
  // Algorithm: apply JCS to the object containing exactly these 6 envelope fields.
  // JCS sorts keys by Unicode code point — implementers MUST use JCS, not hardcoded order.
  const fields = {
    cipher:          envelope.cipher,
    created_at:      envelope.created_at,
    domain:          envelope.domain,
    encrypted:       envelope.encrypted,
    kdf:             envelope.kdf,
    klickd_version:  envelope.klickd_version,
  };
  return jcsCanonicalize(fields);
}

// ── Argon2id key derivation (v3.0) ───────────────────────────────────────────
async function deriveKeyArgon2id(passphrase, saltBuf, m, t, p) {
  if (!argon2id) {
    throw new Error('KLICKD_E_SKIP_ARGON2: hash-wasm not installed. Run: npm install hash-wasm');
  }
  const hashHex = await argon2id({
    password:    passphrase,
    salt:        saltBuf,
    iterations:  t,
    memorySize:  m,          // KiB
    parallelism: p,
    hashLength:  32,
    outputType:  'hex',
  });
  return Buffer.from(hashHex, 'hex');
}

// ── PBKDF2 key derivation (v2.x + v3.0 legacy) ───────────────────────────────
async function deriveKeyPbkdf2(passphrase, saltBuf, iterations) {
  const km = await webcrypto.subtle.importKey(
    'raw', enc.encode(passphrase), { name: 'PBKDF2' }, false, ['deriveKey']
  );
  const key = await webcrypto.subtle.deriveKey(
    { name: 'PBKDF2', salt: saltBuf, iterations, hash: 'SHA-256' },
    km,
    { name: 'AES-GCM', length: 256 },
    true,
    ['decrypt']
  );
  const raw = await webcrypto.subtle.exportKey('raw', key);
  return Buffer.from(raw);
}

// ── Core decode function — handles v2.x and v3.0 ─────────────────────────────
async function decodeKlickdEnvelope(envelope, passphrase) {

  // Step 1: Passphrase validation
  const ppLen = [...passphrase].length;  // Unicode code points
  if (ppLen < MIN_PASSPHRASE_LEN) {
    KlickdWeakPassphraseError(`passphrase too short (${ppLen} < ${MIN_PASSPHRASE_LEN} code points)`);
  }
  if (ppLen < WARN_PASSPHRASE_LEN) {
    process.stderr.write(
      `WARNING: passphrase entropy below recommended threshold ` +
      `(${ppLen} chars < ${WARN_PASSPHRASE_LEN} recommended). ` +
      `Use a passphrase of at least ${WARN_PASSPHRASE_LEN} recommended in production.\n`
    );
  }

  // Step 2: Version check — must be string matching \d+\.\d+
  const versionStr = envelope.klickd_version;
  if (typeof versionStr !== 'string' || !VERSION_RE.test(versionStr)) {
    KlickdFormatError(
      `klickd_version must be a string matching N.N, got ${JSON.stringify(versionStr)}`
    );
  }
  const major = versionStr.split('.')[0];
  if (major !== '2' && major !== '3') {
    KlickdVersionError(`unsupported major version '${major}' in '${versionStr}'`);
  }

  // Step 3: Required envelope fields (common)
  for (const field of ['encrypted', 'domain', 'created_at', 'ciphertext']) {
    if (!(field in envelope)) KlickdFormatError(`missing required field '${field}'`);
  }

  // Step 4: Version-specific field validation
  let saltBuf, ivBuf, kdfName, kdfParams;

  if (major === '2') {
    // v2.x: flat kdf_salt + iv at envelope root
    if (!('kdf_salt' in envelope)) KlickdFormatError("missing required field 'kdf_salt'");
    if (!('iv' in envelope))       KlickdFormatError("missing required field 'iv'");
    saltBuf  = b64DecodeStrict(envelope.kdf_salt, 'kdf_salt');
    ivBuf    = b64DecodeStrict(envelope.iv, 'iv');
    kdfName  = 'pbkdf2-sha256';
    kdfParams = { iterations: 600_000 };
  } else {
    // v3.0: structured kdf + cipher objects
    if (!envelope.kdf)    KlickdFormatError("missing required field 'kdf'");
    if (!envelope.cipher) KlickdFormatError("missing required field 'cipher'");

    // kdf validation — missing or invalid kdf.name is KLICKD_E_KDF (§5 of §19)
    if (typeof envelope.kdf.name !== 'string') {
      KlickdKdfError(`kdf.name must be a string, got ${JSON.stringify(envelope.kdf.name)}`);
    }
    kdfName = envelope.kdf.name;
    if (kdfName !== 'argon2id' && kdfName !== 'pbkdf2-sha256') {
      KlickdKdfError(`unsupported kdf.name '${kdfName}'`);
    }
    if (!envelope.kdf.params) KlickdFormatError("missing required field 'kdf.params'");
    if (!('salt' in envelope.kdf)) KlickdFormatError("missing required field 'kdf.salt'");
    saltBuf = b64DecodeStrict(envelope.kdf.salt, 'kdf.salt');
    if (saltBuf.length < 16) KlickdFormatError("kdf.salt must decode to at least 16 bytes");

    // Argon2id parameter floor validation (§14.1)
    if (kdfName === 'argon2id') {
      const p = envelope.kdf.params;
      if (typeof p.m !== 'number' || p.m < ARGON2_MIN_M)
        KlickdKdfError(`argon2id m=${p.m} below minimum ${ARGON2_MIN_M}`);
      if (typeof p.t !== 'number' || p.t < ARGON2_MIN_T)
        KlickdKdfError(`argon2id t=${p.t} below minimum ${ARGON2_MIN_T}`);
      if (typeof p.p !== 'number' || p.p < ARGON2_MIN_P)
        KlickdKdfError(`argon2id p=${p.p} below minimum ${ARGON2_MIN_P}`);
      if (p.m > ARGON2_MAX_M)
        KlickdKdfError(`argon2id m=${p.m} exceeds maximum ${ARGON2_MAX_M}`);
      if (p.t > ARGON2_MAX_T)
        KlickdKdfError(`argon2id t=${p.t} exceeds maximum ${ARGON2_MAX_T}`);
      if (p.p > ARGON2_MAX_P)
        KlickdKdfError(`argon2id p=${p.p} exceeds maximum ${ARGON2_MAX_P}`);
    }
    // PBKDF2 floor validation (§15.1)
    if (kdfName === 'pbkdf2-sha256') {
      const itr = envelope.kdf.params.iterations;
      if (typeof itr !== 'number' || itr < PBKDF2_MIN_ITERATIONS)
        KlickdKdfError(`pbkdf2 iterations=${itr} below minimum ${PBKDF2_MIN_ITERATIONS}`);
    }
    kdfParams = envelope.kdf.params;

    // cipher validation — canonical = 'AES-256-GCM' (uppercase) per SPEC v3.5 + schema.
    // Accept legacy 'aes-256-gcm' (lowercase) with console deprecation notice.
    const cipherName = envelope.cipher.name;
    if (cipherName === 'aes-256-gcm') {
      console.warn(
        "KLICKD_W_DEPRECATED: cipher.name='aes-256-gcm' (lowercase) is legacy; canonical is 'AES-256-GCM'."
      );
    } else if (cipherName !== 'AES-256-GCM') {
      KlickdFormatError(`cipher.name must be 'AES-256-GCM' (canonical) or 'aes-256-gcm' (legacy), got ${JSON.stringify(cipherName)}`);
    }
    if (!('iv' in envelope.cipher)) KlickdFormatError("missing required field 'cipher.iv'");
    ivBuf = b64DecodeStrict(envelope.cipher.iv, 'cipher.iv');
    if (ivBuf.length !== 12) KlickdFormatError(`cipher.iv must be exactly 12 bytes, got ${ivBuf.length}`);
  }

  // Step 5: Ciphertext decode + minimum length check
  const raw = b64DecodeStrict(envelope.ciphertext, 'ciphertext');
  if (raw.length < GCM_TAG_BYTES) {
    KlickdFormatError(`ciphertext too short (${raw.length} < ${GCM_TAG_BYTES} bytes minimum)`);
  }

  // Step 6: AAD construction per spec version
  // Algorithm: JCS applied to the version-appropriate field subset (§17 for v3.0, v2.5 AAD for v2.x)
  const aad = buildAad(envelope, major);

  // Step 7: Key derivation
  let keyBuf;
  if (kdfName === 'argon2id') {
    const { m, t, p } = kdfParams;
    if (!argon2id) {
      throw new Error('KLICKD_E_SKIP_ARGON2: hash-wasm not installed. Run: npm install hash-wasm');
    }
    keyBuf = await deriveKeyArgon2id(passphrase, saltBuf, m, t, p);
  } else {
    const itr = kdfParams.iterations ?? 600_000;
    keyBuf = await deriveKeyPbkdf2(passphrase, saltBuf, itr);
  }

  // Step 8: AES-256-GCM decrypt
  const cryptoKey = await webcrypto.subtle.importKey(
    'raw', keyBuf, { name: 'AES-GCM' }, false, ['decrypt']
  );

  let plaintext;
  try {
    const ptBuf = await webcrypto.subtle.decrypt(
      { name: 'AES-GCM', iv: ivBuf, additionalData: aad, tagLength: 128 },
      cryptoKey,
      raw
    );
    if (ptBuf.byteLength > MAX_PAYLOAD_BYTES) {
      KlickdFormatError(`payload exceeds 4 MiB limit (${ptBuf.byteLength} bytes)`);
    }
    plaintext = dec.decode(ptBuf);
  } catch (e) {
    if (e.message && e.message.startsWith('KLICKD_E_')) throw e;
    KlickdAuthError('decryption failed — wrong passphrase or tampered file');
  }

  // Step 9: Parse inner JSON
  let payload;
  try { payload = JSON.parse(plaintext); }
  catch { KlickdFormatError('decrypted payload is not valid JSON'); }

  // Step 10: agent_instructions size cap (§22 — 32 KiB)
  // Also checks v2.5-era user_preferences when stored as a plain string.
  if (typeof payload.agent_instructions === 'string') {
    const byteLen = Buffer.byteLength(payload.agent_instructions, 'utf8');
    if (byteLen > MAX_AGENT_INSTR_BYTES) {
      KlickdFormatError(
        `agent_instructions exceeds 32 KiB limit (${byteLen} bytes)`
      );
    }
  }
  // v2.5 backward-compat: user_preferences was sometimes stored as a plain string
  if (typeof payload.user_preferences === 'string') {
    const byteLen = Buffer.byteLength(payload.user_preferences, 'utf8');
    if (byteLen > MAX_AGENT_INSTR_BYTES) {
      KlickdFormatError(
        `user_preferences (string) exceeds 32 KiB limit (${byteLen} bytes)`
      );
    }
  }

  return payload;
}

// ── Expected-behavior classifier ─────────────────────────────────────────────
// Reads expected_behavior string and returns the most specific error code token.
// Precedence: specific codes first (KDF, WEAK_PASS, VERSION, AUTH), then FORMAT.
// A behavior string like "KlickdFormatError — KLICKD_E_KDF" means the thrown error
// is KLICKD_E_KDF (the class is KlickdFormatError but the code is KDF).
function expectedErrorCode(behavior) {
  if (!behavior) return null;
  // Match explicit error codes first (most specific)
  if (behavior.includes('KLICKD_E_KDF'))        return 'KLICKD_E_KDF';
  if (behavior.includes('KLICKD_E_WEAK_PASS'))  return 'KLICKD_E_WEAK_PASS';
  if (behavior.includes('KLICKD_E_VERSION'))     return 'KLICKD_E_VERSION';
  if (behavior.includes('KLICKD_E_AUTH'))        return 'KLICKD_E_AUTH';
  if (behavior.includes('KLICKD_E_FORMAT'))      return 'KLICKD_E_FORMAT';
  if (behavior.includes('KLICKD_E_SCHEMA'))      return 'KLICKD_E_SCHEMA';
  // Fallback: class name only
  if (behavior.includes('KlickdAuthError'))           return 'KLICKD_E_AUTH';
  if (behavior.includes('KlickdVersionError'))        return 'KLICKD_E_VERSION';
  if (behavior.includes('KlickdWeakPassphraseError')) return 'KLICKD_E_WEAK_PASS';
  if (behavior.includes('KlickdKdfError'))            return 'KLICKD_E_KDF';
  if (behavior.includes('KlickdFormatError'))         return 'KLICKD_E_FORMAT';
  if (behavior.includes('decrypt_success'))           return null;
  return null;
}

// ── Suite runner ──────────────────────────────────────────────────────────────
async function runSuite(vectorsPath, label) {
  if (!existsSync(vectorsPath)) {
    console.log(`\n[SKIP] ${label} — file not found: ${vectorsPath}`);
    return { passed: 0, failed: 0, skipped: 0, results: [] };
  }

  const rawBuf = readFileSync(vectorsPath);
  if (rawBuf.length > MAX_ENVELOPE_BYTES * 10) {  // sanity: vector file shouldn't be > 10 MB
    console.log(`\n[SKIP] ${label} — vector file too large`);
    return { passed: 0, failed: 0, skipped: 0, results: [] };
  }
  const data = JSON.parse(rawBuf.toString('utf8'));

  let passed = 0, failed = 0, skipped = 0;
  const results = [];
  const specVer = data.spec_version ?? '?';
  console.log(`\n── ${label} — spec ${specVer} ──────────────────────────`);

  for (const v of data.vectors) {
    const vid      = v.id;
    const behavior = v.expected_behavior ?? '';
    const errCode  = expectedErrorCode(behavior);

    try {
      const payload = await decodeKlickdEnvelope(v.envelope, v.passphrase);

      if (errCode !== null) {
        const msg = `FAIL ${vid}: expected error '${errCode}', got success`;
        console.log(`  ${msg}`);
        failed++;
        results.push({ id: vid, status: 'FAIL', detail: msg });
      } else {
        const dn = payload.identity?.name
                ?? payload.display_name
                ?? payload.user_preferences
                ?? '(no identity.name)';
        const ppArr = [...(v.passphrase ?? '')];
        const warnFlag = ppArr.length < WARN_PASSPHRASE_LEN && ppArr.length >= MIN_PASSPHRASE_LEN
                         ? ' [warned:short-pass]' : '';
        const rollbackNote = vid.includes('rollback') ? ' [rollback-gap documented]' : '';
        const msg = `PASS ${vid}: display_name=${JSON.stringify(dn)}${warnFlag}${rollbackNote}`;
        console.log(`  ${msg}`);
        passed++;
        results.push({ id: vid, status: 'PASS', detail: msg });
      }
    } catch (e) {
      const errMsg = e.message ?? String(e);

      // Argon2 skip — hash-wasm not installed
      if (errMsg.includes('KLICKD_E_SKIP_ARGON2')) {
        const msg = `SKIP ${vid}: Argon2id unavailable (install hash-wasm)`;
        console.log(`  ${msg}`);
        skipped++;
        results.push({ id: vid, status: 'SKIP', detail: msg });
        continue;
      }

      if (errCode !== null && errMsg.includes(errCode)) {
        const msg = `PASS ${vid}: ${errCode} as expected`;
        console.log(`  ${msg}`);
        passed++;
        results.push({ id: vid, status: 'PASS', detail: msg });
      } else if (errCode !== null) {
        const msg = `FAIL ${vid}: expected '${errCode}', got: ${errMsg.slice(0, 120)}`;
        console.log(`  ${msg}`);
        failed++;
        results.push({ id: vid, status: 'FAIL', detail: msg });
      } else {
        const msg = `FAIL ${vid}: unexpected error: ${errMsg.slice(0, 120)}`;
        console.log(`  ${msg}`);
        failed++;
        results.push({ id: vid, status: 'FAIL', detail: msg });
      }
    }
  }

  return { passed, failed, skipped, results };
}

// ── Main ──────────────────────────────────────────────────────────────────────
let totalPassed = 0, totalFailed = 0, totalSkipped = 0;

const hashWasmAvail = argon2id !== null;
console.log(`.klickd multi-version cross-impl JS test runner (v2.5 + v3.0)`);
console.log(`hash-wasm (Argon2id): ${hashWasmAvail ? 'available ✓' : 'NOT installed — v3.0 vectors will be skipped'}`);

const suites = [
  { path: 'tests/vectors_v25.json',          label: 'POSITIVE vectors — v2.5' },
  { path: 'tests/negative_vectors_v25.json', label: 'NEGATIVE vectors — v2.5' },
  { path: 'tests/vectors_v30.json',          label: 'POSITIVE vectors — v3.0' },
  { path: 'tests/negative_vectors_v30.json', label: 'NEGATIVE vectors — v3.0' },
];

for (const { path, label } of suites) {
  const { passed, failed, skipped } = await runSuite(join(__dir, path), label);
  totalPassed  += passed;
  totalFailed  += failed;
  totalSkipped += skipped;
}

const total = totalPassed + totalFailed;
console.log('\n' + '='.repeat(50));
if (totalSkipped > 0) {
  console.log(`SKIPPED: ${totalSkipped} (hash-wasm not installed — install with: npm install hash-wasm)`);
}
console.log(`TOTAL: ${totalPassed}/${total} passed  (${totalFailed} failed, ${totalSkipped} skipped)`);
process.exit(totalFailed > 0 ? 1 : 0);
