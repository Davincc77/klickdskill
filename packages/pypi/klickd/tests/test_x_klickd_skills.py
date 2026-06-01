# klickd — x.klickd v4.1 skill-pack inclusion test
# SPDX-License-Identifier: CC0-1.0

import hashlib

import pytest

import klickd


def test_manifest_is_42_packs_8_lite_34_pro():
    manifest = klickd.get_xklickd_skills_manifest()
    assert manifest["non_normative"] is True
    assert manifest["claims_v41_ga"] is False
    assert manifest["total_count"] == 42
    assert len(manifest["packs"]) == 42
    lite = [p for p in manifest["packs"] if p["tier"] == "lite"]
    pro = [p for p in manifest["packs"] if p["tier"] == "pro"]
    assert len(lite) == 8
    assert len(pro) == 34


def test_every_bundled_pack_hash_matches_manifest():
    for pack in klickd.list_xklickd_skill_packs():
        data = klickd.get_xklickd_skill_pack_bytes(pack["file"])
        assert hashlib.sha256(data).hexdigest() == pack["sha256_file"]
        assert len(data) == pack["bytes"]


def test_resolves_by_file_pack_id_and_bare_id():
    by_file = klickd.load_xklickd_skill_pack("work-assistant.klickd")
    by_pack = klickd.load_xklickd_skill_pack("x.klickd/work_assistant")
    by_bare = klickd.load_xklickd_skill_pack("work-assistant")
    assert by_file["sha256"] == by_pack["sha256"] == by_bare["sha256"]


def test_load_work_assistant_reports_verified_artifact():
    summary = klickd.load_xklickd_skill_pack("work-assistant")
    assert summary["artifact_loaded"] is True
    assert summary["sha256_matches_manifest"] is True
    assert summary["tier"] == "lite"
    assert summary["pack"] == "x.klickd/work_assistant"
    assert summary["klickd_version"] is not None


def test_load_llm_agent_engineering_exposes_governance_fields():
    summary = klickd.load_xklickd_skill_pack("llm-agent-engineering")
    assert summary["artifact_loaded"] is True
    assert summary["sha256_matches_manifest"] is True
    assert summary["tier"] == "pro"
    assert summary["pack"] == "x.klickd/llm_agent_engineering"
    assert summary["domain"] == "software_engineering"
    assert summary["profile_kind"] == "carrier_competency_pack"
    assert len(summary["competency_ids"]) > 0
    assert len(summary["gates"]) > 0
    assert summary["evidence_policy"] is not None
    assert summary["human_authority"] is not None


def test_rejects_unknown_pack():
    with pytest.raises(ValueError):
        klickd.get_xklickd_skill_pack_bytes("../pyproject.toml")
    with pytest.raises(ValueError):
        klickd.get_xklickd_skill_pack_bytes("does-not-exist")
    with pytest.raises(ValueError):
        klickd.load_xklickd_skill_pack("nope")


def test_dir_returns_string():
    d = klickd.get_xklickd_skills_dir()
    assert isinstance(d, str)
    assert d
