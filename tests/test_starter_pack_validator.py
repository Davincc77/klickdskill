"""Tests for scripts/validate_starter_packs.py.

These tests build tiny in-memory pack fixtures in a tmp_path directory and
exercise both the happy path and each failure mode. They do not depend on
any actual starter-pack file existing in the repo.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "scripts" / "validate_starter_packs.py"


def _load_module():
    spec = importlib.util.spec_from_file_location(
        "validate_starter_packs", SCRIPT
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["validate_starter_packs"] = mod
    spec.loader.exec_module(mod)
    return mod


vsp = _load_module()


VALID_PACK: dict = {
    "pack": "x.klickd/student",
    "pack_version": "0.1.0-draft",
    "publisher": {"name": "klickd", "ref": "https://klickd.app"},
    "frameworks": [
        {
            "scheme": "esco",
            "version": "v1.1.1",
            "iri_prefix": "http://data.europa.eu/esco/skill/",
            "canonical_url": "https://esco.ec.europa.eu/en/classification/skill_main",
        }
    ],
    "base_transversal_core": {
        "frameworks": [
            {
                "scheme": "esco",
                "version": "v1.1.1",
                "iri_prefix": "http://data.europa.eu/esco/skill/",
            }
        ],
        "transversal_refs": [
            {"competency_ref": "esco:S2", "scheme": "esco", "prefLabel": "info skills"}
        ],
    },
    "competencies": [
        {"competency_ref": "esco:S2", "scheme": "esco", "prefLabel": "info skills"}
    ],
    "source_policy": {
        "frameworks_offline_bundle": "docs/rfcs/chimera/frameworks/x.klickd.student.bundle.json",
        "allow_inline_definitions": False,
        "language_tags": ["en"],
    },
    "evidence_policy": {
        "required_for_claims": True,
        "pointer_only": True,
        "attestation_shape_ref": "rfc-002#8b",
    },
    "gates": {
        "verification_gates_default": {
            "raise_only": True,
            "claim_grounding_required": True,
            "reversibility_threshold": "medium",
        }
    },
    "human_authority": {
        "final_decision_owner": "human_carrier",
        "agent_role": "advisory",
        "escalation": "self",
    },
    "memory_scope": "memory.x_klickd.student",
}


def _write(d: Path, name: str, data: dict) -> Path:
    p = d / name
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


def test_missing_dir_exits_2(tmp_path, capsys):
    rc = vsp.main(["--dir", str(tmp_path / "nope")])
    assert rc == 2
    err = capsys.readouterr().err
    assert "no pack files found" in err


def test_empty_dir_exits_2(tmp_path):
    rc = vsp.main(["--dir", str(tmp_path)])
    assert rc == 2


def test_happy_path(tmp_path, capsys):
    _write(tmp_path, "student.json", VALID_PACK)
    rc = vsp.main(["--dir", str(tmp_path)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "[OK]" in out
    assert "passed=1" in out


def test_top_level_verification_gates_also_accepted(tmp_path):
    data = copy.deepcopy(VALID_PACK)
    data.pop("gates")
    data["verification_gates"] = {"raise_only": True}
    _write(tmp_path, "p.json", data)
    assert vsp.main(["--dir", str(tmp_path)]) == 0


def test_structured_memory_alias(tmp_path):
    data = copy.deepcopy(VALID_PACK)
    data.pop("memory_scope")
    data["structured_memory"] = {"slice": "memory.x_klickd.student"}
    _write(tmp_path, "p.json", data)
    assert vsp.main(["--dir", str(tmp_path)]) == 0


@pytest.mark.parametrize(
    "drop",
    [
        "base_transversal_core",
        "competencies",
        "source_policy",
        "evidence_policy",
        "human_authority",
    ],
)
def test_missing_required_field_fails(tmp_path, drop):
    data = copy.deepcopy(VALID_PACK)
    data.pop(drop)
    _write(tmp_path, "p.json", data)
    assert vsp.main(["--dir", str(tmp_path)]) == 1


def test_missing_verification_gates_fails(tmp_path):
    data = copy.deepcopy(VALID_PACK)
    data.pop("gates")
    _write(tmp_path, "p.json", data)
    assert vsp.main(["--dir", str(tmp_path)]) == 1


def test_missing_structured_memory_fails(tmp_path):
    data = copy.deepcopy(VALID_PACK)
    data.pop("memory_scope")
    _write(tmp_path, "p.json", data)
    assert vsp.main(["--dir", str(tmp_path)]) == 1


def test_missing_frameworks_fails(tmp_path):
    data = copy.deepcopy(VALID_PACK)
    data.pop("frameworks")
    data["base_transversal_core"] = {"frameworks": [], "transversal_refs": []}
    _write(tmp_path, "p.json", data)
    assert vsp.main(["--dir", str(tmp_path)]) == 1


@pytest.mark.parametrize(
    "forbidden",
    [
        "host_skill",
        "pedagogy",
        "teaching_method",
        "socratic_steps",
        "prompt_strategy",
        "scoring_rubric",
        "intervention_policy",
        "tone_rules",
        "system_prompt",
        "system_prompt_overrides",
    ],
)
def test_forbidden_top_level_field_fails(tmp_path, forbidden):
    data = copy.deepcopy(VALID_PACK)
    data[forbidden] = "anything"
    _write(tmp_path, "p.json", data)
    assert vsp.main(["--dir", str(tmp_path)]) == 1


def test_human_authority_role_must_be_advisory(tmp_path):
    data = copy.deepcopy(VALID_PACK)
    data["human_authority"]["agent_role"] = "autonomous"
    _write(tmp_path, "p.json", data)
    assert vsp.main(["--dir", str(tmp_path)]) == 1


def test_invalid_json_fails(tmp_path):
    p = tmp_path / "broken.json"
    p.write_text("{not json", encoding="utf-8")
    assert vsp.main(["--dir", str(tmp_path)]) == 1


def test_secret_pattern_detection(tmp_path):
    data = copy.deepcopy(VALID_PACK)
    data["leak"] = "AKIAABCDEFGHIJKLMNOP"
    _write(tmp_path, "p.json", data)
    assert vsp.main(["--dir", str(tmp_path)]) == 1


def test_pii_email_detection(tmp_path):
    data = copy.deepcopy(VALID_PACK)
    data["contact"] = "real.person@gmail.com"
    _write(tmp_path, "p.json", data)
    assert vsp.main(["--dir", str(tmp_path)]) == 1


def test_pii_allowlisted_framework_host_not_flagged(tmp_path):
    data = copy.deepcopy(VALID_PACK)
    # Emails on framework hosts (defensive — currently no @ in real refs)
    # should not trip the email regex.
    data["note"] = "contact@europa.eu"
    _write(tmp_path, "p.json", data)
    assert vsp.main(["--dir", str(tmp_path)]) == 0


def test_require_known_pack_name_flag(tmp_path):
    data = copy.deepcopy(VALID_PACK)
    data["pack"] = "x.klickd/work"  # P1, not in starter four
    _write(tmp_path, "p.json", data)
    assert vsp.main(
        ["--dir", str(tmp_path), "--require-known-pack-name"]
    ) == 1


def test_json_report_mode(tmp_path, capsys):
    _write(tmp_path, "p.json", VALID_PACK)
    rc = vsp.main(["--dir", str(tmp_path), "--json"])
    assert rc == 0
    out = capsys.readouterr().out
    report = json.loads(out)
    assert report["summary"]["passed"] == 1
    assert report["summary"]["failed"] == 0


def test_bundle_manifest_hash_ok(tmp_path):
    bundle = tmp_path / "fw.bundle.json"
    bundle.write_text('{"@context": {}}', encoding="utf-8")
    import hashlib

    sha = hashlib.sha256(bundle.read_bytes()).hexdigest()
    manifest = tmp_path / "bundle-manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "bundles": [
                    {"kind": "pack", "path": "fw.bundle.json", "sha256": sha}
                ]
            }
        ),
        encoding="utf-8",
    )
    _write(tmp_path, "p.json", VALID_PACK)
    assert vsp.main(
        ["--dir", str(tmp_path), "--manifest", str(manifest)]
    ) == 0


def test_bundle_manifest_hash_mismatch_fails(tmp_path):
    bundle = tmp_path / "fw.bundle.json"
    bundle.write_text('{"@context": {}}', encoding="utf-8")
    manifest = tmp_path / "bundle-manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "bundles": [
                    {"kind": "pack", "path": "fw.bundle.json", "sha256": "0" * 64}
                ]
            }
        ),
        encoding="utf-8",
    )
    _write(tmp_path, "p.json", VALID_PACK)
    rc = vsp.main(
        ["--dir", str(tmp_path), "--manifest", str(manifest)]
    )
    assert rc == 1


def test_existing_student_fixture_passes():
    fixture_dir = (
        REPO / "docs" / "rfcs" / "chimera" / "packs" / "fixtures"
    )
    if not fixture_dir.is_dir():
        pytest.skip("fixture dir missing")
    # Ensure at least one pack file is present.
    files = vsp.find_pack_files(fixture_dir)
    if not files:
        pytest.skip("no fixture pack files")
    rc = vsp.main(["--dir", str(fixture_dir)])
    assert rc == 0
