// @klickd/core — x.klickd v4.1 skill-pack inclusion test
// SPDX-License-Identifier: CC0-1.0

import { createHash } from 'node:crypto';
import {
  listXKlickdSkillPacks,
  getXKlickdSkillPackBytes,
  getXKlickdSkillsManifest,
  getXKlickdSkillsDir,
  loadXKlickdSkillPack,
} from '../index.js';

describe('bundled x.klickd v4.1 skill packs', () => {
  it('exposes a 42-pack manifest (8 Lite + 34 Pro)', () => {
    const manifest = getXKlickdSkillsManifest();
    expect(manifest.non_normative).toBe(true);
    expect(manifest.claims_v41_ga).toBe(false);
    expect(manifest.total_count).toBe(42);
    expect(manifest.packs.length).toBe(42);
    const lite = manifest.packs.filter((p) => p.tier === 'lite');
    const pro = manifest.packs.filter((p) => p.tier === 'pro');
    expect(lite.length).toBe(8);
    expect(pro.length).toBe(34);
  });

  it('every bundled pack hash matches the manifest', () => {
    for (const pack of listXKlickdSkillPacks()) {
      const bytes = getXKlickdSkillPackBytes(pack.file);
      const hash = createHash('sha256').update(bytes).digest('hex');
      expect(hash).toBe(pack.sha256_file);
      expect(bytes.byteLength).toBe(pack.bytes);
    }
  });

  it('resolves packs by file name, full pack id, and bare id', () => {
    const byFile = loadXKlickdSkillPack('work-assistant.klickd');
    const byPack = loadXKlickdSkillPack('x.klickd/work_assistant');
    const byBare = loadXKlickdSkillPack('work-assistant');
    expect(byFile.sha256).toBe(byPack.sha256);
    expect(byPack.sha256).toBe(byBare.sha256);
  });

  it('loadXKlickdSkillPack reports artifact_loaded and a verified hash', () => {
    const summary = loadXKlickdSkillPack('llm-agent-engineering');
    expect(summary.artifact_loaded).toBe(true);
    expect(summary.sha256_matches_manifest).toBe(true);
    expect(summary.tier).toBe('pro');
    expect(summary.pack).toBe('x.klickd/llm_agent_engineering');
    expect(summary.klickd_version).toBe('4.0');
    expect(summary.domain).toBe('software_engineering');
    expect(summary.profile_kind).toBe('carrier_competency_pack');
    expect(summary.competency_ids.length).toBeGreaterThan(0);
    expect(summary.gates.length).toBeGreaterThan(0);
    expect(summary.evidence_policy).not.toBeNull();
    expect(summary.human_authority).not.toBeNull();
  });

  it('rejects unknown packs and path traversal', () => {
    expect(() => getXKlickdSkillPackBytes('../package.json')).toThrow();
    expect(() => getXKlickdSkillPackBytes('does-not-exist')).toThrow();
    expect(() => loadXKlickdSkillPack('nope')).toThrow();
  });

  it('returns a directory path that exists', () => {
    const dir = getXKlickdSkillsDir();
    expect(typeof dir).toBe('string');
    expect(dir.length).toBeGreaterThan(0);
  });
});
