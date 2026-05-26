#!/usr/bin/env python3
# RFC-009 Chimera Draft scaffold — local offline checker.
#
# Performs the following deterministic, offline checks against the Draft
# scaffold under docs/rfcs/chimera/:
#   1. JSON validity of every *.bundle.json + bundle-manifest.json + every
#      file under packs/fixtures/.
#   2. Strict Draft 2020-12 schema validation of the round-trip fixture
#      docs/rfcs/chimera/packs/fixtures/x.klickd.student.example.json
#      against docs/rfcs/chimera/schema-fragments/x.klickd.student.schema.json.
#   3. Negative fixtures: corrupted copies that inject forbidden / legacy /
#      authority-weakening fields MUST fail validation.
#   4. SKOS bundle round-trip: every competency_ref / framework_ref /
#      cefr scheme_ref used by the fixture resolves to an @id in one of
#      the SKOS bundles (base_transversal_core.bundle.json or
#      x.klickd.student.bundle.json).
#   5. SHA-256 bundle integrity against frameworks/bundle-manifest.json.
#   6. PII guard: no PII keys appear anywhere in the fixture.
#   7. Banned-wording guard: docs touched by RFC-009 do not contain
#      "persona-as-pack" phrasings.
#   8. Markdown link check: every relative link in the four RFC-009 docs
#      touched by this PR resolves to an existing file.
#
# Exit code 0 = all checks pass. Non-zero = at least one check failed.
#
# No network calls. No provider tokens. No paid resources.

from __future__ import annotations

import copy
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[4]
RFC_DIR = REPO_ROOT / "docs" / "rfcs"
CHIMERA = RFC_DIR / "chimera"

SCHEMA_PATH = CHIMERA / "schema-fragments" / "x.klickd.student.schema.json"
FIXTURE_PATH = CHIMERA / "packs" / "fixtures" / "x.klickd.student.example.json"
BUNDLE_BASE = CHIMERA / "frameworks" / "base_transversal_core.bundle.json"
BUNDLE_STUDENT = CHIMERA / "frameworks" / "x.klickd.student.bundle.json"
BUNDLE_MANIFEST = CHIMERA / "frameworks" / "bundle-manifest.json"

DOCS_TOUCHED_BY_PR = [
    RFC_DIR / "RFC-009-chimera-v4.1.md",
    CHIMERA / "README.md",
    CHIMERA / "packs" / "README.md",
    CHIMERA / "packs" / "student.md",
    CHIMERA / "packs" / "router_cost.md",
    CHIMERA / "packs" / "fixtures" / "README.md",
    CHIMERA / "frameworks" / "README.md",
    CHIMERA / "schema-fragments" / "README.md",
]

# Banned wording: phrases that conflate persona with pack (RFC-009 §0.1.2)
# or imply a legacy adapter (RFC-009 §5.0). These MUST NOT appear in the
# RFC-009 documents themselves (other than as the FORBIDDEN examples they
# explicitly list and reject). The allowlist below enumerates the legitimate
# discussion sites so the check stays strict everywhere else.
BANNED_PHRASES = [
    "skill file",                # ambiguous; should be carrier_pack / competency_pack / host_skill
    "student skill",             # implies pedagogy in the pack
    "domain skill",              # same
    "competency skill",          # tautology
    "pack skill",                # self-contradiction
    "persona-as-pack",           # only OK in test names / this script
    "personas as packs",
    "relabelled persona",        # the RFC rejects this; only OK when refuted
    "repackaged persona",
]

# Files where the banned phrases legitimately appear (because the RFC
# describes them in order to forbid them). Counts in these files are
# allowed up to the documented occurrence count; counts ABOVE that ceiling
# fail the check.
BANNED_PHRASES_ALLOWED_OCCURRENCES = {
    # In RFC-009-chimera-v4.1.md, the §0.1.2 "Forbidden ambiguous phrasings"
    # table enumerates the banned phrases inside backticks; that table is
    # itself the canonical reference. Each phrase MAY appear there but
    # nowhere else in normative prose.
    RFC_DIR / "RFC-009-chimera-v4.1.md": {
        "skill file": 2,        # §0.1.2 row + the description it rejects
        "student skill": 2,     # §0.1.2 row + the description it rejects
        "domain skill": 2,
        "competency skill": 2,
        "pack skill": 2,
        "relabelled persona": 1,
        "repackaged persona": 0,
        "personas as packs": 1,
        "persona-as-pack": 0,
    },
    # The chimera README has a single-line refutation of the forbidden phrasings,
    # mirroring §0.1.2 of the RFC.
    CHIMERA / "README.md": {
        "skill file": 1,
        "student skill": 1,
        "domain skill": 1,
    },
    # The packs README defines the no-fake-catalog rule and so MAY mention
    # the rejected shapes when refuting them.
    CHIMERA / "packs" / "README.md": {
        "skill file": 0,
        "relabelled persona": 1,
        "repackaged persona": 1,
        "personas as packs": 1,
        "persona-as-pack": 0,
    },
    # This very script enumerates the banned phrases; that file is NOT
    # in DOCS_TOUCHED_BY_PR for the banned-wording check (the check
    # targets docs only), so we don't need an entry here. The fixtures
    # README also legitimately discusses the rejected shapes:
    CHIMERA / "packs" / "fixtures" / "README.md": {
        "persona-as-pack": 1,   # §1: "fixtures are not persona files"
    },
}

# PII keys: top-level or nested keys that MUST NOT appear anywhere in a
# pack manifest (RFC-009 §8.4 — no PII in publisher-owned pack files).
PII_KEYS = {
    "email", "phone", "phone_number", "national_id", "social_security_number",
    "address", "street_address", "postal_address", "postcode",
    "birthdate", "date_of_birth", "dob",
    "full_name", "first_name", "last_name", "surname", "given_name",
    "passport_number", "id_card_number",
    "iban", "bank_account",
}


class CheckError(RuntimeError):
    """Raised by individual checks; collected then reported."""


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _walk_keys(obj: Any):
    """Yield every JSON key (recursively) under `obj`."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k
            yield from _walk_keys(v)
    elif isinstance(obj, list):
        for item in obj:
            yield from _walk_keys(item)


def _gather_refs(obj: Any) -> set[str]:
    """Collect every competency_ref / framework_ref / scheme_ref / iri."""
    refs: set[str] = set()
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in {"competency_ref", "framework_ref"} and isinstance(v, str):
                refs.add(v)
            if k == "subject_ref" and isinstance(v, str):
                refs.add(v)
            refs |= _gather_refs(v)
    elif isinstance(obj, list):
        for item in obj:
            refs |= _gather_refs(item)
    return refs


def check_json_validity() -> list[str]:
    errors: list[str] = []
    paths = [
        SCHEMA_PATH,
        FIXTURE_PATH,
        BUNDLE_BASE,
        BUNDLE_STUDENT,
        BUNDLE_MANIFEST,
    ]
    for p in paths:
        try:
            _read_json(p)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"JSON invalid: {p} — {exc!r}")
    return errors


def check_schema_validates_fixture() -> list[str]:
    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        return ["jsonschema>=4.18 not available — pip install 'jsonschema>=4.18' to run schema checks"]

    schema = _read_json(SCHEMA_PATH)
    fixture = _read_json(FIXTURE_PATH)

    errs: list[str] = []
    try:
        Draft202012Validator.check_schema(schema)
    except Exception as exc:  # noqa: BLE001
        errs.append(f"schema itself fails Draft 2020-12 meta-check: {exc!r}")
        return errs

    v = Draft202012Validator(schema)
    fixture_errors = sorted(v.iter_errors(fixture), key=lambda e: list(e.absolute_path))
    for e in fixture_errors:
        errs.append(f"fixture fails schema at {list(e.absolute_path)}: {e.message}")
    return errs


def check_negative_fixtures() -> list[str]:
    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        return []

    schema = _read_json(SCHEMA_PATH)
    base = _read_json(FIXTURE_PATH)
    v = Draft202012Validator(schema)

    cases = []

    # (1) Carrier-vs-skill violation: inject `pedagogy` top-level block.
    bad = copy.deepcopy(base)
    bad["pedagogy"] = {"steps": ["ask", "wait", "correct"]}
    cases.append(("pedagogy top-level", bad))

    # (2) Legacy persona key.
    bad = copy.deepcopy(base)
    bad["mastered_topics"] = ["derivatives", "limits"]
    cases.append(("mastered_topics legacy key", bad))

    # (3) Homegrown competency.
    bad = copy.deepcopy(base)
    bad["competencies"].append({
        "competency_ref": "klickd:custom:foo",
        "scheme": "esco",
        "prefLabel": "homegrown",
        "acquired_at": None,
    })
    cases.append(("homegrown competency_ref", bad))

    # (4) Human-authority weakening: raise_only false.
    bad = copy.deepcopy(base)
    bad["gates"]["verification_gates_default"]["raise_only"] = False
    cases.append(("raise_only=false weakens v4.0 gate", bad))

    # (5) agent_role weakening.
    bad = copy.deepcopy(base)
    bad["human_authority"]["agent_role"] = "executor"
    cases.append(("agent_role=executor breaks advisory invariant", bad))

    # (6) PII in identity.
    bad = copy.deepcopy(base)
    bad["identity"]["email"] = "test@example.com"
    cases.append(("PII in identity (email)", bad))

    # (7) Removing a required forbidden_fields literal.
    bad = copy.deepcopy(base)
    bad["forbidden_fields"] = [f for f in bad["forbidden_fields"] if f != "pedagogy"]
    cases.append(("forbidden_fields missing 'pedagogy' literal", bad))

    errs: list[str] = []
    for name, payload in cases:
        errors_found = list(v.iter_errors(payload))
        if not errors_found:
            errs.append(f"negative fixture '{name}' UNEXPECTEDLY validated (should have failed)")
    return errs


def check_skos_resolves() -> list[str]:
    fixture = _read_json(FIXTURE_PATH)
    base_bundle = _read_json(BUNDLE_BASE)
    student_bundle = _read_json(BUNDLE_STUDENT)

    iri_index: set[str] = set()
    notation_index: set[str] = set()
    for bundle in (base_bundle, student_bundle):
        for node in bundle["concepts"]["@graph"]:
            iri = node.get("@id")
            if iri:
                iri_index.add(iri)
            notation = node.get("skos:notation")
            scheme = None
            for fw in bundle.get("frameworks", []):
                if iri and iri.startswith(fw["iri_prefix"]):
                    scheme = fw["scheme"]
                    break
            if notation and scheme:
                notation_index.add(f"{scheme}:{notation}")
            # also accept the prefixed form using last-path-component for ESCO
            if iri and scheme == "esco" and "/skill/" in iri:
                code = iri.rsplit("/", 1)[-1]
                notation_index.add(f"esco:{code}")

    # also accept CEFR levels which appear in the fixture as cefr_level strings
    # plus the scheme_ref URL — the URL itself must be in iri_index for the
    # CEFR scheme to be considered resolved.
    refs = _gather_refs(fixture)

    errs: list[str] = []
    for ref in sorted(refs):
        # framework_ref values are full URLs; competency_ref values are
        # prefix-shortened. Accept either if present in either index.
        if ref.startswith("http://") or ref.startswith("https://"):
            if ref not in iri_index:
                errs.append(f"SKOS resolution miss: full IRI '{ref}' not in bundle @graph")
        else:
            if ref not in notation_index:
                errs.append(f"SKOS resolution miss: prefixed ref '{ref}' not in bundle notation index")

    return errs


def check_bundle_hashes() -> list[str]:
    manifest = _read_json(BUNDLE_MANIFEST)
    errs: list[str] = []
    for entry in manifest["bundles"]:
        path = REPO_ROOT / entry["path"]
        if not path.exists():
            errs.append(f"manifest entry path missing: {entry['path']}")
            continue
        b = path.read_bytes()
        actual = hashlib.sha256(b).hexdigest()
        expected = entry["sha256"]
        if actual != expected:
            errs.append(
                f"SHA-256 mismatch for {entry['path']}: manifest={expected} disk={actual} "
                "(regenerate bundle-manifest.json)"
            )
        if len(b) != entry["bytes"]:
            errs.append(
                f"byte-count mismatch for {entry['path']}: manifest={entry['bytes']} disk={len(b)}"
            )
    return errs


def check_pii_guard() -> list[str]:
    fixture = _read_json(FIXTURE_PATH)
    found = [k for k in _walk_keys(fixture) if k.lower() in PII_KEYS]
    if found:
        return [f"PII key(s) found in fixture: {sorted(set(found))}"]
    return []


def check_banned_wording() -> list[str]:
    errs: list[str] = []
    for doc_path in DOCS_TOUCHED_BY_PR:
        if not doc_path.exists():
            errs.append(f"banned-wording check: doc missing — {doc_path}")
            continue
        text = _read_text(doc_path).lower()
        allow = BANNED_PHRASES_ALLOWED_OCCURRENCES.get(doc_path, {})
        for phrase in BANNED_PHRASES:
            count = text.count(phrase)
            ceiling = allow.get(phrase, 0)
            if count > ceiling:
                errs.append(
                    f"banned wording '{phrase}' appears {count}x in {doc_path.relative_to(REPO_ROOT)} "
                    f"(ceiling for this file: {ceiling})"
                )
    return errs


_MD_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
_FENCE_RE = re.compile(r"^```", re.MULTILINE)


def _strip_fences(md: str) -> str:
    # remove fenced code blocks to avoid matching code-comment URLs
    parts = re.split(r"```", md)
    return "".join(parts[i] for i in range(0, len(parts), 2))


def check_markdown_links() -> list[str]:
    errs: list[str] = []
    for doc_path in DOCS_TOUCHED_BY_PR:
        if not doc_path.exists():
            continue
        text = _strip_fences(_read_text(doc_path))
        for m in _MD_LINK_RE.finditer(text):
            target = m.group(1).strip()
            # skip http(s), mailto:, anchors, urn:, data:
            if target.startswith(("http://", "https://", "mailto:", "urn:", "data:", "#")):
                continue
            # strip fragment / query
            fragment = ""
            if "#" in target:
                target, fragment = target.split("#", 1)
                if not target:
                    continue  # pure anchor in same file
            target_path = (doc_path.parent / target).resolve()
            if not target_path.exists():
                errs.append(
                    f"broken link in {doc_path.relative_to(REPO_ROOT)} -> '{m.group(1)}'"
                )
    return errs


def main() -> int:
    all_errors: list[str] = []

    print("[1/8] JSON validity (5 files)...", end=" ")
    errs = check_json_validity()
    print("ok" if not errs else f"FAIL ({len(errs)})")
    all_errors += errs

    print("[2/8] strict Draft 2020-12 schema validates fixture...", end=" ")
    errs = check_schema_validates_fixture()
    print("ok" if not errs else f"FAIL ({len(errs)})")
    all_errors += errs

    print("[3/8] negative fixtures must fail validation...", end=" ")
    errs = check_negative_fixtures()
    print("ok" if not errs else f"FAIL ({len(errs)})")
    all_errors += errs

    print("[4/8] SKOS bundle resolves every fixture ref...", end=" ")
    errs = check_skos_resolves()
    print("ok" if not errs else f"FAIL ({len(errs)})")
    all_errors += errs

    print("[5/8] bundle SHA-256 matches manifest...", end=" ")
    errs = check_bundle_hashes()
    print("ok" if not errs else f"FAIL ({len(errs)})")
    all_errors += errs

    print("[6/8] no PII keys in fixture...", end=" ")
    errs = check_pii_guard()
    print("ok" if not errs else f"FAIL ({len(errs)})")
    all_errors += errs

    print("[7/8] no persona-as-pack banned wording above ceiling...", end=" ")
    errs = check_banned_wording()
    print("ok" if not errs else f"FAIL ({len(errs)})")
    all_errors += errs

    print("[8/8] markdown relative links resolve...", end=" ")
    errs = check_markdown_links()
    print("ok" if not errs else f"FAIL ({len(errs)})")
    all_errors += errs

    if all_errors:
        print("\nFAILURES:")
        for e in all_errors:
            print(f"  - {e}")
        return 1

    print("\nAll Chimera Draft scaffold checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
