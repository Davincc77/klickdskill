// @klickd/core — x.klickd v4.1 skill-pack helper
// SPDX-License-Identifier: CC0-1.0
//
// The 42 x.klickd v4.1 candidate skill packs (8 Lite + 34 Pro) ship as
// package data under the `x-klickd-skills/` directory at the package root,
// alongside the aggregated download index `manifest.json`. They are
// NON-NORMATIVE and NOT a v4.1 GA release (see
// examples/v4.1/x-klickd-skills/README.md in the source repository).
//
// These are JSON `.klickd` artifacts, not native skills in any assistant.
// A pack is only "used" once its bytes have been loaded and hash-verified
// against the manifest (or a host runtime has otherwise integrated it).
// `loadXKlickdSkillPack` returns `artifact_loaded: true` only after that
// load + SHA-256 step has completed in-process.

import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { existsSync, readFileSync, readdirSync } from 'node:fs';
import { createHash } from 'node:crypto';

export interface XKlickdSkillPackEntry {
  tier: string;
  pack: string;
  file: string;
  relative_path: string;
  bytes: number;
  sha256_file: string;
  status: string;
  [key: string]: unknown;
}

export interface XKlickdSkillManifest {
  manifest_version: string;
  kind: string;
  non_normative: boolean;
  claims_v41_ga: boolean;
  total_count: number;
  tiers: Record<string, { expected_count: number; actual_count: number }>;
  packs: XKlickdSkillPackEntry[];
  [key: string]: unknown;
}

export interface XKlickdSkillGateSummary {
  id?: string;
  action_class?: string;
  level?: string;
  reason?: string;
  [key: string]: unknown;
}

export interface XKlickdSkillPackSummary {
  /**
   * True only after the artifact bytes were read and their SHA-256 was
   * computed in-process. A pack is not "used" until this is true.
   */
  artifact_loaded: true;
  id: string;
  tier: string | null;
  file: string;
  pack: string | null;
  pack_version: string | null;
  bytes: number;
  sha256: string;
  sha256_matches_manifest: boolean;
  klickd_version: string | null;
  payload_schema_version: string | null;
  domain: string | null;
  profile_kind: string | null;
  competency_ids: string[];
  gates: XKlickdSkillGateSummary[];
  evidence_policy: Record<string, unknown> | null;
  human_authority: Record<string, unknown> | null;
  human_veto: Record<string, unknown> | null;
}

// Resolve the directory of the running module in a way that works for both
// the CommonJS and ESM builds produced by tsup. (Same probe as
// starter-skills.ts: `import.meta.url` is rewritten to an empty object in
// the CJS bundle, and `__dirname` is undefined in the ESM bundle.)
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
    '@klickd/core: unable to resolve module directory for x-klickd-skills',
  );
}

function skillsDir(): string {
  const here = moduleDir();
  const candidates = [
    join(here, '..', 'x-klickd-skills'),
    join(here, 'x-klickd-skills'),
  ];
  for (const candidate of candidates) {
    if (existsSync(candidate)) {
      return candidate;
    }
  }
  return candidates[0];
}

export function getXKlickdSkillsDir(): string {
  return skillsDir();
}

export function getXKlickdSkillsManifest(): XKlickdSkillManifest {
  const raw = readFileSync(join(skillsDir(), 'manifest.json'), 'utf8');
  return JSON.parse(raw) as XKlickdSkillManifest;
}

/**
 * List the 42 skill-pack manifest entries. The manifest is authoritative for
 * tier, pack id, byte length, and expected SHA-256.
 */
export function listXKlickdSkillPacks(): XKlickdSkillPackEntry[] {
  return getXKlickdSkillsManifest().packs;
}

function manifestEntryFor(
  idOrFilenameOrPack: string,
): XKlickdSkillPackEntry | undefined {
  const packs = listXKlickdSkillPacks();
  const needle = idOrFilenameOrPack.trim();
  // Match by file name, full pack id (x.klickd/foo), or bare id (foo / foo-bar).
  return packs.find((p) => {
    if (p.file === needle) return true;
    if (p.pack === needle) return true;
    const bareFromPack = p.pack.split('/').pop();
    const bareFromFile = p.file.replace(/\.klickd$/, '');
    const normNeedle = needle.replace(/\.klickd$/, '');
    return (
      bareFromPack === normNeedle ||
      bareFromFile === normNeedle ||
      bareFromPack === normNeedle.replace(/-/g, '_') ||
      bareFromFile === normNeedle.replace(/_/g, '-')
    );
  });
}

/**
 * Return the raw bytes of a bundled skill pack by file name, full pack id
 * (`x.klickd/work_assistant`), or bare id (`work-assistant` / `work_assistant`).
 */
export function getXKlickdSkillPackBytes(
  idOrFilenameOrPack: string,
): Uint8Array {
  const entry = manifestEntryFor(idOrFilenameOrPack);
  if (!entry) {
    throw new Error(
      `unknown x.klickd skill pack: ${idOrFilenameOrPack} (see listXKlickdSkillPacks())`,
    );
  }
  const { file } = entry;
  if (file.includes('/') || file.includes('\\') || file.includes('..')) {
    throw new Error(`invalid x.klickd skill pack file: ${file}`);
  }
  return new Uint8Array(readFileSync(join(skillsDir(), file)));
}

function asRecord(value: unknown): Record<string, unknown> | null {
  return value && typeof value === 'object' && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : null;
}

/**
 * Load a skill pack, hash-verify it against the manifest, and return a JSON
 * summary. The returned `artifact_loaded: true` asserts only that the bytes
 * were read and hashed in-process — it does NOT mean any AI assistant has
 * natively adopted the pack. Always check `sha256_matches_manifest`.
 */
export function loadXKlickdSkillPack(
  idOrFilenameOrPack: string,
): XKlickdSkillPackSummary {
  const entry = manifestEntryFor(idOrFilenameOrPack);
  if (!entry) {
    throw new Error(
      `unknown x.klickd skill pack: ${idOrFilenameOrPack} (see listXKlickdSkillPacks())`,
    );
  }
  const bytes = getXKlickdSkillPackBytes(entry.file);
  const sha256 = createHash('sha256').update(bytes).digest('hex');
  const payload = JSON.parse(new TextDecoder().decode(bytes)) as Record<
    string,
    unknown
  >;
  const pack = asRecord(payload.x_klickd_pack) ?? {};
  const compactIndex = asRecord(pack.compact_index) ?? {};

  const competencyIds: string[] = Array.isArray(compactIndex.competency_ids)
    ? (compactIndex.competency_ids as unknown[]).map((x) => String(x))
    : Array.isArray(pack.competencies)
      ? (pack.competencies as Array<Record<string, unknown>>)
          .map((c) => (c && c.competency_ref ? String(c.competency_ref) : ''))
          .filter(Boolean)
      : [];

  const verificationGates = asRecord(pack.verification_gates);
  const gates: XKlickdSkillGateSummary[] = verificationGates
    && Array.isArray(verificationGates.gates)
    ? (verificationGates.gates as XKlickdSkillGateSummary[])
    : Array.isArray(compactIndex.gate_summaries)
      ? (compactIndex.gate_summaries as XKlickdSkillGateSummary[])
      : [];

  return {
    artifact_loaded: true,
    id: entry.pack,
    tier: typeof entry.tier === 'string' ? entry.tier : null,
    file: entry.file,
    pack: typeof pack.pack === 'string' ? (pack.pack as string) : null,
    pack_version:
      typeof pack.pack_version === 'string'
        ? (pack.pack_version as string)
        : null,
    bytes: bytes.byteLength,
    sha256,
    sha256_matches_manifest: sha256 === entry.sha256_file,
    klickd_version:
      typeof payload.klickd_version === 'string'
        ? (payload.klickd_version as string)
        : null,
    payload_schema_version:
      typeof payload.payload_schema_version === 'string'
        ? (payload.payload_schema_version as string)
        : null,
    domain: typeof payload.domain === 'string' ? (payload.domain as string) : null,
    profile_kind:
      typeof payload.profile_kind === 'string'
        ? (payload.profile_kind as string)
        : null,
    competency_ids: competencyIds,
    gates,
    evidence_policy: asRecord(pack.evidence_policy),
    human_authority: asRecord(pack.human_authority),
    human_veto: asRecord(pack.human_veto),
  };
}
