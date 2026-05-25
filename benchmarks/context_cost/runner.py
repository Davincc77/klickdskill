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


def _heuristic_input_token_estimate(text: str) -> int:
    # Heuristic token estimate: ~4 chars/token for English-like text. Closer
    # to BPE tokenizers than whitespace_tokens, but still deterministic and
    # offline. NOT a provider token count.
    if not text:
        return 0
    return max(1, len(text) // 4) if text.strip() else 0


def _tiktoken_count(text: str) -> int | None:
    # Optional: if tiktoken is installed locally, use cl100k_base. Returns
    # None when unavailable — never installs anything, never calls a network.
    if not text:
        return 0
    try:
        import tiktoken  # type: ignore
    except Exception:
        return None
    try:
        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except Exception:
        return None


def _prompt_size_bytes(text: str) -> int:
    return len(text.encode("utf-8")) if text else 0


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


def _joined_prompt(item: dict[str, str]) -> str:
    return "\n".join([item["system"], item["leading_user"], item["user"]])


def _count_continuity_fields(klickd_ctx: dict[str, Any]) -> dict[str, Any]:
    # Surfaces which "continuity" fields are present in the .klickd payload.
    ctx = klickd_ctx.get("context", {}) or {}
    identity = klickd_ctx.get("identity", {}) or {}
    fields = {
        "identity.display_name": bool(identity.get("display_name")),
        "identity.language": bool(identity.get("language")),
        "context.summary": bool(ctx.get("summary")),
        "context.current_state": bool(ctx.get("current_state")),
        "context.decisions_locked": bool(ctx.get("decisions_locked")),
        "context.handoff": bool(ctx.get("handoff")),
        "tool_permissions": bool(klickd_ctx.get("tool_permissions")),
        "verification_artifacts": bool(klickd_ctx.get("verification_artifacts")),
        "ethics.locked_actions_no_override": bool(
            (klickd_ctx.get("ethics") or {}).get("locked_actions_no_override")
        ),
    }
    return {
        "fields": fields,
        "present_count": sum(1 for v in fields.values() if v),
        "total_count": len(fields),
    }


def _gate_decision_presence(klickd_ctx: dict[str, Any]) -> dict[str, Any]:
    perms = klickd_ctx.get("tool_permissions", {}) or {}
    ctx = klickd_ctx.get("context", {}) or {}
    return {
        "decisions_locked_count": len(ctx.get("decisions_locked") or []),
        "tool_permissions_allowed_count": len(perms.get("allowed") or []),
        "tool_permissions_forbidden_count": len(perms.get("forbidden") or []),
        "tool_permissions_confirm_required_count": len(perms.get("confirm_required") or []),
        "has_ethics_lock": bool((klickd_ctx.get("ethics") or {}).get("locked_actions_no_override")),
    }


def _missing_evidence_warnings(klickd_ctx: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    va = klickd_ctx.get("verification_artifacts") or {}
    if not va:
        warnings.append("verification_artifacts block absent")
    else:
        if "policy" not in va:
            warnings.append("verification_artifacts.policy absent")
        if not isinstance(va.get("records"), list):
            warnings.append("verification_artifacts.records must be a list")
        elif len(va.get("records")) == 0:
            warnings.append(
                "verification_artifacts.records is empty — all external claims will be 'assumed'"
            )
    return warnings


def compute_extended_metrics(
    condition_inputs: dict[str, list[dict[str, str]]],
    klickd_ctx: dict[str, Any],
) -> dict[str, Any]:
    """RFC-003 §6 metrics (input token estimate, prompt size bytes, etc.) plus
    .klickd-payload structural diagnostics. No provider calls."""

    tiktoken_seen = False
    per_message: list[dict[str, Any]] = []
    totals = {c: {
        "input_token_estimate_heuristic": 0,
        "input_token_estimate_tiktoken": 0,
        "prompt_size_bytes": 0,
        "whitespace_tokens": 0,
    } for c in CONDITIONS}

    n_messages = len(condition_inputs[CONDITIONS[0]])
    for idx in range(n_messages):
        row: dict[str, Any] = {"message_id": condition_inputs[CONDITIONS[0]][idx]["id"]}
        for c in CONDITIONS:
            item = condition_inputs[c][idx]
            joined = _joined_prompt(item)
            heur = _heuristic_input_token_estimate(joined)
            tik = _tiktoken_count(joined)
            ws = _whitespace_tokens(joined)
            size_bytes = _prompt_size_bytes(joined)
            row[f"{c}_input_token_estimate_heuristic"] = heur
            row[f"{c}_input_token_estimate_tiktoken"] = tik
            row[f"{c}_prompt_size_bytes"] = size_bytes
            row[f"{c}_whitespace_tokens"] = ws
            totals[c]["input_token_estimate_heuristic"] += heur
            totals[c]["prompt_size_bytes"] += size_bytes
            totals[c]["whitespace_tokens"] += ws
            if tik is not None:
                tiktoken_seen = True
                totals[c]["input_token_estimate_tiktoken"] += tik
        per_message.append(row)

    # context_duplication_avoided: bytes (and heuristic tokens) the paste
    # condition pays that the klickd condition does not. Positive means
    # .klickd is cheaper than naive paste at the prompt boundary.
    duplication_avoided = {
        "prompt_size_bytes": totals["paste"]["prompt_size_bytes"]
            - totals["klickd"]["prompt_size_bytes"],
        "input_token_estimate_heuristic": totals["paste"]["input_token_estimate_heuristic"]
            - totals["klickd"]["input_token_estimate_heuristic"],
        "input_token_estimate_tiktoken": (
            totals["paste"]["input_token_estimate_tiktoken"]
            - totals["klickd"]["input_token_estimate_tiktoken"]
        ) if tiktoken_seen else None,
        "vs_cold_paste_overhead_bytes": totals["paste"]["prompt_size_bytes"]
            - totals["cold"]["prompt_size_bytes"],
        "vs_cold_klickd_overhead_bytes": totals["klickd"]["prompt_size_bytes"]
            - totals["cold"]["prompt_size_bytes"],
    }

    continuity = _count_continuity_fields(klickd_ctx)
    gate = _gate_decision_presence(klickd_ctx)
    warnings = _missing_evidence_warnings(klickd_ctx)

    return {
        "per_message": per_message,
        "per_condition_total": totals,
        "tiktoken_available": tiktoken_seen,
        "context_duplication_avoided": duplication_avoided,
        "gate_decision_presence": gate,
        "continuity_fields_present": continuity,
        "missing_evidence_warnings": warnings,
    }


# --- Chimera.klickd v4.1 forward-looking extrapolation ----------------------

DEFAULT_CHIMERA_PACKS = (
    "core.Kai",          # general agent operating context
    "core.KaiLegal",     # legal reasoning
    "core.MediaKai",     # media/comms
    "core.Code",         # software engineering
    "core.Edu",          # education / tutoring (.klickd v3.x heritage)
    "core.Health",       # health & wellbeing assistant
    "core.Ops",          # ops / project management
)


def chimera_v41_extrapolation(
    klickd_baseline_tokens: int,
    pack_token_costs: dict[str, int] | None = None,
    router_selection: tuple[str, ...] = ("core.Kai", "core.Ops"),
) -> dict[str, Any]:
    """Forward-looking, deterministic extrapolation for Chimera.klickd v4.1.

    Models two activation strategies for a hypothetical v4.1 multi-pack core:

    - `base_plus_seven`: load the base .klickd payload + ALL 7 default packs at
      session start, paying for every pack regardless of need.
    - `router_selected`: load the base payload + only the packs the router
      considers relevant to the current turn (default: core.Kai + core.Ops).

    Inputs are deterministic token estimates. No provider calls. Results are
    illustrative — actual savings depend on real tokenizer + real packs.
    """
    if pack_token_costs is None:
        # Conservative per-pack cost estimates (heuristic tokens) for a
        # ~3-4kB compressed pack. Documented as illustrative.
        pack_token_costs = {name: 850 for name in DEFAULT_CHIMERA_PACKS}

    missing = [p for p in DEFAULT_CHIMERA_PACKS if p not in pack_token_costs]
    if missing:
        # Be explicit rather than silently zero them out.
        for m in missing:
            pack_token_costs[m] = 850

    base_plus_seven_total = klickd_baseline_tokens + sum(
        pack_token_costs[p] for p in DEFAULT_CHIMERA_PACKS
    )
    router_total = klickd_baseline_tokens + sum(
        pack_token_costs[p] for p in router_selection if p in pack_token_costs
    )
    savings_tokens = base_plus_seven_total - router_total
    savings_pct = (savings_tokens / base_plus_seven_total) if base_plus_seven_total else 0.0

    return {
        "assumptions": {
            "klickd_baseline_tokens": klickd_baseline_tokens,
            "pack_token_costs": pack_token_costs,
            "default_packs": list(DEFAULT_CHIMERA_PACKS),
            "router_selection": list(router_selection),
            "note": (
                "Heuristic token estimate (chars/4). Illustrative; "
                "real numbers require a live tokenizer and real packs."
            ),
        },
        "base_plus_seven": {
            "total_tokens": base_plus_seven_total,
            "packs_loaded": list(DEFAULT_CHIMERA_PACKS),
        },
        "router_selected": {
            "total_tokens": router_total,
            "packs_loaded": list(router_selection),
        },
        "expected_savings": {
            "tokens": savings_tokens,
            "pct_vs_base_plus_seven": round(savings_pct, 4),
        },
    }


def write_results(
    validation: dict[str, Any],
    proxy: dict[str, Any],
    out_dir: Path,
    artifact_src: Path,
    extended: dict[str, Any] | None = None,
    extrapolation: dict[str, Any] | None = None,
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

    extra_paths: dict[str, str] = {}

    if extended is not None:
        ext_totals = extended["per_condition_total"]
        dup = extended["context_duplication_avoided"]
        cont = extended["continuity_fields_present"]
        gate = extended["gate_decision_presence"]
        warns = extended["missing_evidence_warnings"]
        lines.extend([
            "## Extended metrics (RFC-003 §6, deterministic / offline)",
            "",
            "Token estimators used (offline, no provider calls):",
            "- `heuristic`: `max(1, len(text)//4)` — coarse BPE-ish approximation.",
            f"- `tiktoken`: {'available (cl100k_base)' if extended['tiktoken_available'] else 'not installed; values are 0'}.",
            "",
            "| Condition | input_tokens_heuristic | input_tokens_tiktoken | prompt_size_bytes | whitespace_tokens |",
            "|---|---:|---:|---:|---:|",
        ])
        for c in CONDITIONS:
            t = ext_totals[c]
            lines.append(
                f"| {c} | {t['input_token_estimate_heuristic']} | "
                f"{t['input_token_estimate_tiktoken']} | "
                f"{t['prompt_size_bytes']} | {t['whitespace_tokens']} |"
            )
        lines.extend([
            "",
            "### Context duplication avoided (paste − klickd)",
            "",
            "Positive numbers mean .klickd is cheaper than naive paste. Negative",
            "numbers mean the .klickd JSON serialisation is heavier than the",
            "free-text paste for this particular fixture — typically because",
            "the structured payload pretty-prints more whitespace than the prose",
            "system prompt. The whitespace-token proxy and the heuristic-token",
            "estimator can disagree for the same input; both are reported.",
            "",
            f"- prompt_size_bytes saved: **{dup['prompt_size_bytes']}**",
            f"- heuristic input tokens saved: **{dup['input_token_estimate_heuristic']}**",
            f"- tiktoken tokens saved: **{dup['input_token_estimate_tiktoken'] if dup['input_token_estimate_tiktoken'] is not None else 'n/a (tiktoken not installed)'}**",
            f"- paste overhead vs cold (bytes): {dup['vs_cold_paste_overhead_bytes']}",
            f"- klickd overhead vs cold (bytes): {dup['vs_cold_klickd_overhead_bytes']}",
            "",
            "### Gate / decision presence in .klickd payload",
            "",
            f"- decisions_locked: {gate['decisions_locked_count']}",
            f"- tool_permissions.allowed: {gate['tool_permissions_allowed_count']}",
            f"- tool_permissions.forbidden: {gate['tool_permissions_forbidden_count']}",
            f"- tool_permissions.confirm_required: {gate['tool_permissions_confirm_required_count']}",
            f"- ethics.locked_actions_no_override: {'yes' if gate['has_ethics_lock'] else 'no'}",
            "",
            "### Continuity fields present",
            "",
            f"{cont['present_count']} / {cont['total_count']} expected continuity fields present:",
        ])
        for k, v in cont["fields"].items():
            lines.append(f"- {k}: {'present' if v else 'absent'}")
        lines.append("")
        lines.append("### Missing-evidence warnings")
        lines.append("")
        if warns:
            for w in warns:
                lines.append(f"- {w}")
        else:
            lines.append("- (none)")
        lines.append("")

        extended_json = out_dir / "extended_metrics.json"
        extended_json.write_text(
            json.dumps(extended, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        extra_paths["extended_metrics_json"] = str(extended_json)

    if extrapolation is not None:
        ex_json = out_dir / "chimera_v41_extrapolation.json"
        ex_json.write_text(
            json.dumps(extrapolation, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        extra_paths["chimera_v41_extrapolation_json"] = str(ex_json)
        savings = extrapolation["expected_savings"]
        lines.extend([
            "## Chimera.klickd v4.1 — forward-looking extrapolation",
            "",
            "> Forward-looking. v4.1 does not exist yet. Numbers below are a",
            "> deterministic offline extrapolation from the v4 baseline and",
            "> illustrative per-pack costs. **Not** a measurement.",
            "",
            f"- base + 7 packs total tokens: **{extrapolation['base_plus_seven']['total_tokens']}**",
            f"- router-selected ({', '.join(extrapolation['router_selected']['packs_loaded'])}) total tokens: **{extrapolation['router_selected']['total_tokens']}**",
            f"- expected savings: **{savings['tokens']} tokens** "
            f"(**{savings['pct_vs_base_plus_seven'] * 100:.1f}%** vs. base+7)",
            "",
            "See `chimera_v41_extrapolation.json` for full assumptions.",
            "",
        ])

    lines.append("## Artifacts")
    lines.append("")
    lines.append(f"- `{copied_artifact.relative_to(out_dir)}` (copied from fixture)")
    lines.append("")
    report_md.write_text("\n".join(lines), encoding="utf-8")

    paths = {
        "summary_csv": str(summary_csv),
        "raw_jsonl": str(raw_jsonl),
        "report_md": str(report_md),
        "artifact_copy": str(copied_artifact),
    }
    paths.update(extra_paths)
    return paths


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
    extended = compute_extended_metrics(inputs, klickd_ctx)
    extrapolation = chimera_v41_extrapolation(
        klickd_baseline_tokens=extended["per_condition_total"]["klickd"][
            "input_token_estimate_heuristic"
        ],
    )

    paths = write_results(
        validation,
        proxy,
        out_dir,
        REQUIRED_FIXTURES["verification_artifact"],
        extended=extended,
        extrapolation=extrapolation,
    )
    return {
        "out_dir": str(out_dir),
        "validation": validation,
        "proxy": proxy,
        "extended": extended,
        "extrapolation": extrapolation,
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
