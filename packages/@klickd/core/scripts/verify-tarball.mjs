#!/usr/bin/env node
// @klickd/core — packed-tarball smoke test
// SPDX-License-Identifier: CC0-1.0
//
// Builds, packs, and then installs the resulting tarball into two scratch
// projects (CJS and ESM) so we exercise the helper API the way real
// consumers will. This catches breakage that source-tree Jest cannot —
// for example: `import.meta.url` becoming undefined in the CJS build,
// JSON `import` attributes being stripped, or starter-skills not being
// shipped in the tarball.
//
// Usage:
//   node scripts/verify-tarball.mjs
//
// Exit status: 0 on success, non-zero on any failure.

import { execSync } from 'node:child_process';
import { existsSync, mkdtempSync, readFileSync, rmSync, writeFileSync, mkdirSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const pkgRoot = resolve(here, '..');

function run(cmd, opts = {}) {
  console.log(`$ ${cmd}`);
  return execSync(cmd, { stdio: 'inherit', ...opts });
}

function runCapture(cmd, opts = {}) {
  return execSync(cmd, { encoding: 'utf8', ...opts }).trim();
}

const expectedVersion = JSON.parse(
  readFileSync(join(pkgRoot, 'package.json'), 'utf8'),
).version;

console.log(`Verifying packed @klickd/core@${expectedVersion} tarball...`);

run('npm run build', { cwd: pkgRoot });
const tarballJson = runCapture('npm pack --json', { cwd: pkgRoot });
const packJson = JSON.parse(tarballJson);
const tarballName = packJson[0].filename.replace('@', '').replace('/', '-');
const tarballPath = join(pkgRoot, tarballName);
if (!existsSync(tarballPath)) {
  console.error(`expected tarball at ${tarballPath}, not found`);
  process.exit(1);
}
console.log(`packed: ${tarballPath}`);

const scratchRoot = mkdtempSync(join(tmpdir(), 'klickd-tarball-'));

const cjsScript = `
const k = require('@klickd/core');
const files = k.listStarterSkills();
const expected = ['coding.klickd','research.klickd','student.klickd','user.klickd'];
if (JSON.stringify(files) !== JSON.stringify(expected)) {
  throw new Error('CJS: unexpected starter skill list: ' + JSON.stringify(files));
}
const m = k.getStarterSkillsManifest();
if (m.packs.length !== 4) throw new Error('CJS: expected 4 manifest packs');
const bytes = k.getStarterSkillBytes('user.klickd');
if (!(bytes instanceof Uint8Array) || bytes.byteLength <= 0) {
  throw new Error('CJS: empty user.klickd');
}
if (k.listBundledSchemas().length !== 4) throw new Error('CJS: expected 4 schemas');
console.log('CJS smoke OK');
`;

const esmScript = `
import * as k from '@klickd/core';
const files = k.listStarterSkills();
const expected = ['coding.klickd','research.klickd','student.klickd','user.klickd'];
if (JSON.stringify(files) !== JSON.stringify(expected)) {
  throw new Error('ESM: unexpected starter skill list: ' + JSON.stringify(files));
}
const m = k.getStarterSkillsManifest();
if (m.packs.length !== 4) throw new Error('ESM: expected 4 manifest packs');
const bytes = k.getStarterSkillBytes('coding.klickd');
if (!(bytes instanceof Uint8Array) || bytes.byteLength <= 0) {
  throw new Error('ESM: empty coding.klickd');
}
if (k.listBundledSchemas().length !== 4) throw new Error('ESM: expected 4 schemas');
console.log('ESM smoke OK');
`;

let failed = false;

try {
  for (const mode of ['cjs', 'esm']) {
    const dir = join(scratchRoot, mode);
    mkdirSync(dir, { recursive: true });
    const pkg = { name: `klickd-${mode}-smoke`, version: '0.0.0', private: true };
    if (mode === 'esm') pkg.type = 'module';
    writeFileSync(join(dir, 'package.json'), JSON.stringify(pkg, null, 2));
    run(`npm install --silent ${tarballPath}`, { cwd: dir });

    const scriptName = mode === 'cjs' ? 'smoke.cjs' : 'smoke.mjs';
    writeFileSync(join(dir, scriptName), mode === 'cjs' ? cjsScript : esmScript);
    try {
      run(`node ${scriptName}`, { cwd: dir });
    } catch (e) {
      failed = true;
      console.error(`${mode.toUpperCase()} smoke FAILED`);
    }
  }
} finally {
  rmSync(scratchRoot, { recursive: true, force: true });
  rmSync(tarballPath, { force: true });
}

if (failed) {
  console.error('Tarball verification FAILED');
  process.exit(1);
}
console.log('Tarball verification OK (CJS + ESM)');
