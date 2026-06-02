"""Tests for the supply-chain audit-trail index + determinism record stage.

Exercises scripts/generate_supply_chain_audit.py directly (stdlib-only, offline)
against a temporary output directory so the committed artefacts are not touched.

Covers:
  - artefacts are generable and parse as JSON;
  - required fields present in both records;
  - deterministic_run_id / hash summary stable across two runs (same inputs);
  - only the timestamp differs between runs (it lives in non_deterministic_zone);
  - no obvious secret/PII in generated artefacts;
  - no banned public-claim / codename string in generated artefacts;
  - `check` reports in-sync, and detects tampering as drift.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "generate_supply_chain_audit.py"


def _load_module(tmp_path: Path):
    """Import the generator with its output paths redirected into tmp_path."""
    spec = importlib.util.spec_from_file_location("gen_sc_audit", SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.AUDIT_DIR = tmp_path / "audit"
    mod.AUDIT_INDEX_PATH = mod.AUDIT_DIR / "audit_trail_index.json"
    mod.DETERMINISM_PATH = mod.AUDIT_DIR / "determinism_record.json"
    return mod


@pytest.fixture()
def gen(tmp_path):
    return _load_module(tmp_path)


def test_generate_succeeds_and_parses(gen):
    assert gen.cmd_generate() == 0
    audit = json.loads(gen.AUDIT_INDEX_PATH.read_text(encoding="utf-8"))
    det = json.loads(gen.DETERMINISM_PATH.read_text(encoding="utf-8"))
    assert isinstance(audit, dict) and isinstance(det, dict)


def test_audit_index_required_fields(gen):
    gen.cmd_generate()
    audit = json.loads(gen.AUDIT_INDEX_PATH.read_text(encoding="utf-8"))
    for field in (
        "schema_version",
        "repo",
        "source_commit_sha",
        "deterministic_run_id",
        "checked_artifacts_count",
        "checked_artifacts_hash_summary",
        "validation_commands",
        "validation_results",
        "build_or_audit_events",
        "stage_automation",
        "notes",
        "non_deterministic_zone",
    ):
        assert field in audit, f"missing {field}"
    assert audit["repo"] == "Davincc77/klickdskill"
    assert audit["checked_artifacts_count"] == 43  # 42 packs + manifest
    assert isinstance(audit["build_or_audit_events"], list)
    assert audit["build_or_audit_events"]
    # validation_results must be empty by design (generator does not run them).
    assert audit["validation_results"] == []


def test_determinism_record_required_fields(gen):
    gen.cmd_generate()
    det = json.loads(gen.DETERMINISM_PATH.read_text(encoding="utf-8"))
    for field in (
        "schema_version",
        "hash_algo",
        "deterministic_run_id",
        "input_files",
        "inputs_hash_summary",
        "output_files",
        "repeatability",
        "non_deterministic_zone",
    ):
        assert field in det, f"missing {field}"
    assert det["hash_algo"] == "sha256"
    assert len(det["input_files"]) == 43
    for item in det["input_files"]:
        assert len(item["sha256"]) == 64


def test_deterministic_run_id_stable_across_runs(gen, tmp_path):
    gen.cmd_generate()
    first_audit = json.loads(gen.AUDIT_INDEX_PATH.read_text(encoding="utf-8"))
    first_det = json.loads(gen.DETERMINISM_PATH.read_text(encoding="utf-8"))

    gen.cmd_generate()  # second run, identical inputs
    second_audit = json.loads(gen.AUDIT_INDEX_PATH.read_text(encoding="utf-8"))
    second_det = json.loads(gen.DETERMINISM_PATH.read_text(encoding="utf-8"))

    assert first_audit["deterministic_run_id"] == second_audit["deterministic_run_id"]
    assert first_det["deterministic_run_id"] == second_det["deterministic_run_id"]
    assert (
        first_audit["checked_artifacts_hash_summary"]
        == second_audit["checked_artifacts_hash_summary"]
    )


def test_only_timestamp_is_non_deterministic(gen):
    """Two runs must agree on everything outside non_deterministic_zone."""
    gen.cmd_generate()
    first = json.loads(gen.AUDIT_INDEX_PATH.read_text(encoding="utf-8"))
    gen.cmd_generate()
    second = json.loads(gen.AUDIT_INDEX_PATH.read_text(encoding="utf-8"))
    first.pop("non_deterministic_zone")
    second.pop("non_deterministic_zone")
    assert first == second


def test_no_banned_claims_or_codename(gen):
    gen.cmd_generate()
    for path in (gen.AUDIT_INDEX_PATH, gen.DETERMINISM_PATH):
        text = path.read_text(encoding="utf-8").lower()
        for banned in gen.BANNED_SUBSTRINGS:
            assert banned not in text, f"{path.name} contains banned {banned!r}"


def test_no_obvious_secret_or_pii(gen):
    gen.cmd_generate()
    for path in (gen.AUDIT_INDEX_PATH, gen.DETERMINISM_PATH):
        text = path.read_text(encoding="utf-8")
        assert gen._scan_secrets(text) == [], f"{path.name} has secret/PII pattern"


def test_check_reports_in_sync_after_generate(gen):
    gen.cmd_generate()
    assert gen.cmd_check() == 0


def test_check_detects_tampering(gen):
    gen.cmd_generate()
    audit = json.loads(gen.AUDIT_INDEX_PATH.read_text(encoding="utf-8"))
    audit["checked_artifacts_count"] = 999  # tamper inside deterministic core
    gen.AUDIT_INDEX_PATH.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    assert gen.cmd_check() == 1


def test_check_detects_banned_string_injection(gen):
    gen.cmd_generate()
    det = json.loads(gen.DETERMINISM_PATH.read_text(encoding="utf-8"))
    det["non_deterministic_zone"]["comment"] = "universal standard"  # banned
    gen.DETERMINISM_PATH.write_text(json.dumps(det, indent=2), encoding="utf-8")
    assert gen.cmd_check() == 1
