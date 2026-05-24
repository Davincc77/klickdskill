# .klickd v4 — strict / preview JSON-Schema validation
# SPDX-License-Identifier: CC0-1.0
#
# P0-3 (SDK Python V4 GA alignment): exposes `validate(payload, strict=...)`
# against the bundled v4 schemas:
#
#   - `klickd-payload-v4.schema.json`         (strict GA candidate, P0-2)
#   - `klickd-payload-v4-preview.schema.json` (permissive v4 preview)
#   - `klickd-v4.schema.json`                 (unified strict GA)
#   - `klickd-v4-preview.schema.json`         (unified preview)
#
# Validation is OPTIONAL: `jsonschema` is not a hard dependency. Callers
# who do not invoke `validate()` continue to work with only the v3 envelope
# crypto deps. Round-trip preservation (SPEC.md §33.7) is the canonical
# forward-compat contract — validation does not modify the payload.

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

from .errors import KlickdError, KlickdErrorCode

# Map a schema target onto its bundled file. The "unified" targets validate
# the full envelope shape (klickd_version, encrypted, kdf, cipher, ...).
# The "payload" targets validate the decrypted inner payload only.
_SCHEMA_FILES: Dict[str, str] = {
    "payload-strict": "klickd-payload-v4.schema.json",
    "payload-preview": "klickd-payload-v4-preview.schema.json",
    "unified-strict": "klickd-v4.schema.json",
    "unified-preview": "klickd-v4-preview.schema.json",
}

_SCHEMA_DIR = Path(__file__).resolve().parent / "schemas"


def _load_schema(name: str) -> dict:
    fname = _SCHEMA_FILES.get(name)
    if not fname:
        raise ValueError(f"Unknown schema target: {name!r}")
    path = _SCHEMA_DIR / fname
    return json.loads(path.read_text(encoding="utf-8"))


def _require_jsonschema():
    try:
        import jsonschema  # noqa: F401
        from jsonschema import Draft202012Validator
    except ImportError as exc:
        raise KlickdError(
            KlickdErrorCode.FORMAT,
            "validate() requires the optional 'jsonschema' dependency. "
            "Install it with: pip install jsonschema",
        ) from exc
    return Draft202012Validator


def _build_validator(name: str):
    """Build a Draft 2020-12 validator with the companion schema registered
    so cross-schema $refs (unified ↔ payload) resolve locally and never
    trigger a network fetch."""
    Draft202012Validator = _require_jsonschema()
    schema = _load_schema(name)

    # Build a registry that includes the companion schema of the requested
    # target. We bundle four schemas; for any unified-* target the payload-*
    # schema MAY be $ref'd, and vice versa.
    try:
        from referencing import Registry, Resource
        from referencing.jsonschema import DRAFT202012
    except ImportError:
        # Older jsonschema/referencing: fall back to no registry. The
        # bundled strict schemas embed their refs by $id and modern
        # jsonschema resolves them via the deprecated RefResolver path
        # (we accept the deprecation warning).
        return Draft202012Validator(schema)

    resources = []
    for key in _SCHEMA_FILES:
        s = _load_schema(key)
        if "$id" in s:
            resources.append((s["$id"], Resource(contents=s, specification=DRAFT202012)))

    registry = Registry().with_resources(resources)
    return Draft202012Validator(schema, registry=registry)


def validate(
    payload: Dict[str, Any],
    strict: bool = True,
    target: str = "payload",
) -> None:
    """
    Validate a .klickd payload (or unified envelope+payload) against the v4
    JSON schema bundled with this SDK.

    Args:
        payload: The decrypted payload dict (or unified envelope dict if
                 ``target="unified"``).
        strict:  ``True`` (default) uses the v4 GA strict schema candidate
                 (RFC-001 v1, RFC-002 v1 core, RFC-004 v1 frozen surface).
                 ``False`` uses the permissive v4 preview schema.
        target:  ``"payload"`` (default) validates the inner payload schema.
                 ``"unified"`` validates against the unified envelope+payload
                 schema (use this when the dict carries envelope fields like
                 ``klickd_version`` / ``encrypted``).

    Raises:
        KlickdError: ``KLICKD_E_SCHEMA`` if validation fails or if
                     ``jsonschema`` is not installed. The exception's
                     ``args[0]`` includes the list of validation errors,
                     truncated to the first 8 messages.
    """
    if target not in ("payload", "unified"):
        raise ValueError(f"target must be 'payload' or 'unified', got {target!r}")

    key = f"{target}-{'strict' if strict else 'preview'}"
    validator = _build_validator(key)
    errors = sorted(validator.iter_errors(payload), key=lambda e: list(e.path))

    if not errors:
        return

    summary: List[str] = []
    for err in errors[:8]:
        path = "/".join(str(p) for p in err.absolute_path) or "<root>"
        summary.append(f"{path}: {err.message[:200]}")
    extra = "" if len(errors) <= 8 else f" (+{len(errors) - 8} more)"
    raise KlickdError(
        KlickdErrorCode.SCHEMA,
        f"v4 {'strict' if strict else 'preview'} {target} validation failed{extra}: "
        + " | ".join(summary),
    )


def validate_iter_errors(
    payload: Dict[str, Any],
    strict: bool = True,
    target: str = "payload",
) -> List[Tuple[str, str]]:
    """
    Non-raising variant of :func:`validate`. Returns a list of
    ``(path, message)`` tuples — empty when the payload is valid.

    Useful when a writer wants to surface all validation issues at once
    (e.g. the R4-P0-1 wizard's reload-verification step) instead of
    failing fast on the first one.
    """
    if target not in ("payload", "unified"):
        raise ValueError(f"target must be 'payload' or 'unified', got {target!r}")

    key = f"{target}-{'strict' if strict else 'preview'}"
    validator = _build_validator(key)
    out: List[Tuple[str, str]] = []
    for err in sorted(validator.iter_errors(payload), key=lambda e: list(e.path)):
        path = "/".join(str(p) for p in err.absolute_path) or "<root>"
        out.append((path, err.message))
    return out
