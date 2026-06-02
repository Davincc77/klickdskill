#!/usr/bin/env python3
"""Scan benchmark artifacts (and any given paths) for leaked secrets.

Defensive secret-safety gate for the Continuity-Hell v1 / coding-200 harness.
Provider API keys live ONLY in the private environment / a secret manager —
never committed, never in logs, never in results/artifacts. This script is a
CI-friendly check that those artifacts are secret-clean: it reuses the
benchmark's own ``secret_guard`` definitions so "what a secret looks like" is
defined in exactly one place.

What it does:
  - walk the target paths (default: the benchmark results/ dir);
  - read each text-ish file and scan for provider-key shapes, auth headers,
    high-entropy tokens, and any *live* provider env var value present in the
    current environment;
  - print a deterministic, sorted report of findings using REDACTED previews
    only — the secret itself is never printed;
  - exit non-zero if any finding is detected, so CI fails loudly.

It NEVER prints a secret value: every finding shows ``[REDACTED:<kind>]``.

Usage:
    python scripts/check_benchmark_secret_leakage.py
    python scripts/check_benchmark_secret_leakage.py path/to/dir other/file.json

Exit codes:
  0  no findings (artifacts are secret-clean)
  1  one or more secret findings
  2  a target path does not exist
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
BENCH = REPO_ROOT / "benchmarks" / "continuity-hell-v1" / "coding-200"
DEFAULT_TARGETS = (BENCH / "results",)

# Reuse the single source of truth for secret detection / redaction.
sys.path.insert(0, str(BENCH))
import secret_guard  # noqa: E402

# File suffixes worth scanning as text. Binary blobs are skipped.
_TEXT_SUFFIXES = {".json", ".md", ".txt", ".log", ".jsonl", ".csv", ".yaml",
                  ".yml", ".py", ".diff", ".patch", ""}


def iter_files(targets: list[Path]) -> list[Path]:
    files: list[Path] = []
    for t in targets:
        if t.is_dir():
            files.extend(p for p in t.rglob("*") if p.is_file())
        elif t.is_file():
            files.append(t)
    return sorted(set(files))


def scan_paths(targets: list[Path]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for path in iter_files(targets):
        if path.suffix.lower() not in _TEXT_SUFFIXES:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for f in secret_guard.scan_text(text):
            rec = dict(f)
            rec["file"] = str(path.relative_to(REPO_ROOT)) if path.is_relative_to(REPO_ROOT) else str(path)
            findings.append(rec)
    findings.sort(key=lambda r: (r["file"], r["kind"]))
    return findings


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="*",
                    help="files/dirs to scan (default: benchmark results/ dir)")
    args = ap.parse_args(argv)

    targets = [Path(p) for p in args.paths] if args.paths else list(DEFAULT_TARGETS)
    for t in targets:
        if not t.exists():
            print(f"ERROR: path does not exist: {t}", file=sys.stderr)
            return 2

    findings = scan_paths(targets)
    if findings:
        print(f"SECRET LEAKAGE DETECTED: {len(findings)} finding(s) (values redacted):",
              file=sys.stderr)
        for f in findings:
            print(f"  {f['file']}: {f['kind']} -> {f['preview']}", file=sys.stderr)
        return 1
    print(f"OK: scanned {len(iter_files(targets))} file(s); no secret leakage detected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
