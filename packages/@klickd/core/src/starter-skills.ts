// @klickd/core — starter skill helper
// SPDX-License-Identifier: CC0-1.0
//
// The four v4.0-envelope starter .klickd skills ship as package data under
// the `starter-skills/` directory at the package root. They are non-normative
// (see examples/v4/starter-skills/README.md in the source repository).

import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { readFileSync, readdirSync } from 'node:fs';

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

function starterSkillsDir(): string {
  const here = dirname(fileURLToPath(import.meta.url));
  return join(here, '..', 'starter-skills');
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
