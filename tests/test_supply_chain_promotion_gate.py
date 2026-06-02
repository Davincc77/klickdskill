"""Tests for scripts/run_supply_chain_promotion_gate.py.

Combined promotion gate. NON-NORMATIVE. The gate orchestrates the existing
tool-backed checks, classifies ACCEPT / ACCEPT_WITH_REVIEW / BLOCK, and reports
(never runs) whether a human premium pass is required. A fixed --eval-date is
used so source freshness classification is reproducible.
"""
from __future__ import annotations

import datetime as _dt
import importlib.util
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
GATE_SCRIPT = REPO_ROOT / "scripts" / "run_supply_chain_promotion_gate.py"
GEN_SCRIPT = REPO_ROOT / "scripts" / "generate_supply_chain_candidate.py"
FIX = REPO_ROOT / "tests" / "fixtures" / "supply_chain_candidate"
EVAL_DATE = _dt.date(2026, 6, 2)


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader, f"could not load {path}"
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _gate_mod():
    return _load(GATE_SCRIPT, "run_supply_chain_promotion_gate")


def _gen_mod():
    return _load(GEN_SCRIPT, "generate_supply_chain_candidate")


def _make_candidate(tmp_path: Path, request_name: str) -> Path:
    """Generate a real candidate from a fixture build_request."""
    gen = _gen_mod()
    out = tmp_path / f"{request_name}.cand.json"
    rc = gen.main([
        "--build-request", str(FIX / request_name),
        "--out", str(out), "--quiet",
    ])
    assert rc == 0
    return out


def _run(gate, candidate_path: Path, **kw):
    candidate_text = candidate_path.read_text()
    candidate = json.loads(candidate_text)
    return gate.run_gate(
        candidate, candidate_text, candidate_path,
        kw.get("source_manifest"), kw.get("before"), EVAL_DATE,
    )


# --- structural --------------------------------------------------------------
def test_script_exists():
    assert GATE_SCRIPT.exists()


def test_clean_candidate_accepts(tmp_path):
    gate = _gate_mod()
    cand = _make_candidate(tmp_path, "build_request_clean.json")
    rep = _run(gate, cand)
    assert rep["classification"] == "ACCEPT"
    assert rep["summary"]["blocking"] == 0
    assert rep["premium_pass_required"] is False


def test_report_has_required_fields(tmp_path):
    gate = _gate_mod()
    cand = _make_candidate(tmp_path, "build_request_clean.json")
    rep = _run(gate, cand)
    for field in (
        "schema_version", "classification", "deterministic_gate_id",
        "summary", "checks", "blocking_findings", "review_findings",
        "premium_pass_required", "claim_boundaries", "non_deterministic_zone",
    ):
        assert field in rep, f"missing gate field: {field}"


# --- premium pass / accept-with-review --------------------------------------
def test_missing_domain_candidate_accepts_with_review(tmp_path):
    gate = _gate_mod()
    cand = _make_candidate(tmp_path, "build_request_missing_domain.json")
    rep = _run(gate, cand)
    assert rep["classification"] == "ACCEPT_WITH_REVIEW"
    assert rep["premium_pass_required"] is True
    assert rep["summary"]["blocking"] == 0


def test_gate_does_not_run_premium_pass(tmp_path):
    gate = _gate_mod()
    cand = _make_candidate(tmp_path, "build_request_missing_domain.json")
    rep = _run(gate, cand)
    assert rep["claim_boundaries"]["runs_premium_pass"] is False


# --- block paths -------------------------------------------------------------
def test_forbidden_claim_blocks(tmp_path):
    gate = _gate_mod()
    cand = _make_candidate(tmp_path, "build_request_clean.json")
    data = json.loads(cand.read_text())
    data["metadata"]["title"] = "the universal standard for everything"
    leak = tmp_path / "claim.json"
    leak.write_text(json.dumps(data))
    rep = _run(gate, leak)
    assert rep["classification"] == "BLOCK"
    assert any("forbidden public claim" in f for f in rep["blocking_findings"])


def test_internal_codename_leak_blocks(tmp_path):
    gate = _gate_mod()
    cand = _make_candidate(tmp_path, "build_request_clean.json")
    data = json.loads(cand.read_text())
    data["metadata"]["note"] = "internal chimera reference"
    leak = tmp_path / "codename.json"
    leak.write_text(json.dumps(data))
    rep = _run(gate, leak)
    assert rep["classification"] == "BLOCK"
    assert any("codename" in f for f in rep["blocking_findings"])


def test_private_public_leak_blocks(tmp_path):
    gate = _gate_mod()
    cand = _make_candidate(tmp_path, "build_request_clean.json")
    data = json.loads(cand.read_text())
    data["private_public_leak"] = True
    leak = tmp_path / "leak.json"
    leak.write_text(json.dumps(data))
    rep = _run(gate, leak)
    assert rep["classification"] == "BLOCK"
    assert any("private->public" in f for f in rep["blocking_findings"])


def test_public_v4_2_overclaim_blocks(tmp_path):
    gate = _gate_mod()
    cand = _make_candidate(tmp_path, "build_request_clean.json")
    data = json.loads(cand.read_text())
    data["internal_target"]["public_version"] = "v4.2"
    leak = tmp_path / "v42.json"
    leak.write_text(json.dumps(data))
    rep = _run(gate, leak)
    assert rep["classification"] == "BLOCK"
    assert any("public_version v4.2" in f for f in rep["blocking_findings"])


def test_missing_v4_2_layer_blocks(tmp_path):
    gate = _gate_mod()
    cand = _make_candidate(tmp_path, "build_request_clean.json")
    data = json.loads(cand.read_text())
    del data["governance_system"]
    bad = tmp_path / "nolayer.json"
    bad.write_text(json.dumps(data))
    rep = _run(gate, bad)
    assert rep["classification"] == "BLOCK"
    assert any("governance_system" in f for f in rep["blocking_findings"])


def test_completeness_claim_blocks(tmp_path):
    gate = _gate_mod()
    cand = _make_candidate(tmp_path, "build_request_clean.json")
    data = json.loads(cand.read_text())
    data["skill_lifecycle"]["completeness_claimed"] = True
    bad = tmp_path / "complete.json"
    bad.write_text(json.dumps(data))
    rep = _run(gate, bad)
    assert rep["classification"] == "BLOCK"
    assert any("completeness" in f for f in rep["blocking_findings"])


# --- orchestrated checks run honestly ---------------------------------------
def test_not_run_checks_recorded_without_inflating_review(tmp_path):
    """A skipped check is recorded as not_run with a reason, not as a review
    finding — otherwise a clean candidate would never be a clean ACCEPT."""
    gate = _gate_mod()
    cand = _make_candidate(tmp_path, "build_request_clean.json")
    rep = _run(gate, cand)  # no source manifest, no before -> 2 not_run checks
    not_run = [c for c in rep["checks"] if c["verdict"] == "not_run"]
    assert len(not_run) >= 2
    for c in not_run:
        assert c["review_findings"] == []
        assert "reason" in c["detail"]
    assert rep["classification"] == "ACCEPT"


def test_source_manifest_check_runs_when_provided(tmp_path):
    gate = _gate_mod()
    cand = _make_candidate(tmp_path, "build_request_clean.json")
    rep = _run(gate, cand,
               source_manifest=FIX / "source_manifest_ok.json")
    sc = next(c for c in rep["checks"] if c["check"] == "source_license")
    assert sc["verdict"] in ("pass", "review")  # it ran
    assert rep["classification"] in ("ACCEPT", "ACCEPT_WITH_REVIEW")


def test_threat_model_check_runs(tmp_path):
    gate = _gate_mod()
    cand = _make_candidate(tmp_path, "build_request_clean.json")
    rep = _run(gate, cand)
    tm = next(c for c in rep["checks"] if c["check"] == "threat_model")
    assert tm["verdict"] != "not_run"
    assert tm["detail"].get("deterministic_threat_model_id")


# --- determinism -------------------------------------------------------------
def test_gate_id_stable_across_runs(tmp_path):
    gate = _gate_mod()
    cand = _make_candidate(tmp_path, "build_request_clean.json")
    a = _run(gate, cand)
    b = _run(gate, cand)
    assert a["deterministic_gate_id"] == b["deterministic_gate_id"]


def test_gate_id_excludes_eval_date(tmp_path):
    gate = _gate_mod()
    cand = _make_candidate(tmp_path, "build_request_clean.json")
    text = cand.read_text()
    data = json.loads(text)
    a = gate.run_gate(data, text, cand, None, None, _dt.date(2026, 6, 2))
    b = gate.run_gate(data, text, cand, None, None, _dt.date(2030, 1, 1))
    assert a["deterministic_gate_id"] == b["deterministic_gate_id"]


# --- CLI exit codes ----------------------------------------------------------
def test_cli_accept_exits_zero(tmp_path):
    gate = _gate_mod()
    cand = _make_candidate(tmp_path, "build_request_clean.json")
    out = tmp_path / "gate.json"
    rc = gate.main(["--candidate", str(cand), "--out", str(out),
                    "--quiet", "--eval-date", "2026-06-02"])
    assert rc == 0
    assert json.loads(out.read_text())["classification"] == "ACCEPT"


def test_cli_block_exits_one(tmp_path):
    gate = _gate_mod()
    cand = _make_candidate(tmp_path, "build_request_clean.json")
    data = json.loads(cand.read_text())
    data["private_public_leak"] = True
    bad = tmp_path / "leak.json"
    bad.write_text(json.dumps(data))
    out = tmp_path / "gate.json"
    rc = gate.main(["--candidate", str(bad), "--out", str(out),
                    "--quiet", "--eval-date", "2026-06-02"])
    assert rc == 1


def test_cli_missing_candidate_exits_two(tmp_path):
    gate = _gate_mod()
    rc = gate.main(["--candidate", str(tmp_path / "nope.json"), "--quiet"])
    assert rc == 2


def test_cli_writes_md_summary(tmp_path):
    gate = _gate_mod()
    cand = _make_candidate(tmp_path, "build_request_clean.json")
    out = tmp_path / "gate.json"
    md = tmp_path / "gate.md"
    rc = gate.main(["--candidate", str(cand), "--out", str(out),
                    "--md", str(md), "--quiet", "--eval-date", "2026-06-02"])
    assert rc == 0
    assert md.exists()
    assert "promotion gate" in md.read_text().lower()
