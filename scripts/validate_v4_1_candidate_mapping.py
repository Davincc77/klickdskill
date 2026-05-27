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

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DOC = REPO_ROOT / "docs" / "chimera" / "V4_1_SKILL_CANDIDATE_MAPPING.md"

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

    if all_failures:
        print(f"FAIL: {len(all_failures)} issue(s) in {doc_path}", file=sys.stderr)
        for f in all_failures:
            print(f"  - {f}", file=sys.stderr)
        return 1

    print(
        f"OK: {doc_path} — {len(rows)} candidate row(s) parsed; "
        f"all strict-mapping-rule checks passed."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
