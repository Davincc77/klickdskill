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
      skill leaks into the candidate list as if it were a v4.1 candidate pack.
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
ARTEFACT_ROOT = REPO_ROOT / "examples" / "v4.1" / "x-klickd-skills"
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

# Size-tier ceilings (decimal KB by repo convention: "12 KB" = 12_000 bytes,
# not 12 KiB). Enforced by validator; raised 2026-05-27 per the v4.1 expansion
# audit response so Pro packs have headroom for compact_index + lazy body and
# Lite packs have headroom for richer per-pack carrier-state vocabulary. The
# new ceilings are an **upper bound (capacity envelope)**, NOT a target —
# artefacts should stay as compact as their framework-anchored content allows.
# Apply to public x.klickd v4.1 candidate catalog artefacts under
# `examples/v4.1/x-klickd-skills/{lite,pro}/` only; Klickd.app student
# carriers under `examples/v4/klickdapp-skills/` and Kai host-side
# artefacts are out of scope (different validator).
TIER_ROUTER_COST_CEILING = {"lite": 900, "pro": 1350}
TIER_BYTES_CEILING = {"lite": 12_000, "pro": 24_000}

# Frozen counts for the v4.1 candidate artefact set (8 Lite + 34 Pro = 42).
# Promotion or removal requires updating this table AND the planning doc.
TIER_EXPECTED_COUNT = {"lite": 8, "pro": 34}

# Per-tier competency-count range — coherence-rule §3.1 of
# docs/chimera/V4_1_COMPETENCY_IDENTIFICATION_PROTOCOL.md. The total
# count is len(competencies[]) (which by RFC-009 §5.5 equals
# len(competency_mappings[])). The bounds matche the as-shipped
# 2026-05-27 catalog; target ranges live in the protocol doc and are
# not enforced.
TIER_COMPETENCY_RANGE = {"lite": (2, 8), "pro": (3, 12)}

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
# public x.klickd v4.1 candidate catalog. Case-insensitive substring match.
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

# Regex variant of the forbidden-pattern check. Catches any future
# `klickdapp.<2+ letters>` country / locale scope (e.g. `klickdapp.it`,
# `klickdapp.nl`, `klickdapp.uk`) without having to enumerate them by
# hand. Audit-hardening 2026-05-27. Case-insensitive.
ARTEFACT_FORBIDDEN_REGEXES = (
    re.compile(r"klickdapp\.[a-z]{2,}", re.IGNORECASE),
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

# Forbidden public terms (QA-G12). Mechanical literal used by the
# `_scan_public_strings_for_forbidden_terms()` helper. Kept here, in a
# single non-public constant, so the public QA protocol doc
# (docs/chimera/V4_1_SKILL_QA_PROTOCOL.md) does NOT have to spell the
# literal. Lowercased case-insensitive substring match.
#
# Rationale (audit PR #76 WARN-1 follow-through): a copy-paste of any
# paragraph of the protocol doc MUST NOT seed the forbidden literal
# into a public surface. The doc references this constant by name
# instead.
#
# To extend: add the new term here AND document the addition in the
# commit message. Do NOT echo the literal into the public protocol doc.
FORBIDDEN_PUBLIC_TERMS: tuple[str, ...] = ("chimera",)

# Public-facing JSON pointer paths within an x_klickd_pack artefact —
# the QA-G12 scan only fires on string values reached via these paths.
# Anything outside this allow-list is internal metadata (publisher
# bookkeeping, schema version, planning-doc pointers, ...) and may
# continue to reference the historical internal planning track.
#
# Each entry is a (segments, kind) pair where:
#   - segments is a tuple of keys / wildcards walked from x_klickd_pack
#     ('*' matches any list index; '**' matches any dict value)
#   - kind is 'string' (the leaf is a string) or 'string_list' (the
#     leaf is a list of strings)
#
# Reviewers extend this list when a new public-facing field is added
# to the artefact shape (RFC bump). Audit-hardening 2026-05-28.
PUBLIC_FIELDS: tuple[tuple[tuple[str, ...], str], ...] = (
    (("target_user",), "string"),
    (("target_user", "**"), "string"),
    (("competencies", "*", "prefLabel"), "string"),
    (("competencies", "*", "description"), "string"),
    (("competency_mappings", "*", "prefLabel"), "string"),
    (("competency_mappings", "*", "description"), "string"),
    (("compact_index", "prefLabel"), "string"),
    (("acceptance_criteria",), "string_list"),
)

ALLOWED_STATUSES = {"needs_mapping", "candidate_mapped", "ship_ready"}

# Names that MUST NOT appear in any candidate row as if they were
# x.klickd v4.1 candidate packs (per README_V4_1.md §3). They live
# elsewhere (Klickd.app product carriers / Kai host-side artefacts).
EXCLUDED_NAMES = (
    "klickdapp.lu.klickd",
    "klickdapp.fr.klickd",
    "klickdapp.be.klickd",
    "klickdapp.de.klickd",
)

# Host-side artefact name patterns that MUST NOT appear as candidate
# carrier_pack identifiers. Substring match; lower-cased on input.
# Audit-hardening 2026-05-27: `klickdapp.` substring added so any
# `klickdapp.<scope>` reference (current LU/FR/BE/DE or any future scope)
# is rejected at the row-scan level, not only the four enumerated names
# in EXCLUDED_NAMES above.
EXCLUDED_PATTERNS = (
    "klickdapp.",
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
        "video-production-pipeline",
        # v4.1 expansion 2026-05-27 — 15 new Lot B candidates (B20..B34).
        "product-manager", "ux-researcher", "data-analyst", "api-integrator",
        "devops-operator", "security-incident-response", "sales-operator",
        "customer-support-operator", "finance-analyst", "accounting-operator",
        "technical-writer", "learning-designer", "sustainability-analyst",
        "healthcare-ai-safety-reviewer", "edge-ai-operator",
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

    # Competency-coherence checks
    # (docs/chimera/V4_1_COMPETENCY_IDENTIFICATION_PROTOCOL.md §3).
    # 3.1 Tier-specific count range.
    if tier in TIER_COMPETENCY_RANGE and isinstance(comps, list):
        lo, hi = TIER_COMPETENCY_RANGE[tier]
        if not (lo <= len(comps) <= hi):
            fails.append(
                f"{path.name}: competencies[] count {len(comps)} outside "
                f"{tier} range [{lo}, {hi}] (protocol §3.1)"
            )
    # 3.2 Common transversal base.
    btc = block.get("base_transversal_core") or {}
    transversal = btc.get("transversal_refs") or []
    if not isinstance(transversal, list) or not transversal:
        fails.append(
            f"{path.name}: base_transversal_core.transversal_refs[] must be "
            f"a non-empty list (protocol §3.2)"
        )
    else:
        for t in transversal:
            if not isinstance(t, dict) or "competency_ref" not in t:
                fails.append(
                    f"{path.name}: transversal_refs[] entry missing 'competency_ref'"
                )
    # 3.3 competency_mappings[] and competencies[] must agree in size
    # (RFC-009 §5.5 equal-shape rule); soft check — warn-via-fail when
    # one is empty and the other is not, but not when both shapes use
    # the same anchor set.
    cms = block.get("competency_mappings") or []
    if isinstance(cms, list) and isinstance(comps, list):
        if (len(cms) == 0) ^ (len(comps) == 0):
            fails.append(
                f"{path.name}: competency_mappings[] and competencies[] "
                f"must both be populated or both empty (RFC-009 §5.5)"
            )

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
    # Regex sweep — catches any future `klickdapp.<scope>` country code
    # we haven't enumerated yet (audit-hardening 2026-05-27).
    for pat in ARTEFACT_FORBIDDEN_REGEXES:
        m = pat.search(raw)
        if m:
            fails.append(
                f"{path.name}: forbidden Klickd.app pattern matches "
                f"{pat.pattern!r} (matched text: '{m.group(0)}')"
            )

    # Secrets / PII scan. The patterns below are conservative shape
    # checks; false-positive policy: if a real-world legitimate value
    # ever needs to live in an artefact (e.g. a published support email,
    # a publisher OIDC issuer), add the literal substring to
    # `PII_ALLOWED_SUBSTRINGS` above with a one-line comment naming the
    # artefact and reason. Do NOT silence the check by widening the
    # pattern itself.
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


# Near-duplicate heuristic thresholds — see
# docs/chimera/V4_1_SKILL_QA_PROTOCOL.md §5.1. The exact-clone (1.00)
# case is enforced as a BLOCKER by validate_no_competency_clones();
# pairs above the WARN threshold but below the BLOCKER threshold are
# reported as warnings via validate_near_duplicate_competency_sets(),
# which does NOT contribute to the validator exit code. Reviewers
# acknowledge each WARN in the QA-G09 scoring row.
NEAR_DUPLICATE_JACCARD_WARN = 0.80


def _jaccard(a: frozenset, b: frozenset) -> float:
    if not a and not b:
        return 0.0
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)


def validate_near_duplicate_competency_sets() -> list[str]:
    """Near-duplicate heuristic (QA-G09 WARN, QA protocol §5.1).

    Pairs of artefacts inside the same tier whose `competencies[]`
    sets (compared as frozensets of `competency_ref` strings) have
    Jaccard overlap >= NEAR_DUPLICATE_JACCARD_WARN and < 1.00 are
    reported as warnings. Exact clones (overlap == 1.00) are caught
    by validate_no_competency_clones() as BLOCKERs and are not
    duplicated here. Cross-tier pairs are not flagged because a
    Lite/Pro re-anchoring is a legitimate tier shift.

    Returns a list of WARN lines (empty when nothing is suspect).
    The caller MUST treat the returned list as advisory: the QA
    protocol §5.1 explicitly states that WARNs do not auto-block the
    ship; they only require a task-boundary justification recorded
    in the QA-G09 scoring row.
    """
    warns: list[str] = []
    if not ARTEFACT_ROOT.exists():
        return warns
    for tier_dir in (LITE_DIR, PRO_DIR):
        if not tier_dir.exists():
            continue
        entries: list[tuple[str, frozenset]] = []
        for path in sorted(tier_dir.glob("*.klickd")):
            try:
                obj = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            comps = (obj.get("x_klickd_pack") or {}).get("competencies") or []
            sig = frozenset(
                c["competency_ref"] for c in comps
                if isinstance(c, dict) and "competency_ref" in c
            )
            if sig:
                entries.append((path.name, sig))
        for i in range(len(entries)):
            for j in range(i + 1, len(entries)):
                name_i, sig_i = entries[i]
                name_j, sig_j = entries[j]
                j_score = _jaccard(sig_i, sig_j)
                if NEAR_DUPLICATE_JACCARD_WARN <= j_score < 1.0:
                    warns.append(
                        f"WARN near-duplicate ({tier_dir.name}): "
                        f"{name_i} <-> {name_j} Jaccard={j_score:.2f} "
                        f"(QA-G09 WARN; record task-boundary justification "
                        f"or split/merge — QA protocol §5.1)"
                    )
    return warns


def validate_no_competency_clones() -> list[str]:
    """Anti-clone rule (protocol §3.4): no two artefacts in the catalog
    may share an identical `competencies[]` set (compared as the
    frozenset of `competency_ref` strings). Prevents two skills from
    being indistinguishable except by name."""
    fails: list[str] = []
    if not ARTEFACT_ROOT.exists():
        return fails
    sigs: dict[frozenset, list[str]] = {}
    for tier_dir in (LITE_DIR, PRO_DIR):
        if not tier_dir.exists():
            continue
        for path in sorted(tier_dir.glob("*.klickd")):
            try:
                obj = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            comps = (obj.get("x_klickd_pack") or {}).get("competencies") or []
            sig = frozenset(
                c["competency_ref"] for c in comps
                if isinstance(c, dict) and "competency_ref" in c
            )
            if not sig:
                continue
            sigs.setdefault(sig, []).append(path.name)
    for sig, files in sigs.items():
        if len(files) > 1:
            fails.append(
                f"competency-clone detected: {files} share identical "
                f"competencies[] set {sorted(sig)} (protocol §3.4)"
            )
    return fails


def _collect_public_strings(block: dict) -> list[tuple[str, str]]:
    """Walk an x_klickd_pack block and yield (json_pointer, value) pairs
    for every string reached via a path in PUBLIC_FIELDS.

    Returns a list of (pointer, string_value) pairs. Pointer is a
    slash-separated path starting at 'x_klickd_pack' so reviewer-facing
    error messages are self-explanatory.
    """
    results: list[tuple[str, str]] = []

    def _walk(node, segments: tuple[str, ...], pointer: str, kind: str) -> None:
        if not segments:
            if kind == "string" and isinstance(node, str):
                results.append((pointer, node))
            elif kind == "string_list" and isinstance(node, list):
                for i, item in enumerate(node):
                    if isinstance(item, str):
                        results.append((f"{pointer}[{i}]", item))
            return
        head, rest = segments[0], segments[1:]
        if head == "*":
            if isinstance(node, list):
                for i, item in enumerate(node):
                    _walk(item, rest, f"{pointer}[{i}]", kind)
            return
        if head == "**":
            if isinstance(node, dict):
                for k, v in node.items():
                    _walk(v, rest, f"{pointer}.{k}", kind)
            return
        if isinstance(node, dict) and head in node:
            _walk(node[head], rest, f"{pointer}.{head}", kind)

    for segments, kind in PUBLIC_FIELDS:
        _walk(block, segments, "x_klickd_pack", kind)
    return results


def _scan_public_strings_for_forbidden_terms(
    public_strings: list[tuple[str, str]],
) -> list[tuple[str, str, str]]:
    """Return (pointer, value, matched_term) triples for every string
    that contains a FORBIDDEN_PUBLIC_TERMS substring (case-insensitive).
    """
    hits: list[tuple[str, str, str]] = []
    for pointer, value in public_strings:
        low = value.lower()
        for term in FORBIDDEN_PUBLIC_TERMS:
            if term in low:
                hits.append((pointer, value, term))
                break
    return hits


def validate_no_forbidden_public_wording() -> list[str]:
    """QA-G12 (BLOCKER): no string reachable through a PUBLIC_FIELDS
    pointer may contain a FORBIDDEN_PUBLIC_TERMS substring (case-
    insensitive). Internal metadata outside PUBLIC_FIELDS is allowed
    to reference the historical internal planning track. See
    docs/chimera/V4_1_SKILL_QA_PROTOCOL.md §5.4 for the allow-list
    and the rationale for not spelling the forbidden literal in the
    public doc.
    """
    fails: list[str] = []
    if not ARTEFACT_ROOT.exists():
        return fails
    for tier_dir in (LITE_DIR, PRO_DIR):
        if not tier_dir.exists():
            continue
        for path in sorted(tier_dir.glob("*.klickd")):
            try:
                obj = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            block = obj.get("x_klickd_pack") or {}
            public_strings = _collect_public_strings(block)
            hits = _scan_public_strings_for_forbidden_terms(public_strings)
            for pointer, value, term in hits:
                fails.append(
                    f"{path.name}: QA-G12 BLOCKER — public field "
                    f"'{pointer}' contains forbidden term "
                    f"(matched '{term}' in {value!r})"
                )
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


def validate_public_surface_codename_clean() -> list[str]:
    """Raw-byte scan over every file under ARTEFACT_ROOT.

    The public download surface (every `.klickd`, every `manifest.json`,
    the in-directory `README.md`, and any other file shipped alongside
    them) must not contain any FORBIDDEN_PUBLIC_TERMS byte. This is
    deliberately *stricter* than `_scan_public_strings_for_forbidden_terms()`
    — that function only scans the PUBLIC_FIELDS allow-list inside the
    artefact JSON object, which is fine for catching public-facing prose
    leaks but does NOT catch internal-metadata fields (`_pack_metadata`,
    `domain_schema_version`, `spec_ref`, etc.) that a downloader sees as
    soon as they `cat` the file.

    A path is on the public download surface iff it lives under
    `examples/v4.1/x-klickd-skills/`. Internal planning docs under
    `docs/chimera/` or RFC files such as `docs/rfcs/RFC-009-chimera-v4.1.md`
    are NOT on this surface and are explicitly out of scope here.
    """
    fails: list[str] = []
    if not ARTEFACT_ROOT.exists():
        return fails
    for path in sorted(ARTEFACT_ROOT.rglob("*")):
        if not path.is_file():
            continue
        try:
            raw = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        lower = raw.lower()
        for term in FORBIDDEN_PUBLIC_TERMS:
            if term in lower:
                rel = path.relative_to(REPO_ROOT)
                line_no = next(
                    (i + 1 for i, line in enumerate(raw.splitlines())
                     if term in line.lower()),
                    None,
                )
                fails.append(
                    f"{rel}: contains forbidden public term '{term}'"
                    + (f" (first hit at line {line_no})" if line_no else "")
                    + " — the public download surface under "
                      "examples/v4.1/x-klickd-skills/ MUST NOT mention the "
                      "internal v4.1 working codename in any byte (artefact "
                      "JSON, manifest, README, or any other shipped file)."
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
        expected = TIER_EXPECTED_COUNT.get(tier_dir.name)
        if expected is not None and len(actual_files) != expected:
            fails.append(
                f"{mpath}: tier '{tier_dir.name}' has {len(actual_files)} artefact(s); "
                f"expected exactly {expected} per TIER_EXPECTED_COUNT"
            )
    return fails


# --- RFC-010 (`compressed_memory` draft/preview) artefact invariants ---
#
# Every x.klickd v4.1 candidate skill now ships an RFC-010 `compressed_memory`
# draft block under `x_klickd_pack.structured_memory.compressed_memory`. The
# block is NON-NORMATIVE, NON-GA. The checks below enforce the RFC-010
# invariants on the block as it appears inside the skill artefacts:
#
#   - presence + version pin (`rfc-010-draft`)
#   - draft-preview markers (`_status`, `_non_normative`, `_claims_v41_ga`)
#   - empty pointer arrays (these are skill templates, not carrier state)
#   - pointer-only invariants (no inline embeddings, no data: URIs, no inline
#     extraction logic)
#   - hardened extractor (`kind` enum, `x.klickd/host/`-prefixed `agent_ref`,
#     semver-shaped `version`, algo-prefixed `attestation_hash` when
#     extraction is automated)
#   - GDPR Art.17 erasure cascade (`on_user_request = cascade_purge`)
#   - `memory_recall_injection` gate ref present
#   - retrieval scope is role-specific: no two artefacts may share an
#     identical `_draft_retrieval_scope` (tags + entity_classes + priority)

RFC010_EXTRACTOR_KINDS = {"host_skill", "local_runtime", "verified_bridge"}
RFC010_FRESHNESS_VALUES = {"none", "linear_recency", "exponential_recency"}
RFC010_REQUIRED_TOP_KEYS = (
    "version",
    "derived_from",
    "fact_pointers",
    "entity_links",
    "graph_refs",
    "vector_index",
    "retrieval_policy",
    "erasure_cascade",
    "gate_refs",
)
RFC010_SEMVER_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+(?:-[A-Za-z0-9.+-]+)?$")
RFC010_HASH_RE = re.compile(r"^(?:sha256|blake3):[A-Fa-f0-9]{32,}$")


def _validate_rfc010_block(path: Path, cm: dict) -> list[str]:
    fails: list[str] = []
    name = path.name

    for key in RFC010_REQUIRED_TOP_KEYS:
        if key not in cm:
            fails.append(f"{name}: compressed_memory.{key} missing (RFC-010 §5)")
    if cm.get("version") != "rfc-010-draft":
        fails.append(
            f"{name}: compressed_memory.version must be 'rfc-010-draft' "
            f"(RFC-010 §5)"
        )
    if cm.get("_non_normative") is not True:
        fails.append(
            f"{name}: compressed_memory._non_normative must be true "
            f"(draft/preview marker)"
        )
    if cm.get("_claims_v41_ga") is not False:
        fails.append(
            f"{name}: compressed_memory._claims_v41_ga must be false "
            f"(RFC-010 is v4.2 Draft, not v4.1 GA)"
        )

    # Empty pointer arrays — skill templates carry no carrier facts.
    for arr_key in ("fact_pointers", "entity_links", "graph_refs"):
        v = cm.get(arr_key)
        if not isinstance(v, list):
            fails.append(f"{name}: compressed_memory.{arr_key} must be a list")
            continue
        if v:
            fails.append(
                f"{name}: compressed_memory.{arr_key} must be empty in a "
                f"skill template (no per-carrier facts; RFC-010 §5.1)"
            )

    # Extractor hardening
    dfrom = cm.get("derived_from") or {}
    if dfrom.get("pack") != (cm.get("derived_from") or {}).get("pack"):
        pass  # no-op (kept for symmetry)
    extractor = (dfrom.get("extractor") or {})
    kind = extractor.get("kind")
    if kind not in RFC010_EXTRACTOR_KINDS:
        fails.append(
            f"{name}: derived_from.extractor.kind '{kind}' must be in "
            f"{sorted(RFC010_EXTRACTOR_KINDS)} (RFC-010 §5)"
        )
    agent_ref = extractor.get("agent_ref", "")
    if not agent_ref.startswith("x.klickd/host/"):
        fails.append(
            f"{name}: derived_from.extractor.agent_ref must start with "
            f"'x.klickd/host/' (RFC-010 §6.1)"
        )
    version = extractor.get("version", "")
    if not RFC010_SEMVER_RE.match(version):
        fails.append(
            f"{name}: derived_from.extractor.version '{version}' is not "
            f"semver-shaped (RFC-010 §5)"
        )
    att = extractor.get("attestation_hash")
    if kind in {"host_skill", "verified_bridge"}:
        if not (isinstance(att, str) and RFC010_HASH_RE.match(att)):
            fails.append(
                f"{name}: derived_from.extractor.attestation_hash must be "
                f"'<sha256|blake3>:<hex>' when kind='{kind}' (RFC-010 §5)"
            )

    # vector_index — pointer-only, no inline embeddings
    vi = cm.get("vector_index") or {}
    if vi.get("inline_embeddings_forbidden") is not True:
        fails.append(
            f"{name}: vector_index.inline_embeddings_forbidden must be true "
            f"(RFC-010 §5.3)"
        )
    uri = vi.get("uri", "")
    if not isinstance(uri, str) or uri.startswith("data:"):
        fails.append(
            f"{name}: vector_index.uri must be a non-data: URI "
            f"(RFC-010 §5)"
        )
    if not isinstance(vi.get("dim"), int) or vi.get("dim", 0) < 1:
        fails.append(f"{name}: vector_index.dim must be a positive integer")
    if not isinstance(vi.get("embedding_model_ref"), str) or not vi.get(
        "embedding_model_ref"
    ):
        fails.append(
            f"{name}: vector_index.embedding_model_ref must be a non-empty "
            f"discriminated reference (RFC-010 §5)"
        )

    # retrieval_policy
    rp = cm.get("retrieval_policy") or {}
    if rp.get("host_side_only") is not True:
        fails.append(
            f"{name}: retrieval_policy.host_side_only must be true "
            f"(RFC-010 §5)"
        )
    if rp.get("require_gate") != "memory_recall_injection":
        fails.append(
            f"{name}: retrieval_policy.require_gate must be "
            f"'memory_recall_injection' (RFC-010 §6.3)"
        )
    if rp.get("freshness_weighting") not in RFC010_FRESHNESS_VALUES:
        fails.append(
            f"{name}: retrieval_policy.freshness_weighting "
            f"'{rp.get('freshness_weighting')}' must be in "
            f"{sorted(RFC010_FRESHNESS_VALUES)}"
        )
    for k in ("top_k", "max_facts_per_turn"):
        v = rp.get(k)
        if not isinstance(v, int) or not (1 <= v <= 50):
            fails.append(
                f"{name}: retrieval_policy.{k}={v!r} must be int in [1, 50]"
            )

    # erasure_cascade — Art.17 deterministic
    ec = cm.get("erasure_cascade") or {}
    if ec.get("on_user_request") != "cascade_purge":
        fails.append(
            f"{name}: erasure_cascade.on_user_request must be "
            f"'cascade_purge' (RFC-010 §6.2; no exceptions)"
        )
    if ec.get("on_evidence_deletion") not in {"cascade_purge", "tombstone_only"}:
        fails.append(
            f"{name}: erasure_cascade.on_evidence_deletion must be "
            f"'cascade_purge' or 'tombstone_only' (RFC-010 §6.2)"
        )
    targets = ec.get("targets") or []
    if not isinstance(targets, list) or not targets:
        fails.append(
            f"{name}: erasure_cascade.targets must be a non-empty list"
        )

    # gate_refs — at least one memory_recall_injection
    grefs = cm.get("gate_refs") or []
    if not (
        isinstance(grefs, list)
        and any(
            isinstance(g, dict)
            and g.get("action_class") == "memory_recall_injection"
            for g in grefs
        )
    ):
        fails.append(
            f"{name}: gate_refs[] must include a memory_recall_injection "
            f"action_class (RFC-010 §6.3)"
        )

    # No inline extraction logic (§5.4) — heuristic byte check.
    raw_block = json.dumps(cm).lower()
    for forbidden_key in (
        "extraction_prompt",
        "extractor_prompt",
        "scoring_function",
        "scoring_code",
        "prompt_template",
    ):
        if forbidden_key in raw_block:
            fails.append(
                f"{name}: compressed_memory must not contain extraction "
                f"prompts / scoring code (RFC-010 §5.4, §6.5); found "
                f"'{forbidden_key}'"
            )

    # Anti-copy: no third-party memory-system compatibility claim inside
    # the artefact's compressed_memory block (RFC-010 §2, §8 #6).
    for sys_name in ("mem0", "graphrag", "letta", "memgpt", "zep", "a-mem", "amem"):
        for needle in (
            f"{sys_name} compatible",
            f"{sys_name}-compatible",
            f"compatible with {sys_name}",
        ):
            if needle in raw_block:
                fails.append(
                    f"{name}: compressed_memory must not claim "
                    f"third-party compatibility ('{needle}'); see "
                    f"RFC-010 §2 anti-copy statement"
                )
    return fails


def validate_rfc010_blocks_in_artefacts() -> list[str]:
    """Enforce RFC-010 invariants in every x.klickd v4.1 candidate skill."""
    fails: list[str] = []
    if not ARTEFACT_ROOT.exists():
        return fails
    for tier_dir in (LITE_DIR, PRO_DIR):
        if not tier_dir.exists():
            continue
        for path in sorted(tier_dir.glob("*.klickd")):
            try:
                obj = json.loads(path.read_text(encoding="utf-8"))
            except Exception as e:
                fails.append(f"{path.name}: JSON parse failed: {e}")
                continue
            block = (obj.get("x_klickd_pack") or {})
            sm = block.get("structured_memory") or {}
            cm = sm.get("compressed_memory")
            if not isinstance(cm, dict):
                fails.append(
                    f"{path.name}: x_klickd_pack.structured_memory."
                    f"compressed_memory missing (RFC-010 §4.1 pinned path)"
                )
                continue
            # pack id consistency
            dfrom_pack = (cm.get("derived_from") or {}).get("pack")
            pack_id = block.get("pack")
            if dfrom_pack != pack_id:
                fails.append(
                    f"{path.name}: compressed_memory.derived_from.pack "
                    f"'{dfrom_pack}' != x_klickd_pack.pack '{pack_id}'"
                )
            fails.extend(_validate_rfc010_block(path, cm))
    return fails


def validate_rfc010_retrieval_scope_unique() -> list[str]:
    """No two artefacts may share an identical RFC-010 retrieval scope.

    The retrieval scope is the tuple
        (sorted(tags), sorted(entity_classes), priority,
         top_k, max_facts_per_turn, freshness_weighting, dim)
    drawn from `_draft_retrieval_scope`, `retrieval_policy`, and
    `vector_index`. Identical scopes across packs would mean the
    catalogue carries copy-paste compressed_memory blocks — which the
    parent audit explicitly forbids.
    """
    fails: list[str] = []
    if not ARTEFACT_ROOT.exists():
        return fails
    scope_keys: dict[tuple, list[str]] = {}
    tag_sets: dict[tuple, list[str]] = {}
    for tier_dir in (LITE_DIR, PRO_DIR):
        if not tier_dir.exists():
            continue
        for path in sorted(tier_dir.glob("*.klickd")):
            try:
                obj = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            cm = (
                ((obj.get("x_klickd_pack") or {}).get("structured_memory") or {})
                .get("compressed_memory")
            )
            if not isinstance(cm, dict):
                continue
            scope = cm.get("_draft_retrieval_scope") or {}
            rp = cm.get("retrieval_policy") or {}
            vi = cm.get("vector_index") or {}
            tags = tuple(sorted(scope.get("tags") or []))
            ents = tuple(sorted(scope.get("entity_classes") or []))
            key = (
                tags,
                ents,
                scope.get("priority"),
                rp.get("top_k"),
                rp.get("max_facts_per_turn"),
                rp.get("freshness_weighting"),
                vi.get("dim"),
            )
            scope_keys.setdefault(key, []).append(path.name)
            tag_sets.setdefault(tags, []).append(path.name)
    for key, files in scope_keys.items():
        if len(files) > 1:
            fails.append(
                f"RFC-010 retrieval-scope clone: {files} share identical "
                f"retrieval scope {key} (no copy-paste compressed_memory "
                f"across the 42 skills)"
            )
    for tags, files in tag_sets.items():
        if len(files) > 1:
            fails.append(
                f"RFC-010 retrieval-tags clone: {files} share identical "
                f"_draft_retrieval_scope.tags {list(tags)} (each pack "
                f"must contribute a role-specific tag set)"
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
    near_dup_warns: list[str] = []
    if ARTEFACT_ROOT.exists():
        for tier_dir in (LITE_DIR, PRO_DIR):
            if not tier_dir.exists():
                continue
            for path in sorted(tier_dir.glob("*.klickd")):
                artefact_count += 1
                all_failures.extend(validate_artefact(path))
        all_failures.extend(validate_no_deferred_artefacts())
        all_failures.extend(validate_no_competency_clones())
        all_failures.extend(validate_no_forbidden_public_wording())
        all_failures.extend(validate_public_surface_codename_clean())
        all_failures.extend(validate_manifests())
        all_failures.extend(validate_rfc010_blocks_in_artefacts())
        all_failures.extend(validate_rfc010_retrieval_scope_unique())
        # Near-duplicate heuristic is advisory (QA protocol §5.1).
        # Reported to stderr but does NOT affect exit code.
        near_dup_warns = validate_near_duplicate_competency_sets()

    if all_failures:
        print(f"FAIL: {len(all_failures)} issue(s) found", file=sys.stderr)
        for f in all_failures:
            print(f"  - {f}", file=sys.stderr)
        return 1

    if near_dup_warns:
        print(
            f"WARN: {len(near_dup_warns)} near-duplicate pair(s) "
            f"(QA-G09 WARN; advisory only — see "
            f"docs/chimera/V4_1_SKILL_QA_PROTOCOL.md §5)",
            file=sys.stderr,
        )
        for w in near_dup_warns:
            print(f"  - {w}", file=sys.stderr)

    print(
        f"OK: {doc_path.name} — {len(rows)} candidate row(s) parsed; "
        f"{artefact_count} artefact(s) validated; all checks passed."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
