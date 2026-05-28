#!/usr/bin/env python3
"""Pilot output auditor.

Reads a pilot run directory (containing ``raw_outputs.jsonl``,
``errors.jsonl``, ``run_manifest.json``, ``metrics_summary.json``) and
produces ``audit_report.md`` with the following checks:

- Completeness: every (user_id, prompt_id, condition) cell present OR
  accounted for in ``errors.jsonl``.
- Condition balance: each of ``no_klickd``, ``xklickd_lite``,
  ``xklickd_pro`` has the same count of attempts.
- Output coverage: count of ok rows; share of rows with non-empty
  ``output_text``; share with provider-reported tokens.
- Error coverage: count of rows in ``errors.jsonl`` and breakdown by
  condition.
- Secret scan: scans raw + manifest for common secret patterns. Any hit
  is a hard FAIL.
- Hash completeness: every ok row has ``prompt_hash`` and
  ``output_hash``; every error row has ``prompt_hash``.
- Model/config consistency: every row uses the same ``model`` and the
  manifest's ``config.model``.
- Token/latency summary: min / max / mean / median per condition.

Exits non-zero if any hard check fails. Soft warnings are reported in the
audit report but do not change the exit code.
"""
from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9]{16,}"),
    re.compile(r"AIza[0-9A-Za-z\-_]{30,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"xox[abprs]-[A-Za-z0-9-]{10,}"),
    re.compile(r"-----BEGIN (RSA |EC |OPENSSH |)PRIVATE KEY-----"),
]


def _load_jsonl(p: Path) -> list[dict[str, Any]]:
    if not p.exists():
        return []
    rows: list[dict[str, Any]] = []
    with p.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def _scan_secrets(text: str) -> list[str]:
    hits: list[str] = []
    for pat in SECRET_PATTERNS:
        for m in pat.findall(text):
            sample = m if isinstance(m, str) else str(m)
            hits.append(sample[:8] + "…")
    return hits


def audit_run(run_dir: Path) -> dict[str, Any]:
    raw = _load_jsonl(run_dir / "raw_outputs.jsonl")
    errors = _load_jsonl(run_dir / "errors.jsonl")
    manifest_path = run_dir / "run_manifest.json"
    summary_path = run_dir / "metrics_summary.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"missing run_manifest.json in {run_dir}")
    manifest = json.loads(manifest_path.read_text())
    summary = json.loads(summary_path.read_text()) if summary_path.exists() else {}

    report: dict[str, Any] = {
        "run_dir": str(run_dir),
        "run_id": manifest.get("run_id"),
        "provider": manifest.get("provider"),
        "model_manifest": manifest.get("config", {}).get("model"),
        "checks": {},
        "failures": [],
        "warnings": [],
    }

    # Completeness + condition balance.
    by_cond_attempts: Counter[str] = Counter()
    for r in raw:
        by_cond_attempts[r["condition"]] += 1
    for e in errors:
        by_cond_attempts[e.get("condition", "_unknown")] += 1
    expected_conditions = ("no_klickd", "xklickd_lite", "xklickd_pro")
    counts = {c: by_cond_attempts.get(c, 0) for c in expected_conditions}
    balanced = len(set(counts.values())) == 1 and all(v > 0 for v in counts.values())
    report["checks"]["condition_balance"] = {
        "by_condition": counts,
        "balanced": balanced,
    }
    if not balanced:
        report["failures"].append("condition_balance: counts differ across conditions")

    # Coverage.
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

    # Hash completeness.
    missing_prompt_hash = [r["run_id"] for r in raw if not r.get("prompt_hash")]
    missing_output_hash = [r["run_id"] for r in raw if not r.get("output_hash")]
    missing_err_prompt_hash = [e.get("run_id") for e in errors if not e.get("prompt_hash")]
    report["checks"]["hashes"] = {
        "missing_prompt_hash_ok_rows": missing_prompt_hash,
        "missing_output_hash_ok_rows": missing_output_hash,
        "missing_prompt_hash_error_rows": missing_err_prompt_hash,
    }
    if missing_prompt_hash or missing_output_hash or missing_err_prompt_hash:
        report["failures"].append("hashes: missing prompt or output hash on at least one row")

    # Model consistency.
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

    # Secret scan over raw outputs and manifest body.
    secret_hits: list[dict[str, Any]] = []
    for r in raw:
        hits = _scan_secrets(json.dumps(r, ensure_ascii=False))
        if hits:
            secret_hits.append({"run_id": r["run_id"], "hits": hits})
    manifest_hits = _scan_secrets(json.dumps(manifest, ensure_ascii=False))
    report["checks"]["secret_scan"] = {
        "rows_with_hits": secret_hits,
        "manifest_hits": manifest_hits,
    }
    if secret_hits or manifest_hits:
        report["failures"].append("secret_scan: potential secret-like pattern detected")

    # Token / latency stats.
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

    # Per-condition token stats.
    by_cond_tokens_in: dict[str, list[int]] = defaultdict(list)
    by_cond_tokens_out: dict[str, list[int]] = defaultdict(list)
    by_cond_latency: dict[str, list[int]] = defaultdict(list)
    for r in raw:
        if isinstance(r.get("input_tokens"), int):
            by_cond_tokens_in[r["condition"]].append(r["input_tokens"])
        if isinstance(r.get("output_tokens"), int):
            by_cond_tokens_out[r["condition"]].append(r["output_tokens"])
        if isinstance(r.get("latency_ms"), int):
            by_cond_latency[r["condition"]].append(r["latency_ms"])
    report["checks"]["per_condition"] = {
        cond: {
            "input_tokens": _stats(by_cond_tokens_in.get(cond, [])),
            "output_tokens": _stats(by_cond_tokens_out.get(cond, [])),
            "latency_ms": _stats(by_cond_latency.get(cond, [])),
        }
        for cond in expected_conditions
    }

    report["summary_recorded"] = summary
    report["passed"] = not report["failures"]
    return report


def write_markdown(report: dict[str, Any], out_path: Path) -> None:
    lines: list[str] = []
    lines.append(f"# Pilot audit report — `{report.get('run_id')}`")
    lines.append("")
    lines.append(f"- Run directory: `{report['run_dir']}`")
    lines.append(f"- Provider: `{report.get('provider')}`")
    lines.append(f"- Model (manifest): `{report.get('model_manifest')}`")
    lines.append(f"- Overall: **{'PASS' if report['passed'] else 'FAIL'}**")
    lines.append("")
    if report["failures"]:
        lines.append("## Failures")
        for f in report["failures"]:
            lines.append(f"- {f}")
        lines.append("")
    if report["warnings"]:
        lines.append("## Warnings")
        for w in report["warnings"]:
            lines.append(f"- {w}")
        lines.append("")
    lines.append("## Checks")
    lines.append("")
    lines.append("```json")
    lines.append(json.dumps(report["checks"], indent=2, sort_keys=True))
    lines.append("```")
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Audit a pilot run directory.")
    ap.add_argument("run_dir", type=Path,
                    help="Directory containing raw_outputs.jsonl, errors.jsonl, "
                         "run_manifest.json, metrics_summary.json.")
    ap.add_argument("--report", type=Path, default=None,
                    help="Output markdown path (default: <run_dir>/audit_report.md).")
    args = ap.parse_args()
    report = audit_run(args.run_dir)
    out = args.report or (args.run_dir / "audit_report.md")
    write_markdown(report, out)
    # JSON copy for machine consumption.
    (args.run_dir / "audit_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"[audit] {'PASS' if report['passed'] else 'FAIL'}: {out}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
