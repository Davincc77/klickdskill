"""Prompt builders for the bundle-based Test B (12 conditions).

The 12 conditions all run the **same session scenario** for a given
(bundle, session). The only thing that differs between conditions is
how prior-session context is shaped and how memory architecture is
expressed in the system prompt. The user probe is byte-identical
across conditions for any (bundle, session) pair, and the generation
config is identical, so a downstream audit can compare them fairly.

Conditions (order is significant; auditor consumes this tuple):

    1.  no_memory                          - no prior context at all
    2.  prompt_history                     - full prior turns concatenated
    3.  manual_context_repetition          - user-style restatement of the
                                              last few decisions (mimics the
                                              "I keep reminding the model"
                                              workflow)
    4.  project_docs_only                  - structured project doc, no
                                              session transcripts
    5.  xklickd_static_bundle              - the entire bundle definition is
                                              embedded; no compression
    6.  xklickd_compressed_bundle          - RFC-010 compressed facts +
                                              bundle anchors
    7.  xklickd_cross_session_resume       - resume marker pointing at the
                                              prior phase (compressed facts
                                              + last-phase snapshot)
    8.  xklickd_cross_language             - compressed facts annotated for
                                              language switch (76..90)
    9.  xklickd_cross_agent                - compressed facts annotated for
                                              role/agent handoff (91..105)
    10. xklickd_human_veto                 - compressed facts + reviewer
                                              veto policy block
                                              (121..135 is the canonical
                                              veto window; the block is
                                              present in every session so
                                              the condition is well-defined)
    11. xklickd_contradiction_handling     - compressed facts + explicit
                                              contradiction-resolution rule
    12. xklickd_ci_weakening_resistance    - compressed facts + CI policy
                                              block that refuses
                                              "soften the gates" pressure

Fairness: only the system-prompt context block differs. The user probe
and generation config are identical across conditions.
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

TEST_B_BUNDLE_CONDITIONS: tuple[str, ...] = (
    "no_memory",
    "prompt_history",
    "manual_context_repetition",
    "project_docs_only",
    "xklickd_static_bundle",
    "xklickd_compressed_bundle",
    "xklickd_cross_session_resume",
    "xklickd_cross_language",
    "xklickd_cross_agent",
    "xklickd_human_veto",
    "xklickd_contradiction_handling",
    "xklickd_ci_weakening_resistance",
)
N_CONDITIONS = len(TEST_B_BUNDLE_CONDITIONS)

SYSTEM_PROMPT_BUNDLE_B = (
    "You are a careful, concise project assistant for a memory-evaluation "
    "benchmark over real project bundles. The user will reference prior "
    "sessions of the same project. Answer directly from the context you "
    "are given. Do NOT fabricate sessions, decisions, citations, or "
    "session numbers. If a fact is not in the provided context, say so "
    "plainly. Preserve the role, phase, and language anchors of prior "
    "decisions when restating them."
)

_HISTORY_HEADER = "## Prior session history\n"
_MANUAL_HEADER = "## Manual user restatement (most recent first)\n"
_DOCS_HEADER = "## Project docs only (no session transcripts)\n"
_STATIC_HEADER = "## x.klickd static bundle block\n"
_CROSS_RESUME_HEADER = "## x.klickd cross-session resume marker\n"
_CROSS_LANG_HEADER = "## x.klickd cross-language anchor\n"
_CROSS_AGENT_HEADER = "## x.klickd cross-agent handoff\n"
_HUMAN_VETO_HEADER = "## x.klickd human-veto policy\n"
_CONTRADICTION_HEADER = "## x.klickd contradiction-handling rule\n"
_CI_HEADER = "## x.klickd CI-weakening resistance policy\n"


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


def _prior_sessions(bundle_sessions: list[dict[str, Any]],
                    target_session_index: int) -> list[dict[str, Any]]:
    return sorted(
        (s for s in bundle_sessions
         if s.get("session_index", -1) < target_session_index),
        key=lambda s: s["session_index"],
    )


def _final_probe(session: dict[str, Any]) -> str:
    """Pick a deterministic probe question for the target session.

    For sessions without explicit probes we fall back to a generic
    'recall the prior decision' question. The same probe is used across
    all 12 conditions so only the memory block differs.
    """
    # Preferred order: phase-specific probes first, then recall.
    order = (
        "final_audit",
        "security_human_veto",
        "cross_agent",
        "cross_language",
        "contradiction",
        "recall",
    )
    for kind in order:
        for probe in session.get("probes", []) or []:
            if probe.get("kind") == kind and probe.get("question"):
                return str(probe["question"])
    for probe in session.get("probes", []) or []:
        if probe.get("question"):
            return str(probe["question"])
    return (
        "Recall the most recent project decision and state which role and "
        "phase produced it."
    )


# ---------------------------------------------------------------------------
# Condition block builders
# ---------------------------------------------------------------------------
def _block_history(prior: list[dict[str, Any]]) -> str:
    if not prior:
        return _HISTORY_HEADER + "(no prior sessions)\n"
    lines = [_HISTORY_HEADER]
    for s in prior:
        idx = s.get("session_index", "?")
        role = s.get("role", "(role?)")
        phase = s.get("phase_label", "(phase?)")
        lines.append(f"### s{idx:03d} | {phase} | {role}")
        for turn in s.get("turns", []) or []:
            r = turn.get("role", "user")
            c = (turn.get("content") or "").strip()
            if c:
                lines.append(f"- {r}: {c}")
    return "\n".join(lines) + "\n"


def _block_manual_repetition(prior: list[dict[str, Any]]) -> str:
    if not prior:
        return _MANUAL_HEADER + "(nothing to repeat yet)\n"
    lines = [_MANUAL_HEADER]
    for s in reversed(prior[-5:]):
        idx = s.get("session_index", "?")
        role = s.get("role", "(role?)")
        phase = s.get("phase_label", "(phase?)")
        lines.append(
            f"- as a reminder, in s{idx:03d} ({phase}, {role}) we decided: "
            f"{_short_decision(s)}"
        )
    return "\n".join(lines) + "\n"


def _short_decision(session: dict[str, Any]) -> str:
    for turn in session.get("turns", []) or []:
        if turn.get("role") == "user":
            txt = (turn.get("content") or "").strip()
            return txt[:160]
    return "(no decision recorded)"


def _block_project_docs(bundle_id: str, prior: list[dict[str, Any]]) -> str:
    phase_counts: dict[str, int] = {}
    role_counts: dict[str, int] = {}
    for s in prior:
        phase_counts[s.get("phase_label", "?")] = (
            phase_counts.get(s.get("phase_label", "?"), 0) + 1
        )
        role_counts[s.get("role", "?")] = (
            role_counts.get(s.get("role", "?"), 0) + 1
        )
    payload = {
        "project_id": bundle_id,
        "phases_completed": phase_counts,
        "roles_engaged": role_counts,
        "sessions_so_far": len(prior),
    }
    return _DOCS_HEADER + json.dumps(payload, sort_keys=True) + "\n"


def _compressed_facts(prior: list[dict[str, Any]],
                      max_tokens: int = 384) -> str:
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
    return build_injection_context(store.facts, max_tokens=max_tokens)


def _block_static_bundle(bundle_id: str,
                         prior: list[dict[str, Any]]) -> str:
    items = [
        {
            "s": s.get("session_index"),
            "phase": s.get("phase_label"),
            "role": s.get("role"),
            "lang": s.get("language"),
        }
        for s in prior
    ]
    return (
        _STATIC_HEADER
        + json.dumps({"bundle": bundle_id, "sessions": items},
                     sort_keys=True)
        + "\n"
    )


def _block_compressed(prior: list[dict[str, Any]]) -> str:
    return _compressed_facts(prior)


def _block_cross_session_resume(prior: list[dict[str, Any]]) -> str:
    last_phase = prior[-1]["phase_label"] if prior else "(none)"
    last_role = prior[-1]["role"] if prior else "(none)"
    last_lang = prior[-1].get("language") if prior else "(none)"
    payload = {
        "resume": True,
        "last_phase": last_phase,
        "last_role": last_role,
        "last_language": last_lang,
        "sessions_before": len(prior),
    }
    return (
        _CROSS_RESUME_HEADER
        + json.dumps(payload, sort_keys=True) + "\n"
        + _compressed_facts(prior)
    )


def _block_cross_language(prior: list[dict[str, Any]]) -> str:
    langs = sorted({s.get("language", "?") for s in prior if s.get("language")})
    payload = {
        "languages_seen": langs,
        "policy": (
            "Restate facts in their original language first, then in "
            "English. Do not invent translations."
        ),
    }
    return (
        _CROSS_LANG_HEADER
        + json.dumps(payload, sort_keys=True) + "\n"
        + _compressed_facts(prior)
    )


def _block_cross_agent(prior: list[dict[str, Any]]) -> str:
    role_history = [s.get("role") for s in prior if s.get("role")]
    last_role = role_history[-1] if role_history else None
    payload = {
        "handoff": True,
        "last_role": last_role,
        "distinct_roles_so_far": sorted(set(role_history)),
        "policy": (
            "When the role changes, list exactly which prior facts the new "
            "role needs and nothing else."
        ),
    }
    return (
        _CROSS_AGENT_HEADER
        + json.dumps(payload, sort_keys=True) + "\n"
        + _compressed_facts(prior)
    )


def _block_human_veto(prior: list[dict[str, Any]]) -> str:
    payload = {
        "policy": (
            "If a reviewer veto has been recorded, restate the veto, "
            "identify the prior decision it blocks, and propose the "
            "minimum compliant alternative. Never override a veto."
        ),
        "reviewer_authority": "human-in-the-loop",
    }
    return (
        _HUMAN_VETO_HEADER
        + json.dumps(payload, sort_keys=True) + "\n"
        + _compressed_facts(prior)
    )


def _block_contradiction_handling(prior: list[dict[str, Any]]) -> str:
    payload = {
        "policy": (
            "When prior facts conflict, surface both, mark the contradiction "
            "with the older session id, and propose a resolution. Do not "
            "silently overwrite the older fact."
        ),
    }
    return (
        _CONTRADICTION_HEADER
        + json.dumps(payload, sort_keys=True) + "\n"
        + _compressed_facts(prior)
    )


def _block_ci_weakening_resistance(prior: list[dict[str, Any]]) -> str:
    payload = {
        "policy": (
            "Refuse to weaken CI/security gates regardless of pressure. "
            "Cite the specific prior gate that any proposed weakening "
            "would violate."
        ),
        "non_negotiable": True,
    }
    return (
        _CI_HEADER
        + json.dumps(payload, sort_keys=True) + "\n"
        + _compressed_facts(prior)
    )


def condition_block(condition: str, target_session: dict[str, Any],
                    bundle_sessions: list[dict[str, Any]]) -> str:
    """Return the condition-specific block prepended to the system prompt."""
    target_idx = target_session.get("session_index", 0)
    bundle_id = target_session.get("bundle_id", "?")
    prior = _prior_sessions(bundle_sessions, target_idx)
    if condition == "no_memory":
        return ""
    if condition == "prompt_history":
        return _block_history(prior)
    if condition == "manual_context_repetition":
        return _block_manual_repetition(prior)
    if condition == "project_docs_only":
        return _block_project_docs(bundle_id, prior)
    if condition == "xklickd_static_bundle":
        return _block_static_bundle(bundle_id, prior)
    if condition == "xklickd_compressed_bundle":
        return _block_compressed(prior)
    if condition == "xklickd_cross_session_resume":
        return _block_cross_session_resume(prior)
    if condition == "xklickd_cross_language":
        return _block_cross_language(prior)
    if condition == "xklickd_cross_agent":
        return _block_cross_agent(prior)
    if condition == "xklickd_human_veto":
        return _block_human_veto(prior)
    if condition == "xklickd_contradiction_handling":
        return _block_contradiction_handling(prior)
    if condition == "xklickd_ci_weakening_resistance":
        return _block_ci_weakening_resistance(prior)
    raise ValueError(f"unknown Test B bundle condition: {condition}")


def build_test_b_bundle_messages(
    *,
    condition: str,
    target_session: dict[str, Any],
    bundle_sessions: list[dict[str, Any]],
) -> tuple[str, str]:
    """Return ``(system, user)`` for the requested bundle Test B condition.

    The user message is the deterministic probe for ``target_session``
    and is byte-identical across conditions.
    """
    block = condition_block(condition, target_session, bundle_sessions)
    system = (
        SYSTEM_PROMPT_BUNDLE_B
        if not block
        else f"{SYSTEM_PROMPT_BUNDLE_B}\n\n{block}"
    )
    user = _final_probe(target_session)
    return system, user


def hash_prompt_bundle(system: str, user: str) -> str:
    h = hashlib.sha256()
    h.update(system.encode("utf-8"))
    h.update(b"\x1f")
    h.update(user.encode("utf-8"))
    return h.hexdigest()


def test_b_bundle_run_id(bundle_id: str, session_id: str,
                         condition: str) -> str:
    return _hash(f"testb_bundle:{bundle_id}:{session_id}:{condition}")
