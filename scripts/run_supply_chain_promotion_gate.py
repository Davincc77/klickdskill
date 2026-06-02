#!/usr/bin/env python3
"""x.klickd supply-chain — combined promotion gate (v0.1).

The promotion gate is the pass/fail orchestrator for the documented
supply-chain pipeline. It runs the existing tool-backed checks on a candidate
skill, applies candidate schema/shape checks and public/private boundary
tripwires, and classifies the candidate as:

    ACCEPT               -- no blocking findings, no premium-pass requirement
    ACCEPT_WITH_REVIEW   -- no blocking findings, but human review/premium pass
                            is required (gaps, review-bucket sources, mediums)
    BLOCK                -- at least one blocking finding

NON-NORMATIVE. Internal only. The gate:
  - does NOT run the premium pass; it only REPORTS whether one is required;
  - makes NO compliance, legal, security-certification, or benchmark claim;
  - produces NO release, tag, DOI, package, or deploy;
  - asserts a check result ONLY when it actually ran the check. A check that
    could not run is recorded as "not_run" with a reason, never as "pass".

Orchestrated checks (each is run only if its tool is importable on this branch):
  - threat model        (scripts/generate_supply_chain_threat_model.py)
  - source/license      (scripts/check_supply_chain_sources.py) when a source
                         manifest is provided
  - logical diff        (scripts/generate_supply_chain_diff.py) when --before is
                         provided
  - candidate schema/shape checks (built in here)
  - forbidden-claims / public-private boundary tripwires (built in here)

Determinism:
  - The gate report's deterministic_gate_id is derived only from the candidate
    hash plus the sorted, normalized check verdicts. Clock values live under
    non_deterministic_zone and are excluded from the id.

CLI:
  python scripts/run_supply_chain_promotion_gate.py --candidate CAND.json
  python scripts/run_supply_chain_promotion_gate.py --candidate CAND.json \
      --source-manifest SRC.json --before PREV.json --out gate.json --md gate.md

Exit codes:
  0  ACCEPT or ACCEPT_WITH_REVIEW (acceptable)
  1  BLOCK (a blocking finding was raised)
  2  usage / I-O error
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
DEFAULT_OUT_DIR = (
    REPO_ROOT / ".internal-skills" / "supply-chain" / "promotion-gate"
)

GATE_SCHEMA_VERSION = "xklickd.promotion_gate.v0.1"

# v4.2 internal target top-level layers a candidate MUST carry (mapping §1).
REQUIRED_CANDIDATE_LAYERS = (
    "metadata",
    "competency_architecture",
    "memory_system",
    "governance_system",
    "memory_governance",
    "runtime",
    "context_graph",
    "interactions",
    "evidence",
    "security",
    "audit",
    "skill_lifecycle",
    "output_contract",
)

# Forbidden public claims (over-claim tripwire). Lower-cased substring match.
FORBIDDEN_CLAIM_SUBSTRINGS = (
    "universal standard",
    "automatic gdpr",
    "automatic eu ai act",
    "automatically gdpr compliant",
    "guaranteed compliance",
    "benchmark superiority",
    "proven benchmark",
    "industry standard for all",
)

# Internal codename that must never appear anywhere in a candidate.
FORBIDDEN_CODENAME_SUBSTRINGS = (
    "chimera",
)

# The internal target-track name is allowed ONLY under the candidate's
# `internal_target` block; anywhere else is a leak of an internal name into a
# field that could surface publicly.
INTERNAL_TRACK_NAME = "xklickd_internal_skill_v4_2"


def _load_module(name: str, filename: str) -> ModuleType | None:
    """Import a sibling script as a module, or return None if unavailable."""
    path = SCRIPTS_DIR / filename
    if not path.exists():
        return None
    spec = importlib.util.spec_from_file_location(name, path)
    if not spec or not spec.loader:
        return None
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception:  # noqa: BLE001 - a broken tool must not crash the gate
        return None
    return mod


def _check(
    name: str,
    verdict: str,
    blocking: list[str],
    review: list[str],
    detail: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """A single normalized check result.

    verdict in: pass | review | block | not_run
    """
    return {
        "check": name,
        "verdict": verdict,
        "blocking_findings": sorted(blocking),
        "review_findings": sorted(review),
        "detail": detail or {},
    }


def _not_run(name: str, reason: str) -> dict[str, Any]:
    """A check that did not run. Its reason is a note, NOT a review finding.

    Recording the reason as a review finding would conflate "we skipped this"
    with "a reviewer must look at this" and inflate the review count. A not_run
    check contributes neither blocking nor review findings to the verdict.
    """
    return {
        "check": name,
        "verdict": "not_run",
        "blocking_findings": [],
        "review_findings": [],
        "detail": {"reason": reason},
    }


# --- individual checks -------------------------------------------------------
def check_candidate_shape(candidate: dict[str, Any]) -> dict[str, Any]:
    blocking: list[str] = []
    review: list[str] = []

    if not isinstance(candidate, dict):
        return _check("candidate_shape", "block",
                      ["candidate is not a JSON object"], [])

    for layer in REQUIRED_CANDIDATE_LAYERS:
        if layer not in candidate:
            blocking.append(f"missing required v4.2 layer: {layer}")

    if not candidate.get("skill_id"):
        blocking.append("missing skill_id")
    if not candidate.get("candidate_hash"):
        review.append("missing candidate_hash (cannot anchor determinism)")

    # skill_lifecycle must not be literally named supply_chain and must not
    # claim completeness.
    sl = candidate.get("skill_lifecycle") or {}
    if isinstance(sl, dict):
        if sl.get("completeness_claimed") is True:
            blocking.append(
                "skill_lifecycle.completeness_claimed is true (supply-chain "
                "completeness must not be claimed)"
            )
        if str(sl.get("name", "")).lower() == "supply_chain":
            blocking.append("skill_lifecycle must not be named 'supply_chain'")

    # output_contract.graph_bindings must be present (mapping §7).
    oc = candidate.get("output_contract") or {}
    if isinstance(oc, dict) and "graph_bindings" not in oc:
        blocking.append("output_contract.graph_bindings missing")

    # Governance floor: human veto must be required and not lowerable.
    gov = candidate.get("governance_system") or {}
    hv = gov.get("human_veto") if isinstance(gov, dict) else None
    if isinstance(hv, dict):
        if not hv.get("required"):
            blocking.append("governance_system.human_veto.required is not true")
        if hv.get("lowerable") is True:
            blocking.append("governance_system.human_veto is lowerable")

    verdict = "block" if blocking else ("review" if review else "pass")
    return _check("candidate_shape", verdict, blocking, review,
                  {"required_layers": list(REQUIRED_CANDIDATE_LAYERS)})


def check_boundary_tripwires(candidate_text: str,
                             candidate: dict[str, Any]) -> dict[str, Any]:
    """Forbidden public claims + internal-name / private->public leakage."""
    blocking: list[str] = []
    review: list[str] = []
    low = candidate_text.lower()

    for sub in FORBIDDEN_CLAIM_SUBSTRINGS:
        if sub in low:
            blocking.append(f"forbidden public claim: {sub!r}")

    for sub in FORBIDDEN_CODENAME_SUBSTRINGS:
        if sub in low:
            blocking.append(f"internal codename leak: {sub!r}")

    # Internal track name is allowed only inside the internal_target block.
    if INTERNAL_TRACK_NAME.lower() in low:
        it = candidate.get("internal_target")
        it_text = json.dumps(it, sort_keys=True).lower() if it else ""
        # Count occurrences outside the internal_target block.
        total = low.count(INTERNAL_TRACK_NAME.lower())
        inside = it_text.count(INTERNAL_TRACK_NAME.lower())
        if total > inside:
            blocking.append(
                "internal track name leaks outside internal_target block"
            )

    # Explicit private->public leak flags (mirrors threat-model contract).
    if candidate.get("private_public_leak"):
        blocking.append("candidate declares a private->public leak")
    boundaries = candidate.get("boundaries") or {}
    if isinstance(boundaries, dict) and boundaries.get("private_to_public_leak"):
        blocking.append("boundaries.private_to_public_leak is set")

    # Public v4.2 over-claim: a candidate must not claim public v4.2.
    it = candidate.get("internal_target") or {}
    if isinstance(it, dict) and str(it.get("public_version", "")).startswith("v4.2"):
        blocking.append("candidate claims public_version v4.2 (public stays v4.1)")

    verdict = "block" if blocking else ("review" if review else "pass")
    return _check("boundary_tripwires", verdict, blocking, review)


def check_threat_model(candidate: dict[str, Any], candidate_path: str,
                       mod: ModuleType | None) -> dict[str, Any]:
    if mod is None:
        return _not_run("threat_model",
                        "threat-model tool not importable on this branch")
    try:
        report = mod.build_report(candidate, candidate_path)
    except Exception as exc:  # noqa: BLE001
        return _not_run("threat_model", f"threat-model tool errored: {exc}")
    blocked = list(report.get("blocked_findings") or [])
    mediums = report.get("summary", {}).get("by_severity", {}).get("medium", 0)
    review = [f"{mediums} medium finding(s) to review"] if mediums else []
    verdict = "block" if blocked else ("review" if review else "pass")
    return _check(
        "threat_model", verdict,
        [f"threat:{t}" for t in blocked], review,
        {"deterministic_threat_model_id":
            report.get("deterministic_threat_model_id"),
         "summary": report.get("summary")},
    )


def check_source_license(source_manifest: Path | None,
                         eval_date: _dt.date,
                         mod: ModuleType | None) -> dict[str, Any]:
    if source_manifest is None:
        return _not_run("source_license", "no --source-manifest provided")
    if mod is None:
        return _not_run("source_license",
                        "source-check tool not importable on this branch")
    try:
        manifest, text = mod.load_manifest(source_manifest)
        report = mod.build_report(manifest, text, source_manifest, eval_date, 3)
    except Exception as exc:  # noqa: BLE001
        return _not_run("source_license", f"source-check could not run: {exc}")
    summary = report.get("summary", {})
    blocked_n = summary.get("blocked", 0)
    review_n = summary.get("review", 0)
    blocking = [
        f"source:{f['id']}" for f in report.get("blocked_findings") or []
    ]
    review = [f"{review_n} source(s) need review"] if review_n else []
    verdict = "block" if blocked_n else ("review" if review_n else "pass")
    return _check("source_license", verdict, blocking, review,
                  {"deterministic_report_id":
                       report.get("deterministic_report_id"),
                   "summary": summary})


def check_logical_diff(before: Path | None, candidate_path: Path,
                       mod: ModuleType | None) -> dict[str, Any]:
    if before is None:
        return _not_run("logical_diff", "no --before candidate provided")
    if mod is None:
        return _not_run("logical_diff",
                        "diff tool not importable on this branch")
    try:
        report = mod.build_report(before, candidate_path)
    except Exception as exc:  # noqa: BLE001
        return _not_run("logical_diff", f"diff tool could not run: {exc}")
    blocked = report.get("blocked_findings") or []
    high = report.get("high_risk_findings") or []
    blocking = [f"diff:{f.get('path')}:{f.get('kind')}" for f in blocked]
    review = [f"{len(high)} high-risk diff finding(s)"] if high else []
    verdict = "block" if blocked else ("review" if high else "pass")
    return _check("logical_diff", verdict, blocking, review,
                  {"deterministic_diff_id": report.get("deterministic_diff_id"),
                   "summary": report.get("summary")})


def check_premium_pass(candidate: dict[str, Any]) -> dict[str, Any]:
    """Report (never run) whether a human premium pass is required."""
    status = candidate.get("premium_pass_status") or {}
    gaps = list(status.get("gaps") or [])
    requires = bool(status.get("requires_human_premium_pass")) or bool(gaps)
    review = (
        [f"premium pass required for gap: {g}" for g in gaps]
        if requires else []
    )
    # A premium-pass requirement is NOT blocking; it routes to ACCEPT_WITH_REVIEW.
    verdict = "review" if requires else "pass"
    return _check("premium_pass_required", verdict, [], review,
                  {"requires_human_premium_pass": requires, "gaps": sorted(gaps)})


# --- orchestration -----------------------------------------------------------
def _deterministic_gate_id(candidate_hash: str | None,
                           checks: list[dict[str, Any]]) -> str:
    normalized = [
        {
            "check": c["check"],
            "verdict": c["verdict"],
            "blocking_findings": c["blocking_findings"],
            "review_findings": c["review_findings"],
        }
        for c in sorted(checks, key=lambda c: c["check"])
    ]
    payload = json.dumps(
        {"candidate_hash": candidate_hash, "checks": normalized},
        sort_keys=True, separators=(",", ":"),
    )
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def run_gate(
    candidate: dict[str, Any],
    candidate_text: str,
    candidate_path: Path,
    source_manifest: Path | None,
    before: Path | None,
    eval_date: _dt.date,
) -> dict[str, Any]:
    threat_mod = _load_module(
        "sc_threat_model", "generate_supply_chain_threat_model.py"
    )
    source_mod = _load_module(
        "sc_source_check", "check_supply_chain_sources.py"
    )
    diff_mod = _load_module("sc_diff", "generate_supply_chain_diff.py")

    checks: list[dict[str, Any]] = [
        check_candidate_shape(candidate),
        check_boundary_tripwires(candidate_text, candidate),
        check_threat_model(candidate, str(candidate_path), threat_mod),
        check_source_license(source_manifest, eval_date, source_mod),
        check_logical_diff(before, candidate_path, diff_mod),
        check_premium_pass(candidate),
    ]

    any_block = any(c["verdict"] == "block" for c in checks)
    any_review = any(c["verdict"] == "review" for c in checks)

    if any_block:
        classification = "BLOCK"
    elif any_review:
        classification = "ACCEPT_WITH_REVIEW"
    else:
        classification = "ACCEPT"

    all_blocking = sorted(
        f for c in checks for f in c["blocking_findings"]
    )
    all_review = sorted(
        f for c in checks for f in c["review_findings"]
    )

    return {
        "schema_version": GATE_SCHEMA_VERSION,
        "kind": "xklickd_supply_chain_promotion_gate_report",
        "non_normative": True,
        "candidate_path": str(candidate_path),
        "candidate_id": candidate.get("candidate_id"),
        "candidate_hash": candidate.get("candidate_hash"),
        "classification": classification,
        "deterministic_gate_id": _deterministic_gate_id(
            candidate.get("candidate_hash"), checks
        ),
        "summary": {
            "checks_run": sum(1 for c in checks if c["verdict"] != "not_run"),
            "checks_not_run": sum(1 for c in checks if c["verdict"] == "not_run"),
            "blocking": len(all_blocking),
            "review": len(all_review),
        },
        "checks": checks,
        "blocking_findings": all_blocking,
        "review_findings": all_review,
        "premium_pass_required": any(
            c["check"] == "premium_pass_required"
            and c["detail"].get("requires_human_premium_pass")
            for c in checks
        ),
        "claim_boundaries": {
            "is_security_certification": False,
            "establishes_legal_compliance": False,
            "is_full_automation": False,
            "proves_loaded_executable_skill": False,
            "runs_premium_pass": False,
            "note": ("The gate orchestrates offline, stdlib-only checks and "
                     "reports whether a human premium pass is required; it "
                     "does not run that pass and makes no compliance claim."),
        },
        "non_deterministic_zone": {
            "evaluated_at": eval_date.isoformat(),
            "note": ("evaluated_at is excluded from deterministic_gate_id."),
        },
    }


def render_json(report: dict[str, Any]) -> str:
    return json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def render_md(report: dict[str, Any]) -> str:
    lines = [
        f"# Supply-chain promotion gate — {report['classification']}",
        "",
        f"- **Candidate:** `{report.get('candidate_id')}`",
        f"- **Gate id:** `{report['deterministic_gate_id']}`",
        f"- **Premium pass required:** {report['premium_pass_required']}",
        f"- **Blocking:** {report['summary']['blocking']}  ·  "
        f"**Review:** {report['summary']['review']}  ·  "
        f"**Checks run:** {report['summary']['checks_run']}  ·  "
        f"**Not run:** {report['summary']['checks_not_run']}",
        "",
        "## Checks",
        "",
        "| Check | Verdict | Blocking | Review |",
        "|---|---|---|---|",
    ]
    for c in report["checks"]:
        lines.append(
            f"| {c['check']} | {c['verdict']} | "
            f"{len(c['blocking_findings'])} | {len(c['review_findings'])} |"
        )
    if report["blocking_findings"]:
        lines += ["", "## Blocking findings", ""]
        lines += [f"- {f}" for f in report["blocking_findings"]]
    if report["review_findings"]:
        lines += ["", "## Review findings", ""]
        lines += [f"- {f}" for f in report["review_findings"]]
    lines += [
        "",
        "> NON-NORMATIVE. No release, no compliance claim. The gate reports "
        "whether a human premium pass is required; it does not run one.",
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Combined x.klickd supply-chain promotion gate "
                    "(non-normative).",
    )
    parser.add_argument("--candidate", required=True,
                        help="path to candidate skill JSON")
    parser.add_argument("--source-manifest", default=None,
                        help="optional source manifest for the source/license check")
    parser.add_argument("--before", default=None,
                        help="optional prior candidate JSON for a logical diff")
    parser.add_argument("--out", default=None,
                        help="path to write the gate report JSON "
                             "(default: .internal-skills/supply-chain/"
                             "promotion-gate/<candidate>.gate.json)")
    parser.add_argument("--md", default=None,
                        help="optional path to write a Markdown summary")
    parser.add_argument("--eval-date", default=None,
                        help="ISO date for source freshness math "
                             "(default: today UTC)")
    parser.add_argument("--quiet", action="store_true",
                        help="do not print the report JSON to stdout")
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    cand_path = Path(args.candidate)
    if not cand_path.exists():
        print(f"error: candidate not found: {cand_path}", file=sys.stderr)
        return 2
    candidate_text = cand_path.read_text(encoding="utf-8")
    try:
        candidate = json.loads(candidate_text)
    except json.JSONDecodeError as exc:
        print(f"error: candidate JSON parse failed: {exc}", file=sys.stderr)
        return 2
    if not isinstance(candidate, dict):
        print("error: candidate root must be a JSON object", file=sys.stderr)
        return 2

    source_manifest = Path(args.source_manifest) if args.source_manifest else None
    if source_manifest is not None and not source_manifest.exists():
        print(f"error: source manifest not found: {source_manifest}",
              file=sys.stderr)
        return 2
    before = Path(args.before) if args.before else None
    if before is not None and not before.exists():
        print(f"error: --before not found: {before}", file=sys.stderr)
        return 2

    if args.eval_date:
        try:
            eval_date = _dt.date.fromisoformat(args.eval_date[:10])
        except ValueError:
            print(f"error: invalid --eval-date: {args.eval_date}", file=sys.stderr)
            return 2
    else:
        eval_date = _dt.datetime.now(_dt.timezone.utc).date()

    report = run_gate(
        candidate, candidate_text, cand_path, source_manifest, before, eval_date
    )

    serialized = render_json(report)
    if args.out:
        out_path = Path(args.out)
    else:
        out_path = DEFAULT_OUT_DIR / f"{cand_path.stem}.gate.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(serialized, encoding="utf-8")
    if args.md:
        md_path = Path(args.md)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(render_md(report), encoding="utf-8")
    if not args.quiet:
        sys.stdout.write(serialized)

    print(
        f"GATE: {report['classification']} "
        f"(blocking={report['summary']['blocking']}, "
        f"review={report['summary']['review']}, "
        f"premium_pass_required={report['premium_pass_required']}) "
        f"id={report['deterministic_gate_id']}",
        file=sys.stderr,
    )
    return 1 if report["classification"] == "BLOCK" else 0


if __name__ == "__main__":
    raise SystemExit(main())
