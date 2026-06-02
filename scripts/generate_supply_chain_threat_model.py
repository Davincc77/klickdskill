#!/usr/bin/env python3
"""Deterministic supply-chain threat-model generator for x.klickd
skill/candidate manifests.

Scope (NON-NORMATIVE, planning / governance tool):
  - Parses a candidate manifest JSON (schema_version `xklickd.candidate.v0.1`,
    or a minimal subset of those keys).
  - Computes a deterministic candidate_hash over the canonical JSON bytes.
  - Classifies threats per category against the candidate's declared
    governance / tools / memory / output_contract / risk_profile.
  - Emits required_mitigations and a deterministic report JSON.
  - Blocks (exit 1) when any unmitigated `critical` or `high` finding is
    present.

What this tool IS:
  - A deterministic, offline, stdlib-only static analyser of a *declared*
    candidate manifest. Same input bytes -> identical report bytes.

What this tool IS NOT (claim boundaries — do NOT widen):
  - It is NOT a security certification.
  - It does NOT establish GDPR or EU AI Act compliance.
  - It does NOT execute, load, or network-scan the candidate.
  - It does NOT prove the candidate is a loaded/executable skill.
  - It makes no benchmark-superiority or universal-standard claim.
  The findings reflect only what the manifest declares about itself.

Threat categories (brief §"classer menaces par catégorie"):
  authority_escalation, human_veto_bypass, tool_boundary_violation,
  memory_poisoning, private_public_leak, evidence_weakening,
  unsourced_claim, unsafe_external_action, irreversible_action,
  compliance_overclaim, stale_or_unlicensed_source_dependency

Severities: low / medium / high / critical

Exit codes:
  0  no blocking finding (no unmitigated high/critical)
  1  at least one unmitigated high/critical finding -> candidate BLOCKED
  2  usage / I/O / parse error

CLI:
  python scripts/generate_supply_chain_threat_model.py \
      --candidate path/to/candidate.json \
      --out .internal-skills/supply-chain/threat-model/report.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "xklickd.threat-model.v0.1"
CANDIDATE_SCHEMA_VERSION = "xklickd.candidate.v0.1"

# Severity ordering for deterministic comparison / sorting.
SEVERITY_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}

# Actions treated as sensitive even if the candidate does not flag them.
# These are the irreversible / externally-visible action classes the brief
# wants gated behind a human veto.
KNOWN_SENSITIVE_ACTIONS = (
    "external_communication",
    "send_email",
    "publish",
    "deploy",
    "file_write",
    "file_delete",
    "payment",
    "network_request",
    "code_execution",
)

# Tool names that perform an external or irreversible action. Used to detect
# tool/action mismatches with the declared governance gates.
EXTERNAL_ACTION_TOOLS = (
    "send_email",
    "publish",
    "deploy",
    "post_webhook",
    "http_post",
    "network_request",
    "payment",
)
IRREVERSIBLE_ACTION_TOOLS = (
    "file_delete",
    "deploy",
    "publish",
    "payment",
    "drop_table",
    "rm",
)

# Substrings that, if present in any declared claim / overclaim field, are
# treated as a compliance / superiority overclaim. Mirrors the public claim
# boundaries we must preserve.
COMPLIANCE_OVERCLAIM_TERMS = (
    "gdpr compliant",
    "gdpr compliance",
    "automatic gdpr",
    "eu ai act compliant",
    "eu ai act compliance",
    "ai act compliant",
    "certified secure",
    "security certified",
    "security certification",
    "universal standard",
    "benchmark superiority",
    "state of the art",
    "best in class",
    "fully automated compliance",
)


def _canonical_bytes(obj: Any) -> bytes:
    """Canonical JSON encoding for hashing: sorted keys, no insignificant
    whitespace, UTF-8. Deterministic for a given logical object."""
    return json.dumps(
        obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def candidate_hash(candidate: dict) -> str:
    """sha256 over the canonical bytes of the candidate object."""
    return "sha256:" + hashlib.sha256(_canonical_bytes(candidate)).hexdigest()


def deterministic_threat_model_id(candidate: dict, threats: list[dict]) -> str:
    """Stable id derived from candidate hash + the sorted finding ids.

    Two runs on the same input produce the same id; a change in any finding
    changes the id. Independent of dict ordering or run time."""
    finding_ids = sorted(t["id"] for t in threats)
    seed = {
        "schema_version": SCHEMA_VERSION,
        "candidate_hash": candidate_hash(candidate),
        "finding_ids": finding_ids,
    }
    return "tmid:" + hashlib.sha256(_canonical_bytes(seed)).hexdigest()[:32]


def _g(candidate: dict, *path: str, default: Any = None) -> Any:
    """Safe nested getter."""
    cur: Any = candidate
    for key in path:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


def _finding(
    category: str,
    severity: str,
    title: str,
    detail: str,
    mitigations: list[str],
    *,
    mitigated: bool = False,
) -> dict:
    """Build a finding with a deterministic id (category + title hash)."""
    fid = "thr:" + hashlib.sha256(
        f"{category}|{title}".encode("utf-8")
    ).hexdigest()[:16]
    return {
        "id": fid,
        "category": category,
        "severity": severity,
        "title": title,
        "detail": detail,
        "required_mitigations": list(mitigations),
        "mitigated": bool(mitigated),
    }


def classify(candidate: dict) -> list[dict]:
    """Return the deterministic list of threat findings for a candidate.

    Each rule is a pure function of declared manifest fields. The output
    order is the rule order below; the caller re-sorts deterministically.
    """
    findings: list[dict] = []

    gov = candidate.get("governance") or {}
    mem = candidate.get("memory") or {}
    tools = candidate.get("tools") or {}
    risk = candidate.get("risk_profile") or {}
    out = candidate.get("output_contract") or {}

    human_veto = bool(gov.get("human_veto_required"))
    no_auto_external = bool(gov.get("no_auto_external_action"))
    non_lowerable = list(gov.get("non_lowerable_rules") or [])

    sensitive_actions = list(risk.get("sensitive_actions") or [])
    allowed_tools = list(tools.get("allowed") or [])
    forbidden_tools = list(tools.get("forbidden") or [])

    declared_sensitive = set(sensitive_actions)
    # Sensitive actions implied by the allowed tool set, even if not declared.
    implied_sensitive = {
        t for t in allowed_tools if t in KNOWN_SENSITIVE_ACTIONS
    }
    effective_sensitive = declared_sensitive | implied_sensitive

    # --- authority_escalation ---
    if gov.get("requests_admin") or gov.get("self_grant_authority"):
        findings.append(_finding(
            "authority_escalation", "critical",
            "Candidate requests elevated/admin authority",
            "governance declares requests_admin/self_grant_authority, which "
            "lets the candidate widen its own authority.",
            ["Remove self-granted authority; authority must be assigned by a "
             "human-owned governance layer, raise-only."],
        ))
    final_owner = str(gov.get("final_decision_owner", "")).lower()
    if final_owner and not final_owner.startswith("human"):
        findings.append(_finding(
            "authority_escalation", "high",
            "Final decision owner is not human",
            f"governance.final_decision_owner='{final_owner}' is not a "
            "human_* value.",
            ["Set final_decision_owner to a human_* role."],
        ))

    # --- human_veto_bypass ---
    if effective_sensitive and not human_veto:
        findings.append(_finding(
            "human_veto_bypass", "critical",
            "Sensitive actions present without human veto",
            "candidate exposes sensitive actions "
            f"{sorted(effective_sensitive)} but governance."
            "human_veto_required is not true.",
            ["Set governance.human_veto_required=true and route every "
             "sensitive action through a raise-only human veto gate."],
        ))
    if gov.get("can_override_veto") or gov.get("veto_optional"):
        findings.append(_finding(
            "human_veto_bypass", "critical",
            "Candidate can override or skip the human veto",
            "governance declares can_override_veto/veto_optional.",
            ["The human veto must be non-overridable (raise-only); remove the "
             "override flag."],
        ))

    # --- tool_boundary_violation ---
    overlap = sorted(set(allowed_tools) & set(forbidden_tools))
    if overlap:
        findings.append(_finding(
            "tool_boundary_violation", "high",
            "Tool appears in both allowed and forbidden lists",
            f"tools allowed and forbidden overlap on {overlap}.",
            ["Resolve the contradiction; a forbidden tool must not be "
             "allowed."],
        ))

    # --- memory_poisoning ---
    writes_long_term = bool(mem.get("writes_long_term"))
    has_promotion_rules = bool(
        mem.get("promotion_rules") or mem.get("write_gate")
    )
    if writes_long_term and not has_promotion_rules:
        findings.append(_finding(
            "memory_poisoning", "high",
            "Long-term memory write without promotion/write gate",
            "memory.writes_long_term is true but no promotion_rules / "
            "write_gate is declared; unreviewed writes can poison memory.",
            ["Declare memory.promotion_rules (human/gate-reviewed) before any "
             "long-term write is persisted."],
        ))

    # --- private_public_leak ---
    reads_private = bool(mem.get("reads_private_context"))
    forbidden_outputs = list(out.get("forbidden_outputs") or [])
    has_public_output = bool(
        out.get("emits_public_output")
        or "publish" in effective_sensitive
        or "external_communication" in effective_sensitive
    )
    if candidate.get("private_public_leak") or _g(
        candidate, "boundaries", "private_to_public_leak"
    ):
        findings.append(_finding(
            "private_public_leak", "critical",
            "Declared private-to-public data leak",
            "candidate flags a private/public boundary leak.",
            ["Eliminate the leak; private context must not cross into public "
             "output without an explicit redaction + human gate."],
        ))
    elif reads_private and has_public_output and (
        "private_to_public" not in forbidden_outputs
        and "unsourced_public_claim" not in forbidden_outputs
    ):
        findings.append(_finding(
            "private_public_leak", "high",
            "Private context readable and public output emitted without "
            "boundary guard",
            "memory.reads_private_context is true and the candidate can emit "
            "public output, but output_contract.forbidden_outputs does not "
            "guard the private->public boundary.",
            ["Add a private->public boundary guard to "
             "output_contract.forbidden_outputs and gate public emission."],
        ))

    # --- evidence_weakening ---
    non_lowerable_lower = {str(r).lower() for r in non_lowerable}
    if candidate.get("lowers_evidence") or gov.get("evidence_optional"):
        findings.append(_finding(
            "evidence_weakening", "high",
            "Candidate weakens or makes evidence optional",
            "candidate declares lowers_evidence / evidence_optional.",
            ["Evidence requirements are non-lowerable; restore the evidence "
             "gate."],
        ))

    # --- unsourced_claim ---
    requires_citations = bool(out.get("requires_citations"))
    if has_public_output and not requires_citations and (
        "no_unsourced_claim" not in non_lowerable_lower
    ):
        findings.append(_finding(
            "unsourced_claim", "high",
            "Public output without required citations",
            "candidate emits public output but "
            "output_contract.requires_citations is not true and no "
            "no_unsourced_claim non-lowerable rule is declared.",
            ["Set output_contract.requires_citations=true or declare the "
             "no_unsourced_claim non-lowerable rule."],
        ))

    # --- unsafe_external_action ---
    external_tools = sorted(set(allowed_tools) & set(EXTERNAL_ACTION_TOOLS))
    if external_tools and not no_auto_external:
        findings.append(_finding(
            "unsafe_external_action", "critical",
            "External-action tool allowed without no-auto-external gate",
            f"candidate allows external-action tool(s) {external_tools} but "
            "governance.no_auto_external_action is not true.",
            ["Set governance.no_auto_external_action=true; external actions "
             "must require an explicit human-gated step."],
        ))

    # --- irreversible_action ---
    irreversible_tools = sorted(
        set(allowed_tools) & set(IRREVERSIBLE_ACTION_TOOLS)
    )
    if irreversible_tools and not human_veto:
        findings.append(_finding(
            "irreversible_action", "high",
            "Irreversible-action tool allowed without human veto",
            f"candidate allows irreversible tool(s) {irreversible_tools} but "
            "human_veto_required is not true.",
            ["Gate irreversible actions behind a raise-only human veto and a "
             "rollback/confirmation step."],
        ))

    # --- compliance_overclaim ---
    claim_texts: list[str] = []
    for key in ("claims", "marketing_claims", "description"):
        v = candidate.get(key)
        if isinstance(v, str):
            claim_texts.append(v)
        elif isinstance(v, list):
            claim_texts.extend(str(x) for x in v)
    joined = "  ".join(claim_texts).lower()
    matched_terms = sorted({t for t in COMPLIANCE_OVERCLAIM_TERMS if t in joined})
    if matched_terms:
        findings.append(_finding(
            "compliance_overclaim", "high",
            "Compliance / superiority overclaim in candidate text",
            f"candidate claim text contains overclaim term(s): "
            f"{matched_terms}.",
            ["Remove the overclaim; this tool establishes neither legal "
             "compliance nor benchmark superiority."],
        ))

    # --- stale_or_unlicensed_source_dependency ---
    sources = candidate.get("sources") or []
    if isinstance(sources, list):
        for src in sources:
            if not isinstance(src, dict):
                continue
            name = str(src.get("name") or src.get("id") or src.get("uri") or "?")
            lic = src.get("license")
            if lic in (None, "", "unknown", "unspecified"):
                findings.append(_finding(
                    "stale_or_unlicensed_source_dependency", "medium",
                    f"Source '{name}' has no resolved license",
                    f"source '{name}' declares no usable license "
                    f"(license={lic!r}).",
                    ["Resolve and record an explicit, compatible license for "
                     "the source before use."],
                ))
            if src.get("stale") is True or src.get("freshness") == "stale":
                findings.append(_finding(
                    "stale_or_unlicensed_source_dependency", "medium",
                    f"Source '{name}' is marked stale",
                    f"source '{name}' is flagged stale.",
                    ["Refresh the source or pin a current, dated revision."],
                ))

    return findings


def build_report(candidate: dict, candidate_path: str) -> dict:
    """Assemble the deterministic threat-model report."""
    threats = classify(candidate)
    # Deterministic ordering: severity desc, then category, then id.
    threats_sorted = sorted(
        threats,
        key=lambda t: (
            -SEVERITY_ORDER.get(t["severity"], 0),
            t["category"],
            t["id"],
        ),
    )

    counts: dict[str, int] = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    by_category: dict[str, int] = {}
    for t in threats_sorted:
        counts[t["severity"]] = counts.get(t["severity"], 0) + 1
        by_category[t["category"]] = by_category.get(t["category"], 0) + 1

    blocked_findings = [
        t for t in threats_sorted
        if t["severity"] in ("high", "critical") and not t["mitigated"]
    ]

    required_mitigations = sorted({
        m for t in threats_sorted for m in t["required_mitigations"]
    })

    recommendations: list[str] = []
    if blocked_findings:
        recommendations.append(
            "Resolve all high/critical findings and re-run before promotion."
        )
    else:
        recommendations.append(
            "No blocking finding from the declared manifest; promotion gate "
            "may proceed to the next pipeline stage (human review still "
            "required)."
        )
    if counts["medium"]:
        recommendations.append(
            "Review medium findings (e.g. source license/freshness) before "
            "promotion."
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "candidate_schema_version": candidate.get(
            "schema_version", CANDIDATE_SCHEMA_VERSION
        ),
        "candidate_path": candidate_path,
        "candidate_id": candidate.get("skill_id"),
        "candidate_hash": candidate_hash(candidate),
        "deterministic_threat_model_id": deterministic_threat_model_id(
            candidate, threats_sorted
        ),
        "summary": {
            "total": len(threats_sorted),
            "by_severity": counts,
            "by_category": dict(sorted(by_category.items())),
            "blocked": len(blocked_findings),
        },
        "threats": threats_sorted,
        "required_mitigations": required_mitigations,
        "blocked_findings": [t["id"] for t in blocked_findings],
        "recommendations": recommendations,
        "non_deterministic_zone": [
            "Human review judgement on each finding.",
            "Runtime behaviour of the candidate once loaded (not executed "
            "here).",
            "External legal/compliance assessment (out of scope; this tool "
            "makes no compliance claim).",
            "Source content drift after the recorded candidate_hash.",
        ],
        "claim_boundaries": {
            "is_security_certification": False,
            "establishes_legal_compliance": False,
            "is_full_automation": False,
            "proves_loaded_executable_skill": False,
            "note": "Findings reflect only what the manifest declares; this "
                    "tool is offline, stdlib-only, and non-normative.",
        },
    }


def render(report: dict) -> str:
    """Deterministic pretty JSON (sorted keys, trailing newline)."""
    return json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Deterministic supply-chain threat-model generator "
                    "for x.klickd candidate manifests (non-normative).",
    )
    parser.add_argument(
        "--candidate", required=True,
        help="Path to candidate/skill manifest JSON.",
    )
    parser.add_argument(
        "--out", default=None,
        help="Path to write the report JSON. If omitted, prints to stdout.",
    )
    parser.add_argument(
        "--no-block", action="store_true",
        help="Report findings but always exit 0 (do not block on "
             "high/critical). Default is to block.",
    )
    args = parser.parse_args(argv[1:])

    cand_path = Path(args.candidate)
    if not cand_path.exists():
        print(f"ERROR: candidate not found: {cand_path}", file=sys.stderr)
        return 2
    try:
        candidate = json.loads(cand_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"ERROR: candidate JSON parse failed: {e}", file=sys.stderr)
        return 2
    if not isinstance(candidate, dict):
        print("ERROR: candidate JSON must be an object", file=sys.stderr)
        return 2

    report = build_report(candidate, str(args.candidate))
    rendered = render(report)

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(rendered, encoding="utf-8")
        print(f"wrote {out_path}")
    else:
        sys.stdout.write(rendered)

    blocked = report["blocked_findings"]
    if blocked and not args.no_block:
        print(
            f"BLOCKED: {len(blocked)} unmitigated high/critical finding(s): "
            f"{blocked}",
            file=sys.stderr,
        )
        return 1
    print(
        f"OK: {report['summary']['total']} finding(s); "
        f"{len(blocked)} blocking.",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
