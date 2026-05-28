#!/usr/bin/env python3
"""x.klickd v4.1 benchmark runner — dry-run by default.

Modes:
    --dry-run   (default) Never calls an LLM. Validates fixtures and writes
                a planned-run manifest under results/.
    --pilot     Up to 10 users. Requires an LLM API key. If none set, falls
                back to a planned-run manifest.
    --full      Requires --confirm-full-run AND XKLICKD_BENCHMARK_FULL_APPROVED=1
                AND a pre-flight snapshot under results/snapshots/<date>/.

Token accounting is heuristic unless a provider returns usage. Heuristic counts
are labelled as such.

NEVER claims Mem0 compatibility. The mem0 condition is skipped unless a Mem0
local install or MEM0_API_KEY is detected, and even then the runner reports
it as `mem0_present=true` without asserting compatibility.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
FIXTURES_DIR = ROOT / "fixtures" / "generated"
RESULTS_ROOT = ROOT / "results"
SNAPSHOTS_ROOT = RESULTS_ROOT / "snapshots"

PILOT_MAX_USERS = 10
ENV_FULL_APPROVAL = "XKLICKD_BENCHMARK_FULL_APPROVED"
ENV_LLM_KEYS = ("LLM_API_KEY", "ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GROQ_API_KEY")
ENV_MEM0_KEY = "MEM0_API_KEY"


class RunnerError(RuntimeError):
    pass


def _utcnow_date() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d")


def _utcnow_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def llm_configured() -> bool:
    return any(os.environ.get(k) for k in ENV_LLM_KEYS)


def mem0_present() -> bool:
    if os.environ.get(ENV_MEM0_KEY):
        return True
    try:
        import importlib
        importlib.util.find_spec("mem0")  # type: ignore[attr-defined]
        return importlib.util.find_spec("mem0") is not None  # type: ignore[attr-defined]
    except Exception:
        return False


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def load_manifest(fixtures_dir: Path) -> dict[str, Any]:
    mpath = fixtures_dir / "manifest.json"
    if not mpath.exists():
        raise RunnerError(
            f"Missing fixture manifest at {mpath}. "
            f"Run: python -m benchmarks.v4_1.fixtures.generator"
        )
    return json.loads(mpath.read_text())


def filter_users(rows: list[dict[str, Any]], user_ids: set[str]) -> list[dict[str, Any]]:
    return [r for r in rows if r.get("user_id") in user_ids]


def planned_run_manifest(mode: str, fixtures_dir: Path, n_users: int,
                         reason: str) -> dict[str, Any]:
    manifest = load_manifest(fixtures_dir)
    return {
        "kind": "planned_run_manifest",
        "mode": mode,
        "reason_no_execution": reason,
        "timestamp_utc": _utcnow_iso(),
        "fixtures": manifest,
        "n_users_planned": n_users,
        "mem0": {
            "present": mem0_present(),
            "compatibility_claim": False,
            "_note": "This harness makes NO Mem0 compatibility claim.",
        },
        "llm_configured": llm_configured(),
        "conditions": {
            "test_a": ["no_klickd", "xklickd_lite", "xklickd_pro"],
            "test_b": ["no_memory", "prompt_history", "xklickd_compressed",
                       "mem0" if mem0_present() else "mem0_skipped"],
        },
        "token_accounting": "heuristic_unless_provider_reports",
    }


def write_results(out_dir: Path, name: str, payload: dict[str, Any]) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / name
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")
    return out_path


def cmd_dry_run(args: argparse.Namespace) -> int:
    fixtures_dir = args.fixtures
    manifest = load_manifest(fixtures_dir)
    personas = load_jsonl(fixtures_dir / manifest["files"]["personas"]["path"])
    test_a = load_jsonl(fixtures_dir / manifest["files"]["test_a_runs"]["path"])
    test_b = load_jsonl(fixtures_dir / manifest["files"]["test_b_sessions"]["path"])

    if len(personas) != manifest["counts"]["personas"]:
        raise RunnerError("Persona count mismatch vs manifest.")
    if len(test_a) != manifest["counts"]["test_a_runs"]:
        raise RunnerError("Test A count mismatch vs manifest.")
    if len(test_b) != manifest["counts"]["test_b_sessions"]:
        raise RunnerError("Test B count mismatch vs manifest.")

    out_dir = RESULTS_ROOT / _utcnow_date() / "dry_run"
    payload = planned_run_manifest(
        mode="dry_run",
        fixtures_dir=fixtures_dir,
        n_users=len(personas),
        reason="dry_run mode never calls a provider",
    )
    payload["counts_observed"] = {
        "personas": len(personas),
        "test_a_runs": len(test_a),
        "test_b_sessions": len(test_b),
    }
    out_path = write_results(out_dir, "planned_run.json", payload)
    print(f"[dry-run] OK. Wrote {out_path}")
    return 0


def cmd_pilot(args: argparse.Namespace) -> int:
    if args.users > PILOT_MAX_USERS:
        raise RunnerError(
            f"--pilot is limited to {PILOT_MAX_USERS} users (requested {args.users})."
        )
    fixtures_dir = args.fixtures
    manifest = load_manifest(fixtures_dir)
    personas = load_jsonl(fixtures_dir / manifest["files"]["personas"]["path"])
    pilot_ids = {p["user_id"] for p in personas[: args.users]}

    out_dir = RESULTS_ROOT / _utcnow_date() / "pilot"
    if not llm_configured():
        payload = planned_run_manifest(
            mode="pilot",
            fixtures_dir=fixtures_dir,
            n_users=args.users,
            reason="No LLM API key set; emitting planned-run manifest only.",
        )
        payload["pilot_user_ids"] = sorted(pilot_ids)
        out_path = write_results(out_dir, "planned_run.json", payload)
        print(f"[pilot] No LLM API key found. Planned manifest written: {out_path}")
        return 0

    # When an LLM is configured, the pilot still does not run by default
    # without --execute. This keeps accidental spend at zero.
    if not args.execute:
        payload = planned_run_manifest(
            mode="pilot",
            fixtures_dir=fixtures_dir,
            n_users=args.users,
            reason="LLM configured but --execute not supplied; emitting plan only.",
        )
        payload["pilot_user_ids"] = sorted(pilot_ids)
        out_path = write_results(out_dir, "planned_run.json", payload)
        print(f"[pilot] LLM available; rerun with --execute to actually call. Plan: {out_path}")
        return 0

    # Execution path is intentionally a stub: real provider wiring lives in
    # an adapter the human approves separately.
    raise RunnerError(
        "Pilot execution adapter is not wired in this commit. "
        "Add a provider adapter and re-invoke with --execute after review."
    )


def cmd_full(args: argparse.Namespace) -> int:
    if not args.confirm_full_run:
        raise RunnerError("Full run requires --confirm-full-run.")
    if os.environ.get(ENV_FULL_APPROVAL) != "1":
        raise RunnerError(
            f"Full run requires environment variable {ENV_FULL_APPROVAL}=1."
        )
    snapshot_dir = SNAPSHOTS_ROOT / _utcnow_date()
    if not snapshot_dir.exists():
        raise RunnerError(
            f"Full run requires a pre-flight snapshot at {snapshot_dir}/. "
            f"Create one explicitly before approving."
        )
    raise RunnerError(
        "Full run execution adapter is not wired in this commit. "
        "All preconditions verified; refusing to run."
    )


def _parse() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="x.klickd v4.1 benchmark runner.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_dry = sub.add_parser("dry-run", help="Validate fixtures, write planned manifest.")
    p_dry.add_argument("--fixtures", type=Path, default=FIXTURES_DIR)
    p_dry.set_defaults(func=cmd_dry_run)

    p_pilot = sub.add_parser("pilot", help=f"Pilot run, max {PILOT_MAX_USERS} users.")
    p_pilot.add_argument("--fixtures", type=Path, default=FIXTURES_DIR)
    p_pilot.add_argument("--users", type=int, default=10)
    p_pilot.add_argument("--execute", action="store_true",
                         help="Actually call the provider (requires adapter).")
    p_pilot.set_defaults(func=cmd_pilot)

    p_full = sub.add_parser("full", help="Full run; heavily gated.")
    p_full.add_argument("--fixtures", type=Path, default=FIXTURES_DIR)
    p_full.add_argument("--confirm-full-run", action="store_true")
    p_full.set_defaults(func=cmd_full)

    return ap.parse_args()


def main() -> int:
    args = _parse()
    try:
        return args.func(args)
    except RunnerError as e:
        print(f"[runner] ERROR: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
