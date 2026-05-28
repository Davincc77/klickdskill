"""Runner safety guards: no LLM in dry-run, full-run requires all approvals."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import pytest

from conftest import generator, runner


@pytest.fixture
def fixtures_dir(tmp_path: Path) -> Path:
    out = tmp_path / "fxt"
    generator.generate(seed=4242, n_users=5, sessions_per_user=4, out_dir=out)
    return out


_PILOT_DEFAULTS = dict(
    execute=False,
    provider="gemini",
    model="gemini-2.5-flash",
    temperature=0.2,
    max_output_tokens=512,
    concurrency=1,
    batch_size=10,
    sleep_between_batches=0.0,
    retry_max=2,
    retry_backoff=2.0,
    retry_backoff_max=30.0,
    retry_jitter=0.25,
    run_id=None,
    _provider_instance=None,
)


def _ns(**kw):
    return argparse.Namespace(**kw)


def _pilot_ns(**kw):
    base = dict(_PILOT_DEFAULTS)
    base.update(kw)
    return argparse.Namespace(**base)


def test_dry_run_never_calls_llm(fixtures_dir: Path, monkeypatch, tmp_path: Path) -> None:
    """Even with API keys set, dry-run must not attempt provider calls.

    We assert by monkeypatching every env var that *would* be checked, and
    confirming dry-run still completes without invoking a hypothetical client.
    """
    for k in runner.ENV_LLM_KEYS:
        monkeypatch.setenv(k, "test-key")
    monkeypatch.setattr(runner, "RESULTS_ROOT", tmp_path / "results")
    rc = runner.cmd_dry_run(_ns(fixtures=fixtures_dir))
    assert rc == 0
    written = list((tmp_path / "results").rglob("planned_run.json"))
    assert written, "dry-run did not write planned_run.json"
    payload = json.loads(written[0].read_text())
    assert payload["mode"] == "dry_run"
    assert "never calls a provider" in payload["reason_no_execution"]


def test_pilot_caps_at_10_users(fixtures_dir: Path) -> None:
    ns = _pilot_ns(fixtures=fixtures_dir, users=11)
    with pytest.raises(runner.RunnerError, match="pilot.*limited"):
        runner.cmd_pilot(ns)


def test_pilot_without_llm_emits_plan_only(fixtures_dir: Path, monkeypatch,
                                            tmp_path: Path) -> None:
    for k in runner.ENV_LLM_KEYS:
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setattr(runner, "RESULTS_ROOT", tmp_path / "results")
    rc = runner.cmd_pilot(_pilot_ns(fixtures=fixtures_dir, users=5))
    assert rc == 0
    written = list((tmp_path / "results").rglob("planned_run.json"))
    assert written
    payload = json.loads(written[0].read_text())
    assert payload["mode"] == "pilot"
    assert payload["llm_configured"] is False


def test_full_run_requires_confirm_flag(fixtures_dir: Path) -> None:
    ns = _ns(fixtures=fixtures_dir, confirm_full_run=False)
    with pytest.raises(runner.RunnerError, match="--confirm-full-run"):
        runner.cmd_full(ns)


def test_full_run_requires_env_var(fixtures_dir: Path, monkeypatch) -> None:
    monkeypatch.delenv(runner.ENV_FULL_APPROVAL, raising=False)
    ns = _ns(fixtures=fixtures_dir, confirm_full_run=True)
    with pytest.raises(runner.RunnerError, match="environment variable"):
        runner.cmd_full(ns)


def test_full_run_requires_snapshot(fixtures_dir: Path, monkeypatch,
                                     tmp_path: Path) -> None:
    monkeypatch.setenv(runner.ENV_FULL_APPROVAL, "1")
    monkeypatch.setattr(runner, "SNAPSHOTS_ROOT", tmp_path / "no_snap")
    ns = _ns(fixtures=fixtures_dir, confirm_full_run=True)
    with pytest.raises(runner.RunnerError, match="snapshot"):
        runner.cmd_full(ns)


def test_full_run_refuses_even_with_all_preconditions(fixtures_dir: Path,
                                                      monkeypatch,
                                                      tmp_path: Path) -> None:
    """Even with all gates passed, the run is refused: no adapter wired."""
    monkeypatch.setenv(runner.ENV_FULL_APPROVAL, "1")
    snap_root = tmp_path / "snaps"
    today = runner._utcnow_date()
    (snap_root / today).mkdir(parents=True)
    monkeypatch.setattr(runner, "SNAPSHOTS_ROOT", snap_root)
    ns = _ns(fixtures=fixtures_dir, confirm_full_run=True)
    with pytest.raises(runner.RunnerError, match="adapter is not wired"):
        runner.cmd_full(ns)
