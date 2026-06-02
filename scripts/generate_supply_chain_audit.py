#!/usr/bin/env python3
"""Generate the x.klickd supply-chain audit-trail index + determinism record.

This is the FIRST real (tool-backed) automation stage of the supply-chain
protocol described in the supply-chain RFC under docs/rfcs/ (docs-only spec PR,
not merged) and summarised in .internal-skills/supply-chain/audit/README.md. It
does NOT automate the full pipeline. It turns two traceability elements from
spec into artefacts that are actually produced, hashed, and re-checkable:

  1. audit_trail_index.json    -- a consultable index of the verifiable
                                  artifacts the supply chain operates on, the
                                  validation commands run against them, and an
                                  append-style event list.
  2. determinism_record.json   -- input file hashes, output file hashes, and a
                                  deterministic_run_id derived only from inputs,
                                  so two runs over identical inputs produce an
                                  identical id (timestamps are quarantined in a
                                  documented non-deterministic zone and are NOT
                                  part of the hash).

Inputs are the 42 NON-NORMATIVE x.klickd v4.1 candidate skill packs and their
manifest under examples/v4.1/x-klickd-skills/. A pack is only treated as a real
artifact here because its bytes exist on disk and hash-match the manifest --
the same loaded + sha256_matches_manifest gate enforced by
scripts/verify_xklickd_skill_packs.py. A catalogue entry alone is NOT a loaded
skill.

Stdlib-only. Offline. No network, no provider calls, no paid resources. No
release, tag, merge, publish, or deploy. Does not touch the private repo.

CLI:

  python scripts/generate_supply_chain_audit.py            # write artefacts
  python scripts/generate_supply_chain_audit.py generate   # (explicit) write
  python scripts/generate_supply_chain_audit.py check       # verify on-disk
                                                            #   artefacts are
                                                            #   in sync; no write

Exit codes:
  0  success (write succeeded, or check found no drift)
  1  a critical invariant failed (missing/changed input, hash mismatch,
     banned claim, obvious secret/PII), or `check` found drift
  2  usage / I-O error
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
PACK_DIR = REPO_ROOT / "examples" / "v4.1" / "x-klickd-skills"
MANIFEST_PATH = PACK_DIR / "manifest.json"

AUDIT_DIR = REPO_ROOT / ".internal-skills" / "supply-chain" / "audit"
AUDIT_INDEX_PATH = AUDIT_DIR / "audit_trail_index.json"
DETERMINISM_PATH = AUDIT_DIR / "determinism_record.json"

SCHEMA_VERSION = "0.1.0"
REPO_NAME = "Davincc77/klickdskill"

# Validation commands this stage records as the supply-chain's current
# tool-backed checks. They are recorded as declared commands; this generator
# does not silently run them (anti-mirage: the operator runs and audits them).
VALIDATION_COMMANDS = [
    "python scripts/verify_xklickd_skill_packs.py verify",
    "python scripts/validate_v4_1_candidate_mapping.py",
    "pytest tests/test_supply_chain_audit.py",
]

# Substrings that must never appear in the generated public-facing artefacts.
# Two classes: internal codename leak, and banned unbounded public claims.
BANNED_SUBSTRINGS = (
    "chimera",
    "universal standard",
    "automatic gdpr",
    "automatic eu ai act",
    "benchmark superiority",
    "proven benchmark",
)

# Coarse secret / PII signatures. This is a tripwire on our OWN generated
# output, not a general scanner -- the inputs are public artifacts, but we
# refuse to emit anything that looks like a credential or personal contact.
_SECRET_PATTERNS = (
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bghp_[A-Za-z0-9]{36}\b"),
    re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
)


class InvariantError(RuntimeError):
    """Raised when a critical supply-chain invariant fails."""


def _rel(path: Path) -> str:
    """Repo-relative path when possible, else the bare name.

    The bare-name fallback keeps the output stable and the record self-describing
    when artefacts are written outside the repo (e.g. a temp dir under test).
    """
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return path.name


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _load_manifest() -> dict[str, Any]:
    if not MANIFEST_PATH.exists():
        raise InvariantError(f"manifest not found at {MANIFEST_PATH}")
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def _pack_path(entry: dict[str, Any]) -> Path:
    rel = entry.get("relative_path")
    if rel:
        return REPO_ROOT / rel
    return PACK_DIR / entry["tier"] / entry["file"]


def _git_commit_sha() -> str | None:
    """Best-effort source commit, read from .git without invoking git.

    Returns None when not in a usable git checkout (the artefact then records
    null rather than a guessed value -- never fabricate provenance).
    """
    head = REPO_ROOT / ".git" / "HEAD"
    if not head.exists():
        return None
    try:
        ref = head.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    if ref.startswith("ref:"):
        ref_path = REPO_ROOT / ".git" / ref.split(" ", 1)[1].strip()
        if ref_path.exists():
            return ref_path.read_text(encoding="utf-8").strip() or None
        # packed-refs fallback
        packed = REPO_ROOT / ".git" / "packed-refs"
        target = ref.split(" ", 1)[1].strip()
        if packed.exists():
            for line in packed.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith(("#", "^")):
                    continue
                sha, _, name = line.partition(" ")
                if name == target:
                    return sha or None
        return None
    return ref or None


def _collect_inputs() -> list[dict[str, Any]]:
    """Collect the verifiable supply-chain inputs with deterministic ordering.

    Each input must (a) exist on disk and (b) hash-match the manifest, mirroring
    the loaded + sha256_matches_manifest gate. A mismatch is a critical
    invariant failure -- we do NOT silently paper over it.
    """
    manifest = _load_manifest()
    packs = manifest.get("packs", [])
    if manifest.get("total_count") != 42 or len(packs) != 42:
        raise InvariantError(
            f"manifest must report 42 packs, got "
            f"total_count={manifest.get('total_count')} entries={len(packs)}"
        )

    inputs: list[dict[str, Any]] = []
    # The manifest itself is an input.
    inputs.append(
        {
            "role": "manifest",
            "relative_path": str(MANIFEST_PATH.relative_to(REPO_ROOT)),
            "bytes": MANIFEST_PATH.stat().st_size,
            "sha256": _sha256_file(MANIFEST_PATH),
        }
    )

    for entry in packs:
        path = _pack_path(entry)
        label = entry.get("file", "<unknown>")
        if not path.exists():
            raise InvariantError(f"{label}: missing input file at {path}")
        data = path.read_bytes()
        sha = _sha256_bytes(data)
        expected = entry.get("sha256_file")
        if sha != expected:
            raise InvariantError(
                f"{label}: sha256 {sha} != manifest {expected} "
                "(artifact not in a loaded+verified state)"
            )
        if len(data) != entry.get("bytes"):
            raise InvariantError(
                f"{label}: byte length {len(data)} != manifest {entry.get('bytes')}"
            )
        inputs.append(
            {
                "role": "pack",
                "pack": entry.get("pack"),
                "tier": entry.get("tier"),
                "relative_path": entry.get("relative_path"),
                "bytes": len(data),
                "sha256": sha,
            }
        )

    # Stable ordering by relative_path so the derived id is order-independent
    # w.r.t. manifest layout changes that do not change content.
    inputs.sort(key=lambda x: x["relative_path"])
    return inputs


def _hash_summary(inputs: list[dict[str, Any]]) -> str:
    """A single deterministic digest over (relative_path, sha256) pairs.

    Depends only on input content + identity -- not on timestamps, host, or run
    order -- so it is the reproducibility anchor.
    """
    h = hashlib.sha256()
    for item in inputs:
        h.update(item["relative_path"].encode("utf-8"))
        h.update(b"\0")
        h.update(item["sha256"].encode("utf-8"))
        h.update(b"\n")
    return h.hexdigest()


def _scan_banned(text: str) -> list[str]:
    low = text.lower()
    return [s for s in BANNED_SUBSTRINGS if s in low]


def _scan_secrets(text: str) -> list[str]:
    hits: list[str] = []
    for pat in _SECRET_PATTERNS:
        if pat.search(text):
            hits.append(pat.pattern)
    return hits


def build_records() -> tuple[dict[str, Any], dict[str, Any]]:
    """Build (audit_index, determinism_record) as plain dicts.

    The deterministic core of both records excludes the timestamp, which lives
    only under `non_deterministic_zone`.
    """
    inputs = _collect_inputs()
    inputs_hash_summary = _hash_summary(inputs)
    commit_sha = _git_commit_sha()
    now = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # deterministic_run_id is derived ONLY from inputs -> identical inputs give
    # an identical id across runs / hosts / clocks.
    deterministic_run_id = "sha256:" + inputs_hash_summary

    audit_index: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "kind": "x_klickd_supply_chain_audit_trail_index",
        "non_normative": True,
        "repo": REPO_NAME,
        "source_commit_sha": commit_sha,
        "deterministic_run_id": deterministic_run_id,
        "checked_artifacts_count": len(inputs),
        "checked_artifacts_hash_summary": inputs_hash_summary,
        "validation_commands": list(VALIDATION_COMMANDS),
        # validation_results is intentionally empty here: this generator records
        # the declared commands but does NOT run them, so it cannot honestly
        # assert their results. The operator runs them and the audit/CI captures
        # outcomes. Pre-filled "pass" values would be a mirage.
        "validation_results": [],
        "build_or_audit_events": [
            {
                "event": "audit_trail_index_generated",
                "stage": "audit_trail_index",
                "automation": "tool",
                "inputs_hash_summary": inputs_hash_summary,
                "source_commit_sha": commit_sha,
            }
        ],
        "stage_automation": {
            "audit_trail_index": "tool",
            "determinism_record": "tool",
            "reproducibility_check": "tool",
            "pack_hash_verification": "tool",
            "candidate_mapping_validation": "tool",
            "diff_report": "planned",
            "threat_model": "planned",
            "license_check": "planned",
            "source_freshness_check": "planned",
            "pii_secrets_scan": "partial",
            "private_public_boundary_check": "planned",
            "context_graph_generation": "planned",
            "candidate_skill_generation": "planned",
            "premium_pass": "manual",
        },
        "notes": [
            "NON-NORMATIVE. Not a v4.1 GA release artefact.",
            "Only the stages marked 'tool' are backed by shipped automation; "
            "'planned' stages are spec-only; 'partial' is a tripwire, not a "
            "full scanner; 'manual' is human/agent premium work.",
            "An artifact is counted only when its bytes exist on disk and "
            "hash-match the manifest (loaded + sha256_matches_manifest).",
            "validation_results is empty by design: this generator does not run "
            "the validation commands, so it does not assert their outcomes.",
            "Timestamps are excluded from deterministic_run_id; see "
            "determinism_record.json non_deterministic_zone.",
        ],
        "non_deterministic_zone": {
            "generated_at": now,
            "comment": "Fields here are excluded from deterministic_run_id and "
            "checked_artifacts_hash_summary.",
        },
    }

    determinism_record: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "kind": "x_klickd_supply_chain_determinism_record",
        "non_normative": True,
        "repo": REPO_NAME,
        "hash_algo": "sha256",
        "deterministic_run_id": deterministic_run_id,
        "input_files": [
            {"relative_path": i["relative_path"], "sha256": i["sha256"], "bytes": i["bytes"]}
            for i in inputs
        ],
        "inputs_hash_summary": inputs_hash_summary,
        # output_files hashes are computed over the deterministic core of each
        # output (with non_deterministic_zone stripped), so the record is
        # self-consistent across runs. See verify_outputs().
        "output_files": [
            {"relative_path": _rel(AUDIT_INDEX_PATH)},
            {"relative_path": _rel(DETERMINISM_PATH)},
        ],
        "repeatability": {
            "instructions": "Re-run `python scripts/generate_supply_chain_audit.py`. "
            "If inputs are unchanged, deterministic_run_id and "
            "inputs_hash_summary are identical across runs and hosts.",
            "deterministic_fields": [
                "deterministic_run_id",
                "inputs_hash_summary",
                "input_files[*].sha256",
            ],
            "non_deterministic_fields_excluded": [
                "non_deterministic_zone.generated_at",
                "source_commit_sha (provenance, not part of the hash)",
            ],
        },
        "non_deterministic_zone": {
            "generated_at": now,
            "comment": "Excluded from deterministic_run_id and from the output "
            "determinism hashes.",
        },
    }
    return audit_index, determinism_record


def _deterministic_core(record: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of `record` with the non-deterministic zone removed.

    Used to hash outputs in a clock-independent way.
    """
    core = dict(record)
    core.pop("non_deterministic_zone", None)
    core.pop("source_commit_sha", None)
    if "build_or_audit_events" in core:
        core["build_or_audit_events"] = [
            {k: v for k, v in ev.items() if k != "source_commit_sha"}
            for ev in core["build_or_audit_events"]
        ]
    return core


def _canonical_json(obj: Any) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def _serialize(record: dict[str, Any]) -> str:
    # Stable, human-diffable serialization. sort_keys keeps the on-disk bytes
    # deterministic regardless of dict construction order.
    return _canonical_json(record)


def _guard_output(name: str, text: str) -> None:
    banned = _scan_banned(text)
    if banned:
        raise InvariantError(f"{name}: banned substring(s) present: {banned}")
    secrets = _scan_secrets(text)
    if secrets:
        raise InvariantError(f"{name}: possible secret/PII pattern(s): {secrets}")


def cmd_generate() -> int:
    audit_index, determinism_record = build_records()

    # Stamp the deterministic-core hashes of each output into the determinism
    # record so the record describes the bytes it ships next to.
    audit_core_hash = _sha256_bytes(
        _canonical_json(_deterministic_core(audit_index)).encode("utf-8")
    )
    det_core_hash = _sha256_bytes(
        _canonical_json(_deterministic_core(determinism_record)).encode("utf-8")
    )
    for out in determinism_record["output_files"]:
        if out["relative_path"].endswith("audit_trail_index.json"):
            out["deterministic_core_sha256"] = audit_core_hash
        else:
            out["deterministic_core_sha256"] = det_core_hash

    audit_text = _serialize(audit_index)
    det_text = _serialize(determinism_record)

    _guard_output("audit_trail_index.json", audit_text)
    _guard_output("determinism_record.json", det_text)

    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    AUDIT_INDEX_PATH.write_text(audit_text, encoding="utf-8")
    DETERMINISM_PATH.write_text(det_text, encoding="utf-8")

    print(
        f"OK: wrote audit-trail index + determinism record "
        f"({audit_index['checked_artifacts_count']} artifacts, "
        f"run_id {audit_index['deterministic_run_id']})."
    )
    print(f"  - {_rel(AUDIT_INDEX_PATH)}")
    print(f"  - {_rel(DETERMINISM_PATH)}")
    return 0


def cmd_check() -> int:
    """Verify on-disk artefacts are in sync with current inputs (no write).

    Compares the deterministic core of the freshly-built records against the
    deterministic core of the on-disk records. Drift in the time-quarantined
    zone is ignored; drift anywhere else (or missing files) is a failure.
    """
    if not AUDIT_INDEX_PATH.exists() or not DETERMINISM_PATH.exists():
        print("FAIL: audit artefacts missing; run generate.", file=sys.stderr)
        return 1

    audit_index, determinism_record = build_records()

    disk_audit = json.loads(AUDIT_INDEX_PATH.read_text(encoding="utf-8"))
    disk_det = json.loads(DETERMINISM_PATH.read_text(encoding="utf-8"))

    problems: list[str] = []
    if _deterministic_core(audit_index) != _deterministic_core(disk_audit):
        problems.append("audit_trail_index.json out of sync with current inputs")
    # output_files carry computed hashes; rebuild them before comparing.
    audit_core_hash = _sha256_bytes(
        _canonical_json(_deterministic_core(audit_index)).encode("utf-8")
    )
    det_core_hash = _sha256_bytes(
        _canonical_json(_deterministic_core(determinism_record)).encode("utf-8")
    )
    for out in determinism_record["output_files"]:
        out["deterministic_core_sha256"] = (
            audit_core_hash
            if out["relative_path"].endswith("audit_trail_index.json")
            else det_core_hash
        )
    if _deterministic_core(determinism_record) != _deterministic_core(disk_det):
        problems.append("determinism_record.json out of sync with current inputs")

    # Re-guard on-disk bytes for banned/secret content.
    for name, text in (
        ("audit_trail_index.json", AUDIT_INDEX_PATH.read_text(encoding="utf-8")),
        ("determinism_record.json", DETERMINISM_PATH.read_text(encoding="utf-8")),
    ):
        try:
            _guard_output(name, text)
        except InvariantError as exc:
            problems.append(str(exc))

    if problems:
        print(f"FAIL: {len(problems)} problem(s):", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        print("Run `python scripts/generate_supply_chain_audit.py` to refresh.", file=sys.stderr)
        return 1

    print(
        f"OK: audit artefacts in sync (run_id {audit_index['deterministic_run_id']}, "
        f"{audit_index['checked_artifacts_count']} artifacts)."
    )
    return 0


def main(argv: list[str]) -> int:
    args = argv[1:]
    cmd = args[0] if args else "generate"
    try:
        if cmd == "generate":
            return cmd_generate()
        if cmd == "check":
            return cmd_check()
    except InvariantError as exc:
        print(f"FAIL (invariant): {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"FAIL (io): {exc}", file=sys.stderr)
        return 2
    print(f"unknown command: {cmd!r} (generate|check)", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
