#!/usr/bin/env python3
"""Deterministic local demo: resuming an interrupted task, with vs without
x.klickd structured memory/skill context.

WHAT THIS IS
------------
A fully deterministic, offline simulation. It does NOT call any LLM or API.
It runs a tiny rule-based "resumer" twice over the same interrupted-task
fixture:

  * BASELINE  -- only the ambiguous resume prompt ("...ship it") is available.
  * X.KLICKD  -- the same prompt PLUS structured context read from a real
                 bundled x.klickd skill (the verification gates and human-veto
                 policy carried in `coding.klickd`) and the saved carrier
                 state (memory) from the fixture.

The point is to make the *value of carried structure* visible and reproducible
without a model in the loop. The governance rules the x.klickd path obeys are
read live from the SDK -- they are not hardcoded in this script.

WHAT THIS IS NOT
----------------
Not a model benchmark, not a performance/quality claim about any assistant,
and not evidence that any AI client natively supports .klickd. See the README
in this directory for the full truth boundary.

Run:
    python examples/dev-preview/run_demo.py

Writes results/comparison_scorecard.md next to this script and prints a summary.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
FIXTURE = HERE / "fixtures" / "interrupted_task.json"
SCORECARD = HERE / "results" / "comparison_scorecard.md"

# The verb in the ambiguous resume prompt that a naive resumer treats as
# "do whatever it takes to be done", and the risky default it expands to.
RISKY_SHIP_ACTIONS = ("force_push", "production_deploy")


def load_task() -> dict[str, Any]:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def load_skill_governance() -> dict[str, Any]:
    """Read real governance structure out of the bundled coding skill.

    Returns the human-veto scopes and verification-gate defaults that the
    x.klickd-guided resume path must honour. These come from the SDK, so the
    demo cannot drift from what the skill actually carries.
    """
    import klickd

    payload = json.loads(klickd.get_starter_skill_bytes("coding.klickd"))
    gates = payload["x_klickd_pack"]["gates"]
    veto = gates.get("human_veto_policy", {})
    return {
        "veto_owner": veto.get("owner"),
        "veto_scope": list(veto.get("scope", [])),
        "gate_defaults": gates.get("verification_gates_default", {}),
        "skill_pack": payload["x_klickd_pack"]["pack"],
        "skill_version": payload["x_klickd_pack"].get("pack_version"),
    }


def resume_baseline(task: dict[str, Any]) -> dict[str, Any]:
    """Resume using ONLY the ambiguous prompt -- no carried structure.

    With no memory of the failing test or the review channel, and no
    governance, a naive resumer reads "ship it" literally: declare done and
    push to main. It has no basis to know the test is red or that pushing to
    main is vetoed.
    """
    plan = [
        "Re-read the ambiguous prompt: 'continue where we left off and ship it'",
        "Assume prior work is complete (no carried task state available)",
        "Interpret 'ship it' as: push branch straight to main / deploy",
    ]
    return {
        "lane": "baseline",
        "inputs_available": ["ambiguous_resume_prompt"],
        "knows_test_is_failing": False,
        "ran_test_suite": False,
        "respected_human_veto": False,
        "planned_actions": plan,
        "risky_actions_taken": list(RISKY_SHIP_ACTIONS),
        "final_state": "Claimed 'shipped' with a failing test; pushed to main "
        "(a human-veto-scoped action) without sign-off.",
    }


def resume_with_xklickd(task: dict[str, Any], gov: dict[str, Any]) -> dict[str, Any]:
    """Resume using the carried memory (fixture carrier_state) + skill gates.

    The resumer now knows: a test is failing (carried task state), the agreed
    review channel (carried memory), and which actions require a human's
    sign-off (skill human-veto policy). It blocks the risky actions whose
    names appear in the skill's veto scope and follows the saved plan.
    """
    carrier = task.get("carrier_state", {})
    veto_scope = set(gov["veto_scope"])
    blocked = [a for a in RISKY_SHIP_ACTIONS if a in veto_scope]

    plan = [
        "Restore carried task state: header-row test is FAILING",
        "Fix the failing header-row assertion before claiming done",
        f"Run the saved test command: {carrier.get('test_suite_command')}",
        f"Follow the saved review channel: {carrier.get('review_channel')}",
        "Hold human-veto-scoped actions for explicit sign-off: "
        + ", ".join(blocked),
    ]
    return {
        "lane": "x.klickd",
        "inputs_available": [
            "ambiguous_resume_prompt",
            "carrier_state (carried memory)",
            f"skill gates from {gov['skill_pack']}",
        ],
        "knows_test_is_failing": True,
        "ran_test_suite": True,
        "respected_human_veto": True,
        "planned_actions": plan,
        "risky_actions_taken": [],
        "blocked_by_human_veto": blocked,
        "final_state": "Fixed the test, ran the suite, opened a PR for review; "
        "no human-veto-scoped action taken without sign-off.",
    }


def score(lane: dict[str, Any]) -> dict[str, Any]:
    """Deterministic scorecard metrics derived from a lane's outcome."""
    return {
        "recovered_task_state": lane["knows_test_is_failing"],
        "verified_before_done": lane["ran_test_suite"],
        "respected_human_veto": lane["respected_human_veto"],
        "risky_actions": len(lane["risky_actions_taken"]),
    }


def render_scorecard(
    task: dict[str, Any],
    gov: dict[str, Any],
    baseline: dict[str, Any],
    guided: dict[str, Any],
) -> str:
    sb = score(baseline)
    sg = score(guided)

    def yn(v: bool) -> str:
        return "yes" if v else "no"

    lines: list[str] = []
    lines.append("# Dev-preview comparison scorecard")
    lines.append("")
    lines.append(
        "Deterministic local demo (no LLM, no API key). Generated by "
        "`examples/dev-preview/run_demo.py`. **This is not a model benchmark.**"
    )
    lines.append("")
    lines.append(f"- Task: `{task['task_id']}` — {task['goal']}")
    lines.append(f"- Ambiguous resume prompt: \"{task['ambiguous_resume_prompt']}\"")
    lines.append(
        f"- Skill source: `{gov['skill_pack']}` "
        f"(pack_version `{gov['skill_version']}`), human-veto scope read live "
        f"from the SDK: `{', '.join(gov['veto_scope'])}`"
    )
    lines.append("")
    lines.append("## Outcome by lane")
    lines.append("")
    lines.append("| Metric | Baseline (prompt only) | With x.klickd context |")
    lines.append("|---|---|---|")
    lines.append(
        f"| Recovered interrupted task state | {yn(sb['recovered_task_state'])} "
        f"| {yn(sg['recovered_task_state'])} |"
    )
    lines.append(
        f"| Verified (ran tests) before 'done' | {yn(sb['verified_before_done'])} "
        f"| {yn(sg['verified_before_done'])} |"
    )
    lines.append(
        f"| Respected human-veto policy | {yn(sb['respected_human_veto'])} "
        f"| {yn(sg['respected_human_veto'])} |"
    )
    lines.append(
        f"| Risky actions taken without sign-off | {sb['risky_actions']} "
        f"| {sg['risky_actions']} |"
    )
    lines.append("")
    lines.append("## Baseline lane (prompt only)")
    lines.append("")
    for step in baseline["planned_actions"]:
        lines.append(f"- {step}")
    lines.append("")
    lines.append(f"**Final state:** {baseline['final_state']}")
    lines.append("")
    lines.append("## x.klickd lane (carried memory + skill gates)")
    lines.append("")
    for step in guided["planned_actions"]:
        lines.append(f"- {step}")
    lines.append("")
    lines.append(f"**Final state:** {guided['final_state']}")
    lines.append("")
    lines.append("## What this shows / does not show")
    lines.append("")
    lines.append(
        "- **Shows:** carrying structured task state + a skill's governance "
        "rules lets a resumer recover context and refuse vetoed actions, "
        "deterministically and offline."
    )
    lines.append(
        "- **Does not show:** any quality/performance claim about a real LLM, "
        "or that any AI client natively supports `.klickd`. The two lanes are "
        "rule-based simulations over a static fixture."
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    try:
        import klickd  # noqa: F401
    except ModuleNotFoundError:
        print(
            "klickd is not installed. From a fresh clone run:\n"
            "    python -m venv .venv && source .venv/bin/activate\n"
            "    pip install -e .",
            file=sys.stderr,
        )
        return 1

    task = load_task()
    gov = load_skill_governance()
    baseline = resume_baseline(task)
    guided = resume_with_xklickd(task, gov)

    SCORECARD.parent.mkdir(parents=True, exist_ok=True)
    SCORECARD.write_text(render_scorecard(task, gov, baseline, guided), encoding="utf-8")

    sb, sg = score(baseline), score(guided)
    print("Deterministic local demo (no LLM, no API key).")
    print(f"  Baseline : recovered_state={sb['recovered_task_state']} "
          f"verified={sb['verified_before_done']} "
          f"respected_veto={sb['respected_human_veto']} "
          f"risky_actions={sb['risky_actions']}")
    print(f"  x.klickd : recovered_state={sg['recovered_task_state']} "
          f"verified={sg['verified_before_done']} "
          f"respected_veto={sg['respected_human_veto']} "
          f"risky_actions={sg['risky_actions']}")
    print(f"\nScorecard written to: {SCORECARD.relative_to(HERE.parent.parent)}")

    # The demo is only meaningful if the two lanes actually diverge.
    assert sb != sg, "baseline and x.klickd lanes did not diverge"
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
