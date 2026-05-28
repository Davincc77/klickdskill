#!/usr/bin/env python3
"""Recompute SHA-256 + bytes for every x.klickd v4.1 candidate artefact
and rewrite the two per-tier manifests and the root download index.

Idempotent. NON-NORMATIVE. Run after any change to the artefacts under
examples/v4.1/x-klickd-skills/{lite,pro}/.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ART_ROOT = REPO_ROOT / "examples" / "v4.1" / "x-klickd-skills"
LITE = ART_ROOT / "lite"
PRO = ART_ROOT / "pro"


def _sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _canonical_json_sha256(obj) -> str:
    canon = json.dumps(
        obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return _sha256_bytes(canon)


def update_tier_manifest(tier_dir: Path) -> int:
    mpath = tier_dir / "manifest.json"
    m = json.loads(mpath.read_text(encoding="utf-8"))
    by_file = {p["file"]: p for p in m["packs"]}
    actual = sorted(p.name for p in tier_dir.glob("*.klickd"))
    if sorted(by_file) != actual:
        print(
            f"ERROR: manifest files {sorted(by_file)} != "
            f"directory {actual}",
            file=sys.stderr,
        )
        return 1
    for path in tier_dir.glob("*.klickd"):
        raw = path.read_bytes()
        obj = json.loads(raw.decode("utf-8"))
        entry = by_file[path.name]
        entry["bytes"] = len(raw)
        entry["sha256_file"] = _sha256_bytes(raw)
        if "sha256_canonical_json" in entry:
            entry["sha256_canonical_json"] = _canonical_json_sha256(obj)
    mpath.write_text(
        json.dumps(m, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return 0


def update_root_manifest() -> int:
    mpath = ART_ROOT / "manifest.json"
    m = json.loads(mpath.read_text(encoding="utf-8"))
    by_file = {p["file"]: p for p in m["packs"]}
    for tier_dir in (LITE, PRO):
        for path in tier_dir.glob("*.klickd"):
            if path.name not in by_file:
                print(
                    f"ERROR: root manifest missing entry for {path.name}",
                    file=sys.stderr,
                )
                return 1
            raw = path.read_bytes()
            entry = by_file[path.name]
            entry["bytes"] = len(raw)
            entry["sha256_file"] = _sha256_bytes(raw)
    mpath.write_text(
        json.dumps(m, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return 0


def main(argv: list[str]) -> int:
    rc = update_tier_manifest(LITE)
    rc |= update_tier_manifest(PRO)
    rc |= update_root_manifest()
    if rc == 0:
        print("OK: manifests updated (lite, pro, root).")
    return rc


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
