// @klickd/core — starter skill helper
// SPDX-License-Identifier: CC0-1.0
//
// The four v4.0-envelope starter .klickd skills ship as package data under
// the `starter-skills/` directory at the package root. They are non-normative
// (see examples/v4/starter-skills/README.md in the source repository).

import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { existsSync, readFileSync, readdirSync } from 'node:fs';

export interface StarterSkillEntry {
  id: string;
  file: string;
  pack_version: string;
  bytes: number;
  sha256_file: string;
  sha256_canonical_json: string;
}

export interface StarterSkillManifest {
  manifest_version: string;
  kind: string;
  non_normative: boolean;
  claims_v41_ga: boolean;
  packs: StarterSkillEntry[];
  [key: string]: unknown;
}

// Resolve the directory of the running module in a way that works for both
// the CommonJS and ESM builds produced by tsup. In the CJS bundle
// `import.meta.url` is rewritten to an empty object and would cause
// `fileURLToPath(undefined)` to throw `ERR_INVALID_ARG_TYPE`; in the ESM
// bundle `__dirname` is not defined. We probe each one in turn.
function moduleDir(): string {
  if (typeof __dirname !== 'undefined') {
    return __dirname;
  }
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const metaUrl: string | undefined = (import.meta as any)?.url;
  if (typeof metaUrl === 'string' && metaUrl.length > 0) {
    return dirname(fileURLToPath(metaUrl));
  }
  throw new Error(
    '@klickd/core: unable to resolve module directory for starter-skills',
  );
}

function starterSkillsDir(): string {
  const here = moduleDir();
  // The compiled entry lives in `dist/`; starter skills are at the package
  // root in `starter-skills/`. If a downstream consumer reorganises the
  // layout (e.g. flattens `dist/`), fall back to a sibling lookup so the
  // helper still resolves.
  const candidates = [
    join(here, '..', 'starter-skills'),
    join(here, 'starter-skills'),
  ];
  for (const candidate of candidates) {
    if (existsSync(candidate)) {
      return candidate;
    }
  }
  return candidates[0];
}

export function getStarterSkillsDir(): string {
  return starterSkillsDir();
}

export function listStarterSkills(): string[] {
  return readdirSync(starterSkillsDir())
    .filter((name) => name.endsWith('.klickd'))
    .sort();
}

export function getStarterSkillBytes(name: string): Uint8Array {
  if (!name.endsWith('.klickd')) {
    throw new Error(`starter skill name must end with .klickd: ${name}`);
  }
  if (name.includes('/') || name.includes('\\') || name.includes('..')) {
    throw new Error(`invalid starter skill name: ${name}`);
  }
  return new Uint8Array(readFileSync(join(starterSkillsDir(), name)));
}

export function getStarterSkillsManifest(): StarterSkillManifest {
  const raw = readFileSync(join(starterSkillsDir(), 'manifest.json'), 'utf8');
  return JSON.parse(raw) as StarterSkillManifest;
}
