# klickd — v3.x → v4 GA payload migrator (P0-5)
# SPDX-License-Identifier: CC0-1.0
#
# Cross-impl spec parity: equivalent suite lives at
# packages/@klickd/core/src/__tests__/migrate-v3-to-v4.test.ts.
#
# Contract under test: docs/spec/MIGRATION_V3_TO_V4.md

from __future__ import annotations

import json
from pathlib import Path

import pytest

from klickd import (
    KlickdError,
    KlickdErrorCode,
    migrate_payload,
    migrate_payload_iter_warnings,
    needs_migration,
)

# Strict-schema assertions are skipped when jsonschema is unavailable.
jsonschema = pytest.importorskip("jsonschema", reason="optional jsonschema dep")

from klickd import validate, validate_iter_errors  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[4]
V3_EXAMPLES_DIR = REPO_ROOT / "examples"
PINNED_TS = "2026-05-24T10:00:00Z"

# v3.x example files at the repo root (encrypted:false plain-payload form).
V3_FILES = [
    "student_fr.klickd",
    "full_v34.klickd",
    "family_plan.klickd",
    "minimal.klickd",
    "professional_en.klickd",
    "example_v33_full.klickd",
]

# v3 example files whose CONTENT carries v3-era enum values that the v4 GA
# strict schema deliberately tightens (e.g. learning_goal.stakes='critical'
# was accepted by v3.4 but the v4 GA strict enum is {low, medium, high}).
# Per docs/spec/MIGRATION_V3_TO_V4.md §3.4 the migrator is NON-DESTRUCTIVE,
# so it must surface these via warnings rather than rewrite the value. The
# round-trip assertions below still run for these files; only the strict
# schema-pass assertion is skipped.
V3_FILES_STRICT_EXEMPT = {"full_v34.klickd"}


def _load_v3(name: str) -> dict:
    return json.loads((V3_EXAMPLES_DIR / name).read_text(encoding="utf-8"))


# -- needs_migration ---------------------------------------------------------


def test_needs_migration_v3_no_schema_version_field():
    assert needs_migration({"identity": {"name": "x"}}) is True


def test_needs_migration_explicit_v3():
    assert needs_migration({"payload_schema_version": "3.0"}) is True
    assert needs_migration({"payload_schema_version": "3.4"}) is True
    assert needs_migration({"payload_schema_version": "3.5"}) is True


def test_needs_migration_already_v4():
    assert needs_migration({"payload_schema_version": "4.0"}) is False
    assert needs_migration({"payload_schema_version": "4.0.0-preview.1"}) is False


def test_needs_migration_non_dict():
    assert needs_migration("not a dict") is False
    assert needs_migration([]) is False
    assert needs_migration(None) is False


def test_needs_migration_unknown_version_does_not_auto_migrate():
    # Unknown values are not auto-migrated; migrate_payload would raise.
    assert needs_migration({"payload_schema_version": "9.9"}) is False


# -- migrate_payload: core invariants ----------------------------------------


def test_migrator_stamps_v4_schema_and_profile_kind():
    src = {"payload_schema_version": "3.0", "identity": {"name": "Alice"}}
    out = migrate_payload(src, migrated_at=PINNED_TS)
    assert out["payload_schema_version"] == "4.0"
    assert out["profile_kind"] == "learner"
    assert out["migration"] == {
        "source_version": "3.0",
        "migrated_at": PINNED_TS,
    }


def test_migrator_records_pointer_refs():
    src = {"payload_schema_version": "3.4"}
    out = migrate_payload(
        src,
        migrated_at=PINNED_TS,
        migration_report_ref="file://reports/2026-05-24.md",
        backup_ref="ipfs://Qm...",
    )
    assert out["migration"] == {
        "source_version": "3.4",
        "migrated_at": PINNED_TS,
        "migration_report_ref": "file://reports/2026-05-24.md",
        "backup_ref": "ipfs://Qm...",
    }


def test_migrator_is_non_destructive():
    src = {"payload_schema_version": "3.4", "identity": {"name": "Bob"}}
    snapshot = json.loads(json.dumps(src))
    _ = migrate_payload(src, migrated_at=PINNED_TS)
    assert src == snapshot, "migrate_payload must not mutate its input"


def test_migrator_default_source_version_when_absent():
    out = migrate_payload({"identity": {}}, migrated_at=PINNED_TS)
    assert out["migration"]["source_version"] == "3.x"


def test_migrator_respects_caller_profile_kind():
    out = migrate_payload(
        {"payload_schema_version": "3.4"},
        profile_kind="creator",
        migrated_at=PINNED_TS,
    )
    assert out["profile_kind"] == "creator"


def test_migrator_preserves_caller_supplied_profile_kind():
    out = migrate_payload(
        {"payload_schema_version": "3.4", "profile_kind": "team"},
        migrated_at=PINNED_TS,
    )
    assert out["profile_kind"] == "team"


def test_migrator_preserves_all_v3_blocks_verbatim():
    src = {
        "payload_schema_version": "3.4",
        "domain_schema_version": "education-1.2",
        "injection_target": "system_prompt",
        "identity": {"name": "Eve", "language": "fr"},
        "context": {"summary": "test", "decisions_locked": ["always-fr"]},
        "knowledge": {"mastered": ["pythagoras"]},
        "memory": [],
        "agent_instructions": "be concise",
        "user_preferences": "advisory",
        "companion_identity": {"name": "Aria"},
        "ethics": {"locked_actions": ["self_harm"]},
        "learning_goal": {"type": "exam", "stakes": "high"},
        "x_custom_extension": {"foo": "bar"},
    }
    out = migrate_payload(src, migrated_at=PINNED_TS)
    for key in (
        "domain_schema_version",
        "injection_target",
        "identity",
        "context",
        "knowledge",
        "memory",
        "agent_instructions",
        "user_preferences",
        "companion_identity",
        "ethics",
        "learning_goal",
        "x_custom_extension",
    ):
        assert out[key] == src[key], f"{key} must round-trip verbatim"
    # Locked safety fields preserved without mutation.
    assert out["context"]["decisions_locked"] == ["always-fr"]
    assert out["ethics"]["locked_actions"] == ["self_harm"]


def test_migrator_does_not_invent_safety_surface():
    out = migrate_payload({"payload_schema_version": "3.4"}, migrated_at=PINNED_TS)
    for forbidden in (
        "verification_gates",
        "human_veto_policy",
        "claim_sources",
        "risk_thresholds",
        "preflight_checks",
        "error_journal",
        "media_profile",
        "verification_artifacts",
        "reversibility",
        "blast_radius",
        "contract_tests",
        "success_criteria",
        "deprecated_fields",
        "gaming_profile",
        "_example_metadata",
        "context_cost",
    ):
        assert forbidden not in out, f"migrator must not synthesize {forbidden!r}"


def test_migrator_does_not_touch_envelope_keys_if_present_in_payload_dict():
    # When a caller hands the full envelope+payload dict (encrypted:false
    # files), the migrator must NOT mutate envelope-AAD fields.
    src = _load_v3("minimal.klickd")
    envelope_snapshot = {
        k: src[k]
        for k in ("klickd_version", "created_at", "encrypted", "domain")
        if k in src
    }
    out = migrate_payload(src, migrated_at=PINNED_TS)
    for k, v in envelope_snapshot.items():
        assert out[k] == v, f"envelope key {k} must not be rewritten"


def test_migrator_idempotent_on_v4_passthrough():
    v4 = {
        "payload_schema_version": "4.0",
        "profile_kind": "learner",
        "migration": {"source_version": "3.4", "migrated_at": PINNED_TS},
        "identity": {"name": "Sam"},
    }
    once = migrate_payload(v4)
    assert once == v4
    twice = migrate_payload(once)
    assert twice == v4


def test_migrator_v4_passthrough_with_pointer_refs_only():
    v4 = {"payload_schema_version": "4.0", "identity": {"name": "Sam"}}
    out = migrate_payload(
        v4,
        migrated_at=PINNED_TS,
        migration_report_ref="file://r.md",
    )
    assert out["migration"]["migration_report_ref"] == "file://r.md"
    assert out["migration"]["source_version"] == "4.0"


def test_migrator_idempotent_running_twice_on_v3():
    src = {"payload_schema_version": "3.4", "identity": {"name": "Lex"}}
    once = migrate_payload(src, migrated_at=PINNED_TS)
    twice = migrate_payload(once, migrated_at=PINNED_TS)
    assert twice == once


# -- migrate_payload: errors -------------------------------------------------


def test_migrator_rejects_non_dict():
    with pytest.raises(KlickdError) as exc:
        migrate_payload("nope")  # type: ignore[arg-type]
    assert exc.value.code == KlickdErrorCode.SCHEMA


def test_migrator_rejects_unknown_schema_version():
    with pytest.raises(KlickdError) as exc:
        migrate_payload({"payload_schema_version": "9.9"})
    assert exc.value.code == KlickdErrorCode.SCHEMA


# -- warnings ----------------------------------------------------------------


def test_no_warnings_on_clean_v3_minimal():
    src = {
        "payload_schema_version": "3.4",
        "domain_schema_version": "education-1.0",
    }
    assert migrate_payload_iter_warnings(src) == []


def test_warns_on_no_schema_version_and_no_domain_version():
    warnings = migrate_payload_iter_warnings({"identity": {"name": "x"}})
    assert any("pin source_version" in m for _, m in warnings)


def test_warns_on_overlong_decisions_locked():
    payload = {
        "payload_schema_version": "3.4",
        "domain_schema_version": "education-1.0",
        "context": {"decisions_locked": ["a" * 2000]},
    }
    warnings = migrate_payload_iter_warnings(payload)
    assert any("exceeds 1024" in m for _, m in warnings)


def test_warns_on_unknown_profile_kind():
    payload = {
        "payload_schema_version": "3.4",
        "domain_schema_version": "education-1.0",
        "profile_kind": "ufo",
    }
    warnings = migrate_payload_iter_warnings(payload)
    assert any("non-reserved profile_kind" in m for _, m in warnings)


# -- v3 example files validate strict v4 after migration ---------------------


@pytest.mark.parametrize("filename", V3_FILES)
def test_v3_examples_round_trip_through_migrator(filename):
    if not (V3_EXAMPLES_DIR / filename).is_file():
        pytest.skip(f"missing v3 example {filename}")
    src = _load_v3(filename)
    out = migrate_payload(src, migrated_at=PINNED_TS)
    assert out["payload_schema_version"] == "4.0"
    # Every non-migration top-level key from the v3 source must survive.
    for key in src:
        if key in ("payload_schema_version",):
            continue
        assert key in out, f"{filename}: v3 key {key!r} dropped by migrator"


@pytest.mark.parametrize("filename", V3_FILES)
def test_migrated_v3_examples_validate_strict_v4_payload(filename):
    if not (V3_EXAMPLES_DIR / filename).is_file():
        pytest.skip(f"missing v3 example {filename}")
    if filename in V3_FILES_STRICT_EXEMPT:
        pytest.skip(
            f"{filename}: contains v3-era enum value tightened by v4 GA "
            "strict schema; migrator preserves it verbatim by design"
        )
    src = _load_v3(filename)
    out = migrate_payload(src, migrated_at=PINNED_TS)
    # Payload-strict schema is permissive on top-level unknown envelope
    # fields (klickd_version, encrypted, …), so we validate the whole
    # migrated dict directly.
    errors = validate_iter_errors(out, strict=True, target="payload")
    assert errors == [], (
        f"{filename}: strict v4 payload validation failed: {errors[:3]}"
    )


# -- no secrets / PII leakage ------------------------------------------------


def test_migrator_does_not_emit_secret_like_fields():
    """The migrator must not introduce any field that looks like a
    secret. This is a structural check, not a content sanitizer."""
    out = migrate_payload(
        {"payload_schema_version": "3.4", "identity": {"name": "x"}},
        migrated_at=PINNED_TS,
    )
    # Walk all keys (recursively) and assert none start with a
    # well-known secret prefix that the migrator might have invented.
    forbidden_substrings = ("password", "passphrase", "secret", "api_key", "token")

    def walk(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                low = k.lower()
                # Identity keys are caller-supplied; only flag keys the
                # migrator itself synthesizes, which all live at the top
                # level + inside `migration`.
                for needle in forbidden_substrings:
                    assert needle not in low, (
                        f"migrator-introduced key {k!r} resembles a secret"
                    )
                walk(v)
        elif isinstance(obj, list):
            for x in obj:
                walk(x)

    # Only validate keys not present in the caller-supplied source.
    src_keys = {"payload_schema_version", "identity"}
    extra = {k: v for k, v in out.items() if k not in src_keys}
    walk(extra)
