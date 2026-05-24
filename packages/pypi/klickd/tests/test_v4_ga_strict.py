# klickd — v4 GA strict schema + persona round-trip tests
# SPDX-License-Identifier: CC0-1.0
#
# P0-3 (SDK Python V4 GA alignment): validates the SDK's strict / preview
# validation surface against the five R4-P0-3 persona examples and against
# negative cases. Round-trip behaviour (SPEC.md §33.7 unknown-field
# preservation) is verified for every persona.
#
# These tests intentionally do NOT cover the wizard-only docs-only error
# codes from R4-P0-2 (KLICKD_E_PASS_MISMATCH, KLICKD_E_SAVE_LOCAL,
# KLICKD_E_LEGACY_VERSION, KLICKD_E_CORRUPT, KLICKD_E_POLICY_LOCKED,
# KLICKD_E_UNSAFE_QR) — the R4-P0-2 spec explicitly defers SDK alignment
# of those codes to a later track.

from __future__ import annotations

import json
from pathlib import Path

import pytest

from klickd import (
    KlickdError,
    KlickdErrorCode,
    load_klickd,
    save_klickd,
    validate,
    validate_iter_errors,
)

# Validation tests require the optional `jsonschema` dependency.
# Install with `pip install klickd[validate]` (or `pip install jsonschema`).
# When absent, every validation test in this file is skipped — load/save
# tests in test_roundtrip.py and test_v4_preview_roundtrip.py still run.
jsonschema = pytest.importorskip("jsonschema")

REPO_ROOT = Path(__file__).resolve().parents[4]
PERSONAS_DIR = REPO_ROOT / "examples" / "v4" / "personas"
PASSPHRASE = "correct-horse-battery-staple-v4"


def _load_persona(name: str) -> dict:
    return json.loads((PERSONAS_DIR / name).read_text(encoding="utf-8"))


PERSONA_FILES = sorted(
    p.name for p in PERSONAS_DIR.glob("*.klickd")
) if PERSONAS_DIR.is_dir() else []


# -- Sanity: personas directory and bundled schemas resolve ------------------


def test_personas_dir_exists():
    assert PERSONAS_DIR.is_dir(), f"missing personas dir: {PERSONAS_DIR}"
    assert PERSONA_FILES, "no persona examples found"
    assert len(PERSONA_FILES) == 5, f"expected 5 personas, got {len(PERSONA_FILES)}"


def test_bundled_schemas_resolve():
    from klickd import validate as _v  # re-export available
    assert callable(_v)
    # The validate module bundles four schema files; load one to prove it.
    from klickd.validate import _load_schema  # type: ignore[attr-defined]
    payload_schema = _load_schema("payload-strict")
    assert payload_schema["$id"].endswith("klickd-payload.schema.json")
    unified_schema = _load_schema("unified-strict")
    assert unified_schema["$id"].endswith("klickd.schema.json")


# -- Strict validation: personas ---------------------------------------------


@pytest.mark.parametrize("persona", PERSONA_FILES)
def test_persona_passes_strict_payload(persona):
    """Each R4-P0-3 persona MUST validate against the strict v4 payload schema."""
    data = _load_persona(persona)
    # Personas carry envelope fields too; validate the payload schema first
    # (which is permissive on unknown top-level envelope fields).
    validate(data, strict=True, target="payload")


@pytest.mark.parametrize("persona", PERSONA_FILES)
def test_persona_passes_strict_unified(persona):
    """Each persona MUST also validate against the unified strict schema."""
    data = _load_persona(persona)
    validate(data, strict=True, target="unified")


@pytest.mark.parametrize("persona", PERSONA_FILES)
def test_persona_passes_preview_payload(persona):
    """Each persona MUST also validate against the permissive preview schema."""
    data = _load_persona(persona)
    validate(data, strict=False, target="payload")


# -- Round-trip preservation: §33.7 ------------------------------------------


@pytest.mark.parametrize("persona", PERSONA_FILES)
def test_persona_roundtrips_unknown_fields(persona):
    """save_klickd → load_klickd MUST preserve every persona field verbatim."""
    original = _load_persona(persona)
    envelope = save_klickd(original, PASSPHRASE, domain=original.get("domain", "education"))
    recovered = load_klickd(envelope, passphrase=PASSPHRASE)
    assert recovered == original, f"persona {persona} mutated on round-trip"


@pytest.mark.parametrize("persona", PERSONA_FILES)
def test_persona_double_roundtrip_stable(persona):
    """Two consecutive round-trips MUST be stable (idempotent)."""
    original = _load_persona(persona)
    once = load_klickd(save_klickd(original, PASSPHRASE), passphrase=PASSPHRASE)
    twice = load_klickd(save_klickd(once, PASSPHRASE), passphrase=PASSPHRASE)
    assert twice == original


# -- Strict validation: negative cases (must reject) -------------------------


def _minimal_strict_payload() -> dict:
    return {"payload_schema_version": "4.0"}


def test_unknown_gate_level_rejected():
    bad = _minimal_strict_payload()
    bad["verification_gates"] = {
        "version": 1,
        "gates": [{"action_class": "x", "level": "loud"}],
    }
    with pytest.raises(KlickdError) as exc:
        validate(bad, strict=True)
    assert exc.value.code == KlickdErrorCode.SCHEMA


def test_media_entry_missing_hash_rejected():
    bad = _minimal_strict_payload()
    bad["media_profile"] = {
        "version": 1,
        "entries": [{"id": "x", "modality": "voice"}],
    }
    with pytest.raises(KlickdError) as exc:
        validate(bad, strict=True)
    assert exc.value.code == KlickdErrorCode.SCHEMA


def test_unknown_media_modality_rejected():
    bad = _minimal_strict_payload()
    bad["media_profile"] = {
        "version": 1,
        "entries": [
            {
                "id": "x",
                "modality": "video",  # not in v1 enum
                "hash": {"algo": "blake3", "value": "deadbeef"},
            }
        ],
    }
    with pytest.raises(KlickdError) as exc:
        validate(bad, strict=True)
    assert exc.value.code == KlickdErrorCode.SCHEMA


def test_unsupported_payload_schema_version_rejected():
    with pytest.raises(KlickdError) as exc:
        validate({"payload_schema_version": "9.9"}, strict=True)
    assert exc.value.code == KlickdErrorCode.SCHEMA


def test_missing_payload_schema_version_rejected():
    with pytest.raises(KlickdError) as exc:
        validate({}, strict=True)
    assert exc.value.code == KlickdErrorCode.SCHEMA


def test_encrypted_envelope_missing_kdf_rejected_unified():
    bad = {
        "klickd_version": "4.0",
        "created_at": "2026-05-24T00:00:00Z",
        "encrypted": True,
    }
    with pytest.raises(KlickdError) as exc:
        validate(bad, strict=True, target="unified")
    assert exc.value.code == KlickdErrorCode.SCHEMA


# -- Both strict gate shapes accepted ----------------------------------------


def test_structured_gates_form_accepted():
    payload = _minimal_strict_payload()
    payload["verification_gates"] = {
        "version": 1,
        "user_default": "silent",
        "gates": [
            {"id": "g1", "action_class": "public_post", "level": "block"},
            {"action_class": "factual_claim_with_date", "level": "confirm"},
        ],
    }
    validate(payload, strict=True)


def test_flat_gates_form_accepted():
    payload = _minimal_strict_payload()
    payload["verification_gates"] = {
        "public_post": "block",
        "factual_claim_with_date": "confirm",
    }
    validate(payload, strict=True)


def test_flat_gates_unknown_level_rejected():
    payload = _minimal_strict_payload()
    payload["verification_gates"] = {"public_post": "loud"}
    with pytest.raises(KlickdError) as exc:
        validate(payload, strict=True)
    assert exc.value.code == KlickdErrorCode.SCHEMA


# -- Preview-style files validate against both schemas -----------------------


def test_preview_value_accepted_in_strict_schema():
    """payload_schema_version '4.0.0-preview.1' MUST be accepted by strict (P0-2 design)."""
    payload = {"payload_schema_version": "4.0.0-preview.1"}
    validate(payload, strict=True)
    validate(payload, strict=False)


def test_ga_value_accepted_in_preview_schema():
    payload = {"payload_schema_version": "4.0", "preview": "v4.0.0-preview.1"}
    validate(payload, strict=False)


# -- v3.x backward compatibility (no regression) -----------------------------


def test_v3_payload_unaffected_by_v4_validator():
    """A v3.0 payload MUST still load/save without invoking v4 validation."""
    v3_payload = {
        "payload_schema_version": "3.0.0",
        "domain_schema_version": "1.0.0",
        "identity": {"name": "v3 user", "language": "fr"},
        "agent_instructions": "be concise",
    }
    envelope = save_klickd(v3_payload, PASSPHRASE)
    recovered = load_klickd(envelope, passphrase=PASSPHRASE)
    assert recovered == v3_payload


def test_v3_payload_fails_v4_strict_validation():
    """A v3 payload_schema_version MUST NOT validate against v4 strict (different enum)."""
    v3_payload = {"payload_schema_version": "3.0.0"}
    with pytest.raises(KlickdError) as exc:
        validate(v3_payload, strict=True)
    assert exc.value.code == KlickdErrorCode.SCHEMA


# -- Optional registered profiles (media/project/gaming) ---------------------


def test_gaming_profile_persona_validates():
    """RPG persona carries a gaming-style profile_kind; MUST validate strict."""
    persona = _load_persona("05-rpg-gamer-en.klickd")
    validate(persona, strict=True, target="payload")
    # And round-trip preserves any gaming-specific fields verbatim.
    recovered = load_klickd(save_klickd(persona, PASSPHRASE), passphrase=PASSPHRASE)
    assert recovered == persona


def test_creator_persona_validates():
    """Créateur média persona; MUST validate strict and round-trip."""
    persona = _load_persona("04-createur-media-fr.klickd")
    validate(persona, strict=True, target="payload")
    recovered = load_klickd(save_klickd(persona, PASSPHRASE), passphrase=PASSPHRASE)
    assert recovered == persona


def test_project_chef_persona_validates():
    """Chef de projet PME persona (project.klickd-flavoured); MUST validate."""
    persona = _load_persona("02-chef-projet-pme-fr.klickd")
    validate(persona, strict=True, target="payload")


# -- iter_errors variant -----------------------------------------------------


def test_validate_iter_errors_empty_on_valid():
    persona = _load_persona(PERSONA_FILES[0])
    assert validate_iter_errors(persona, strict=True) == []


def test_validate_iter_errors_returns_paths():
    bad = _minimal_strict_payload()
    bad["verification_gates"] = {"public_post": "loud"}
    errs = validate_iter_errors(bad, strict=True)
    assert errs
    # Each entry is (path, message)
    for path, msg in errs:
        assert isinstance(path, str)
        assert isinstance(msg, str)


# -- Unknown-field preservation under validation (§33.7) ---------------------


def test_unknown_top_level_field_validates_and_roundtrips():
    """An unknown top-level field MUST validate (additionalProperties: true)
    AND MUST round-trip verbatim (§33.7)."""
    payload = _minimal_strict_payload()
    payload["x_experimental_block"] = {"future": True, "values": [1, 2, 3]}
    validate(payload, strict=True)
    recovered = load_klickd(save_klickd(payload, PASSPHRASE), passphrase=PASSPHRASE)
    assert recovered["x_experimental_block"] == payload["x_experimental_block"]
