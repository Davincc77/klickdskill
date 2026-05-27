#!/usr/bin/env python3
"""Validate docs/chimera/V4_1_SKILL_CANDIDATE_MAPPING.md against the
strict mapping rule of docs/chimera/README_V4_1.md §1.

Scope (NON-NORMATIVE, planning-doc validator):
  - Parses the Lot A and Lot B candidate tables.
  - Verifies that each row carries all nine required fields:
      working nickname, proposed canonical filename, parent pack(s),
      target carrier, framework anchors, gates / human veto,
      source / evidence policy, size tier, status.
  - Verifies that every proposed canonical filename uses the
      `x.klickd/<name>` namespace (or is an explicit sub-area of an
      existing pack such as `x.klickd/student.exam_targets[]`).
  - Verifies that no Klickd.app-specific carrier name and no Kai host
      skill leaks into the candidate list as if it were a Chimera pack.
      The blocklist is the §3 exclusion table of README_V4_1.md.
  - Verifies that the status field is one of `needs_mapping`,
      `candidate_mapped`, `ship_ready`.

Exit codes:
  0  all-pass
  1  one or more candidate rows failed the strict mapping rule
  2  usage / I/O error (file missing, table cannot be parsed)

Stdlib-only, offline. No release artefact, no schema change.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DOC = REPO_ROOT / "docs" / "chimera" / "V4_1_SKILL_CANDIDATE_MAPPING.md"
ARTEFACT_ROOT = REPO_ROOT / "examples" / "v4.1" / "chimera-skills"
LITE_DIR = ARTEFACT_ROOT / "lite"
PRO_DIR = ARTEFACT_ROOT / "pro"

# Candidates that MUST NOT have a concrete .klickd file under the
# artefact directory (their framework anchor or PII-of-others consent
# shape is unresolved). They stay documented in the planning doc only.
DEFERRED_NICKNAMES = {
    "personal-finance",
    "budget",
    "crypto-lite",     # audit response: no SKOS-published crypto-literacy framework
    "crypto-basics",
    "crypto",
    "wellbeing-lite",
    "family",
}

# Sub-areas of an existing P0 pack, NEVER separate .klickd files.
SUB_AREA_NICKNAMES = {
    "language",  # x.klickd/student.language_proficiency
    "exam",      # x.klickd/student.exam_targets[]
}

# Size-tier ceilings (descriptive planning hints; enforced by validator).
TIER_ROUTER_COST_CEILING = {"lite": 900, "pro": 1350}
TIER_BYTES_CEILING = {"lite": 8_000, "pro": 12_000}

FORBIDDEN_FIELDS_LITERAL = [
    "pedagogy", "teaching_method", "socratic_steps", "prompt_strategy",
    "scoring_rubric", "intervention_policy", "tone_rules",
    "system_prompt_overrides", "knowledge.mastered", "mastered_topics",
]

# Explicit allow-list for filenames whose stem is permitted to diverge
# from `pack.rsplit('/', 1)[-1].replace('_', '-')`. Empty by default —
# every artefact must have filename_stem == pack_tail_dashed. Audit
# W-1 fix.
FILENAME_PACK_ALLOWED_DIVERGENCE: dict[str, str] = {}

# Patterns that, if matched in the raw artefact text, indicate a
# Klickd.app product carrier or Kai host-side artefact leaked into the
# public Chimera catalog. Case-insensitive substring match.
ARTEFACT_FORBIDDEN_PATTERNS = (
    "klickdapp.lu",
    "klickdapp.fr",
    "klickdapp.be",
    "klickdapp.de",
    "skill.kai.",
    "core.kai.klickd",
    "kai tutor",
    "kai mentor",
    "kai.tutor",
)

# Regex patterns that catch likely secrets / PII inside an artefact.
SECRET_PATTERNS = (
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),                 # AWS access key id
    re.compile(r"\bASIA[0-9A-Z]{16}\b"),                 # AWS session id
    re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"),            # Google API key
    re.compile(r"\bghp_[A-Za-z0-9]{20,}\b"),             # GitHub personal token
    re.compile(r"\bxox[abp]-[A-Za-z0-9-]{10,}\b"),       # Slack token
    re.compile(r"\bsk_live_[A-Za-z0-9]{16,}\b"),         # Stripe live secret
)
PII_PATTERNS = (
    re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"),         # email
    # IBAN: 2 letters + 2 digits + 11-30 alphanumerics; require word boundary
    re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b"),
    # Phone with international prefix (broad; allowed only in citation URLs)
    re.compile(r"\+\d{2,3}[\s-]?\d[\s\d-]{8,}"),
)
# Allow-list literal email-like substrings (publisher placeholders only)
PII_ALLOWED_SUBSTRINGS = ()

ALLOWED_STATUSES = {"needs_mapping", "candidate_mapped", "ship_ready"}

# Names that MUST NOT appear in any candidate row as if they were
# Chimera packs (per README_V4_1.md §3). They live elsewhere.
EXCLUDED_NAMES = (
    "klickdapp.lu.klickd",
    "klickdapp.fr.klickd",
    "klickdapp.be.klickd",
    "klickdapp.de.klickd",
)

# Host-side artefact name patterns that MUST NOT appear as candidate
# carrier_pack identifiers. Substring match; lower-cased on input.
EXCLUDED_PATTERNS = (
    "core.kai.klickd",
    "skill.kai.",
    "kai.tutor",
    "kai tutor",
    "kai mentor",
)

# Required column headers (order-independent; matched by substring).
REQUIRED_COLUMN_TOKENS = (
    "working nickname",
    "proposed canonical filename",
    "parent pack",
    "target carrier",
    "framework anchors",
    "gates",
    "source / evidence policy",
    "size tier",
    "status",
)


def parse_candidate_tables(text: str) -> list[dict]:
    """Extract Lot A (§1) and Lot B (§2) candidate rows.

    Returns one dict per row with raw cell values keyed by column header
    (lowercased + stripped). Skips header / separator rows.
    """
    rows: list[dict] = []
    in_table = False
    headers: list[str] = []
    section: str | None = None

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if line.startswith("## 1. Lot A"):
            section = "A"
            in_table = False
            headers = []
            continue
        if line.startswith("## 2. Lot B"):
            section = "B"
            in_table = False
            headers = []
            continue
        if line.startswith("## ") and section in {"A", "B"} and not line.startswith(
            ("## 1.", "## 2.")
        ):
            section = None
            in_table = False
            headers = []
            continue
        if section not in {"A", "B"}:
            continue
        if not line.startswith("|"):
            in_table = False
            headers = []
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if not headers:
            headers = [c.lower() for c in cells]
            in_table = True
            continue
        # Separator row like |---|---|---|
        if all(set(c) <= set("-: ") for c in cells):
            continue
        if not in_table:
            continue
        if len(cells) != len(headers):
            continue
        row = {h: v for h, v in zip(headers, cells)}
        row["_section"] = "Lot A" if section == "A" else "Lot B"
        rows.append(row)
    return rows


def find_header(row: dict, token: str) -> str | None:
    for h in row:
        if token in h:
            return h
    return None


def validate_row(row: dict) -> list[str]:
    failures: list[str] = []
    nickname_h = find_header(row, "working nickname")
    nickname = row.get(nickname_h, "") if nickname_h else ""

    # Field-presence checks (C-001..C-009 fields)
    for token in REQUIRED_COLUMN_TOKENS:
        h = find_header(row, token)
        if h is None:
            failures.append(f"missing column '{token}'")
            continue
        v = row.get(h, "").strip()
        if not v:
            failures.append(f"row '{nickname}' has empty '{token}' cell")

    # Status field check
    status_h = find_header(row, "status")
    if status_h is not None:
        status_cell = row.get(status_h, "").lower()
        if not any(s in status_cell for s in ALLOWED_STATUSES):
            failures.append(
                f"row '{nickname}' status '{status_cell}' must contain one of "
                f"{sorted(ALLOWED_STATUSES)}"
            )

    # Namespace check on proposed canonical filename
    name_h = find_header(row, "proposed canonical filename")
    if name_h is not None:
        name_cell = row.get(name_h, "")
        if "x.klickd/" not in name_cell and "sub-area" not in name_cell.lower() \
                and "sub-profile" not in name_cell.lower():
            failures.append(
                f"row '{nickname}' canonical filename '{name_cell}' is not in the "
                f"x.klickd/<name> namespace and is not an explicit sub-area/sub-profile"
            )
        for bad in ("klickdapp.", "core.kai.klickd", "skill.kai.", "kai.tutor"):
            if bad in name_cell.lower():
                failures.append(
                    f"row '{nickname}' canonical filename '{name_cell}' contains "
                    f"forbidden name fragment '{bad}'"
                )

    return failures


def check_excluded_names_in_table_rows(rows: list[dict]) -> list[str]:
    """Scan candidate-table rows for any leak of Klickd.app-specific or
    Kai host-side names into the candidate list itself (the §3 exclusion
    table is allowed to mention them; this only scans the §1 / §2 rows).
    """
    failures: list[str] = []
    for row in rows:
        nickname_h = find_header(row, "working nickname")
        nickname = row.get(nickname_h, "") if nickname_h else ""
        # Skip the structural columns; scan every cell value.
        for h, v in row.items():
            if h == "_section":
                continue
            lv = v.lower()
            for bad in EXCLUDED_NAMES:
                if bad in lv:
                    failures.append(
                        f"row '{nickname}' column '{h}' leaks excluded name "
                        f"'{bad}' (belongs to Klickd.app, see README_V4_1.md §3)"
                    )
            for bad in EXCLUDED_PATTERNS:
                if bad in lv:
                    failures.append(
                        f"row '{nickname}' column '{h}' leaks host-side pattern "
                        f"'{bad}' (see README_V4_1.md §3)"
                    )
    return failures


def check_required_candidates_present(rows: list[dict]) -> list[str]:
    """Ensure every nickname Vince asked for is present at least once."""
    required = {
        "work-lite", "language", "exam", "media-lite", "agent-security",
        "ai-agent-builder", "iam-endpoint", "personal-finance", "budget",
        "consumer-rights", "crypto-lite", "social", "artist", "streamer-lite",
        "game-literacy", "parent-gaming", "release-engineer", "trust-evidence",
        "eu-ai-act", "gdpr-readiness", "contract-review", "privacy-product",
        "evidence-desk", "policy-analyst", "second-brain", "literature-review",
        "project-operator", "drone", "mission-control", "game-design",
        "rights-guard", "wellbeing-lite", "family",
    }
    found = set()
    for row in rows:
        h = find_header(row, "working nickname")
        if h is None:
            continue
        val = row.get(h, "")
        # working nickname cell is wrapped in backticks: `work-lite`
        m = re.search(r"`([a-z0-9_.-]+)`", val)
        if m:
            found.add(m.group(1))
    missing = sorted(required - found)
    return [f"required candidate nickname '{n}' is missing from the mapping table"
            for n in missing]


REQUIRED_ARTEFACT_KEYS = (
    "pack", "pack_version", "spec_ref", "publisher", "size_tier",
    "parent_packs", "target_user", "frameworks", "competency_mappings",
    "competencies", "base_transversal_core", "memory_scope",
    "memory_segments", "gates", "human_veto", "human_authority",
    "evidence_policy", "source_policy", "verification_gates",
    "router_cost", "acceptance_criteria", "tests", "forbidden_fields",
)
REQUIRED_PRO_EXTRA_KEYS = ("loading_strategy", "compact_index")
REQUIRED_PACK_METADATA_KEYS = (
    "kind", "size_tier", "non_normative", "claims_v41_ga",
    "contains_real_pii", "contains_secrets", "status",
)


def validate_artefact(path: Path) -> list[str]:
    fails: list[str] = []
    try:
        raw = path.read_text(encoding="utf-8")
    except Exception as e:
        return [f"{path.name}: read failed: {e}"]
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError as e:
        return [f"{path.name}: JSON parse failed: {e}"]

    # envelope
    if obj.get("klickd_version") != "4.0":
        fails.append(f"{path.name}: klickd_version must equal '4.0'")
    if obj.get("encrypted") is not False:
        fails.append(f"{path.name}: encrypted must be false (envelope round-trip).")

    meta = obj.get("_pack_metadata") or {}
    for key in REQUIRED_PACK_METADATA_KEYS:
        if key not in meta:
            fails.append(f"{path.name}: _pack_metadata.{key} missing")
    if meta.get("claims_v41_ga") is not False:
        fails.append(f"{path.name}: _pack_metadata.claims_v41_ga must be false (no GA claim)")
    if meta.get("contains_real_pii") is not False:
        fails.append(f"{path.name}: _pack_metadata.contains_real_pii must be false")
    if meta.get("contains_secrets") is not False:
        fails.append(f"{path.name}: _pack_metadata.contains_secrets must be false")
    if meta.get("status") not in ALLOWED_STATUSES:
        fails.append(
            f"{path.name}: _pack_metadata.status='{meta.get('status')}' "
            f"must be in {sorted(ALLOWED_STATUSES)}"
        )
    if meta.get("status") == "ship_ready":
        fails.append(f"{path.name}: status='ship_ready' is not allowed in this candidate directory.")

    block = obj.get("x_klickd_pack") or {}
    for key in REQUIRED_ARTEFACT_KEYS:
        if key not in block:
            fails.append(f"{path.name}: x_klickd_pack.{key} missing")

    pack_id = block.get("pack", "")
    if not pack_id.startswith("x.klickd/"):
        fails.append(f"{path.name}: pack '{pack_id}' must be in x.klickd/<name> namespace")
    for bad in ARTEFACT_FORBIDDEN_PATTERNS:
        if bad in pack_id.lower():
            fails.append(f"{path.name}: pack '{pack_id}' contains forbidden fragment '{bad}'")

    # Filename <-> pack-id consistency (audit W-1). The filename stem
    # MUST equal the pack-tail with underscores converted to dashes,
    # unless the file appears in FILENAME_PACK_ALLOWED_DIVERGENCE with
    # a documented justification.
    if pack_id.startswith("x.klickd/"):
        pack_tail = pack_id.rsplit("/", 1)[-1]
        expected_stem = pack_tail.replace("_", "-")
        stem = path.stem
        allow = FILENAME_PACK_ALLOWED_DIVERGENCE.get(path.name)
        if stem != expected_stem and allow is None:
            fails.append(
                f"{path.name}: filename stem '{stem}' must equal "
                f"pack tail '{pack_tail}' with underscores as dashes "
                f"('{expected_stem}'); no allowed-divergence entry."
            )

    tier = block.get("size_tier")
    tier_dir = path.parent.name
    if tier != tier_dir:
        fails.append(f"{path.name}: size_tier '{tier}' does not match directory '{tier_dir}'")
    if tier not in TIER_ROUTER_COST_CEILING:
        fails.append(f"{path.name}: size_tier must be one of {sorted(TIER_ROUTER_COST_CEILING)}")

    # Router cost ceiling
    rc = block.get("router_cost") or {}
    tokens = rc.get("tokens_estimate")
    if not isinstance(tokens, int):
        fails.append(f"{path.name}: router_cost.tokens_estimate must be int, got {tokens!r}")
    elif tier in TIER_ROUTER_COST_CEILING and tokens > TIER_ROUTER_COST_CEILING[tier]:
        fails.append(
            f"{path.name}: router_cost.tokens_estimate {tokens} > {tier} ceiling "
            f"{TIER_ROUTER_COST_CEILING[tier]}"
        )

    # Bytes ceiling (loose tier sanity)
    if tier in TIER_BYTES_CEILING and len(raw.encode("utf-8")) > TIER_BYTES_CEILING[tier]:
        fails.append(
            f"{path.name}: file size {len(raw.encode('utf-8'))} > {tier} ceiling "
            f"{TIER_BYTES_CEILING[tier]} bytes"
        )

    # parent_packs must reference x.klickd/* identifiers
    parents = block.get("parent_packs") or []
    if not isinstance(parents, list) or not parents:
        fails.append(f"{path.name}: parent_packs must be a non-empty list")
    else:
        for p in parents:
            if not isinstance(p, str) or not p.startswith("x.klickd/"):
                fails.append(f"{path.name}: parent_packs entry '{p}' must be x.klickd/<name>")

    # frameworks[] non-empty and SKOS-shaped
    fws = block.get("frameworks") or []
    if not isinstance(fws, list) or not fws:
        fails.append(f"{path.name}: frameworks[] must be a non-empty list")
    else:
        for fw in fws:
            if not isinstance(fw, dict) or "scheme" not in fw:
                fails.append(f"{path.name}: frameworks[] entry missing 'scheme'")

    # competencies non-empty and framework-anchored
    comps = block.get("competencies") or []
    if not isinstance(comps, list) or not comps:
        fails.append(f"{path.name}: competencies[] must be a non-empty list")
    else:
        for c in comps:
            if not isinstance(c, dict):
                fails.append(f"{path.name}: competencies[] entry must be object")
                continue
            for k in ("competency_ref", "scheme", "prefLabel"):
                if k not in c:
                    fails.append(f"{path.name}: competencies[] entry missing '{k}'")

    # human_authority + human_veto
    ha = block.get("human_authority") or {}
    if ha.get("final_decision_owner", "").split("_")[0] != "human":
        fails.append(
            f"{path.name}: human_authority.final_decision_owner must be a human_* value"
        )
    if (block.get("human_veto") or {}).get("raise_only") is not True:
        fails.append(f"{path.name}: human_veto.raise_only must be true")

    # gates
    gates = block.get("gates") or {}
    if not (gates.get("verification_gates_default") or {}).get("raise_only") is True:
        fails.append(f"{path.name}: gates.verification_gates_default.raise_only must be true")

    # evidence_policy / source_policy
    ep = block.get("evidence_policy") or {}
    if ep.get("pointer_only") is not True:
        fails.append(f"{path.name}: evidence_policy.pointer_only must be true")
    sp = block.get("source_policy") or {}
    if sp.get("allow_inline_definitions") is not False:
        fails.append(f"{path.name}: source_policy.allow_inline_definitions must be false")

    # forbidden_fields literal must be frozen list
    forbidden = block.get("forbidden_fields") or []
    if forbidden != FORBIDDEN_FIELDS_LITERAL:
        fails.append(
            f"{path.name}: forbidden_fields literal does not match frozen list (RFC-009 §8.1)"
        )

    # No forbidden_fields key may appear as a key inside x_klickd_pack
    for forbidden_key in FORBIDDEN_FIELDS_LITERAL:
        # nested key paths like 'knowledge.mastered' / 'mastered_topics'
        if "." in forbidden_key:
            parts = forbidden_key.split(".")
            cur = block
            for p in parts:
                if isinstance(cur, dict) and p in cur:
                    cur = cur[p]
                else:
                    cur = None
                    break
            if cur is not None:
                fails.append(
                    f"{path.name}: forbidden carrier-vs-skill key path '{forbidden_key}' present"
                )
        else:
            if forbidden_key in block:
                fails.append(
                    f"{path.name}: forbidden carrier-vs-skill key '{forbidden_key}' present"
                )

    # Pro tier compact_index requirement
    if tier == "pro":
        for k in REQUIRED_PRO_EXTRA_KEYS:
            if k not in block:
                fails.append(f"{path.name}: pro tier requires x_klickd_pack.{k}")
        ci = block.get("compact_index") or {}
        for k in ("pack", "frameworks", "competency_ids", "gate_summaries",
                  "human_authority", "router_cost"):
            if k not in ci:
                fails.append(f"{path.name}: compact_index.{k} missing")
        ls = block.get("loading_strategy") or {}
        if ls.get("mode") != "compact_index_plus_lazy_body":
            fails.append(
                f"{path.name}: loading_strategy.mode must equal 'compact_index_plus_lazy_body'"
            )

    # Forbidden Klickd.app / Kai patterns anywhere in the raw text
    low = raw.lower()
    for bad in ARTEFACT_FORBIDDEN_PATTERNS:
        if bad in low:
            fails.append(
                f"{path.name}: forbidden Klickd.app / Kai host-side pattern '{bad}' present"
            )

    # Secrets / PII scan
    for pat in SECRET_PATTERNS:
        if pat.search(raw):
            fails.append(f"{path.name}: suspected secret matches pattern {pat.pattern!r}")
    for pat in PII_PATTERNS:
        for m in pat.finditer(raw):
            value = m.group(0)
            if any(allow in value for allow in PII_ALLOWED_SUBSTRINGS):
                continue
            fails.append(f"{path.name}: suspected PII '{value}' matches pattern {pat.pattern!r}")

    return fails


def validate_no_deferred_artefacts() -> list[str]:
    """Ensure no .klickd file exists for a deferred (needs_mapping) candidate."""
    fails: list[str] = []
    if not ARTEFACT_ROOT.exists():
        return fails
    for tier_dir in (LITE_DIR, PRO_DIR):
        if not tier_dir.exists():
            continue
        for path in tier_dir.glob("*.klickd"):
            nickname = path.stem
            if nickname in DEFERRED_NICKNAMES:
                fails.append(
                    f"{path}: deferred (needs_mapping) candidate '{nickname}' MUST NOT have a "
                    f"concrete .klickd artefact (see V4_1_SKILL_CANDIDATE_MAPPING.md §1.1)"
                )
            if nickname in SUB_AREA_NICKNAMES:
                fails.append(
                    f"{path}: '{nickname}' is a sub-area of x.klickd/student, NOT a separate "
                    f"pack; remove the file."
                )
    return fails


def validate_manifests() -> list[str]:
    fails: list[str] = []
    for tier_dir in (LITE_DIR, PRO_DIR):
        mpath = tier_dir / "manifest.json"
        if not tier_dir.exists():
            continue
        if not mpath.exists():
            fails.append(f"{mpath}: manifest.json missing for tier '{tier_dir.name}'")
            continue
        try:
            m = json.loads(mpath.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            fails.append(f"{mpath}: JSON parse failed: {e}")
            continue
        if m.get("size_tier") != tier_dir.name:
            fails.append(f"{mpath}: size_tier must equal '{tier_dir.name}'")
        if m.get("claims_v41_ga") is not False:
            fails.append(f"{mpath}: claims_v41_ga must be false (no GA claim)")
        packs = m.get("packs") or []
        if not packs:
            fails.append(f"{mpath}: packs[] must be non-empty")
        actual_files = sorted(p.name for p in tier_dir.glob("*.klickd"))
        manifest_files = sorted(p.get("file") for p in packs)
        if actual_files != manifest_files:
            fails.append(
                f"{mpath}: manifest files {manifest_files} do not match directory "
                f"contents {actual_files}"
            )
    return fails


def main(argv: list[str]) -> int:
    doc_path = Path(argv[1]) if len(argv) > 1 else DEFAULT_DOC
    if not doc_path.exists():
        print(f"ERROR: mapping doc not found: {doc_path}", file=sys.stderr)
        return 2
    text = doc_path.read_text(encoding="utf-8")
    rows = parse_candidate_tables(text)
    if not rows:
        print(
            f"ERROR: no candidate rows parsed from {doc_path}; "
            f"expected Lot A and Lot B tables under '## 1.' / '## 2.'",
            file=sys.stderr,
        )
        return 2

    all_failures: list[str] = []
    for row in rows:
        all_failures.extend(validate_row(row))
    all_failures.extend(check_excluded_names_in_table_rows(rows))
    all_failures.extend(check_required_candidates_present(rows))

    # Artefact-level validation
    artefact_count = 0
    if ARTEFACT_ROOT.exists():
        for tier_dir in (LITE_DIR, PRO_DIR):
            if not tier_dir.exists():
                continue
            for path in sorted(tier_dir.glob("*.klickd")):
                artefact_count += 1
                all_failures.extend(validate_artefact(path))
        all_failures.extend(validate_no_deferred_artefacts())
        all_failures.extend(validate_manifests())

    if all_failures:
        print(f"FAIL: {len(all_failures)} issue(s) found", file=sys.stderr)
        for f in all_failures:
            print(f"  - {f}", file=sys.stderr)
        return 1

    print(
        f"OK: {doc_path.name} — {len(rows)} candidate row(s) parsed; "
        f"{artefact_count} artefact(s) validated; all checks passed."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
