"""Terminal billing / spend-cap classification tests.

Regression for the corrected v4.1 Test B run 26642239431, which produced
230 errors and zero raw outputs because Gemini returned
``429 RESOURCE_EXHAUSTED`` with message
``Your project has exceeded its monthly spending cap. Please go to AI
Studio at https://ai.studio/spend...``. The harness misclassified that
as a transient 429 and retried every item 6 times — wasting a 120-min
job on a guaranteed-failing condition that only a human can fix.

These tests pin down:
- A monthly-spend-cap message is NOT classified as transient even though
  it carries a 429 / RESOURCE_EXHAUSTED token.
- ``TerminalProviderError`` is a distinct, non-retryable class.
- ``_call_with_retry`` calls the provider exactly ONCE for a terminal
  billing failure regardless of how high ``retry_max`` is.
- Genuine transient 429 / rate-limit messages (no spend-cap text) keep
  the old transient-retry behaviour.
- The Gemini adapter wraps a spend-cap SDK exception as
  ``TerminalProviderError`` (without making any network call).
- The bundle executor aborts the run on the first terminal_billing
  result instead of attempting the full pending list, records the
  remaining work as ``skipped_terminal_abort``, and stamps the
  abort_reason into both summary and manifest.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path
from typing import Any

import pytest

from conftest import executor, providers, runner


GEMINI_SPEND_CAP_MSG = (
    "429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'Your "
    "project has exceeded its monthly spending cap. Please go to AI "
    "Studio at https://ai.studio/spend to raise your spend cap or "
    "wait until next month.', 'status': 'RESOURCE_EXHAUSTED'}}"
)


# ---------------------------------------------------------------------------
# Classifier
# ---------------------------------------------------------------------------

def test_spend_cap_is_terminal_not_transient() -> None:
    exc = Exception(GEMINI_SPEND_CAP_MSG)
    assert providers.is_terminal_billing_error(exc)
    # The 429 / RESOURCE_EXHAUSTED tokens must NOT win over the cap text.
    assert not providers.is_transient_error(exc)


@pytest.mark.parametrize(
    "msg",
    [
        "Your project has exceeded its monthly spending cap.",
        "monthly spend cap reached for this project",
        "billing hard cap exceeded — contact support",
        "429 RESOURCE_EXHAUSTED: spending cap reached",
        "see https://ai.studio/spend for details",
    ],
)
def test_terminal_billing_variants(msg: str) -> None:
    exc = Exception(msg)
    assert providers.is_terminal_billing_error(exc), msg
    assert not providers.is_transient_error(exc), msg


def test_genuine_rate_limit_still_transient() -> None:
    """A normal 429 rate-limit (no cap text) must remain retryable."""
    for msg in (
        "HTTP 429 Too Many Requests: rate limit exceeded, retry after 30s",
        "RESOURCE_EXHAUSTED: per-minute quota exceeded",
        "429: rate-limit cooldown, please retry",
    ):
        exc = Exception(msg)
        assert not providers.is_terminal_billing_error(exc), msg
        assert providers.is_transient_error(exc), msg


def test_terminal_provider_error_class() -> None:
    exc = providers.TerminalProviderError("monthly spending cap reached")
    # Subclass of ProviderError (so callers that catch ProviderError still see it)
    assert isinstance(exc, providers.ProviderError)
    # But NOT a subclass of TransientProviderError.
    assert not isinstance(exc, providers.TransientProviderError)
    assert providers.is_terminal_billing_error(exc)
    assert not providers.is_transient_error(exc)


# ---------------------------------------------------------------------------
# Retry loop
# ---------------------------------------------------------------------------

class _SpendCapProvider:
    name = "spend_cap"

    def __init__(self) -> None:
        self.calls = 0

    def generate(self, system: str, user: str, config: Any) -> Any:
        self.calls += 1
        raise providers.ProviderError(GEMINI_SPEND_CAP_MSG)


class _SpendCapTerminalProvider:
    """As above but raises the explicit TerminalProviderError subclass."""
    name = "spend_cap_terminal"

    def __init__(self) -> None:
        self.calls = 0

    def generate(self, system: str, user: str, config: Any) -> Any:
        self.calls += 1
        raise providers.TerminalProviderError(GEMINI_SPEND_CAP_MSG)


def _cfg() -> Any:
    return providers.ProviderConfig(model="m", temperature=0.0,
                                    max_output_tokens=8)


def test_retry_loop_calls_provider_once_for_spend_cap_plain() -> None:
    prov = _SpendCapProvider()
    sleeps: list[float] = []
    resp, attempts, cum = executor._call_with_retry(
        prov, _cfg(), "sys", "user",
        retry_max=8, retry_backoff_s=0.0,
        retry_backoff_max_s=1.0, retry_jitter=0.0,
        sleep=sleeps.append, rng=random.Random(0),
    )
    assert resp is None
    # 1 attempt, NOT 9 — no retries should have been scheduled.
    assert prov.calls == 1
    assert len(attempts) == 1
    assert attempts[0]["error_class"] == "terminal_billing"
    assert sleeps == []
    assert cum == 0.0


def test_retry_loop_calls_provider_once_for_spend_cap_terminal_subclass() -> None:
    prov = _SpendCapTerminalProvider()
    sleeps: list[float] = []
    resp, attempts, _ = executor._call_with_retry(
        prov, _cfg(), "sys", "user",
        retry_max=8, retry_backoff_s=0.0,
        retry_backoff_max_s=1.0, retry_jitter=0.0,
        sleep=sleeps.append, rng=random.Random(0),
    )
    assert resp is None
    assert prov.calls == 1
    assert len(attempts) == 1
    assert attempts[0]["error_class"] == "terminal_billing"
    assert attempts[0]["error_type"] == "TerminalProviderError"
    assert sleeps == []


def test_executor_classify_returns_terminal_billing() -> None:
    exc = providers.ProviderError(GEMINI_SPEND_CAP_MSG)
    assert executor._classify(exc) == "terminal_billing"
    exc2 = providers.TerminalProviderError("monthly spending cap")
    assert executor._classify(exc2) == "terminal_billing"
    # Genuine transient still classified as transient.
    exc3 = providers.TransientProviderError("503 UNAVAILABLE")
    assert executor._classify(exc3) == "transient"


# ---------------------------------------------------------------------------
# Gemini adapter (no network)
# ---------------------------------------------------------------------------

class _FakeGeminiClient:
    """Minimal client stub mimicking the surface used by gemini_adapter."""

    def __init__(self, exc: BaseException) -> None:
        self._exc = exc
        self.calls = 0

        class _Models:
            def __init__(_self) -> None:
                _self.calls = 0

            def generate_content(_self, **_kwargs: Any) -> Any:
                _self.calls += 1
                self.calls += 1
                raise self._exc

        self.models = _Models()


def test_gemini_adapter_wraps_spend_cap_as_terminal(monkeypatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key-for-tests")
    gemini = sys.modules["_v4_1_pkg.providers.gemini_adapter"]
    g = providers.get_provider("gemini")
    fake_exc = Exception(GEMINI_SPEND_CAP_MSG)
    fake_client = _FakeGeminiClient(fake_exc)
    g._client = fake_client  # type: ignore[attr-defined]
    cfg = providers.ProviderConfig(model="gemini-2.5-flash", timeout_s=5.0)
    with pytest.raises(providers.TerminalProviderError) as exc_info:
        g.generate("sys", "user", cfg)
    # Adapter must NOT be retried by the loop either:
    assert fake_client.calls == 1
    # And the cause carries the original error text:
    assert "monthly spending cap" in str(exc_info.value).lower()


def test_gemini_adapter_still_wraps_503_as_transient(monkeypatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key-for-tests")
    g = providers.get_provider("gemini")
    fake_exc = Exception("503 UNAVAILABLE high demand")
    fake_client = _FakeGeminiClient(fake_exc)
    g._client = fake_client  # type: ignore[attr-defined]
    cfg = providers.ProviderConfig(model="gemini-2.5-flash", timeout_s=5.0)
    with pytest.raises(providers.TransientProviderError):
        g.generate("sys", "user", cfg)


# ---------------------------------------------------------------------------
# Bundle executor: fail-fast / abort behaviour
# ---------------------------------------------------------------------------

def _load_bundle_modules() -> tuple[Any, Any]:
    runner._load_executor_b_bundles_module()
    return (
        sys.modules["_v4_1_pkg.prompts.test_b_bundles"],
        sys.modules["_v4_1_pkg.runner.executor_b_bundles"],
    )


def _mini_sessions(n: int = 4) -> list[dict[str, Any]]:
    """Hand-rolled session list to keep this test focused & fast."""
    out: list[dict[str, Any]] = []
    for i in range(n):
        out.append({
            "bundle_id": "b01_test",
            "session_id": f"b01_test_{i+1:03d}",
            "session_index": i + 1,
            "phase_id": "p01",
            "phase_label": "phase 1",
            "role": "tester",
            "language": "en",
            "title": f"session {i+1}",
            "summary_compressed": "ctx",
            "interaction": "tick",
            "context_snippets": [],
        })
    return out


def test_bundle_executor_aborts_on_first_spend_cap(tmp_path: Path) -> None:
    prompts_bb, executor_bb = _load_bundle_modules()
    conditions = prompts_bb.TEST_B_BUNDLE_CONDITIONS
    sessions = _mini_sessions(n=3)
    # Total calls = 3 sessions * 12 conditions = 36.
    total_expected = len(sessions) * len(conditions)

    class _AlwaysSpendCap:
        name = "always_cap"

        def __init__(self) -> None:
            self.calls = 0

        def generate(self, system, user, config):
            self.calls += 1
            raise providers.ProviderError(GEMINI_SPEND_CAP_MSG)

    prov = _AlwaysSpendCap()
    plan = executor.ExecutionPlan(
        provider_name="always_cap",
        config=providers.ProviderConfig(
            model="gemini-2.5-flash", temperature=0.0, max_output_tokens=8,
            timeout_s=5.0,
        ),
        concurrency=1,
        batch_size=4,
        sleep_between_batches_s=0.0,
        retry_max=6,             # The bug: this was producing 6 retries / item.
        retry_backoff_s=0.0,
        retry_backoff_max_s=1.0,
        retry_jitter=0.0,
    )

    out_dir = tmp_path / "bb_out"
    result = executor_bb.execute_bundle_pilot(
        sessions=sessions,
        conditions=conditions,
        provider=prov,
        plan=plan,
        out_dir=out_dir,
        fixtures_manifest={"kind": "test_only"},
        repo_commit=None,
        run_id="rTerminalAbort",
        bundle_ids=["b01_test"],
        sessions_per_bundle=len(sessions),
    )

    summary = result["summary"]
    manifest = result["manifest"]

    # The provider was hit at most ``batch_size`` times — never the
    # full 36 calls and never 36 * (retry_max + 1) = 252.
    assert prov.calls <= plan.batch_size, prov.calls
    assert prov.calls >= 1
    # Abort flags are recorded.
    assert summary["aborted"] is True
    assert summary["abort_reason"] is not None
    assert manifest["aborted"] is True
    # Counts: at least one error (the first cap hit), the rest are
    # recorded as skipped_terminal_abort (or simply not dispatched after
    # the first batch). Total accounted-for must equal total_expected.
    counts = summary["counts"]
    accounted = (
        counts["ok"] + counts["error"]
        + counts.get("skipped_terminal_abort", 0)
        + counts.get("skipped_resumed", 0)
    )
    assert counts["ok"] == 0
    assert counts["error"] >= 1
    # Every dispatched item should classify as terminal_billing, NOT as
    # transient (the bug).
    err_path = out_dir / "errors.jsonl"
    err_rows = [json.loads(l) for l in err_path.read_text().splitlines() if l.strip()]
    assert err_rows
    for row in err_rows:
        assert row["final_error_class"] == "terminal_billing", row
        # Per-call retried_attempts must be exactly 1 (no retries burned).
        assert row["retried_attempts"] == 1, row
    # Subsequent batches are NOT dispatched at all (no provider call,
    # no counts row). Accounted-for must be strictly less than the
    # full plan — that is the whole point of failing fast.
    assert accounted < total_expected
    # Only the very first batch was touched: 1 error + the rest of that
    # batch as skipped_terminal_abort, with later batches simply not
    # visited.
    in_flight_batch = min(plan.batch_size, total_expected)
    assert accounted == in_flight_batch, (accounted, in_flight_batch, counts)


def test_bundle_executor_does_not_abort_on_genuine_transient(tmp_path: Path) -> None:
    """If failures are only transient 429s (rate limit), the executor must
    NOT trip the terminal abort — it must keep going (and exhaust the
    per-call retry budget) so the existing recovery path still applies."""
    prompts_bb, executor_bb = _load_bundle_modules()
    conditions = prompts_bb.TEST_B_BUNDLE_CONDITIONS
    sessions = _mini_sessions(n=2)

    class _AlwaysRateLimit:
        name = "always_429"

        def __init__(self) -> None:
            self.calls = 0

        def generate(self, system, user, config):
            self.calls += 1
            raise providers.TransientProviderError(
                "HTTP 429 rate limit exceeded; please retry"
            )

    prov = _AlwaysRateLimit()
    plan = executor.ExecutionPlan(
        provider_name="always_429",
        config=providers.ProviderConfig(
            model="gemini-2.5-flash", temperature=0.0, max_output_tokens=8,
            timeout_s=5.0,
        ),
        concurrency=1,
        batch_size=4,
        sleep_between_batches_s=0.0,
        retry_max=1,
        retry_backoff_s=0.0,
        retry_backoff_max_s=1.0,
        retry_jitter=0.0,
    )

    out_dir = tmp_path / "bb_out_429"
    result = executor_bb.execute_bundle_pilot(
        sessions=sessions,
        conditions=conditions,
        provider=prov,
        plan=plan,
        out_dir=out_dir,
        fixtures_manifest={"kind": "test_only"},
        repo_commit=None,
        run_id="rNoAbort429",
        bundle_ids=["b01_test"],
        sessions_per_bundle=len(sessions),
    )
    summary = result["summary"]
    assert summary["aborted"] is False
    # Every call attempted, each retried once (retry_max=1) → 2 calls per item.
    total = len(sessions) * len(conditions)
    assert summary["counts"]["error"] == total
    # All errors classified transient — no terminal_billing slips in.
    err_path = out_dir / "errors.jsonl"
    err_rows = [json.loads(l) for l in err_path.read_text().splitlines() if l.strip()]
    for row in err_rows:
        assert row["final_error_class"] == "transient", row
