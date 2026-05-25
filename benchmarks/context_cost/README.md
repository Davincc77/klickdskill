# `benchmarks/context_cost/` — Context Cost Benchmark (RFC-003)

This directory hosts the in-progress **Context Cost Benchmark** for `.klickd`.

- Specification: [`RFC.md`](./RFC.md) — RFC-003, Draft.
- Status: docs + fixtures + **local dry-run runner**. No provider API calls yet.
- Companion to the existing quality benchmark in [`../README.md`](../README.md).

## Local dry-run

The runner under [`runner.py`](./runner.py) is a **local, dry-run-only** harness.
It does **not** call any provider API, does **not** consume paid resources, and
does **not** produce real provider token counts.

What it does:

1. Loads fixtures from [`fixtures/`](./fixtures/).
2. Validates that [`baseline/system_prompt.txt`](./fixtures/baseline/system_prompt.txt)
   and [`klickd/sample_context.json`](./fixtures/klickd/sample_context.json) both
   contain the key facts listed in
   [`validation/ground_truth.json`](./fixtures/validation/ground_truth.json).
3. Confirms [`prompts/flow.json`](./fixtures/prompts/flow.json) carries exactly
   10 messages.
4. Computes a **deterministic whitespace token-proxy** per condition
   (`cold`, `paste`, `klickd`). This is a coarse approximation — NOT a
   provider token count and NOT comparable across tokenizers.
5. Computes **extended RFC-003 §6 metrics**, all deterministic and offline:
   - `input_token_estimate_heuristic` — `len(text)//4` BPE-ish proxy.
   - `input_token_estimate_tiktoken` — populated only if `tiktoken` is
     already installed locally. Never installs anything; never calls a
     network. Falls back to `0` and a clear "not installed" note.
   - `prompt_size_bytes` — UTF-8 byte length of the assembled prompt.
   - `context_duplication_avoided` — paste − klickd, per estimator.
   - `gate_decision_presence` — count of `decisions_locked`, allowed /
     forbidden / confirm-required tool permissions, and whether the ethics
     lock is present in the `.klickd` payload.
   - `continuity_fields_present` — boolean map of the structural continuity
     fields a v4 payload is expected to carry.
   - `missing_evidence_warnings` — diagnostic strings when the payload's
     `verification_artifacts` block is absent, malformed, or empty.
6. Writes outputs to `results/<YYYY-MM-DD>/`:
   - `summary.csv` — per-message proxy counts and totals.
   - `raw_runs.jsonl` — one record per (condition, message).
   - `report.md` — human-readable summary (now includes the extended
     metrics block and a Chimera.klickd v4.1 extrapolation section).
   - `extended_metrics.json` — full structured metrics dump.
   - `chimera_v41_extrapolation.json` — forward-looking projection.
   - `artifacts/sample_test.log` — copy of the fixture verification artifact,
     mirroring RFC-003 §1.2 artifact-tee rule.

### Usage

```bash
# validate fixtures only (no writes)
python benchmarks/context_cost/runner.py --check

# write a full dry-run report
python benchmarks/context_cost/runner.py

# run the tests
python -m unittest benchmarks.context_cost.tests.test_runner
```

### What this dry-run is NOT

- It is **not** a real benchmark of model behaviour.
- It does **not** produce real provider token counts; the token-proxy is a
  whitespace-split approximation only.
- It does **not** make any network requests.
- The numbers in `results/` are illustrative and labelled as approximations.

A future PR will add the actual model-calling runner; this dry-run gives
contributors something reproducible to wire CI / local checks against in the
meantime.

## Optional follow-up edge-case scenarios

A small set of **non-normative** edge-case fixtures lives under
[`fixtures/edge_cases/`](./fixtures/edge_cases/). They are NOT part of the v1
core 10-run flow and are NOT consumed by `runner.py` today — the next runner
iteration will exercise them. The current cases are:

- `migration_version_break/` — loading a pre-v4 context with a v4-aware runner.
  Migration MUST warn but MUST NOT drop decision data.
- `tool_call_failure_recovery/` — a tool fails once; the agent MUST consult the
  artifact-tee log instead of blindly retrying or fabricating output.
- `multi_session_handoff/` — decisions spread across three sessions. The
  resuming model MUST preserve every prior decision and handoff note.

Structural expectations live in
[`fixtures/validation/edge_ground_truth.json`](./fixtures/validation/edge_ground_truth.json)
and are spot-checked by
[`tests/test_edge_cases.py`](./tests/test_edge_cases.py).

## Chimera.klickd v4.1 — forward-looking extrapolation (non-normative)

The runner also emits a forward-looking projection for a hypothetical
`Chimera.klickd v4.1`, where the single `.klickd` payload becomes a base
context plus a set of domain "skill packs" (`core.Kai`, `core.KaiLegal`,
`core.MediaKai`, `core.Code`, `core.Edu`, `core.Health`, `core.Ops`).

Two activation strategies are compared:

| Strategy | What loads at session start | Why it matters |
|---|---|---|
| `base_plus_seven` | base `.klickd` payload + ALL 7 packs | upper-bound cost; pays for every domain regardless of relevance |
| `router_selected` | base `.klickd` payload + only the packs the router considers relevant to the turn (default: `core.Kai` + `core.Ops`) | lower-bound cost; pays only for what the current task needs |

Inputs are deterministic token estimates. The per-pack cost is an explicit
assumption (default: 850 heuristic tokens per pack, documented in
`chimera_v41_extrapolation.json`). The result is **not a measurement**: it is
an offline projection meant to bracket how much a router-selected activation
could save vs. unconditional loading.

The function `chimera_v41_extrapolation()` in `runner.py` is the canonical
entry point and accepts a custom `pack_token_costs` dict and a custom
`router_selection` tuple for what-if exploration. The connection to RFC-008
(`skill_pack_manifest`) is intentional: a router-selected activation is the
operational reading of an `agent_core` carrying a v4.1 skill-pack manifest.

This section is non-normative. v4.1 does not exist yet; the projection is
re-runnable with new assumptions as soon as real packs are drafted.

## Don't make the agent re-run the test suite to find the failure

The benchmark treats **re-running an expensive command to recover lost output** as a first-class context-waste source (see [`RFC.md` §1.1](./RFC.md#11-sources-of-repeated-context--computation-waste-v1-catalogue)). Concretely:

- The runner tees stdout / stderr of every expensive verification command into a deterministic artifact path — `.test-output/<scenario-id>/<command-slug>.<ext>` for ad-hoc runs, or `benchmarks/context_cost/results/YYYY-MM-DD[-N]/artifacts/...` inside a dated run. See [`RFC.md` §1.2](./RFC.md#12-artifact-tee-rule-normative-for-benchmark-runs-only) for the rule.
- Each artifact is referenced from `run.json` with the same shape as RFC-002 §8b.8 `verification_artifacts[]` (`id`, `command`, `artifact_path`, `status`, `query_hint`, `checked_at`, `retention`, `scope`) so downstream steps can answer "did this pass?" by reading the artifact instead of re-executing.
- Re-execution inside the same run is reported as `commands_executed - commands_reused_from_artifact > distinct_commands_required` and flags the run `methodology: invalid`.

This is the benchmark-runner analogue of RFC-002 §8b.8: the `.klickd` payload carries the *pointer* to durable evidence, and the runner is the producer that writes the bytes.
