#!/usr/bin/env python3
"""Wrapper script — RFC-003 context-cost dry-run, driven for the Hermes POC.

This script is **local-only**:

- No network access.
- No provider API calls.
- No paid resources.

It runs `benchmarks/context_cost/runner.py --check`, then (unless ``--check``
is passed) the full dry-run, then prints the summary paths.

The wrapper works **without** Hermes — it just shells out to the existing
local runner. The Hermes skill in ``../skill/SKILL.md`` is what invokes this
from inside a Hermes session.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

# Resolve the repo root from this file's location:
#   integrations/hermes/scripts/run_context_cost_benchmark.py -> repo root is 3 levels up.
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
RUNNER = REPO_ROOT / "benchmarks" / "context_cost" / "runner.py"
RESULTS_ROOT = REPO_ROOT / "benchmarks" / "context_cost" / "results"


def _invoke_runner(args: list[str]) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, str(RUNNER), *args]
    return subprocess.run(  # noqa: S603 — local runner, no shell
        cmd,
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )


def _print_step(label: str, result: subprocess.CompletedProcess[str]) -> None:
    sys.stdout.write(f"[hermes-poc] {label}: exit={result.returncode}\n")
    if result.stdout:
        sys.stdout.write(result.stdout)
        if not result.stdout.endswith("\n"):
            sys.stdout.write("\n")
    if result.stderr:
        sys.stderr.write(result.stderr)
        if not result.stderr.endswith("\n"):
            sys.stderr.write("\n")


def _print_summary_paths() -> None:
    """Print the paths of the most recent dated results directory, if any."""
    if not RESULTS_ROOT.is_dir():
        sys.stdout.write(
            "[hermes-poc] no results directory yet — was the run skipped?\n"
        )
        return

    dated = sorted(
        (p for p in RESULTS_ROOT.iterdir() if p.is_dir()),
        reverse=True,
    )
    if not dated:
        sys.stdout.write("[hermes-poc] results root exists but is empty\n")
        return

    latest = dated[0]
    sys.stdout.write(f"[hermes-poc] latest results dir: {latest}\n")
    expected = ["report.md", "summary.csv", "raw_runs.jsonl"]
    for name in expected:
        path = latest / name
        marker = "OK" if path.is_file() else "MISSING"
        sys.stdout.write(f"[hermes-poc]   {marker}: {path}\n")

    artifacts = latest / "artifacts"
    if artifacts.is_dir():
        sys.stdout.write(f"[hermes-poc]   OK: {artifacts}\n")
        for child in sorted(artifacts.iterdir()):
            sys.stdout.write(f"[hermes-poc]     - {child.name}\n")
    else:
        sys.stdout.write(f"[hermes-poc]   MISSING: {artifacts}\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Hermes POC wrapper around benchmarks/context_cost/runner.py. "
            "Local dry-run only — no provider API calls, no paid resources."
        )
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Only validate fixtures (runner.py --check); do not write results.",
    )
    args = parser.parse_args(argv)

    if not RUNNER.is_file():
        sys.stderr.write(f"[hermes-poc] runner not found: {RUNNER}\n")
        return 1

    sys.stdout.write(
        "[hermes-poc] dry-run only — no provider API calls, no paid resources.\n"
    )

    check_result = _invoke_runner(["--check"])
    _print_step("fixture check", check_result)
    if check_result.returncode != 0:
        return check_result.returncode

    if args.check:
        sys.stdout.write("[hermes-poc] --check passed; skipping full dry-run.\n")
        return 0

    run_result = _invoke_runner([])
    _print_step("full dry-run", run_result)
    if run_result.returncode != 0:
        return run_result.returncode

    _print_summary_paths()
    sys.stdout.write(
        "[hermes-poc] done. NOTE: token-proxy values are a whitespace "
        "approximation, NOT provider tokens.\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
