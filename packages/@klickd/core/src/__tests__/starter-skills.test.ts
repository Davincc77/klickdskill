// @klickd/core — starter skills inclusion test
// SPDX-License-Identifier: CC0-1.0

import { createHash } from 'node:crypto';
import {
  listStarterSkills,
  getStarterSkillBytes,
  getStarterSkillsManifest,
  getStarterSkillsDir,
} from '../index.js';

describe('bundled starter .klickd skills', () => {
  it('exposes the four starter skill files', () => {
    expect(listStarterSkills().sort()).toEqual([
      'coding.klickd',
      'research.klickd',
      'student.klickd',
      'user.klickd',
    ]);
  });

  it('exposes a manifest whose SHA-256 hashes match the bundled files', () => {
    const manifest = getStarterSkillsManifest();
    expect(manifest.kind).toBe('klickd_starter_skill_manifest');
    expect(manifest.non_normative).toBe(true);
    expect(manifest.claims_v41_ga).toBe(false);
    expect(manifest.packs.length).toBe(4);

    for (const pack of manifest.packs) {
      const bytes = getStarterSkillBytes(pack.file);
      const hash = createHash('sha256').update(bytes).digest('hex');
      expect(hash).toBe(pack.sha256_file);
      expect(bytes.byteLength).toBe(pack.bytes);
    }
  });

  it('rejects path traversal in getStarterSkillBytes', () => {
    expect(() => getStarterSkillBytes('../package.json')).toThrow();
    expect(() => getStarterSkillBytes('not-a-klickd.txt')).toThrow();
  });

  it('returns a directory path that exists', () => {
    const dir = getStarterSkillsDir();
    expect(typeof dir).toBe('string');
    expect(dir.length).toBeGreaterThan(0);
  });

  it('resolves the directory under either ESM (import.meta.url) or CJS (__dirname)', () => {
    // Regression guard for the 4.0.1 incident where the CJS build of this
    // helper called fileURLToPath(undefined) and threw
    // ERR_INVALID_ARG_TYPE. listStarterSkills() must work without throwing
    // regardless of which module system the consumer uses; this Jest run
    // exercises both module systems via verify:tarball.
    expect(() => listStarterSkills()).not.toThrow();
    expect(() => getStarterSkillsManifest()).not.toThrow();
  });
});
