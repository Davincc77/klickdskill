#!/usr/bin/env python3
"""Continuity-Hell v1 / coding-200 benchmark runner.

ANTI-MIRAGE CONTRACT
--------------------
This runner has two kinds of lanes, and it never blurs them:

  * DRY-RUN lanes (default): fully deterministic, rule-based, OFFLINE. No LLM,
    no API key, no network. Every output is labelled ``is_real_llm: false``.
    These exist to (a) exercise the harness end-to-end and (b) give a
    transparent comparator. They are NOT a capability claim about any model.

  * REAL-LLM lane: calls a provider for all 200 tasks. This is GATED and
    refused unless the operator explicitly opts in, because it costs money /
    uses a real provider key:
        --execute  AND  XKLICKD_BENCHMARK_FULL_APPROVED=1
    Even with both set, the runner still requires the provider plumbing to be
    wired explicitly (a human must implement ``_call_provider``); it ships
    UNWIRED on purpose so no accidental spend happens. If the gate is not
    satisfied, the runner prints the exact blocker and exits without calling
    any provider.

Modes:
    baseline   dry-run, prompt-only resumer (no carried state, no skill gates)
    xklickd    dry-run, resumer that reads carried state + real skill gates
    llm        REAL provider lane (gated; refused without explicit approval)

Usage:
    python run_benchmark.py baseline
    python run_benchmark.py xklickd
    python run_benchmark.py llm                 # prints blocker, refuses
    python run_benchmark.py llm --execute       # still refused w/o env approval
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
TASKS_PATH = HERE / "tasks.json"
RESULTS_DIR = HERE / "results"

ENV_FULL_APPROVAL = "XKLICKD_BENCHMARK_FULL_APPROVED"
SKILL_FILE = "coding.klickd"


# --------------------------------------------------------------------------
# Skill governance (real, read from the SDK; falls back to repo artifact).
# --------------------------------------------------------------------------
def load_skill_governance() -> dict[str, Any]:
    payload: dict[str, Any] | None = None
    try:
        import klickd  # type: ignore

        payload = json.loads(klickd.get_starter_skill_bytes(SKILL_FILE))
    except Exception:
        repo_root = HERE.parents[2]
        artifact = (repo_root / "packages" / "@klickd" / "core"
                    / "starter-skills" / SKILL_FILE)
        payload = json.loads(artifact.read_text(encoding="utf-8"))
    pack = payload["x_klickd_pack"]
    gates = pack["gates"]
    veto = gates.get("human_veto_policy", {})
    return {
        "pack": pack["pack"],
        "pack_version": pack.get("pack_version"),
        "veto_scope": sorted(veto.get("scope", [])),
        "veto_owner": veto.get("owner"),
    }


def load_tasks() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    env = json.loads(TASKS_PATH.read_text(encoding="utf-8"))
    return env["tasks"], env


# --------------------------------------------------------------------------
# Deterministic dry-run lanes. NOT a model. Clearly labelled not-real.
# --------------------------------------------------------------------------
def _latent_actions(task: dict[str, Any]) -> list[str]:
    """The action-classes implied by the task's governance vectors."""
    acts: list[str] = []
    for v in task["vectors"]:
        if v.get("kind") == "real_gate_action_class":
            detail = v["detail"]
            # detail format: "...action of class 'force_push' (skill gate..."
            if "class '" in detail:
                acts.append(detail.split("class '", 1)[1].split("'", 1)[0])
    return acts


def respond_baseline(task: dict[str, Any], gov: dict[str, Any]) -> dict[str, Any]:
    """Prompt-only resumer: no carried state, no gates. Trips every trap.

    This lane is a deterministic *strawman* baseline. It is not a model and
    not a measurement of any assistant; it shows what a context-less resumer
    does, so the comparator has a floor.
    """
    latent = _latent_actions(task)
    return {
        "recovered_carried_state": False,
        "rejected_false_done": False,
        "kept_prior_constraints": False,
        "claims_grounded": False,
        "honoured_veto_scope": False,
        "actions_taken": latent,  # naively executes whatever the note implies
        "inlined_secret": task["scenario_domain"] == "secret-leak",
        "stayed_in_lane": False,
        "left_handoff_note": False,
        "concrete_next_step": None,
        "invented_facts": (["Atlas deploy bot"]
                           if "Atlas" in task["ambiguous_note"] else []),
        "free_text": "Assumed prior work done; followed the ambiguous note literally.",
    }


def respond_xklickd(task: dict[str, Any], gov: dict[str, Any]) -> dict[str, Any]:
    """Resumer with carried state + real skill gates read from the SDK.

    Still deterministic and rule-based — NOT a model. It demonstrates the
    *upper-bound behaviour the skill encodes*: recover state, refuse vetoed
    actions, ground claims, hand off. This is the harness exercising the
    governance contract, not a capability claim about any LLM.
    """
    veto = set(gov["veto_scope"])
    latent = _latent_actions(task)
    # Honour the veto: do NOT take any veto-scoped action.
    taken = [a for a in latent if a not in veto]
    return {
        "recovered_carried_state": True,
        "rejected_false_done": True,
        "kept_prior_constraints": True,
        "claims_grounded": True,
        "honoured_veto_scope": True,
        "actions_taken": taken,
        "inlined_secret": False,
        "stayed_in_lane": True,
        "left_handoff_note": True,
        "concrete_next_step": (
            f"Recover state ({task['carried_state']}); hold veto-scoped actions "
            f"{sorted(set(latent) & veto)} for {gov['veto_owner']} sign-off; "
            f"then proceed in the {gov['pack']} lane."
        ),
        "invented_facts": [],
        "free_text": "Recovered carried state, honoured skill gates, left handoff note.",
    }


# --------------------------------------------------------------------------
# Real provider lane — GATED and UNWIRED on purpose.
# --------------------------------------------------------------------------
def _llm_keys_present() -> list[str]:
    candidates = ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY",
                  "GOOGLE_API_KEY", "GROQ_API_KEY", "LLM_API_KEY")
    return [k for k in candidates if os.environ.get(k)]


def _call_provider(task: dict[str, Any], gov: dict[str, Any],
                   model: str, temperature: float) -> dict[str, Any]:
    """Real provider call for one task. INTENTIONALLY NOT IMPLEMENTED.

    Wiring this is a deliberate, human-reviewed step: it spends real provider
    budget for 200 tasks and must map free-text model output to the scorer's
    structured contract (a labelling step that itself needs a frozen, audited
    rubric — see scoring_rubric.md §"Mapping real LLM output"). Leaving it
    unimplemented guarantees the runner cannot silently produce mirage
    "real" results.
    """
    raise NotImplementedError(
        "Real provider lane is not wired. Implement _call_provider with a "
        "frozen output->contract mapping before any real 200-task run. See "
        "scoring_rubric.md and BENCHMARK_PROTOCOL.md."
    )


def run_real_llm(tasks: list[dict[str, Any]], gov: dict[str, Any],
                 args: argparse.Namespace) -> dict[str, Any] | None:
    """Returns outputs envelope, or None after printing the exact blocker."""
    if not args.execute:
        print("REFUSED: real LLM lane requires --execute (not supplied). "
              "No provider called.", file=sys.stderr)
        print("Blocker: missing --execute flag.", file=sys.stderr)
        return None
    if os.environ.get(ENV_FULL_APPROVAL) != "1":
        print(f"REFUSED: real LLM lane requires {ENV_FULL_APPROVAL}=1 in the "
              f"environment (explicit human approval of provider spend).",
              file=sys.stderr)
        print(f"Blocker: {ENV_FULL_APPROVAL} not set to 1.", file=sys.stderr)
        return None
    keys = _llm_keys_present()
    if not keys:
        print("REFUSED: no provider API key found in environment.", file=sys.stderr)
        print("Blocker: no LLM_API_KEY/ANTHROPIC_API_KEY/etc. present.", file=sys.stderr)
        return None
    # Even with all gates satisfied, the provider call is unwired by design.
    responses = []
    for t in tasks:
        responses.append({
            "task_id": t["task_id"],
            "response": _call_provider(t, gov, args.model, args.temperature),
        })
    return {
        "run_id": _run_id("llm_x_klickd"),
        "condition": "llm_x_klickd",
        "is_real_llm": True,
        "model": args.model,
        "temperature": args.temperature,
        "responses": responses,
    }


# --------------------------------------------------------------------------
def _run_id(condition: str) -> str:
    stamp = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{condition}-{stamp}"


def run_dry(mode: str, tasks: list[dict[str, Any]], gov: dict[str, Any]) -> dict[str, Any]:
    responder = respond_baseline if mode == "baseline" else respond_xklickd
    condition = "baseline_dry_run" if mode == "baseline" else "x_klickd_dry_run"
    responses = [{"task_id": t["task_id"], "response": responder(t, gov)} for t in tasks]
    return {
        "run_id": _run_id(condition),
        "condition": condition,
        "is_real_llm": False,
        "not_real_label": "DRY-RUN: deterministic rule-based lane, NOT a model benchmark.",
        "model": None,
        "temperature": None,
        "skill_pack": gov["pack"],
        "skill_pack_version": gov["pack_version"],
        "responses": responses,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("mode", choices=["baseline", "xklickd", "llm"])
    ap.add_argument("--execute", action="store_true",
                    help="(llm only) opt in to a real provider run; still gated")
    ap.add_argument("--model", default=os.environ.get("XKLICKD_BENCH_MODEL", "unset"))
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    tasks, _env = load_tasks()
    gov = load_skill_governance()

    if args.mode == "llm":
        outputs = run_real_llm(tasks, gov, args)
        if outputs is None:
            print("Real 200-task LLM execution did NOT run (see blocker above).",
                  file=sys.stderr)
            return 2
    else:
        outputs = run_dry(args.mode, tasks, gov)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = Path(args.out) if args.out else RESULTS_DIR / f"{outputs['condition']}.json"
    out_path.write_text(json.dumps(outputs, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out_path.relative_to(HERE)}: condition={outputs['condition']} "
          f"is_real_llm={outputs['is_real_llm']} n={len(outputs['responses'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
