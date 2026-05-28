"""RFC-010 reference runtime: deterministic primitive behavior."""
from __future__ import annotations

from conftest import rfc010


def test_extract_facts_splits_sentences() -> None:
    facts = rfc010.extract_facts("Alpha is one. Beta is two!", session_index=1)
    assert len(facts) == 2
    assert facts[0].session_index == 1
    assert facts[0].time_marker == "t1"


def test_link_entities_indexes() -> None:
    facts = rfc010.extract_facts(
        "Discussing entity_101. Also entity_202 matters. entity_101 again.",
        session_index=0,
    )
    idx = rfc010.link_entities(facts)
    assert "entity_101" in idx
    assert len(idx["entity_101"]) == 2


def test_retrieve_returns_overlap_in_stable_order() -> None:
    store = rfc010.MemoryStore()
    for i, t in enumerate(["alpha beta", "beta gamma", "delta epsilon"]):
        for f in rfc010.extract_facts(t + ".", session_index=i):
            store.add(f)
    hits = rfc010.retrieve(store, "beta", k=5)
    assert len(hits) == 2
    # Same query -> same order.
    hits2 = rfc010.retrieve(store, "beta", k=5)
    assert [h.fact_id for h in hits] == [h.fact_id for h in hits2]


def test_build_injection_context_tagged_nonprod() -> None:
    facts = rfc010.extract_facts("A short fact.", session_index=0)
    ctx = rfc010.build_injection_context(facts)
    assert "rfc010-reference" in ctx
    assert "nonprod" in ctx


def test_erase_by_fact_id() -> None:
    store = rfc010.MemoryStore()
    for f in rfc010.extract_facts("One. Two. Three.", session_index=0):
        store.add(f)
    target = store.facts[0].fact_id
    erased = rfc010.erase(store, fact_ids=[target])
    assert erased == 1
    assert all(f.fact_id != target for f in store.facts)


def test_erase_by_entity() -> None:
    store = rfc010.MemoryStore()
    for f in rfc010.extract_facts("entity_111 is here. entity_222 also.", session_index=0):
        store.add(f)
    erased = rfc010.erase(store, entity="entity_111")
    assert erased >= 1
    for f in store.facts:
        assert "entity_111" not in f.entities
