#!/usr/bin/env python3
"""
P0-2 strict v4 schema validation runner.

Validates the .klickd v4 GA strict candidate schemas against:
  - the 5 persona examples under examples/v4/personas/
  - examples/v4-preview/minimal.klickd (unified shape only — it carries no
    payload_schema_version on purpose)
  - every expected_payload of tests/vectors_v40_preview.json (payload schema)
  - a fixed set of negative cases (each one MUST fail validation)

Exits 0 on success, 1 on any unexpected error. Intended for local use and
as a candidate CI step. Does not modify any file. No SDK is bumped, no
release is triggered. See docs/roadmap/ROAD-TO-V4-GA.md §P0-2.
"""
from __future__ import annotations

import json
import pathlib
import sys

try:
    from jsonschema import Draft202012Validator, RefResolver
except ImportError:
    print("ERROR: jsonschema not installed. pip install jsonschema", file=sys.stderr)
    sys.exit(2)

REPO = pathlib.Path(__file__).resolve().parent.parent
PAYLOAD_SCHEMA_PATH = REPO / "schemas" / "klickd-payload-v4.schema.json"
UNIFIED_SCHEMA_PATH = REPO / "schema" / "klickd-v4.schema.json"


def load_validators() -> tuple[Draft202012Validator, Draft202012Validator]:
    payload_schema = json.loads(PAYLOAD_SCHEMA_PATH.read_text())
    unified_schema = json.loads(UNIFIED_SCHEMA_PATH.read_text())
    store = {
        payload_schema["$id"]: payload_schema,
        unified_schema["$id"]: unified_schema,
    }
    resolver = RefResolver.from_schema(unified_schema, store=store)
    return (
        Draft202012Validator(payload_schema),
        Draft202012Validator(unified_schema, resolver=resolver),
    )


def report(label: str, errs: list, expect_fail: bool = False) -> int:
    ok = bool(errs) if expect_fail else not errs
    tag = "OK" if ok else "FAIL"
    print(f"[{tag}] {label} — errors={len(errs)}")
    for e in errs[:3]:
        print(f"       - {list(e.path)}: {e.message[:200]}")
    return 0 if ok else 1


def main() -> int:
    payload_validator, unified_validator = load_validators()
    failures = 0

    # 1. 5 persona examples — unified + payload validation
    for p in sorted((REPO / "examples" / "v4" / "personas").glob("*.klickd")):
        data = json.loads(p.read_text())
        failures += report(
            f"persona unified {p.name}",
            list(unified_validator.iter_errors(data)),
        )
        failures += report(
            f"persona payload  {p.name}",
            list(payload_validator.iter_errors(data)),
        )

    # 2. SPEC §33.5 minimal preview example — unified validation only
    #    (no payload_schema_version; it's an envelope-shaped illustration).
    minimal = REPO / "examples" / "v4-preview" / "minimal.klickd"
    if minimal.is_file():
        failures += report(
            f"unified {minimal.relative_to(REPO)}",
            list(unified_validator.iter_errors(json.loads(minimal.read_text()))),
        )

    # 3. Every expected_payload in vectors_v40_preview.json — payload schema
    vectors = REPO / "tests" / "vectors_v40_preview.json"
    if vectors.is_file():
        vdoc = json.loads(vectors.read_text())
        for v in vdoc.get("vectors", []):
            ep = v.get("expected_payload")
            if not ep:
                continue
            failures += report(
                f"vector  {v['id']}",
                list(payload_validator.iter_errors(ep)),
            )

    # 4. Negative cases — each MUST fail.
    negatives = [
        (
            "neg: unknown gate level",
            payload_validator,
            {
                "payload_schema_version": "4.0",
                "verification_gates": {
                    "version": 1,
                    "gates": [{"action_class": "x", "level": "loud"}],
                },
            },
        ),
        (
            "neg: media entry missing hash",
            payload_validator,
            {
                "payload_schema_version": "4.0",
                "media_profile": {
                    "version": 1,
                    "entries": [{"id": "x", "modality": "voice"}],
                },
            },
        ),
        (
            "neg: unsupported payload_schema_version",
            payload_validator,
            {"payload_schema_version": "9.9"},
        ),
        (
            "neg: encrypted=true missing kdf/cipher/ciphertext",
            unified_validator,
            {
                "klickd_version": "4.0",
                "created_at": "2026-05-24T00:00:00Z",
                "encrypted": True,
            },
        ),
        (
            "neg: media modality not in v1 enum",
            payload_validator,
            {
                "payload_schema_version": "4.0",
                "media_profile": {
                    "version": 1,
                    "entries": [
                        {
                            "id": "x",
                            "modality": "video",
                            "hash": {"algo": "blake3", "value": "xx"},
                        }
                    ],
                },
            },
        ),
    ]
    for label, validator, data in negatives:
        failures += report(
            label, list(validator.iter_errors(data)), expect_fail=True
        )

    if failures:
        print(f"\nFAILED: {failures} validation issue(s).", file=sys.stderr)
        return 1
    print("\nAll v4 strict-schema validations passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
