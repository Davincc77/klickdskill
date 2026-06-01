# klickd — x.klickd v4.1 skill-pack helper
# SPDX-License-Identifier: CC0-1.0
#
# The 42 x.klickd v4.1 candidate skill packs (8 Lite + 34 Pro) ship as
# package data under klickd/x_klickd_skills/, alongside the aggregated
# download index manifest.json. They are NON-NORMATIVE and NOT a v4.1 GA
# release (see examples/v4.1/x-klickd-skills/README.md in the source repo).
#
# These are JSON `.klickd` artifacts, not native skills in any assistant.
# A pack is only "used" once its bytes have been loaded and hash-verified
# against the manifest (or a host runtime has otherwise integrated it).
# load_xklickd_skill_pack() returns {"artifact_loaded": True, ...} only after
# that load + SHA-256 step has completed in-process.

from __future__ import annotations

import hashlib
import json
from importlib import resources
from importlib.resources.abc import Traversable
from typing import Any


_RESOURCE_PKG = "klickd.x_klickd_skills"


def _root() -> Traversable:
    return resources.files(_RESOURCE_PKG)


def get_xklickd_skills_dir() -> str:
    """Return the filesystem path to the bundled x.klickd skill-pack directory."""
    return str(_root())


def get_xklickd_skills_manifest() -> dict[str, Any]:
    """Return the bundled manifest.json (the 42-pack download index) as a dict."""
    raw = _root().joinpath("manifest.json").read_text(encoding="utf-8")
    return json.loads(raw)


def list_xklickd_skill_packs() -> list[dict[str, Any]]:
    """Return the 42 manifest pack entries (tier, pack id, file, bytes, sha256)."""
    return get_xklickd_skills_manifest()["packs"]


def _manifest_entry_for(name: str) -> dict[str, Any] | None:
    needle = name.strip()
    norm = needle[:-7] if needle.endswith(".klickd") else needle
    for pack in list_xklickd_skill_packs():
        if pack["file"] == needle or pack["pack"] == needle:
            return pack
        bare_pack = pack["pack"].split("/")[-1]
        bare_file = pack["file"][:-7] if pack["file"].endswith(".klickd") else pack["file"]
        if norm in (bare_pack, bare_file):
            return pack
        if bare_pack == norm.replace("-", "_") or bare_file == norm.replace("_", "-"):
            return pack
    return None


def get_xklickd_skill_pack_bytes(name: str) -> bytes:
    """Return raw bytes of a bundled pack by file name, full pack id, or bare id."""
    entry = _manifest_entry_for(name)
    if entry is None:
        raise ValueError(
            f"unknown x.klickd skill pack: {name!r} "
            "(see list_xklickd_skill_packs())"
        )
    file = entry["file"]
    if "/" in file or "\\" in file or ".." in file:
        raise ValueError(f"invalid x.klickd skill pack file: {file!r}")
    return _root().joinpath(file).read_bytes()


def load_xklickd_skill_pack(name: str) -> dict[str, Any]:
    """Load a pack, hash-verify it against the manifest, and return a summary.

    The returned ``artifact_loaded: True`` asserts only that the bytes were
    read and hashed in-process — it does NOT mean any AI assistant has
    natively adopted the pack. Always check ``sha256_matches_manifest``.
    """
    entry = _manifest_entry_for(name)
    if entry is None:
        raise ValueError(
            f"unknown x.klickd skill pack: {name!r} "
            "(see list_xklickd_skill_packs())"
        )
    data = get_xklickd_skill_pack_bytes(entry["file"])
    sha256 = hashlib.sha256(data).hexdigest()
    payload = json.loads(data.decode("utf-8"))
    pack = payload.get("x_klickd_pack") or {}
    compact = pack.get("compact_index") or {}

    competency_ids = compact.get("competency_ids")
    if not isinstance(competency_ids, list):
        competency_ids = [
            c.get("competency_ref")
            for c in pack.get("competencies", [])
            if isinstance(c, dict) and c.get("competency_ref")
        ]

    vgates = pack.get("verification_gates")
    if isinstance(vgates, dict) and isinstance(vgates.get("gates"), list):
        gates = vgates["gates"]
    else:
        gates = compact.get("gate_summaries", []) if isinstance(compact, dict) else []

    return {
        "artifact_loaded": True,
        "id": entry["pack"],
        "tier": entry.get("tier"),
        "file": entry["file"],
        "pack": pack.get("pack"),
        "pack_version": pack.get("pack_version"),
        "bytes": len(data),
        "sha256": sha256,
        "sha256_matches_manifest": sha256 == entry["sha256_file"],
        "klickd_version": payload.get("klickd_version"),
        "payload_schema_version": payload.get("payload_schema_version"),
        "domain": payload.get("domain"),
        "profile_kind": payload.get("profile_kind"),
        "competency_ids": competency_ids,
        "gates": gates,
        "evidence_policy": pack.get("evidence_policy"),
        "human_authority": pack.get("human_authority"),
        "human_veto": pack.get("human_veto"),
    }
