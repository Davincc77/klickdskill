"""Retry / backoff classification tests for the v4.1 pilot executor.

These tests pin down the behaviour added after the first real Gemini
pilot produced 4 transient ``503 UNAVAILABLE`` failures:

- Transient (5xx, UNAVAILABLE, RESOURCE_EXHAUSTED, 429, timeouts) are
  retried with exponential jittered backoff up to ``retry_max``.
- Permanent errors (auth / config / unknown) abort immediately so we do
  not burn quota.
- Persistent transient errors surface as recorded failures after the
  configured budget — failures are NOT hidden.
- The structured log carries ``retried_attempts``,
  ``cumulative_retry_delay_s``, ``final_error_class``, and the per-attempt
  trace.
- Backoff is capped at ``retry_backoff_max_s`` even at high attempt
  counts.
"""
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Any

import pytest

from conftest import executor, generator, providers, runner


# --------------------------------------------------------------------------
# Classifier
# --------------------------------------------------------------------------

def test_classifier_marks_503_unavailable_as_transient() -> None:
    assert providers.is_transient_error(Exception("503 UNAVAILABLE: high demand"))
    assert providers.is_transient_error(Exception("HTTP 503 Service Unavailable"))


def test_classifier_marks_429_and_rate_limit_as_transient() -> None:
    assert providers.is_transient_error(Exception("HTTP 429 rate limit exceeded"))
    assert providers.is_transient_error(Exception("RESOURCE_EXHAUSTED quota"))


def test_classifier_marks_5xx_as_transient() -> None:
    for code in (500, 502, 503, 504):
        assert providers.is_transient_error(Exception(f"HTTP {code} server error")), code


def test_classifier_marks_timeouts_as_transient() -> None:
    assert providers.is_transient_error(Exception("Read timed out after 60s"))
    assert providers.is_transient_error(Exception("DEADLINE_EXCEEDED"))


def test_classifier_skips_auth_and_config_errors() -> None:
    assert not providers.is_transient_error(Exception("invalid API key"))
    assert not providers.is_transient_error(Exception("PERMISSION_DENIED"))
    assert not providers.is_transient_error(Exception("400 INVALID_ARGUMENT model"))
    assert not providers.is_transient_error(Exception("401 unauthorized"))


def test_classifier_respects_status_code_attribute() -> None:
    class HasStatus(Exception):
        status_code = 503

    class HasCode(Exception):
        code = 429

    assert providers.is_transient_error(HasStatus("anything"))
    assert providers.is_transient_error(HasCode("anything"))


# --------------------------------------------------------------------------
# _call_with_retry direct behaviour
# --------------------------------------------------------------------------

def _config() -> Any:
    return providers.ProviderConfig(model="m", temperature=0.0,
                                    max_output_tokens=8)


class _ScriptedProvider:
    """Yields a queue of behaviours: 'transient', 'permanent', 'ok'."""
    name = "scripted"

    def __init__(self, script: list[str]) -> None:
        self.script = list(script)
        self.calls = 0

    def generate(self, system, user, config):
        self.calls += 1
        if not self.script:
            return providers.MockProvider().generate(system, user, config)
        action = self.script.pop(0)
        if action == "transient":
            raise providers.TransientProviderError(
                "503 UNAVAILABLE high demand (scripted)"
            )
        if action == "transient_str":
            raise providers.ProviderError("HTTP 503 Service Unavailable")
        if action == "permanent":
            raise providers.ProviderError("invalid API key")
        if action == "ok":
            return providers.MockProvider().generate(system, user, config)
        raise AssertionError(f"unknown action {action}")


def test_retry_succeeds_after_three_transient_503() -> None:
    prov = _ScriptedProvider(["transient", "transient", "transient", "ok"])
    sleeps: list[float] = []
    resp, attempts, cum = executor._call_with_retry(
        prov, _config(), "sys", "user",
        retry_max=5, retry_backoff_s=2.0,
        retry_backoff_max_s=30.0, retry_jitter=0.0,
        sleep=sleeps.append, rng=random.Random(0),
    )
    assert resp is not None
    assert len(attempts) == 3
    assert all(a["error_class"] == "transient" for a in attempts)
    # 3 retries → 3 sleeps of 2, 4, 8 with jitter=0
    assert sleeps == [2.0, 4.0, 8.0]
    assert pytest.approx(cum, abs=1e-9) == 14.0


def test_retry_classifies_string_503_without_subclass() -> None:
    prov = _ScriptedProvider(["transient_str", "ok"])
    sleeps: list[float] = []
    resp, attempts, _ = executor._call_with_retry(
        prov, _config(), "sys", "user",
        retry_max=3, retry_backoff_s=0.0,
        retry_backoff_max_s=1.0, retry_jitter=0.0,
        sleep=sleeps.append, rng=random.Random(0),
    )
    assert resp is not None
    assert attempts[0]["error_class"] == "transient"


def test_persistent_transient_failure_returns_none_after_budget() -> None:
    prov = _ScriptedProvider(["transient"] * 10)
    sleeps: list[float] = []
    resp, attempts, _ = executor._call_with_retry(
        prov, _config(), "sys", "user",
        retry_max=4, retry_backoff_s=1.0,
        retry_backoff_max_s=5.0, retry_jitter=0.0,
        sleep=sleeps.append, rng=random.Random(0),
    )
    assert resp is None
    # initial + 4 retries = 5 attempts recorded
    assert len(attempts) == 5
    assert all(a["error_class"] == "transient" for a in attempts)
    # 4 sleeps fired between attempts (none after the last attempt)
    assert len(sleeps) == 4


def test_permanent_error_aborts_immediately() -> None:
    prov = _ScriptedProvider(["permanent", "ok"])
    sleeps: list[float] = []
    resp, attempts, _ = executor._call_with_retry(
        prov, _config(), "sys", "user",
        retry_max=5, retry_backoff_s=1.0,
        retry_backoff_max_s=5.0, retry_jitter=0.0,
        sleep=sleeps.append, rng=random.Random(0),
    )
    assert resp is None
    assert len(attempts) == 1
    assert attempts[0]["error_class"] == "permanent"
    # No retry should have been scheduled.
    assert sleeps == []
    # The "ok" action was never consumed.
    assert prov.script == ["ok"]


def test_backoff_is_capped_at_retry_backoff_max_s() -> None:
    sleeps: list[float] = []
    prov = _ScriptedProvider(["transient"] * 20)
    executor._call_with_retry(
        prov, _config(), "sys", "user",
        retry_max=8, retry_backoff_s=3.0,
        retry_backoff_max_s=10.0, retry_jitter=0.0,
        sleep=sleeps.append, rng=random.Random(0),
    )
    # Raw sequence would be 3,6,12,24,48,96,192,384. Cap=10 → most clamp to 10.
    assert max(sleeps) <= 10.0
    assert sleeps[-1] == 10.0


def test_jitter_perturbs_but_stays_bounded() -> None:
    sleeps: list[float] = []
    prov = _ScriptedProvider(["transient"] * 5)
    executor._call_with_retry(
        prov, _config(), "sys", "user",
        retry_max=3, retry_backoff_s=4.0,
        retry_backoff_max_s=30.0, retry_jitter=0.25,
        sleep=sleeps.append, rng=random.Random(1234),
    )
    # raw delays: 4, 8, 16; with jitter=0.25 each falls in [0.75x, 1.25x]
    expected_bounds = [(3.0, 5.0), (6.0, 10.0), (12.0, 20.0)]
    for s, (lo, hi) in zip(sleeps, expected_bounds):
        assert lo <= s <= hi, (s, lo, hi)


# --------------------------------------------------------------------------
# End-to-end via runner.cmd_pilot — log shape
# --------------------------------------------------------------------------

def _fixtures(tmp_path: Path, n_users: int = 1) -> Path:
    out = tmp_path / "fxt"
    generator.generate(seed=4242, n_users=n_users, sessions_per_user=4,
                       out_dir=out)
    return out


def _pilot_ns(fixtures_dir: Path, provider_obj: Any, **overrides) -> argparse.Namespace:
    base = dict(
        fixtures=fixtures_dir,
        users=1,
        execute=True,
        provider="mock",
        model="m",
        temperature=0.0,
        max_output_tokens=64,
        concurrency=1,
        batch_size=4,
        sleep_between_batches=0.0,
        retry_max=3,
        retry_backoff=0.0,
        retry_backoff_max=1.0,
        retry_jitter=0.0,
        run_id="rRetry",
        _provider_instance=provider_obj,
    )
    base.update(overrides)
    return argparse.Namespace(**base)


def test_pilot_log_records_retried_attempts_on_success(tmp_path, monkeypatch) -> None:
    fxt = _fixtures(tmp_path)
    monkeypatch.setattr(runner, "RESULTS_ROOT", tmp_path / "results")

    class FlakyOnce:
        name = "flaky"

        def __init__(self) -> None:
            self.first_call_by_prompt: dict[str, bool] = {}

        def generate(self, system, user, config):
            key = user[:32]
            if not self.first_call_by_prompt.get(key, False):
                self.first_call_by_prompt[key] = True
                raise providers.TransientProviderError("503 UNAVAILABLE")
            return providers.MockProvider().generate(system, user, config)

    ns = _pilot_ns(fxt, FlakyOnce(), run_id="rLogOk")
    rc = runner.cmd_pilot(ns)
    assert rc == 0
    raw = next((tmp_path / "results").rglob("rLogOk/raw_outputs.jsonl"))
    rows = [json.loads(l) for l in raw.read_text().splitlines() if l.strip()]
    assert rows
    sample = rows[0]
    assert sample["status"] == "ok"
    assert sample["retried_attempts"] == 1
    assert "cumulative_retry_delay_s" in sample
    assert sample["retry_attempts"][0]["error_class"] == "transient"


def test_pilot_log_records_persistent_failure(tmp_path, monkeypatch) -> None:
    fxt = _fixtures(tmp_path)
    monkeypatch.setattr(runner, "RESULTS_ROOT", tmp_path / "results")

    class AlwaysTransient:
        name = "always_503"

        def generate(self, system, user, config):
            raise providers.TransientProviderError(
                "503 UNAVAILABLE: persistent high demand"
            )

    ns = _pilot_ns(fxt, AlwaysTransient(), retry_max=2, run_id="rLogErr")
    rc = runner.cmd_pilot(ns)
    assert rc == 0
    err_path = next((tmp_path / "results").rglob("rLogErr/errors.jsonl"))
    err_rows = [json.loads(l) for l in err_path.read_text().splitlines() if l.strip()]
    assert err_rows, "expected errors.jsonl to record persistent failures"
    sample = err_rows[0]
    assert sample["status"] == "error"
    # initial + 2 retries = 3 attempts recorded
    assert sample["retried_attempts"] == 3
    assert sample["final_error_class"] == "transient"
    assert sample["attempts"][-1]["error_class"] == "transient"
    # Failures are not hidden — raw_outputs must NOT contain this run_id.
    raw_path = err_path.parent / "raw_outputs.jsonl"
    if raw_path.exists():
        raw_ids = {json.loads(l)["run_id"]
                   for l in raw_path.read_text().splitlines() if l.strip()}
        assert sample["run_id"] not in raw_ids


def test_pilot_does_not_retry_on_permanent_error(tmp_path, monkeypatch) -> None:
    fxt = _fixtures(tmp_path)
    monkeypatch.setattr(runner, "RESULTS_ROOT", tmp_path / "results")

    class PermFail:
        name = "perm"

        def __init__(self) -> None:
            self.calls = 0

        def generate(self, system, user, config):
            self.calls += 1
            raise providers.ProviderError("invalid API key (config error)")

    perm = PermFail()
    ns = _pilot_ns(fxt, perm, retry_max=5, run_id="rPerm")
    rc = runner.cmd_pilot(ns)
    assert rc == 0
    # 1 user * 6 families * 3 conditions = 18 prompts. Each must call exactly
    # ONCE — retries are forbidden for permanent errors.
    assert perm.calls == 18, perm.calls
    err_path = next((tmp_path / "results").rglob("rPerm/errors.jsonl"))
    sample = json.loads(err_path.read_text().splitlines()[0])
    assert sample["final_error_class"] == "permanent"
    assert sample["retried_attempts"] == 1


def test_runner_caps_retry_max(tmp_path) -> None:
    fxt = _fixtures(tmp_path)
    ns = _pilot_ns(fxt, providers.MockProvider(), retry_max=99,
                   run_id="rCap")
    with pytest.raises(runner.RunnerError, match="retry-max"):
        runner.cmd_pilot(ns)


def test_runner_caps_retry_backoff_max(tmp_path) -> None:
    fxt = _fixtures(tmp_path)
    ns = _pilot_ns(fxt, providers.MockProvider(), retry_backoff_max=999.0,
                   run_id="rCap2")
    with pytest.raises(runner.RunnerError, match="retry-backoff-max"):
        runner.cmd_pilot(ns)


def test_manifest_records_retry_settings(tmp_path, monkeypatch) -> None:
    fxt = _fixtures(tmp_path)
    monkeypatch.setattr(runner, "RESULTS_ROOT", tmp_path / "results")
    ns = _pilot_ns(fxt, providers.MockProvider(), retry_max=4,
                   retry_backoff=2.0, retry_backoff_max=10.0,
                   retry_jitter=0.25, run_id="rManifest")
    runner.cmd_pilot(ns)
    manifest_path = next((tmp_path / "results").rglob("rManifest/run_manifest.json"))
    manifest = json.loads(manifest_path.read_text())
    exec_cfg = manifest["execution"]
    assert exec_cfg["retry_max"] == 4
    assert exec_cfg["retry_backoff_s"] == 2.0
    assert exec_cfg["retry_backoff_max_s"] == 10.0
    assert exec_cfg["retry_jitter"] == 0.25
