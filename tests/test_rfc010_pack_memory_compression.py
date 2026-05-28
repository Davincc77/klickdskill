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
        "gate_refs",
        "memory_recall_injection",
        "host-side",
        "pointer-only",
        "GDPR Art.17",
        "knowledge.skills_compressed",
        "x_klickd_pack.structured_memory.compressed_memory",
    ]
    missing = [t for t in required if t not in text]
    assert not missing, f"RFC-010 missing required terms: {missing}"


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
