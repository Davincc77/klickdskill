// .klickd v3.x → v4 GA payload migrator (TypeScript)
// SPDX-License-Identifier: CC0-1.0
//
// Implements the R4-P0-5 normative migrator contract documented at
// docs/spec/MIGRATION_V3_TO_V4.md. Cross-impl parity with
// packages/pypi/klickd/src/klickd/migrate.py.
//
// Pure / non-destructive / idempotent. Operates on the decrypted
// payload only — the encrypted wire envelope is left untouched.

import { KlickdError, HTTP_STATUS } from './errors.js';

const V3_SCHEMA_VERSIONS = new Set<string>([
  '3.0',
  '3.1',
  '3.2',
  '3.3',
  '3.4',
  '3.5',
]);
const V4_SCHEMA_VERSIONS = new Set<string>(['4.0', '4.0.0-preview.1']);

// Reserved profile_kind discriminator values per
// schemas/klickd-payload-v4.schema.json#/properties/profile_kind.
const RESERVED_PROFILE_KINDS = new Set<string>([
  'learner',
  'agent',
  'team',
  'robot',
  'creator',
]);

export interface MigrateOptions {
  /** Override the recorded source_version. Defaults to the input's
   *  payload_schema_version, or "3.x" when absent. */
  sourceVersion?: string;
  /** RFC 3339 UTC timestamp (must end with `Z`). Defaults to now().
   *  Tests SHOULD pin this for reproducibility. */
  migratedAt?: string;
  /** Default "learner" (v3.x is implicitly "learner"). */
  profileKind?: string;
  /** Optional pointer (URI / path) to a human-authored migration report. */
  migrationReportRef?: string;
  /** Optional pointer to a backup of the pre-migration file. */
  backupRef?: string;
}

export interface MigrationWarning {
  /** JSON-pointer-ish path; `<root>` for the top-level object. */
  path: string;
  /** Human-readable warning message. */
  message: string;
}

type JsonObject = Record<string, unknown>;

function isPlainObject(value: unknown): value is JsonObject {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function utcNowIso(): string {
  // Trim millisecond precision to match the v4 GA schema pattern
  // ^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z$ (millis allowed but
  // not required; we omit them for stable, comparable timestamps).
  const now = new Date();
  const pad = (n: number) => String(n).padStart(2, '0');
  return (
    `${now.getUTCFullYear()}-${pad(now.getUTCMonth() + 1)}-${pad(now.getUTCDate())}` +
    `T${pad(now.getUTCHours())}:${pad(now.getUTCMinutes())}:${pad(now.getUTCSeconds())}Z`
  );
}

function deepClone<T>(value: T): T {
  // structuredClone is available on Node >=17 and all modern browsers;
  // the @klickd/core package targets Node >=18 (see package.json).
  return structuredClone(value);
}

/**
 * Return true iff `payload` is a v3.x payload that should be lifted to v4 GA.
 *
 * Mirrors Python `needs_migration`.
 */
export function needsMigration(payload: unknown): boolean {
  if (!isPlainObject(payload)) return false;
  const ver = payload['payload_schema_version'];
  if (ver === undefined || ver === null) return true;
  if (typeof ver !== 'string') return false;
  if (V4_SCHEMA_VERSIONS.has(ver)) return false;
  if (V3_SCHEMA_VERSIONS.has(ver)) return true;
  return false;
}

/**
 * Lift a v3.x .klickd payload to the v4 GA payload shape.
 *
 * Pure: the input is never mutated; a structurally cloned result is
 * returned. Idempotent on already-v4 inputs (unchanged unless the caller
 * passes pointer refs).
 *
 * Throws `KlickdError(KLICKD_E_SCHEMA)` when the input is not a plain
 * object or carries an unrecognized `payload_schema_version`.
 */
export function migratePayload(
  payload: unknown,
  options: MigrateOptions = {},
): JsonObject {
  if (!isPlainObject(payload)) {
    throw new KlickdError(
      'KLICKD_E_SCHEMA',
      `migratePayload requires a plain object payload; got ${typeof payload}`,
      HTTP_STATUS['KLICKD_E_SCHEMA'],
    );
  }

  const incomingVersion = payload['payload_schema_version'];
  if (
    incomingVersion !== undefined &&
    typeof incomingVersion === 'string' &&
    !V3_SCHEMA_VERSIONS.has(incomingVersion) &&
    !V4_SCHEMA_VERSIONS.has(incomingVersion)
  ) {
    throw new KlickdError(
      'KLICKD_E_SCHEMA',
      `migratePayload does not recognize payload_schema_version=` +
        `${JSON.stringify(incomingVersion)}; expected v3.x (3.0..3.5) or ` +
        `v4 (4.0 / 4.0.0-preview.1)`,
      HTTP_STATUS['KLICKD_E_SCHEMA'],
    );
  }

  const out = deepClone(payload) as JsonObject;

  const {
    sourceVersion,
    migratedAt,
    profileKind = 'learner',
    migrationReportRef,
    backupRef,
  } = options;

  // R8 — already-v4 payloads round-trip unchanged unless pointer refs
  // are supplied (which we splice into the migration block).
  if (typeof incomingVersion === 'string' && V4_SCHEMA_VERSIONS.has(incomingVersion)) {
    if (migrationReportRef === undefined && backupRef === undefined) {
      return out;
    }
    const existing = isPlainObject(out['migration']) ? (out['migration'] as JsonObject) : {};
    if (migrationReportRef !== undefined) {
      existing['migration_report_ref'] = migrationReportRef;
    }
    if (backupRef !== undefined) {
      existing['backup_ref'] = backupRef;
    }
    if (existing['source_version'] === undefined) {
      existing['source_version'] = incomingVersion;
    }
    existing['migrated_at'] = migratedAt ?? utcNowIso();
    out['migration'] = existing;
    return out;
  }

  // R1 — stamp the payload version to the GA canonical value.
  out['payload_schema_version'] = '4.0';

  // R2 — default profile_kind when absent.
  if (out['profile_kind'] === undefined) {
    out['profile_kind'] = profileKind;
  }

  // R4 — record the migration provenance block.
  const migrationBlock: JsonObject = {
    source_version:
      sourceVersion ??
      (typeof incomingVersion === 'string' ? incomingVersion : '3.x'),
    migrated_at: migratedAt ?? utcNowIso(),
  };
  if (migrationReportRef !== undefined) {
    migrationBlock['migration_report_ref'] = migrationReportRef;
  }
  if (backupRef !== undefined) {
    migrationBlock['backup_ref'] = backupRef;
  }
  out['migration'] = migrationBlock;

  return out;
}

/**
 * Return manual-review warnings without mutating `payload`. Mirrors
 * Python `migrate_payload_iter_warnings`.
 */
export function migratePayloadIterWarnings(payload: unknown): MigrationWarning[] {
  const warnings: MigrationWarning[] = [];
  if (!isPlainObject(payload)) {
    warnings.push({ path: '<root>', message: 'payload is not a JSON object' });
    return warnings;
  }

  const ver = payload['payload_schema_version'];
  if (ver === undefined) {
    if (payload['domain_schema_version'] === undefined) {
      warnings.push({
        path: '<root>',
        message:
          'no payload_schema_version and no domain_schema_version; ' +
          'pin sourceVersion explicitly when migrating',
      });
    }
  } else if (
    typeof ver === 'string' &&
    !V3_SCHEMA_VERSIONS.has(ver) &&
    !V4_SCHEMA_VERSIONS.has(ver)
  ) {
    warnings.push({
      path: '/payload_schema_version',
      message: `unknown payload_schema_version ${JSON.stringify(ver)}; migrator will refuse`,
    });
  }

  const ctx = payload['context'];
  if (isPlainObject(ctx)) {
    const decisions = ctx['decisions_locked'];
    if (Array.isArray(decisions)) {
      decisions.forEach((d, i) => {
        if (typeof d === 'string' && d.length > 1024) {
          warnings.push({
            path: `/context/decisions_locked/${i}`,
            message: `entry exceeds 1024 chars (${d.length}); some readers will truncate`,
          });
        }
      });
    }
  }

  const ethics = payload['ethics'];
  const veto = payload['human_veto_policy'];
  if (isPlainObject(ethics) && isPlainObject(veto)) {
    const locked = ethics['locked_actions'];
    const appliesTo = veto['applies_to'];
    if (Array.isArray(locked) && Array.isArray(appliesTo)) {
      const lockedSet = new Set<string>(locked.filter((x): x is string => typeof x === 'string'));
      const overlap = appliesTo
        .filter((x): x is string => typeof x === 'string' && lockedSet.has(x))
        .sort();
      if (overlap.length > 0) {
        warnings.push({
          path: '/human_veto_policy/applies_to',
          message:
            'overlaps with /ethics/locked_actions: ' +
            overlap.map((x) => JSON.stringify(x)).join(', '),
        });
      }
    }
  }

  const pk = payload['profile_kind'];
  if (typeof pk === 'string' && !RESERVED_PROFILE_KINDS.has(pk)) {
    warnings.push({
      path: '/profile_kind',
      message: `non-reserved profile_kind ${JSON.stringify(pk)}; readers MAY treat as extension`,
    });
  }

  return warnings;
}
