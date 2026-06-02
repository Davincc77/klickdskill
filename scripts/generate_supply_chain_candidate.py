#!/usr/bin/env python3
"""x.klickd supply-chain — internal candidate skill generator (runner v0.1).

This is the candidate-generation stage of the documented supply-chain pipeline:
the build *runner* that turns a deterministic, config-only `build_request` into
a candidate skill in the INTERNAL v4.2 target shape described in
docs/internal/INTERNAL_SKILL_V4_2_MAPPING.md.

NON-NORMATIVE. Internal only. This runner:
  - produces NO public release, tag, DOI, package, or deploy;
  - does NOT promote any public artefact to v4.2 (public stays v4.1 candidate);
  - does NOT run the premium pass — it only marks where one is required;
  - does NOT invent sources: every source comes from the build_request or a
    referenced source_manifest. Missing domain information is surfaced as a
    `requires_human_premium_pass` flag, never hallucinated.

Anti-mirage contract:
  - The runner emits the v4.2 *target shape* (metadata, competency_architecture,
    memory_system, governance_system, memory_governance, runtime, context_graph,
    interactions, evidence, security, audit, skill_lifecycle, output_contract).
    Emitting the shape is NOT a claim that every lifecycle stage is implemented
    or verified — that is the promotion gate's job, and it stays honest about
    what it has and has not run.
  - A candidate is only "complete enough to promote without human premium pass"
    when no `requires_human_premium_pass` marker is set. The generator never
    fabricates competencies, domain risk, or sources to clear that bar.

Determinism:
  - candidate_id / candidate_hash / run_id are derived ONLY from the canonical
    build_request bytes (+ resolved source manifest bytes when referenced).
    Identical inputs -> identical ids across runs / hosts / clocks.
  - Any clock value (generated_at) is quarantined under non_deterministic_zone
    and excluded from every hash.

CLI:
  python scripts/generate_supply_chain_candidate.py --build-request REQ.json
  python scripts/generate_supply_chain_candidate.py --build-request REQ.json --out cand.json

Exit codes:
  0  candidate generated (may carry requires_human_premium_pass markers)
  1  the build_request is structurally invalid (cannot generate honestly)
  2  usage / I-O error
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = (
    REPO_ROOT / ".internal-skills" / "supply-chain" / "candidates"
)

CANDIDATE_SCHEMA_VERSION = "xklickd.candidate.v0.1"
INTERNAL_TARGET_TRACK = "xklickd_internal_skill_v4_2"

# The 7 foundation (transversal) competency anchors and 12 transversal-flow
# competencies. These are STRUCTURAL anchors (framework-referenced names), not
# fabricated domain knowledge — they are the shared "base transversal core"
# every candidate carries per docs/chimera/V4_1_COMPETENCY_IDENTIFICATION_PROTOCOL.md.
FOUNDATION_COMPETENCIES = (
    "ESCO:S1.transversal_thinking",
    "ESCO:S2.transversal_collaboration",
    "ESCO:S3.transversal_communication",
    "LifeComp:Personal.self_regulation",
    "LifeComp:Social.cooperation",
    "LifeComp:Learning.learning_to_learn",
    "DigComp:transversal.responsible_use",
)
TRANSVERSAL_COMPETENCIES = (
    "WEF:critical_thinking",
    "WEF:problem_solving",
    "WEF:creativity",
    "WEF:adaptability",
    "WEF:ethical_reasoning",
    "ESCO:information_literacy",
    "ESCO:digital_literacy",
    "LifeComp:growth_mindset",
    "LifeComp:empathy",
    "DigComp:information_evaluation",
    "DigComp:data_protection_awareness",
    "DigComp:safety",
)

# Harmonised v4.2 competency_architecture sub-layer names (mapping §3).
COMPETENCY_ARCH_LAYERS = (
    "competency_core",
    "primary_domain_competencies",
    "secondary_domain_competencies",
    "domain_risk_profile",
    "domain_output_requirements",
)

# Canonical interactions flow (mapping §5.1). Stored verbatim so the candidate
# records the intended layer-communication contract, not an invented one.
CANONICAL_FLOW = (
    "user_task",
    "intent_detection",
    "competency_activation",
    "memory_retrieval",
    "context_graph_traversal",
    "evidence_resolution",
    "policy_evaluation",
    "output_contract_check",
    "human_veto_if_required",
    "response_or_action",
    "audit_event",
    "memory_update_candidate",
)

INTERACTION_FLOWS = (
    "task_to_competency_flow",
    "competency_to_memory_flow",
    "memory_to_context_graph_flow",
    "context_graph_to_policy_flow",
    "policy_to_output_contract_flow",
    "output_to_audit_flow",
    "lifecycle_to_runtime_flow",
)

# skill_lifecycle stages (mapping §6). NOT named "supply_chain".
SKILL_LIFECYCLE_STAGES = (
    "build_request",
    "source_manifest",
    "generated_candidate",
    "validation_pipeline",
    "audit_trail_index",
    "determinism_record",
    "logical_diff_report",
    "source_license_report",
    "threat_model_report",
    "benchmark_report",
    "premium_pass_report",
    "promotion_gate",
    "rollback_protocol",
    "deprecation_protocol",
    "release_record",
)

# Banned substrings on the generated output: internal-codename leakage and
# unbounded public claims. Mirrors the audit-stage tripwire. NOTE: the internal
# target-track name itself is allowed only under the explicit `internal_target`
# metadata key (it must not leak into any public-facing field), so we do not ban
# it globally here — the promotion gate's boundary tripwire enforces placement.
BANNED_SUBSTRINGS = (
    "chimera",
    "universal standard",
    "automatic gdpr",
    "automatic eu ai act",
    "benchmark superiority",
    "proven benchmark",
)


class BuildRequestError(RuntimeError):
    """Raised when the build_request cannot be honestly turned into a candidate."""


# --- hashing / canonical helpers --------------------------------------------
def _canonical_bytes(obj: Any) -> bytes:
    return json.dumps(
        obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def _sha256_obj(obj: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical_bytes(obj)).hexdigest()


def _sha256_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return path.name


# --- input loading -----------------------------------------------------------
def load_build_request(path: Path) -> tuple[dict[str, Any], str]:
    if not path.exists():
        raise BuildRequestError(f"build_request not found: {path}")
    text = path.read_text(encoding="utf-8")
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise BuildRequestError(f"build_request is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise BuildRequestError("build_request root must be a JSON object")
    return data, text


def _resolve_sources(
    request: dict[str, Any], request_path: Path
) -> tuple[list[dict[str, Any]], str | None, str | None]:
    """Resolve declared sources from the request and/or a source_manifest.

    Sources come ONLY from the build_request (inline `sources`) or a referenced
    `source_manifest` file. The runner never adds a source of its own. Returns
    (sources, source_manifest_relpath, source_manifest_hash).
    """
    sources: list[dict[str, Any]] = []
    inline = request.get("sources")
    if inline is not None:
        if not isinstance(inline, list):
            raise BuildRequestError("build_request.sources must be a list")
        for i, s in enumerate(inline):
            if not isinstance(s, dict):
                raise BuildRequestError(f"sources[{i}] must be an object")
        sources.extend(inline)

    manifest_rel: str | None = None
    manifest_hash: str | None = None
    ref = request.get("source_manifest")
    if ref:
        manifest_path = (request_path.resolve().parent / str(ref))
        if not manifest_path.exists():
            raise BuildRequestError(
                f"referenced source_manifest not found: {ref}"
            )
        mtext = manifest_path.read_text(encoding="utf-8")
        try:
            mdata = json.loads(mtext)
        except json.JSONDecodeError as exc:
            raise BuildRequestError(
                f"source_manifest is not valid JSON: {exc}"
            ) from exc
        msources = mdata.get("sources")
        if not isinstance(msources, list):
            raise BuildRequestError("source_manifest.sources must be a list")
        for i, s in enumerate(msources):
            if not isinstance(s, dict):
                raise BuildRequestError(
                    f"source_manifest.sources[{i}] must be an object"
                )
        sources.extend(msources)
        manifest_rel = _rel(manifest_path)
        manifest_hash = _sha256_text(mtext)

    return sources, manifest_rel, manifest_hash


# --- candidate assembly ------------------------------------------------------
def _gap(reason: str) -> dict[str, str]:
    return {"requires_human_premium_pass": True, "reason": reason}


def _competency_architecture(
    request: dict[str, Any], gaps: list[str]
) -> dict[str, Any]:
    domain = request.get("domain")
    primary = request.get("primary_domain_competencies")
    secondary = request.get("secondary_domain_competencies") or []

    # Domain competencies MUST come from the request. We never invent them.
    if not primary:
        gaps.append("competency_architecture.primary_domain_competencies")
        primary_block: Any = _gap(
            "no primary domain competencies declared in build_request; "
            "domain expertise must be supplied by a human premium pass, "
            "not generated"
        )
    else:
        if not isinstance(primary, list):
            raise BuildRequestError(
                "primary_domain_competencies must be a list when provided"
            )
        primary_block = list(primary)

    if not isinstance(secondary, list):
        raise BuildRequestError(
            "secondary_domain_competencies must be a list when provided"
        )

    domain_risk = request.get("domain_risk_profile")
    if not domain_risk:
        gaps.append("competency_architecture.domain_risk_profile")
        risk_block: Any = _gap(
            "no domain risk profile declared; domain risk must be assessed by "
            "a human premium pass"
        )
    else:
        risk_block = domain_risk

    domain_out = request.get("domain_output_requirements")
    if not domain_out:
        gaps.append("competency_architecture.domain_output_requirements")
        out_block: Any = _gap(
            "no domain output requirements declared; must be specified by a "
            "human premium pass"
        )
    else:
        out_block = domain_out

    return {
        "competency_core": {
            "foundation_competencies": list(FOUNDATION_COMPETENCIES),
            "transversal_competencies": list(TRANSVERSAL_COMPETENCIES),
            "base_transversal_core": {
                "transversal_refs": list(FOUNDATION_COMPETENCIES),
            },
            "note": (
                "Foundation/transversal anchors are framework-referenced "
                "structural names, not fabricated domain knowledge."
            ),
        },
        "primary_domain_competencies": primary_block,
        "secondary_domain_competencies": list(secondary),
        "domain_risk_profile": risk_block,
        "domain_output_requirements": out_block,
        "harmonized_layers": list(COMPETENCY_ARCH_LAYERS),
        "domain": domain,
    }


def _governance_system(request: dict[str, Any]) -> dict[str, Any]:
    """Governance defaults to the strictest safe posture.

    Where the request under-specifies, we DEFAULT TO SAFE (veto required, no
    auto external action, human final owner) rather than guessing a permissive
    setting. A request may tighten but the runner never loosens below the floor.
    """
    g = request.get("governance") or {}
    sensitive = list((request.get("risk_profile") or {}).get("sensitive_actions") or [])
    return {
        "authority_hierarchy": g.get("authority_hierarchy")
        or ["human_operator", "human_reviewer", "agent"],
        "human_veto": {
            "required": True,
            "lowerable": False,
            "note": "raise-only; not lowerable by an agent",
        },
        "consent_rules": g.get("consent_rules") or [],
        "risk_levels": g.get("risk_levels")
        or ["low", "medium", "high", "critical"],
        "action_gates": g.get("action_gates") or [],
        "non_lowerable_rules": sorted(set(
            list(g.get("non_lowerable_rules") or [])
            + ["no_unsourced_claim", "no_stub_as_loaded_skill"]
        )),
        "escalation_rules": g.get("escalation_rules") or [],
        "approval_lifecycle": ["requested", "granted", "denied", "expired"],
        "revocation_rules": g.get("revocation_rules") or [],
        "policy_conflict_resolution": g.get("policy_conflict_resolution")
        or "strictest_rule_wins",
        "governance_audit": {"emits_to": "audit"},
        # Flat mirror consumed by the threat-model tool (classify()).
        "human_veto_required": True,
        "no_auto_external_action": True,
        "final_decision_owner": "human_operator",
        "_declared_sensitive_actions": sensitive,
    }


def _memory_system(request: dict[str, Any]) -> dict[str, Any]:
    m = request.get("memory") or {}
    writes_long_term = bool(m.get("writes_long_term"))
    return {
        "retrieval": m.get("retrieval") or "scoped_by_active_competency",
        "write_candidates": "subject_to_memory_governance",
        "retention": m.get("retention") or "session_default",
        # Flat mirror for the threat-model tool.
        "writes_long_term": writes_long_term,
        "reads_private_context": bool(m.get("reads_private_context")),
        "promotion_rules": m.get("promotion_rules")
        or (["human_review_required"] if writes_long_term else []),
    }


def _memory_governance() -> dict[str, Any]:
    return {
        "role": "bridge_between_memory_and_governance",
        "every_action_influencing_write_is_governed": True,
        "every_governance_decision_consulting_memory_is_audited": True,
    }


def _runtime(request: dict[str, Any]) -> dict[str, Any]:
    return {
        "loadable_only_if_promoted": True,
        "lifecycle_gates_availability": True,
        "tools": {
            "allowed": list((request.get("tools") or {}).get("allowed") or []),
            "forbidden": sorted(set(
                list((request.get("tools") or {}).get("forbidden") or [])
                + ["publish", "send_email"]
            )),
        },
    }


def _context_graph() -> dict[str, Any]:
    return {
        "node_types": [
            "competency", "memory", "evidence", "policy", "action", "audit",
        ],
        "edge_types": ["scopes", "requires", "creates", "vetoes", "audits"],
        "traversed_by_runtime": True,
    }


def _interactions() -> dict[str, Any]:
    return {
        "flows": list(INTERACTION_FLOWS),
        "canonical_flow": list(CANONICAL_FLOW),
        "human_veto_if_required_lowerable": False,
        "memory_update_is_candidate_only": True,
    }


def _evidence(sources: list[dict[str, Any]], gaps: list[str]) -> dict[str, Any]:
    if not sources:
        gaps.append("evidence.sources")
        return {
            "sources": [],
            "requires_citations": True,
            "status": _gap(
                "no sources declared in build_request or source_manifest; "
                "evidence must be supplied, not invented"
            ),
        }
    return {
        "sources": list(sources),
        "requires_citations": True,
        "source_count": len(sources),
    }


def _security(request: dict[str, Any]) -> dict[str, Any]:
    return {
        "no_secrets_in_candidate": True,
        "no_real_pii_in_candidate": True,
        "private_public_boundary_guarded": True,
        "declared_classification": request.get("classification") or "internal",
    }


def _audit(build_request_hash: str) -> dict[str, Any]:
    return {
        "build_request_hash": build_request_hash,
        "emits_audit_event_per_output": True,
        "audit_trail_stage": "audit_trail_index",
    }


def _skill_lifecycle() -> dict[str, Any]:
    # Records the TARGET lifecycle layout. Stage presence here is structural;
    # it is NOT an assertion that each stage is implemented/verified.
    return {
        "stages": list(SKILL_LIFECYCLE_STAGES),
        "renamed_from": "supply_chain",
        "completeness_claimed": False,
        "note": (
            "Target lifecycle layout only; not an assertion that every stage "
            "is implemented or verified. release_record is an INTERNAL record, "
            "never a public tag/DOI/package/release."
        ),
    }


def _output_contract(request: dict[str, Any]) -> dict[str, Any]:
    oc = request.get("output_contract") or {}
    return {
        "allowed_outputs": list(oc.get("allowed_outputs") or ["text_response"]),
        "forbidden_outputs": sorted(set(
            list(oc.get("forbidden_outputs") or [])
            + ["unsourced_public_claim", "private_to_public"]
        )),
        "required_citations": True,
        "required_uncertainty_markers": True,
        "required_handoff_summary": True,
        "required_audit_event": True,
        "graph_bindings": {
            "creates_action_node": bool(oc.get("creates_action_node")),
            "requires_policy_node": True,
            "requires_evidence_node": True,
            "may_trigger_veto_edge": True,
            "writes_audit_edge": True,
        },
        # Flat mirror for the threat-model tool.
        "requires_citations": True,
        "emits_public_output": bool(oc.get("emits_public_output")),
    }


def build_candidate(
    request: dict[str, Any],
    request_text: str,
    request_path: Path,
) -> dict[str, Any]:
    """Build the candidate skill in the v4.2 internal target shape.

    Deterministic given (request bytes + resolved source manifest bytes).
    """
    skill_id = request.get("skill_id")
    if not skill_id or not isinstance(skill_id, str):
        raise BuildRequestError("build_request.skill_id (string) is required")
    if not request.get("domain"):
        raise BuildRequestError("build_request.domain is required")

    sources, manifest_rel, manifest_hash = _resolve_sources(request, request_path)

    build_request_hash = _sha256_text(request_text)
    # Determinism anchor: id derived ONLY from canonical request + manifest hash.
    id_material = {
        "skill_id": skill_id,
        "build_request_hash": build_request_hash,
        "source_manifest_hash": manifest_hash,
    }
    candidate_id = _sha256_obj(id_material)
    run_id = candidate_id  # one run == one deterministic candidate id

    gaps: list[str] = []

    candidate: dict[str, Any] = {
        "schema_version": CANDIDATE_SCHEMA_VERSION,
        "kind": "xklickd_internal_candidate_skill",
        "non_normative": True,
        "internal_target": {
            "track": INTERNAL_TARGET_TRACK,
            "public_version": "v4.1",
            "note": (
                "Internal v4.2 target shape. NOT a public v4.2 release; public "
                "x.klickd artefacts remain v4.1 candidates."
            ),
        },
        "skill_id": skill_id,
        "domain": request.get("domain"),
        "candidate_id": candidate_id,
        "run_id": run_id,
        "build_request_hash": build_request_hash,
        "source_manifest": manifest_rel,
        "source_manifest_hash": manifest_hash,
        # --- v4.2 target top-level layers (mapping §1) ---
        "metadata": {
            "skill_id": skill_id,
            "domain": request.get("domain"),
            "title": request.get("title") or skill_id,
            "size_tier": request.get("size_tier") or "lite",
            "publisher": request.get("publisher") or "internal",
            "status": "candidate",
        },
        "competency_architecture": _competency_architecture(request, gaps),
        "memory_system": _memory_system(request),
        "governance_system": _governance_system(request),
        "memory_governance": _memory_governance(),
        "runtime": _runtime(request),
        "context_graph": _context_graph(),
        "interactions": _interactions(),
        "evidence": _evidence(sources, gaps),
        "security": _security(request),
        "audit": _audit(build_request_hash),
        "skill_lifecycle": _skill_lifecycle(),
        "output_contract": _output_contract(request),
        # --- threat-model-compatible flat mirrors (classify() reads these) ---
        "risk_profile": request.get("risk_profile")
        or {"default_risk": "low", "sensitive_actions": []},
        "governance": None,  # filled below from governance_system mirror
        "memory": None,      # filled below from memory_system mirror
        "tools": None,       # filled below from runtime mirror
        "sources": list(sources),
    }

    # Wire the flat mirrors the threat-model tool consumes, derived (not
    # duplicated by hand) from the structured layers above.
    gov = candidate["governance_system"]
    candidate["governance"] = {
        "human_veto_required": gov["human_veto_required"],
        "no_auto_external_action": gov["no_auto_external_action"],
        "final_decision_owner": gov["final_decision_owner"],
        "non_lowerable_rules": list(gov["non_lowerable_rules"]),
    }
    mem = candidate["memory_system"]
    candidate["memory"] = {
        "writes_long_term": mem["writes_long_term"],
        "reads_private_context": mem["reads_private_context"],
        "promotion_rules": list(mem["promotion_rules"]),
    }
    candidate["tools"] = {
        "allowed": list(candidate["runtime"]["tools"]["allowed"]),
        "forbidden": list(candidate["runtime"]["tools"]["forbidden"]),
    }

    # Anti-mirage summary: surface (not hide) any premium-pass requirements.
    candidate["premium_pass_status"] = {
        "requires_human_premium_pass": bool(gaps),
        "gaps": sorted(gaps),
        "note": (
            "Missing domain information is surfaced as a gap, never "
            "hallucinated. A clean candidate has an empty gaps list."
        ),
    }

    # candidate_hash over the deterministic core (no clock zone yet present).
    candidate["candidate_hash"] = _sha256_obj(candidate)
    return candidate


def render(candidate: dict[str, Any]) -> str:
    return json.dumps(candidate, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def _scan_banned(text: str) -> list[str]:
    low = text.lower()
    return [s for s in BANNED_SUBSTRINGS if s in low]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Internal x.klickd supply-chain candidate generator "
                    "(v4.2 target shape, non-normative).",
    )
    parser.add_argument(
        "--build-request", required=True,
        help="path to a deterministic build_request JSON",
    )
    parser.add_argument(
        "--out", default=None,
        help="output path for the candidate JSON (default: "
             ".internal-skills/supply-chain/candidates/<skill_id>.json)",
    )
    parser.add_argument(
        "--quiet", action="store_true",
        help="do not print the candidate to stdout",
    )
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    req_path = Path(args.build_request)
    try:
        request, request_text = load_build_request(req_path)
        candidate = build_candidate(request, request_text, req_path)
    except BuildRequestError as exc:
        print(f"FAIL (build_request): {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"FAIL (io): {exc}", file=sys.stderr)
        return 2

    serialized = render(candidate)

    banned = _scan_banned(serialized)
    if banned:
        print(f"FAIL: banned substring(s) in candidate: {banned}", file=sys.stderr)
        return 1

    if args.out:
        out_path = Path(args.out)
    else:
        out_path = DEFAULT_OUT_DIR / f"{candidate['skill_id']}.json"
    try:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(serialized, encoding="utf-8")
    except OSError as exc:
        print(f"FAIL (io): {exc}", file=sys.stderr)
        return 2

    if not args.quiet:
        sys.stdout.write(serialized)
    print(
        f"OK: candidate {candidate['skill_id']} (id {candidate['candidate_id']}, "
        f"premium_pass_required="
        f"{candidate['premium_pass_status']['requires_human_premium_pass']}) "
        f"-> {_rel(out_path)}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
