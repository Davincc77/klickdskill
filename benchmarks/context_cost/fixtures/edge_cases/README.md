# Edge-case fixtures (optional follow-up scenarios)

> **Non-normative, optional benchmark fixtures.** These scenarios are
> **not** part of the RFC-003 v1 core 10-run flow exercised by
> [`../prompts/flow.json`](../prompts/flow.json) and validated by
> [`../validation/ground_truth.json`](../validation/ground_truth.json).
> The v1 dry-run runner (`runner.py`) does not consume them.

## Purpose

These fixtures capture three review-driven edge cases the next runner
iteration should be able to exercise:

| Scenario | What it stresses |
|---|---|
| [`migration_version_break/`](./migration_version_break/) | Loading an older (`v3.0`) context with a v4-aware runner. Migration MUST warn but MUST NOT drop decision data. |
| [`tool_call_failure_recovery/`](./tool_call_failure_recovery/) | A tool call fails once; the agent MUST consult the artifact-tee log instead of blindly retrying or fabricating results. |
| [`multi_session_handoff/`](./multi_session_handoff/) | Decisions and handoff notes spread across three sessions. The resuming model MUST preserve every prior decision without asking Léa to re-explain. |

## Validation

A lightweight unit test ([`../../tests/test_edge_cases.py`](../../tests/test_edge_cases.py))
parses each fixture's JSON and cross-checks the structural expectations declared in
[`../validation/edge_ground_truth.json`](../validation/edge_ground_truth.json).
No model is invoked.

## What this is NOT

- Not part of the v1 dry-run runner's required input set.
- Not a spec change; RFC-003 remains `Draft`.
- Not a leaderboard, not a result.
