"""Controlled Test B pilot executor.

Test B evaluates cross-session memory. For each (user, session) the
executor enumerates the configured Test B conditions and calls the
provider once per (session, condition) on the deterministic final probe.

Reuses the same retry / backoff / batching / JSONL logging primitives as
the Test A executor (:mod:`benchmarks.v4.1.runner.executor`). Provider
calls go through the *injected* provider object so no real LLM call is
made under tests; tests pass :class:`providers.MockProvider`.

The on-disk shape matches Test A so the audit script can be reused.
"""
from __future__ import annotations

import dataclasses
import json
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
from ..prompts.test_b import (
    TEST_B_BASE_CONDITIONS,
    TEST_B_MEM0_CONDITION,
    TEST_B_MEM0_SKIPPED,
    build_test_b_messages,
    hash_prompt_b,
    test_b_run_id,
)


def _persona_index(personas: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {p["user_id"]: p for p in personas}


def _sessions_by_user(sessions: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    for s in sessions:
        out.setdefault(s["user_id"], []).append(s)
    for user_id in out:
        out[user_id].sort(key=lambda s: s.get("session_index", 0))
    return out


def expand_test_b_calls(
    *,
    personas: list[dict[str, Any]],
    sessions: list[dict[str, Any]],
    conditions: tuple[str, ...],
) -> list[dict[str, Any]]:
    """Expand (persona, session, condition) into deterministic call specs."""
    personas_by_id = _persona_index(personas)
    grouped = _sessions_by_user(sessions)
    calls: list[dict[str, Any]] = []
    for user_id, user_sessions in grouped.items():
        persona = personas_by_id.get(user_id)
        if persona is None:
            continue
        for session in user_sessions:
            for condition in conditions:
                system, user = build_test_b_messages(
                    condition=condition,
                    persona=persona,
                    target_session=session,
                    all_sessions=user_sessions,
                )
                calls.append({
                    "run_id": test_b_run_id(
                        user_id, session["session_id"], condition,
                    ),
                    "user_id": user_id,
                    "session_id": session["session_id"],
                    "session_index": session.get("session_index", 0),
                    "topic": session.get("topic"),
                    "condition": condition,
                    "system": system,
                    "user": user,
                    "prompt_hash": hash_prompt_b(system, user),
                    # Reused by the audit script (treated like a prompt id).
                    "prompt_id": session["session_id"],
                    "family": "test_b_session",
                })
    return calls


def execute_test_b_pilot(
    *,
    personas: list[dict[str, Any]],
    sessions: list[dict[str, Any]],
    conditions: tuple[str, ...],
    provider: Any,
    plan: ExecutionPlan,
    out_dir: Path,
    fixtures_manifest: dict[str, Any],
    repo_commit: str | None,
    run_id: str,
    mem0_present: bool,
) -> dict[str, Any]:
    """Run the Test B pilot and emit the same artefact set as Test A.

    ``mem0_present`` is recorded in the manifest but never used to claim
    Mem0 compatibility. When False, the mem0 condition is replaced by
    :data:`TEST_B_MEM0_SKIPPED` upstream.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_path = out_dir / "raw_outputs.jsonl"
    err_path = out_dir / "errors.jsonl"

    already_done = _read_completed_ids(raw_path)
    pending = [
        c for c in expand_test_b_calls(
            personas=personas, sessions=sessions, conditions=conditions,
        ) if c["run_id"] not in already_done
    ]

    raw_writer = _Writer(raw_path)
    err_writer = _Writer(err_path)

    counts = {"ok": 0, "error": 0, "skipped_resumed": len(already_done)}
    latencies: list[int] = []
    by_condition: dict[str, int] = {}
    tokens = {"input": 0, "output": 0}

    def _do_call(call: dict[str, Any]) -> None:
        t_start = _utcnow_iso()
        resp, attempts, cumulative_delay = _call_with_retry(
            provider, plan.config, call["system"], call["user"],
            plan.retry_max, plan.retry_backoff_s,
            retry_backoff_max_s=plan.retry_backoff_max_s,
            retry_jitter=plan.retry_jitter,
        )
        retried_attempts = len(attempts)
        if resp is None:
            final_class = attempts[-1]["error_class"] if attempts else "unknown"
            err_writer.write({
                "run_id": call["run_id"],
                "user_id": call["user_id"],
                "session_id": call["session_id"],
                "session_index": call["session_index"],
                "topic": call["topic"],
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
            return
        raw_writer.write({
            "run_id": call["run_id"],
            "user_id": call["user_id"],
            "session_id": call["session_id"],
            "session_index": call["session_index"],
            "topic": call["topic"],
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
        latencies.append(resp.latency_ms)
        by_condition[call["condition"]] = by_condition.get(call["condition"], 0) + 1
        tokens["input"] += resp.input_tokens or 0
        tokens["output"] += resp.output_tokens or 0

    import concurrent.futures as _f
    import time as _time
    try:
        for batch_start in range(0, len(pending), plan.batch_size):
            batch = pending[batch_start:batch_start + plan.batch_size]
            if plan.concurrency <= 1:
                for call in batch:
                    _do_call(call)
            else:
                with _f.ThreadPoolExecutor(max_workers=plan.concurrency) as pool:
                    list(pool.map(_do_call, batch))
            if plan.sleep_between_batches_s > 0 and batch_start + plan.batch_size < len(pending):
                _time.sleep(plan.sleep_between_batches_s)
    finally:
        raw_writer.close()
        err_writer.close()

    summary = {
        "run_id": run_id,
        "test": "test_b",
        "counts": counts,
        "total_attempted": len(pending),
        "by_condition": by_condition,
        "conditions": list(conditions),
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
        "mode": "pilot_test_b_execute",
        "test": "test_b",
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
        "mem0": {
            "present": mem0_present,
            "compatibility_claim": False,
            "_note": "This harness makes NO Mem0 compatibility claim.",
        },
    }
    (out_dir / "run_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {"summary": summary, "manifest": manifest}
