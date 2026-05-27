"""Tests for examples/v4/klickdapp-skills/.

App-specific student `.klickd` carrier examples for Klickd.app on the v4.0
envelope. Verifies envelope shape, app/country metadata, learner-state
surface (state/progression/curriculum/country/language/session evidence/
mastery delta policy/human authority/gates), language matrix per country
and absence of host-side / Kai / intelligence-scoring / public
Chimera/v4.1/RFC wording.

No network. No provider calls. No paid resources.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
PACK_DIR = REPO_ROOT / "examples" / "v4" / "klickdapp-skills"

EXPECTED_FILES = [
    "klickdapp.lu.klickd",
    "klickdapp.fr.klickd",
    "klickdapp.be.klickd",
    "klickdapp.de.klickd",
]

EXPECTED_COUNTRY_LANGUAGES = {
    "LU": ["lb", "fr", "de", "en"],
    "FR": ["fr", "en"],
    "BE": ["fr", "nl", "de", "en"],
    "DE": ["de", "en"],
}

V40_ENVELOPE_REQUIRED = {
    "klickd_version",
    "payload_schema_version",
    "created_at",
    "encrypted",
    "domain",
    "profile_kind",
    "_pack_metadata",
}

REQUIRED_PACK_FIELDS = {
    "pack",
    "pack_version",
    "spec_ref",
    "publisher",
    "frameworks",
    "base_transversal_core",
    "competencies",
    "levels",
    "gates",
    "human_authority",
    "memory_scope",
    "evidence_policy",
    "source_policy",
    "verification_gates",
    "structured_memory",
    "router_cost",
    "forbidden_fields",
    "identity",
    "language_proficiency",
    "curriculum_refs",
    "subjects",
    "mastery",
    "mastery_delta_policy",
    "progression",
    "session_evidence",
}

FORBIDDEN_HOST_SKILL_KEYS = {
    "pedagogy",
    "teaching_method",
    "socratic_steps",
    "prompt_strategy",
    "scoring_rubric",
    "intervention_policy",
    "tone_rules",
    "system_prompt_overrides",
    "system_prompt",
    "kai",
    "kai_behavior",
    "kai_behaviour",
    "intelligence_score",
    "understanding_score",
}

FORBIDDEN_TEXT_PATTERNS = [
    re.compile(r"\bChimera\b", re.IGNORECASE),
    re.compile(r"\bRFC-?009\b", re.IGNORECASE),
    re.compile(r"v4\.1[^\"]*GA", re.IGNORECASE),
]

REQUIRED_FORBIDDEN_FIELDS_LITERAL = [
    "pedagogy",
    "teaching_method",
    "socratic_steps",
    "prompt_strategy",
    "scoring_rubric",
    "intervention_policy",
    "tone_rules",
    "system_prompt_overrides",
    "knowledge.mastered",
    "mastered_topics",
]


def _walk_keys(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            here = f"{path}.{k}" if path else k
            yield here, k, v
            yield from _walk_keys(v, here)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            yield from _walk_keys(item, f"{path}[{i}]")


@pytest.fixture(scope="module")
def packs():
    out = {}
    for name in EXPECTED_FILES:
        out[name] = json.loads((PACK_DIR / name).read_text(encoding="utf-8"))
    return out


def test_expected_files_only_present():
    actual = sorted(p.name for p in PACK_DIR.glob("klickdapp*.klickd"))
    assert actual == sorted(EXPECTED_FILES), (
        f"unexpected klickdapp.* files: actual={actual} expected={sorted(EXPECTED_FILES)}"
    )


def test_v40_envelope(packs):
    for name, obj in packs.items():
        missing = V40_ENVELOPE_REQUIRED - set(obj.keys())
        assert not missing, f"{name}: missing envelope keys {sorted(missing)}"
        assert obj["klickd_version"] == "4.0", name
        assert obj["encrypted"] is False, name
        assert obj["domain"] == "education", name
        assert obj["profile_kind"] == "learner", name


def test_pack_metadata(packs):
    for name, obj in packs.items():
        meta = obj["_pack_metadata"]
        assert meta["kind"] == "app_student_carrier", name
        assert meta["app"] == "klickd.app", name
        country = name.split(".")[1].upper()
        assert meta["country_scope"] == country, name
        assert meta["claims_v41_ga"] is False, name
        assert meta["contains_real_pii"] is False, name
        assert meta["contains_secrets"] is False, name


def test_required_pack_fields(packs):
    for name, obj in packs.items():
        pack = obj.get("x_klickd_pack")
        assert isinstance(pack, dict), f"{name}: x_klickd_pack missing"
        missing = REQUIRED_PACK_FIELDS - set(pack.keys())
        assert not missing, f"{name}: missing pack fields {sorted(missing)}"
        assert pack["pack"] == "x.klickd/student", name


def test_country_and_languages(packs):
    for name, obj in packs.items():
        country = name.split(".")[1].upper()
        pack = obj["x_klickd_pack"]
        assert pack["identity"]["country_ref"] == f"iso3166:{country}", name
        langs_in_proficiency = [
            entry["language_ref"].split(":", 1)[1]
            for entry in pack["language_proficiency"]
        ]
        assert langs_in_proficiency == EXPECTED_COUNTRY_LANGUAGES[country], (
            f"{name}: language_proficiency mismatch — got {langs_in_proficiency}"
        )
        assert pack["source_policy"]["language_tags"] == EXPECTED_COUNTRY_LANGUAGES[country], name
        assert pack["preferences"]["preferred_languages"] == EXPECTED_COUNTRY_LANGUAGES[country], name


def test_human_authority_and_gates(packs):
    for name, obj in packs.items():
        pack = obj["x_klickd_pack"]
        ha = pack["human_authority"]
        assert ha["final_decision_owner"] == "human_carrier", name
        assert ha["agent_role"] == "advisory", name
        gd = pack["gates"]["verification_gates_default"]
        assert gd["raise_only"] is True, name
        assert gd["claim_grounding_required"] is True, name
        veto = pack["gates"]["human_veto_policy"]
        for required_scope in (
            "mastery_writes",
            "exam_target_changes",
            "accommodations_changes",
            "curriculum_ref_changes",
            "progression_writes",
        ):
            assert required_scope in veto["scope"], f"{name}: missing veto scope {required_scope}"
        gates = {g["id"]: g for g in pack["verification_gates"]["gates"]}
        assert gates["public-post"]["level"] == "block", name
        assert gates["mastery-write"]["level"] == "confirm", name
        assert gates["progression-write"]["level"] == "confirm", name


def test_mastery_delta_policy(packs):
    for name, obj in packs.items():
        mdp = obj["x_klickd_pack"]["mastery_delta_policy"]
        assert mdp["raise_only"] is True, name
        assert mdp["human_confirmation_required"] is True, name
        assert mdp["evidence_pointer_required"] is True, name
        assert isinstance(mdp["max_delta_per_session"], (int, float)), name


def test_progression_and_session_evidence_pointer_only(packs):
    for name, obj in packs.items():
        pack = obj["x_klickd_pack"]
        prog = pack["progression"]
        assert prog["current_stage_ref"] is None, name
        assert prog["next_stage_ref"] is None, name
        sess = pack["session_evidence"]
        assert sess["pointer_only"] is True, name
        assert sess["entries"] == [], name
        assert pack["evidence_policy"]["pointer_only"] is True, name


def test_curriculum_refs_country_scoped(packs):
    for name, obj in packs.items():
        country = name.split(".")[1].upper()
        crefs = obj["x_klickd_pack"]["curriculum_refs"]
        assert len(crefs) >= 1, name
        for entry in crefs:
            assert "curriculum_ref" in entry and "scheme" in entry, name
        if country == "LU":
            assert any(c["scheme"] == "menje-lu" for c in crefs), name
        if country == "FR":
            assert any(c["scheme"] == "education-nationale-fr" for c in crefs), name
        if country == "BE":
            schemes = {c["scheme"] for c in crefs}
            assert "fwb-be" in schemes and "vlaanderen-onderwijs-be" in schemes, name
        if country == "DE":
            assert any(c["scheme"] == "kmk-de" for c in crefs), name


def test_no_pii_or_secrets(packs):
    pii_keys = {
        "email",
        "phone",
        "phone_number",
        "address",
        "ssn",
        "national_id",
        "real_name",
        "given_name",
        "family_name",
        "surname",
        "dob",
        "passport_number",
    }
    for name, obj in packs.items():
        for path, key, value in _walk_keys(obj):
            if key in pii_keys and value not in (None, "", [], {}, False):
                pytest.fail(f"{name}: PII key '{key}' at {path} has value {value!r}")
        assert obj["x_klickd_pack"]["identity"]["display_name"] is None, name
        assert obj["x_klickd_pack"]["identity"]["school_or_institution_ref"] is None, name


def test_no_host_side_or_kai_fields(packs):
    for name, obj in packs.items():
        for path, key, _ in _walk_keys(obj):
            if path.endswith(".forbidden_fields") or ".forbidden_fields[" in path:
                continue
            assert key not in FORBIDDEN_HOST_SKILL_KEYS, (
                f"{name}: forbidden host-side/Kai/scoring key '{key}' at {path}"
            )


def test_no_public_chimera_v41_rfc_text(packs):
    for name, obj in packs.items():
        raw = json.dumps(obj, ensure_ascii=False)
        for pattern in FORBIDDEN_TEXT_PATTERNS:
            assert not pattern.search(raw), (
                f"{name}: forbidden public-spec wording matched /{pattern.pattern}/"
            )


def test_forbidden_fields_literal(packs):
    for name, obj in packs.items():
        ff = obj["x_klickd_pack"]["forbidden_fields"]
        assert ff == REQUIRED_FORBIDDEN_FIELDS_LITERAL, (
            f"{name}: forbidden_fields literal mismatch — got {ff}"
        )
