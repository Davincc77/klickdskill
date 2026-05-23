// @klickd/core — v4 preview round-trip preservation test
// SPDX-License-Identifier: CC0-1.0
//
// Verifies that v4.0.0-preview.1 additive payload fields (profile_kind,
// media_profile, verification_gates, claim_sources, verification_artifacts,
// migration, context_cost) round-trip without data loss through saveKlickd /
// loadKlickd. The on-disk envelope remains v3 ("klickd_version":"3.0") — only
// the inner payload exercises v4 preview fields. No strict v4 validation is
// performed; preview support is purely additive preservation.

import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { dirname } from 'node:path';

import { saveKlickd, loadKlickd } from '../index.js';
import type { KlickdPayload } from '../index.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const FIXTURE_PATH = join(__dirname, 'fixtures', 'v4-preview-payload.json');
const PASSPHRASE = 'correct-horse-battery-staple';

function loadFixture(): KlickdPayload {
  return JSON.parse(readFileSync(FIXTURE_PATH, 'utf8')) as KlickdPayload;
}

describe('v4 preview round-trip (additive preservation)', () => {
  const V4_PREVIEW_FIELDS = [
    'profile_kind',
    'media_profile',
    'verification_gates',
    'claim_sources',
    'verification_artifacts',
    'migration',
    'context_cost',
    'preview',
  ] as const;

  it('preserves all v4 preview top-level fields on round-trip', async () => {
    const original = loadFixture();
    const envelope = await saveKlickd(original, { passphrase: PASSPHRASE, domain: 'education' });
    const recovered = await loadKlickd(envelope, { passphrase: PASSPHRASE });

    for (const key of V4_PREVIEW_FIELDS) {
      expect(recovered).toHaveProperty(key);
      expect(recovered[key]).toEqual(original[key]);
    }
  });

  it('preserves the exact top-level key set', async () => {
    const original = loadFixture();
    const envelope = await saveKlickd(original, { passphrase: PASSPHRASE });
    const recovered = await loadKlickd(envelope, { passphrase: PASSPHRASE });

    expect(new Set(Object.keys(recovered))).toEqual(new Set(Object.keys(original)));
  });

  it('is structurally equal to the original payload', async () => {
    const original = loadFixture();
    const envelope = await saveKlickd(original, { passphrase: PASSPHRASE });
    const recovered = await loadKlickd(envelope, { passphrase: PASSPHRASE });

    expect(recovered).toEqual(original);
  });

  it('is stable across a double round-trip', async () => {
    const original = loadFixture();
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

  it('preserves nested v4 structures (gates, sources, artifacts, migration, cost)', async () => {
    const original = loadFixture();
    const recovered = await loadKlickd(
      await saveKlickd(original, { passphrase: PASSPHRASE }),
      { passphrase: PASSPHRASE },
    );

    const gates = recovered.verification_gates as Record<string, string>;
    expect(gates.factual_claim_about_person).toBe('block');

    const sources = recovered.claim_sources as Record<string, string[]>;
    expect(sources.prefer).toEqual(['user_supplied', 'tool:web_search']);

    const artifacts = recovered.verification_artifacts as Array<Record<string, unknown>>;
    expect(artifacts[0].kind).toBe('citation');

    const migration = recovered.migration as Record<string, string>;
    expect(migration.from_version).toBe('3.5.1');

    const cost = recovered.context_cost as Record<string, number>;
    expect(cost.tokens_in).toBe(0);
  });
});
