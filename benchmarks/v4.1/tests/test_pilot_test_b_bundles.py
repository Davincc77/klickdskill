"""Tests for the bundle-based Test B 'real project' design.

These tests cover:

- The bundle generator produces the exact set of bundles, phases, and
  conditions required by the final design.
- The full design produces 9000 call specs (5 bundles x 150 sessions
  x 12 conditions) and the long pilot produces 1800 (1 x 150 x 12).
- Every condition has the same call count when expanded.
- The runner refuses --full-design, refuses --bundles > 1, refuses
  concurrency > 2, and refuses sessions_per_bundle > 150.
- The plan-only path emits planned_run.json without calling the
  provider and reports expected_outputs = 1800 by default.
- Execute path (mock provider) writes raw_outputs.jsonl with all 12
  conditions; the audit script PASSes.
- The bundle audit script flags forbidden Mem0 compatibility claims
  and forbidden 'full benchmark result' claim phrases.
- The manual-only workflow imposes the documented caps.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

from conftest import providers, runner, ROOT


def _load_module(name: str, path: Path) -> ModuleType:
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


bundles_mod = _load_module(
    "v4_1_bundles_generator", ROOT / "fixtures" / "bundles.py"
)


def _load_test_b_bundle_modules() -> tuple[ModuleType, ModuleType]:
    runner._load_executor_b_bundles_module()
    return (
        sys.modules["_v4_1_pkg.prompts.test_b_bundles"],
        sys.modules["_v4_1_pkg.runner.executor_b_bundles"],
    )


def _gen_fixtures(tmp_path: Path, n_bundles: int = 1,
                  sessions_per_bundle: int = 150) -> Path:
    out = tmp_path / "fxt_bundles"
    bundles_mod.generate(
        seed=4242,
        out_dir=out,
        n_bundles=n_bundles,
        sessions_per_bundle=sessions_per_bundle,
    )
    return out


def _ns(fixtures_dir: Path, **overrides) -> argparse.Namespace:
    base = dict(
        fixtures=fixtures_dir,
        bundles=1,
        bundle_index=0,
        sessions_per_bundle=150,
        execute=True,
        provider="mock",
        model="mock-bundle-model",
        temperature=0.0,
        max_output_tokens=64,
        concurrency=1,
        batch_size=64,
        sleep_between_batches=0.0,
        retry_max=0,
        retry_backoff=0.0,
        retry_backoff_max=1.0,
        retry_jitter=0.0,
        run_id="bundle_unit_001",
        full_design=False,
        _provider_instance=providers.MockProvider(),
    )
    base.update(overrides)
    return argparse.Namespace(**base)


# ---------------------------------------------------------------------------
# Design counts: 5 bundles, 150 sessions, 12 conditions
# ---------------------------------------------------------------------------
def test_bundles_design_constants() -> None:
    assert len(bundles_mod.BUNDLES) == 5
    assert len(bundles_mod.PHASES) == 10
    assert len(bundles_mod.TEST_B_BUNDLE_CONDITIONS) == 12
    # Phases cover sessions 1..150 contiguously.
    cursor = 1
    for p in bundles_mod.PHASES:
        assert p["first"] == cursor
        cursor = p["last"] + 1
    assert cursor == 151
    # Bundle roles match the approved list.
    bundle_ids = [b["bundle_id"] for b in bundles_mod.BUNDLES]
    assert bundle_ids == [
        "b01_ai_app_launch",
        "b02_video_media_campaign",
        "b03_security_compliance",
        "b04_research_policy_publication",
        "b05_drone_mission_ops",
    ]


def test_generator_counts_full_and_long_pilot(tmp_path: Path) -> None:
    fxt = _gen_fixtures(tmp_path, n_bundles=5, sessions_per_bundle=150)
    manifest = json.loads((fxt / "bundle_manifest.json").read_text())
    assert manifest["expected_counts"]["sessions_total"] == 5 * 150
    assert manifest["expected_counts"]["outputs_per_full_design"] == 9000
    assert manifest["expected_counts"]["outputs_per_pilot_long"] == 1800
    assert len(manifest["conditions"]) == 12
    # Sessions JSONL row count matches manifest.
    sessions = (fxt / "test_b_bundle_sessions.jsonl").read_text().splitlines()
    assert len(sessions) == 5 * 150


def test_expand_full_design_yields_9000_specs(tmp_path: Path) -> None:
    fxt = _gen_fixtures(tmp_path, n_bundles=5, sessions_per_bundle=150)
    prompts_bb, executor_bb = _load_test_b_bundle_modules()
    sessions = [
        json.loads(l) for l in
        (fxt / "test_b_bundle_sessions.jsonl").read_text().splitlines()
        if l.strip()
    ]
    calls = executor_bb.expand_bundle_calls(
        sessions=sessions,
        conditions=prompts_bb.TEST_B_BUNDLE_CONDITIONS,
    )
    assert len(calls) == 9000
    # Every condition has the same count.
    by_cond: dict[str, int] = {}
    for c in calls:
        by_cond[c["condition"]] = by_cond.get(c["condition"], 0) + 1
    assert set(by_cond) == set(prompts_bb.TEST_B_BUNDLE_CONDITIONS)
    assert len(set(by_cond.values())) == 1
    assert next(iter(by_cond.values())) == 5 * 150  # 750 per condition


def test_expand_long_pilot_yields_1800_specs(tmp_path: Path) -> None:
    fxt = _gen_fixtures(tmp_path, n_bundles=1, sessions_per_bundle=150)
    prompts_bb, executor_bb = _load_test_b_bundle_modules()
    sessions = [
        json.loads(l) for l in
        (fxt / "test_b_bundle_sessions.jsonl").read_text().splitlines()
        if l.strip()
    ]
    calls = executor_bb.expand_bundle_calls(
        sessions=sessions,
        conditions=prompts_bb.TEST_B_BUNDLE_CONDITIONS,
    )
    assert len(calls) == 1800
    by_cond: dict[str, int] = {}
    for c in calls:
        by_cond[c["condition"]] = by_cond.get(c["condition"], 0) + 1
    assert len(by_cond) == 12
    assert all(v == 150 for v in by_cond.values())


def test_phase_coverage_in_calls(tmp_path: Path) -> None:
    fxt = _gen_fixtures(tmp_path, n_bundles=1, sessions_per_bundle=150)
    prompts_bb, executor_bb = _load_test_b_bundle_modules()
    sessions = [
        json.loads(l) for l in
        (fxt / "test_b_bundle_sessions.jsonl").read_text().splitlines()
        if l.strip()
    ]
    calls = executor_bb.expand_bundle_calls(
        sessions=sessions,
        conditions=prompts_bb.TEST_B_BUNDLE_CONDITIONS,
    )
    phases = {c["phase_id"] for c in calls}
    assert len(phases) == 10  # all 10 phases represented


# ---------------------------------------------------------------------------
# Prompt determinism and condition distinctness
# ---------------------------------------------------------------------------
def test_bundle_prompts_deterministic_and_distinct(tmp_path: Path) -> None:
    fxt = _gen_fixtures(tmp_path, n_bundles=1, sessions_per_bundle=20)
    prompts_bb, _ = _load_test_b_bundle_modules()
    sessions = [
        json.loads(l) for l in
        (fxt / "test_b_bundle_sessions.jsonl").read_text().splitlines()
        if l.strip()
    ]
    target = sessions[-1]
    seen_systems: dict[str, str] = {}
    seen_users: dict[str, str] = {}
    for cond in prompts_bb.TEST_B_BUNDLE_CONDITIONS:
        s1, u1 = prompts_bb.build_test_b_bundle_messages(
            condition=cond, target_session=target, bundle_sessions=sessions,
        )
        s2, u2 = prompts_bb.build_test_b_bundle_messages(
            condition=cond, target_session=target, bundle_sessions=sessions,
        )
        assert (s1, u1) == (s2, u2), f"{cond} not deterministic"
        seen_systems[cond] = s1
        seen_users[cond] = u1
    # All conditions share the same user probe (fairness).
    distinct_users = set(seen_users.values())
    assert len(distinct_users) == 1, (
        "user probe must be identical across all conditions"
    )
    # System prompts must differ across the 12 conditions (no_memory is
    # the only one with no extra block; every other one prepends a
    # distinct header so the systems must be distinct from no_memory).
    no_memory_system = seen_systems["no_memory"]
    distinct_from_no_memory = {
        cond for cond, s in seen_systems.items()
        if s != no_memory_system
    }
    # Of the 12 conditions, 11 should differ from no_memory.
    assert len(distinct_from_no_memory) == 11


# ---------------------------------------------------------------------------
# Runner caps & full-run refusal
# ---------------------------------------------------------------------------
def test_runner_refuses_full_design(tmp_path: Path) -> None:
    fxt = _gen_fixtures(tmp_path, n_bundles=5, sessions_per_bundle=5)
    with pytest.raises(runner.RunnerError, match="not wired"):
        runner.cmd_pilot_test_b_bundles(
            _ns(fxt, full_design=True, sessions_per_bundle=5)
        )


def test_runner_refuses_more_than_one_bundle(tmp_path: Path) -> None:
    fxt = _gen_fixtures(tmp_path, n_bundles=5, sessions_per_bundle=5)
    with pytest.raises(runner.RunnerError, match="capped at"):
        runner.cmd_pilot_test_b_bundles(_ns(fxt, bundles=2,
                                            sessions_per_bundle=5))


def test_runner_concurrency_cap(tmp_path: Path) -> None:
    fxt = _gen_fixtures(tmp_path, n_bundles=1, sessions_per_bundle=5)
    with pytest.raises(runner.RunnerError, match="concurrency"):
        runner.cmd_pilot_test_b_bundles(
            _ns(fxt, concurrency=3, sessions_per_bundle=5)
        )
    with pytest.raises(runner.RunnerError, match="concurrency"):
        runner.cmd_pilot_test_b_bundles(
            _ns(fxt, concurrency=0, sessions_per_bundle=5)
        )


def test_runner_sessions_per_bundle_cap(tmp_path: Path) -> None:
    fxt = _gen_fixtures(tmp_path, n_bundles=1, sessions_per_bundle=5)
    with pytest.raises(runner.RunnerError, match="sessions-per-bundle"):
        runner.cmd_pilot_test_b_bundles(_ns(fxt, sessions_per_bundle=151))


# ---------------------------------------------------------------------------
# Plan-only and execute paths
# ---------------------------------------------------------------------------
def test_plan_only_emits_1800_outputs_estimate(tmp_path: Path,
                                                monkeypatch) -> None:
    fxt = _gen_fixtures(tmp_path, n_bundles=1, sessions_per_bundle=150)
    monkeypatch.setattr(runner, "RESULTS_ROOT", tmp_path / "results")

    class TrippingProvider:
        name = "trip"

        def generate(self, *args, **kwargs):  # pragma: no cover
            raise AssertionError(
                "provider must not be called in plan-only mode"
            )

    ns = _ns(fxt, execute=False, _provider_instance=TrippingProvider())
    rc = runner.cmd_pilot_test_b_bundles(ns)
    assert rc == 0
    plan_files = list((tmp_path / "results").rglob("planned_run.json"))
    assert plan_files
    payload = json.loads(plan_files[0].read_text())
    assert payload["mode"] == "pilot_test_b_bundles"
    assert payload["expected_outputs"] == 1800
    assert len(payload["test_b_bundle_conditions_planned"]) == 12
    assert payload["bundles_selected"] == ["b01_ai_app_launch"]


def test_execute_writes_raw_outputs(tmp_path: Path, monkeypatch) -> None:
    # Small bundle (10 sessions) so the smoke run is fast.
    fxt = _gen_fixtures(tmp_path, n_bundles=1, sessions_per_bundle=10)
    monkeypatch.setattr(runner, "RESULTS_ROOT", tmp_path / "results")
    rc = runner.cmd_pilot_test_b_bundles(
        _ns(fxt, sessions_per_bundle=10)
    )
    assert rc == 0
    run_dir = next((tmp_path / "results").rglob("bundle_unit_001"))
    raw = [
        json.loads(l) for l in
        (run_dir / "raw_outputs.jsonl").read_text().splitlines() if l.strip()
    ]
    # 1 bundle x 10 sessions x 12 conditions = 120 outputs.
    assert len(raw) == 120
    by_cond: dict[str, int] = {}
    for r in raw:
        by_cond[r["condition"]] = by_cond.get(r["condition"], 0) + 1
    assert len(by_cond) == 12
    assert all(v == 10 for v in by_cond.values())
    manifest = json.loads((run_dir / "run_manifest.json").read_text())
    assert manifest["expected_outputs"] == 120
    assert manifest["mem0"]["compatibility_claim"] is False
    assert manifest["bundle_ids"] == ["b01_ai_app_launch"]


def test_execute_audit_passes(tmp_path: Path, monkeypatch) -> None:
    fxt = _gen_fixtures(tmp_path, n_bundles=1, sessions_per_bundle=15)
    monkeypatch.setattr(runner, "RESULTS_ROOT", tmp_path / "results")
    rc = runner.cmd_pilot_test_b_bundles(
        _ns(fxt, sessions_per_bundle=15)
    )
    assert rc == 0
    run_dir = next((tmp_path / "results").rglob("bundle_unit_001"))
    audit_mod = _load_module(
        "_v4_1_audit_b_bundles_test", ROOT / "runner" / "audit_b_bundles.py"
    )
    report = audit_mod.audit_bundle_run(run_dir)
    assert report["passed"], report["failures"]
    # Condition balance check is part of hard checks.
    assert report["checks"]["condition_balance"]["balanced"] is True
    assert len(report["checks"]["condition_balance"]["by_condition"]) == 12
    assert report["checks"]["bundle_phase_session_coverage"][
        "by_bundle"
    ]["b01_ai_app_launch"] == 15 * 12


def test_audit_flags_forbidden_mem0_claim(tmp_path: Path,
                                          monkeypatch) -> None:
    fxt = _gen_fixtures(tmp_path, n_bundles=1, sessions_per_bundle=5)
    monkeypatch.setattr(runner, "RESULTS_ROOT", tmp_path / "results")
    rc = runner.cmd_pilot_test_b_bundles(
        _ns(fxt, sessions_per_bundle=5)
    )
    assert rc == 0
    run_dir = next((tmp_path / "results").rglob("bundle_unit_001"))
    manifest_path = run_dir / "run_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["mem0"]["compatibility_claim"] = True
    manifest_path.write_text(json.dumps(manifest, sort_keys=True))
    audit_mod = _load_module(
        "_v4_1_audit_b_bundles_test_mem0",
        ROOT / "runner" / "audit_b_bundles.py",
    )
    report = audit_mod.audit_bundle_run(run_dir)
    assert not report["passed"]
    assert any(
        "Mem0 compatibility claim" in f for f in report["failures"]
    )


def test_audit_flags_forbidden_claim_phrase(tmp_path: Path,
                                             monkeypatch) -> None:
    fxt = _gen_fixtures(tmp_path, n_bundles=1, sessions_per_bundle=5)
    monkeypatch.setattr(runner, "RESULTS_ROOT", tmp_path / "results")
    rc = runner.cmd_pilot_test_b_bundles(
        _ns(fxt, sessions_per_bundle=5)
    )
    assert rc == 0
    run_dir = next((tmp_path / "results").rglob("bundle_unit_001"))
    raw_path = run_dir / "raw_outputs.jsonl"
    rows = [json.loads(l) for l in raw_path.read_text().splitlines() if l.strip()]
    rows[0]["output_text"] = "This system is Mem0-compatible."
    raw_path.write_text(
        "\n".join(json.dumps(r, sort_keys=True) for r in rows) + "\n"
    )
    audit_mod = _load_module(
        "_v4_1_audit_b_bundles_test_claim",
        ROOT / "runner" / "audit_b_bundles.py",
    )
    report = audit_mod.audit_bundle_run(run_dir)
    assert not report["passed"]
    assert any("forbidden_claims" in f for f in report["failures"])


# ---------------------------------------------------------------------------
# Workflow caps
# ---------------------------------------------------------------------------
WORKFLOW_PATH = ROOT.parent.parent / ".github" / "workflows" \
    / "benchmark-v41-pilot-testb-bundles.yml"


def test_workflow_manual_only_and_caps_present() -> None:
    assert WORKFLOW_PATH.exists(), f"missing workflow at {WORKFLOW_PATH}"
    text = WORKFLOW_PATH.read_text()
    # workflow_dispatch only.
    assert "workflow_dispatch:" in text
    assert "on:\n  workflow_dispatch:" in text
    # No push/pull_request triggers.
    assert "\n  push:" not in text
    assert "\n  pull_request:" not in text
    # Bundle index range [0, 4]; concurrency cap 2; sessions cap 150.
    assert "bundle_index must be in [0, 4]" in text
    assert "concurrency must be in [1, 2]" in text
    assert "sessions_per_bundle must be in [1, 150]" in text
    # No publish/release steps. We allow the disclaimer ("no PyPI"...) but
    # forbid any actual publishing command.
    forbidden_substrings = (
        "npm publish",
        "twine upload",
        "pypa/gh-action-pypi-publish",
        "zenodo/zenodo-upload",
        "gh release create",
        "git push --tags",
    )
    for forbidden in forbidden_substrings:
        assert forbidden.lower() not in text.lower(), (
            f"workflow must not reference {forbidden}"
        )
    # Provider hard-locked to gemini.
    assert "provider must be 'gemini'" in text
    # The --full-design CLI flag must NOT appear as an actual command
    # argument in any run step. (It is fine for the comment header to
    # explain that the runner refuses it.)
    in_run_step = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("run:") or stripped.startswith("run: |"):
            in_run_step = True
            continue
        if stripped.startswith("- name:") or stripped.startswith("name:"):
            in_run_step = False
        if in_run_step and "--full-design" in stripped:
            raise AssertionError(
                "workflow must not pass --full-design to the runner"
            )
