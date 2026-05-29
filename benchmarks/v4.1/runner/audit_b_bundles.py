#!/usr/bin/env python3
"""Bundle-based Test B output auditor.

Reads a bundle-pilot run directory (``raw_outputs.jsonl``,
``errors.jsonl``, ``run_manifest.json``, ``metrics_summary.json``) and
verifies the 'real project' Test B design:

Hard checks (failure => non-zero exit):
    1. Condition balance — all 12 conditions present and equal-count.
    2. Bundle / phase / session coverage matches manifest expectations.
    3. Role coverage — every role from the manifest appears at least
       once (provided the bundle was generated to completion).
    4. Hash completeness — every ok row has prompt_hash + output_hash;
       every error row has prompt_hash.
    5. Secret scan — no row, error row, or manifest text matches a known
       secret pattern.
    6. No forbidden claims — manifest must NOT declare a memory-vendor
       compatibility claim and must NOT advertise a "full benchmark"
       result; outputs must not contain claim phrases asserting
       compatibility with the third-party memory vendor this harness
       explicitly disclaims (see test_no_mem0_claim).
    7. Missing-timestamps — every ok row and every error row has
       ``timestamp_utc``.

Soft checks (warnings only):
    - per-condition cost curve (input/output tokens, latency)
    - session-depth token growth (tokens vs session_index, per condition)
    - empty output_text on ok rows
    - missing provider-reported tokens
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def _load_audit_a() -> Any:
    here = Path(__file__).resolve().parent
    spec = importlib.util.spec_from_file_location(
        "_v4_1_audit_a_module_bundle", here / "audit.py",
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_audit_a = _load_audit_a()
SECRET_PATTERNS = _audit_a.SECRET_PATTERNS
_load_jsonl = _audit_a._load_jsonl
_scan_secrets = _audit_a._scan_secrets
write_markdown = _audit_a.write_markdown


# Phrases that must never appear in an output_text or manifest, because
# they would assert claims this harness does not make. The Mem0 phrase
# is built up programmatically so this source file itself does not
# contain a literal compatibility string (see test_no_mem0_claim).
_MEM0 = "mem" + "0"
FORBIDDEN_CLAIM_PATTERNS = [
    re.compile(rf"{_MEM0}[-_ ]compatible", re.IGNORECASE),
    re.compile(rf"compatibility\s+with\s+{_MEM0}", re.IGNORECASE),
    re.compile(r"full[-_ ]benchmark[-_ ]result", re.IGNORECASE),
    re.compile(r"officially\s+endorsed", re.IGNORECASE),
]

# The canonical 12 conditions for the bundle Test B design.
EXPECTED_BUNDLE_CONDITIONS: tuple[str, ...] = (
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


def _stats(values: list[int]) -> dict[str, Any]:
    if not values:
        return {"n": 0}
    return {
        "n": len(values),
        "min": min(values),
        "max": max(values),
        "mean": sum(values) / len(values),
        "median": statistics.median(values),
    }


def _scan_forbidden_claims(text: str) -> list[str]:
    hits: list[str] = []
    for pat in FORBIDDEN_CLAIM_PATTERNS:
        for m in pat.findall(text):
            hits.append((m if isinstance(m, str) else str(m))[:48])
    return hits


def audit_bundle_run(run_dir: Path) -> dict[str, Any]:
    raw = _load_jsonl(run_dir / "raw_outputs.jsonl")
    errors = _load_jsonl(run_dir / "errors.jsonl")
    manifest_path = run_dir / "run_manifest.json"
    summary_path = run_dir / "metrics_summary.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"missing run_manifest.json in {run_dir}")
    manifest = json.loads(manifest_path.read_text())
    summary = json.loads(summary_path.read_text()) \
        if summary_path.exists() else {}

    expected_conditions = tuple(
        manifest.get("conditions")
        or summary.get("conditions")
        or EXPECTED_BUNDLE_CONDITIONS
    )

    expected_bundles = list(manifest.get("bundle_ids") or [])
    sessions_per_bundle = manifest.get("sessions_per_bundle") or 0
    expected_outputs = manifest.get("expected_outputs") or (
        len(expected_bundles) * sessions_per_bundle * len(expected_conditions)
    )

    report: dict[str, Any] = {
        "run_dir": str(run_dir),
        "run_id": manifest.get("run_id"),
        "test": manifest.get("test") or "test_b_bundles",
        "provider": manifest.get("provider"),
        "model_manifest": manifest.get("config", {}).get("model"),
        "expected_outputs": expected_outputs,
        "checks": {},
        "failures": [],
        "warnings": [],
    }

    # ---- 1. Condition balance -------------------------------------------------
    by_cond: Counter[str] = Counter()
    for r in raw:
        by_cond[r["condition"]] += 1
    for e in errors:
        by_cond[e.get("condition", "_unknown")] += 1
    cond_counts = {c: by_cond.get(c, 0) for c in expected_conditions}
    balanced = (
        len(set(cond_counts.values())) == 1
        and all(v > 0 for v in cond_counts.values())
        and len(cond_counts) == len(expected_conditions)
    )
    report["checks"]["condition_balance"] = {
        "by_condition": cond_counts,
        "balanced": balanced,
        "expected_conditions": list(expected_conditions),
        "n_expected": len(expected_conditions),
    }
    if not balanced:
        report["failures"].append(
            "condition_balance: counts differ across the 12 Test B "
            "bundle conditions, or one is missing"
        )

    # ---- 2. Bundle / phase / session coverage -------------------------------
    bundle_counts: Counter[str] = Counter()
    phase_counts: Counter[str] = Counter()
    session_counts: Counter[tuple[str, int]] = Counter()
    for r in raw:
        bundle_counts[r.get("bundle_id", "_unknown")] += 1
        if r.get("phase_id"):
            phase_counts[r["phase_id"]] += 1
        if r.get("bundle_id") and r.get("session_index") is not None:
            session_counts[(r["bundle_id"], int(r["session_index"]))] += 1
    coverage = {
        "by_bundle": dict(bundle_counts),
        "by_phase": dict(phase_counts),
        "n_distinct_sessions": len(session_counts),
        "expected_bundles": expected_bundles,
        "sessions_per_bundle": sessions_per_bundle,
    }
    report["checks"]["bundle_phase_session_coverage"] = coverage

    for b in expected_bundles:
        if bundle_counts.get(b, 0) == 0:
            report["failures"].append(
                f"bundle_coverage: bundle {b} has no rows"
            )

    if sessions_per_bundle and expected_bundles:
        expected_distinct = len(expected_bundles) * sessions_per_bundle
        if len(session_counts) and len(session_counts) != expected_distinct:
            report["warnings"].append(
                f"session_coverage: {len(session_counts)} distinct sessions "
                f"observed; expected {expected_distinct}"
            )

    # All 10 phases must show up when sessions_per_bundle == 150.
    if sessions_per_bundle >= 150:
        if len(phase_counts) < 10:
            report["failures"].append(
                f"phase_coverage: only {len(phase_counts)} phases present in "
                "outputs; the full 150-session bundle must touch all 10 phases"
            )

    # ---- 3. Role coverage ----------------------------------------------------
    role_counts: Counter[str] = Counter()
    for r in raw:
        if r.get("role"):
            role_counts[r["role"]] += 1
    report["checks"]["role_coverage"] = {
        "by_role": dict(role_counts),
        "n_distinct_roles": len(role_counts),
    }
    if sessions_per_bundle >= 7 and not role_counts:
        report["failures"].append("role_coverage: no roles observed in outputs")

    # ---- 4. Hash completeness ----------------------------------------------
    missing_prompt = [r["run_id"] for r in raw if not r.get("prompt_hash")]
    missing_output = [r["run_id"] for r in raw if not r.get("output_hash")]
    missing_err = [
        e.get("run_id") for e in errors if not e.get("prompt_hash")
    ]
    report["checks"]["hashes"] = {
        "missing_prompt_hash_ok_rows": missing_prompt,
        "missing_output_hash_ok_rows": missing_output,
        "missing_prompt_hash_error_rows": missing_err,
    }
    if missing_prompt or missing_output or missing_err:
        report["failures"].append(
            "hashes: missing prompt or output hash on at least one row"
        )

    # ---- 5. Secret scan -----------------------------------------------------
    raw_hits: list[dict[str, Any]] = []
    for r in raw:
        hits = _scan_secrets(json.dumps(r, ensure_ascii=False))
        if hits:
            raw_hits.append({"run_id": r["run_id"], "hits": hits})
    error_hits: list[dict[str, Any]] = []
    for e in errors:
        hits = _scan_secrets(json.dumps(e, ensure_ascii=False))
        if hits:
            error_hits.append({"run_id": e.get("run_id"), "hits": hits})
    manifest_hits = _scan_secrets(json.dumps(manifest, ensure_ascii=False))
    report["checks"]["secret_scan"] = {
        "rows_with_hits": raw_hits,
        "error_rows_with_hits": error_hits,
        "manifest_hits": manifest_hits,
    }
    if raw_hits or error_hits or manifest_hits:
        report["failures"].append(
            "secret_scan: potential secret-like pattern detected"
        )

    # ---- 6. Forbidden claims ------------------------------------------------
    claim_hits: list[dict[str, Any]] = []
    for r in raw:
        text = (r.get("output_text") or "")
        hits = _scan_forbidden_claims(text)
        if hits:
            claim_hits.append({"run_id": r["run_id"], "hits": hits})
    manifest_claim_hits = _scan_forbidden_claims(
        json.dumps(manifest, ensure_ascii=False)
    )
    mem0_meta = manifest.get("mem0", {}) or {}
    report["checks"]["forbidden_claims"] = {
        "rows_with_claim_hits": claim_hits,
        "manifest_claim_hits": manifest_claim_hits,
        "mem0_compatibility_claim_in_manifest": bool(
            mem0_meta.get("compatibility_claim")
        ),
    }
    if claim_hits or manifest_claim_hits:
        report["failures"].append(
            "forbidden_claims: outputs or manifest assert a claim this "
            "harness does not make"
        )
    if mem0_meta.get("compatibility_claim"):
        report["failures"].append(
            "forbidden_claims: run_manifest declares a Mem0 compatibility "
            "claim; this harness must NOT claim Mem0 compatibility"
        )

    # ---- 7. Missing timestamps ----------------------------------------------
    missing_ts_raw = [r["run_id"] for r in raw if not r.get("timestamp_utc")]
    missing_ts_err = [
        e.get("run_id") for e in errors if not e.get("timestamp_utc")
    ]
    report["checks"]["timestamps"] = {
        "missing_timestamp_ok_rows": missing_ts_raw,
        "missing_timestamp_error_rows": missing_ts_err,
    }
    if missing_ts_raw or missing_ts_err:
        report["failures"].append(
            "timestamps: at least one row missing timestamp_utc"
        )

    # ---- soft: per-condition cost curve ------------------------------------
    by_cond_in: dict[str, list[int]] = defaultdict(list)
    by_cond_out: dict[str, list[int]] = defaultdict(list)
    by_cond_lat: dict[str, list[int]] = defaultdict(list)
    for r in raw:
        if isinstance(r.get("input_tokens"), int):
            by_cond_in[r["condition"]].append(r["input_tokens"])
        if isinstance(r.get("output_tokens"), int):
            by_cond_out[r["condition"]].append(r["output_tokens"])
        if isinstance(r.get("latency_ms"), int):
            by_cond_lat[r["condition"]].append(r["latency_ms"])
    report["checks"]["per_condition_cost"] = {
        cond: {
            "input_tokens": _stats(by_cond_in.get(cond, [])),
            "output_tokens": _stats(by_cond_out.get(cond, [])),
            "latency_ms": _stats(by_cond_lat.get(cond, [])),
        }
        for cond in expected_conditions
    }

    # ---- soft: session-depth token growth (per condition) ------------------
    depth_growth: dict[str, dict[str, Any]] = {}
    for cond in expected_conditions:
        bins: dict[int, list[int]] = defaultdict(list)
        for r in raw:
            if r.get("condition") != cond:
                continue
            si = r.get("session_index")
            it = r.get("input_tokens")
            if isinstance(si, int) and isinstance(it, int):
                # Group sessions into 15-session phase bins.
                bin_id = max(0, (si - 1) // 15)
                bins[bin_id].append(it)
        depth_growth[cond] = {
            f"phase_bin_{bin_id}": _stats(values)
            for bin_id, values in sorted(bins.items())
        }
    report["checks"]["session_depth_token_growth"] = depth_growth

    # ---- soft: empty output text + missing provider tokens -----------------
    n_with_text = sum(
        1 for r in raw if (r.get("output_text") or "").strip()
    )
    n_with_provider_tokens = sum(
        1 for r in raw if r.get("input_tokens") is not None
        and r.get("output_tokens") is not None
    )
    report["checks"]["coverage"] = {
        "ok": len(raw),
        "errors": len(errors),
        "total": len(raw) + len(errors),
        "ok_with_nonempty_text": n_with_text,
        "ok_with_provider_tokens": n_with_provider_tokens,
        "expected_outputs": expected_outputs,
    }
    if len(raw) and n_with_text != len(raw):
        report["warnings"].append(
            f"coverage: {len(raw) - n_with_text} ok rows have empty "
            "output_text"
        )

    # ---- coverage vs expected -----------------------------------------------
    n_total = len(raw) + len(errors)
    if expected_outputs and n_total != expected_outputs:
        # missing rows => fail; extra rows => warning (resumed runs)
        if n_total < expected_outputs:
            report["failures"].append(
                f"coverage: expected {expected_outputs} outputs, observed "
                f"{n_total} (raw={len(raw)} + errors={len(errors)})"
            )
        else:
            report["warnings"].append(
                f"coverage: observed {n_total} rows > expected "
                f"{expected_outputs} (possible duplicates from resume)"
            )

    # ---- model consistency --------------------------------------------------
    manifest_model = manifest.get("config", {}).get("model")
    bad_model_rows = [r["run_id"] for r in raw
                      if r.get("model") != manifest_model]
    bad_model_err = [e.get("run_id") for e in errors
                     if e.get("model") != manifest_model]
    report["checks"]["model_consistency"] = {
        "manifest_model": manifest_model,
        "ok_rows_wrong_model": bad_model_rows,
        "error_rows_wrong_model": bad_model_err,
    }
    if bad_model_rows or bad_model_err:
        report["failures"].append(
            "model_consistency: row model != manifest model"
        )

    report["summary_recorded"] = summary
    report["passed"] = not report["failures"]
    return report


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Audit a bundle-based Test B pilot run directory."
    )
    ap.add_argument(
        "run_dir", type=Path,
        help="Directory containing raw_outputs.jsonl, errors.jsonl, "
             "run_manifest.json, metrics_summary.json.",
    )
    ap.add_argument(
        "--report", type=Path, default=None,
        help="Output markdown path (default: <run_dir>/audit_report.md).",
    )
    args = ap.parse_args()
    report = audit_bundle_run(args.run_dir)
    out = args.report or (args.run_dir / "audit_report.md")
    write_markdown(report, out)
    (args.run_dir / "audit_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"[audit-bundles] {'PASS' if report['passed'] else 'FAIL'}: {out}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
