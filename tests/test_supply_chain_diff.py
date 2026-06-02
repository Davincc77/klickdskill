"""Tests for scripts/generate_supply_chain_diff.py.

The logical-diff stage compares a previous skill/pack candidate against a new
one and classifies the changes that matter for governance, security and claim
discipline. These tests exercise the static fixtures under
tests/fixtures/supply_chain_diff/ plus a couple of in-memory edge cases.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "scripts" / "generate_supply_chain_diff.py"
FIX = REPO / "tests" / "fixtures" / "supply_chain_diff"


def _load_module():
    spec = importlib.util.spec_from_file_location("generate_supply_chain_diff", SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["generate_supply_chain_diff"] = mod
    spec.loader.exec_module(mod)
    return mod


diff = _load_module()

BEFORE = FIX / "before.json"


def _report(after_name: str) -> dict:
    return diff.build_report(BEFORE, FIX / after_name)


def _kinds(report: dict) -> set[str]:
    return {f["kind"] for f in report["findings"]}


# --- structural ------------------------------------------------------------


def test_report_is_valid_json_and_has_required_fields():
    report = _report("after_benign.json")
    rendered = json.dumps(report)  # must serialize
    parsed = json.loads(rendered)
    for field in (
        "schema_version",
        "before_path",
        "after_path",
        "before_hash",
        "after_hash",
        "deterministic_diff_id",
        "summary",
        "changed_paths",
        "findings",
        "high_risk_findings",
        "blocked_findings",
        "recommendations",
        "non_deterministic_zone",
    ):
        assert field in parsed, f"missing field {field}"
    assert parsed["deterministic_diff_id"].startswith("sha256:")


def test_unchanged_file_yields_stable_empty_diff():
    report = _report("after_unchanged.json")
    assert report["findings"] == []
    assert report["changed_paths"] == []
    assert report["summary"] == {"unchanged": 1}
    assert report["blocked_findings"] == []
    assert "UNCHANGED" in report["recommendations"][0]


def test_added_removed_changed_detected():
    report = _report("after_benign.json")
    # added competency esco:S2.0 ; pack_version changed (generic) ; non-blocking
    assert "added" in _kinds(report)
    assert report["blocked_findings"] == []
    paths = report["changed_paths"]
    assert any("competencies[esco:S2.0]" in p for p in paths)
    assert any("pack_version" in p for p in paths)


# --- guardrails (blocking) -------------------------------------------------


def test_guardrail_lowering_gate_level_blocks():
    report = _report("after_guardrail_lowered.json")
    blocked = report["blocked_findings"]
    assert blocked, "expected a blocking finding"
    assert all(f["blocking"] for f in blocked)
    assert any(f["kind"] == "guardrail_lowered" for f in blocked)
    assert "REJECT_OR_ROLLBACK" in report["recommendations"][0]


def test_non_lowerable_floor_removal_and_raise_only_block():
    report = _report("after_floor_removed.json")
    details = [f["detail"] for f in report["blocked_findings"]]
    assert any("non-lowerable floor" in d for d in details)
    assert any("raise_only disabled" in d for d in details)


def test_evidence_weakening_blocks_and_flags_change():
    report = _report("after_evidence_weakened.json")
    kinds = _kinds(report)
    assert "evidence_changed" in kinds
    assert any(
        f["kind"] == "guardrail_lowered" and "evidence" in f["detail"]
        for f in report["blocked_findings"]
    )


def test_governance_owner_move_off_human_blocks():
    report = _report("after_governance_violation.json")
    assert any(
        f["kind"] == "guardrail_lowered"
        and "final_decision_owner" in f["path"]
        for f in report["blocked_findings"]
    )
    # agent_role advisory -> autonomous is risk_raised (non-blocking)
    assert any(f["kind"] == "risk_raised" for f in report["findings"])


# --- claim / public boundary (blocking) ------------------------------------


def test_claim_boundary_violation_detected():
    report = _report("after_claim_violation.json")
    details = [f["detail"] for f in report["blocked_findings"]]
    assert any("claims v4.1 GA" in d for d in details)
    assert any("banned claim introduced" in d for d in details)
    assert "claim_boundary_changed" in _kinds(report)


def test_public_boundary_violation_detected():
    report = _report("after_public_violation.json")
    details = [f["detail"] for f in report["blocked_findings"]]
    assert any("codename leaked" in d for d in details)
    assert any("contains_real_pii now true" in d for d in details)
    assert any("forbidden_fields entry" in d for d in details)


def test_memory_policy_change_flagged_non_blocking():
    report = _report("after_memory_changed.json")
    assert "memory_policy_changed" in _kinds(report)
    assert report["blocked_findings"] == []
    assert "PREMIUM_PASS_REQUIRED" not in report["recommendations"][0]


# --- determinism -----------------------------------------------------------


def test_diff_id_is_deterministic_across_runs():
    r1 = _report("after_guardrail_lowered.json")
    r2 = _report("after_guardrail_lowered.json")
    assert r1["deterministic_diff_id"] == r2["deterministic_diff_id"]
    assert r1["findings"] == r2["findings"]


def test_diff_id_changes_when_content_changes():
    r1 = _report("after_benign.json")
    r2 = _report("after_guardrail_lowered.json")
    assert r1["deterministic_diff_id"] != r2["deterministic_diff_id"]


# --- CLI exit codes --------------------------------------------------------


def test_cli_exit_zero_on_unchanged():
    rc = diff.main(
        ["prog", "--before", str(BEFORE), "--after", str(FIX / "after_unchanged.json"), "--quiet"]
    )
    assert rc == 0


def test_cli_exit_one_on_blocking():
    rc = diff.main(
        [
            "prog",
            "--before",
            str(BEFORE),
            "--after",
            str(FIX / "after_guardrail_lowered.json"),
            "--quiet",
        ]
    )
    assert rc == 1


def test_cli_exit_two_on_missing_input(tmp_path):
    rc = diff.main(["prog", "--before", str(BEFORE), "--after", str(tmp_path / "nope.json"), "--quiet"])
    assert rc == 2


def test_cli_writes_out_file(tmp_path):
    out = tmp_path / "nested" / "report.json"
    diff.main(
        [
            "prog",
            "--before",
            str(BEFORE),
            "--after",
            str(FIX / "after_benign.json"),
            "--out",
            str(out),
            "--quiet",
        ]
    )
    assert out.exists()
    parsed = json.loads(out.read_text())
    assert parsed["schema_version"] == diff.SCHEMA_VERSION


# --- artifacts hygiene -----------------------------------------------------


def test_no_codename_leak_in_script_output_for_clean_input():
    # A clean before/after pair must not surface the internal codename in the
    # report unless the candidate itself leaked it.
    report = _report("after_benign.json")
    blob = json.dumps(report).lower()
    assert diff.INTERNAL_CODENAME not in blob
