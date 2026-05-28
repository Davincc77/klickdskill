#!/usr/bin/env python3
"""RFC-010 reference runtime — minimal, deterministic, NON-PRODUCTION.

Implements the five primitives required by Test B:
    extract_facts, link_entities, retrieve, build_injection_context, erase

This is a *reference* runtime for benchmarking. It is rule-based, has no
storage backend, and is not intended for production use. The production
implementation lives outside this benchmark harness.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Any

REFERENCE_RUNTIME_TAG = "rfc010-reference/0.1.0-nonprod"


@dataclass
class Fact:
    fact_id: str
    text: str
    entities: list[str] = field(default_factory=list)
    session_index: int = 0
    time_marker: str = ""


@dataclass
class MemoryStore:
    facts: list[Fact] = field(default_factory=list)
    entity_index: dict[str, list[str]] = field(default_factory=dict)

    def add(self, fact: Fact) -> None:
        self.facts.append(fact)
        for ent in fact.entities:
            self.entity_index.setdefault(ent, []).append(fact.fact_id)


_ENTITY_PATTERN = re.compile(r"\bentity_\d{3}\b")


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


def extract_facts(turn_text: str, session_index: int = 0,
                  time_marker: str = "") -> list[Fact]:
    """Rule-based extraction: each sentence becomes a candidate fact."""
    if not turn_text:
        return []
    sentences = re.split(r"(?<=[.!?])\s+", turn_text.strip())
    facts: list[Fact] = []
    for sent in sentences:
        if not sent.strip():
            continue
        entities = list(dict.fromkeys(_ENTITY_PATTERN.findall(sent)))
        fid = _hash(f"{session_index}:{sent}")
        facts.append(Fact(
            fact_id=fid,
            text=sent.strip(),
            entities=entities,
            session_index=session_index,
            time_marker=time_marker or f"t{session_index}",
        ))
    return facts


def link_entities(facts: list[Fact]) -> dict[str, list[str]]:
    """Group fact_ids by entity. Deterministic, no fuzzy matching."""
    index: dict[str, list[str]] = {}
    for f in facts:
        for ent in f.entities:
            index.setdefault(ent, []).append(f.fact_id)
    return index


def retrieve(store: MemoryStore, query: str, k: int = 5) -> list[Fact]:
    """Lexical retrieval: rank by simple token overlap, stable tiebreak by session_index desc."""
    if not query:
        return []
    q_tokens = set(re.findall(r"\w+", query.lower()))
    scored = []
    for f in store.facts:
        f_tokens = set(re.findall(r"\w+", f.text.lower()))
        overlap = len(q_tokens & f_tokens)
        if overlap:
            scored.append((overlap, f.session_index, f))
    scored.sort(key=lambda x: (-x[0], -x[1], x[2].fact_id))
    return [f for _, _, f in scored[:k]]


def build_injection_context(facts: list[Fact], max_tokens: int = 256) -> str:
    """Build a compact, structured context block. Deterministic ordering."""
    if not facts:
        return ""
    lines = [f"<RFC010_REFERENCE tag={REFERENCE_RUNTIME_TAG}>"]
    budget = max_tokens
    for f in sorted(facts, key=lambda x: (x.session_index, x.fact_id)):
        line = f"- [{f.time_marker}] {f.text}"
        approx_tokens = max(1, len(line) // 4)
        if approx_tokens > budget:
            break
        lines.append(line)
        budget -= approx_tokens
    lines.append("</RFC010_REFERENCE>")
    return "\n".join(lines)


def erase(store: MemoryStore, fact_ids: list[str] | None = None,
          entity: str | None = None) -> int:
    """Erase facts by id list or by entity. Returns count erased."""
    before = len(store.facts)
    if fact_ids:
        targets = set(fact_ids)
        store.facts = [f for f in store.facts if f.fact_id not in targets]
    if entity is not None:
        store.facts = [f for f in store.facts if entity not in f.entities]
    # Rebuild entity index.
    store.entity_index = {}
    for f in store.facts:
        for ent in f.entities:
            store.entity_index.setdefault(ent, []).append(f.fact_id)
    return before - len(store.facts)
