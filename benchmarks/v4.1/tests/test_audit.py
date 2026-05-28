"""Pilot audit tests."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from conftest import audit, generator, providers, runner


def _run_pilot(tmp_path: Path, monkeypatch, run_id: str = "rAudit") -> Path:
    fxt = tmp_path / "fxt"
    generator.generate(seed=4242, n_users=2, sessions_per_user=4, out_dir=fxt)
    monkeypatch.setattr(runner, "RESULTS_ROOT", tmp_path / "results")
    ns = argparse.Namespace(
        fixtures=fxt, users=2, execute=True, provider="mock",
        model="m-audit", temperature=0.0, max_output_tokens=64,
        concurrency=1, batch_size=4, sleep_between_batches=0.0,
        retry_max=0, run_id=run_id,
        _provider_instance=providers.MockProvider(),
    )
    runner.cmd_pilot(ns)
    return next((tmp_path / "results").rglob(run_id))


def test_audit_pass_on_clean_run(tmp_path: Path, monkeypatch) -> None:
    run_dir = _run_pilot(tmp_path, monkeypatch)
    report = audit.audit_run(run_dir)
    assert report["passed"], report["failures"]
    assert report["checks"]["condition_balance"]["balanced"]
    assert report["checks"]["coverage"]["ok"] > 0
    assert report["checks"]["coverage"]["errors"] == 0
    # Per-condition stats exist for all 3 conditions.
    per_c = report["checks"]["per_condition"]
    assert set(per_c) == {"no_klickd", "xklickd_lite", "xklickd_pro"}


def test_audit_detects_secret_pattern(tmp_path: Path, monkeypatch) -> None:
    run_dir = _run_pilot(tmp_path, monkeypatch, run_id="rSecret")
    raw_path = run_dir / "raw_outputs.jsonl"
    poisoned = raw_path.read_text().splitlines()
    row = json.loads(poisoned[0])
    row["output_text"] = "leaked AIzaSyA1234567890abcdefghijklmnopqrstuv key"
    poisoned[0] = json.dumps(row, sort_keys=True)
    raw_path.write_text("\n".join(poisoned) + "\n")
    report = audit.audit_run(run_dir)
    assert not report["passed"]
    assert any("secret_scan" in f for f in report["failures"])


def test_audit_detects_model_inconsistency(tmp_path: Path, monkeypatch) -> None:
    run_dir = _run_pilot(tmp_path, monkeypatch, run_id="rModel")
    raw_path = run_dir / "raw_outputs.jsonl"
    lines = raw_path.read_text().splitlines()
    row = json.loads(lines[0])
    row["model"] = "different-model"
    lines[0] = json.dumps(row, sort_keys=True)
    raw_path.write_text("\n".join(lines) + "\n")
    report = audit.audit_run(run_dir)
    assert not report["passed"]
    assert any("model_consistency" in f for f in report["failures"])


def test_audit_writes_markdown(tmp_path: Path, monkeypatch) -> None:
    run_dir = _run_pilot(tmp_path, monkeypatch, run_id="rMd")
    report = audit.audit_run(run_dir)
    out = run_dir / "audit_report.md"
    audit.write_markdown(report, out)
    text = out.read_text()
    assert "Pilot audit report" in text
    assert "rMd" in text
