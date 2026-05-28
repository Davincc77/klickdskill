#!/usr/bin/env python3
"""x.klickd v4.1 benchmark runner — dry-run by default.

Modes:
    dry-run   Never calls an LLM. Validates fixtures and writes a planned
              manifest under results/.
    pilot     Up to 10 users. With ``--execute`` AND a provider, calls the
              provider with low concurrency. Without ``--execute`` or
              without a provider, only a planned manifest is emitted.
    full      Requires ``--confirm-full-run`` AND ``XKLICKD_BENCHMARK_FULL_APPROVED=1``
              AND a pre-flight snapshot under results/snapshots/<date>/.
              The full run is intentionally still refused even when all
              gates pass; a human must wire the execution path explicitly.

Token accounting is heuristic unless a provider returns usage. Heuristic
counts are labelled as such.

NEVER claims Mem0 compatibility. The mem0 condition is skipped unless a
local Mem0 install or MEM0_API_KEY is detected, and even then the runner
reports it as ``mem0_present=true`` without asserting compatibility.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import importlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
FIXTURES_DIR = ROOT / "fixtures" / "generated"
RESULTS_ROOT = ROOT / "results"
SNAPSHOTS_ROOT = RESULTS_ROOT / "snapshots"

PILOT_MAX_USERS = 10
PILOT_MAX_CONCURRENCY = 8
PILOT_RETRY_MAX_CAP = 8
PILOT_RETRY_BACKOFF_MAX_CAP = 30.0
PILOT_RETRY_BACKOFF_BASE_CAP = 10.0
PILOT_DEFAULT_RETRY_MAX = 5
PILOT_DEFAULT_RETRY_BACKOFF_S = 2.0
PILOT_DEFAULT_RETRY_BACKOFF_MAX_S = 30.0
PILOT_DEFAULT_RETRY_JITTER = 0.25
ENV_FULL_APPROVAL = "XKLICKD_BENCHMARK_FULL_APPROVED"
ENV_LLM_KEYS = (
    "LLM_API_KEY",
    "GEMINI_API_KEY",
    "GOOGLE_API_KEY",
    "ANTHROPIC_API_KEY",
    "OPENAI_API_KEY",
    "GROQ_API_KEY",
)
ENV_MEM0_KEY = "MEM0_API_KEY"


class RunnerError(RuntimeError):
    pass


def _utcnow_date() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d")


def _utcnow_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _run_id() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("pilot_%Y%m%dT%H%M%SZ")


def _git_sha() -> str | None:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT,
            check=False, capture_output=True, text=True, timeout=5,
        )
        if out.returncode == 0:
            return out.stdout.strip() or None
    except Exception:
        return None
    return None


def llm_configured() -> bool:
    return any(os.environ.get(k) for k in ENV_LLM_KEYS)


def mem0_present() -> bool:
    if os.environ.get(ENV_MEM0_KEY):
        return True
    try:
        return importlib.util.find_spec("mem0") is not None
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
            f"Run: python benchmarks/v4.1/fixtures/generator.py"
        )
    return json.loads(mpath.read_text())


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
        "repo_commit": _git_sha(),
    }


def write_results(out_dir: Path, name: str, payload: dict[str, Any]) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / name
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")
    return out_path


def _load_executor_module() -> Any:
    """Load the executor module without relying on package imports.

    The ``benchmarks/v4.1`` directory is not a valid Python identifier so
    we cannot ``from .. import ...``. We load both ``executor`` and the
    ``providers`` / ``prompts`` packages by absolute path.
    """
    base = ROOT
    # Register a synthetic top-level package mapping so relative imports work.
    pkg_name = "_v4_1_pkg"
    if pkg_name not in sys.modules:
        import types as _types
        pkg = _types.ModuleType(pkg_name)
        pkg.__path__ = [str(base)]
        sys.modules[pkg_name] = pkg
    for child in ("providers", "prompts", "runner"):
        full = f"{pkg_name}.{child}"
        if full in sys.modules:
            continue
        spec = importlib.util.spec_from_file_location(
            full, base / child / "__init__.py",
            submodule_search_locations=[str(base / child)],
        )
        assert spec and spec.loader
        mod = importlib.util.module_from_spec(spec)
        sys.modules[full] = mod
        spec.loader.exec_module(mod)
    # Now load the executor as a submodule of _v4_1_pkg.runner so its
    # relative imports (``..prompts``, ``..providers``) resolve.
    full = f"{pkg_name}.runner.executor"
    if full not in sys.modules:
        spec = importlib.util.spec_from_file_location(
            full, base / "runner" / "executor.py",
        )
        assert spec and spec.loader
        mod = importlib.util.module_from_spec(spec)
        sys.modules[full] = mod
        spec.loader.exec_module(mod)
    return sys.modules[full]


def _resolve_provider(name: str) -> Any:
    """Resolve a provider factory from the loaded providers package."""
    _load_executor_module()
    providers_pkg = sys.modules["_v4_1_pkg.providers"]
    return providers_pkg.get_provider(name)


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
    if args.concurrency < 1 or args.concurrency > PILOT_MAX_CONCURRENCY:
        raise RunnerError(
            f"--concurrency must be in [1, {PILOT_MAX_CONCURRENCY}] (got {args.concurrency})."
        )
    if args.batch_size < 1:
        raise RunnerError("--batch-size must be >= 1.")
    if args.retry_max < 0:
        raise RunnerError("--retry-max must be >= 0.")
    if args.retry_max > PILOT_RETRY_MAX_CAP:
        raise RunnerError(
            f"--retry-max is capped at {PILOT_RETRY_MAX_CAP} for pilots "
            f"(got {args.retry_max}). Higher values would risk overwhelming "
            f"a stressed provider."
        )
    if args.retry_backoff < 0:
        raise RunnerError("--retry-backoff must be >= 0.")
    if args.retry_backoff > PILOT_RETRY_BACKOFF_BASE_CAP:
        raise RunnerError(
            f"--retry-backoff base is capped at {PILOT_RETRY_BACKOFF_BASE_CAP}s "
            f"(got {args.retry_backoff})."
        )
    if args.retry_backoff_max < 0:
        raise RunnerError("--retry-backoff-max must be >= 0.")
    if args.retry_backoff_max > PILOT_RETRY_BACKOFF_MAX_CAP:
        raise RunnerError(
            f"--retry-backoff-max is capped at {PILOT_RETRY_BACKOFF_MAX_CAP}s "
            f"(got {args.retry_backoff_max})."
        )
    if args.retry_jitter < 0 or args.retry_jitter > 1:
        raise RunnerError("--retry-jitter must be in [0, 1].")
    if args.sleep_between_batches < 0:
        raise RunnerError("--sleep-between-batches must be >= 0.")

    fixtures_dir = args.fixtures
    manifest = load_manifest(fixtures_dir)
    personas = load_jsonl(fixtures_dir / manifest["files"]["personas"]["path"])
    pilot_personas = personas[: args.users]
    pilot_ids = {p["user_id"] for p in pilot_personas}
    test_a = load_jsonl(fixtures_dir / manifest["files"]["test_a_runs"]["path"])
    pilot_runs = [r for r in test_a if r["user_id"] in pilot_ids]

    out_dir = RESULTS_ROOT / _utcnow_date() / "pilot"

    # Plan-only branch: no execute, or no provider, or no LLM key.
    needs_provider = args.execute
    has_key = args.provider == "mock" or llm_configured()
    if not needs_provider or not has_key:
        reason = (
            "No LLM API key set and provider != mock; emitting planned-run "
            "manifest only."
            if not has_key
            else "Provider available but --execute not supplied; emitting plan only."
        )
        payload = planned_run_manifest(
            mode="pilot",
            fixtures_dir=fixtures_dir,
            n_users=args.users,
            reason=reason,
        )
        payload["pilot_user_ids"] = sorted(pilot_ids)
        payload["provider_requested"] = args.provider
        payload["execution_plan"] = {
            "concurrency": args.concurrency,
            "batch_size": args.batch_size,
            "sleep_between_batches_s": args.sleep_between_batches,
            "retry_max": args.retry_max,
            "retry_backoff_s": args.retry_backoff,
            "retry_backoff_max_s": args.retry_backoff_max,
            "retry_jitter": args.retry_jitter,
            "model": args.model,
            "temperature": args.temperature,
            "max_output_tokens": args.max_output_tokens,
        }
        out_path = write_results(out_dir, "planned_run.json", payload)
        print(f"[pilot] {reason}\n[pilot] Plan: {out_path}")
        return 0

    # Execution path. Use the run-id subdirectory to keep multiple pilot
    # attempts side by side; resumability is per-run.
    rid = args.run_id or _run_id()
    run_dir = out_dir / rid
    run_dir.mkdir(parents=True, exist_ok=True)

    executor = _load_executor_module()
    providers_pkg = sys.modules["_v4_1_pkg.providers"]
    config = providers_pkg.ProviderConfig(
        model=args.model,
        temperature=args.temperature,
        max_output_tokens=args.max_output_tokens,
    )
    if args._provider_instance is not None:
        provider = args._provider_instance
    else:
        provider = _resolve_provider(args.provider)

    plan = executor.ExecutionPlan(
        provider_name=args.provider,
        config=config,
        concurrency=args.concurrency,
        batch_size=args.batch_size,
        sleep_between_batches_s=args.sleep_between_batches,
        retry_max=args.retry_max,
        retry_backoff_s=args.retry_backoff,
        retry_backoff_max_s=args.retry_backoff_max,
        retry_jitter=args.retry_jitter,
    )
    result = executor.execute_pilot(
        run_specs=pilot_runs,
        personas=pilot_personas,
        provider=provider,
        plan=plan,
        out_dir=run_dir,
        fixtures_manifest=manifest,
        repo_commit=_git_sha(),
        run_id=rid,
    )
    print(
        f"[pilot] Executed {result['summary']['counts']['ok']} ok / "
        f"{result['summary']['counts']['error']} errors. "
        f"Outputs in {run_dir}"
    )
    return 0


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
    p_pilot.add_argument("--provider", default="gemini",
                         choices=["gemini", "mock"],
                         help="Provider name (default: gemini).")
    p_pilot.add_argument("--model", default="gemini-2.5-flash",
                         help="Model id (default: gemini-2.5-flash).")
    p_pilot.add_argument("--temperature", type=float, default=0.2)
    p_pilot.add_argument("--max-output-tokens", type=int, default=512)
    p_pilot.add_argument("--concurrency", type=int, default=1,
                         help=f"Parallel calls (default 1, max {PILOT_MAX_CONCURRENCY}).")
    p_pilot.add_argument("--batch-size", type=int, default=10)
    p_pilot.add_argument("--sleep-between-batches", type=float, default=1.0)
    p_pilot.add_argument(
        "--retry-max", type=int, default=PILOT_DEFAULT_RETRY_MAX,
        help=(
            f"Max retries on transient errors (default {PILOT_DEFAULT_RETRY_MAX}, "
            f"cap {PILOT_RETRY_MAX_CAP}). Only retries on 429/5xx/UNAVAILABLE/"
            f"RESOURCE_EXHAUSTED; permanent errors abort immediately."
        ),
    )
    p_pilot.add_argument(
        "--retry-backoff", type=float, default=PILOT_DEFAULT_RETRY_BACKOFF_S,
        help=(
            f"Base backoff in seconds (default {PILOT_DEFAULT_RETRY_BACKOFF_S}s, "
            f"cap {PILOT_RETRY_BACKOFF_BASE_CAP}s). Exponential with jitter."
        ),
    )
    p_pilot.add_argument(
        "--retry-backoff-max", type=float,
        default=PILOT_DEFAULT_RETRY_BACKOFF_MAX_S,
        help=(
            f"Maximum single backoff in seconds (default "
            f"{PILOT_DEFAULT_RETRY_BACKOFF_MAX_S}s, cap "
            f"{PILOT_RETRY_BACKOFF_MAX_CAP}s)."
        ),
    )
    p_pilot.add_argument(
        "--retry-jitter", type=float, default=PILOT_DEFAULT_RETRY_JITTER,
        help=(
            f"Backoff jitter fraction in [0, 1] (default "
            f"{PILOT_DEFAULT_RETRY_JITTER})."
        ),
    )
    p_pilot.add_argument("--run-id", default=None,
                         help="Reuse a prior run-id to resume.")
    # Internal-only: allow tests to inject a provider instance directly.
    p_pilot.set_defaults(func=cmd_pilot, _provider_instance=None)

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
