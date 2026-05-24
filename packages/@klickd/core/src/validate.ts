// .klickd v4 — strict / preview JSON-Schema validation (TypeScript)
// SPDX-License-Identifier: CC0-1.0
//
// P0-4 (SDK TypeScript v4 GA alignment): mirrors the Python SDK's
// `validate(payload, strict=..., target=...)` and `validate_iter_errors`
// surface against the bundled v4 schemas:
//
//   - klickd-payload-v4.schema.json         (strict GA candidate, P0-2)
//   - klickd-payload-v4-preview.schema.json (permissive v4 preview)
//   - klickd-v4.schema.json                 (unified strict GA)
//   - klickd-v4-preview.schema.json         (unified preview)
//
// Validation is OPTIONAL: `ajv` is an optional peer dependency. Callers
// who do not invoke `validate()` continue to work with only the v3
// envelope crypto deps. Round-trip preservation (SPEC.md §33.7) is the
// canonical forward-compat contract — validation does not modify the
// payload.

import payloadStrict from './schemas/klickd-payload-v4.schema.json' with { type: 'json' };
import payloadPreview from './schemas/klickd-payload-v4-preview.schema.json' with { type: 'json' };
import unifiedStrict from './schemas/klickd-v4.schema.json' with { type: 'json' };
import unifiedPreview from './schemas/klickd-v4-preview.schema.json' with { type: 'json' };

import { KlickdError, HTTP_STATUS } from './errors.js';

export type ValidationTarget = 'payload' | 'unified';

export interface ValidateOptions {
  /** True (default) = v4 GA strict schema; false = permissive preview. */
  strict?: boolean;
  /**
   * "payload" (default) validates the inner payload schema.
   * "unified" validates against the unified envelope+payload schema.
   */
  target?: ValidationTarget;
}

export interface ValidationIssue {
  /** JSON-pointer-like path ("" / "<root>" when at root). */
  path: string;
  /** Validator-produced human-readable message. */
  message: string;
}

const SCHEMAS = {
  'payload-strict': payloadStrict as Record<string, unknown>,
  'payload-preview': payloadPreview as Record<string, unknown>,
  'unified-strict': unifiedStrict as Record<string, unknown>,
  'unified-preview': unifiedPreview as Record<string, unknown>,
} as const;

type SchemaKey = keyof typeof SCHEMAS;

/**
 * Return a parsed copy of one of the four bundled v4 schemas. Provides the
 * same affordance as Python `klickd.validate._load_schema` — useful for
 * tooling that wants to introspect the bundled JSON without reaching back
 * into the repo.
 */
export function getBundledSchema(key: SchemaKey): Record<string, unknown> {
  const s = SCHEMAS[key];
  if (!s) {
    throw new Error(`Unknown schema key: ${String(key)}`);
  }
  // Deep clone so callers can mutate freely.
  return JSON.parse(JSON.stringify(s)) as Record<string, unknown>;
}

/** List of bundled schema keys (parity with Python `_SCHEMA_FILES`). */
export function listBundledSchemas(): SchemaKey[] {
  return Object.keys(SCHEMAS) as SchemaKey[];
}

// Lazy Ajv import + per-key validator cache. Ajv 2020 is the entry point
// for Draft 2020-12, which is what these schemas declare.
type ValidatorFn = ((data: unknown) => boolean) & {
  errors?: Array<{ instancePath?: string; schemaPath?: string; message?: string }> | null;
};

interface AjvBundle {
  validators: Map<SchemaKey, ValidatorFn>;
}

let ajvBundle: AjvBundle | null = null;

async function getAjv(): Promise<AjvBundle> {
  if (ajvBundle) return ajvBundle;

  let AjvCtor: new (opts?: Record<string, unknown>) => {
    addSchema: (s: unknown, key?: string) => unknown;
    compile: (s: unknown) => ValidatorFn;
    getSchema: (id: string) => ValidatorFn | undefined;
  };
  try {
    const mod = await import('ajv/dist/2020.js');
    AjvCtor = (mod as { default?: typeof AjvCtor }).default ?? (mod as unknown as typeof AjvCtor);
  } catch (e) {
    throw new KlickdError(
      'KLICKD_E_SCHEMA',
      "validate() requires the optional 'ajv' dependency (>=8.12, Draft 2020-12). " +
        "Install it with: npm install ajv",
      HTTP_STATUS['KLICKD_E_SCHEMA'],
    );
  }

  // strict:false → tolerate unknown formats (e.g. "date-time") and unknown
  // keywords. Our schemas use a small custom vocabulary that Ajv's strict
  // mode would otherwise warn about; the runtime check itself is unaffected.
  const ajv = new AjvCtor({ allErrors: true, strict: false, validateFormats: false });

  // Register all four schemas first so cross-schema $ref resolves locally
  // (parity with the Python `referencing.Registry` setup).
  for (const key of listBundledSchemas()) {
    ajv.addSchema(SCHEMAS[key], `klickd:${key}`);
  }

  const validators = new Map<SchemaKey, ValidatorFn>();
  for (const key of listBundledSchemas()) {
    validators.set(key, ajv.compile(SCHEMAS[key]));
  }

  ajvBundle = { validators };
  return ajvBundle;
}

function keyFor(target: ValidationTarget, strict: boolean): SchemaKey {
  return `${target}-${strict ? 'strict' : 'preview'}` as SchemaKey;
}

function formatPath(instancePath: string | undefined): string {
  if (!instancePath || instancePath === '') return '<root>';
  // Ajv yields RFC 6901 JSON pointer ("/foo/0/bar"). Strip leading "/".
  return instancePath.replace(/^\//, '');
}

/**
 * Validate a .klickd payload (or unified envelope+payload) against the v4
 * JSON schema bundled with this package. Throws KlickdError(KLICKD_E_SCHEMA)
 * on validation failure or when the optional `ajv` peer is missing.
 *
 * Mirrors Python `klickd.validate`. See packages/pypi/klickd/src/klickd/validate.py.
 */
export async function validate(
  payload: unknown,
  options: ValidateOptions = {},
): Promise<void> {
  const strict = options.strict ?? true;
  const target = options.target ?? 'payload';
  if (target !== 'payload' && target !== 'unified') {
    throw new Error(`target must be 'payload' or 'unified', got ${String(target)}`);
  }

  const { validators } = await getAjv();
  const validator = validators.get(keyFor(target, strict));
  if (!validator) {
    throw new Error(`No bundled validator for ${target}-${strict ? 'strict' : 'preview'}`);
  }

  if (validator(payload)) return;

  const errors = validator.errors ?? [];
  const summary = errors
    .slice(0, 8)
    .map((e) => `${formatPath(e.instancePath)}: ${(e.message ?? '').slice(0, 200)}`);
  const extra = errors.length > 8 ? ` (+${errors.length - 8} more)` : '';
  throw new KlickdError(
    'KLICKD_E_SCHEMA',
    `v4 ${strict ? 'strict' : 'preview'} ${target} validation failed${extra}: ${summary.join(' | ')}`,
    HTTP_STATUS['KLICKD_E_SCHEMA'],
  );
}

/**
 * Non-throwing variant. Returns an array of {path, message} issues — empty
 * when the payload is valid. Mirrors Python `validate_iter_errors`.
 */
export async function validateIterErrors(
  payload: unknown,
  options: ValidateOptions = {},
): Promise<ValidationIssue[]> {
  const strict = options.strict ?? true;
  const target = options.target ?? 'payload';
  if (target !== 'payload' && target !== 'unified') {
    throw new Error(`target must be 'payload' or 'unified', got ${String(target)}`);
  }

  const { validators } = await getAjv();
  const validator = validators.get(keyFor(target, strict));
  if (!validator) {
    throw new Error(`No bundled validator for ${target}-${strict ? 'strict' : 'preview'}`);
  }

  if (validator(payload)) return [];
  return (validator.errors ?? []).map((e) => ({
    path: formatPath(e.instancePath),
    message: e.message ?? '',
  }));
}
