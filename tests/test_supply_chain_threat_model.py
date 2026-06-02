"""Tests for scripts/generate_supply_chain_threat_model.py.

NON-NORMATIVE. Stdlib-only, offline. Exercises the deterministic
threat-model generator against the candidate fixtures under
tests/fixtures/threat-model/ and asserts the blocking behaviour and
determinism the brief requires.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "generate_supply_chain_threat_model.py"
FIXTURES = REPO_ROOT / "tests" / "fixtures" / "threat-model"


def _load_mod():
    spec = importlib.util.spec_from_file_location("sc_threat_model", SCRIPT)
    assert spec and spec.loader, f"could not load {SCRIPT}"
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _candidate(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def _report(name: str) -> dict:
    mod = _load_mod()
    return mod.build_report(_candidate(name), name)


def test_script_exists():
    assert SCRIPT.exists()


def test_fixtures_exist():
    expected = {
        "candidate_low_risk_ok.json",
        "candidate_no_veto_sensitive_action.json",
        "candidate_external_action_no_gate.json",
        "candidate_longterm_memory_no_promotion.json",
        "candidate_private_public_leak.json",
        "candidate_evidence_false_public_claims.json",
        "candidate_compliance_overclaim.json",
    }
    present = {p.name for p in FIXTURES.glob("*.json")}
    assert expected <= present, expected - present


def test_low_risk_candidate_has_no_blocking_findings():
    rep = _report("candidate_low_risk_ok.json")
    assert rep["blocked_findings"] == []
    assert rep["summary"]["by_severity"]["critical"] == 0
    assert rep["summary"]["by_severity"]["high"] == 0


def test_no_veto_with_sensitive_action_blocks():
    rep = _report("candidate_no_veto_sensitive_action.json")
    cats = {t["category"] for t in rep["threats"]}
    assert "human_veto_bypass" in cats
    assert rep["blocked_findings"]


def test_external_action_without_gate_blocks():
    rep = _report("candidate_external_action_no_gate.json")
    cats = {t["category"] for t in rep["threats"]}
    assert "unsafe_external_action" in cats
    assert rep["blocked_findings"]


def test_longterm_memory_without_promotion_blocks_or_high():
    rep = _report("candidate_longterm_memory_no_promotion.json")
    mem = [t for t in rep["threats"] if t["category"] == "memory_poisoning"]
    assert mem, "expected a memory_poisoning finding"
    assert mem[0]["severity"] in ("high", "critical")
    assert rep["blocked_findings"]


def test_private_public_leak_blocks():
    rep = _report("candidate_private_public_leak.json")
    cats = {t["category"] for t in rep["threats"]}
    assert "private_public_leak" in cats
    assert rep["blocked_findings"]


def test_evidence_false_with_public_claims_blocks():
    rep = _report("candidate_evidence_false_public_claims.json")
    cats = {t["category"] for t in rep["threats"]}
    assert "evidence_weakening" in cats
    assert "unsourced_claim" in cats
    assert rep["blocked_findings"]


def test_compliance_overclaim_blocks():
    rep = _report("candidate_compliance_overclaim.json")
    cats = {t["category"] for t in rep["threats"]}
    assert "compliance_overclaim" in cats
    assert rep["blocked_findings"]


def test_output_is_deterministic():
    mod = _load_mod()
    cand = _candidate("candidate_no_veto_sensitive_action.json")
    r1 = mod.render(mod.build_report(cand, "x"))
    r2 = mod.render(mod.build_report(cand, "x"))
    assert r1 == r2


def test_candidate_hash_is_order_independent():
    mod = _load_mod()
    a = {"skill_id": "s", "tools": {"allowed": ["read_file"]}, "domain": "d"}
    b = {"domain": "d", "tools": {"allowed": ["read_file"]}, "skill_id": "s"}
    assert mod.candidate_hash(a) == mod.candidate_hash(b)


def test_threat_model_id_changes_with_findings():
    mod = _load_mod()
    ok = _candidate("candidate_low_risk_ok.json")
    bad = _candidate("candidate_no_veto_sensitive_action.json")
    id_ok = mod.build_report(ok, "x")["deterministic_threat_model_id"]
    id_bad = mod.build_report(bad, "x")["deterministic_threat_model_id"]
    assert id_ok != id_bad


def test_report_has_required_fields():
    rep = _report("candidate_low_risk_ok.json")
    for key in (
        "schema_version",
        "candidate_path",
        "candidate_hash",
        "deterministic_threat_model_id",
        "summary",
        "threats",
        "required_mitigations",
        "blocked_findings",
        "recommendations",
        "non_deterministic_zone",
    ):
        assert key in rep, f"missing report field: {key}"


def test_claim_boundaries_preserved():
    rep = _report("candidate_low_risk_ok.json")
    cb = rep["claim_boundaries"]
    assert cb["is_security_certification"] is False
    assert cb["establishes_legal_compliance"] is False
    assert cb["is_full_automation"] is False
    assert cb["proves_loaded_executable_skill"] is False
