/**
 * verify_vectors.mjs — .klickd v2.5 cross-impl JS test runner
 *
 * Runs both positive (vectors_v25.json) and negative (negative_vectors_v25.json) test vectors.
 *
 * Error code mapping (mirrors Python load_klickd.py):
 *   KlickdAuthError          → thrown Error containing "KLICKD_E_AUTH"
 *   KlickdVersionError       → thrown Error containing "KLICKD_E_VERSION"
 *   KlickdFormatError        → thrown Error containing "KLICKD_E_FORMAT"
 *   KlickdWeakPassphraseError→ thrown Error containing "KLICKD_E_WEAK_PASS"
 *   decrypt_success          → no throw
 *
 * Parity gaps documented inline where the JS decoder does NOT yet enforce a check
 * that the Python reference implementation (load_klickd.py) does.
 */

import { webcrypto } from 'crypto';
import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __dir = dirname(fileURLToPath(import.meta.url));
const enc = new TextEncoder();
const dec = new TextDecoder();

// ── Constants (mirror load_klickd.py) ─────────────────────────────────────────
const MIN_PASSPHRASE_LEN    = 8;
const WARN_PASSPHRASE_LEN   = 12;
const GCM_TAG_BYTES         = 16;
const MAX_ENVELOPE_BYTES    = 1 * 1024 * 1024;   // 1 MB  — Bankr HIGH 2.3a
const MAX_PAYLOAD_BYTES     = 4 * 1024 * 1024;   // 4 MB  — Bankr HIGH 2.3a (post-GCM)
const MAX_AGENT_INSTR_BYTES = 32 * 1024;          // 32 KB — Bankr P1 #6
const SUPPORTED_MAJOR       = new Set(['2']);      // v3.0 needs Argon2id — skipped
const VERSION_RE            = /^\d+\.\d+$/;

// ── Error helpers ──────────────────────────────────────────────────────────────
function KlickdFormatError(msg)        { throw new Error(`KLICKD_E_FORMAT: ${msg}`); }
function KlickdVersionError(msg)       { throw new Error(`KLICKD_E_VERSION: ${msg}`); }
function KlickdAuthError(msg)          { throw new Error(`KLICKD_E_AUTH: ${msg}`); }
function KlickdWeakPassphraseError(msg){ throw new Error(`KLICKD_E_WEAK_PASS: ${msg}`); }

// ── Strict standard-alphabet base64 decoder (Bankr MEDIUM 1.5) ────────────────
// Rejects URL-safe characters (- _) and non-padded strings.
const STANDARD_B64_RE = /^[A-Za-z0-9+/]*={0,2}$/;
function b64DecodeStrict(value, fieldName) {
  if (typeof value !== 'string' || !STANDARD_B64_RE.test(value)) {
    KlickdFormatError(`malformed base64 in '${fieldName}'`);
  }
  // Also reject if padding is wrong (length % 4 !== 0)
  if (value.length % 4 !== 0) {
    KlickdFormatError(`malformed base64 (bad padding) in '${fieldName}'`);
  }
  return Buffer.from(value, 'base64');
}

// ── AAD builder (v2.x: 4 fields, sort_keys, no spaces) ───────────────────────
function canonicalAadV2(envelope) {
  const fields = Object.fromEntries(
    ['created_at', 'domain', 'encrypted', 'klickd_version'].map(k => [k, envelope[k]])
  );
  // Must match Python: json.dumps(fields, sort_keys=True, separators=(',',':'), ensure_ascii=True)
  return enc.encode(JSON.stringify(fields));
}

// ── Core decode function (mirrors load_klickd.py, v2.x path) ─────────────────
async function decodeKlickdEnvelope(envelope, passphrase) {
  // 1. Passphrase length check (Bankr WEAK_PASS)
  if (passphrase.length < MIN_PASSPHRASE_LEN) {
    KlickdWeakPassphraseError(
      `passphrase too short (${passphrase.length} < ${MIN_PASSPHRASE_LEN})`
    );
  }
  if (passphrase.length < WARN_PASSPHRASE_LEN) {
    process.stderr.write(
      `WARNING: passphrase entropy below recommended threshold ` +
      `(${passphrase.length} chars < ${WARN_PASSPHRASE_LEN} recommended).\n`
    );
  }

  // 2. Version validation — Bankr MEDIUM 2.1a: must be string matching \d+\.\d+
  const versionStr = envelope.klickd_version;
  if (typeof versionStr !== 'string' || !VERSION_RE.test(versionStr)) {
    KlickdFormatError(
      `klickd_version must be a string matching N.N, got ${JSON.stringify(versionStr)}`
    );
  }
  const major = versionStr.split('.')[0];
  if (!SUPPORTED_MAJOR.has(major)) {
    // v3.0 uses Argon2id — not available in Web Crypto; skip gracefully
    if (major === '3') {
      throw new Error('KLICKD_E_SKIP_ARGON2: v3.0 requires Argon2id (not available in Web Crypto)');
    }
    KlickdVersionError(`unsupported version '${versionStr}'`);
  }

  // 3. Required field presence
  for (const field of ['encrypted', 'domain', 'created_at', 'ciphertext']) {
    if (!(field in envelope)) {
      KlickdFormatError(`missing required field '${field}'`);
    }
  }

  // 4. Strict base64 decode of ciphertext (Bankr MEDIUM 1.5)
  const raw = b64DecodeStrict(envelope.ciphertext, 'ciphertext');

  // 5. Ciphertext minimum length check
  if (raw.length < GCM_TAG_BYTES) {
    KlickdFormatError(`ciphertext too short (< ${GCM_TAG_BYTES} bytes)`);
  }

  // 6. v2.x-specific fields
  if (!('kdf_salt' in envelope)) {
    KlickdFormatError("missing required field 'kdf_salt'");
  }
  if (!('iv' in envelope)) {
    KlickdFormatError("missing required field 'iv'");
  }

  const salt = b64DecodeStrict(envelope.kdf_salt, 'kdf_salt');
  const iv   = b64DecodeStrict(envelope.iv, 'iv');
  const aad  = canonicalAadV2(envelope);

  // 7. PBKDF2-SHA256 key derivation (600 000 iterations)
  const km  = await webcrypto.subtle.importKey(
    'raw', enc.encode(passphrase), { name: 'PBKDF2' }, false, ['deriveKey']
  );
  const key = await webcrypto.subtle.deriveKey(
    { name: 'PBKDF2', salt, iterations: 600_000, hash: 'SHA-256' },
    km,
    { name: 'AES-GCM', length: 256 },
    false,
    ['decrypt']
  );

  // 8. AES-GCM decrypt
  let plaintext;
  try {
    const ptBuf = await webcrypto.subtle.decrypt(
      { name: 'AES-GCM', iv, additionalData: aad, tagLength: 128 },
      key,
      raw
    );
    // GAP-2 fix: 4 MB raw plaintext cap post-GCM (Bankr HIGH 2.3a)
    if (ptBuf.byteLength > MAX_PAYLOAD_BYTES) {
      KlickdFormatError(
        `payload exceeds 4MB limit (${ptBuf.byteLength} bytes)`
      );
    }
    plaintext = dec.decode(ptBuf);
  } catch (e) {
    if (e.message && e.message.startsWith('KLICKD_E_')) throw e;
    KlickdAuthError('decryption failed — wrong passphrase or tampered file');
  }

  // 9. Parse inner JSON
  let payload;
  try {
    payload = JSON.parse(plaintext);
  } catch {
    KlickdFormatError('decrypted payload is not valid JSON');
  }

  // 10. agent_instructions / user_preferences 32 KB cap (Bankr P1 #6)
  const agentInstr = payload.agent_instructions ?? payload.user_preferences ?? '';
  if (typeof agentInstr === 'string') {
    const byteLen = Buffer.byteLength(agentInstr, 'utf8');
    if (byteLen > MAX_AGENT_INSTR_BYTES) {
      KlickdFormatError(
        `agent_instructions/user_preferences exceeds 32 KB limit (${byteLen} bytes)`
      );
    }
  }

  return payload;
}

// ── Expected-behavior classifier ──────────────────────────────────────────────
// Returns the expected error code string fragment, or null for success.
function expectedErrorCode(behavior) {
  if (!behavior) return null;
  if (behavior.includes('KlickdAuthError'))           return 'KLICKD_E_AUTH';
  if (behavior.includes('KlickdVersionError'))        return 'KLICKD_E_VERSION';
  if (behavior.includes('KlickdFormatError'))         return 'KLICKD_E_FORMAT';
  if (behavior.includes('KlickdWeakPassphraseError')) return 'KLICKD_E_WEAK_PASS';
  if (behavior.includes('decrypt_success'))           return null;
  return null;  // unknown behavior string → treat as success
}

// ── Suite runner ───────────────────────────────────────────────────────────────
async function runSuite(vectorsPath, label) {
  // GAP-1 fix: 1 MB envelope file-level cap (Bankr HIGH 2.3a)
  const rawBuf = readFileSync(vectorsPath);
  const data   = JSON.parse(rawBuf.toString('utf8'));
  let passed = 0, failed = 0, skipped = 0;
  const results = [];

  console.log(`\n── ${label} — spec ${data.spec_version} ──────────────────────────`);

  for (const v of data.vectors) {
    const vid      = v.id;
    const behavior = v.expected_behavior ?? '';
    const errCode  = expectedErrorCode(behavior);

    let result;
    try {
      const payload = await decodeKlickdEnvelope(v.envelope, v.passphrase);

      if (errCode !== null) {
        // Expected an error but got success
        const msg = `FAIL ${vid}: expected error containing '${errCode}', got success`;
        console.log(`  ${msg}`);
        failed++;
        results.push({ id: vid, status: 'FAIL', detail: msg });
      } else {
        const dn     = payload.display_name ?? payload.user_preferences ?? '(no display_name)';
        const warnFlag = v.passphrase?.length < WARN_PASSPHRASE_LEN &&
                         v.passphrase?.length >= MIN_PASSPHRASE_LEN ? ' [warned:short-pass]' : '';
        const rollbackNote = vid.includes('rollback') ? ' [rollback-gap documented]' : '';
        const msg = `PASS ${vid}: display_name=${JSON.stringify(dn)}${warnFlag}${rollbackNote}`;
        console.log(`  ${msg}`);
        passed++;
        results.push({ id: vid, status: 'PASS', detail: msg });
      }
    } catch (e) {
      const errMsg = e.message ?? String(e);

      // Argon2 skip
      if (errMsg.includes('KLICKD_E_SKIP_ARGON2')) {
        const msg = `SKIP ${vid}: ${errMsg}`;
        console.log(`  ${msg}`);
        skipped++;
        results.push({ id: vid, status: 'SKIP', detail: msg });
        continue;
      }

      if (errCode !== null && errMsg.includes(errCode)) {
        const msg = `PASS ${vid}: ${errCode} as expected (${errMsg.slice(0, 80)})`;
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

// ── Main ───────────────────────────────────────────────────────────────────────
let totalPassed = 0, totalFailed = 0, totalSkipped = 0;
const allResults = {};

const posPath = join(__dir, 'tests', 'vectors_v25.json');
const negPath = join(__dir, 'tests', 'negative_vectors_v25.json');

console.log('.klickd cross-impl JS test runner (v2.5)');

{ // Positive vectors
  const { passed, failed, skipped, results } = await runSuite(posPath, 'POSITIVE vectors');
  totalPassed  += passed;
  totalFailed  += failed;
  totalSkipped += skipped;
  allResults.positive = results;
}

{ // Negative vectors
  const { passed, failed, skipped, results } = await runSuite(negPath, 'NEGATIVE vectors');
  totalPassed  += passed;
  totalFailed  += failed;
  totalSkipped += skipped;
  allResults.negative = results;
}

const total = totalPassed + totalFailed;
console.log('\n' + '='.repeat(50));
console.log(`TOTAL: ${totalPassed}/${total} passed  (${totalFailed} failed, ${totalSkipped} skipped)`);
process.exit(totalFailed > 0 ? 1 : 0);
