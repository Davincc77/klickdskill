"""Tests for scripts/check_supply_chain_sources.py.

Source freshness + license compatibility triage. NON-NORMATIVE; no legal
advice, no schema change. A fixed --eval-date (2026-06-02) is used so freshness
classification is reproducible regardless of when the suite runs.
"""
from __future__ import annotations

import datetime as _dt
import importlib.util
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "check_supply_chain_sources.py"
FIX = REPO_ROOT / "tests" / "fixtures" / "supply_chain_sources"
EVAL_DATE = _dt.date(2026, 6, 2)


def _load():
    spec = importlib.util.spec_from_file_location("check_supply_chain_sources", SCRIPT)
    assert spec and spec.loader, f"could not load {SCRIPT}"
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _report(mod, name: str):
    path = FIX / name
    manifest, text = mod.load_manifest(path)
    return mod.build_report(manifest, text, path, EVAL_DATE, 3)


def _by_id(report, sid):
    return next(f for f in report["source_findings"] if f["id"] == sid)


# --- structural --------------------------------------------------------------
def test_script_exists():
    assert SCRIPT.exists()


def test_ok_manifest_all_allowed():
    mod = _load()
    rep = _report(mod, "manifest_ok.json")
    assert rep["summary"]["blocked"] == 0
    assert rep["summary"]["review"] == 0
    assert rep["summary"]["allowed"] == 2
    assert all(f["verdict"] == "allowed" for f in rep["source_findings"])


def test_report_has_required_fields():
    mod = _load()
    rep = _report(mod, "manifest_ok.json")
    for field in (
        "schema_version", "manifest_path", "manifest_hash",
        "deterministic_report_id", "summary", "source_findings",
        "blocked_findings", "review_findings", "recommendations",
        "non_deterministic_zone",
    ):
        assert field in rep, f"missing report field: {field}"


# --- license -----------------------------------------------------------------
def test_unknown_license_is_review():
    mod = _load()
    rep = _report(mod, "manifest_license_unknown.json")
    f = _by_id(rep, "source-unknown-lic")
    assert f["license_class"] == "unknown"
    assert f["verdict"] == "review"
    assert rep["summary"]["blocked"] == 0


def test_blocked_license_blocks():
    mod = _load()
    rep = _report(mod, "manifest_license_blocked.json")
    f = _by_id(rep, "source-blocked-lic")
    assert f["license_class"] == "blocked"
    assert f["verdict"] == "blocked"
    assert rep["summary"]["blocked"] == 1


def test_license_normalization_aliases():
    mod = _load()
    assert mod.normalize_license("apache2") == "APACHE-2.0"
    assert mod.classify_license(mod.normalize_license("apache2")) == "allowed"
    assert mod.normalize_license("ARR") == "ALL-RIGHTS-RESERVED"
    assert mod.classify_license(mod.normalize_license("ARR")) == "blocked"


# --- missing fields ----------------------------------------------------------
def test_missing_url_and_date_flagged():
    mod = _load()
    rep = _report(mod, "manifest_missing_fields.json")
    f = _by_id(rep, "source-no-url")
    joined = " ".join(f["findings"])
    assert "missing url" in joined
    assert "published_at" in joined
    assert f["verdict"] == "blocked"  # missing url is blocking


# --- freshness ---------------------------------------------------------------
def test_stale_reference_is_review_not_blocked():
    mod = _load()
    rep = _report(mod, "manifest_stale_reference.json")
    f = _by_id(rep, "source-stale-ref")
    assert f["freshness_class"] == "stale"
    assert f["verdict"] == "review"
    assert rep["summary"]["blocked"] == 0


def test_stale_security_source_blocks():
    mod = _load()
    rep = _report(mod, "manifest_stale_security.json")
    f = _by_id(rep, "source-stale-security")
    assert f["freshness_class"] == "stale"
    assert f["verdict"] == "blocked"


def test_missing_security_date_blocks():
    mod = _load()
    rep = _report(mod, "manifest_missing_security_date.json")
    f = _by_id(rep, "source-sec-no-date")
    assert f["freshness_class"] == "missing_date"
    assert f["verdict"] == "blocked"


def test_academic_long_budget_and_superseded_review():
    mod = _load()
    rep = _report(mod, "manifest_academic_superseded.json")
    ok = _by_id(rep, "source-academic-old-ok")
    sup = _by_id(rep, "source-academic-superseded")
    assert ok["freshness_class"] == "fresh"
    assert sup["freshness_class"] == "review"


# --- non-commercial / premium ------------------------------------------------
def test_noncommercial_for_premium_blocks():
    mod = _load()
    rep = _report(mod, "manifest_noncommercial_premium.json")
    f = _by_id(rep, "source-nc-premium")
    assert f["verdict"] == "blocked"
    assert any("non-commercial" in b for b in f["blocking_findings"])


# --- hash --------------------------------------------------------------------
def test_hash_match_ok():
    mod = _load()
    rep = _report(mod, "manifest_hash_match.json")
    f = _by_id(rep, "source-hash-ok")
    assert f["hash_status"] == "match"
    assert f["verdict"] == "allowed"


def test_hash_mismatch_blocks():
    mod = _load()
    rep = _report(mod, "manifest_hash_mismatch.json")
    f = _by_id(rep, "source-hash-bad")
    assert f["hash_status"] == "mismatch"
    assert f["verdict"] == "blocked"


# --- determinism -------------------------------------------------------------
def test_deterministic_report_id_stable_across_runs():
    mod = _load()
    r1 = _report(mod, "manifest_ok.json")
    r2 = _report(mod, "manifest_ok.json")
    assert r1["deterministic_report_id"] == r2["deterministic_report_id"]


def test_report_id_excludes_clock_marker_and_age():
    """Same inputs (manifest + eval-date) -> same id, regardless of when run.

    The id excludes the wall-clock timestamp and raw age_days, but DOES include
    derived freshness/license classification (those are meaningful outputs). So
    two runs on the same eval-date must match even though evaluated_at is a clock
    value living in non_deterministic_zone.
    """
    mod = _load()
    path = FIX / "manifest_ok.json"
    manifest, text = mod.load_manifest(path)
    a = mod.build_report(manifest, text, path, _dt.date(2026, 6, 2), 3)
    b = mod.build_report(manifest, text, path, _dt.date(2026, 6, 2), 3)
    assert a["deterministic_report_id"] == b["deterministic_report_id"]
    assert "evaluated_at" in a["non_deterministic_zone"]


def test_changed_freshness_class_changes_id():
    """A different eval-date that flips a freshness class is a different
    semantic result and SHOULD yield a different id (not silently identical)."""
    mod = _load()
    path = FIX / "manifest_stale_reference.json"
    manifest, text = mod.load_manifest(path)
    a = mod.build_report(manifest, text, path, _dt.date(2023, 1, 1), 3)  # fresh
    b = mod.build_report(manifest, text, path, _dt.date(2026, 6, 2), 3)  # stale
    assert a["source_findings"][0]["freshness_class"] != \
        b["source_findings"][0]["freshness_class"]
    assert a["deterministic_report_id"] != b["deterministic_report_id"]


def test_distinct_manifests_distinct_ids():
    mod = _load()
    a = _report(mod, "manifest_ok.json")
    b = _report(mod, "manifest_license_blocked.json")
    assert a["deterministic_report_id"] != b["deterministic_report_id"]


# --- CLI exit codes ----------------------------------------------------------
def test_cli_exit_zero_on_ok(tmp_path):
    mod = _load()
    out = tmp_path / "report.json"
    rc = mod.main([
        "--manifest", str(FIX / "manifest_ok.json"),
        "--out", str(out), "--quiet", "--eval-date", "2026-06-02",
    ])
    assert rc == 0
    data = json.loads(out.read_text())
    assert data["summary"]["blocked"] == 0


def test_cli_exit_one_on_blocked(tmp_path):
    mod = _load()
    out = tmp_path / "report.json"
    rc = mod.main([
        "--manifest", str(FIX / "manifest_license_blocked.json"),
        "--out", str(out), "--quiet", "--eval-date", "2026-06-02",
    ])
    assert rc == 1


def test_cli_exit_two_on_missing_manifest(tmp_path):
    mod = _load()
    rc = mod.main(["--manifest", str(tmp_path / "nope.json"), "--quiet"])
    assert rc == 2


def test_cli_exit_two_on_bad_schema(tmp_path):
    mod = _load()
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"schema_version": "wrong", "sources": []}))
    rc = mod.main(["--manifest", str(bad), "--quiet"])
    assert rc == 2
