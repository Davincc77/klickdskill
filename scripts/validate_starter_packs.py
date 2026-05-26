#!/usr/bin/env python3
# Starter-pack validator for the four Chimera v4.1 carrier_pack scaffolds
# (x.klickd/user, x.klickd/student, x.klickd/research, x.klickd/coding).
#
# Purpose: quickly check a directory of *.json starter packs for the
# v4.1-native shape (RFC-009 §5.0/§5.1/§5.1.1/§8.1) WITHOUT pulling in
# jsonschema or any other runtime dependency. Stdlib-only, offline.
#
# What this checks per file:
#   1. UTF-8 readable + json.loads parses.
#   2. Required top-level fields are present (RFC-009 §8.1):
#         base_transversal_core, competencies, source_policy,
#         evidence_policy, verification_gates*, human_authority,
#         structured_memory*
#      (*) verification_gates is satisfied by either a top-level
#          `verification_gates` field or `gates.verification_gates_default`
#          (the shape used by the published student scaffold).
#          structured_memory is satisfied by either `structured_memory`
#          or `memory_scope` (RFC-009 §5.6 — pack-scoped memory slice).
#   3. framework_refs presence — top-level `frameworks[]` is required by
#      RFC-009 §8.1, OR `base_transversal_core.frameworks[]` carries them.
#   4. No PII / no secrets — regex scan of the full JSON text against
#      common credential / key / token / email / phone / IBAN patterns.
#   5. No forbidden carrier-vs-skill fields (RFC-009 §5.1.1): the keys
#      `host_skill`, `pedagogy`, `teaching_method`, `socratic_steps`,
#      `prompt_strategy`, `scoring_rubric`, `intervention_policy`,
#      `tone_rules`, `system_prompt`, `system_prompt_overrides` MUST NOT
#      appear as top-level keys.
#   6. If a hash manifest (bundle-manifest.json) is alongside the packs
#      OR pointed at by --manifest, verify each listed bundle file's
#      SHA-256 against the manifest entry.
#
# Behaviour:
#   - If the target directory does not exist OR contains no *.json files,
#     the script exits with code 2 and prints a clear "no packs found"
#     line. Useful before the starter packs are created (graceful fail).
#   - Otherwise exits 0 on all-pass, 1 on any failure, 2 on usage / I/O
#     errors.
#
# Usage:
#   python3 scripts/validate_starter_packs.py --dir packs/starter
#   python3 scripts/validate_starter_packs.py --dir packs/starter --manifest packs/starter/bundle-manifest.json
#   python3 scripts/validate_starter_packs.py --dir packs/starter --json  # machine-readable report
#
# This script is independent of the starter-pack files; it can be added
# to CI before any pack exists. No network calls. No release implied.

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

REQUIRED_TOP_LEVEL_FIELDS = [
    "base_transversal_core",
    "competencies",
    "source_policy",
    "evidence_policy",
    "human_authority",
]

VERIFICATION_GATES_KEYS = ("verification_gates", "gates")
STRUCTURED_MEMORY_KEYS = ("structured_memory", "memory_scope")

FORBIDDEN_TOP_LEVEL_FIELDS = {
    "host_skill",
    "pedagogy",
    "teaching_method",
    "socratic_steps",
    "prompt_strategy",
    "scoring_rubric",
    "intervention_policy",
    "tone_rules",
    "system_prompt",
    "system_prompt_overrides",
    "lesson_plan_template",
}

KNOWN_PACK_NAMES = {
    "x.klickd/user",
    "x.klickd/student",
    "x.klickd/research",
    "x.klickd/coding",
}

SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("aws_access_key_id", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("github_token", re.compile(r"gh[pousr]_[A-Za-z0-9]{30,}")),
    ("slack_token", re.compile(r"xox[abprs]-[A-Za-z0-9-]{10,}")),
    ("openai_key", re.compile(r"sk-(?:proj-)?[A-Za-z0-9_\-]{20,}")),
    ("anthropic_key", re.compile(r"sk-ant-[A-Za-z0-9_\-]{20,}")),
    ("private_key_block", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----")),
    ("bearer_token", re.compile(r"\bbearer\s+[A-Za-z0-9._\-]{20,}", re.IGNORECASE)),
    ("jwt_three_segments", re.compile(r"\beyJ[A-Za-z0-9_\-]{8,}\.eyJ[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}\b")),
    ("password_assignment", re.compile(r"\"password\"\s*:\s*\"(?!\s*\"\s*$)[^\"]{1,}\"")),
    ("secret_assignment", re.compile(r"\"(?:api[_-]?key|secret|access[_-]?token)\"\s*:\s*\"[^\"]{8,}\"", re.IGNORECASE)),
]

PII_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("email", re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,24}")),
    ("phone_e164", re.compile(r"(?<![A-Za-z0-9])\+\d{8,15}(?![A-Za-z0-9])")),
    ("iban", re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{10,30}\b")),
    ("ssn_us", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    ("credit_card_like", re.compile(r"\b(?:\d[ -]?){13,19}\b")),
]

# Some scheme/curriculum/canonical URLs contain @ (none currently, but be
# defensive) — exclude obvious framework hosts from email-pattern hits.
PII_HOST_ALLOWLIST = {
    "esco.ec.europa.eu",
    "europa.eu",
    "data.europa.eu",
    "publications.jrc.ec.europa.eu",
    "joint-research-centre.ec.europa.eu",
    "coe.int",
    "rm.coe.int",
    "klickd.app",
    "eduscol.education.fr",
    "example.com",
    "example.org",
    "example.invalid",
}


def find_pack_files(target_dir: Path) -> list[Path]:
    if not target_dir.exists() or not target_dir.is_dir():
        return []
    # Accept both .json and .klickd extensions; skip bundle manifests.
    out: list[Path] = []
    for p in sorted(target_dir.iterdir()):
        if not p.is_file():
            continue
        if p.suffix.lower() not in (".json", ".klickd"):
            continue
        if p.name == "bundle-manifest.json":
            continue
        if p.name.endswith(".bundle.json"):
            continue
        out.append(p)
    return out


def _filter_email_hits(text: str, hits: list[str]) -> list[str]:
    real: list[str] = []
    for h in hits:
        host = h.split("@", 1)[1].lower()
        if any(host == a or host.endswith("." + a) for a in PII_HOST_ALLOWLIST):
            continue
        real.append(h)
    return real


def scan_text_for_pii_and_secrets(text: str) -> list[str]:
    findings: list[str] = []
    for name, pat in SECRET_PATTERNS:
        for m in pat.findall(text):
            findings.append(f"secret:{name}:{(m[:40] + '...') if isinstance(m, str) and len(m) > 40 else m!r}")
    for name, pat in PII_PATTERNS:
        hits = pat.findall(text)
        if name == "email":
            hits = _filter_email_hits(text, hits)
        elif name == "credit_card_like":
            # Luhn check to suppress false positives like dates / IRIs.
            hits = [h for h in hits if _luhn_ok(h)]
        for h in hits:
            findings.append(f"pii:{name}:{h}")
    return findings


def _luhn_ok(candidate: str) -> bool:
    digits = [int(c) for c in candidate if c.isdigit()]
    if not (13 <= len(digits) <= 19):
        return False
    s = 0
    parity = len(digits) % 2
    for i, d in enumerate(digits):
        if i % 2 == parity:
            d *= 2
            if d > 9:
                d -= 9
        s += d
    return s % 10 == 0


def check_required_fields(data: dict[str, Any]) -> list[str]:
    errs: list[str] = []
    for field in REQUIRED_TOP_LEVEL_FIELDS:
        if field not in data:
            errs.append(f"missing required top-level field: {field}")
    if not any(k in data for k in VERIFICATION_GATES_KEYS):
        errs.append(
            "missing verification_gates: expected `verification_gates` "
            "or `gates.verification_gates_default`"
        )
    elif "gates" in data and "verification_gates" not in data:
        gates = data.get("gates")
        if not isinstance(gates, dict) or "verification_gates_default" not in gates:
            errs.append(
                "`gates` present but missing `verification_gates_default`"
            )
    if not any(k in data for k in STRUCTURED_MEMORY_KEYS):
        errs.append(
            "missing structured_memory: expected `structured_memory` "
            "or `memory_scope`"
        )
    return errs


def check_framework_refs(data: dict[str, Any]) -> list[str]:
    errs: list[str] = []
    top = data.get("frameworks")
    base = data.get("base_transversal_core")
    base_frameworks = (
        base.get("frameworks") if isinstance(base, dict) else None
    )
    if not (isinstance(top, list) and top) and not (
        isinstance(base_frameworks, list) and base_frameworks
    ):
        errs.append(
            "no framework_refs: expected non-empty top-level `frameworks[]` "
            "or `base_transversal_core.frameworks[]`"
        )
    return errs


def check_forbidden_fields(data: dict[str, Any]) -> list[str]:
    errs: list[str] = []
    for k in data.keys():
        if k in FORBIDDEN_TOP_LEVEL_FIELDS:
            errs.append(f"forbidden top-level field present: {k}")
    return errs


def check_human_authority(data: dict[str, Any]) -> list[str]:
    errs: list[str] = []
    ha = data.get("human_authority")
    if ha is None:
        return errs  # already flagged by required-fields check
    if not isinstance(ha, dict):
        errs.append("human_authority must be an object")
        return errs
    role = ha.get("agent_role")
    if role is not None and role != "advisory":
        errs.append(
            f"human_authority.agent_role must be \"advisory\" (got {role!r})"
        )
    return errs


def validate_pack_file(path: Path) -> tuple[list[str], dict[str, Any] | None]:
    try:
        raw = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        return [f"could not read: {e}"], None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        return [f"JSON parse error: {e.msg} at line {e.lineno} col {e.colno}"], None
    if not isinstance(data, dict):
        return ["top-level JSON value must be an object"], None
    errs: list[str] = []
    errs += check_required_fields(data)
    errs += check_framework_refs(data)
    errs += check_forbidden_fields(data)
    errs += check_human_authority(data)
    errs += scan_text_for_pii_and_secrets(raw)
    return errs, data


def verify_manifest(manifest_path: Path) -> list[str]:
    errs: list[str] = []
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as e:
        return [f"could not read manifest {manifest_path}: {e}"]
    bundles = manifest.get("bundles", [])
    if not isinstance(bundles, list):
        return [f"manifest {manifest_path}: `bundles` must be a list"]
    repo_root = _find_repo_root(manifest_path)
    for entry in bundles:
        if not isinstance(entry, dict):
            errs.append(f"manifest entry not an object: {entry!r}")
            continue
        rel = entry.get("path")
        expect = entry.get("sha256")
        if not rel or not expect:
            errs.append(f"manifest entry missing path or sha256: {entry!r}")
            continue
        # Resolve path: first try relative to repo root, then to manifest dir.
        candidates = [repo_root / rel, manifest_path.parent / rel, Path(rel)]
        bundle_path = next((c for c in candidates if c.exists()), None)
        if bundle_path is None:
            errs.append(f"manifest path not found on disk: {rel}")
            continue
        try:
            actual = hashlib.sha256(bundle_path.read_bytes()).hexdigest()
        except OSError as e:
            errs.append(f"could not read bundle {bundle_path}: {e}")
            continue
        if actual != expect:
            errs.append(
                f"sha256 mismatch for {rel}: manifest={expect} actual={actual}"
            )
    return errs


def _find_repo_root(start: Path) -> Path:
    p = start.resolve()
    for parent in [p, *p.parents]:
        if (parent / ".git").exists():
            return parent
    return start.parent


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Validate Chimera v4.1 starter packs in a directory.",
    )
    ap.add_argument(
        "--dir",
        default="packs/starter",
        help="Directory containing starter-pack JSON files (default: packs/starter)",
    )
    ap.add_argument(
        "--manifest",
        default=None,
        help="Optional path to a bundle-manifest.json to hash-verify",
    )
    ap.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON report on stdout instead of text",
    )
    ap.add_argument(
        "--require-known-pack-name",
        action="store_true",
        help=(
            "Fail if a pack's `pack` field is not one of "
            "x.klickd/{user,student,research,coding}"
        ),
    )
    args = ap.parse_args(argv)

    target = Path(args.dir)
    pack_files = find_pack_files(target)

    report: dict[str, Any] = {
        "dir": str(target),
        "files": [],
        "manifest": None,
        "summary": {"checked": 0, "passed": 0, "failed": 0},
    }

    if not pack_files:
        msg = (
            f"no pack files found in {target} "
            f"(directory exists={target.exists()}). Nothing to validate."
        )
        if args.json:
            report["error"] = msg
            print(json.dumps(report, indent=2))
        else:
            print(msg, file=sys.stderr)
        return 2

    any_failed = False
    for f in pack_files:
        errs, data = validate_pack_file(f)
        if args.require_known_pack_name and data is not None:
            name = data.get("pack")
            if name not in KNOWN_PACK_NAMES:
                errs.append(
                    f"pack name {name!r} not in known set {sorted(KNOWN_PACK_NAMES)}"
                )
        entry = {"path": str(f), "ok": not errs, "errors": errs}
        report["files"].append(entry)
        report["summary"]["checked"] += 1
        if errs:
            report["summary"]["failed"] += 1
            any_failed = True
        else:
            report["summary"]["passed"] += 1

    if args.manifest:
        mpath = Path(args.manifest)
        merrs = verify_manifest(mpath)
        report["manifest"] = {"path": str(mpath), "ok": not merrs, "errors": merrs}
        if merrs:
            any_failed = True

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        for entry in report["files"]:
            tag = "OK" if entry["ok"] else "FAIL"
            print(f"[{tag}] {entry['path']}")
            for e in entry["errors"]:
                print(f"       - {e}")
        if report["manifest"] is not None:
            m = report["manifest"]
            tag = "OK" if m["ok"] else "FAIL"
            print(f"[{tag}] manifest {m['path']}")
            for e in m["errors"]:
                print(f"       - {e}")
        s = report["summary"]
        print(
            f"summary: checked={s['checked']} passed={s['passed']} "
            f"failed={s['failed']}"
        )

    return 1 if any_failed else 0


if __name__ == "__main__":
    sys.exit(main())
