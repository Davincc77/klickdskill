"""Tests for scripts/generate_supply_chain_candidate.py.

Internal candidate generator (v4.2 target shape). NON-NORMATIVE. These tests
assert the anti-mirage contract: deterministic ids, the full v4.2 layer set,
foundation/transversal competency anchors, and that missing domain information
is surfaced as `requires_human_premium_pass` rather than hallucinated.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "generate_supply_chain_candidate.py"
FIX = REPO_ROOT / "tests" / "fixtures" / "supply_chain_candidate"

V4_2_LAYERS = (
    "metadata",
    "competency_architecture",
    "memory_system",
    "governance_system",
    "memory_governance",
    "runtime",
    "context_graph",
    "interactions",
    "evidence",
    "security",
    "audit",
    "skill_lifecycle",
    "output_contract",
)


def _load():
    spec = importlib.util.spec_from_file_location(
        "generate_supply_chain_candidate", SCRIPT
    )
    assert spec and spec.loader, f"could not load {SCRIPT}"
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _candidate(mod, name: str):
    path = FIX / name
    request, text = mod.load_build_request(path)
    return mod.build_candidate(request, text, path)


# --- structural --------------------------------------------------------------
def test_script_exists():
    assert SCRIPT.exists()


def test_candidate_has_all_v4_2_layers():
    mod = _load()
    cand = _candidate(mod, "build_request_clean.json")
    for layer in V4_2_LAYERS:
        assert layer in cand, f"missing v4.2 layer: {layer}"


def test_foundation_and_transversal_counts():
    mod = _load()
    cand = _candidate(mod, "build_request_clean.json")
    core = cand["competency_architecture"]["competency_core"]
    assert len(core["foundation_competencies"]) == 7
    assert len(core["transversal_competencies"]) == 12


def test_harmonized_domain_names_present():
    mod = _load()
    cand = _candidate(mod, "build_request_clean.json")
    arch = cand["competency_architecture"]
    for name in (
        "competency_core",
        "primary_domain_competencies",
        "secondary_domain_competencies",
        "domain_risk_profile",
        "domain_output_requirements",
    ):
        assert name in arch, f"missing harmonized arch layer: {name}"


def test_skill_lifecycle_not_named_supply_chain():
    mod = _load()
    cand = _candidate(mod, "build_request_clean.json")
    sl = cand["skill_lifecycle"]
    assert sl.get("renamed_from") == "supply_chain"
    assert sl.get("completeness_claimed") is False
    # build_request stage exists but the lifecycle is not literally "supply_chain".
    assert "build_request" in sl["stages"]
    assert "promotion_gate" in sl["stages"]


def test_output_contract_graph_bindings():
    mod = _load()
    cand = _candidate(mod, "build_request_clean.json")
    gb = cand["output_contract"]["graph_bindings"]
    for field in (
        "creates_action_node",
        "requires_policy_node",
        "requires_evidence_node",
        "may_trigger_veto_edge",
        "writes_audit_edge",
    ):
        assert field in gb, f"missing graph_binding: {field}"


def test_interactions_canonical_flow():
    mod = _load()
    cand = _candidate(mod, "build_request_clean.json")
    flow = cand["interactions"]["canonical_flow"]
    assert flow[0] == "user_task"
    assert "human_veto_if_required" in flow
    assert flow[-1] == "memory_update_candidate"


# --- anti-mirage: no hallucination ------------------------------------------
def test_missing_domain_info_triggers_premium_pass():
    mod = _load()
    cand = _candidate(mod, "build_request_missing_domain.json")
    status = cand["premium_pass_status"]
    assert status["requires_human_premium_pass"] is True
    # The specific missing-domain gaps must be named, not silently filled.
    assert "competency_architecture.primary_domain_competencies" in status["gaps"]
    assert "evidence.sources" in status["gaps"]


def test_missing_domain_does_not_hallucinate_competencies():
    mod = _load()
    cand = _candidate(mod, "build_request_missing_domain.json")
    primary = cand["competency_architecture"]["primary_domain_competencies"]
    # Must be the gap marker, not an invented competency list.
    assert isinstance(primary, dict)
    assert primary.get("requires_human_premium_pass") is True
    # No sources were declared, so none may appear.
    assert cand["sources"] == []
    assert cand["evidence"]["sources"] == []


def test_clean_candidate_has_no_premium_pass_requirement():
    mod = _load()
    cand = _candidate(mod, "build_request_clean.json")
    assert cand["premium_pass_status"]["requires_human_premium_pass"] is False
    assert cand["premium_pass_status"]["gaps"] == []


def test_sources_only_from_request():
    mod = _load()
    cand = _candidate(mod, "build_request_clean.json")
    ids = {s.get("id") for s in cand["sources"]}
    assert ids == {"skos"}  # exactly what the request declared, nothing added


# --- governance floor --------------------------------------------------------
def test_governance_floor_is_safe_by_default():
    mod = _load()
    cand = _candidate(mod, "build_request_missing_domain.json")
    gov = cand["governance_system"]
    assert gov["human_veto"]["required"] is True
    assert gov["human_veto"]["lowerable"] is False
    assert gov["human_veto_required"] is True
    assert gov["no_auto_external_action"] is True
    assert gov["final_decision_owner"].startswith("human")


def test_threat_model_flat_mirrors_present():
    mod = _load()
    cand = _candidate(mod, "build_request_clean.json")
    # The flat fields consumed by the threat-model tool must be present.
    for key in ("governance", "memory", "tools", "risk_profile",
                "output_contract", "sources", "skill_id"):
        assert key in cand, f"missing threat-model flat field: {key}"


# --- determinism -------------------------------------------------------------
def test_candidate_id_deterministic_across_runs():
    mod = _load()
    a = _candidate(mod, "build_request_clean.json")
    b = _candidate(mod, "build_request_clean.json")
    assert a["candidate_id"] == b["candidate_id"]
    assert a["candidate_hash"] == b["candidate_hash"]
    assert a["run_id"] == b["run_id"]


def test_candidate_id_changes_with_input():
    mod = _load()
    a = _candidate(mod, "build_request_clean.json")
    b = _candidate(mod, "build_request_missing_domain.json")
    assert a["candidate_id"] != b["candidate_id"]


def test_no_clock_field_in_deterministic_core():
    mod = _load()
    cand = _candidate(mod, "build_request_clean.json")
    # The candidate carries no top-level generated_at; any clock value would
    # have to live in a quarantined zone, never in the hashed core.
    assert "generated_at" not in cand


# --- CLI ---------------------------------------------------------------------
def test_cli_writes_candidate_and_exits_zero(tmp_path):
    mod = _load()
    out = tmp_path / "cand.json"
    rc = mod.main([
        "--build-request", str(FIX / "build_request_clean.json"),
        "--out", str(out), "--quiet",
    ])
    assert rc == 0
    data = json.loads(out.read_text())
    assert data["skill_id"] == "xklickd-research-reader"


def test_cli_invalid_request_exits_one(tmp_path):
    mod = _load()
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"domain": "x"}))  # no skill_id
    rc = mod.main(["--build-request", str(bad), "--quiet",
                   "--out", str(tmp_path / "o.json")])
    assert rc == 1


def test_cli_missing_request_exits_two(tmp_path):
    mod = _load()
    rc = mod.main(["--build-request", str(tmp_path / "nope.json"), "--quiet",
                   "--out", str(tmp_path / "o.json")])
    # missing file is a build_request error -> exit 1 (cannot generate)
    assert rc == 1
