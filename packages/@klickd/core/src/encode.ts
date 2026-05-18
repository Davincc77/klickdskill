// .klickd v3 — encode (save) implementation
// SPDX-License-Identifier: CC0-1.0

import { randomBytes, createCipheriv, createSecretKey } from 'node:crypto';
import canonicalize from 'canonicalize';
import type { KlickdPayload, KlickdEnvelope, KlickdDomain, SaveKlickdOptions } from './types.js';
import { KlickdError, HTTP_STATUS } from './errors.js';

const KLICKD_VERSION = '3.0.0';

/** RFC 4648 §4 standard padded base64 */
function toBase64(buf: Uint8Array): string {
  return Buffer.from(buf).toString('base64');
}

/**
 * Derive a 32-byte key using Argon2id.
 * Tries the 'argon2' package (Node.js native), falls back to 'argon2-browser' (browser/bundler).
 */
async function deriveKeyArgon2id(
  passphrase: string,
  salt: Uint8Array,
  m: number,
  t: number,
  p: number,
): Promise<Uint8Array> {
  // Try Node.js native argon2 first
  try {
    const argon2 = await import('argon2');
    const hash = await argon2.hash(passphrase, {
      type: argon2.argon2id,
      memoryCost: m,
      timeCost: t,
      parallelism: p,
      salt: Buffer.from(salt),
      hashLength: 32,
      raw: true,
    });
    return new Uint8Array(hash);
  } catch {
    // Fallback to argon2-browser (browser/bundler environments)
    try {
      const argon2browser = await import('argon2-browser');
      const result = await argon2browser.hash({
        pass: passphrase,
        salt,
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

/**
 * Save a KlickdPayload as an encrypted .klickd envelope JSON string.
 *
 * @param payload  - The plaintext payload to encrypt.
 * @param options  - Passphrase, domain, and optional Argon2id param overrides.
 * @returns        - The complete .klickd JSON string (UTF-8).
 */
export async function saveKlickd(
  payload: KlickdPayload,
  options: SaveKlickdOptions,
): Promise<string> {
  const { passphrase, domain = 'education', kdfParams = { m: 65536, t: 3, p: 1 } } = options;

  // Validate passphrase length
  if (!passphrase || passphrase.length < 8) {
    throw new KlickdError(
      'KLICKD_E_WEAK_PASS',
      'Passphrase must be at least 8 characters.',
      HTTP_STATUS['KLICKD_E_WEAK_PASS'],
    );
  }

  // Validate payload schema version
  if (!payload.payload_schema_version) {
    throw new KlickdError(
      'KLICKD_E_SCHEMA',
      'payload.payload_schema_version is required.',
      HTTP_STATUS['KLICKD_E_SCHEMA'],
    );
  }

  // Generate fresh CSPRNG salt (16 bytes) and IV (12 bytes)
  const salt = randomBytes(16);
  const iv = randomBytes(12);

  // Derive 32-byte key with Argon2id
  const keyBytes = await deriveKeyArgon2id(passphrase, salt, kdfParams.m, kdfParams.t, kdfParams.p);

  // Build the 6-field envelope (without ciphertext) for AAD
  const created_at = new Date().toISOString().replace(/\.\d{3}Z$/, 'Z');
  const envelopeForAad = {
    klickd_version: KLICKD_VERSION,
    encrypted: true,
    domain: domain as KlickdDomain,
    created_at,
    kdf: {
      name: 'argon2id' as const,
      params: kdfParams,
      salt: toBase64(salt),
    },
    cipher: {
      name: 'AES-256-GCM' as const,
      iv: toBase64(iv),
    },
  };

  // AAD = RFC 8785 JCS over the 6 canonical fields
  const aadString = canonicalize(envelopeForAad);
  if (!aadString) {
    throw new KlickdError('KLICKD_E_FORMAT', 'Failed to canonicalize AAD.', 400);
  }
  const aad = Buffer.from(aadString, 'utf8');

  // Encrypt payload JSON with AES-256-GCM
  const plaintext = Buffer.from(JSON.stringify(payload), 'utf8');
  const cipher = createCipheriv('aes-256-gcm', createSecretKey(keyBytes), iv);
  cipher.setAAD(aad);
  const encrypted = Buffer.concat([cipher.update(plaintext), cipher.final()]);
  const authTag = cipher.getAuthTag(); // 16 bytes

  // Ciphertext = encrypted || authTag (base64)
  const ciphertext = toBase64(Buffer.concat([encrypted, authTag]));

  const envelope: KlickdEnvelope = {
    ...envelopeForAad,
    ciphertext,
  };

  return JSON.stringify(envelope);
}
