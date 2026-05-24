// @klickd/core — v3.x → v4 GA payload migrator (P0-5)
// SPDX-License-Identifier: CC0-1.0
//
// Cross-impl parity with packages/pypi/klickd/tests/test_migrate_v3_to_v4.py.
// Contract under test: docs/spec/MIGRATION_V3_TO_V4.md.

import { readFileSync, existsSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

import {
  KlickdError,
  migratePayload,
  migratePayloadIterWarnings,
  needsMigration,
  validateIterErrors,
} from '../index.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const REPO_ROOT = join(__dirname, '..', '..', '..', '..', '..');
const V3_EXAMPLES_DIR = join(REPO_ROOT, 'examples');
const PINNED_TS = '2026-05-24T10:00:00Z';

const V3_FILES = [
  'student_fr.klickd',
  'full_v34.klickd',
  'family_plan.klickd',
  'minimal.klickd',
  'professional_en.klickd',
  'example_v33_full.klickd',
];

// See companion Python suite for the rationale: full_v34.klickd contains
// learning_goal.stakes="critical", which the v4 GA strict enum tightens to
// {low, medium, high}. The migrator is non-destructive and preserves the
// value verbatim, so we exclude this file from the strict-pass assertion.
const V3_FILES_STRICT_EXEMPT = new Set<string>(['full_v34.klickd']);

function loadV3(name: string): Record<string, unknown> {
  return JSON.parse(readFileSync(join(V3_EXAMPLES_DIR, name), 'utf8')) as Record<
    string,
    unknown
  >;
}

// -- needsMigration ----------------------------------------------------------

describe('needsMigration', () => {
  it('returns true for v3 payload with no schema version field', () => {
    expect(needsMigration({ identity: { name: 'x' } })).toBe(true);
  });

  it('returns true for explicit v3.x', () => {
    expect(needsMigration({ payload_schema_version: '3.0' })).toBe(true);
    expect(needsMigration({ payload_schema_version: '3.4' })).toBe(true);
    expect(needsMigration({ payload_schema_version: '3.5' })).toBe(true);
  });

  it('returns false for already-v4 payloads', () => {
    expect(needsMigration({ payload_schema_version: '4.0' })).toBe(false);
    expect(needsMigration({ payload_schema_version: '4.0.0-preview.1' })).toBe(false);
  });

  it('returns false for non-objects', () => {
    expect(needsMigration('nope' as unknown)).toBe(false);
    expect(needsMigration([])).toBe(false);
    expect(needsMigration(null)).toBe(false);
    expect(needsMigration(undefined)).toBe(false);
  });

  it('does not auto-migrate unknown versions', () => {
    expect(needsMigration({ payload_schema_version: '9.9' })).toBe(false);
  });
});

// -- migratePayload: core invariants ----------------------------------------

describe('migratePayload', () => {
  it('stamps v4 schema and default profile_kind', () => {
    const src = { payload_schema_version: '3.0', identity: { name: 'Alice' } };
    const out = migratePayload(src, { migratedAt: PINNED_TS });
    expect(out.payload_schema_version).toBe('4.0');
    expect(out.profile_kind).toBe('learner');
    expect(out.migration).toEqual({
      source_version: '3.0',
      migrated_at: PINNED_TS,
    });
  });

  it('records pointer refs', () => {
    const out = migratePayload(
      { payload_schema_version: '3.4' },
      {
        migratedAt: PINNED_TS,
        migrationReportRef: 'file://reports/2026-05-24.md',
        backupRef: 'ipfs://Qm...',
      },
    );
    expect(out.migration).toEqual({
      source_version: '3.4',
      migrated_at: PINNED_TS,
      migration_report_ref: 'file://reports/2026-05-24.md',
      backup_ref: 'ipfs://Qm...',
    });
  });

  it('does not mutate input', () => {
    const src = { payload_schema_version: '3.4', identity: { name: 'Bob' } };
    const snapshot = JSON.parse(JSON.stringify(src));
    migratePayload(src, { migratedAt: PINNED_TS });
    expect(src).toEqual(snapshot);
  });

  it('defaults source_version to "3.x" when payload has none', () => {
    const out = migratePayload({ identity: {} }, { migratedAt: PINNED_TS });
    expect((out.migration as Record<string, unknown>).source_version).toBe('3.x');
  });

  it('respects caller-supplied profileKind', () => {
    const out = migratePayload(
      { payload_schema_version: '3.4' },
      { profileKind: 'creator', migratedAt: PINNED_TS },
    );
    expect(out.profile_kind).toBe('creator');
  });

  it('preserves payload-supplied profile_kind', () => {
    const out = migratePayload(
      { payload_schema_version: '3.4', profile_kind: 'team' },
      { migratedAt: PINNED_TS },
    );
    expect(out.profile_kind).toBe('team');
  });

  it('preserves all v3 blocks verbatim', () => {
    const src: Record<string, unknown> = {
      payload_schema_version: '3.4',
      domain_schema_version: 'education-1.2',
      injection_target: 'system_prompt',
      identity: { name: 'Eve', language: 'fr' },
      context: { summary: 'test', decisions_locked: ['always-fr'] },
      knowledge: { mastered: ['pythagoras'] },
      memory: [],
      agent_instructions: 'be concise',
      user_preferences: 'advisory',
      companion_identity: { name: 'Aria' },
      ethics: { locked_actions: ['self_harm'] },
      learning_goal: { type: 'exam', stakes: 'high' },
      x_custom_extension: { foo: 'bar' },
    };
    const out = migratePayload(src, { migratedAt: PINNED_TS });
    for (const key of [
      'domain_schema_version',
      'injection_target',
      'identity',
      'context',
      'knowledge',
      'memory',
      'agent_instructions',
      'user_preferences',
      'companion_identity',
      'ethics',
      'learning_goal',
      'x_custom_extension',
    ]) {
      expect(out[key]).toEqual(src[key]);
    }
  });

  it('does not invent safety surface', () => {
    const out = migratePayload({ payload_schema_version: '3.4' }, { migratedAt: PINNED_TS });
    for (const forbidden of [
      'verification_gates',
      'human_veto_policy',
      'claim_sources',
      'risk_thresholds',
      'preflight_checks',
      'error_journal',
      'media_profile',
      'verification_artifacts',
      'reversibility',
      'blast_radius',
      'contract_tests',
      'success_criteria',
      'deprecated_fields',
      'gaming_profile',
      '_example_metadata',
      'context_cost',
    ]) {
      expect(out[forbidden]).toBeUndefined();
    }
  });

  it('does not touch envelope-AAD keys when present in input dict', () => {
    if (!existsSync(join(V3_EXAMPLES_DIR, 'minimal.klickd'))) return;
    const src = loadV3('minimal.klickd');
    const snapshot: Record<string, unknown> = {};
    for (const k of ['klickd_version', 'created_at', 'encrypted', 'domain']) {
      if (k in src) snapshot[k] = src[k];
    }
    const out = migratePayload(src, { migratedAt: PINNED_TS });
    for (const [k, v] of Object.entries(snapshot)) {
      expect(out[k]).toEqual(v);
    }
  });

  it('is idempotent on already-v4 payloads (no pointer refs)', () => {
    const v4 = {
      payload_schema_version: '4.0',
      profile_kind: 'learner',
      migration: { source_version: '3.4', migrated_at: PINNED_TS },
      identity: { name: 'Sam' },
    };
    const once = migratePayload(v4);
    expect(once).toEqual(v4);
    const twice = migratePayload(once);
    expect(twice).toEqual(v4);
  });

  it('refreshes migration block on v4 passthrough when pointer refs supplied', () => {
    const v4 = { payload_schema_version: '4.0', identity: { name: 'Sam' } };
    const out = migratePayload(v4, {
      migratedAt: PINNED_TS,
      migrationReportRef: 'file://r.md',
    });
    const mig = out.migration as Record<string, unknown>;
    expect(mig.migration_report_ref).toBe('file://r.md');
    expect(mig.source_version).toBe('4.0');
  });

  it('is idempotent when run twice on a v3 source', () => {
    const src = { payload_schema_version: '3.4', identity: { name: 'Lex' } };
    const once = migratePayload(src, { migratedAt: PINNED_TS });
    const twice = migratePayload(once, { migratedAt: PINNED_TS });
    expect(twice).toEqual(once);
  });
});

// -- migratePayload: errors --------------------------------------------------

describe('migratePayload errors', () => {
  it('rejects non-object input', () => {
    expect(() => migratePayload('nope' as unknown)).toThrow(KlickdError);
    try {
      migratePayload('nope' as unknown);
    } catch (e) {
      expect((e as KlickdError).code).toBe('KLICKD_E_SCHEMA');
    }
  });

  it('rejects unknown payload_schema_version', () => {
    expect(() => migratePayload({ payload_schema_version: '9.9' })).toThrow(KlickdError);
  });
});

// -- warnings ----------------------------------------------------------------

describe('migratePayloadIterWarnings', () => {
  it('returns [] for a clean v3 minimal payload', () => {
    expect(
      migratePayloadIterWarnings({
        payload_schema_version: '3.4',
        domain_schema_version: 'education-1.0',
      }),
    ).toEqual([]);
  });

  it('warns when both payload + domain schema versions are absent', () => {
    const w = migratePayloadIterWarnings({ identity: { name: 'x' } });
    expect(w.some((x) => x.message.includes('pin sourceVersion'))).toBe(true);
  });

  it('warns on overlong decisions_locked entries', () => {
    const w = migratePayloadIterWarnings({
      payload_schema_version: '3.4',
      domain_schema_version: 'education-1.0',
      context: { decisions_locked: ['a'.repeat(2000)] },
    });
    expect(w.some((x) => x.message.includes('exceeds 1024'))).toBe(true);
  });

  it('warns on unknown profile_kind', () => {
    const w = migratePayloadIterWarnings({
      payload_schema_version: '3.4',
      domain_schema_version: 'education-1.0',
      profile_kind: 'ufo',
    });
    expect(w.some((x) => x.message.includes('non-reserved profile_kind'))).toBe(true);
  });
});

// -- v3 example files round-trip + validate strict v4 ----------------------

describe('v3 examples round-trip', () => {
  for (const filename of V3_FILES) {
    it(`preserves every v3 top-level key for ${filename}`, () => {
      if (!existsSync(join(V3_EXAMPLES_DIR, filename))) return;
      const src = loadV3(filename);
      const out = migratePayload(src, { migratedAt: PINNED_TS });
      expect(out.payload_schema_version).toBe('4.0');
      for (const key of Object.keys(src)) {
        if (key === 'payload_schema_version') continue;
        expect(out[key]).toBeDefined();
      }
    });
  }

  for (const filename of V3_FILES) {
    if (V3_FILES_STRICT_EXEMPT.has(filename)) continue;
    it(`migrated ${filename} validates strict v4 payload schema`, async () => {
      if (!existsSync(join(V3_EXAMPLES_DIR, filename))) return;
      const src = loadV3(filename);
      const out = migratePayload(src, { migratedAt: PINNED_TS });
      const errors = await validateIterErrors(out, {
        strict: true,
        target: 'payload',
      });
      expect(errors).toEqual([]);
    });
  }
});

// -- no PII / no secret-like fields introduced ------------------------------

describe('migrator structural safety', () => {
  it('does not synthesize any secret-looking keys', () => {
    const out = migratePayload(
      { payload_schema_version: '3.4', identity: { name: 'x' } },
      { migratedAt: PINNED_TS },
    );
    const forbidden = ['password', 'passphrase', 'secret', 'api_key', 'token'];
    const srcKeys = new Set(['payload_schema_version', 'identity']);
    const extra = Object.fromEntries(
      Object.entries(out).filter(([k]) => !srcKeys.has(k)),
    );
    function walk(obj: unknown): void {
      if (obj && typeof obj === 'object' && !Array.isArray(obj)) {
        for (const [k, v] of Object.entries(obj as Record<string, unknown>)) {
          const low = k.toLowerCase();
          for (const needle of forbidden) {
            expect(low.includes(needle)).toBe(false);
          }
          walk(v);
        }
      } else if (Array.isArray(obj)) {
        obj.forEach(walk);
      }
    }
    walk(extra);
  });
});
