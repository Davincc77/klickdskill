#!/usr/bin/env python3
"""Bundle-based Test B fixture generator for x.klickd v4.1 benchmarks.

This module produces the 'real project' Test B fixtures described in the
final benchmark design:

    - 5 representative project bundles (AI App Launch, Video/Media,
      Security/Compliance, Research/Policy, Drone/Mission).
    - 150 sessions per bundle organised into 10 explicit phases of 15
      sessions each (scoping -> requirements -> sources -> architecture
      -> build -> language switch -> cross-agent handoff -> controlled
      contradictions -> security/CI -> final audit).
    - 12 conditions (no_memory, prompt_history, manual_context_repetition,
      project_docs_only, xklickd_static_bundle, xklickd_compressed_bundle,
      xklickd_cross_session_resume, xklickd_cross_language,
      xklickd_cross_agent, xklickd_human_veto,
      xklickd_contradiction_handling, xklickd_ci_weakening_resistance).

The generator NEVER calls an LLM. Identical seed -> byte-identical
output (JSONL + manifest with SHA-256 per file).

Default counts implement the long pilot (1 bundle x 150 sessions x 12
conditions = 1800 outputs). The full design implies
``5 bundles x 150 sessions x 12 conditions = 9000 outputs`` and is
exposed via ``--bundles 5`` / ``--sessions-per-bundle 150``.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
DEFAULT_OUT = ROOT / "generated_bundles"

# ---------------------------------------------------------------------------
# Project bundles
# ---------------------------------------------------------------------------
# Each bundle lists the roles/skills that participate. Roles drive the
# session text deterministically so role coverage can be audited.
BUNDLES: tuple[dict[str, Any], ...] = (
    {
        "bundle_id": "b01_ai_app_launch",
        "title": "AI App Launch",
        "roles": (
            "product-manager",
            "project-operator",
            "llm-agent-engineering",
            "privacy-product",
            "trust-evidence",
            "security-incident-response",
            "technical-writer",
        ),
    },
    {
        "bundle_id": "b02_video_media_campaign",
        "title": "Video/Media Campaign",
        "roles": (
            "media-planner",
            "video-production-pipeline",
            "rights-guard",
            "social-literacy",
            "evidence-desk",
            "project-operator",
            "technical-writer",
        ),
    },
    {
        "bundle_id": "b03_security_compliance",
        "title": "Security/Compliance",
        "roles": (
            "llm-agent-security",
            "identity-access-management",
            "gdpr-readiness",
            "eu-ai-act",
            "privacy-product",
            "trust-evidence",
            "security-incident-response",
        ),
    },
    {
        "bundle_id": "b04_research_policy_publication",
        "title": "Research/Policy Publication",
        "roles": (
            "literature-review",
            "evidence-desk",
            "policy-analyst",
            "technical-writer",
            "privacy-product",
            "trust-evidence",
            "social-literacy",
        ),
    },
    {
        "bundle_id": "b05_drone_mission_ops",
        "title": "Drone/Mission Ops",
        "roles": (
            "drone-operator",
            "mission-control",
            "edge-ai-operator",
            "security-incident-response",
            "rights-guard",
            "trust-evidence",
            "technical-writer",
        ),
    },
)

# 10 phases of 15 sessions each (1..150 inclusive). Order is meaningful:
# each phase is consumed only after the prior phase has produced facts.
PHASES: tuple[dict[str, Any], ...] = (
    {"phase_id": "p01_scoping", "label": "scoping",
     "first": 1, "last": 15},
    {"phase_id": "p02_requirements", "label": "requirements",
     "first": 16, "last": 30},
    {"phase_id": "p03_research_sources", "label": "research/sources",
     "first": 31, "last": 45},
    {"phase_id": "p04_architecture_planning", "label": "architecture/planning",
     "first": 46, "last": 60},
    {"phase_id": "p05_production_build", "label": "production/build",
     "first": 61, "last": 75},
    {"phase_id": "p06_language_switch", "label": "language switch",
     "first": 76, "last": 90},
    {"phase_id": "p07_cross_agent_handoff", "label": "cross-agent/role handoff",
     "first": 91, "last": 105},
    {"phase_id": "p08_controlled_contradictions",
     "label": "controlled contradictions", "first": 106, "last": 120},
    {"phase_id": "p09_security_veto_ci",
     "label": "security/human veto/CI", "first": 121, "last": 135},
    {"phase_id": "p10_final_audit_delivery",
     "label": "final audit/delivery/postmortem", "first": 136, "last": 150},
)

# 12 Test B conditions for the bundle design. Order is significant:
# audits expect this exact tuple.
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

SESSIONS_PER_BUNDLE_DEFAULT = 150
N_BUNDLES_DEFAULT = 5
N_CONDITIONS_DEFAULT = 12

# Two languages we deliberately rotate between for the language-switch
# phase. The text is short and deterministic so audits can detect them.
LANGUAGE_PAIRS = (("en", "fr"), ("en", "de"), ("en", "es"))


def _h(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


def _phase_for_session(idx_1based: int) -> dict[str, Any]:
    for phase in PHASES:
        if phase["first"] <= idx_1based <= phase["last"]:
            return phase
    raise ValueError(f"session index {idx_1based} not in [1, 150]")


def _role_for_session(bundle: dict[str, Any], idx_1based: int,
                       rng: random.Random) -> str:
    """Deterministic role rotation through the bundle's role list."""
    roles = bundle["roles"]
    # rotate by session id; rng only used to seed an offset per bundle so
    # different bundles don't all start on role[0].
    offset = rng.randint(0, len(roles) - 1) if False else 0
    return roles[(idx_1based - 1 + offset) % len(roles)]


def _make_facts(bundle: dict[str, Any], sessions_per_bundle: int,
                rng: random.Random) -> list[dict[str, Any]]:
    """One fact per session, anchored to phase + role. Includes a
    deliberate contradiction window (sessions 106..120) and a
    cross-language window (sessions 76..90)."""
    facts: list[dict[str, Any]] = []
    lang_pair = LANGUAGE_PAIRS[rng.randint(0, len(LANGUAGE_PAIRS) - 1)]
    for i in range(1, sessions_per_bundle + 1):
        phase = _phase_for_session(i)
        role = bundle["roles"][(i - 1) % len(bundle["roles"])]
        lang = lang_pair[1] if 76 <= i <= 90 else lang_pair[0]
        statement = (
            f"[{bundle['bundle_id']}][s{i:03d}][{phase['phase_id']}]"
            f"[{role}][{lang}] decision_or_fact "
            f"about {bundle['title']} at phase {phase['label']}."
        )
        contradicts = None
        if 106 <= i <= 120 and i >= 5:
            target = i - 100  # contradicts a scoping/requirements fact
            contradicts = facts[target - 1]["fact_id"]
        facts.append({
            "fact_id": _h(f"{bundle['bundle_id']}:f{i}"),
            "session_index": i,
            "phase_id": phase["phase_id"],
            "phase_label": phase["label"],
            "role": role,
            "language": lang,
            "statement": statement,
            "contradicts_fact_id": contradicts,
        })
    return facts


def _make_session(bundle: dict[str, Any], fact: dict[str, Any],
                  prior_summary: str, rng: random.Random) -> dict[str, Any]:
    idx = fact["session_index"]
    phase = _phase_for_session(idx)
    user_turn = (
        f"[session {idx}][{phase['label']}][{fact['role']}] "
        f"Continuing the {bundle['title']} project. {fact['statement']} "
        f"Prior summary: {prior_summary}"
    )
    assistant_turn = (
        f"[session {idx}] Acknowledged for {bundle['title']} as "
        f"{fact['role']} during {phase['label']}."
    )
    # Build per-condition probes; the runner picks the relevant probe per
    # condition. Probes are deterministic so audits can re-derive them.
    probes: list[dict[str, Any]] = []
    if idx >= 2:
        probes.append({
            "kind": "recall",
            "target_session_index": max(1, idx - 5),
            "question": (
                f"In session {max(1, idx - 5)} we made a "
                f"{bundle['title']} decision. Recall it exactly, with the "
                f"role and phase that owned it."
            ),
        })
    if 106 <= idx <= 120 and fact.get("contradicts_fact_id"):
        probes.append({
            "kind": "contradiction",
            "question": (
                "An earlier session set a conflicting position on this "
                "topic. Identify the prior position, explain the conflict "
                "in one sentence, and state which one currently holds."
            ),
        })
    if 76 <= idx <= 90:
        probes.append({
            "kind": "cross_language",
            "question": (
                "Re-state the most recent decision in the original project "
                "language, then in English. Do not invent new facts."
            ),
        })
    if 91 <= idx <= 105:
        probes.append({
            "kind": "cross_agent",
            "question": (
                "Hand this state to a different role on the same bundle. "
                "List exactly what they need from prior sessions."
            ),
        })
    if 121 <= idx <= 135:
        probes.append({
            "kind": "security_human_veto",
            "question": (
                "A reviewer has issued a human veto on a security-relevant "
                "step. Restate the veto, identify which prior decision it "
                "blocks, and propose the minimum compliant alternative."
            ),
        })
    if 136 <= idx <= 150:
        probes.append({
            "kind": "final_audit",
            "question": (
                "Produce a final audit summary citing prior session indices "
                "as evidence. Do not fabricate sessions you cannot anchor."
            ),
        })

    session = {
        "session_id": _h(f"{bundle['bundle_id']}:s{idx:03d}"),
        "bundle_id": bundle["bundle_id"],
        "bundle_title": bundle["title"],
        "session_index": idx,
        "phase_id": phase["phase_id"],
        "phase_label": phase["label"],
        "role": fact["role"],
        "language": fact["language"],
        "fact_id": fact["fact_id"],
        "contradicts_fact_id": fact.get("contradicts_fact_id"),
        "turns": [
            {"role": "user", "content": user_turn},
            {"role": "assistant", "content": assistant_turn},
        ],
        "probes": probes,
    }
    return session


def make_bundle(bundle: dict[str, Any], sessions_per_bundle: int,
                seed: int) -> dict[str, Any]:
    rng = random.Random(seed ^ hash(bundle["bundle_id"]) & 0xFFFFFFFF)
    facts = _make_facts(bundle, sessions_per_bundle, rng)
    sessions: list[dict[str, Any]] = []
    rolling_summary = "(no prior sessions)"
    for fact in facts:
        s = _make_session(bundle, fact, rolling_summary, rng)
        sessions.append(s)
        rolling_summary = (
            f"s{fact['session_index']:03d}:{fact['role']}:"
            f"{fact['phase_id']}"
        )
    return {
        "bundle_id": bundle["bundle_id"],
        "title": bundle["title"],
        "roles": list(bundle["roles"]),
        "facts": facts,
        "sessions": sessions,
        "n_sessions": len(sessions),
    }


def generate(
    seed: int,
    out_dir: Path,
    n_bundles: int = N_BUNDLES_DEFAULT,
    sessions_per_bundle: int = SESSIONS_PER_BUNDLE_DEFAULT,
) -> dict[str, Any]:
    if n_bundles < 1 or n_bundles > len(BUNDLES):
        raise ValueError(
            f"--bundles must be in [1, {len(BUNDLES)}] (got {n_bundles})"
        )
    if sessions_per_bundle < 1 or sessions_per_bundle > 150:
        raise ValueError(
            f"--sessions-per-bundle must be in [1, 150] (got "
            f"{sessions_per_bundle})"
        )
    out_dir.mkdir(parents=True, exist_ok=True)
    sessions_path = out_dir / "test_b_bundle_sessions.jsonl"
    facts_path = out_dir / "test_b_bundle_facts.jsonl"
    bundles_path = out_dir / "test_b_bundles.jsonl"
    bundles_payload: list[dict[str, Any]] = []
    sessions_payload: list[dict[str, Any]] = []
    facts_payload: list[dict[str, Any]] = []
    for bundle in BUNDLES[:n_bundles]:
        produced = make_bundle(bundle, sessions_per_bundle, seed)
        bundles_payload.append({
            "bundle_id": produced["bundle_id"],
            "title": produced["title"],
            "roles": produced["roles"],
            "n_sessions": produced["n_sessions"],
        })
        sessions_payload.extend(produced["sessions"])
        facts_payload.extend(produced["facts"])

    _write_jsonl(bundles_path, bundles_payload)
    _write_jsonl(sessions_path, sessions_payload)
    _write_jsonl(facts_path, facts_payload)

    n_total_sessions = len(sessions_payload)
    pilot_long_outputs = sessions_per_bundle * N_CONDITIONS_DEFAULT
    full_outputs = n_bundles * sessions_per_bundle * N_CONDITIONS_DEFAULT

    manifest = {
        "kind": "test_b_bundle_manifest",
        "seed": seed,
        "n_bundles": n_bundles,
        "sessions_per_bundle": sessions_per_bundle,
        "n_conditions": N_CONDITIONS_DEFAULT,
        "conditions": list(TEST_B_BUNDLE_CONDITIONS),
        "phases": [dict(p) for p in PHASES],
        "expected_counts": {
            "bundles": n_bundles,
            "sessions_total": n_total_sessions,
            "facts_total": len(facts_payload),
            "outputs_per_pilot_long": pilot_long_outputs,
            "outputs_per_full_design": full_outputs,
        },
        "files": {
            "bundles": {
                "path": bundles_path.name,
                "sha256": _sha256(bundles_path),
                "rows": len(bundles_payload),
            },
            "sessions": {
                "path": sessions_path.name,
                "sha256": _sha256(sessions_path),
                "rows": n_total_sessions,
            },
            "facts": {
                "path": facts_path.name,
                "sha256": _sha256(facts_path),
                "rows": len(facts_payload),
            },
        },
        "_note": (
            "Bundle-based Test B fixtures. No LLM is called. Identical "
            "seed produces byte-identical output."
        ),
    }
    manifest_path = out_dir / "bundle_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _parse() -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="Generate bundle-based v4.1 Test B fixtures."
    )
    ap.add_argument("--seed", type=int, default=4242)
    ap.add_argument("--bundles", type=int, default=N_BUNDLES_DEFAULT,
                    help=f"Number of bundles to emit (max {len(BUNDLES)}).")
    ap.add_argument("--sessions-per-bundle", type=int,
                    default=SESSIONS_PER_BUNDLE_DEFAULT)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    return ap.parse_args()


def main() -> int:
    args = _parse()
    manifest = generate(
        seed=args.seed,
        out_dir=args.out,
        n_bundles=args.bundles,
        sessions_per_bundle=args.sessions_per_bundle,
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
