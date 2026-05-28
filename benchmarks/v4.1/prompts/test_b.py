"""Prompt builders for Test B (memory-level) conditions.

Test B evaluates how a model handles cross-session memory under four
conditions:

    no_memory          — no prior session context provided.
    prompt_history     — the full prior turn history is prepended.
    xklickd_compressed — compressed RFC-010 reference context is prepended.
    mem0               — Mem0-shaped context block; only emitted when a
                         local Mem0 install / MEM0_API_KEY is detected.
                         This harness makes NO Mem0 compatibility claim.
                         The block is a deterministic placeholder; we never
                         call Mem0 at benchmark time.

Fairness requirement: across the conditions for a given (user, session),
the final user probe is identical and generation config is identical.
The ONLY difference is the prepended memory-context block.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

from ..reference_runtime.rfc010_reference import (
    MemoryStore,
    build_injection_context,
    extract_facts,
)

TEST_B_BASE_CONDITIONS = (
    "no_memory",
    "prompt_history",
    "xklickd_compressed",
)
TEST_B_MEM0_CONDITION = "mem0"
TEST_B_MEM0_SKIPPED = "mem0_skipped"

SYSTEM_PROMPT_B = (
    "You are a careful, concise assistant for a memory-evaluation "
    "benchmark. The user will ask about prior sessions. Answer directly "
    "from the context you are given. Do not fabricate facts, citations, "
    "or session numbers; if a fact is not in the provided context, say "
    "so plainly."
)

_HISTORY_HEADER = "## Prior session history\n"
_MEM0_HEADER = (
    "## Mem0-shaped placeholder context (no compatibility claim)\n"
    "This block is a deterministic placeholder. The harness does not call "
    "Mem0 at benchmark time and asserts no compatibility with any Mem0 "
    "release.\n"
)


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


def _prior_sessions(sessions: list[dict[str, Any]],
                    target_session_index: int) -> list[dict[str, Any]]:
    """Return sessions strictly before the target, ordered by session_index."""
    return sorted(
        (s for s in sessions if s.get("session_index", -1) < target_session_index),
        key=lambda s: s["session_index"],
    )


def _final_probe(session: dict[str, Any]) -> str:
    """Pick the deterministic probe question used as the user prompt.

    Prefer a ``recall`` probe (most diagnostic of memory). Fall back to
    the first probe of any kind, and finally to the last user turn.
    """
    for kind in ("recall", "temporal_order", "contradiction", "false_memory"):
        for probe in session.get("probes", []) or []:
            if probe.get("kind") == kind and probe.get("question"):
                return str(probe["question"])
            if probe.get("kind") == kind and probe.get("false_fact"):
                return f"Earlier you claimed: {probe['false_fact']} Is that accurate?"
    for probe in session.get("probes", []) or []:
        if probe.get("question"):
            return str(probe["question"])
    for turn in reversed(session.get("turns", []) or []):
        if turn.get("role") == "user" and turn.get("content"):
            return str(turn["content"])
    return "Recall what we discussed in earlier sessions."


def _format_history_block(prior: list[dict[str, Any]]) -> str:
    if not prior:
        return _HISTORY_HEADER + "(no prior sessions)\n"
    lines = [_HISTORY_HEADER]
    for s in prior:
        idx = s.get("session_index", "?")
        topic = s.get("topic", "(no topic)")
        lines.append(f"### Session {idx} — {topic}")
        for turn in s.get("turns", []) or []:
            role = turn.get("role", "user")
            content = (turn.get("content") or "").strip()
            if content:
                lines.append(f"- {role}: {content}")
    return "\n".join(lines) + "\n"


def _format_compressed_block(prior: list[dict[str, Any]]) -> str:
    store = MemoryStore()
    for s in prior:
        idx = s.get("session_index", 0)
        for turn in s.get("turns", []) or []:
            if turn.get("role") != "user":
                continue
            for fact in extract_facts(
                turn.get("content") or "",
                session_index=idx,
                time_marker=f"t{idx}",
            ):
                store.add(fact)
    return build_injection_context(store.facts, max_tokens=256)


def _format_mem0_block(prior: list[dict[str, Any]]) -> str:
    # Deterministic, non-network placeholder. Mirrors the *shape* of a Mem0
    # context block but contains no API calls and no Mem0-specific data.
    items = []
    for s in prior:
        idx = s.get("session_index", 0)
        topic = s.get("topic", "(no topic)")
        items.append({"session": idx, "topic": topic})
    payload = {
        "_kind": "mem0_placeholder",
        "_compatibility_claim": False,
        "items": items,
    }
    return _MEM0_HEADER + json.dumps(payload, sort_keys=True)


def condition_block(
    condition: str,
    persona: dict[str, Any],
    target_session: dict[str, Any],
    all_sessions: list[dict[str, Any]],
) -> str:
    """Return the condition-specific memory-context block.

    ``all_sessions`` should be every session for the same user (any order).
    """
    target_idx = target_session.get("session_index", 0)
    prior = _prior_sessions(all_sessions, target_idx)
    if condition == "no_memory":
        return ""
    if condition == "prompt_history":
        return _format_history_block(prior)
    if condition == "xklickd_compressed":
        return _format_compressed_block(prior)
    if condition == TEST_B_MEM0_CONDITION:
        return _format_mem0_block(prior)
    if condition == TEST_B_MEM0_SKIPPED:
        # When mem0 is not present we still record the condition (audit
        # treats it as informational); the block is empty so the call is
        # equivalent to no_memory and we never imply compatibility.
        return ""
    raise ValueError(f"unknown Test B condition: {condition}")


def build_test_b_messages(
    *,
    condition: str,
    persona: dict[str, Any],
    target_session: dict[str, Any],
    all_sessions: list[dict[str, Any]],
) -> tuple[str, str]:
    """Return ``(system, user)`` for the requested Test B condition."""
    block = condition_block(condition, persona, target_session, all_sessions)
    system = SYSTEM_PROMPT_B if not block else f"{SYSTEM_PROMPT_B}\n\n{block}"
    user = _final_probe(target_session)
    return system, user


def hash_prompt_b(system: str, user: str) -> str:
    h = hashlib.sha256()
    h.update(system.encode("utf-8"))
    h.update(b"\x1f")
    h.update(user.encode("utf-8"))
    return h.hexdigest()


def test_b_run_id(user_id: str, session_id: str, condition: str) -> str:
    return _hash(f"testb:{user_id}:{session_id}:{condition}")
