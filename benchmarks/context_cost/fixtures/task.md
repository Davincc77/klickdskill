# Task — Project-Management Agent Resume

> **Non-normative benchmark fixture for RFC-003.** This document describes the
> single task the model is asked to handle across all three RFC-003 conditions
> (`cold`, `paste`, `klickd`). The same task runs 10 times — once per user
> message in [`prompts/flow.json`](./prompts/flow.json).

## Persona

The user is **Léa**, a solo project manager at a small Luxembourg-based EdTech
team (3 engineers, 1 designer). She is preparing the **v4 launch** of an
internal tool, scheduled for **2026-06-15**. She works across two AI assistants
during the day and frequently resumes a planning conversation on a fresh model
after lunch.

## Agent role

A **project-management assistant**. The agent helps Léa:

- track open tasks and their owners,
- surface blockers,
- decide what to do next,
- draft short status updates.

The agent MUST NOT:

- send messages, emails, or post anywhere external,
- change calendars or shared docs,
- spend money or commit to vendors,
- promise features that are not in `decisions_locked`.

These constraints are encoded in
[`validation/ground_truth.json`](./validation/ground_truth.json) under
`forbidden_actions`.

## Repeatability

The same project-management task is exercised **10 times**, with each of the 10
user messages in `flow.json` standing in for a different mid-day resume moment.
Each message can be answered without external tools — only the project context
provided by the condition is needed.

A run that passes RFC-003 §8 demonstrates that the `klickd` condition lets the
agent answer with fewer input tokens than the `paste` condition (because the
context is structured, not pasted), while preserving the constraints declared
in `decisions_locked` and `tool_permissions`.

## Continuity facts the agent must preserve

These are checked by the validator against every answer, on every run:

1. Launch date is **2026-06-15** (locked).
2. The mobile build is **paused** pending a security review.
3. Léa speaks **French and English**; defaults to English in writing, French in
   voice.
4. The agent must address her as **Léa**, not "user" or "Madame".
5. No vendor commitment without Léa's explicit OK in the current turn.

See `validation/ground_truth.json` for the full machine-readable list.

## Out of scope

- Real project-management software integration (Linear, Jira, Notion).
- Multi-agent / handoff orchestration.
- Anything that requires model output to be `JSON-strict` — the benchmark
  measures **context cost**, not structured-output discipline.
