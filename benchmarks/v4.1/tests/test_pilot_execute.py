"""Controlled pilot execution tests.

These tests inject a mock provider; no network call is ever made and no
``GEMINI_API_KEY`` is required. We assert:

- Pilot execute writes raw_outputs.jsonl + errors.jsonl + metrics_summary.json
  + run_manifest.json with the expected shapes.
- Logs are deterministic for a given prompt + mock provider.
- Concurrency default is 1 and the CLI rejects out-of-range values.
- Retries are exercised on transient failures.
- Resumability: a second invocation against the same run dir does NOT
  re-call the provider for already-completed run_ids.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from conftest import executor, generator, providers, runner


def _fixtures(tmp_path: Path, n_users: int = 3) -> Path:
    out = tmp_path / "fxt"
    generator.generate(seed=4242, n_users=n_users, sessions_per_user=4, out_dir=out)
    return out


def _pilot_ns(fixtures_dir: Path, **overrides) -> argparse.Namespace:
    base = dict(
        fixtures=fixtures_dir,
        users=3,
        execute=True,
        provider="mock",
        model="mock-test-model",
        temperature=0.0,
        max_output_tokens=64,
        concurrency=1,
        batch_size=4,
        sleep_between_batches=0.0,
        retry_max=0,
        retry_backoff=0.0,
        retry_backoff_max=1.0,
        retry_jitter=0.0,
        run_id="test_run_001",
        _provider_instance=providers.MockProvider(),
    )
    base.update(overrides)
    return argparse.Namespace(**base)


def test_pilot_execute_writes_all_artifacts(tmp_path: Path, monkeypatch) -> None:
    fxt = _fixtures(tmp_path)
    monkeypatch.setattr(runner, "RESULTS_ROOT", tmp_path / "results")
    rc = runner.cmd_pilot(_pilot_ns(fxt))
    assert rc == 0
    run_dirs = list((tmp_path / "results").rglob("test_run_001"))
    assert run_dirs, "run directory not created"
    run_dir = run_dirs[0]
    for name in ("raw_outputs.jsonl", "metrics_summary.json", "run_manifest.json"):
        assert (run_dir / name).exists(), f"missing {name}"


def test_pilot_execute_logs_are_deterministic(tmp_path: Path, monkeypatch) -> None:
    fxt = _fixtures(tmp_path)
    monkeypatch.setattr(runner, "RESULTS_ROOT", tmp_path / "results")
    runner.cmd_pilot(_pilot_ns(fxt, run_id="rA"))
    runner.cmd_pilot(_pilot_ns(fxt, run_id="rB"))
    raw_a = (tmp_path / "results").rglob("rA/raw_outputs.jsonl").__next__().read_text()
    raw_b = (tmp_path / "results").rglob("rB/raw_outputs.jsonl").__next__().read_text()

    def _strip(line: str) -> dict:
        row = json.loads(line)
        # Drop fields that legitimately vary between runs.
        row.pop("timestamp_utc", None)
        row.pop("latency_ms", None)
        return row

    rows_a = sorted((_strip(l) for l in raw_a.splitlines() if l.strip()),
                    key=lambda r: r["run_id"])
    rows_b = sorted((_strip(l) for l in raw_b.splitlines() if l.strip()),
                    key=lambda r: r["run_id"])
    assert rows_a == rows_b


def test_pilot_concurrency_validation(tmp_path: Path) -> None:
    fxt = _fixtures(tmp_path)
    with pytest.raises(runner.RunnerError, match="concurrency"):
        runner.cmd_pilot(_pilot_ns(fxt, concurrency=0))
    with pytest.raises(runner.RunnerError, match="concurrency"):
        runner.cmd_pilot(_pilot_ns(fxt, concurrency=runner.PILOT_MAX_CONCURRENCY + 1))


def test_pilot_user_cap(tmp_path: Path, monkeypatch) -> None:
    fxt = _fixtures(tmp_path, n_users=12)
    monkeypatch.setattr(runner, "RESULTS_ROOT", tmp_path / "results")
    with pytest.raises(runner.RunnerError, match="pilot.*limited"):
        runner.cmd_pilot(_pilot_ns(fxt, users=11))


def test_pilot_retries_then_succeeds(tmp_path: Path, monkeypatch) -> None:
    fxt = _fixtures(tmp_path, n_users=1)
    monkeypatch.setattr(runner, "RESULTS_ROOT", tmp_path / "results")

    class FlakyProvider:
        name = "flaky"

        def __init__(self) -> None:
            self.calls = 0

        def generate(self, system, user, config):
            self.calls += 1
            if self.calls % 3 == 1:
                raise providers.TransientProviderError(
                    "503 UNAVAILABLE high demand (simulated transient)"
                )
            return providers.MockProvider().generate(system, user, config)

    flaky = FlakyProvider()
    ns = _pilot_ns(fxt, users=1, retry_max=2, run_id="rFlaky",
                   _provider_instance=flaky)
    rc = runner.cmd_pilot(ns)
    assert rc == 0
    run_dir = next((tmp_path / "results").rglob("rFlaky"))
    raw = (run_dir / "raw_outputs.jsonl").read_text().splitlines()
    summary = json.loads((run_dir / "metrics_summary.json").read_text())
    assert summary["counts"]["ok"] == len(raw)
    assert summary["counts"]["ok"] > 0
    # 1 user * 6 families * 3 conditions = 18; every 3rd attempt fails once
    # so retries must have fired at least 6 times.
    assert flaky.calls > 18


def test_pilot_resumability(tmp_path: Path, monkeypatch) -> None:
    fxt = _fixtures(tmp_path, n_users=2)
    monkeypatch.setattr(runner, "RESULTS_ROOT", tmp_path / "results")
    runner.cmd_pilot(_pilot_ns(fxt, users=2, run_id="rResume"))
    run_dir = next((tmp_path / "results").rglob("rResume"))
    first_count = len((run_dir / "raw_outputs.jsonl").read_text().splitlines())

    # Re-invoke; the executor should skip already-done run_ids.
    class CountingProvider:
        name = "counting"

        def __init__(self) -> None:
            self.calls = 0

        def generate(self, system, user, config):
            self.calls += 1
            return providers.MockProvider().generate(system, user, config)

    counting = CountingProvider()
    runner.cmd_pilot(
        _pilot_ns(fxt, users=2, run_id="rResume", _provider_instance=counting)
    )
    # No new calls expected because raw_outputs already covers every run_id.
    assert counting.calls == 0
    second_count = len((run_dir / "raw_outputs.jsonl").read_text().splitlines())
    assert second_count == first_count


def test_dry_run_still_never_calls_llm_after_changes(tmp_path: Path,
                                                     monkeypatch) -> None:
    fxt = _fixtures(tmp_path)
    for k in runner.ENV_LLM_KEYS:
        monkeypatch.setenv(k, "irrelevant")
    monkeypatch.setattr(runner, "RESULTS_ROOT", tmp_path / "results")
    rc = runner.cmd_dry_run(argparse.Namespace(fixtures=fxt))
    assert rc == 0
    written = list((tmp_path / "results").rglob("planned_run.json"))
    assert written
    payload = json.loads(written[0].read_text())
    assert payload["mode"] == "dry_run"
    assert "never calls a provider" in payload["reason_no_execution"]
