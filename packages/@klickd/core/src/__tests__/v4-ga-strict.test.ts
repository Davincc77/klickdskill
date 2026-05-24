// @klickd/core — v4 GA strict schema + persona validation tests
// SPDX-License-Identifier: CC0-1.0
//
// P0-4 (SDK TypeScript V4 GA alignment): mirrors the Python pytest matrix
// from packages/pypi/klickd/tests/test_v4_ga_strict.py against the
// TypeScript validate / validateIterErrors surface.
//
// Validation tests require the optional `ajv` peer dependency (installed
// as a devDependency for CI). Round-trip tests do NOT require ajv.

import { readFileSync, readdirSync, existsSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

import {
  KlickdError,
  saveKlickd,
  loadKlickd,
  validate,
  validateIterErrors,
  getBundledSchema,
  listBundledSchemas,
} from '../index.js';
import type { KlickdPayload } from '../index.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const REPO_ROOT = join(__dirname, '..', '..', '..', '..', '..');
const PERSONAS_DIR = join(REPO_ROOT, 'examples', 'v4', 'personas');
const PASSPHRASE = 'correct-horse-battery-staple-v4';

function loadPersona(name: string): KlickdPayload {
  return JSON.parse(readFileSync(join(PERSONAS_DIR, name), 'utf8')) as KlickdPayload;
}

const PERSONA_FILES = existsSync(PERSONAS_DIR)
  ? readdirSync(PERSONAS_DIR)
      .filter((f) => f.endsWith('.klickd'))
      .sort()
  : [];

// -- Sanity: personas dir and bundled schemas resolve ------------------------

describe('bundled v4 schemas', () => {
  it('lists all four bundled schema keys', () => {
    expect(listBundledSchemas().sort()).toEqual([
      'payload-preview',
      'payload-strict',
      'unified-preview',
      'unified-strict',
    ]);
  });

  it('payload-strict schema $id matches canonical', () => {
    const s = getBundledSchema('payload-strict');
    expect(s.$id).toEqual('https://klickd.app/schemas/v4/klickd-payload.schema.json');
  });

  it('unified-strict schema $id matches canonical', () => {
    const s = getBundledSchema('unified-strict');
    expect(String(s.$id)).toMatch(/klickd\.schema\.json$/);
  });
});

describe('personas directory', () => {
  it('contains 5 persona files', () => {
    expect(PERSONA_FILES.length).toBe(5);
  });
});

// -- Strict validation: personas ---------------------------------------------

describe.each(PERSONA_FILES)('persona %s', (persona) => {
  it('validates against strict v4 payload schema', async () => {
    await expect(validate(loadPersona(persona), { strict: true, target: 'payload' })).resolves.toBeUndefined();
  });

  it('validates against strict v4 unified schema', async () => {
    await expect(validate(loadPersona(persona), { strict: true, target: 'unified' })).resolves.toBeUndefined();
  });

  it('validates against permissive v4 preview payload schema', async () => {
    await expect(validate(loadPersona(persona), { strict: false, target: 'payload' })).resolves.toBeUndefined();
  });
});

// -- Round-trip preservation (SPEC.md §33.7) ---------------------------------

describe.each(PERSONA_FILES)('persona %s round-trip', (persona) => {
  it('save → load preserves the persona verbatim', async () => {
    const original = loadPersona(persona);
    const envelope = await saveKlickd(original, {
      passphrase: PASSPHRASE,
      domain: (original.domain as string | undefined) ?? 'education',
    });
    const recovered = await loadKlickd(envelope, { passphrase: PASSPHRASE });
    expect(recovered).toEqual(original);
  });

  it('double round-trip is stable', async () => {
    const original = loadPersona(persona);
    const once = await loadKlickd(
      await saveKlickd(original, { passphrase: PASSPHRASE }),
      { passphrase: PASSPHRASE },
    );
    const twice = await loadKlickd(
      await saveKlickd(once, { passphrase: PASSPHRASE }),
      { passphrase: PASSPHRASE },
    );
    expect(twice).toEqual(original);
  });
});

// -- Negative cases (must reject) --------------------------------------------

function minimalStrictPayload(): Record<string, unknown> {
  return { payload_schema_version: '4.0' };
}

describe('strict negative cases', () => {
  it('rejects unknown gate level', async () => {
    const bad = minimalStrictPayload();
    bad.verification_gates = {
      version: 1,
      gates: [{ action_class: 'x', level: 'loud' }],
    };
    await expect(validate(bad, { strict: true })).rejects.toMatchObject({ code: 'KLICKD_E_SCHEMA' });
  });

  it('rejects media entry missing hash', async () => {
    const bad = minimalStrictPayload();
    bad.media_profile = {
      version: 1,
      entries: [{ id: 'x', modality: 'voice' }],
    };
    await expect(validate(bad, { strict: true })).rejects.toMatchObject({ code: 'KLICKD_E_SCHEMA' });
  });

  it('rejects unknown media modality', async () => {
    const bad = minimalStrictPayload();
    bad.media_profile = {
      version: 1,
      entries: [
        { id: 'x', modality: 'video', hash: { algo: 'blake3', value: 'deadbeef' } },
      ],
    };
    await expect(validate(bad, { strict: true })).rejects.toMatchObject({ code: 'KLICKD_E_SCHEMA' });
  });

  it('rejects unsupported payload_schema_version', async () => {
    await expect(validate({ payload_schema_version: '9.9' }, { strict: true })).rejects.toMatchObject({
      code: 'KLICKD_E_SCHEMA',
    });
  });

  it('rejects missing payload_schema_version', async () => {
    await expect(validate({}, { strict: true })).rejects.toMatchObject({ code: 'KLICKD_E_SCHEMA' });
  });

  it('rejects encrypted envelope missing kdf (unified target)', async () => {
    const bad = {
      klickd_version: '4.0',
      created_at: '2026-05-24T00:00:00Z',
      encrypted: true,
    };
    await expect(validate(bad, { strict: true, target: 'unified' })).rejects.toMatchObject({
      code: 'KLICKD_E_SCHEMA',
    });
  });
});

// -- Both strict gate shapes accepted ----------------------------------------

describe('gate shapes', () => {
  it('accepts the structured form', async () => {
    const payload = minimalStrictPayload();
    payload.verification_gates = {
      version: 1,
      user_default: 'silent',
      gates: [
        { id: 'g1', action_class: 'public_post', level: 'block' },
        { action_class: 'factual_claim_with_date', level: 'confirm' },
      ],
    };
    await expect(validate(payload, { strict: true })).resolves.toBeUndefined();
  });

  it('accepts the flat map form', async () => {
    const payload = minimalStrictPayload();
    payload.verification_gates = {
      public_post: 'block',
      factual_claim_with_date: 'confirm',
    };
    await expect(validate(payload, { strict: true })).resolves.toBeUndefined();
  });

  it('rejects flat map with unknown level', async () => {
    const payload = minimalStrictPayload();
    payload.verification_gates = { public_post: 'loud' };
    await expect(validate(payload, { strict: true })).rejects.toMatchObject({ code: 'KLICKD_E_SCHEMA' });
  });
});

// -- Preview vs GA cross-acceptance ------------------------------------------

describe('preview/GA cross-acceptance', () => {
  it("accepts payload_schema_version '4.0.0-preview.1' in strict schema", async () => {
    await expect(validate({ payload_schema_version: '4.0.0-preview.1' }, { strict: true })).resolves.toBeUndefined();
    await expect(validate({ payload_schema_version: '4.0.0-preview.1' }, { strict: false })).resolves.toBeUndefined();
  });

  it("accepts payload_schema_version '4.0' with preview marker in preview schema", async () => {
    await expect(
      validate({ payload_schema_version: '4.0', preview: 'v4.0.0-preview.1' }, { strict: false }),
    ).resolves.toBeUndefined();
  });
});

// -- v3.x backward compatibility ---------------------------------------------

describe('v3.x non-regression', () => {
  it('v3 payload still saves/loads (no v4 validation invoked)', async () => {
    const v3: KlickdPayload = {
      payload_schema_version: '3.0.0',
      domain_schema_version: '1.0.0',
      identity: { name: 'v3 user', language: 'fr' },
      agent_instructions: 'be concise',
    };
    const envelope = await saveKlickd(v3, { passphrase: PASSPHRASE });
    const recovered = await loadKlickd(envelope, { passphrase: PASSPHRASE });
    expect(recovered).toEqual(v3);
  });

  it('v3 payload_schema_version fails v4 strict validation', async () => {
    await expect(validate({ payload_schema_version: '3.0.0' }, { strict: true })).rejects.toMatchObject({
      code: 'KLICKD_E_SCHEMA',
    });
  });
});

// -- Optional registered profiles (media/project/gaming) ---------------------

describe('registered profiles', () => {
  it('RPG gaming persona validates strict and round-trips', async () => {
    const persona = loadPersona('05-rpg-gamer-en.klickd');
    await expect(validate(persona, { strict: true, target: 'payload' })).resolves.toBeUndefined();
    const recovered = await loadKlickd(
      await saveKlickd(persona, { passphrase: PASSPHRASE }),
      { passphrase: PASSPHRASE },
    );
    expect(recovered).toEqual(persona);
  });

  it('créateur média persona validates strict and round-trips', async () => {
    const persona = loadPersona('04-createur-media-fr.klickd');
    await expect(validate(persona, { strict: true, target: 'payload' })).resolves.toBeUndefined();
    const recovered = await loadKlickd(
      await saveKlickd(persona, { passphrase: PASSPHRASE }),
      { passphrase: PASSPHRASE },
    );
    expect(recovered).toEqual(persona);
  });

  it('chef de projet PME persona validates strict', async () => {
    const persona = loadPersona('02-chef-projet-pme-fr.klickd');
    await expect(validate(persona, { strict: true, target: 'payload' })).resolves.toBeUndefined();
  });
});

// -- iter_errors variant -----------------------------------------------------

describe('validateIterErrors', () => {
  it('returns empty array on valid payload', async () => {
    expect(await validateIterErrors(loadPersona(PERSONA_FILES[0]), { strict: true })).toEqual([]);
  });

  it('returns {path, message} entries on invalid payload', async () => {
    const bad = minimalStrictPayload();
    bad.verification_gates = { public_post: 'loud' };
    const issues = await validateIterErrors(bad, { strict: true });
    expect(issues.length).toBeGreaterThan(0);
    for (const i of issues) {
      expect(typeof i.path).toBe('string');
      expect(typeof i.message).toBe('string');
    }
  });
});

// -- Unknown-field preservation under validation (§33.7) ---------------------

describe('unknown-field preservation', () => {
  it('unknown top-level field validates AND round-trips verbatim', async () => {
    const payload: Record<string, unknown> = minimalStrictPayload();
    payload.x_experimental_block = { future: true, values: [1, 2, 3] };
    await expect(validate(payload, { strict: true })).resolves.toBeUndefined();
    const recovered = await loadKlickd(
      await saveKlickd(payload as KlickdPayload, { passphrase: PASSPHRASE }),
      { passphrase: PASSPHRASE },
    );
    expect(recovered.x_experimental_block).toEqual(payload.x_experimental_block);
  });
});

// -- Optional-peer behaviour -------------------------------------------------

describe('KlickdError shape', () => {
  it('validation failure carries code KLICKD_E_SCHEMA + 400 httpStatus', async () => {
    try {
      await validate({}, { strict: true });
      throw new Error('should have thrown');
    } catch (e) {
      expect(e).toBeInstanceOf(KlickdError);
      const err = e as KlickdError;
      expect(err.code).toBe('KLICKD_E_SCHEMA');
      expect(err.httpStatus).toBe(400);
    }
  });
});
