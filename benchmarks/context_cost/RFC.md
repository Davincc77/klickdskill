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

All numbers are reported per-run and aggregated as `min / median / max` over N runs (target N = 3 for v1).

The benchmark MUST NOT report a single "score". It MUST report the raw table.

## 7. Output tree

Each invocation of the runner writes to a dated directory:

```
benchmarks/context_cost/results/YYYY-MM-DD/
  ├── run.json         # machine-readable: scenarios, conditions, models, raw metrics
  ├── summary.md       # human-readable: per-scenario tables, aggregate medians
  ├── env.json         # SDK version, provider SDK versions, model IDs, sampling params
  └── prompts/         # exact prompts sent, per condition, for auditability
```

`YYYY-MM-DD` is the UTC date of the run. Multiple runs on the same day MUST not overwrite each other; the runner appends a suffix (`-2`, `-3`, …) when the directory already exists.

`run.json` is the source of truth. `summary.md` is regenerated from it.

## 8. Pass / fail criteria

RFC-003 v1 considers the benchmark **methodologically valid** (independent of the result) when:

1. Re-running the same scenario × condition × model on the same day produces token counts within ±2% (deterministic except for provider-side noise).
2. The `cold` condition reaches "useful" in strictly *more* exchanges than the `klickd` condition on at least one scenario, on at least one model — otherwise the scenarios are too easy and MUST be revised.
3. The `klickd` condition's `input_tokens` is *smaller* than the `paste` condition's `input_tokens` on every scenario × model pair — otherwise the `.klickd` payload is not earning its place vs. raw paste, and either the payload is over-stuffed or the scenario is mis-designed.
4. Every prompt sent during the run is captured under `prompts/` and is regeneratable from `run.json` + `env.json`.

A run that does not meet (1)–(4) is reported but flagged `methodology: invalid` in `run.json`.

## 9. Non-goals

- **Not a quality benchmark.** Answer quality is the job of the existing `benchmarks/` tree.
- **Not a vendor leaderboard.** Cross-vendor comparisons are reported as raw numbers; no aggregate ranking is produced.
- **Not a spec change.** RFC-003 introduces no payload field, no envelope field, and no behavioural rule on readers / writers.
- **Not a paywall.** Scenarios, prompts, and `run.json` outputs MUST be reproducible by any external contributor with their own API keys, without access to private fixtures.

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
