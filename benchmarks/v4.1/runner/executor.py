"""Controlled pilot executor.

Coordinates: prompt building, provider calls, retries with backoff,
batched concurrency, deterministic JSONL logging, resumability via
``raw_outputs.jsonl``, and final metrics summary + manifest.

Design notes
------------
- Concurrency defaults to **1**; the runner's CLI caps it at 8 to keep
  pilots gentle on provider rate limits.
- Batches are processed sequentially; ``--sleep-between-batches`` adds a
  cooperative pause between batches to spread load.
- The executor is resumable: if ``raw_outputs.jsonl`` already exists in
  the run directory, completed ``run_id``s are skipped on relaunch.
- Every successful call writes ONE line to ``raw_outputs.jsonl``; every
  failure writes ONE line to ``errors.jsonl``. Both files are append-only
  so partial progress survives crashes.
- No real LLM call is ever made unless the caller passes an explicit
  provider object. Tests inject :class:`providers.MockProvider`.
"""
from __future__ import annotations

import concurrent.futures as _f
import dataclasses
import hashlib
import json
import random
import threading
import time
import traceback
from pathlib import Path
from typing import Any, Iterable

from ..prompts.test_a import build_test_a_messages, hash_prompt
from ..providers.base import (
    LLMProvider,
    ProviderConfig,
    ProviderError,
    ProviderResponse,
    TerminalProviderError,
    TransientProviderError,
    is_terminal_billing_error,
    is_transient_error,
)


# Conservative caps shared with the runner CLI to avoid aggressive hammering.
RETRY_MAX_HARD_CAP = 8
RETRY_BACKOFF_MAX_S = 30.0


@dataclasses.dataclass(frozen=True)
class ExecutionPlan:
    provider_name: str
    config: ProviderConfig
    concurrency: int
    batch_size: int
    sleep_between_batches_s: float
    retry_max: int
    retry_backoff_s: float = 2.0
    retry_backoff_max_s: float = RETRY_BACKOFF_MAX_S
    retry_jitter: float = 0.25


def _output_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _utcnow_iso() -> str:
    import datetime as _dt
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _read_completed_ids(raw_path: Path) -> set[str]:
    """Return run_ids already present in an existing raw_outputs.jsonl."""
    done: set[str] = set()
    if not raw_path.exists():
        return done
    with raw_path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            rid = row.get("run_id")
            if rid:
                done.add(rid)
    return done


def _persona_index(personas: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {p["user_id"]: p for p in personas}


def _build_call(
    run_spec: dict[str, Any],
    personas_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    persona = personas_by_id[run_spec["user_id"]]
    system, user = build_test_a_messages(
        condition=run_spec["condition"],
        persona=persona,
        user_prompt=run_spec["prompt"],
    )
    return {
        "run_id": run_spec["run_id"],
        "user_id": run_spec["user_id"],
        "prompt_id": run_spec["prompt_id"],
        "family": run_spec["family"],
        "condition": run_spec["condition"],
        "system": system,
        "user": user,
        "prompt_hash": hash_prompt(system, user),
    }


def _classify(exc: BaseException) -> str:
    """Stable short string used in retry logs.

    Classes:
    - ``transient``: retryable (429 rate limit cooldown, 5xx, timeout)
    - ``terminal_billing``: provider-side billing/spend hard cap. NOT
      retryable; the entire run should stop because every subsequent
      call will hit the identical cap.
    - ``permanent``: auth/config/schema errors. NOT retryable for this
      call but the rest of the run is unaffected.
    - ``unhandled``: anything we did not recognise — treated as permanent
      for safety so we never silently retry an unknown failure mode.
    """
    if is_terminal_billing_error(exc):
        return "terminal_billing"
    if isinstance(exc, TransientProviderError):
        return "transient"
    if isinstance(exc, ProviderError):
        return "transient" if is_transient_error(exc) else "permanent"
    return "transient" if is_transient_error(exc) else "unhandled"


def _compute_backoff(
    attempt: int,
    base: float,
    cap: float,
    jitter: float,
    rng: random.Random,
) -> float:
    """Exponential backoff with full-bandwidth jitter, capped at ``cap``."""
    raw = min(cap, base * (2 ** attempt))
    if jitter <= 0:
        return max(0.0, raw)
    spread = raw * jitter
    return max(0.0, raw + rng.uniform(-spread, spread))


def _call_with_retry(
    provider: LLMProvider,
    config: ProviderConfig,
    system: str,
    user: str,
    retry_max: int,
    retry_backoff_s: float,
    retry_backoff_max_s: float = RETRY_BACKOFF_MAX_S,
    retry_jitter: float = 0.25,
    sleep: Any = time.sleep,
    rng: random.Random | None = None,
) -> tuple[ProviderResponse | None, list[dict[str, Any]], float]:
    """Call the provider with bounded jittered exponential backoff.

    Only :class:`TransientProviderError` (or any exception classified as
    transient by :func:`is_transient_error`) triggers a retry. Permanent
    errors (auth, config, schema) abort immediately so quotas are not
    burned on calls that cannot succeed.

    Returns ``(response, attempts, cumulative_retry_delay_s)``.
    ``response`` is ``None`` iff every attempt failed. ``attempts`` is a
    list of structured dicts (one per attempt) used by the executor for
    logging and by tests for verification.
    """
    rng = rng or random.Random()
    attempts: list[dict[str, Any]] = []
    cumulative_delay = 0.0
    for attempt in range(retry_max + 1):
        try:
            resp = provider.generate(system, user, config)
            return resp, attempts, cumulative_delay
        except ProviderError as exc:
            cls = _classify(exc)
            attempts.append({
                "attempt": attempt,
                "error_class": cls,
                "error_type": type(exc).__name__,
                "error": str(exc),
            })
            if cls != "transient":
                return None, attempts, cumulative_delay
        except Exception as exc:  # pragma: no cover - defensive
            cls = _classify(exc)
            attempts.append({
                "attempt": attempt,
                "error_class": cls,
                "error_type": type(exc).__name__,
                "error": str(exc),
                "traceback": traceback.format_exc(limit=2),
            })
            if cls != "transient":
                return None, attempts, cumulative_delay
        if attempt < retry_max:
            delay = _compute_backoff(
                attempt, retry_backoff_s, retry_backoff_max_s,
                retry_jitter, rng,
            )
            attempts[-1]["sleep_s"] = round(delay, 3)
            cumulative_delay += delay
            sleep(delay)
    return None, attempts, cumulative_delay


class _Writer:
    """Thread-safe append-only JSONL writer."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._lock = threading.Lock()
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = self._path.open("a", encoding="utf-8")

    def write(self, row: dict[str, Any]) -> None:
        line = json.dumps(row, sort_keys=True, ensure_ascii=False)
        with self._lock:
            self._fh.write(line + "\n")
            self._fh.flush()

    def close(self) -> None:
        try:
            self._fh.close()
        except Exception:
            pass


def execute_pilot(
    *,
    run_specs: list[dict[str, Any]],
    personas: list[dict[str, Any]],
    provider: LLMProvider,
    plan: ExecutionPlan,
    out_dir: Path,
    fixtures_manifest: dict[str, Any],
    repo_commit: str | None,
    run_id: str,
) -> dict[str, Any]:
    """Run the pilot and emit JSONL + summary + manifest.

    The function NEVER imports a real SDK; the caller supplies the provider.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_path = out_dir / "raw_outputs.jsonl"
    err_path = out_dir / "errors.jsonl"

    already_done = _read_completed_ids(raw_path)
    personas_by_id = _persona_index(personas)
    pending = [_build_call(rs, personas_by_id) for rs in run_specs
               if rs["run_id"] not in already_done]

    raw_writer = _Writer(raw_path)
    err_writer = _Writer(err_path)

    counts = {"ok": 0, "error": 0, "skipped_resumed": len(already_done)}
    latencies: list[int] = []
    input_tok_total = 0
    output_tok_total = 0
    by_condition: dict[str, int] = {}

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
        nonlocal_state["input_tokens"] += resp.input_tokens or 0
        nonlocal_state["output_tokens"] += resp.output_tokens or 0
        by_condition[call["condition"]] = by_condition.get(call["condition"], 0) + 1

    nonlocal_state = {"input_tokens": 0, "output_tokens": 0}

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
                time.sleep(plan.sleep_between_batches_s)
    finally:
        raw_writer.close()
        err_writer.close()

    input_tok_total = nonlocal_state["input_tokens"]
    output_tok_total = nonlocal_state["output_tokens"]

    summary = {
        "run_id": run_id,
        "counts": counts,
        "total_attempted": len(pending),
        "by_condition": by_condition,
        "latency_ms": {
            "n": len(latencies),
            "min": min(latencies) if latencies else None,
            "max": max(latencies) if latencies else None,
            "mean": (sum(latencies) / len(latencies)) if latencies else None,
        },
        "tokens": {
            "input_total": input_tok_total,
            "output_total": output_tok_total,
        },
        "provider": plan.provider_name,
        "model": plan.config.model,
        "timestamp_utc": _utcnow_iso(),
    }
    (out_dir / "metrics_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    manifest = {
        "kind": "run_manifest",
        "run_id": run_id,
        "mode": "pilot_execute",
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
        "n_run_specs_total": len(run_specs),
        "n_already_done_on_start": len(already_done),
    }
    (out_dir / "run_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"summary": summary, "manifest": manifest}
