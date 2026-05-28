#!/usr/bin/env python3
"""Inject the RFC-010 `compressed_memory` draft/preview block into every
x.klickd v4.1 candidate skill artefact.

NON-NORMATIVE / NON-RELEASE. The block is mounted at the RFC-010 pinned
path `x_klickd_pack.structured_memory.compressed_memory` (per
docs/rfcs/RFC-010-pack-memory-compression.md §4.1). It declares the
`rfc-010-draft` shape: pointer-only, host-side-only, no inline
embeddings, GDPR Art.17 erasure cascade, `memory_recall_injection` gate.

`fact_pointers`, `entity_links`, and `graph_refs` are emitted EMPTY in
every artefact: these are generic skill templates, not carrier state,
so there are no real per-carrier facts to extract. The block carries
only the *pointer-ready* surface (URIs, schemes, policy, extractor
metadata, erasure semantics).

The block is INTENTIONALLY non-identical across the 42 skills: each
pack contributes its own role-specific retrieval scope (tags,
candidate entity schemes, vector index URI, embedding model ref,
top_k, max_facts_per_turn, freshness weighting). The validator in
scripts/validate_v4_1_candidate_mapping.py is updated in the same PR
to enforce that no two artefacts share an identical retrieval scope.

Idempotent: re-running this script on already-injected artefacts is a
no-op (the existing block is replaced byte-for-byte with the
deterministic re-render so file SHAs stay reproducible).
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ART_ROOT = REPO_ROOT / "examples" / "v4.1" / "x-klickd-skills"
LITE = ART_ROOT / "lite"
PRO = ART_ROOT / "pro"


# Per-pack role-specific retrieval scope. Each entry tunes the
# RFC-010 `compressed_memory` block so no two skills share an
# identical retrieval surface (validator-enforced in this PR).
#
# Fields:
#   tags                 - retrieval tag vocabulary the host MAY use to
#                          filter the vector index. Role-specific; not
#                          carrier PII.
#   entity_schemes       - candidate entity-scheme identifiers the host
#                          SHOULD prefer when resolving entity_links[].
#                          Always a subset / extension of the skill's
#                          declared `frameworks[]`.
#   top_k                - retrieval_policy.top_k.
#   max_facts_per_turn   - retrieval_policy.max_facts_per_turn.
#   freshness            - retrieval_policy.freshness_weighting.
#   dim                  - vector_index.dim. Distinct dims per role
#                          keeps the index URIs disjoint at the model
#                          level.
#   priority             - host-side retrieval priority class
#                          (advisory, role-specific).
PACK_SCOPES: dict[str, dict] = {
    # --- Lite tier (8 packs, user-lambda audience) ---
    "x.klickd/artist": {
        "tags": ["creator", "visual_arts", "portfolio", "originality"],
        "entity_schemes": ["esco", "lifecomp"],
        "top_k": 4, "max_facts_per_turn": 6, "freshness": "linear_recency",
        "dim": 384, "priority": "creative_practice",
    },
    "x.klickd/consumer_rights": {
        "tags": ["consumer", "eu_law", "redress", "complaint", "warranty"],
        "entity_schemes": ["esco", "eu_law_ref"],
        "top_k": 5, "max_facts_per_turn": 6, "freshness": "linear_recency",
        "dim": 512, "priority": "rights_lookup",
    },
    "x.klickd/game_literacy": {
        "tags": ["gaming", "spend_control", "design_pattern", "minor_safety"],
        "entity_schemes": ["esco", "digcomp"],
        "top_k": 4, "max_facts_per_turn": 5, "freshness": "linear_recency",
        "dim": 384, "priority": "literacy_assist",
    },
    "x.klickd/media_planner": {
        "tags": ["media", "audience", "campaign", "channel_mix", "kpi"],
        "entity_schemes": ["esco"],
        "top_k": 5, "max_facts_per_turn": 7, "freshness": "exponential_recency",
        "dim": 512, "priority": "planning_assist",
    },
    "x.klickd/parent_gaming": {
        "tags": ["parenting", "child_safety", "screen_time", "age_rating"],
        "entity_schemes": ["esco", "lifecomp", "digcomp"],
        "top_k": 4, "max_facts_per_turn": 5, "freshness": "linear_recency",
        "dim": 384, "priority": "guardian_assist",
    },
    "x.klickd/social_literacy": {
        "tags": ["social_media", "verification", "disinformation", "consent"],
        "entity_schemes": ["digcomp", "lifecomp"],
        "top_k": 5, "max_facts_per_turn": 6, "freshness": "exponential_recency",
        "dim": 384, "priority": "literacy_assist",
    },
    "x.klickd/streaming_creator": {
        "tags": ["livestream", "creator_economy", "monetisation", "compliance"],
        "entity_schemes": ["esco", "digcomp"],
        "top_k": 5, "max_facts_per_turn": 6, "freshness": "linear_recency",
        "dim": 384, "priority": "creator_practice",
    },
    "x.klickd/work_assistant": {
        "tags": ["work_admin", "scheduling", "email_triage", "documents"],
        "entity_schemes": ["esco", "lifecomp"],
        "top_k": 5, "max_facts_per_turn": 7, "freshness": "linear_recency",
        "dim": 512, "priority": "workflow_assist",
    },

    # --- Pro tier (34 packs, dev/pro audience) ---
    "x.klickd/accounting_operator": {
        "tags": ["accounting", "ledger", "vat", "month_end", "audit_trail"],
        "entity_schemes": ["esco", "sfia"],
        "top_k": 6, "max_facts_per_turn": 8, "freshness": "linear_recency",
        "dim": 768, "priority": "ledger_operation",
    },
    "x.klickd/api_integrator": {
        "tags": ["api", "webhook", "retry", "idempotency", "schema_drift"],
        "entity_schemes": ["esco", "sfia", "onet"],
        "top_k": 7, "max_facts_per_turn": 9, "freshness": "exponential_recency",
        "dim": 768, "priority": "integration_assist",
    },
    "x.klickd/contract_review": {
        "tags": ["contract", "liability_clause", "indemnity", "redline", "term_extraction"],
        "entity_schemes": ["esco", "eu_law_ref"],
        "top_k": 6, "max_facts_per_turn": 8, "freshness": "none",
        "dim": 768, "priority": "legal_review",
    },
    "x.klickd/customer_support_operator": {
        "tags": ["support", "ticket", "macro", "csat", "escalation"],
        "entity_schemes": ["esco", "sfia"],
        "top_k": 6, "max_facts_per_turn": 8, "freshness": "exponential_recency",
        "dim": 512, "priority": "support_operation",
    },
    "x.klickd/data_analyst": {
        "tags": ["sql", "metric_definition", "deanonymisation_guard", "dashboard"],
        "entity_schemes": ["esco", "sfia", "onet", "wef"],
        "top_k": 7, "max_facts_per_turn": 9, "freshness": "exponential_recency",
        "dim": 768, "priority": "analytic_assist",
    },
    "x.klickd/devops_operator": {
        "tags": ["devops", "incident", "deploy", "rollback", "observability"],
        "entity_schemes": ["esco", "sfia", "onet"],
        "top_k": 7, "max_facts_per_turn": 9, "freshness": "exponential_recency",
        "dim": 768, "priority": "ops_operation",
    },
    "x.klickd/drone_operator": {
        "tags": ["drone", "easa", "flight_plan", "no_fly_zone", "preflight"],
        "entity_schemes": ["esco", "easa_ref"],
        "top_k": 5, "max_facts_per_turn": 7, "freshness": "linear_recency",
        "dim": 512, "priority": "field_operation",
    },
    "x.klickd/edge_ai_operator": {
        "tags": ["edge_inference", "model_pinning", "latency_budget", "device_fleet"],
        "entity_schemes": ["esco", "sfia", "onet"],
        "top_k": 6, "max_facts_per_turn": 8, "freshness": "exponential_recency",
        "dim": 768, "priority": "ops_operation",
    },
    "x.klickd/eu_ai_act": {
        "tags": ["eu_ai_act", "risk_class", "transparency_obligation", "logging"],
        "entity_schemes": ["esco", "eu_law_ref"],
        "top_k": 6, "max_facts_per_turn": 8, "freshness": "none",
        "dim": 768, "priority": "compliance_lookup",
    },
    "x.klickd/evidence_desk": {
        "tags": ["evidence", "chain_of_custody", "attestation", "verification_artifact"],
        "entity_schemes": ["esco", "sfia"],
        "top_k": 6, "max_facts_per_turn": 8, "freshness": "linear_recency",
        "dim": 768, "priority": "evidence_handling",
    },
    "x.klickd/finance_analyst": {
        "tags": ["finance", "valuation", "scenario", "kpi", "forecast"],
        "entity_schemes": ["esco", "sfia", "onet"],
        "top_k": 7, "max_facts_per_turn": 9, "freshness": "exponential_recency",
        "dim": 768, "priority": "analytic_assist",
    },
    "x.klickd/game_design": {
        "tags": ["game_design", "loop_design", "monetisation_pattern", "balance"],
        "entity_schemes": ["esco", "onet"],
        "top_k": 5, "max_facts_per_turn": 7, "freshness": "linear_recency",
        "dim": 512, "priority": "creative_practice",
    },
    "x.klickd/gdpr_readiness": {
        "tags": ["gdpr", "art17_erasure", "dsar", "lawful_basis", "ropa"],
        "entity_schemes": ["esco", "eu_law_ref"],
        "top_k": 6, "max_facts_per_turn": 8, "freshness": "none",
        "dim": 768, "priority": "compliance_lookup",
    },
    "x.klickd/healthcare_ai_safety_reviewer": {
        "tags": ["healthcare_ai", "clinical_risk", "device_class", "mdr_ivdr"],
        "entity_schemes": ["esco", "eu_law_ref"],
        "top_k": 5, "max_facts_per_turn": 7, "freshness": "none",
        "dim": 768, "priority": "safety_review",
    },
    "x.klickd/identity_access_management": {
        "tags": ["iam", "rbac", "abac", "session_lifecycle", "key_rotation"],
        "entity_schemes": ["esco", "sfia", "nice"],
        "top_k": 6, "max_facts_per_turn": 8, "freshness": "exponential_recency",
        "dim": 768, "priority": "security_operation",
    },
    "x.klickd/learning_designer": {
        "tags": ["instructional_design", "learning_objective", "assessment", "scaffold"],
        "entity_schemes": ["esco", "eqf"],
        "top_k": 6, "max_facts_per_turn": 8, "freshness": "linear_recency",
        "dim": 512, "priority": "design_assist",
    },
    "x.klickd/literature_review": {
        "tags": ["literature", "systematic_review", "prisma", "citation"],
        "entity_schemes": ["esco", "onet"],
        "top_k": 7, "max_facts_per_turn": 9, "freshness": "none",
        "dim": 768, "priority": "research_assist",
    },
    "x.klickd/llm_agent_engineering": {
        "tags": ["agent", "tool_use", "router", "eval_harness", "regression"],
        "entity_schemes": ["esco", "sfia", "onet"],
        "top_k": 7, "max_facts_per_turn": 9, "freshness": "exponential_recency",
        "dim": 768, "priority": "engineering_assist",
    },
    "x.klickd/llm_agent_security": {
        "tags": ["prompt_injection", "jailbreak", "exfiltration", "owasp_llm"],
        "entity_schemes": ["esco", "nice", "enisa_ref"],
        "top_k": 7, "max_facts_per_turn": 9, "freshness": "exponential_recency",
        "dim": 768, "priority": "security_operation",
    },
    "x.klickd/mission_control": {
        "tags": ["mission_control", "task_routing", "agent_orchestration", "audit"],
        "entity_schemes": ["esco", "sfia"],
        "top_k": 6, "max_facts_per_turn": 8, "freshness": "linear_recency",
        "dim": 768, "priority": "orchestration_assist",
    },
    "x.klickd/policy_analyst": {
        "tags": ["policy", "impact_assessment", "stakeholder_map", "scenario"],
        "entity_schemes": ["esco", "eu_law_ref"],
        "top_k": 6, "max_facts_per_turn": 8, "freshness": "linear_recency",
        "dim": 768, "priority": "policy_analysis",
    },
    "x.klickd/privacy_product": {
        "tags": ["privacy_by_design", "consent", "dpia", "data_minimisation"],
        "entity_schemes": ["esco", "eu_law_ref"],
        "top_k": 6, "max_facts_per_turn": 8, "freshness": "linear_recency",
        "dim": 768, "priority": "design_assist",
    },
    "x.klickd/product_manager": {
        "tags": ["product", "discovery", "roadmap", "north_star", "prioritisation"],
        "entity_schemes": ["esco", "sfia", "onet"],
        "top_k": 6, "max_facts_per_turn": 8, "freshness": "exponential_recency",
        "dim": 768, "priority": "planning_assist",
    },
    "x.klickd/project_operator": {
        "tags": ["project", "schedule", "raci", "risk_register", "milestone"],
        "entity_schemes": ["esco", "sfia"],
        "top_k": 6, "max_facts_per_turn": 8, "freshness": "linear_recency",
        "dim": 512, "priority": "delivery_assist",
    },
    "x.klickd/release_engineer": {
        "tags": ["release", "sbom", "sign", "rollback", "supply_chain"],
        "entity_schemes": ["esco", "sfia", "nice"],
        "top_k": 6, "max_facts_per_turn": 8, "freshness": "exponential_recency",
        "dim": 768, "priority": "ops_operation",
    },
    "x.klickd/rights_guard": {
        "tags": ["rights", "copyright", "moral_rights", "license", "takedown"],
        "entity_schemes": ["esco", "eu_law_ref"],
        "top_k": 5, "max_facts_per_turn": 7, "freshness": "none",
        "dim": 512, "priority": "rights_lookup",
    },
    "x.klickd/sales_operator": {
        "tags": ["sales", "pipeline", "discovery_call", "objection", "forecast"],
        "entity_schemes": ["esco", "sfia", "onet"],
        "top_k": 6, "max_facts_per_turn": 8, "freshness": "exponential_recency",
        "dim": 512, "priority": "sales_operation",
    },
    "x.klickd/second_brain": {
        "tags": ["note", "atomic_note", "link", "spaced_review", "weekly_review"],
        "entity_schemes": ["esco", "lifecomp"],
        "top_k": 8, "max_facts_per_turn": 10, "freshness": "exponential_recency",
        "dim": 768, "priority": "personal_research",
    },
    "x.klickd/security_incident_response": {
        "tags": ["incident", "containment", "forensics", "post_mortem", "ttp"],
        "entity_schemes": ["esco", "nice", "enisa_ref"],
        "top_k": 7, "max_facts_per_turn": 9, "freshness": "exponential_recency",
        "dim": 768, "priority": "security_operation",
    },
    "x.klickd/sustainability_analyst": {
        "tags": ["sustainability", "csrd", "scope1", "scope2", "scope3", "esg"],
        "entity_schemes": ["esco", "eu_law_ref"],
        "top_k": 6, "max_facts_per_turn": 8, "freshness": "linear_recency",
        "dim": 768, "priority": "analytic_assist",
    },
    "x.klickd/technical_writer": {
        "tags": ["docs", "style_guide", "diataxis", "release_notes", "api_reference"],
        "entity_schemes": ["esco", "sfia"],
        "top_k": 6, "max_facts_per_turn": 8, "freshness": "linear_recency",
        "dim": 512, "priority": "writing_assist",
    },
    "x.klickd/trust_evidence": {
        "tags": ["trust", "attestation", "sbom", "provenance", "verification_artifact"],
        "entity_schemes": ["esco", "nice"],
        "top_k": 6, "max_facts_per_turn": 8, "freshness": "linear_recency",
        "dim": 768, "priority": "evidence_handling",
    },
    "x.klickd/ux_researcher": {
        "tags": ["ux_research", "interview", "usability_test", "synthesis", "jtbd"],
        "entity_schemes": ["esco", "sfia", "onet"],
        "top_k": 6, "max_facts_per_turn": 8, "freshness": "linear_recency",
        "dim": 512, "priority": "research_assist",
    },
    "x.klickd/video_production_pipeline": {
        "tags": ["video", "edit_decision_list", "color_pipeline", "delivery_spec"],
        "entity_schemes": ["esco", "onet"],
        "top_k": 6, "max_facts_per_turn": 8, "freshness": "linear_recency",
        "dim": 768, "priority": "creative_practice",
    },
}


def _det_hex(seed: str, n: int) -> str:
    """Deterministic hex digest of length `n` from a seed string."""
    h = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    while len(h) < n:
        h += hashlib.sha256(h.encode("utf-8")).hexdigest()
    return h[:n]


def build_compressed_memory(pack_id: str, scope: dict) -> dict:
    """Construct the RFC-010 draft compressed_memory block for `pack_id`.

    Returns an empty-fact_pointers / empty-entity_links / empty-graph_refs
    block: this is a skill template, not carrier state.
    """
    pack_tail = pack_id.rsplit("/", 1)[-1]
    attestation = _det_hex(f"rfc-010|{pack_id}|attestation", 64)
    seed = _det_hex(f"rfc-010|{pack_id}|seed", 32)
    return {
        "version": "rfc-010-draft",
        "_status": "draft_preview",
        "_non_normative": True,
        "_claims_v41_ga": False,
        "_rfc_ref": "docs/rfcs/RFC-010-pack-memory-compression.md",
        "derived_from": {
            "pack": pack_id,
            "slice_path": "structured_memory",
            "extractor": {
                "kind": "host_skill",
                "host": "x.klickd.host.placeholder",
                "agent_ref": "x.klickd/host/memory-extractor",
                "version": "0.1.0-draft",
                "deterministic_seed": f"sha256:{seed}",
                "attestation_hash": f"sha256:{attestation}",
            },
        },
        "fact_pointers": [],
        "entity_links": [],
        "graph_refs": [],
        "vector_index": {
            "uri": f"klickd://vector-index/{pack_tail}/v0-draft",
            "embedding_model_ref": f"klickd-embed-{pack_tail}-2026-v0-placeholder",
            "dim": scope["dim"],
            "inline_embeddings_forbidden": True,
        },
        "retrieval_policy": {
            "top_k": scope["top_k"],
            "max_facts_per_turn": scope["max_facts_per_turn"],
            "freshness_weighting": scope["freshness"],
            "host_side_only": True,
            "require_gate": "memory_recall_injection",
        },
        "_draft_retrieval_scope": {
            "tags": list(scope["tags"]),
            "entity_classes": list(scope["entity_schemes"]),
            "priority": scope["priority"],
            "_note": (
                "Draft / non-normative extension surface. Carries the "
                "pack-role-specific retrieval scope so hosts can route "
                "memory recall by topic. NOT part of any current schema; "
                "see RFC-010 §5 for the normative-intent fragment."
            ),
        },
        "erasure_cascade": {
            "targets": ["fact_pointers", "entity_links", "graph_refs", "vector_index"],
            "on_evidence_deletion": "cascade_purge",
            "on_user_request": "cascade_purge",
            "verification_artifact_ref": None,
        },
        "gate_refs": [
            {
                "gate_name": "compressed_memory_recall",
                "action_class": "memory_recall_injection",
            }
        ],
    }


def inject(path: Path) -> tuple[bool, str]:
    raw = path.read_text(encoding="utf-8")
    obj = json.loads(raw)
    block = obj.get("x_klickd_pack")
    if not isinstance(block, dict):
        return False, "missing x_klickd_pack"
    pack_id = block.get("pack", "")
    scope = PACK_SCOPES.get(pack_id)
    if scope is None:
        return False, f"no PACK_SCOPES entry for {pack_id}"
    sm = block.get("structured_memory")
    if not isinstance(sm, dict):
        return False, "missing structured_memory"
    cm = build_compressed_memory(pack_id, scope)
    sm["compressed_memory"] = cm
    # Stable serialization: 2-space indent + trailing newline (repo
    # convention; preserves byte-for-byte round-trip).
    new_raw = json.dumps(obj, indent=2, ensure_ascii=False) + "\n"
    if new_raw == raw:
        return False, "unchanged"
    path.write_text(new_raw, encoding="utf-8")
    return True, "injected"


def main(argv: list[str]) -> int:
    failures: list[str] = []
    changed: list[str] = []
    for tier_dir in (LITE, PRO):
        for path in sorted(tier_dir.glob("*.klickd")):
            ok, msg = inject(path)
            tag = "CHG" if ok else ("OK " if msg == "unchanged" else "ERR")
            print(f"  {tag}  {path.relative_to(REPO_ROOT)}  {msg}")
            if ok:
                changed.append(str(path.relative_to(REPO_ROOT)))
            if msg.startswith("no PACK_SCOPES") or msg == "missing x_klickd_pack" or msg == "missing structured_memory":
                failures.append(f"{path.name}: {msg}")
    print()
    print(f"changed: {len(changed)}")
    if failures:
        print("FAIL: " + "; ".join(failures), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
