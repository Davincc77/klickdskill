#!/usr/bin/env python3
"""Offline verifier for examples/v4/chimera-packs/.

Performs the following deterministic checks against the four starter
Chimera-aligned packs and their manifest:

  1. JSON validity for every *.klickd file and manifest.json.
  2. v4.0 envelope present (klickd_version == "4.0", payload_schema_version,
     created_at, encrypted == False, _pack_metadata.claims_v41_ga == False).
  3. Required Chimera fields present on x_klickd_pack (pack, pack_version,
     spec_ref, publisher, frameworks, base_transversal_core, competencies,
     levels, gates, human_authority, memory_scope, evidence_policy,
     source_policy, verification_gates, structured_memory, router_cost,
     forbidden_fields).
  4. No PII keys (display_name with a value, email, phone, address, ssn,
     national_id, real_name, dob, …) anywhere in the file. Allowed: keys set
     to null / [] / {} (publisher-owned starter shape).
  5. No host_skill fields (pedagogy, teaching_method, socratic_steps,
     prompt_strategy, scoring_rubric, intervention_policy, tone_rules,
     system_prompt_overrides) anywhere in the file.
  6. No persona-only fields (knowledge.mastered, mastered_topics,
     teaching_mode, agent_instructions, onboarding_trigger, user_preferences,
     companion_identity, learning_goal).
  7. forbidden_fields literal matches the RFC-009 §8.1 list exactly.
  8. SHA-256 file hash matches manifest.json; canonical-JSON hash is stable
     (re-canonicalising the parsed object yields the same hash recorded in
     the manifest).

Exit code 0 = all checks pass. Non-zero = at least one check failed.

No network. No provider calls. No paid resources.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
PACK_DIR = REPO_ROOT / "examples" / "v4" / "chimera-packs"
MANIFEST_PATH = PACK_DIR / "manifest.json"

PACK_FILES = ["user.klickd", "student.klickd", "research.klickd", "coding.klickd"]

V40_ENVELOPE_REQUIRED = {
    "klickd_version",
    "payload_schema_version",
    "created_at",
    "encrypted",
    "domain",
    "profile_kind",
    "_pack_metadata",
}

CHIMERA_PACK_REQUIRED = {
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
}

FORBIDDEN_PERSONA_ONLY_KEYS = {
    "mastered_topics",
    "teaching_mode",
    "agent_instructions",
    "onboarding_trigger",
    "user_preferences",
    "companion_identity",
    "learning_goal",
}

# Keys that, if present with a non-empty value, indicate PII. Keys are
# allowed if their value is null / [] / {} / False (publisher-owned starter).
PII_KEYS_WITH_VALUE = {
    "email",
    "phone",
    "phone_number",
    "address",
    "ssn",
    "social_security_number",
    "national_id",
    "real_name",
    "given_name",
    "family_name",
    "surname",
    "dob",
    "date_of_birth",
    "passport_number",
    "ip_address",
    "geolocation",
}

# display_name MUST be null in a starter pack (it is publisher-owned).
DISPLAY_NAME_MUST_BE_NULL_KEYS = {"display_name", "school_or_institution_ref"}

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


def _walk(obj: Any, path: str = ""):
    """Yield (path, key, value) for every key/value pair inside obj."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            here = f"{path}.{k}" if path else k
            yield here, k, v
            yield from _walk(v, here)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            here = f"{path}[{i}]"
            yield from _walk(item, here)


def _canonical_json_bytes(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def check_json_valid() -> list[str]:
    errs = []
    for name in PACK_FILES + ["manifest.json"]:
        p = PACK_DIR / name
        try:
            json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:
            errs.append(f"{name}: invalid JSON ({e})")
    return errs


def check_v40_envelope() -> list[str]:
    errs = []
    for name in PACK_FILES:
        obj = json.loads((PACK_DIR / name).read_text(encoding="utf-8"))
        missing = V40_ENVELOPE_REQUIRED - set(obj.keys())
        if missing:
            errs.append(f"{name}: missing v4.0 envelope keys: {sorted(missing)}")
        if obj.get("klickd_version") != "4.0":
            errs.append(f"{name}: klickd_version must be '4.0', got {obj.get('klickd_version')!r}")
        if obj.get("encrypted") is not False:
            errs.append(f"{name}: encrypted must be false")
        meta = obj.get("_pack_metadata", {})
        if meta.get("claims_v41_ga") is not False:
            errs.append(f"{name}: _pack_metadata.claims_v41_ga must be false")
        if meta.get("contains_real_pii") is not False:
            errs.append(f"{name}: _pack_metadata.contains_real_pii must be false")
    return errs


def check_chimera_required_fields() -> list[str]:
    errs = []
    for name in PACK_FILES:
        obj = json.loads((PACK_DIR / name).read_text(encoding="utf-8"))
        pack = obj.get("x_klickd_pack")
        if not isinstance(pack, dict):
            errs.append(f"{name}: x_klickd_pack block missing or not an object")
            continue
        missing = CHIMERA_PACK_REQUIRED - set(pack.keys())
        if missing:
            errs.append(f"{name}: x_klickd_pack missing required fields: {sorted(missing)}")
        if not pack.get("pack", "").startswith("x.klickd/"):
            errs.append(f"{name}: x_klickd_pack.pack must start with 'x.klickd/'")
        # frameworks must be a non-empty list of objects with scheme + iri_prefix
        fws = pack.get("frameworks", [])
        if not isinstance(fws, list) or len(fws) == 0:
            errs.append(f"{name}: frameworks[] must be a non-empty list")
        else:
            for i, fw in enumerate(fws):
                if not all(k in fw for k in ("scheme", "version", "iri_prefix")):
                    errs.append(f"{name}: frameworks[{i}] missing scheme/version/iri_prefix")
        # competencies must reference declared schemes
        declared = {fw["scheme"] for fw in fws if isinstance(fw, dict) and "scheme" in fw}
        for i, c in enumerate(pack.get("competencies", [])):
            ref = c.get("competency_ref", "")
            scheme = ref.split(":", 1)[0] if ":" in ref else None
            if scheme not in declared:
                errs.append(f"{name}: competencies[{i}].competency_ref scheme {scheme!r} not in declared frameworks")
        # human_authority shape
        ha = pack.get("human_authority", {})
        if ha.get("final_decision_owner") not in {"human_carrier", "human_carrier_with_guardian"}:
            errs.append(f"{name}: human_authority.final_decision_owner must be human_carrier(_with_guardian)")
        if ha.get("agent_role") != "advisory":
            errs.append(f"{name}: human_authority.agent_role must be 'advisory'")
        # gates raise_only
        gates = pack.get("gates", {})
        vg = gates.get("verification_gates_default", {})
        if vg.get("raise_only") is not True:
            errs.append(f"{name}: gates.verification_gates_default.raise_only must be true")
        # evidence_policy pointer_only
        ev = pack.get("evidence_policy", {})
        if ev.get("pointer_only") is not True:
            errs.append(f"{name}: evidence_policy.pointer_only must be true")
        # memory_scope shape
        ms = pack.get("memory_scope", "")
        if not ms.startswith("memory.x_klickd."):
            errs.append(f"{name}: memory_scope must start with 'memory.x_klickd.'")
        # router_cost.tokens_estimate must be int
        rc = pack.get("router_cost", {})
        if not isinstance(rc.get("tokens_estimate"), int):
            errs.append(f"{name}: router_cost.tokens_estimate must be an integer")
    return errs


def check_no_pii() -> list[str]:
    errs = []
    for name in PACK_FILES:
        obj = json.loads((PACK_DIR / name).read_text(encoding="utf-8"))
        for path, k, v in _walk(obj):
            if k in PII_KEYS_WITH_VALUE and v not in (None, "", [], {}, False):
                errs.append(f"{name}: PII key {k!r} at {path} has a non-empty value")
            if k in DISPLAY_NAME_MUST_BE_NULL_KEYS and v not in (None, "", [], {}):
                errs.append(f"{name}: {k!r} at {path} must be null in a starter pack, got {v!r}")
    return errs


def check_no_host_skill_fields() -> list[str]:
    errs = []
    for name in PACK_FILES:
        obj = json.loads((PACK_DIR / name).read_text(encoding="utf-8"))
        for path, k, _v in _walk(obj):
            if k in FORBIDDEN_HOST_SKILL_KEYS:
                errs.append(f"{name}: forbidden host_skill key {k!r} at {path}")
    return errs


def check_no_persona_only_fields() -> list[str]:
    errs = []
    for name in PACK_FILES:
        obj = json.loads((PACK_DIR / name).read_text(encoding="utf-8"))
        for path, k, v in _walk(obj):
            if k in FORBIDDEN_PERSONA_ONLY_KEYS:
                errs.append(f"{name}: forbidden persona-only key {k!r} at {path}")
            if k == "knowledge" and isinstance(v, dict) and "mastered" in v:
                errs.append(f"{name}: forbidden 'knowledge.mastered' shape at {path}")
    return errs


def check_forbidden_fields_literal() -> list[str]:
    errs = []
    for name in PACK_FILES:
        obj = json.loads((PACK_DIR / name).read_text(encoding="utf-8"))
        ff = obj.get("x_klickd_pack", {}).get("forbidden_fields")
        if ff != REQUIRED_FORBIDDEN_FIELDS_LITERAL:
            errs.append(
                f"{name}: forbidden_fields literal must equal RFC-009 §8.1 list, got {ff!r}"
            )
    return errs


def check_hash_stable() -> list[str]:
    errs = []
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    by_file = {p["file"]: p for p in manifest["packs"]}
    for name in PACK_FILES:
        if name not in by_file:
            errs.append(f"manifest.json: missing entry for {name}")
            continue
        entry = by_file[name]
        raw = (PACK_DIR / name).read_bytes()
        h_file = hashlib.sha256(raw).hexdigest()
        if h_file != entry["sha256_file"]:
            errs.append(
                f"{name}: sha256_file mismatch (file={h_file}, manifest={entry['sha256_file']})"
            )
        obj = json.loads(raw.decode("utf-8"))
        h_canon = hashlib.sha256(_canonical_json_bytes(obj)).hexdigest()
        if h_canon != entry["sha256_canonical_json"]:
            errs.append(
                f"{name}: sha256_canonical_json mismatch (canon={h_canon}, manifest={entry['sha256_canonical_json']})"
            )
        # bytes count
        if len(raw) != entry["bytes"]:
            errs.append(f"{name}: bytes mismatch (file={len(raw)}, manifest={entry['bytes']})")
    return errs


CHECKS = [
    ("json_valid", check_json_valid),
    ("v40_envelope", check_v40_envelope),
    ("chimera_required_fields", check_chimera_required_fields),
    ("no_pii", check_no_pii),
    ("no_host_skill_fields", check_no_host_skill_fields),
    ("no_persona_only_fields", check_no_persona_only_fields),
    ("forbidden_fields_literal", check_forbidden_fields_literal),
    ("hash_stable", check_hash_stable),
]


def main() -> int:
    all_errs: list[str] = []
    for name, fn in CHECKS:
        errs = fn()
        if errs:
            print(f"[FAIL] {name}")
            for e in errs:
                print(f"  - {e}")
            all_errs.extend(errs)
        else:
            print(f"[ OK ] {name}")
    if all_errs:
        print(f"\n{len(all_errs)} check(s) failed.")
        return 1
    print("\nAll checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
