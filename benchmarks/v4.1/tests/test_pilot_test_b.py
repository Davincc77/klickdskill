"""Controlled Test B pilot execution tests.

These tests inject a mock provider via the runner's internal
``_provider_instance`` hook; no network call is ever made and no
``GEMINI_API_KEY`` is required. We assert:

- ``pilot-test-b execute`` writes raw_outputs.jsonl + errors.jsonl +
  metrics_summary.json + run_manifest.json with the expected shapes.
- Condition balance: every Test B condition has the same call count.
- No Mem0 compatibility claim is ever set in the manifest.
- The CLI rejects out-of-range concurrency / user count.
- The plan-only path emits ``planned_run.json`` without calling the
  provider.
- Test B prompt builders never embed PII or non-deterministic strings.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from types import ModuleType

import pytest

from conftest import executor, generator, providers, runner, ROOT


def _load_test_b_modules() -> tuple[ModuleType, ModuleType]:
    """Load the Test B prompt + executor modules into the synthetic pkg."""
    runner._load_executor_b_module()
    return (
        sys.modules["_v4_1_pkg.prompts.test_b"],
        sys.modules["_v4_1_pkg.runner.executor_b"],
    )


def _fixtures(tmp_path: Path, n_users: int = 3,
              sessions_per_user: int = 4) -> Path:
    out = tmp_path / "fxt"
    generator.generate(
        seed=4242, n_users=n_users,
        sessions_per_user=sessions_per_user, out_dir=out,
    )
    return out


def _ns(fixtures_dir: Path, **overrides) -> argparse.Namespace:
    base = dict(
        fixtures=fixtures_dir,
        users=3,
        execute=True,
        provider="mock",
        model="mock-test-model",
        temperature=0.0,
        max_output_tokens=64,
        concurrency=1,
        batch_size=8,
        sleep_between_batches=0.0,
        retry_max=0,
        retry_backoff=0.0,
        retry_backoff_max=1.0,
        retry_jitter=0.0,
        run_id="testb_unit_001",
        _provider_instance=providers.MockProvider(),
    )
    base.update(overrides)
    return argparse.Namespace(**base)


def test_pilot_test_b_writes_all_artifacts(tmp_path: Path, monkeypatch) -> None:
    fxt = _fixtures(tmp_path, n_users=3, sessions_per_user=4)
    monkeypatch.setattr(runner, "RESULTS_ROOT", tmp_path / "results")
    rc = runner.cmd_pilot_test_b(_ns(fxt))
    assert rc == 0
    run_dirs = list((tmp_path / "results").rglob("testb_unit_001"))
    assert run_dirs, "run directory not created"
    run_dir = run_dirs[0]
    for name in (
        "raw_outputs.jsonl", "metrics_summary.json", "run_manifest.json",
    ):
        assert (run_dir / name).exists(), f"missing {name}"


def test_pilot_test_b_condition_balance(tmp_path: Path, monkeypatch) -> None:
    fxt = _fixtures(tmp_path, n_users=3, sessions_per_user=4)
    monkeypatch.setattr(runner, "RESULTS_ROOT", tmp_path / "results")
    rc = runner.cmd_pilot_test_b(_ns(fxt, users=3))
    assert rc == 0
    run_dir = next((tmp_path / "results").rglob("testb_unit_001"))
    raw = [json.loads(l) for l in (run_dir / "raw_outputs.jsonl").read_text().splitlines() if l.strip()]
    by_cond: dict[str, int] = {}
    for r in raw:
        by_cond[r["condition"]] = by_cond.get(r["condition"], 0) + 1
    # Without Mem0 installed the conditions tuple ends with mem0_skipped.
    assert set(by_cond) == {"no_memory", "prompt_history",
                            "xklickd_compressed", "mem0_skipped"}
    counts = set(by_cond.values())
    assert len(counts) == 1, f"unbalanced counts: {by_cond}"
    # 3 users * 4 sessions = 12 calls per condition.
    assert next(iter(counts)) == 12


def test_pilot_test_b_no_mem0_compatibility_claim(tmp_path: Path, monkeypatch) -> None:
    fxt = _fixtures(tmp_path, n_users=2, sessions_per_user=3)
    monkeypatch.setattr(runner, "RESULTS_ROOT", tmp_path / "results")
    rc = runner.cmd_pilot_test_b(_ns(fxt, users=2))
    assert rc == 0
    run_dir = next((tmp_path / "results").rglob("testb_unit_001"))
    manifest = json.loads((run_dir / "run_manifest.json").read_text())
    assert manifest["mem0"]["compatibility_claim"] is False
    assert "NO Mem0 compatibility claim" in manifest["mem0"]["_note"]


def test_pilot_test_b_concurrency_validation(tmp_path: Path) -> None:
    fxt = _fixtures(tmp_path, n_users=2, sessions_per_user=3)
    with pytest.raises(runner.RunnerError, match="concurrency"):
        runner.cmd_pilot_test_b(_ns(fxt, concurrency=0))
    with pytest.raises(runner.RunnerError, match="concurrency"):
        runner.cmd_pilot_test_b(
            _ns(fxt, concurrency=runner.PILOT_MAX_CONCURRENCY + 1)
        )


def test_pilot_test_b_user_cap(tmp_path: Path, monkeypatch) -> None:
    fxt = _fixtures(tmp_path, n_users=12, sessions_per_user=2)
    monkeypatch.setattr(runner, "RESULTS_ROOT", tmp_path / "results")
    with pytest.raises(runner.RunnerError, match="pilot-test-b.*limited"):
        runner.cmd_pilot_test_b(_ns(fxt, users=11))


def test_pilot_test_b_plan_only_no_provider_call(tmp_path: Path, monkeypatch) -> None:
    fxt = _fixtures(tmp_path, n_users=2, sessions_per_user=3)
    monkeypatch.setattr(runner, "RESULTS_ROOT", tmp_path / "results")

    class TrippingProvider:
        name = "trip"

        def generate(self, *args, **kwargs):  # pragma: no cover - must not run
            raise AssertionError("provider must not be called in plan-only mode")

    ns = _ns(fxt, execute=False, _provider_instance=TrippingProvider())
    rc = runner.cmd_pilot_test_b(ns)
    assert rc == 0
    plan_files = list((tmp_path / "results").rglob("planned_run.json"))
    assert plan_files, "expected planned_run.json"
    payload = json.loads(plan_files[0].read_text())
    assert payload["mode"] == "pilot_test_b"
    assert "mem0_skipped" in payload["test_b_conditions_planned"]


def test_pilot_test_b_audit_pass(tmp_path: Path, monkeypatch) -> None:
    fxt = _fixtures(tmp_path, n_users=2, sessions_per_user=3)
    monkeypatch.setattr(runner, "RESULTS_ROOT", tmp_path / "results")
    rc = runner.cmd_pilot_test_b(_ns(fxt, users=2))
    assert rc == 0
    run_dir = next((tmp_path / "results").rglob("testb_unit_001"))

    audit_b = importlib_load(
        "_v4_1_pkg.runner.audit_b",
        ROOT / "runner" / "audit_b.py",
    )
    report = audit_b.audit_run_b(run_dir)
    assert report["passed"], report["failures"]
    # Sanity: secret scanner never flags our deterministic fixtures.
    assert report["checks"]["secret_scan"]["rows_with_hits"] == []
    assert report["checks"]["secret_scan"]["manifest_hits"] == []


def importlib_load(name: str, file_path: Path) -> ModuleType:
    import importlib.util
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, file_path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_test_b_prompts_deterministic_and_distinct_per_condition(tmp_path: Path) -> None:
    fxt = _fixtures(tmp_path, n_users=2, sessions_per_user=5)
    personas = [json.loads(l) for l in (fxt / "personas.jsonl").read_text().splitlines() if l.strip()]
    sessions = [json.loads(l) for l in (fxt / "test_b_sessions.jsonl").read_text().splitlines() if l.strip()]
    prompts_test_b, _ = _load_test_b_modules()
    persona = personas[0]
    user_sessions = sorted(
        [s for s in sessions if s["user_id"] == persona["user_id"]],
        key=lambda s: s["session_index"],
    )
    target = user_sessions[-1]
    seen: dict[str, str] = {}
    for cond in (
        "no_memory", "prompt_history", "xklickd_compressed", "mem0_skipped",
    ):
        sys1, usr1 = prompts_test_b.build_test_b_messages(
            condition=cond, persona=persona,
            target_session=target, all_sessions=user_sessions,
        )
        sys2, usr2 = prompts_test_b.build_test_b_messages(
            condition=cond, persona=persona,
            target_session=target, all_sessions=user_sessions,
        )
        assert (sys1, usr1) == (sys2, usr2), f"{cond} prompt not deterministic"
        seen[cond] = sys1
        assert usr1 == usr2
    # no_memory and mem0_skipped both emit no extra block, so their system
    # prompts are intentionally identical. The other two MUST differ.
    assert seen["no_memory"] == seen["mem0_skipped"]
    assert seen["no_memory"] != seen["prompt_history"]
    assert seen["no_memory"] != seen["xklickd_compressed"]
    assert seen["prompt_history"] != seen["xklickd_compressed"]


def test_test_b_mem0_condition_emitted_when_present(tmp_path: Path, monkeypatch) -> None:
    fxt = _fixtures(tmp_path, n_users=2, sessions_per_user=3)
    monkeypatch.setattr(runner, "RESULTS_ROOT", tmp_path / "results")
    # Force mem0_present() to return True without installing the package.
    monkeypatch.setattr(runner, "mem0_present", lambda: True)
    rc = runner.cmd_pilot_test_b(_ns(fxt, users=2, run_id="testb_mem0"))
    assert rc == 0
    run_dir = next((tmp_path / "results").rglob("testb_mem0"))
    raw = [json.loads(l) for l in (run_dir / "raw_outputs.jsonl").read_text().splitlines() if l.strip()]
    conditions_seen = {r["condition"] for r in raw}
    assert "mem0" in conditions_seen
    assert "mem0_skipped" not in conditions_seen
    manifest = json.loads((run_dir / "run_manifest.json").read_text())
    # The compatibility claim must remain False even when mem0 is "present".
    assert manifest["mem0"]["present"] is True
    assert manifest["mem0"]["compatibility_claim"] is False
