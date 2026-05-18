// @klickd/core — roundtrip test
// SPDX-License-Identifier: CC0-1.0

import { saveKlickd, loadKlickd, KlickdError } from '../index.js';
import type { KlickdPayload } from '../index.js';

const TEST_PAYLOAD: KlickdPayload = {
  payload_schema_version: '3.0.0',
  domain_schema_version: '1.0.0',
  identity: {
    name: 'Test User',
    language: 'en',
    timezone: 'Europe/Luxembourg',
  },
  agent_instructions: 'Be concise and precise.',
  memory: [
    {
      id: '00000000-0000-4000-a000-000000000001',
      ts: '2025-01-01T00:00:00Z',
      role: 'user',
      content: 'Hello from the test suite.',
      modality: 'text',
      tags: ['test'],
    },
  ],
};

describe('saveKlickd / loadKlickd roundtrip', () => {
  const PASSPHRASE = 'correct-horse-battery-staple';

  it('encrypts and decrypts a payload successfully', async () => {
    const envelope = await saveKlickd(TEST_PAYLOAD, {
      passphrase: PASSPHRASE,
      domain: 'education',
    });

    expect(typeof envelope).toBe('string');

    const parsed = JSON.parse(envelope);
    expect(parsed.klickd_version).toBe('3.0');
    expect(parsed.encrypted).toBe(true);
    expect(parsed.domain).toBe('education');
    expect(typeof parsed.ciphertext).toBe('string');

    const recovered = await loadKlickd(envelope, { passphrase: PASSPHRASE });

    expect(recovered.payload_schema_version).toBe(TEST_PAYLOAD.payload_schema_version);
    expect(recovered.domain_schema_version).toBe(TEST_PAYLOAD.domain_schema_version);
    expect(recovered.identity?.name).toBe('Test User');
    expect(recovered.memory?.[0].content).toBe('Hello from the test suite.');
  });

  it('rejects a wrong passphrase with KLICKD_E_AUTH', async () => {
    const envelope = await saveKlickd(TEST_PAYLOAD, { passphrase: PASSPHRASE });

    await expect(loadKlickd(envelope, { passphrase: 'wrong-passphrase' })).rejects.toMatchObject({
      code: 'KLICKD_E_AUTH',
    });
  });

  it('rejects a weak passphrase with KLICKD_E_WEAK_PASS', async () => {
    await expect(saveKlickd(TEST_PAYLOAD, { passphrase: 'short' })).rejects.toMatchObject({
      code: 'KLICKD_E_WEAK_PASS',
    });
  });

  it('rejects malformed JSON with KLICKD_E_FORMAT', async () => {
    await expect(loadKlickd('not-json', { passphrase: PASSPHRASE })).rejects.toMatchObject({
      code: 'KLICKD_E_FORMAT',
    });
  });

  it('rejects legacy KDF without legacy flag', async () => {
    // Manually craft a v3 envelope with pbkdf2-sha256 KDF
    const fakeEnvelope = JSON.stringify({
      klickd_version: '3.0',
      encrypted: true,
      domain: 'education',
      created_at: '2025-01-01T00:00:00Z',
      kdf: { name: 'pbkdf2-sha256', params: { iterations: 600000 }, salt: 'AAAAAAAAAAAAAAAA' },
      cipher: { name: 'AES-256-GCM', iv: 'AAAAAAAAAAAA' },
      ciphertext: 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA==',
    });
    await expect(loadKlickd(fakeEnvelope, { passphrase: PASSPHRASE })).rejects.toMatchObject({
      code: 'KLICKD_E_KDF',
    });
  });

  it('KlickdError has correct httpStatus', () => {
    const err = new KlickdError('KLICKD_E_AUTH', 'test', 401);
    expect(err.httpStatus).toBe(401);
    expect(err.name).toBe('KlickdError');
    expect(err.message).toContain('KLICKD_E_AUTH');
  });
});
