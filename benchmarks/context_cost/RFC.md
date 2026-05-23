# RFC-003 — Context Cost Benchmark

| | |
|---|---|
| **RFC** | 003 |
| **Title** | Reproducible measurement of "repeated context waste" with and without `.klickd` |
| **Target** | `.klickd v4` — research / benchmark track |
| **Status** | **Draft** |
| **Author** | Davincc77 + Team 2.0 (Klickd / Luxlearn, Luxembourg) |
| **Created** | 2026-05-22 |

> **This RFC is non-normative.** It targets a research / benchmark track for `.klickd v4`. It defines a measurement protocol, not a wire-format change. No part of this document is binding on any current v3.x reader or writer. Nothing in this RFC introduces, removes, or modifies any field of the `.klickd` envelope or payload.

---

## 1. Objective

Define a small, reproducible benchmark that quantifies the **context-restatement cost** a user incurs when interacting with an AI assistant across sessions, models, or vendors — and the reduction of that cost obtainable by injecting a `.klickd` payload at the start of each session.

Where the existing benchmark in [`benchmarks/`](../README.md) measures *pedagogical quality* (does the answer get better with `.klickd`?), RFC-003 measures **token / time / friction cost** of re-establishing context (how much does the user pay, before the answer even starts, to be understood again?).

The two benchmarks are complementary. RFC-003 is the cheaper, more mechanical one — and the one most directly tied to user-visible cost.

### 1.1 Sources of repeated context / computation waste (v1 catalogue)

The benchmark exists because real agent sessions repeatedly pay for information they already had. v1 considers the following waste sources in scope for measurement; new sources MAY be added in follow-up PRs as long as they are observable without modifying the `.klickd` envelope.

1. **Re-introducing the user.** A new session does not know who the user is, what they know, or how they want to be addressed. Measured by `cold` vs. `klickd` `input_tokens` and `exchanges_to_useful`.
2. **Re-pasting prior conversation.** The brute-force baseline (`paste` condition). Always works, always expensive; the most honest upper bound on context cost.
3. **Rerunning expensive commands to recover lost output.** When an agent loses or truncates the output of a costly verification command (test suites, large builds, remote fetches, DOI resolutions), the cheapest-looking next step is *re-execute*. This burns minutes, money, and rate-limit budget to recover information that already existed once. The benchmark MUST count this as waste even when the command itself succeeds — the cost is the *repetition*, not the failure. Maps directly to RFC-002 §8b.8 `verification_artifacts[]`.
4. **Re-deriving facts the prior session already grounded.** A claim that was `executed` (RFC-002 §8b.1) in the prior session is downgraded to `assumed` in the resume session because the provenance was not carried across. The benchmark approximates this via `condition_overhead_tokens` plus a rubric tag.
5. **Re-stating preferences after a vendor / model switch.** Tone, language, formatting conventions, accessibility needs. Same scenario, different vendor — does the user pay to re-explain?

This catalogue is descriptive, not exhaustive. The benchmark's job is to *measure* these costs in `cold` vs. `paste` vs. `klickd`, not to enumerate every possible waste mode.

### 1.2 Artifact-tee rule (normative for benchmark runs only)

Commands run by the benchmark runner that produce expensive output (anything intended to be inspected, asserted against, or referenced later) MUST tee their stdout / stderr into a deterministic artifact path. The required path shape is:

```
.test-output/<scenario-id>/<command-slug>.<ext>
```

or, for outputs produced as part of a dated run:

```
benchmarks/context_cost/results/YYYY-MM-DD[-N]/artifacts/<scenario-id>/<command-slug>.<ext>
```

The runner MUST:

- Write the artifact **before** parsing it (so a parse failure does not destroy the bytes).
- Record a pointer to the artifact in `run.json` under each affected run (suggested key: `verification_artifacts[]`, mirroring the RFC-002 §8b.8 shape — `id`, `command`, `artifact_path`, `status`, `query_hint`, `checked_at`, `retention`, `scope`).
- NOT re-execute a command solely to "see the output again" within the same run. If a downstream step needs the output, it MUST read the artifact (or use the `query_hint`).

This rule is normative only inside the RFC-003 benchmark runner. It does not impose any requirement on `.klickd` readers / writers in general — that scope belongs to RFC-002 §8b.8.

## 2. Comparison

| Axis | Existing `benchmarks/` | RFC-003 `benchmarks/context_cost/` |
|---|---|---|
| Question | Does `.klickd` improve answer quality? | Does `.klickd` reduce context-restatement cost? |
| Primary signal | LLM-as-judge pedagogical scoring | Token counts, latency, exchange counts |
| Stimuli | Tutoring exchanges across 11 profiles | Short cross-session resume scenarios |
| Dependency on judge model | High (scorer model in the loop) | Low (deterministic counting + thin LLM probe) |
| Reproducibility cost | Significant (full multi-turn sessions) | Low (small, scriptable scenarios) |

## 3. Core question

> Holding the user's underlying need constant, how much **input context** (in tokens, exchanges, and seconds-to-useful-answer) does a user have to re-supply when:
> (a) they start from scratch on a new agent / new session,
> (b) they paste a prior conversation log,
> (c) they inject a `.klickd` payload via the standard `<UserContext>` system-prompt block?

The benchmark must produce numbers that are:

- **comparable** across the three conditions above,
- **cheap to re-run** so external contributors can reproduce,
- **honest about variance** (multiple runs, reported with min / median / max).

## 4. Scope (v1)

In scope for the first iteration of the benchmark:

- A small, fixed set of **resume scenarios** (target: 3–5), each describing:
  - a "prior" session summary (what the user was doing),
  - a "resume" prompt (what the user asks next),
  - an expected *kind* of useful answer (rubric, not a fixed string).
- Three **conditions** per scenario:
  1. `cold` — no prior context provided to the agent.
  2. `paste` — prior session pasted verbatim as a user message (worst-case "do it manually" baseline).
  3. `klickd` — a `.klickd` payload loaded via the reference Python SDK and injected into the system prompt.
- A small **model matrix** (at least one open-weights model and one frontier model), reusing the model list already exercised in [`benchmarks/README.md`](../README.md) where possible.
- Deterministic-where-possible settings (temperature 0 or low, fixed seeds where the provider supports them).

**Explicitly out of scope for v1:**

- Cross-vendor cost normalisation (USD per condition). Tokens and latency only.
- Judge-model scoring of answer quality (that is the existing benchmark's job).
- Any new payload field. RFC-003 uses `.klickd` as it exists in v3.x, unchanged.

## 5. Installation note

The benchmark, when implemented in a follow-up PR, will depend on the reference Python SDK installed directly from this repository:

```bash
pip install "git+https://github.com/Davincc77/klickdskill.git@main#subdirectory=packages/pypi/klickd"
```

The current Python API surface used by the benchmark is intentionally minimal:

```python
from klickd import load_klickd, save_klickd
```

`load_klickd` is responsible for decrypting and returning the payload; the benchmark runner is responsible for turning that payload into a `<UserContext>` system-prompt block via the canonical helper documented in `SPEC.md` §12. No additional SDK surface is required for v1 of the benchmark.

## 6. Metrics

For each (scenario × condition × model × run) tuple, the runner records:

- `input_tokens` — total prompt tokens sent to the model (system + user, as reported by the provider where available; otherwise via a documented local tokenizer).
- `output_tokens` — completion tokens.
- `latency_ms_first_token` — time-to-first-token, when the provider exposes streaming; otherwise `null`.
- `latency_ms_total` — wall-clock total for the call.
- `exchanges_to_useful` — number of additional user turns required, by rubric, before the answer becomes useful (0 when the first response is already useful).
- `condition_overhead_tokens` — for the `paste` and `klickd` conditions, the number of *additional* input tokens vs. the `cold` baseline of the same scenario.
- `klickd_payload_bytes` — size of the injected `.klickd` payload (decrypted, canonicalised), reported only for the `klickd` condition.
- `commands_executed` — count of expensive verification commands actually invoked by the runner during this run. Counts re-executions; the lower bound for "no waste" is the number of *distinct* commands required by the scenario.
- `commands_reused_from_artifact` — count of times the runner answered a verification question by reading a previously-teed artifact (per §1.2) instead of re-executing. Higher is better; this is the direct signal that the artifact-tee rule is doing work.

All numbers are reported per-run and aggregated as `min / median / max` over N runs (target N = 3 for v1).

The benchmark MUST NOT report a single "score". It MUST report the raw table.

## 7. Output tree

Each invocation of the runner writes to a dated directory:

```
benchmarks/context_cost/results/YYYY-MM-DD/
  ├── run.json         # machine-readable: scenarios, conditions, models, raw metrics
  ├── summary.md       # human-readable: per-scenario tables, aggregate medians
  ├── env.json         # SDK version, provider SDK versions, model IDs, sampling params
  ├── prompts/         # exact prompts sent, per condition, for auditability
  └── artifacts/       # teed stdout/stderr of expensive verification commands (§1.2)
```

`YYYY-MM-DD` is the UTC date of the run. Multiple runs on the same day MUST not overwrite each other; the runner appends a suffix (`-2`, `-3`, …) when the directory already exists.

`run.json` is the source of truth. `summary.md` is regenerated from it.

## 8. Pass / fail criteria

RFC-003 v1 considers the benchmark **methodologically valid** (independent of the result) when:

1. Re-running the same scenario × condition × model on the same day produces token counts within ±2% (deterministic except for provider-side noise).
2. The `cold` condition reaches "useful" in strictly *more* exchanges than the `klickd` condition on at least one scenario, on at least one model — otherwise the scenarios are too easy and MUST be revised.
3. The `klickd` condition's `input_tokens` is *smaller* than the `paste` condition's `input_tokens` on every scenario × model pair — otherwise the `.klickd` payload is not earning its place vs. raw paste, and either the payload is over-stuffed or the scenario is mis-designed.
4. Every prompt sent during the run is captured under `prompts/` and is regeneratable from `run.json` + `env.json`.
5. Every expensive verification command invoked during the run is teed to an artifact path under `.test-output/` or the run's `artifacts/` directory per §1.2, and `commands_executed - commands_reused_from_artifact` is no larger than the number of *distinct* commands the scenario requires. A run that re-executes a command it already teed within the same run is reported but flagged `methodology: invalid`.

A run that does not meet (1)–(4) is reported but flagged `methodology: invalid` in `run.json`.

## 9. Non-goals

- **Not a quality benchmark.** Answer quality is the job of the existing `benchmarks/` tree.
- **Not a vendor leaderboard.** Cross-vendor comparisons are reported as raw numbers; no aggregate ranking is produced.
- **Not a spec change.** RFC-003 introduces no payload field, no envelope field, and no behavioural rule on readers / writers.
- **Not a paywall.** Scenarios, prompts, and `run.json` outputs MUST be reproducible by any external contributor with their own API keys, without access to private fixtures.

### 9.1 Relation to long-context models and context-window extension

RFC-003 is intentionally *not* a benchmark of context-window size, KV-cache offload, or any other GPU / runtime mechanism that expands what a single inference call can process. Those mechanisms address **capacity** (how much the model can fit in one call). RFC-003 addresses **repetition** (how much the user has to re-supply across calls, sessions, vendors).

To keep the framing honest, follow-up PRs in this track MAY add a fourth, non-normative comparison condition alongside `cold` / `paste` / `klickd`:

- `long_context` — the same prior session content as `paste`, but submitted to a model variant with an explicitly extended context window (where the provider exposes one). Measures whether raw capacity alone closes the gap.
- `hybrid` — `.klickd` payload **plus** the extended-context variant. Measures whether portable state and long context compose, i.e. whether a smaller `.klickd` block at the start of a long window is strictly cheaper / more useful than either alone.

If added, these conditions MUST follow the existing rules: same metrics (§6), same output tree (§7), same artifact-tee rule (§1.2), and no new payload field. The pass / fail criteria of §8 apply unchanged; in particular, `klickd_payload_bytes` is reported only for conditions that actually inject a `.klickd` payload (`klickd`, `hybrid`).

The expected reading of such a four-condition table is *not* "which one wins" but "where do they compose": longer context helps the model fit more; portable state helps the system repeat less. The two are complementary, not substitutes. This sub-section is descriptive — it does not commit the v1 runner to implementing the additional conditions.

*Framing prompted by a [DEV.to discussion](https://dev.to/davincc77/ai-agents-dont-have-a-memory-problem-they-have-an-architecture-problem-3pl6) with VoltageGPU; see [`ACKNOWLEDGEMENTS.md`](../../ACKNOWLEDGEMENTS.md) at the repository root.*

## 10. Next steps

This RFC is intentionally docs-only. Concrete follow-ups, each in a separate PR:

1. **Runner skeleton** — a minimal Python script under `benchmarks/context_cost/` that wires the three conditions through one model and writes `run.json`. No scenarios yet beyond a smoke test.
2. **Scenario fixtures** — 3 to 5 resume scenarios as JSON/YAML files, each with a prior summary, resume prompt, and rubric. Reviewed independently of the runner.
3. **Model matrix** — extend the runner to the model list aligned with `benchmarks/README.md`, with explicit `env.json` capture.
4. **First public run** — produce the first `results/YYYY-MM-DD/` directory and reference it from `benchmarks/README.md`.
5. **Promotion review** — once two independent contributors have reproduced a run, consider promoting this RFC from `Draft` to `Proposed`.

Each follow-up PR remains additive and reversible. Nothing in this track blocks or modifies the v3.x normative specification.

---

*This RFC follows the lifecycle and conventions described in [`docs/rfcs/README.md`](../../docs/rfcs/README.md).*
