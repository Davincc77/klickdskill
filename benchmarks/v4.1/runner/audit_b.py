#!/usr/bin/env python3
"""Test B pilot output auditor.

Mirrors :mod:`audit` (Test A) but expects the conditions defined in
``run_manifest.json`` under ``conditions``. Test B audits typically run
against {no_memory, prompt_history, xklickd_compressed, mem0_skipped|mem0}.

Same checks: completeness, condition balance, hash completeness, secret
scan, model consistency, latency/tokens stats per condition.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def _load_audit_a() -> Any:
    here = Path(__file__).resolve().parent
    spec = importlib.util.spec_from_file_location(
        "_v4_1_audit_a_module", here / "audit.py",
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


def audit_run_b(run_dir: Path) -> dict[str, Any]:
    raw = _load_jsonl(run_dir / "raw_outputs.jsonl")
    errors = _load_jsonl(run_dir / "errors.jsonl")
    manifest_path = run_dir / "run_manifest.json"
    summary_path = run_dir / "metrics_summary.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"missing run_manifest.json in {run_dir}")
    manifest = json.loads(manifest_path.read_text())
    summary = json.loads(summary_path.read_text()) if summary_path.exists() else {}

    expected_conditions = tuple(
        manifest.get("conditions")
        or summary.get("conditions")
        or ("no_memory", "prompt_history", "xklickd_compressed", "mem0_skipped")
    )

    report: dict[str, Any] = {
        "run_dir": str(run_dir),
        "run_id": manifest.get("run_id"),
        "test": manifest.get("test") or "test_b",
        "provider": manifest.get("provider"),
        "model_manifest": manifest.get("config", {}).get("model"),
        "checks": {},
        "failures": [],
        "warnings": [],
    }

    by_cond_attempts: Counter[str] = Counter()
    for r in raw:
        by_cond_attempts[r["condition"]] += 1
    for e in errors:
        by_cond_attempts[e.get("condition", "_unknown")] += 1
    counts = {c: by_cond_attempts.get(c, 0) for c in expected_conditions}
    balanced = len(set(counts.values())) == 1 and all(v > 0 for v in counts.values())
    report["checks"]["condition_balance"] = {
        "by_condition": counts,
        "balanced": balanced,
        "expected_conditions": list(expected_conditions),
    }
    if not balanced:
        report["failures"].append(
            "condition_balance: counts differ across Test B conditions"
        )

    n_ok = len(raw)
    n_err = len(errors)
    n_total = n_ok + n_err
    n_with_text = sum(1 for r in raw if (r.get("output_text") or "").strip())
    n_with_provider_tokens = sum(
        1 for r in raw if r.get("input_tokens") is not None
        and r.get("output_tokens") is not None
    )
    report["checks"]["coverage"] = {
        "ok": n_ok,
        "errors": n_err,
        "total": n_total,
        "ok_with_nonempty_text": n_with_text,
        "ok_with_provider_tokens": n_with_provider_tokens,
    }
    if n_total == 0:
        report["failures"].append("coverage: no rows at all")
    if n_ok and n_with_text != n_ok:
        report["warnings"].append(
            f"coverage: {n_ok - n_with_text} ok rows have empty output_text"
        )

    missing_prompt_hash = [r["run_id"] for r in raw if not r.get("prompt_hash")]
    missing_output_hash = [r["run_id"] for r in raw if not r.get("output_hash")]
    missing_err_prompt_hash = [
        e.get("run_id") for e in errors if not e.get("prompt_hash")
    ]
    report["checks"]["hashes"] = {
        "missing_prompt_hash_ok_rows": missing_prompt_hash,
        "missing_output_hash_ok_rows": missing_output_hash,
        "missing_prompt_hash_error_rows": missing_err_prompt_hash,
    }
    if missing_prompt_hash or missing_output_hash or missing_err_prompt_hash:
        report["failures"].append(
            "hashes: missing prompt or output hash on at least one row"
        )

    manifest_model = manifest.get("config", {}).get("model")
    bad_model_rows = [r["run_id"] for r in raw if r.get("model") != manifest_model]
    bad_model_err = [e.get("run_id") for e in errors if e.get("model") != manifest_model]
    report["checks"]["model_consistency"] = {
        "manifest_model": manifest_model,
        "ok_rows_wrong_model": bad_model_rows,
        "error_rows_wrong_model": bad_model_err,
    }
    if bad_model_rows or bad_model_err:
        report["failures"].append("model_consistency: row model != manifest model")

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

    latencies = [r["latency_ms"] for r in raw if isinstance(r.get("latency_ms"), int)]
    tok_in = [r["input_tokens"] for r in raw if isinstance(r.get("input_tokens"), int)]
    tok_out = [r["output_tokens"] for r in raw if isinstance(r.get("output_tokens"), int)]

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

    report["checks"]["latency_ms"] = _stats(latencies)
    report["checks"]["input_tokens"] = _stats(tok_in)
    report["checks"]["output_tokens"] = _stats(tok_out)

    by_cond_in: dict[str, list[int]] = defaultdict(list)
    by_cond_out: dict[str, list[int]] = defaultdict(list)
    by_cond_latency: dict[str, list[int]] = defaultdict(list)
    for r in raw:
        if isinstance(r.get("input_tokens"), int):
            by_cond_in[r["condition"]].append(r["input_tokens"])
        if isinstance(r.get("output_tokens"), int):
            by_cond_out[r["condition"]].append(r["output_tokens"])
        if isinstance(r.get("latency_ms"), int):
            by_cond_latency[r["condition"]].append(r["latency_ms"])
    report["checks"]["per_condition"] = {
        cond: {
            "input_tokens": _stats(by_cond_in.get(cond, [])),
            "output_tokens": _stats(by_cond_out.get(cond, [])),
            "latency_ms": _stats(by_cond_latency.get(cond, [])),
        }
        for cond in expected_conditions
    }

    mem0_meta = manifest.get("mem0", {})
    if mem0_meta.get("compatibility_claim"):
        report["failures"].append(
            "mem0: run_manifest declares a Mem0 compatibility claim; "
            "this harness must NOT claim Mem0 compatibility"
        )
    report["checks"]["mem0"] = {
        "present": bool(mem0_meta.get("present")),
        "compatibility_claim": bool(mem0_meta.get("compatibility_claim")),
    }

    report["summary_recorded"] = summary
    report["passed"] = not report["failures"]
    return report


def main() -> int:
    ap = argparse.ArgumentParser(description="Audit a Test B pilot run directory.")
    ap.add_argument("run_dir", type=Path,
                    help="Directory containing raw_outputs.jsonl, errors.jsonl, "
                         "run_manifest.json, metrics_summary.json.")
    ap.add_argument("--report", type=Path, default=None,
                    help="Output markdown path (default: <run_dir>/audit_report.md).")
    args = ap.parse_args()
    report = audit_run_b(args.run_dir)
    out = args.report or (args.run_dir / "audit_report.md")
    write_markdown(report, out)
    (args.run_dir / "audit_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8",
    )
    print(f"[audit-b] {'PASS' if report['passed'] else 'FAIL'}: {out}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
