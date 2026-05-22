// .klickd v3 — decode (load) implementation
// SPDX-License-Identifier: CC0-1.0

import { createDecipheriv, createSecretKey, pbkdf2 as pbkdf2Cb } from 'node:crypto';
import { promisify } from 'node:util';
import canonicalize from 'canonicalize';
import type { KlickdEnvelope, KlickdPayload, LoadKlickdOptions } from './types.js';
import { KlickdError, HTTP_STATUS } from './errors.js';

const pbkdf2 = promisify(pbkdf2Cb);

const SUPPORTED_MAJOR = 3;

/** RFC 4648 §4 standard padded base64 → Buffer */
function fromBase64(s: string): Buffer {
  return Buffer.from(s, 'base64');
}

/** Derive key with Argon2id — same dual-import pattern as encode.ts */
async function deriveKeyArgon2id(
  passphrase: string,
  salt: Buffer,
  m: number,
  t: number,
  p: number,
): Promise<Uint8Array> {
  try {
    const argon2 = await import('argon2');
    const hash = await argon2.hash(passphrase, {
      type: argon2.argon2id,
      memoryCost: m,
      timeCost: t,
      parallelism: p,
      salt,
      hashLength: 32,
      raw: true,
    });
    return new Uint8Array(hash);
  } catch {
    try {
      const argon2browser = await import('argon2-browser');
      const result = await argon2browser.hash({
        pass: passphrase,
        salt: new Uint8Array(salt),
        type: argon2browser.ArgonType.Argon2id,
        mem: m,
        time: t,
        parallelism: p,
        hashLen: 32,
      });
      return result.hash;
    } catch {
      throw new KlickdError(
        'KLICKD_E_KDF',
        'Argon2id is unavailable. Install "argon2" (Node.js) or "argon2-browser" (browser).',
        HTTP_STATUS['KLICKD_E_KDF'],
      );
    }
  }
}

/** Derive key with PBKDF2-SHA256 (legacy v2.x) */
async function deriveKeyPbkdf2(
  passphrase: string,
  salt: Buffer,
  iterations: number,
): Promise<Uint8Array> {
  const key = await pbkdf2(passphrase, salt, iterations, 32, 'sha256');
  return new Uint8Array(key);
}

/**
 * Load and decrypt a .klickd envelope.
 *
 * @param input      - Raw .klickd JSON (string or UTF-8 bytes).
 * @param options    - Passphrase and optional legacy mode.
 * @returns          - The decrypted KlickdPayload.
 */
export async function loadKlickd(
  input: string | Uint8Array,
  options: LoadKlickdOptions = {},
): Promise<KlickdPayload> {
  const { passphrase, legacy = false } = options;

  // Parse envelope JSON
  let envelope: KlickdEnvelope;
  try {
    const raw = typeof input === 'string' ? input : new TextDecoder().decode(input);
    envelope = JSON.parse(raw) as KlickdEnvelope;
  } catch {
    throw new KlickdError('KLICKD_E_FORMAT', 'Invalid JSON envelope.', HTTP_STATUS['KLICKD_E_FORMAT']);
  }

  // Validate required top-level fields
  const requiredFields = ['klickd_version', 'encrypted', 'domain', 'created_at', 'kdf', 'cipher', 'ciphertext'];
  for (const field of requiredFields) {
    if (!(field in envelope)) {
      throw new KlickdError(
        'KLICKD_E_FORMAT',
        `Missing required envelope field: ${field}`,
        HTTP_STATUS['KLICKD_E_FORMAT'],
      );
    }
  }

  // Check major version
  const major = parseInt(envelope.klickd_version.split('.')[0], 10);
  if (isNaN(major) || major !== SUPPORTED_MAJOR) {
    throw new KlickdError(
      'KLICKD_E_VERSION',
      `Unsupported klickd_version major: ${envelope.klickd_version}. This library supports v${SUPPORTED_MAJOR}.x.`,
      HTTP_STATUS['KLICKD_E_VERSION'],
    );
  }

  // Reconstruct AAD: JCS over the 6 canonical fields (in envelope key order)
  const envelopeForAad = {
    klickd_version: envelope.klickd_version,
    encrypted: envelope.encrypted,
    domain: envelope.domain,
    created_at: envelope.created_at,
    kdf: envelope.kdf,
    cipher: envelope.cipher,
  };
  const aadString = canonicalize(envelopeForAad);
  if (!aadString) {
    throw new KlickdError('KLICKD_E_FORMAT', 'Failed to canonicalize AAD.', 400);
  }
  const aad = Buffer.from(aadString, 'utf8');

  // Derive decryption key
  if (!passphrase) {
    throw new KlickdError(
      'KLICKD_E_AUTH',
      'A passphrase is required to decrypt this file.',
      HTTP_STATUS['KLICKD_E_AUTH'],
    );
  }

  let keyBytes: Uint8Array;
  const kdf = envelope.kdf;

  if (kdf.name === 'argon2id') {
    const salt = fromBase64(kdf.salt);
    const { m, t, p } = kdf.params;
    // Argon2id parameter floor validation (mirrors Python _validate_argon2_params)
    if (!m || m < 65536) throw new KlickdError('KLICKD_E_KDF', `kdf.params.m=${m} below minimum 65536`, HTTP_STATUS['KLICKD_E_KDF']);
    if (!t || t < 3)     throw new KlickdError('KLICKD_E_KDF', `kdf.params.t=${t} below minimum 3`,     HTTP_STATUS['KLICKD_E_KDF']);
    if (!p || p < 1)     throw new KlickdError('KLICKD_E_KDF', `kdf.params.p=${p} below minimum 1`,     HTTP_STATUS['KLICKD_E_KDF']);
    keyBytes = await deriveKeyArgon2id(passphrase, salt, m, t, p);
  } else if (kdf.name === 'pbkdf2-sha256') {
    if (!legacy) {
      throw new KlickdError(
        'KLICKD_E_KDF',
        'Legacy PBKDF2 KDF detected. Set options.legacy = true to enable reading legacy v2.x files.',
        HTTP_STATUS['KLICKD_E_KDF'],
      );
    }
    const salt = fromBase64(kdf.salt);
    keyBytes = await deriveKeyPbkdf2(passphrase, salt, kdf.params.iterations);
  } else {
    throw new KlickdError(
      'KLICKD_E_KDF',
      `Unknown KDF: ${(kdf as { name: string }).name}`,
      HTTP_STATUS['KLICKD_E_KDF'],
    );
  }

  // Validate cipher name (algorithm agility — reject unknown ciphers explicitly).
  // Canonical = 'AES-256-GCM'. Accept legacy 'aes-256-gcm' (vectors generated < v3.5.1)
  // with a console deprecation notice so existing files keep loading.
  const cipherName = envelope.cipher.name as string;
  if (cipherName === 'aes-256-gcm') {
    // eslint-disable-next-line no-console
    console.warn(
      "KLICKD_W_DEPRECATED: cipher.name='aes-256-gcm' (lowercase) is legacy; canonical is 'AES-256-GCM'. Re-encode to upgrade.",
    );
  } else if (cipherName !== 'AES-256-GCM') {
    throw new KlickdError(
      'KLICKD_E_FORMAT',
      `Unsupported cipher: ${cipherName}. Only AES-256-GCM is supported in v3.0 (legacy 'aes-256-gcm' also accepted).`,
      HTTP_STATUS['KLICKD_E_FORMAT'],
    );
  }

  // Decode ciphertext (ciphertext || 16-byte GCM auth tag)
  const ciphertextWithTag = fromBase64(envelope.ciphertext);
  if (ciphertextWithTag.length < 16) {
    throw new KlickdError('KLICKD_E_FORMAT', 'Ciphertext too short.', HTTP_STATUS['KLICKD_E_FORMAT']);
  }
  const authTag = ciphertextWithTag.subarray(ciphertextWithTag.length - 16);
  const ciphertextBytes = ciphertextWithTag.subarray(0, ciphertextWithTag.length - 16);

  // Decrypt AES-256-GCM
  const iv = fromBase64(envelope.cipher.iv);
  let plaintext: Buffer;
  try {
    const decipher = createDecipheriv('aes-256-gcm', createSecretKey(keyBytes), iv);
    decipher.setAAD(aad);
    decipher.setAuthTag(authTag);
    plaintext = Buffer.concat([decipher.update(ciphertextBytes), decipher.final()]);
  } catch {
    throw new KlickdError(
      'KLICKD_E_AUTH',
      'Decryption failed: wrong passphrase or corrupted file.',
      HTTP_STATUS['KLICKD_E_AUTH'],
    );
  }

  // Parse payload JSON
  let payload: KlickdPayload;
  try {
    payload = JSON.parse(plaintext.toString('utf8')) as KlickdPayload;
  } catch {
    throw new KlickdError('KLICKD_E_FORMAT', 'Decrypted data is not valid JSON.', HTTP_STATUS['KLICKD_E_FORMAT']);
  }

  // Validate payload_schema_version
  if (!payload.payload_schema_version) {
    throw new KlickdError(
      'KLICKD_E_SCHEMA',
      'Decrypted payload is missing payload_schema_version.',
      HTTP_STATUS['KLICKD_E_SCHEMA'],
    );
  }

  return payload;
}
