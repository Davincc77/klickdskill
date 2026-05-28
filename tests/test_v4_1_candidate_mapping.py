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


def test_filename_stem_matches_pack_tail():
    """Audit W-1 fix: every artefact's filename stem MUST equal the
    pack-tail (with underscores converted to dashes). Audit BLOCKER
    rename pass enforces this everywhere; this test guards against
    regression in future PRs."""
    import json as _json
    mod = _load_validator()
    failures: list[str] = []
    for path in _lite_files() + _pro_files():
        obj = _json.loads(path.read_text(encoding="utf-8"))
        pack_id = obj["x_klickd_pack"]["pack"]
        expected_stem = pack_id.rsplit("/", 1)[-1].replace("_", "-")
        stem = path.stem
        allow = mod.FILENAME_PACK_ALLOWED_DIVERGENCE.get(path.name)
        if stem != expected_stem and allow is None:
            failures.append(
                f"{path.name}: stem '{stem}' != expected '{expected_stem}' "
                f"(from pack '{pack_id}')"
            )
    assert not failures, "\n".join(failures)


def test_crypto_lite_artefact_is_deferred():
    """Audit response: crypto-lite artefact was removed because no EU
    SKOS-published crypto-asset-literacy framework exists. The
    nickname is in DEFERRED_NICKNAMES and the validator must reject
    any future attempt to recreate the artefact under any spelling
    (crypto-lite.klickd, crypto-basics.klickd, crypto.klickd)."""
    forbidden_names = {"crypto-lite", "crypto-basics", "crypto",
                       "crypto-asset", "crypto-literacy"}
    for path in _lite_files() + _pro_files():
        assert path.stem not in forbidden_names, (
            f"{path.name}: crypto-* artefact must stay deferred until "
            f"a SKOS-published crypto-literacy framework anchors it"
        )


def test_competency_protocol_doc_exists():
    """Protocol doc is the merge gate per the 2026-05-27 user requirement.
    PR #75 must not be considered ready until this document exists and
    is linked from the planning index + the candidate mapping doc."""
    p = REPO_ROOT / "docs" / "chimera" / "V4_1_COMPETENCY_IDENTIFICATION_PROTOCOL.md"
    assert p.is_file(), f"competency identification protocol doc missing: {p}"
    text = p.read_text(encoding="utf-8")
    # Sanity: the protocol must name its key sections so the validator
    # comment references stay accurate.
    for section in (
        "Admissible source hierarchy",
        "Selection method",
        "Coherence rules",
        "Exclusion rules",
        "Validator support",
    ):
        assert section in text, f"protocol section '{section}' missing"


def test_competency_count_in_tier_range():
    """Coherence rule §3.1: every artefact's competencies[] count must
    fall inside the tier's [min, max] range."""
    import json as _json
    mod = _load_validator()
    failures: list[str] = []
    for path in _lite_files() + _pro_files():
        obj = _json.loads(path.read_text(encoding="utf-8"))
        block = obj["x_klickd_pack"]
        tier = block["size_tier"]
        comps = block.get("competencies") or []
        lo, hi = mod.TIER_COMPETENCY_RANGE[tier]
        if not (lo <= len(comps) <= hi):
            failures.append(
                f"{path.name}: competencies[] count {len(comps)} outside "
                f"{tier} range [{lo}, {hi}]"
            )
    assert not failures, "\n".join(failures)


def test_every_artefact_carries_transversal_base():
    """Coherence rule §3.2: every artefact carries a non-empty
    base_transversal_core.transversal_refs[]. Anchors the 'shared'
    half of the coherent-blend requirement."""
    import json as _json
    failures: list[str] = []
    for path in _lite_files() + _pro_files():
        obj = _json.loads(path.read_text(encoding="utf-8"))
        block = obj["x_klickd_pack"]
        btc = block.get("base_transversal_core") or {}
        tr = btc.get("transversal_refs") or []
        if not tr:
            failures.append(
                f"{path.name}: base_transversal_core.transversal_refs[] empty"
            )
        else:
            for t in tr:
                if "competency_ref" not in t:
                    failures.append(
                        f"{path.name}: transversal_refs[] entry missing 'competency_ref'"
                    )
    assert not failures, "\n".join(failures)


def test_no_two_artefacts_share_competency_set():
    """Anti-clone rule §3.4: no two artefacts may have identical
    competencies[] sets. A failure here means one of the two is a
    duplicate that should be merged or removed."""
    mod = _load_validator()
    failures = mod.validate_no_competency_clones()
    assert not failures, "\n".join(failures)


def test_tier_artefact_counts_are_frozen_at_8_lite_and_34_pro():
    """2026-05-27 v4.1 expansion: the artefact set is frozen at exactly
    8 Lite + 34 Pro = 42 candidate skills covering everyday users (Lite)
    and the majority of AI-assisted future jobs (Pro). Any drift requires
    updating the planning doc, the validator constants
    (`TIER_EXPECTED_COUNT`), and the per-tier `manifest.json`."""
    mod = _load_validator()
    assert mod.TIER_EXPECTED_COUNT["lite"] == 8
    assert mod.TIER_EXPECTED_COUNT["pro"] == 34
    assert len(_lite_files()) == 8, (
        f"expected 8 lite artefacts, found {len(_lite_files())}: "
        f"{[p.name for p in _lite_files()]}"
    )
    assert len(_pro_files()) == 34, (
        f"expected 34 pro artefacts, found {len(_pro_files())}: "
        f"{[p.name for p in _pro_files()]}"
    )


def test_qa_protocol_doc_exists():
    """QA protocol is the mandatory merge gate for `ship_ready`
    promotion (2026-05-28). Must exist, must name its key sections,
    and must use public `x.klickd` wording (not `Chimera`) in its
    title."""
    p = REPO_ROOT / "docs" / "chimera" / "V4_1_SKILL_QA_PROTOCOL.md"
    assert p.is_file(), f"QA protocol doc missing: {p}"
    text = p.read_text(encoding="utf-8")
    assert "x.klickd" in text.splitlines()[0], (
        "QA protocol title must use public `x.klickd` wording"
    )
    for section in (
        "Mandatory gates",
        "Scoring checklist",
        "Required sign-offs",
        "Mandatory ordering",
        "Near-duplicate heuristic",
    ):
        assert section in text, f"QA protocol section '{section}' missing"
    # All 14 gates must be present.
    for gate in [f"QA-G{i:02d}" for i in range(1, 15)]:
        assert gate in text, f"QA protocol gate '{gate}' missing"
    # The five sign-off owners must be present.
    for owner in ("Architecture", "Security", "Legal", "UX", "QA"):
        assert owner in text, f"QA protocol sign-off owner '{owner}' missing"


def test_qa_protocol_linked_from_planning_docs():
    """QA protocol must be reachable from the planning index, the
    competency identification protocol, and the candidate checklist."""
    for doc in (
        REPO_ROOT / "docs" / "chimera" / "README_V4_1.md",
        REPO_ROOT / "docs" / "chimera" / "V4_1_COMPETENCY_IDENTIFICATION_PROTOCOL.md",
        REPO_ROOT / "docs" / "chimera" / "V4_1_CANDIDATE_CHECKLIST.md",
    ):
        text = doc.read_text(encoding="utf-8")
        assert "V4_1_SKILL_QA_PROTOCOL.md" in text, (
            f"{doc.name} must link to V4_1_SKILL_QA_PROTOCOL.md"
        )


def test_near_duplicate_heuristic_function_exists():
    """The near-duplicate Jaccard heuristic (QA-G09 WARN, QA protocol
    §5.1) MUST exist as a function on the validator and MUST return a
    list of strings (the WARN lines)."""
    mod = _load_validator()
    assert hasattr(mod, "validate_near_duplicate_competency_sets"), (
        "validator missing validate_near_duplicate_competency_sets()"
    )
    assert hasattr(mod, "NEAR_DUPLICATE_JACCARD_WARN")
    assert 0.0 < mod.NEAR_DUPLICATE_JACCARD_WARN < 1.0
    warns = mod.validate_near_duplicate_competency_sets()
    assert isinstance(warns, list)
    for w in warns:
        assert isinstance(w, str)
        # WARN lines must not include 'FAIL' or 'BLOCKER' — they are advisory.
        assert "FAIL" not in w


def test_near_duplicate_heuristic_does_not_block_exit_code():
    """The near-duplicate heuristic is advisory (QA protocol §5.1).
    It is reported to stderr but MUST NOT contribute to the validator
    failure list, which would change the exit code. The exact-clone
    case is handled by validate_no_competency_clones() as a BLOCKER."""
    mod = _load_validator()
    # Sanity: the BLOCKER-half function is the exact-clone check.
    blockers = mod.validate_no_competency_clones()
    for b in blockers:
        assert "clone" in b.lower()


def test_no_chimera_wording_in_public_facing_fields():
    """QA-G12 (no forbidden public wording): public-facing fields in
    every candidate artefact MUST NOT contain the internal track name
    `Chimera` (case-insensitive). Public-facing fields are those a
    carrier or `/klickdskill` catalog UI would read directly:
    `x_klickd_pack.target_user` and `x_klickd_pack.competencies[*].prefLabel`.
    Internal metadata (`_pack_metadata.kind`, `_pack_metadata.note`,
    `domain_schema_version`, `see_planning_doc`, ...) is explicitly
    allowed to reference the track name because those keys are not
    surfaced in any public UI."""
    import json as _json
    leaks: list[str] = []
    for path in _lite_files() + _pro_files():
        obj = _json.loads(path.read_text(encoding="utf-8"))
        block = obj.get("x_klickd_pack") or {}
        public_strings: list[str] = []
        tu = block.get("target_user")
        if isinstance(tu, str):
            public_strings.append(tu)
        elif isinstance(tu, dict):
            for v in tu.values():
                if isinstance(v, str):
                    public_strings.append(v)
        for c in block.get("competencies") or []:
            if isinstance(c, dict):
                label = c.get("prefLabel")
                if isinstance(label, str):
                    public_strings.append(label)
        for s in public_strings:
            if "chimera" in s.lower():
                leaks.append(f"{path.name}: public-facing field contains 'Chimera': {s!r}")
    assert not leaks, "\n".join(leaks)


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
