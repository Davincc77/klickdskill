"""Bundle-based Test B pilot/long executor.

Runs (bundle x session x condition) call specs through an injected
provider. Reuses retry / backoff / JSONL / resumability primitives from
:mod:`executor` so tests can inject :class:`providers.MockProvider`.

The long pilot is exactly 1 bundle x 150 sessions x 12 conditions =
1800 outputs. The full design is 5 bundles x 150 sessions x 12
conditions = 9000 outputs, but the runner intentionally refuses to
launch a full path here; see ``runner.py``.
"""
from __future__ import annotations

import json
import sys
import threading
import time
from pathlib import Path
from typing import Any

from .executor import (
    _Writer,
    _call_with_retry,
    _output_hash,
    _read_completed_ids,
    _utcnow_iso,
    ExecutionPlan,
)
from ..prompts.test_b_bundles import (
    TEST_B_BUNDLE_CONDITIONS,
    build_test_b_bundle_messages,
    hash_prompt_bundle,
    test_b_bundle_run_id,
)


def _sessions_by_bundle(sessions: list[dict[str, Any]]
                        ) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    for s in sessions:
        out.setdefault(s["bundle_id"], []).append(s)
    for bid in out:
        out[bid].sort(key=lambda s: s.get("session_index", 0))
    return out


def expand_bundle_calls(
    *,
    sessions: list[dict[str, Any]],
    conditions: tuple[str, ...],
) -> list[dict[str, Any]]:
    """Expand (bundle, session, condition) into deterministic call specs."""
    grouped = _sessions_by_bundle(sessions)
    calls: list[dict[str, Any]] = []
    for bundle_id, bundle_sessions in grouped.items():
        for session in bundle_sessions:
            for condition in conditions:
                system, user = build_test_b_bundle_messages(
                    condition=condition,
                    target_session=session,
                    bundle_sessions=bundle_sessions,
                )
                calls.append({
                    "run_id": test_b_bundle_run_id(
                        bundle_id, session["session_id"], condition,
                    ),
                    "bundle_id": bundle_id,
                    "session_id": session["session_id"],
                    "session_index": session.get("session_index", 0),
                    "phase_id": session.get("phase_id"),
                    "phase_label": session.get("phase_label"),
                    "role": session.get("role"),
                    "language": session.get("language"),
                    "condition": condition,
                    "system": system,
                    "user": user,
                    "prompt_hash": hash_prompt_bundle(system, user),
                    # Reused by the audit script for parity with Test A.
                    "prompt_id": session["session_id"],
                    "family": "test_b_bundle_session",
                })
    return calls


def execute_bundle_pilot(
    *,
    sessions: list[dict[str, Any]],
    conditions: tuple[str, ...],
    provider: Any,
    plan: ExecutionPlan,
    out_dir: Path,
    fixtures_manifest: dict[str, Any],
    repo_commit: str | None,
    run_id: str,
    bundle_ids: list[str],
    sessions_per_bundle: int,
) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_path = out_dir / "raw_outputs.jsonl"
    err_path = out_dir / "errors.jsonl"

    already_done = _read_completed_ids(raw_path)
    all_calls = expand_bundle_calls(sessions=sessions, conditions=conditions)
    pending = [c for c in all_calls if c["run_id"] not in already_done]

    raw_writer = _Writer(raw_path)
    err_writer = _Writer(err_path)

    # Per-item progress logging. Without this the executor was silent for
    # the entire 1800-call run, so a single hung Gemini request looked
    # identical to a healthy run. Lines are emitted on stderr (unbuffered)
    # so GitHub Actions surfaces them in real time.
    total_pending = 0  # set below once we know pending
    progress_lock = threading.Lock()
    progress = {"done": 0, "errors": 0, "started": 0}

    def _log(msg: str) -> None:
        sys.stderr.write(msg + "\n")
        sys.stderr.flush()

    counts = {"ok": 0, "error": 0, "skipped_resumed": len(already_done)}
    latencies: list[int] = []
    by_condition: dict[str, int] = {}
    by_phase: dict[str, int] = {}
    by_bundle: dict[str, int] = {}
    tokens = {"input": 0, "output": 0}

    def _do_call(call: dict[str, Any]) -> None:
        t_start = _utcnow_iso()
        with progress_lock:
            progress["started"] += 1
            started_idx = progress["started"]
        t_call0 = time.monotonic()
        _log(
            f"[bb] start {started_idx}/{total_pending} "
            f"bundle={call['bundle_id']} "
            f"s={call['session_index']:03d} "
            f"cond={call['condition']} "
            f"run_id={call['run_id']}"
        )
        resp, attempts, cumulative_delay = _call_with_retry(
            provider, plan.config, call["system"], call["user"],
            plan.retry_max, plan.retry_backoff_s,
            retry_backoff_max_s=plan.retry_backoff_max_s,
            retry_jitter=plan.retry_jitter,
        )
        dt_ms = int((time.monotonic() - t_call0) * 1000)
        retried_attempts = len(attempts)
        if resp is None:
            final_class = attempts[-1]["error_class"] if attempts else "unknown"
            err_writer.write({
                "run_id": call["run_id"],
                "bundle_id": call["bundle_id"],
                "session_id": call["session_id"],
                "session_index": call["session_index"],
                "phase_id": call["phase_id"],
                "phase_label": call["phase_label"],
                "role": call["role"],
                "language": call["language"],
                "condition": call["condition"],
                "family": call["family"],
                "prompt_id": call["prompt_id"],
                "prompt_hash": call["prompt_hash"],
                "timestamp_utc": t_start,
                "model": plan.config.model,
                "provider": plan.provider_name,
                "errors": [
                    f"attempt={a['attempt']} class={a['error_class']} "
                    f"type={a['error_type']} err={a['error']}"
                    for a in attempts
                ],
                "attempts": attempts,
                "retried_attempts": retried_attempts,
                "final_error_class": final_class,
                "cumulative_retry_delay_s": round(cumulative_delay, 3),
                "status": "error",
            })
            counts["error"] += 1
            with progress_lock:
                progress["errors"] += 1
                progress["done"] += 1
                done_idx = progress["done"]
            _log(
                f"[bb] error {done_idx}/{total_pending} "
                f"run_id={call['run_id']} "
                f"final_class={final_class} "
                f"attempts={retried_attempts} "
                f"wall_ms={dt_ms}"
            )
            return
        raw_writer.write({
            "run_id": call["run_id"],
            "bundle_id": call["bundle_id"],
            "session_id": call["session_id"],
            "session_index": call["session_index"],
            "phase_id": call["phase_id"],
            "phase_label": call["phase_label"],
            "role": call["role"],
            "language": call["language"],
            "condition": call["condition"],
            "family": call["family"],
            "prompt_id": call["prompt_id"],
            "prompt_hash": call["prompt_hash"],
            "output_hash": _output_hash(resp.text),
            "output_text": resp.text,
            "input_tokens": resp.input_tokens,
            "output_tokens": resp.output_tokens,
            "latency_ms": resp.latency_ms,
            "finish_reason": resp.finish_reason,
            "model": plan.config.model,
            "provider": plan.provider_name,
            "provider_metadata": resp.provider_metadata,
            "timestamp_utc": t_start,
            "retried_attempts": retried_attempts,
            "retry_attempts": attempts,
            "cumulative_retry_delay_s": round(cumulative_delay, 3),
            "status": "ok",
        })
        counts["ok"] += 1
        with progress_lock:
            progress["done"] += 1
            done_idx = progress["done"]
        _log(
            f"[bb] ok    {done_idx}/{total_pending} "
            f"run_id={call['run_id']} "
            f"lat_ms={resp.latency_ms} wall_ms={dt_ms} "
            f"in_tok={resp.input_tokens} out_tok={resp.output_tokens}"
        )
        latencies.append(resp.latency_ms)
        by_condition[call["condition"]] = (
            by_condition.get(call["condition"], 0) + 1
        )
        if call["phase_id"]:
            by_phase[call["phase_id"]] = by_phase.get(call["phase_id"], 0) + 1
        by_bundle[call["bundle_id"]] = by_bundle.get(call["bundle_id"], 0) + 1
        tokens["input"] += resp.input_tokens or 0
        tokens["output"] += resp.output_tokens or 0

    import queue as _q
    import time as _time
    total_pending = len(pending)
    _log(
        f"[bb] begin total_pending={total_pending} "
        f"concurrency={plan.concurrency} batch_size={plan.batch_size} "
        f"provider={plan.provider_name} model={plan.config.model}"
    )
    # Defence-in-depth wall-clock cap per call. The provider adapter is
    # the primary line of defence (HttpOptions timeout); this Future-level
    # cap ensures a single hung worker can never block the entire batch.
    per_call_wall_s = max(
        5.0,
        plan.config.timeout_s * (plan.retry_max + 1)
        + plan.retry_backoff_max_s * max(0, plan.retry_max)
        + 5.0,
    )

    def _record_wall_timeout(c: dict[str, Any]) -> None:
        err_writer.write({
            "run_id": c["run_id"],
            "bundle_id": c["bundle_id"],
            "session_id": c["session_id"],
            "session_index": c["session_index"],
            "phase_id": c["phase_id"],
            "phase_label": c["phase_label"],
            "role": c["role"],
            "language": c["language"],
            "condition": c["condition"],
            "family": c["family"],
            "prompt_id": c["prompt_id"],
            "prompt_hash": c["prompt_hash"],
            "timestamp_utc": _utcnow_iso(),
            "model": plan.config.model,
            "provider": plan.provider_name,
            "errors": [f"wall-clock cap exceeded ({per_call_wall_s:.1f}s)"],
            "attempts": [],
            "retried_attempts": 0,
            "final_error_class": "wall_clock_timeout",
            "cumulative_retry_delay_s": 0.0,
            "status": "error",
        })
        counts["error"] += 1
        _log(
            f"[bb] WALL-TIMEOUT run_id={c['run_id']} "
            f"cap_s={per_call_wall_s:.1f}"
        )

    try:
        for batch_start in range(0, len(pending), plan.batch_size):
            batch = pending[batch_start:batch_start + plan.batch_size]
            if plan.concurrency <= 1:
                for call in batch:
                    _do_call(call)
            else:
                # Hand-rolled worker pool of daemon threads. We deliberately
                # avoid ThreadPoolExecutor here: its __exit__ joins all
                # worker threads, which means a single hung HTTPS request
                # would wedge the entire run (the symptom seen on
                # bundle_index=4). Daemon threads cannot prevent process
                # exit, so a wedged worker is harmless once we have
                # classified its job as wall_clock_timeout.
                jobs: _q.Queue = _q.Queue()
                done_q: _q.Queue = _q.Queue()
                pending_calls: dict[str, dict[str, Any]] = {
                    c["run_id"]: c for c in batch
                }
                for c in batch:
                    jobs.put(c)

                def _worker() -> None:
                    while True:
                        try:
                            job = jobs.get_nowait()
                        except _q.Empty:
                            return
                        try:
                            _do_call(job)
                        except BaseException as exc:  # noqa: BLE001
                            _log(
                                f"[bb] worker-raised "
                                f"run_id={job['run_id']} "
                                f"type={type(exc).__name__} err={exc}"
                            )
                        finally:
                            done_q.put(job["run_id"])

                workers = []
                for _ in range(plan.concurrency):
                    t = threading.Thread(
                        target=_worker, name="bb_worker", daemon=True,
                    )
                    t.start()
                    workers.append(t)

                deadline = _time.monotonic() + per_call_wall_s
                while pending_calls:
                    remaining = deadline - _time.monotonic()
                    if remaining <= 0:
                        for rid, c in list(pending_calls.items()):
                            _record_wall_timeout(c)
                            pending_calls.pop(rid, None)
                        break
                    try:
                        finished_rid = done_q.get(timeout=max(0.05, remaining))
                    except _q.Empty:
                        continue
                    pending_calls.pop(finished_rid, None)
                # Don't join wedged workers. They are daemons.
            if plan.sleep_between_batches_s > 0 \
                    and batch_start + plan.batch_size < len(pending):
                _time.sleep(plan.sleep_between_batches_s)
    finally:
        raw_writer.close()
        err_writer.close()

    summary = {
        "run_id": run_id,
        "test": "test_b_bundles",
        "counts": counts,
        "total_attempted": len(pending),
        "by_condition": by_condition,
        "by_phase": by_phase,
        "by_bundle": by_bundle,
        "conditions": list(conditions),
        "bundle_ids": bundle_ids,
        "sessions_per_bundle": sessions_per_bundle,
        "latency_ms": {
            "n": len(latencies),
            "min": min(latencies) if latencies else None,
            "max": max(latencies) if latencies else None,
            "mean": (sum(latencies) / len(latencies)) if latencies else None,
        },
        "tokens": {
            "input_total": tokens["input"],
            "output_total": tokens["output"],
        },
        "provider": plan.provider_name,
        "model": plan.config.model,
        "timestamp_utc": _utcnow_iso(),
    }
    (out_dir / "metrics_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    manifest = {
        "kind": "run_manifest",
        "run_id": run_id,
        "mode": "pilot_test_b_bundles_execute",
        "test": "test_b_bundles",
        "timestamp_utc": _utcnow_iso(),
        "provider": plan.provider_name,
        "config": plan.config.to_dict(),
        "execution": {
            "concurrency": plan.concurrency,
            "batch_size": plan.batch_size,
            "sleep_between_batches_s": plan.sleep_between_batches_s,
            "retry_max": plan.retry_max,
            "retry_backoff_s": plan.retry_backoff_s,
            "retry_backoff_max_s": plan.retry_backoff_max_s,
            "retry_jitter": plan.retry_jitter,
        },
        "fixtures": fixtures_manifest,
        "repo_commit": repo_commit,
        "counts": counts,
        "n_run_specs_total": len(pending) + counts["skipped_resumed"],
        "n_already_done_on_start": counts["skipped_resumed"],
        "conditions": list(conditions),
        "bundle_ids": bundle_ids,
        "sessions_per_bundle": sessions_per_bundle,
        "expected_outputs": len(bundle_ids) * sessions_per_bundle * len(conditions),
        "mem0": {
            "present": False,
            "compatibility_claim": False,
            "_note": "This harness makes NO Mem0 compatibility claim.",
        },
    }
    (out_dir / "run_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {"summary": summary, "manifest": manifest}
