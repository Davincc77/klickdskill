#!/usr/bin/env python3
"""Offline logical-diff CLI for x.klickd skill/pack candidates.

This is the supply-chain *logical diff* stage. It compares a previous version
(``--before``) of a skill/pack candidate against a new version (``--after``)
and classifies the changes that *matter* for governance, security and claim
discipline -- not just raw JSON/text line changes.

It is NOT a full end-to-end supply chain and makes no claim of total
automation. It is one tool-backed stage: it produces a deterministic report
that helps a human/agent reviewer decide whether a candidate is acceptable,
needs a premium pass, must be rejected, or requires rollback/deprecation.

Scope of what it understands (semantic, not just textual):

  * governance        -- human_veto / human_authority / gate policy
  * guardrails        -- gate levels (block > confirm > silent), raise_only,
                         claim_grounding_required, non_lowerable_floor
  * memory policy     -- memory_scope / memory_segments[].policy /
                         structured_memory.policy
  * evidence / proofs -- evidence_policy (required_for_claims, pointer_only)
  * claim boundary    -- _pack_metadata.claims_v41_ga / non_normative /
                         contains_real_pii / contains_secrets + banned claim
                         strings introduced anywhere in the after document
  * public/private    -- internal codename leak, encrypted flag downgrade,
                         forbidden_fields removal
  * competencies      -- added/removed competency refs
  * risk              -- risk markers raised

Change classification (per the brief):

  added, removed, changed, unchanged, risk_raised, guardrail_lowered,
  evidence_changed, governance_changed, memory_policy_changed,
  public_boundary_changed, claim_boundary_changed

Exit codes:

  0  no blocking finding
  1  at least one BLOCKING finding (guardrail lowered, claim-boundary
     violation, or public/private-boundary violation)
  2  usage / input error (cannot read or parse an input)

Determinism: the report's ``deterministic_diff_id`` is a sha256 over the
before/after input hashes plus the sorted, normalized findings. It does not
depend on the clock, host, or run order. A ``generated_at`` field, if present,
lives in ``non_deterministic_zone`` and is excluded from every hash.

No network. No provider calls. No paid resources. Standard library only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "supply-chain-diff/0.1"

# --- claim discipline -------------------------------------------------------
# Substrings that must never be *introduced* by a candidate. Matching is
# case-insensitive over the serialized after-document. These mirror the
# repo-wide banned-claim list; introducing any is a claim-boundary violation.
BANNED_CLAIM_SUBSTRINGS = (
    "universal standard",
    "automatic gdpr compliance",
    "automatic gdpr/eu ai act compliance",
    "automatic eu ai act compliance",
    "proven benchmark superiority",
    "benchmark superiority",
    "guaranteed compliance",
)

# Internal codename that must never leak into a candidate artifact.
INTERNAL_CODENAME = "chimera"

# Ordered guardrail strength. Lower index == stronger guardrail. Moving a gate
# to a higher index (weaker) is a guardrail-lowering event.
GATE_LEVEL_ORDER = {"block": 0, "confirm": 1, "silent": 2, "off": 3, "none": 3}


def _read_json(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    return json.loads(data.decode("utf-8"))


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _pack(doc: dict[str, Any]) -> dict[str, Any]:
    """Return the x_klickd_pack body, or the document itself as a fallback."""
    pack = doc.get("x_klickd_pack")
    return pack if isinstance(pack, dict) else doc


def _meta(doc: dict[str, Any]) -> dict[str, Any]:
    meta = doc.get("_pack_metadata")
    return meta if isinstance(meta, dict) else {}


def _gates_by_id(pack: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Flatten verification_gates.gates into {id: gate}."""
    vg = pack.get("verification_gates")
    out: dict[str, dict[str, Any]] = {}
    if isinstance(vg, dict) and isinstance(vg.get("gates"), list):
        for gate in vg["gates"]:
            if isinstance(gate, dict) and gate.get("id"):
                out[str(gate["id"])] = gate
    return out


def _gate_strength(level: Any) -> int:
    return GATE_LEVEL_ORDER.get(str(level).lower(), 1)


def _as_set(value: Any) -> set[str]:
    if isinstance(value, list):
        return {str(v) for v in value}
    return set()


def _finding(
    kind: str,
    path: str,
    *,
    before: Any = None,
    after: Any = None,
    severity: str = "info",
    blocking: bool = False,
    detail: str = "",
) -> dict[str, Any]:
    return {
        "kind": kind,
        "path": path,
        "before": before,
        "after": after,
        "severity": severity,
        "blocking": blocking,
        "detail": detail,
    }


def _diff_gates(
    before_pack: dict[str, Any], after_pack: dict[str, Any]
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    bg = _gates_by_id(before_pack)
    ag = _gates_by_id(after_pack)

    for gid in sorted(set(bg) | set(ag)):
        b = bg.get(gid)
        a = ag.get(gid)
        path = f"verification_gates.gates[{gid}].level"
        if b is not None and a is None:
            # A removed gate is a removed guardrail -> lowering.
            findings.append(
                _finding(
                    "guardrail_lowered",
                    f"verification_gates.gates[{gid}]",
                    before=b.get("level"),
                    after=None,
                    severity="high",
                    blocking=True,
                    detail=f"gate {gid!r} removed",
                )
            )
            continue
        if a is not None and b is None:
            findings.append(
                _finding(
                    "added",
                    f"verification_gates.gates[{gid}]",
                    before=None,
                    after=a.get("level"),
                    severity="info",
                    detail=f"gate {gid!r} added",
                )
            )
            continue
        bl, al = b.get("level"), a.get("level")
        if bl == al:
            continue
        if _gate_strength(al) > _gate_strength(bl):
            findings.append(
                _finding(
                    "guardrail_lowered",
                    path,
                    before=bl,
                    after=al,
                    severity="high",
                    blocking=True,
                    detail=f"gate {gid!r} weakened {bl!r} -> {al!r}",
                )
            )
        else:
            findings.append(
                _finding(
                    "governance_changed",
                    path,
                    before=bl,
                    after=al,
                    severity="info",
                    detail=f"gate {gid!r} strengthened {bl!r} -> {al!r}",
                )
            )
    return findings


def _diff_floor(
    before_pack: dict[str, Any], after_pack: dict[str, Any]
) -> list[dict[str, Any]]:
    """non_lowerable_floor entries must not disappear."""
    findings: list[dict[str, Any]] = []
    bv = before_pack.get("human_veto") or {}
    av = after_pack.get("human_veto") or {}
    b_floor = _as_set(bv.get("non_lowerable_floor"))
    a_floor = _as_set(av.get("non_lowerable_floor"))
    for removed in sorted(b_floor - a_floor):
        findings.append(
            _finding(
                "guardrail_lowered",
                "human_veto.non_lowerable_floor",
                before=removed,
                after=None,
                severity="high",
                blocking=True,
                detail=f"non-lowerable floor entry {removed!r} removed",
            )
        )
    for added in sorted(a_floor - b_floor):
        findings.append(
            _finding(
                "governance_changed",
                "human_veto.non_lowerable_floor",
                before=None,
                after=added,
                severity="info",
                detail=f"floor entry {added!r} added",
            )
        )
    # raise_only must not go true -> false.
    if bv.get("raise_only") is True and av.get("raise_only") is False:
        findings.append(
            _finding(
                "guardrail_lowered",
                "human_veto.raise_only",
                before=True,
                after=False,
                severity="high",
                blocking=True,
                detail="raise_only disabled",
            )
        )

    # gates.verification_gates_default flags.
    bd = (before_pack.get("gates") or {}).get("verification_gates_default") or {}
    ad = (after_pack.get("gates") or {}).get("verification_gates_default") or {}
    for flag in ("raise_only", "claim_grounding_required"):
        if bd.get(flag) is True and ad.get(flag) is False:
            findings.append(
                _finding(
                    "guardrail_lowered",
                    f"gates.verification_gates_default.{flag}",
                    before=True,
                    after=False,
                    severity="high",
                    blocking=True,
                    detail=f"{flag} disabled",
                )
            )
    return findings


def _diff_governance(
    before_pack: dict[str, Any], after_pack: dict[str, Any]
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    ba = before_pack.get("human_authority") or {}
    aa = after_pack.get("human_authority") or {}
    # Final decision must remain human-owned.
    b_owner = ba.get("final_decision_owner")
    a_owner = aa.get("final_decision_owner")
    if b_owner != a_owner:
        lowered = b_owner == "human_carrier" and a_owner != "human_carrier"
        findings.append(
            _finding(
                "guardrail_lowered" if lowered else "governance_changed",
                "human_authority.final_decision_owner",
                before=b_owner,
                after=a_owner,
                severity="high" if lowered else "info",
                blocking=lowered,
                detail="final decision owner changed",
            )
        )
    # agent_role escalation from advisory to autonomous is risk-raising.
    if ba.get("agent_role") != aa.get("agent_role"):
        raised = ba.get("agent_role") == "advisory" and aa.get("agent_role") not in (
            "advisory",
            None,
        )
        findings.append(
            _finding(
                "risk_raised" if raised else "governance_changed",
                "human_authority.agent_role",
                before=ba.get("agent_role"),
                after=aa.get("agent_role"),
                severity="high" if raised else "info",
                blocking=False,
                detail="agent role changed",
            )
        )
    return findings


def _diff_evidence(
    before_pack: dict[str, Any], after_pack: dict[str, Any]
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    be = before_pack.get("evidence_policy") or {}
    ae = after_pack.get("evidence_policy") or {}
    if be == ae:
        return findings
    # Specific weakenings are blocking; other shape changes are just flagged.
    for flag in ("required_for_claims", "pointer_only"):
        if be.get(flag) is True and ae.get(flag) is False:
            findings.append(
                _finding(
                    "guardrail_lowered",
                    f"evidence_policy.{flag}",
                    before=True,
                    after=False,
                    severity="high",
                    blocking=True,
                    detail=f"evidence policy {flag} disabled",
                )
            )
    findings.append(
        _finding(
            "evidence_changed",
            "evidence_policy",
            before=be,
            after=ae,
            severity="medium",
            detail="evidence policy shape changed",
        )
    )
    return findings


def _diff_memory(
    before_pack: dict[str, Any], after_pack: dict[str, Any]
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    if before_pack.get("memory_scope") != after_pack.get("memory_scope"):
        findings.append(
            _finding(
                "memory_policy_changed",
                "memory_scope",
                before=before_pack.get("memory_scope"),
                after=after_pack.get("memory_scope"),
                severity="medium",
                detail="memory scope changed",
            )
        )
    b_seg = {
        s.get("id"): s.get("policy")
        for s in before_pack.get("memory_segments", [])
        if isinstance(s, dict)
    }
    a_seg = {
        s.get("id"): s.get("policy")
        for s in after_pack.get("memory_segments", [])
        if isinstance(s, dict)
    }
    for sid in sorted(set(b_seg) | set(a_seg), key=lambda x: str(x)):
        if b_seg.get(sid) != a_seg.get(sid):
            findings.append(
                _finding(
                    "memory_policy_changed",
                    f"memory_segments[{sid}].policy",
                    before=b_seg.get(sid),
                    after=a_seg.get(sid),
                    severity="medium",
                    detail=f"memory segment {sid!r} policy changed",
                )
            )
    bsm = (before_pack.get("structured_memory") or {}).get("policy")
    asm = (after_pack.get("structured_memory") or {}).get("policy")
    if bsm != asm:
        findings.append(
            _finding(
                "memory_policy_changed",
                "structured_memory.policy",
                before=bsm,
                after=asm,
                severity="medium",
                detail="structured memory policy changed",
            )
        )
    return findings


def _diff_competencies(
    before_pack: dict[str, Any], after_pack: dict[str, Any]
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    b = {
        c.get("competency_ref")
        for c in before_pack.get("competencies", [])
        if isinstance(c, dict) and c.get("competency_ref")
    }
    a = {
        c.get("competency_ref")
        for c in after_pack.get("competencies", [])
        if isinstance(c, dict) and c.get("competency_ref")
    }
    for ref in sorted(a - b):
        findings.append(
            _finding("added", f"competencies[{ref}]", after=ref, detail="competency added")
        )
    for ref in sorted(b - a):
        findings.append(
            _finding(
                "removed", f"competencies[{ref}]", before=ref, detail="competency removed"
            )
        )
    return findings


def _diff_claim_boundary(
    before_doc: dict[str, Any], after_doc: dict[str, Any]
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    bm = _meta(before_doc)
    am = _meta(after_doc)

    # claims_v41_ga flipping false -> true is a claim-boundary violation.
    if bm.get("claims_v41_ga") in (False, None) and am.get("claims_v41_ga") is True:
        findings.append(
            _finding(
                "claim_boundary_changed",
                "_pack_metadata.claims_v41_ga",
                before=bm.get("claims_v41_ga"),
                after=True,
                severity="high",
                blocking=True,
                detail="candidate now claims v4.1 GA",
            )
        )
    # non_normative true -> false escalates a candidate to a normative claim.
    if bm.get("non_normative") is True and am.get("non_normative") is False:
        findings.append(
            _finding(
                "claim_boundary_changed",
                "_pack_metadata.non_normative",
                before=True,
                after=False,
                severity="high",
                blocking=True,
                detail="candidate dropped non_normative flag",
            )
        )

    # Banned claim substrings newly introduced anywhere in the after document.
    after_blob = json.dumps(after_doc, ensure_ascii=False).lower()
    before_blob = json.dumps(before_doc, ensure_ascii=False).lower()
    for needle in BANNED_CLAIM_SUBSTRINGS:
        if needle in after_blob and needle not in before_blob:
            findings.append(
                _finding(
                    "claim_boundary_changed",
                    "document",
                    after=needle,
                    severity="high",
                    blocking=True,
                    detail=f"banned claim introduced: {needle!r}",
                )
            )
    return findings


def _diff_public_boundary(
    before_doc: dict[str, Any], after_doc: dict[str, Any]
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    before_pack = _pack(before_doc)
    after_pack = _pack(after_doc)
    bm = _meta(before_doc)
    am = _meta(after_doc)

    # Internal codename newly leaking into the candidate.
    after_blob = json.dumps(after_doc, ensure_ascii=False).lower()
    before_blob = json.dumps(before_doc, ensure_ascii=False).lower()
    if INTERNAL_CODENAME in after_blob and INTERNAL_CODENAME not in before_blob:
        findings.append(
            _finding(
                "public_boundary_changed",
                "document",
                after=INTERNAL_CODENAME,
                severity="high",
                blocking=True,
                detail="internal codename leaked into candidate",
            )
        )

    # PII / secrets markers flipping false -> true.
    for flag in ("contains_real_pii", "contains_secrets"):
        if bm.get(flag) in (False, None) and am.get(flag) is True:
            findings.append(
                _finding(
                    "public_boundary_changed",
                    f"_pack_metadata.{flag}",
                    before=bm.get(flag),
                    after=True,
                    severity="high",
                    blocking=True,
                    detail=f"{flag} now true",
                )
            )

    # encrypted true -> false is a confidentiality downgrade.
    if before_doc.get("encrypted") is True and after_doc.get("encrypted") is False:
        findings.append(
            _finding(
                "public_boundary_changed",
                "encrypted",
                before=True,
                after=False,
                severity="high",
                blocking=True,
                detail="encryption flag downgraded",
            )
        )

    # forbidden_fields entries removed weaken the private/public boundary.
    b_ff = _as_set(before_pack.get("forbidden_fields"))
    a_ff = _as_set(after_pack.get("forbidden_fields"))
    for removed in sorted(b_ff - a_ff):
        findings.append(
            _finding(
                "public_boundary_changed",
                "forbidden_fields",
                before=removed,
                after=None,
                severity="high",
                blocking=True,
                detail=f"forbidden_fields entry {removed!r} removed",
            )
        )
    return findings


def _generic_changed(
    before_pack: dict[str, Any], after_pack: dict[str, Any]
) -> list[dict[str, Any]]:
    """Coarse top-level changed/added/removed over pack keys we don't model
    semantically above. Keeps the summary honest without re-flagging the keys
    already covered by dedicated analyzers."""
    covered = {
        "verification_gates",
        "human_veto",
        "human_authority",
        "gates",
        "evidence_policy",
        "memory_scope",
        "memory_segments",
        "structured_memory",
        "competencies",
    }
    findings: list[dict[str, Any]] = []
    keys = sorted((set(before_pack) | set(after_pack)) - covered)
    for k in keys:
        in_b = k in before_pack
        in_a = k in after_pack
        if in_b and not in_a:
            findings.append(_finding("removed", f"x_klickd_pack.{k}", before="<present>"))
        elif in_a and not in_b:
            findings.append(_finding("added", f"x_klickd_pack.{k}", after="<present>"))
        elif before_pack.get(k) != after_pack.get(k):
            findings.append(_finding("changed", f"x_klickd_pack.{k}"))
    return findings


def _normalize_for_hash(finding: dict[str, Any]) -> str:
    return json.dumps(
        {k: finding[k] for k in ("kind", "path", "before", "after", "blocking")},
        sort_keys=True,
        ensure_ascii=False,
        default=str,
    )


def build_report(before_path: Path, after_path: Path) -> dict[str, Any]:
    before_doc = _read_json(before_path)
    after_doc = _read_json(after_path)
    before_pack = _pack(before_doc)
    after_pack = _pack(after_doc)

    findings: list[dict[str, Any]] = []
    findings += _diff_gates(before_pack, after_pack)
    findings += _diff_floor(before_pack, after_pack)
    findings += _diff_governance(before_pack, after_pack)
    findings += _diff_evidence(before_pack, after_pack)
    findings += _diff_memory(before_pack, after_pack)
    findings += _diff_competencies(before_pack, after_pack)
    findings += _diff_claim_boundary(before_doc, after_doc)
    findings += _diff_public_boundary(before_doc, after_doc)
    findings += _generic_changed(before_pack, after_pack)

    # Deterministic ordering: sort by (kind, path, detail).
    findings.sort(key=lambda f: (f["kind"], f["path"], f["detail"]))

    before_hash = _sha256_file(before_path)
    after_hash = _sha256_file(after_path)

    summary: dict[str, int] = {}
    for f in findings:
        summary[f["kind"]] = summary.get(f["kind"], 0) + 1
    if not findings:
        summary["unchanged"] = 1

    blocked = [f for f in findings if f["blocking"]]
    high_risk = [f for f in findings if f["severity"] == "high" and not f["blocking"]]

    diff_id_material = json.dumps(
        {
            "before_hash": before_hash,
            "after_hash": after_hash,
            "findings": [_normalize_for_hash(f) for f in findings],
        },
        sort_keys=True,
        ensure_ascii=False,
    )
    deterministic_diff_id = "sha256:" + hashlib.sha256(
        diff_id_material.encode("utf-8")
    ).hexdigest()

    recommendations = _recommend(blocked, high_risk, findings)

    return {
        "schema_version": SCHEMA_VERSION,
        "before_path": str(before_path),
        "after_path": str(after_path),
        "before_hash": before_hash,
        "after_hash": after_hash,
        "deterministic_diff_id": deterministic_diff_id,
        "summary": dict(sorted(summary.items())),
        "changed_paths": sorted({f["path"] for f in findings if f["kind"] != "unchanged"}),
        "findings": findings,
        "high_risk_findings": high_risk,
        "blocked_findings": blocked,
        "recommendations": recommendations,
        "non_deterministic_zone": {
            "note": (
                "Fields here are excluded from deterministic_diff_id. None are "
                "emitted by default; a generated_at marker may be added by a "
                "caller without affecting the diff id."
            )
        },
    }


def _recommend(
    blocked: list[dict[str, Any]],
    high_risk: list[dict[str, Any]],
    findings: list[dict[str, Any]],
) -> list[str]:
    recs: list[str] = []
    if blocked:
        recs.append("REJECT_OR_ROLLBACK: blocking finding(s) present; do not promote.")
        kinds = sorted({f["kind"] for f in blocked})
        if "guardrail_lowered" in kinds:
            recs.append(
                "guardrail_lowered detected: a non-lowerable safeguard was weakened "
                "or removed. Requires explicit human veto review."
            )
        if "claim_boundary_changed" in kinds:
            recs.append(
                "claim_boundary_changed detected: candidate introduces a claim that "
                "is not proven/bounded. Strip the claim before any further stage."
            )
        if "public_boundary_changed" in kinds:
            recs.append(
                "public_boundary_changed detected: private/internal content or PII/"
                "secrets risk leaking. Quarantine the candidate."
            )
    elif high_risk:
        recs.append(
            "PREMIUM_PASS_REQUIRED: high-risk (non-blocking) changes need human/agent "
            "review before promotion."
        )
    elif findings:
        recs.append("ACCEPTABLE_WITH_REVIEW: only non-critical changes detected.")
    else:
        recs.append("UNCHANGED: no logical change detected between before and after.")
    return recs


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Logical diff between two x.klickd skill/pack candidates."
    )
    parser.add_argument("--before", required=True, help="path to previous version JSON")
    parser.add_argument("--after", required=True, help="path to candidate version JSON")
    parser.add_argument(
        "--out",
        default=None,
        help="optional path to write the deterministic JSON report",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="suppress the report on stdout (still writes --out if given)",
    )
    args = parser.parse_args(argv[1:])

    before_path = Path(args.before)
    after_path = Path(args.after)
    for p in (before_path, after_path):
        if not p.exists():
            print(f"error: input not found: {p}", file=sys.stderr)
            return 2
    try:
        report = build_report(before_path, after_path)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        print(f"error: could not parse input JSON: {exc}", file=sys.stderr)
        return 2

    rendered = json.dumps(report, indent=2, ensure_ascii=False, sort_keys=False)
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(rendered + "\n", encoding="utf-8")
    if not args.quiet:
        print(rendered)

    if report["blocked_findings"]:
        print(
            f"BLOCKED: {len(report['blocked_findings'])} blocking finding(s).",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
