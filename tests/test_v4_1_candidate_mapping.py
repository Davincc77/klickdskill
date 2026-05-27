"""Pytest wrapper for scripts/validate_v4_1_candidate_mapping.py.

Invokes the validator on docs/chimera/V4_1_SKILL_CANDIDATE_MAPPING.md and
asserts that the planning document satisfies the strict mapping rule of
docs/chimera/README_V4_1.md §1. NON-NORMATIVE; no schema change.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "validate_v4_1_candidate_mapping.py"
DOC = REPO_ROOT / "docs" / "chimera" / "V4_1_SKILL_CANDIDATE_MAPPING.md"


def _load_validator():
    spec = importlib.util.spec_from_file_location("v4_1_candidate_validator", SCRIPT)
    assert spec and spec.loader, f"could not load {SCRIPT}"
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_mapping_doc_exists():
    assert DOC.exists(), f"candidate mapping doc missing: {DOC}"


def test_planning_index_exists():
    assert (REPO_ROOT / "docs" / "chimera" / "README_V4_1.md").exists()


def test_candidate_checklist_exists():
    assert (REPO_ROOT / "docs" / "chimera" / "V4_1_CANDIDATE_CHECKLIST.md").exists()


def test_validator_runs_clean_on_mapping_doc():
    mod = _load_validator()
    text = DOC.read_text(encoding="utf-8")
    rows = mod.parse_candidate_tables(text)
    assert rows, "no candidate rows parsed from mapping doc"
    failures: list[str] = []
    for row in rows:
        failures.extend(mod.validate_row(row))
    failures.extend(mod.check_excluded_names_in_table_rows(rows))
    failures.extend(mod.check_required_candidates_present(rows))
    assert not failures, "\n".join(failures)


def test_required_candidates_all_present():
    mod = _load_validator()
    text = DOC.read_text(encoding="utf-8")
    rows = mod.parse_candidate_tables(text)
    missing = mod.check_required_candidates_present(rows)
    assert not missing, "\n".join(missing)


def test_no_klickdapp_in_chimera_planning_dir():
    """Public planning dir MUST NOT mention Klickd.app product carrier
    filenames or Kai host-side skills as if they were Chimera candidate
    packs. The §3 exclusion table is allowed (it lists them precisely
    in order to exclude them) so we scan only the §1 / §2 candidate
    rows via the validator's row-scoped check."""
    mod = _load_validator()
    text = DOC.read_text(encoding="utf-8")
    rows = mod.parse_candidate_tables(text)
    leaks = mod.check_excluded_names_in_table_rows(rows)
    assert not leaks, "\n".join(leaks)
