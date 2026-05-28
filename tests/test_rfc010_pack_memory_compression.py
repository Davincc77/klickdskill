"""Validator tests for RFC-010 (pack_memory_compression, .klickd v4.2 Draft).

These tests enforce the non-release / non-modification invariants that
RFC-010 declares (see docs/rfcs/RFC-010-pack-memory-compression.md §8 and
§12):

  1. The RFC document exists.
  2. The non-normative example fixture exists and is clearly marked
     non-GA / non-release.
  3. No v4.0 GA schema file has been touched by this RFC's PR (verified by
     stable repo paths; the RFC text forbids modification, this test
     enforces presence without modification by checking that the schema
     files are still parseable JSON and still declare a v4.x-shaped
     `$schema`).
  4. The 42 frozen v4.1 x.klickd skill artefacts under
     examples/v4.1/x-klickd-skills/{lite,pro}/*.klickd are still present
     and the directory shape is unchanged. (RFC-010 §8 #5.)
  5. The RFC and example MUST NOT claim Mem0 / GraphRAG / Letta / MemGPT /
     Zep / A-MEM compatibility. (RFC-010 §8 #6, §9.)
  6. Key RFC-010 terms are present in the document. (RFC-010 §8 #7.)
  7. The example fixture mounts at
     `x_klickd_pack.structured_memory.compressed_memory` and contains the
     pointer-only / host-side-only invariants. (RFC-010 §4.1, §5.1, §5.3,
     §6.1.)
  8. The RFC index (docs/rfcs/README.md) lists RFC-010 as v4.2 Draft.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
RFC_PATH = REPO_ROOT / "docs" / "rfcs" / "RFC-010-pack-memory-compression.md"
EXAMPLE_PATH = (
    REPO_ROOT / "docs" / "rfcs" / "examples" / "pack_memory_compression-v1.example.json"
)
RFC_INDEX = REPO_ROOT / "docs" / "rfcs" / "README.md"

V40_GA_SCHEMA = REPO_ROOT / "schemas" / "klickd-payload-v4.schema.json"
V40_PREVIEW_SCHEMA = REPO_ROOT / "schemas" / "klickd-payload-v4-preview.schema.json"
V40_GA_SCHEMA_ALT = REPO_ROOT / "schema" / "klickd-v4.schema.json"
V40_PREVIEW_SCHEMA_ALT = REPO_ROOT / "schema" / "klickd-v4-preview.schema.json"

FROZEN_V41_DIR = REPO_ROOT / "examples" / "v4.1" / "x-klickd-skills"


def test_rfc010_document_exists():
    assert RFC_PATH.is_file(), f"RFC-010 document missing at {RFC_PATH}"


def test_rfc010_example_exists():
    assert EXAMPLE_PATH.is_file(), f"RFC-010 example missing at {EXAMPLE_PATH}"


def test_rfc010_example_is_clearly_non_release():
    text = EXAMPLE_PATH.read_text(encoding="utf-8")
    assert "NON-NORMATIVE" in text and "NON-RELEASE" in text, (
        "Example fixture must clearly state NON-NORMATIVE and NON-RELEASE"
    )
    assert "Draft" in text or "draft" in text


def test_v40_ga_schema_unchanged_at_known_paths():
    for path in (V40_GA_SCHEMA, V40_PREVIEW_SCHEMA, V40_GA_SCHEMA_ALT, V40_PREVIEW_SCHEMA_ALT):
        assert path.is_file(), f"v4 schema vanished: {path}"
        json.loads(path.read_text(encoding="utf-8"))
    text_ga = V40_GA_SCHEMA.read_text(encoding="utf-8")
    assert "rfc-010" not in text_ga.lower() and "compressed_memory" not in text_ga, (
        "RFC-010 must not modify klickd-payload-v4.schema.json"
    )
    text_preview = V40_PREVIEW_SCHEMA.read_text(encoding="utf-8")
    assert "rfc-010" not in text_preview.lower() and "compressed_memory" not in text_preview, (
        "RFC-010 must not modify klickd-payload-v4-preview.schema.json"
    )


def test_frozen_v41_skill_artefacts_unchanged():
    assert FROZEN_V41_DIR.is_dir(), "frozen v4.1 x.klickd skills dir missing"
    lite = sorted(p.name for p in (FROZEN_V41_DIR / "lite").glob("*.klickd"))
    pro = sorted(p.name for p in (FROZEN_V41_DIR / "pro").glob("*.klickd"))
    total = len(lite) + len(pro)
    assert total == 42, (
        f"frozen v4.1 skill artefact count changed: expected 42 (lite+pro), got "
        f"{total} (lite={len(lite)}, pro={len(pro)})"
    )
    for skill in lite + pro:
        # The RFC must not touch these artefacts. Their content is not asserted
        # here (other tests handle that); we only assert the inventory shape.
        assert skill.endswith(".klickd"), skill


@pytest.mark.parametrize(
    "system",
    [
        "mem0",
        "graphrag",
        "letta",
        "memgpt",
        "zep",
        "a-mem",
        "amem",
    ],
)
def test_rfc010_does_not_claim_third_party_compatibility(system):
    """Example fixture must not claim compatibility. The RFC document itself
    discusses these systems explicitly (§2 prior-art table) only to negate
    compatibility — so we check the example fixture (which has no such
    legitimate negation context) and we verify the RFC's anti-copy
    disclaimer is present in the document."""
    example_lower = EXAMPLE_PATH.read_text(encoding="utf-8").lower()
    for needle in (
        f"{system} compatible",
        f"{system}-compatible",
        f"compatible with {system}",
    ):
        assert needle not in example_lower, (
            f"Example must not claim compatibility: '{needle}'"
        )


def test_rfc010_contains_explicit_anti_copy_disclaimer():
    text = RFC_PATH.read_text(encoding="utf-8")
    # The RFC must explicitly disclaim compatibility with Mem0 and the
    # broader memory-system family. §2 carries the canonical statement.
    assert "Anti-copy statement" in text
    assert "claims **no** compatibility" in text or "no compatibility" in text
    assert "Mem0" in text and "GraphRAG" in text and "MemGPT" in text


def test_rfc010_key_terms_present():
    text = RFC_PATH.read_text(encoding="utf-8")
    required = [
        "compressed_memory",
        "fact_pointers",
        "entity_links",
        "graph_refs",
        "vector_index",
        "retrieval_policy",
        "erasure_cascade",
        "erasure_status",
        "cascade_purged",
        "gate_refs",
        "memory_recall_injection",
        "host-side",
        "pointer-only",
        "GDPR Art.17",
        "knowledge.skills_compressed",
        "x_klickd_pack.structured_memory.compressed_memory",
        "host_skill",
        "local_runtime",
        "verified_bridge",
        "attestation_hash",
    ]
    missing = [t for t in required if t not in text]
    assert not missing, f"RFC-010 missing required terms: {missing}"


def test_rfc010_mount_path_pinned_no_alternative():
    text = RFC_PATH.read_text(encoding="utf-8")
    # The pinned canonical path MUST appear and the §4.1 "alternative" wording
    # MUST be gone — the path is no longer an open question.
    assert "x_klickd_pack.structured_memory.compressed_memory" in text
    assert "pinned" in text.lower(), "§4.1 must declare the path pinned"
    # The previously-considered alternative form must not appear anywhere.
    assert "x.klickd.<pack>.structured_memory.compressed_memory" not in text, (
        "alternative mount path must be removed (parent audit pinned the path)"
    )


def test_rfc010_does_not_require_rfc009_kind_enum_change():
    text = RFC_PATH.read_text(encoding="utf-8")
    # RFC-010 must record erasure on the fact pointer, NOT by adding a new
    # value to RFC-009 §10's `kind` enum.
    assert "erasure_status" in text and "cascade_purged" in text
    # Old wording that proposed a kind: "evidence_removed" addition must be
    # gone.
    assert 'kind: "evidence_removed"' not in text
    assert '"evidence_removed"' not in text


def test_rfc010_extractor_is_hardened():
    text = RFC_PATH.read_text(encoding="utf-8")
    # The new extractor must declare a kind enum, an x.klickd/host/ prefixed
    # agent_ref, a semver-shaped version, and an attestation_hash rule.
    for needle in (
        '"kind"',
        "host_skill",
        "local_runtime",
        "verified_bridge",
        "x.klickd/host/",
        "attestation_hash",
    ):
        assert needle in text, f"extractor hardening missing in RFC: '{needle}'"


def test_rfc010_example_mounts_at_recommended_path():
    data = json.loads(EXAMPLE_PATH.read_text(encoding="utf-8"))
    pack = data.get("x_klickd_pack")
    assert isinstance(pack, dict), "example missing x_klickd_pack root"
    sm = pack.get("structured_memory")
    assert isinstance(sm, dict), "example missing structured_memory"
    cm = sm.get("compressed_memory")
    assert isinstance(cm, dict), "example missing compressed_memory"
    assert cm.get("version") == "rfc-010-draft"
    assert cm["retrieval_policy"]["host_side_only"] is True
    assert cm["vector_index"]["inline_embeddings_forbidden"] is True
    assert cm["erasure_cascade"]["on_user_request"] == "cascade_purge"
    for fp in cm["fact_pointers"]:
        assert "evidence_uri" in fp and "evidence_hash" in fp, (
            "fact pointers must be pointer-only (uri + hash)"
        )
        assert not fp["evidence_uri"].startswith("data:"), (
            "inline data: URIs forbidden in fact pointers (§5.2)"
        )
        assert fp.get("erasure_status") in ("active", "cascade_purged"), (
            "every fact_pointer must declare erasure_status"
        )


def test_rfc010_example_extractor_is_hardened():
    data = json.loads(EXAMPLE_PATH.read_text(encoding="utf-8"))
    extractor = data["x_klickd_pack"]["structured_memory"]["compressed_memory"][
        "derived_from"
    ]["extractor"]
    assert extractor["kind"] in {"host_skill", "local_runtime", "verified_bridge"}
    assert extractor["agent_ref"].startswith("x.klickd/host/"), (
        "agent_ref must be x.klickd/host/-prefixed (no arbitrary external URL)"
    )
    # Semver-ish version
    assert re.match(r"^[0-9]+\.[0-9]+\.[0-9]+", extractor["version"])
    # When automated extraction, attestation_hash must be set and prefixed with
    # a recognised algo.
    if extractor["kind"] in {"host_skill", "verified_bridge"}:
        att = extractor.get("attestation_hash")
        assert isinstance(att, str) and (
            att.startswith("sha256:") or att.startswith("blake3:")
        ), "attestation_hash required + algo-prefixed for automated extraction"


def test_rfc010_listed_in_rfc_index_as_v42_draft():
    text = RFC_INDEX.read_text(encoding="utf-8")
    assert "RFC-010" in text or "010" in text, "RFC-010 row missing from RFC index"
    pattern = re.compile(
        r"010.*pack[_ -]?memory[_ -]?compression.*v4\.2.*draft",
        re.IGNORECASE | re.DOTALL,
    )
    assert pattern.search(text), (
        "RFC index must list RFC-010 as v4.2 Draft (target + status visible on the row)"
    )


def test_rfc010_is_non_release_in_text():
    text = RFC_PATH.read_text(encoding="utf-8")
    for explicit in (
        "**No** tag",
        "**No** `latest` on npm",
        "**No** Zenodo",
        "**No** GitHub Release",
        "**No** IANA",
        "**No** site exposure",
    ):
        assert explicit in text, f"RFC-010 must explicitly state '{explicit}'"


# --- RFC-010 `compressed_memory` injected into all 42 x.klickd v4.1 skills ---
#
# The 42 candidate skill artefacts under examples/v4.1/x-klickd-skills/{lite,pro}
# carry an RFC-010 `compressed_memory` draft/preview block under the pinned
# path `x_klickd_pack.structured_memory.compressed_memory`. The block is
# NON-NORMATIVE / NON-GA. The tests below pin the invariants:
#
#   - presence in every artefact
#   - draft-preview markers
#   - empty fact_pointers / entity_links / graph_refs (skill templates)
#   - pointer-only, host-side-only, no inline embeddings
#   - hardened extractor (kind, x.klickd/host/ prefix, semver, attestation)
#   - GDPR Art.17 erasure cascade
#   - memory_recall_injection gate
#   - role-specific retrieval scope (no two skills share an identical
#     `_draft_retrieval_scope` or identical tag set)


def _skill_paths():
    lite = sorted((FROZEN_V41_DIR / "lite").glob("*.klickd"))
    pro = sorted((FROZEN_V41_DIR / "pro").glob("*.klickd"))
    return lite, pro


def _cm(path):
    obj = json.loads(path.read_text(encoding="utf-8"))
    return ((obj.get("x_klickd_pack") or {}).get("structured_memory") or {}).get(
        "compressed_memory"
    )


def test_every_v41_skill_has_compressed_memory_block():
    lite, pro = _skill_paths()
    assert len(lite) + len(pro) == 42
    missing = [p.name for p in lite + pro if not isinstance(_cm(p), dict)]
    assert not missing, f"compressed_memory missing in: {missing}"


def test_every_skill_block_is_draft_preview():
    lite, pro = _skill_paths()
    for p in lite + pro:
        cm = _cm(p)
        assert cm["version"] == "rfc-010-draft", p.name
        assert cm["_non_normative"] is True, p.name
        assert cm["_claims_v41_ga"] is False, p.name


def test_every_skill_block_has_empty_pointer_arrays():
    """Skill templates carry no carrier facts. Pointer arrays MUST be empty."""
    lite, pro = _skill_paths()
    for p in lite + pro:
        cm = _cm(p)
        for k in ("fact_pointers", "entity_links", "graph_refs"):
            v = cm.get(k)
            assert isinstance(v, list) and v == [], (
                f"{p.name}: {k} must be []; got {v!r}"
            )


def test_every_skill_extractor_is_hardened():
    lite, pro = _skill_paths()
    semver = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+(?:-[A-Za-z0-9.+-]+)?$")
    hashre = re.compile(r"^(?:sha256|blake3):[A-Fa-f0-9]{32,}$")
    for p in lite + pro:
        cm = _cm(p)
        ex = cm["derived_from"]["extractor"]
        assert ex["kind"] in {"host_skill", "local_runtime", "verified_bridge"}, p.name
        assert ex["agent_ref"].startswith("x.klickd/host/"), p.name
        assert semver.match(ex["version"]), (p.name, ex["version"])
        if ex["kind"] in {"host_skill", "verified_bridge"}:
            assert hashre.match(ex["attestation_hash"]), (p.name, ex["attestation_hash"])


def test_every_skill_block_is_pointer_only_host_side_only():
    lite, pro = _skill_paths()
    for p in lite + pro:
        cm = _cm(p)
        assert cm["vector_index"]["inline_embeddings_forbidden"] is True, p.name
        assert not cm["vector_index"]["uri"].startswith("data:"), p.name
        assert cm["retrieval_policy"]["host_side_only"] is True, p.name
        assert (
            cm["retrieval_policy"]["require_gate"] == "memory_recall_injection"
        ), p.name


def test_every_skill_block_has_art17_erasure_cascade():
    lite, pro = _skill_paths()
    for p in lite + pro:
        cm = _cm(p)
        ec = cm["erasure_cascade"]
        assert ec["on_user_request"] == "cascade_purge", p.name
        assert ec["on_evidence_deletion"] in {"cascade_purge", "tombstone_only"}, p.name
        assert isinstance(ec["targets"], list) and ec["targets"], p.name


def test_every_skill_block_carries_memory_recall_injection_gate():
    lite, pro = _skill_paths()
    for p in lite + pro:
        cm = _cm(p)
        gates = cm["gate_refs"]
        assert any(
            g.get("action_class") == "memory_recall_injection" for g in gates
        ), p.name


def test_pack_id_matches_compressed_memory_derived_from_pack():
    lite, pro = _skill_paths()
    for p in lite + pro:
        obj = json.loads(p.read_text(encoding="utf-8"))
        pack_id = obj["x_klickd_pack"]["pack"]
        cm_pack = _cm(p)["derived_from"]["pack"]
        assert pack_id == cm_pack, (p.name, pack_id, cm_pack)


def test_no_two_skills_share_identical_compressed_memory_block():
    """Each skill block must differ — at minimum in `derived_from.pack`
    and `vector_index.uri`. The byte hash of the block must therefore be
    unique across all 42 skills."""
    import hashlib

    lite, pro = _skill_paths()
    digests: dict[str, list[str]] = {}
    for p in lite + pro:
        cm = _cm(p)
        h = hashlib.sha256(
            json.dumps(cm, sort_keys=True, ensure_ascii=False).encode("utf-8")
        ).hexdigest()
        digests.setdefault(h, []).append(p.name)
    clones = {h: files for h, files in digests.items() if len(files) > 1}
    assert not clones, f"copy-paste compressed_memory blocks: {clones}"


def test_no_two_skills_share_identical_retrieval_tag_set():
    """RFC-010 retrieval scope must be role-specific. The
    `_draft_retrieval_scope.tags` field MUST differ across the 42
    skills — no copy-paste retrieval tag vocabulary."""
    lite, pro = _skill_paths()
    tag_sets: dict[tuple, list[str]] = {}
    for p in lite + pro:
        cm = _cm(p)
        scope = cm.get("_draft_retrieval_scope") or {}
        tags = tuple(sorted(scope.get("tags") or []))
        assert tags, f"{p.name}: _draft_retrieval_scope.tags must be non-empty"
        tag_sets.setdefault(tags, []).append(p.name)
    dupes = {t: files for t, files in tag_sets.items() if len(files) > 1}
    assert not dupes, f"identical retrieval tag sets across skills: {dupes}"


def test_no_two_skills_share_identical_full_retrieval_scope():
    """The full retrieval scope tuple (tags + entity_classes + priority +
    top_k + max_facts_per_turn + freshness_weighting + dim) MUST be
    unique across the 42 skills."""
    lite, pro = _skill_paths()
    scopes: dict[tuple, list[str]] = {}
    for p in lite + pro:
        cm = _cm(p)
        scope = cm.get("_draft_retrieval_scope") or {}
        rp = cm["retrieval_policy"]
        vi = cm["vector_index"]
        key = (
            tuple(sorted(scope.get("tags") or [])),
            tuple(sorted(scope.get("entity_classes") or [])),
            scope.get("priority"),
            rp["top_k"],
            rp["max_facts_per_turn"],
            rp["freshness_weighting"],
            vi["dim"],
        )
        scopes.setdefault(key, []).append(p.name)
    dupes = {k: files for k, files in scopes.items() if len(files) > 1}
    assert not dupes, f"identical retrieval scope tuples across skills: {dupes}"


def test_no_skill_block_contains_extraction_logic():
    """RFC-010 §5.4: extraction prompts, scoring functions, regex
    mining patterns, etc. MUST NOT live inside the pack. The block
    is state, not behaviour."""
    lite, pro = _skill_paths()
    forbidden_keys = (
        "extraction_prompt",
        "extractor_prompt",
        "scoring_function",
        "scoring_code",
        "prompt_template",
    )
    for p in lite + pro:
        cm = _cm(p)
        body = json.dumps(cm).lower()
        for fk in forbidden_keys:
            assert fk not in body, f"{p.name}: contains forbidden '{fk}'"


def test_no_skill_block_claims_third_party_compatibility():
    """RFC-010 §2 anti-copy: no compressed_memory block may claim
    Mem0 / GraphRAG / Letta / MemGPT / Zep / A-MEM compatibility."""
    lite, pro = _skill_paths()
    for p in lite + pro:
        body = json.dumps(_cm(p)).lower()
        for sys_name in ("mem0", "graphrag", "letta", "memgpt", "zep", "a-mem", "amem"):
            for needle in (
                f"{sys_name} compatible",
                f"{sys_name}-compatible",
                f"compatible with {sys_name}",
            ):
                assert needle not in body, f"{p.name}: claims '{needle}'"


def test_validator_enforces_rfc010_invariants():
    """The repo validator MUST expose the RFC-010 invariant functions
    and they MUST be wired into the main validation run."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "x_validator",
        REPO_ROOT / "scripts" / "validate_v4_1_candidate_mapping.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert hasattr(mod, "validate_rfc010_blocks_in_artefacts")
    assert hasattr(mod, "validate_rfc010_retrieval_scope_unique")
    assert not mod.validate_rfc010_blocks_in_artefacts()
    assert not mod.validate_rfc010_retrieval_scope_unique()
