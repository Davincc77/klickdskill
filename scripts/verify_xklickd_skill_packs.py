#!/usr/bin/env python3
"""Offline verifier + CLI for the 42 x.klickd v4.1 candidate skill packs.

Source of truth: examples/v4.1/x-klickd-skills/ (8 Lite + 34 Pro `.klickd`
artifacts and the aggregated download index manifest.json).

These are NON-NORMATIVE JSON artifacts and NOT a v4.1 GA release. They are
not native skills in any AI assistant. A pack is only "used" once its bytes
have been loaded and hash-verified against the manifest (or a host runtime has
otherwise explicitly integrated it). See
examples/v4.1/x-klickd-skills/README.md and
docs/integrations/skill-loader-protocol.md.

Checks performed by `verify` (the default):

  1. Manifest reports 42 packs total: 8 Lite, 34 Pro; counts agree.
  2. Every `.klickd` parses as JSON.
  3. Required top-level fields present: klickd_version, payload_schema_version,
     domain, profile_kind, x_klickd_pack.
  4. x_klickd_pack.pack is present (and matches the manifest entry).
  5. SHA-256 of the file bytes matches manifest.json (and byte length matches).

Exit code 0 = all checks pass. Non-zero = at least one check failed.

No network. No provider calls. No paid resources.

CLI (no external dependencies; reads the public artifacts directly):

  python scripts/verify_xklickd_skill_packs.py verify          # full check (default)
  python scripts/verify_xklickd_skill_packs.py list            # list 42 packs
  python scripts/verify_xklickd_skill_packs.py load <id>       # load + hash-verify one pack
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
PACK_DIR = REPO_ROOT / "examples" / "v4.1" / "x-klickd-skills"
MANIFEST_PATH = PACK_DIR / "manifest.json"

REQUIRED_TOP_LEVEL = (
    "klickd_version",
    "payload_schema_version",
    "domain",
    "profile_kind",
    "x_klickd_pack",
)


def _load_manifest() -> dict[str, Any]:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def _pack_path(entry: dict[str, Any]) -> Path:
    # relative_path is repo-root-relative; fall back to tier/file.
    rel = entry.get("relative_path")
    if rel:
        return REPO_ROOT / rel
    return PACK_DIR / entry["tier"] / entry["file"]


def _find_entry(manifest: dict[str, Any], name: str) -> dict[str, Any] | None:
    needle = name.strip()
    norm = needle[:-7] if needle.endswith(".klickd") else needle
    for entry in manifest["packs"]:
        if entry["file"] == needle or entry["pack"] == needle:
            return entry
        bare_pack = entry["pack"].split("/")[-1]
        bare_file = entry["file"][:-7] if entry["file"].endswith(".klickd") else entry["file"]
        if norm in (bare_pack, bare_file):
            return entry
        if bare_pack == norm.replace("-", "_") or bare_file == norm.replace("_", "-"):
            return entry
    return None


def cmd_verify() -> int:
    failures: list[str] = []
    manifest = _load_manifest()
    packs = manifest.get("packs", [])

    if manifest.get("total_count") != 42 or len(packs) != 42:
        failures.append(
            f"expected total_count 42 and 42 entries, got "
            f"{manifest.get('total_count')} / {len(packs)}"
        )

    lite = [p for p in packs if p.get("tier") == "lite"]
    pro = [p for p in packs if p.get("tier") == "pro"]
    if len(lite) != 8:
        failures.append(f"expected 8 Lite packs, got {len(lite)}")
    if len(pro) != 34:
        failures.append(f"expected 34 Pro packs, got {len(pro)}")

    for entry in packs:
        path = _pack_path(entry)
        label = entry.get("file", "<unknown>")
        if not path.exists():
            failures.append(f"{label}: missing file at {path}")
            continue
        data = path.read_bytes()

        try:
            payload = json.loads(data.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            failures.append(f"{label}: not valid JSON ({exc})")
            continue

        for field in REQUIRED_TOP_LEVEL:
            if field not in payload:
                failures.append(f"{label}: missing required field {field!r}")

        pack = payload.get("x_klickd_pack")
        if not isinstance(pack, dict) or not pack.get("pack"):
            failures.append(f"{label}: x_klickd_pack.pack missing")
        elif pack["pack"] != entry["pack"]:
            failures.append(
                f"{label}: x_klickd_pack.pack {pack['pack']!r} != manifest "
                f"{entry['pack']!r}"
            )

        sha = hashlib.sha256(data).hexdigest()
        if sha != entry.get("sha256_file"):
            failures.append(
                f"{label}: sha256 {sha} != manifest {entry.get('sha256_file')}"
            )
        if len(data) != entry.get("bytes"):
            failures.append(
                f"{label}: byte length {len(data)} != manifest {entry.get('bytes')}"
            )

    if failures:
        print(f"FAIL: {len(failures)} problem(s) found:")
        for f in failures:
            print(f"  - {f}")
        return 1

    print(f"OK: 42 x.klickd v4.1 skill packs verified ({len(lite)} Lite, {len(pro)} Pro).")
    print("All parse as JSON, carry required fields, and hash-match the manifest.")
    return 0


def cmd_list() -> int:
    manifest = _load_manifest()
    for entry in manifest["packs"]:
        print(f"{entry['tier']:<5} {entry['pack']:<45} {entry['file']}")
    return 0


def _summary(manifest: dict[str, Any], entry: dict[str, Any]) -> dict[str, Any]:
    path = _pack_path(entry)
    data = path.read_bytes()
    sha = hashlib.sha256(data).hexdigest()
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
        "sha256": sha,
        "sha256_matches_manifest": sha == entry.get("sha256_file"),
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


def cmd_load(name: str) -> int:
    manifest = _load_manifest()
    entry = _find_entry(manifest, name)
    if entry is None:
        print(f"unknown x.klickd skill pack: {name!r} (try `list`)", file=sys.stderr)
        return 2
    print(json.dumps(_summary(manifest, entry), indent=2))
    return 0


def main(argv: list[str]) -> int:
    args = argv[1:]
    cmd = args[0] if args else "verify"
    if cmd == "verify":
        return cmd_verify()
    if cmd == "list":
        return cmd_list()
    if cmd == "load":
        if len(args) < 2:
            print("usage: load <id|filename|pack>", file=sys.stderr)
            return 2
        return cmd_load(args[1])
    print(f"unknown command: {cmd!r} (verify|list|load)", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
