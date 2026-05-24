# .klickd v3.x → v4 GA payload migrator
# SPDX-License-Identifier: CC0-1.0
#
# Implements the R4-P0-5 normative migrator contract documented at
# docs/spec/MIGRATION_V3_TO_V4.md. Pure / non-destructive / idempotent.
#
# - Input:  a decrypted .klickd payload dict (v3.x or already-v4).
# - Output: a NEW dict where payload_schema_version=="4.0", profile_kind
#           defaults to "learner", and a migration{} block records the
#           source version + timestamp. Every other v3 field is
#           preserved verbatim (SPEC.md §33.7).
#
# The migrator MUST NOT touch the encrypted envelope (klickd_version,
# kdf, cipher, ciphertext, created_at, domain, encrypted) and MUST NOT
# invent new safety surface (verification_gates, human_veto_policy,
# claim_sources, media_profile, …). Those blocks are caller-authored.

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from .errors import KlickdError, KlickdErrorCode

# Recognized source payload schema versions. Absent / unknown values fall
# back to "3.x" so the migration block always records something useful.
_V3_SCHEMA_VERSIONS = frozenset({"3.0", "3.1", "3.2", "3.3", "3.4", "3.5"})
_V4_SCHEMA_VERSIONS = frozenset({"4.0", "4.0.0-preview.1"})

# Reserved profile_kind discriminator values per
# schemas/klickd-payload-v4.schema.json#/properties/profile_kind.
_RESERVED_PROFILE_KINDS = frozenset({"learner", "agent", "team", "robot", "creator"})


def _utc_now_iso() -> str:
    """Return now() as RFC 3339 UTC with a trailing Z (matches the v4 GA
    schema pattern for migration.migrated_at)."""
    # datetime.isoformat() emits "+00:00"; the v4 schema requires "Z".
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def needs_migration(payload: Any) -> bool:
    """Return True iff ``payload`` is a v3.x payload that should be lifted
    to v4 GA.

    A payload is considered to need migration when it is a dict and
    either:
      * carries no ``payload_schema_version`` at all (pre-v3.4 files
        sometimes omit it); or
      * carries a v3.x ``payload_schema_version`` (``"3.0"`` ..
        ``"3.5"``).

    Payloads that already advertise a v4 ``payload_schema_version`` are
    not re-migrated.
    """
    if not isinstance(payload, dict):
        return False
    ver = payload.get("payload_schema_version")
    if ver is None:
        return True
    if not isinstance(ver, str):
        return False
    if ver in _V4_SCHEMA_VERSIONS:
        return False
    if ver in _V3_SCHEMA_VERSIONS:
        return True
    # Unknown value: do not auto-migrate; surface as an error from
    # migrate_payload() so the caller can route it explicitly.
    return False


def migrate_payload(
    payload: Dict[str, Any],
    *,
    source_version: Optional[str] = None,
    migrated_at: Optional[str] = None,
    profile_kind: str = "learner",
    migration_report_ref: Optional[str] = None,
    backup_ref: Optional[str] = None,
) -> Dict[str, Any]:
    """Lift a v3.x .klickd payload to the v4 GA payload shape.

    Pure function: ``payload`` is never mutated; a deep-copied result is
    returned. Idempotent: calling ``migrate_payload`` on an already-v4
    payload returns it unchanged (modulo an optional refresh of the
    ``migration`` block when the caller explicitly supplies pointer
    refs).

    Args:
        payload: Decrypted v3.x or v4 payload dict.
        source_version: Optional override for the recorded source
            version. Defaults to the input's ``payload_schema_version``
            (or ``"3.x"`` when absent).
        migrated_at: Optional RFC 3339 UTC timestamp. Defaults to
            ``now()``. Callers SHOULD pin this in tests for
            reproducibility.
        profile_kind: Default ``"learner"`` (v3.x is implicitly
            "learner"). MUST be one of the v4 reserved values
            (``learner``, ``agent``, ``team``, ``robot``, ``creator``)
            or a custom extension string.
        migration_report_ref: Optional pointer (URI / path) to a
            human-authored migration report. Recorded verbatim in
            ``migration.migration_report_ref``.
        backup_ref: Optional pointer to a backup of the pre-migration
            file. Recorded verbatim in ``migration.backup_ref``.

    Returns:
        A new dict containing the migrated payload.

    Raises:
        KlickdError: ``KLICKD_E_SCHEMA`` when ``payload`` is not a dict
            or carries a ``payload_schema_version`` the migrator does
            not recognize (neither v3.x nor v4).
    """
    if not isinstance(payload, dict):
        raise KlickdError(
            KlickdErrorCode.SCHEMA,
            "migrate_payload requires a dict payload; got "
            f"{type(payload).__name__}",
        )

    incoming_version = payload.get("payload_schema_version")
    if (
        incoming_version is not None
        and incoming_version not in _V3_SCHEMA_VERSIONS
        and incoming_version not in _V4_SCHEMA_VERSIONS
    ):
        raise KlickdError(
            KlickdErrorCode.SCHEMA,
            "migrate_payload does not recognize payload_schema_version="
            f"{incoming_version!r}; expected v3.x (3.0..3.5) or v4 "
            "(4.0 / 4.0.0-preview.1)",
        )

    # Deep-copy so unknown nested structures are preserved without
    # surprising the caller via shared references.
    out: Dict[str, Any] = deepcopy(payload)

    # R8 — already-v4 payloads round-trip unchanged unless the caller
    # explicitly passes pointer refs (which we splice into the existing
    # migration block, creating it if absent).
    if incoming_version in _V4_SCHEMA_VERSIONS:
        if migration_report_ref is None and backup_ref is None:
            return out
        existing = out.get("migration")
        if not isinstance(existing, dict):
            existing = {}
        if migration_report_ref is not None:
            existing["migration_report_ref"] = migration_report_ref
        if backup_ref is not None:
            existing["backup_ref"] = backup_ref
        # Always record migrated_at on a manual refresh so the trail is
        # monotonic; the caller can still pin it via the kwarg.
        existing.setdefault("source_version", incoming_version)
        existing["migrated_at"] = migrated_at or _utc_now_iso()
        out["migration"] = existing
        return out

    # R1 — stamp the payload version to the GA canonical value.
    out["payload_schema_version"] = "4.0"

    # R2 — default profile_kind to "learner" when absent. Caller-supplied
    # values win.
    if "profile_kind" not in out:
        out["profile_kind"] = profile_kind

    # R4 — record the migration provenance block. Only the v1 frozen
    # fields are emitted; extension fields are reserved for future
    # callers via the `migration` permissive surface.
    migration_block: Dict[str, Any] = {
        "source_version": source_version or incoming_version or "3.x",
        "migrated_at": migrated_at or _utc_now_iso(),
    }
    if migration_report_ref is not None:
        migration_block["migration_report_ref"] = migration_report_ref
    if backup_ref is not None:
        migration_block["backup_ref"] = backup_ref
    out["migration"] = migration_block

    # R3, R5–R7, R9, R10 — every other field is preserved verbatim by
    # virtue of the deepcopy. No further work required.
    return out


def migrate_payload_iter_warnings(payload: Any) -> List[Tuple[str, str]]:
    """Return manual-review warnings for ``payload`` without mutating it.

    Each warning is a ``(json_pointer_path, message)`` tuple. An empty
    list means the migrator can run unattended.

    Surfaces the conditions enumerated in
    docs/spec/MIGRATION_V3_TO_V4.md §3.5.
    """
    warnings: List[Tuple[str, str]] = []
    if not isinstance(payload, dict):
        warnings.append(("<root>", "payload is not a JSON object"))
        return warnings

    ver = payload.get("payload_schema_version")
    if ver is None:
        # Pre-v3.4 files commonly omit it; surface as a warning so the
        # caller can decide whether to pin source_version explicitly.
        if "domain_schema_version" not in payload:
            warnings.append(
                (
                    "<root>",
                    "no payload_schema_version and no domain_schema_version; "
                    "pin source_version explicitly when migrating",
                )
            )
    elif isinstance(ver, str) and ver not in _V3_SCHEMA_VERSIONS and ver not in _V4_SCHEMA_VERSIONS:
        warnings.append(
            (
                "/payload_schema_version",
                f"unknown payload_schema_version {ver!r}; migrator will refuse",
            )
        )

    ctx = payload.get("context")
    if isinstance(ctx, dict):
        decisions = ctx.get("decisions_locked")
        if isinstance(decisions, list):
            for i, d in enumerate(decisions):
                if isinstance(d, str) and len(d) > 1024:
                    warnings.append(
                        (
                            f"/context/decisions_locked/{i}",
                            f"entry exceeds 1024 chars ({len(d)}); some readers will truncate",
                        )
                    )

    ethics = payload.get("ethics")
    veto = payload.get("human_veto_policy")
    if isinstance(ethics, dict) and isinstance(veto, dict):
        locked = ethics.get("locked_actions")
        applies_to = veto.get("applies_to")
        if isinstance(locked, list) and isinstance(applies_to, list):
            overlap = sorted(set(locked) & set(applies_to))
            if overlap:
                warnings.append(
                    (
                        "/human_veto_policy/applies_to",
                        "overlaps with /ethics/locked_actions: "
                        + ", ".join(repr(x) for x in overlap),
                    )
                )

    if isinstance(payload.get("profile_kind"), str):
        pk = payload["profile_kind"]
        if pk not in _RESERVED_PROFILE_KINDS:
            warnings.append(
                (
                    "/profile_kind",
                    f"non-reserved profile_kind {pk!r}; readers MAY treat as extension",
                )
            )

    return warnings


__all__ = [
    "needs_migration",
    "migrate_payload",
    "migrate_payload_iter_warnings",
]
