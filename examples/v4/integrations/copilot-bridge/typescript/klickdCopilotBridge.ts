#!/usr/bin/env node
// klickd-copilot-bridge — TypeScript CLI pre-step for GitHub / M365 Copilot.
//
// Mirror of the Python CLI in `../python/klickd_copilot_bridge.py`.
// Reads a `.klickd` v4 profile from disk, decrypts it locally if
// encrypted (passphrase prompted from a TTY), runs it through the
// schema-tolerant context builder, and writes a sanitized
// system/context block to stdout or a file.
//
// API: uses `loadKlickd` from `@klickd/core` v4 — the v4 GA name.
// (The retired v3 name `decryptKlickd` is NOT used.)
//
// Security properties:
//   * No network I/O — never calls Copilot, OpenAI, Anthropic, etc.
//   * Passphrase is read interactively from the TTY only; the script
//     refuses to read it from `--passphrase`, env vars, or stdin pipes.
//   * Decrypted payload lives only in RAM for the duration of the call.
//
// SPDX-License-Identifier: CC0-1.0

import { readFileSync, writeFileSync } from 'node:fs';
import { argv, exit, stdin, stdout, stderr } from 'node:process';
import * as readline from 'node:readline';
import { loadKlickd } from '@klickd/core';
import { buildContextBlock, type KlickdRecord } from './contextBuilder.js';

interface CliArgs {
  path: string;
  out: string | null;
  dryRun: boolean;
}

function parseArgs(rawArgs: string[]): CliArgs {
  const args: CliArgs = { path: '', out: null, dryRun: false };
  const positional: string[] = [];
  for (let i = 0; i < rawArgs.length; i++) {
    const a = rawArgs[i];
    if (a === '--out') {
      args.out = rawArgs[++i] ?? null;
      if (args.out === null) throw new Error('--out requires a path argument');
    } else if (a === '--dry-run') {
      args.dryRun = true;
    } else if (a === '-h' || a === '--help') {
      printHelp();
      exit(0);
    } else if (a.startsWith('--')) {
      throw new Error(`unknown flag: ${a}`);
    } else {
      positional.push(a);
    }
  }
  if (positional.length !== 1) {
    throw new Error('expected exactly one positional argument: path to .klickd profile');
  }
  args.path = positional[0];
  return args;
}

function printHelp(): void {
  stdout.write(
    `klickd-copilot-bridge — export a sanitized .klickd system block for Copilot

Usage:
  klickd-copilot-bridge <path> [--out FILE] [--dry-run]

Options:
  --out FILE   Write the context block to FILE instead of stdout.
  --dry-run    Skip decryption; emit a block built from envelope-level
               fields only (no passphrase prompt).
  -h, --help   Show this help.

Notes:
  * The passphrase is read interactively from the TTY only. There is no
    --passphrase flag and no env var support, by design.
  * No network calls. Use the output via clipboard or a VS Code
    extension to inject it into a Copilot Chat session.
`,
  );
}

function readEnvelope(path: string): { envelope: KlickdRecord; raw: Uint8Array } {
  const raw = readFileSync(path);
  let envelope: unknown;
  try {
    envelope = JSON.parse(raw.toString('utf-8'));
  } catch (exc) {
    throw new Error(`${path} is not valid UTF-8 JSON: ${(exc as Error).message}`);
  }
  if (typeof envelope !== 'object' || envelope === null || Array.isArray(envelope)) {
    throw new Error(`top-level JSON in ${path} must be an object`);
  }
  return { envelope: envelope as KlickdRecord, raw: new Uint8Array(raw) };
}

function isEncrypted(envelope: KlickdRecord): boolean {
  return envelope.encrypted === true || 'ciphertext' in envelope;
}

async function promptPassphrase(): Promise<string> {
  if (!stdin.isTTY) {
    throw new Error(
      'encrypted profile requires a passphrase, but stdin is not a TTY. ' +
        'Run this script from an interactive terminal — this bridge ' +
        'intentionally refuses to read the passphrase from --passphrase, ' +
        'env vars, or piped stdin to avoid leaking it.',
    );
  }
  const rl = readline.createInterface({ input: stdin, output: stderr, terminal: true });
  // Best-effort echo suppression — Node's readline cannot disable echo
  // directly, so we toggle raw mode and consume keystrokes manually.
  return new Promise((resolve) => {
    stderr.write('Passphrase for .klickd profile (not echoed): ');
    let buf = '';
    const onData = (chunk: Buffer) => {
      for (const byte of chunk) {
        if (byte === 0x0a || byte === 0x0d) {
          stdin.setRawMode(false);
          stdin.removeListener('data', onData);
          stderr.write('\n');
          rl.close();
          resolve(buf);
          return;
        }
        if (byte === 0x7f || byte === 0x08) {
          buf = buf.slice(0, -1);
        } else if (byte >= 0x20) {
          buf += String.fromCharCode(byte);
        }
      }
    };
    stdin.setRawMode(true);
    stdin.resume();
    stdin.on('data', onData);
  });
}

async function loadPayload(path: string, dryRun: boolean): Promise<KlickdRecord> {
  const { envelope, raw } = readEnvelope(path);
  if (!isEncrypted(envelope)) return envelope;
  if (dryRun) {
    const stripped: KlickdRecord = {};
    for (const [k, v] of Object.entries(envelope)) {
      if (k !== 'ciphertext' && k !== 'kdf' && k !== 'cipher') stripped[k] = v;
    }
    if (!('user_preferences' in stripped)) {
      stripped.user_preferences =
        '[dry-run] encrypted payload not decoded; only envelope metadata shown.';
    }
    return stripped;
  }
  const passphrase = await promptPassphrase();
  const payload = await loadKlickd(raw, { passphrase });
  return payload as KlickdRecord;
}

async function main(): Promise<number> {
  let args: CliArgs;
  try {
    args = parseArgs(argv.slice(2));
  } catch (exc) {
    stderr.write(`ERROR: ${(exc as Error).message}\n`);
    printHelp();
    return 2;
  }

  let payload: KlickdRecord;
  try {
    payload = await loadPayload(args.path, args.dryRun);
  } catch (exc) {
    stderr.write(`ERROR: failed to load ${args.path}: ${(exc as Error).message}\n`);
    return 1;
  }

  const block = buildContextBlock(payload);
  if (args.out) {
    writeFileSync(args.out, block, { encoding: 'utf-8' });
    stderr.write(`# wrote ${block.length} chars of sanitized context to ${args.out}\n`);
  } else {
    stdout.write(block);
  }
  return 0;
}

main().then((code) => exit(code));
