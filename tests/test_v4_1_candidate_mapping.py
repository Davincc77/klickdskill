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


# --- artefact-level tests (Lite + Pro real .klickd files) ---

ART_ROOT = REPO_ROOT / "examples" / "v4.1" / "chimera-skills"
LITE = ART_ROOT / "lite"
PRO = ART_ROOT / "pro"


def _lite_files():
    return sorted(LITE.glob("*.klickd"))


def _pro_files():
    return sorted(PRO.glob("*.klickd"))


def test_artefact_directories_exist():
    assert LITE.is_dir(), f"lite directory missing: {LITE}"
    assert PRO.is_dir(), f"pro directory missing: {PRO}"
    assert (LITE / "manifest.json").is_file()
    assert (PRO / "manifest.json").is_file()
    assert (ART_ROOT / "README.md").is_file()


def test_lite_tier_has_artefacts():
    assert _lite_files(), "lite/ has no .klickd files"


def test_pro_tier_has_artefacts():
    assert _pro_files(), "pro/ has no .klickd files"


def test_every_artefact_passes_validator():
    mod = _load_validator()
    failures: list[str] = []
    for path in _lite_files() + _pro_files():
        failures.extend(mod.validate_artefact(path))
    assert not failures, "\n".join(failures)


def test_no_deferred_candidate_has_an_artefact():
    """Deferred (needs_mapping) candidates and sub-area-only nicknames
    MUST NOT appear as concrete .klickd artefacts."""
    mod = _load_validator()
    failures = mod.validate_no_deferred_artefacts()
    assert not failures, "\n".join(failures)


def test_manifests_match_directory_contents():
    mod = _load_validator()
    failures = mod.validate_manifests()
    assert not failures, "\n".join(failures)


def test_no_klickdapp_or_kai_in_any_artefact():
    mod = _load_validator()
    leaks: list[str] = []
    for path in _lite_files() + _pro_files():
        raw = path.read_text(encoding="utf-8").lower()
        for bad in mod.ARTEFACT_FORBIDDEN_PATTERNS:
            if bad in raw:
                leaks.append(f"{path.name}: contains '{bad}'")
    assert not leaks, "\n".join(leaks)


def test_no_artefact_claims_ga():
    import json as _json
    failures: list[str] = []
    for path in _lite_files() + _pro_files():
        obj = _json.loads(path.read_text(encoding="utf-8"))
        if obj.get("_pack_metadata", {}).get("claims_v41_ga") is not False:
            failures.append(f"{path.name}: claims_v41_ga must be false")
        if obj.get("_pack_metadata", {}).get("status") == "ship_ready":
            failures.append(f"{path.name}: status must NOT be ship_ready")
    assert not failures, "\n".join(failures)


def test_pro_tier_artefacts_carry_compact_index():
    import json as _json
    failures: list[str] = []
    for path in _pro_files():
        obj = _json.loads(path.read_text(encoding="utf-8"))
        block = obj.get("x_klickd_pack", {})
        ci = block.get("compact_index", {})
        ls = block.get("loading_strategy", {})
        for k in ("pack", "frameworks", "competency_ids", "gate_summaries",
                  "human_authority", "router_cost"):
            if k not in ci:
                failures.append(f"{path.name}: compact_index.{k} missing")
        if ls.get("mode") != "compact_index_plus_lazy_body":
            failures.append(f"{path.name}: loading_strategy.mode wrong")
    assert not failures, "\n".join(failures)


def test_lite_router_cost_under_900_and_pro_under_1350():
    import json as _json
    failures: list[str] = []
    for path in _lite_files():
        obj = _json.loads(path.read_text(encoding="utf-8"))
        t = obj["x_klickd_pack"]["router_cost"]["tokens_estimate"]
        if t > 900:
            failures.append(f"{path.name}: lite tokens_estimate {t} > 900")
    for path in _pro_files():
        obj = _json.loads(path.read_text(encoding="utf-8"))
        t = obj["x_klickd_pack"]["router_cost"]["tokens_estimate"]
        if t > 1350:
            failures.append(f"{path.name}: pro tokens_estimate {t} > 1350")
    assert not failures, "\n".join(failures)
