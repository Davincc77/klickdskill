#!/usr/bin/env python3
# RFC-003 Context Cost Benchmark — local dry-run runner.
#
# Dry-run only: validates fixtures, computes a deterministic whitespace
# "token-proxy" count per condition, and writes results under
# benchmarks/context_cost/results/<YYYY-MM-DD>/.
#
# No provider API calls. No paid resources. No publishing.
# The token-proxy is NOT a provider token count — it is a deterministic
# whitespace-token approximation, clearly labelled as such throughout.

from __future__ import annotations

import argparse
import csv
import datetime as _dt
import json
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
FIXTURES = ROOT / "fixtures"
RESULTS_ROOT = ROOT / "results"

CONDITIONS = ("cold", "paste", "klickd")

EXPECTED_FLOW_MESSAGES = 10

# Files we must be able to load to run at all.
REQUIRED_FIXTURES = {
    "baseline_system_prompt": FIXTURES / "baseline" / "system_prompt.txt",
    "klickd_sample_context": FIXTURES / "klickd" / "sample_context.json",
    "flow": FIXTURES / "prompts" / "flow.json",
    "ground_truth": FIXTURES / "validation" / "ground_truth.json",
    "verification_artifact": FIXTURES / "verification_artifacts" / "sample_test.log",
}


class CheckError(RuntimeError):
    pass


def _whitespace_tokens(text: str) -> int:
    # Deterministic whitespace-token proxy. NOT a provider token count.
    if not text:
        return 0
    return len(re.split(r"\s+", text.strip())) if text.strip() else 0


def _load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _flatten_json_text(obj: Any) -> str:
    # Stable, deterministic textual rendering for the token proxy.
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2)


def _contains_all(haystack: str, needles: list[str]) -> list[str]:
    return [n for n in needles if n not in haystack]


def _exact_strings_any_of_ok(haystack: str, groups: list[list[str]]) -> bool:
    for group in groups:
        if all(s in haystack for s in group):
            return True
    return False


def validate_fixtures() -> dict[str, Any]:
    """Validate that the required fixtures exist and are coherent.

    Returns a dict of validation results. Raises CheckError on hard failure.
    """
    missing = [name for name, p in REQUIRED_FIXTURES.items() if not p.is_file()]
    if missing:
        raise CheckError(f"missing required fixture files: {missing}")

    system_prompt = _load_text(REQUIRED_FIXTURES["baseline_system_prompt"])
    klickd_ctx = _load_json(REQUIRED_FIXTURES["klickd_sample_context"])
    flow = _load_json(REQUIRED_FIXTURES["flow"])
    ground_truth = _load_json(REQUIRED_FIXTURES["ground_truth"])

    messages = flow.get("messages", [])
    if len(messages) != EXPECTED_FLOW_MESSAGES:
        raise CheckError(
            f"flow.json must contain {EXPECTED_FLOW_MESSAGES} messages, got {len(messages)}"
        )

    klickd_text = _flatten_json_text(klickd_ctx)

    fact_results = []
    for fact in ground_truth.get("continuity_facts", []):
        fact_id = fact["id"]
        exact_strings = fact.get("exact_strings", [])
        exact_any_of = fact.get("exact_strings_any_of", [])

        baseline_ok = True
        klickd_ok = True

        if exact_strings:
            missing_in_baseline = _contains_all(system_prompt, exact_strings)
            missing_in_klickd = _contains_all(klickd_text, exact_strings)
            baseline_ok = not missing_in_baseline
            klickd_ok = not missing_in_klickd
        if exact_any_of:
            baseline_ok = baseline_ok and _exact_strings_any_of_ok(system_prompt, exact_any_of)
            klickd_ok = klickd_ok and _exact_strings_any_of_ok(klickd_text, exact_any_of)

        fact_results.append({
            "id": fact_id,
            "fact": fact.get("fact"),
            "present_in_baseline": baseline_ok,
            "present_in_klickd": klickd_ok,
        })

    failed = [f for f in fact_results if not (f["present_in_baseline"] and f["present_in_klickd"])]
    if failed:
        raise CheckError(
            "continuity_facts not found in both baseline + klickd fixtures: "
            + ", ".join(f["id"] for f in failed)
        )

    artifact_path = REQUIRED_FIXTURES["verification_artifact"]
    if artifact_path.stat().st_size <= 0:
        raise CheckError(f"verification artifact is empty: {artifact_path}")

    return {
        "flow_message_count": len(messages),
        "continuity_facts": fact_results,
        "verification_artifact_path": str(artifact_path.relative_to(ROOT.parent.parent)),
    }


def _build_condition_inputs(
    system_prompt: str,
    klickd_ctx: dict[str, Any],
    flow: dict[str, Any],
) -> dict[str, list[dict[str, str]]]:
    """Build the per-condition input message list for each of the 10 messages.

    The output is NOT sent to any provider. It is only used to compute the
    deterministic whitespace token-proxy.
    """
    short_header = (
        "You are a project-management assistant for Léa. Be concise, no emojis.\n"
    )
    long_form = system_prompt
    user_context_block = (
        "<UserContext>\n"
        + _flatten_json_text(klickd_ctx)
        + "\n</UserContext>\n"
    )

    out: dict[str, list[dict[str, str]]] = {c: [] for c in CONDITIONS}
    messages = flow["messages"]
    for msg in messages:
        out["cold"].append({
            "id": msg["id"],
            "system": short_header,
            "leading_user": "",
            "user": msg["text"],
        })
        out["paste"].append({
            "id": msg["id"],
            "system": short_header,
            "leading_user": long_form,
            "user": msg["text"],
        })
        out["klickd"].append({
            "id": msg["id"],
            "system": short_header,
            "leading_user": user_context_block,
            "user": msg["text"],
        })
    return out


def estimate_token_proxy(condition_inputs: dict[str, list[dict[str, str]]]) -> dict[str, Any]:
    per_message: list[dict[str, Any]] = []
    per_condition_totals = {c: 0 for c in CONDITIONS}

    n_messages = len(condition_inputs[CONDITIONS[0]])
    for idx in range(n_messages):
        row: dict[str, Any] = {"message_id": condition_inputs[CONDITIONS[0]][idx]["id"]}
        for c in CONDITIONS:
            item = condition_inputs[c][idx]
            count = (
                _whitespace_tokens(item["system"])
                + _whitespace_tokens(item["leading_user"])
                + _whitespace_tokens(item["user"])
            )
            row[f"{c}_token_proxy"] = count
            per_condition_totals[c] += count
        per_message.append(row)

    return {
        "per_message": per_message,
        "per_condition_total": per_condition_totals,
    }


def write_results(
    validation: dict[str, Any],
    proxy: dict[str, Any],
    out_dir: Path,
    artifact_src: Path,
) -> dict[str, str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    artifacts_dir = out_dir / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    # Copy the demo verification artifact to mirror the artifact-tee rule.
    copied_artifact = artifacts_dir / artifact_src.name
    shutil.copy2(artifact_src, copied_artifact)

    # summary.csv — per-message proxy counts, condition columns.
    summary_csv = out_dir / "summary.csv"
    with summary_csv.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow([
            "message_id",
            "cold_token_proxy",
            "paste_token_proxy",
            "klickd_token_proxy",
            "note",
        ])
        for row in proxy["per_message"]:
            writer.writerow([
                row["message_id"],
                row["cold_token_proxy"],
                row["paste_token_proxy"],
                row["klickd_token_proxy"],
                "whitespace_token_proxy_not_provider_tokens",
            ])
        totals = proxy["per_condition_total"]
        writer.writerow([
            "TOTAL",
            totals["cold"],
            totals["paste"],
            totals["klickd"],
            "approximation_only",
        ])

    # raw_runs.jsonl — one line per (condition, message).
    raw_jsonl = out_dir / "raw_runs.jsonl"
    with raw_jsonl.open("w", encoding="utf-8") as fh:
        for row in proxy["per_message"]:
            for c in CONDITIONS:
                fh.write(json.dumps({
                    "message_id": row["message_id"],
                    "condition": c,
                    "token_proxy": row[f"{c}_token_proxy"],
                    "proxy_method": "whitespace_split",
                    "note": "NOT a provider token count.",
                }, ensure_ascii=False) + "\n")

    # report.md
    report_md = out_dir / "report.md"
    totals = proxy["per_condition_total"]
    lines = [
        "# Context Cost Benchmark — Dry-run report",
        "",
        f"Generated: {_dt.datetime.now(_dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
        "",
        "> **Dry-run only.** No provider API calls were made. The numbers below",
        "> are a deterministic whitespace-token proxy — NOT real provider tokens",
        "> and NOT comparable across tokenizers. See RFC-003 §10.",
        "",
        "## Token-proxy totals (whitespace split)",
        "",
        "| Condition | Total token-proxy |",
        "|---|---|",
        f"| cold   | {totals['cold']} |",
        f"| paste  | {totals['paste']} |",
        f"| klickd | {totals['klickd']} |",
        "",
        "## Validation",
        "",
        f"- flow.json messages: {validation['flow_message_count']} (expected {EXPECTED_FLOW_MESSAGES})",
        f"- continuity_facts checked: {len(validation['continuity_facts'])}",
        f"- verification artifact: `{validation['verification_artifact_path']}`",
        "",
        "## Per-message token-proxy",
        "",
        "| message_id | cold | paste | klickd |",
        "|---|---:|---:|---:|",
    ]
    for row in proxy["per_message"]:
        lines.append(
            f"| {row['message_id']} | {row['cold_token_proxy']} | "
            f"{row['paste_token_proxy']} | {row['klickd_token_proxy']} |"
        )
    lines.append("")
    lines.append("## Artifacts")
    lines.append("")
    lines.append(f"- `{copied_artifact.relative_to(out_dir)}` (copied from fixture)")
    lines.append("")
    report_md.write_text("\n".join(lines), encoding="utf-8")

    return {
        "summary_csv": str(summary_csv),
        "raw_jsonl": str(raw_jsonl),
        "report_md": str(report_md),
        "artifact_copy": str(copied_artifact),
    }


def run(
    out_root: Path | None = None,
    date_override: str | None = None,
) -> dict[str, Any]:
    out_root = out_root or RESULTS_ROOT
    today = date_override or _dt.date.today().isoformat()
    out_dir = out_root / today

    validation = validate_fixtures()

    system_prompt = _load_text(REQUIRED_FIXTURES["baseline_system_prompt"])
    klickd_ctx = _load_json(REQUIRED_FIXTURES["klickd_sample_context"])
    flow = _load_json(REQUIRED_FIXTURES["flow"])

    inputs = _build_condition_inputs(system_prompt, klickd_ctx, flow)
    proxy = estimate_token_proxy(inputs)

    paths = write_results(
        validation,
        proxy,
        out_dir,
        REQUIRED_FIXTURES["verification_artifact"],
    )
    return {
        "out_dir": str(out_dir),
        "validation": validation,
        "proxy": proxy,
        "paths": paths,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="RFC-003 Context Cost Benchmark — local dry-run runner. "
                    "No provider API calls; whitespace token-proxy only."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Validate fixtures only; do not write results.",
    )
    parser.add_argument(
        "--out-root",
        default=None,
        help="Override results root directory (default: benchmarks/context_cost/results/).",
    )
    parser.add_argument(
        "--date",
        default=None,
        help="Override the YYYY-MM-DD date directory (for deterministic tests).",
    )
    args = parser.parse_args(argv)

    try:
        if args.check:
            validation = validate_fixtures()
            print("OK: fixtures validated.")
            print(f"  flow messages: {validation['flow_message_count']}")
            print(f"  continuity_facts: {len(validation['continuity_facts'])}")
            print(f"  artifact: {validation['verification_artifact_path']}")
            return 0

        out_root = Path(args.out_root) if args.out_root else None
        result = run(out_root=out_root, date_override=args.date)
        print(f"OK: wrote results to {result['out_dir']}")
        for k, v in result["paths"].items():
            print(f"  {k}: {v}")
        print("NOTE: token-proxy is a whitespace approximation, NOT provider tokens.")
        return 0
    except CheckError as e:
        print(f"FAIL: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
