# x.klickd v4.1 — Benchmark Protocol

**Status:** Draft harness. No large/paid LLM runs have been executed.
**Scope:** Local, reproducible, dry-run by default. Full runs require explicit
human approval, an environment variable, AND a CLI flag.
**Non-goals:** Publishing results, tagging releases, pushing to Zenodo/npm/PyPI.

This document describes the protocol for the two approved v4.1 benchmark tests.
The harness lives under `benchmarks/v4.1/` and is independent from the existing
benchmarks under `benchmarks/v3.5/` and `benchmarks/context_cost/`.

---

## 1. Tests

### Test A — Prompt-level value of x.klickd

| Item              | Value                                                              |
|-------------------|--------------------------------------------------------------------|
| Simulated users   | 500                                                                |
| Runs total        | ~3,000 (6 prompts/user × 500 users)                                |
| Conditions        | `no_klickd`, `xklickd_lite`, `xklickd_pro`                         |
| Allocation        | Each user runs each prompt under all three conditions (within-subj)|
| Metrics           | tokens, quality, coherence, gate respect, hallucinations, time, clarifications, output usefulness |

### Test B — Memory-level reference comparison

| Item              | Value                                                              |
|-------------------|--------------------------------------------------------------------|
| Simulated users   | 500                                                                |
| Sessions per user | 10                                                                 |
| Sessions total    | 5,000                                                              |
| Conditions        | `no_memory`, `prompt_history`, `xklickd_compressed` (RFC-010 reference runtime), `mem0` (optional, only if locally configured) |
| Metrics           | recall, entity linking, contradiction handling, retrieval precision, token efficiency, temporal consistency, false-memory injection |

Test B depends on a minimal RFC-010 *reference* runtime. The reference runtime
is rule-based and deterministic, clearly labelled as **non-production**, and
should not be confused with any future production memory layer.

---

## 2. Sampling plan

- **Seed:** Fixed integer seed (`--seed 4242` default). Identical seeds must
  produce byte-identical fixtures.
- **Persona pool:** Drawn from `fixtures/personas.json`. Personas are
  parameterised over: domain (8), level (5), language register (3), and
  tendency to ask clarifying questions (low/med/high).
- **Prompt families (Test A):** clarification-needed, factual, multi-step,
  ambiguous, gate-relevant, hallucination-prone (6 families). Each user gets
  one prompt from each family.
- **Session topics (Test B):** Drawn from `fixtures/topic_pool.json`. Each
  user receives a deterministic 10-session storyline that intentionally
  introduces recall, contradiction, and temporal-consistency probes.
- **Assignment:** Condition order is permuted per user using the seeded RNG
  to balance order effects.

---

## 3. Conditions

### Test A
- `no_klickd` — baseline system prompt, no x.klickd context.
- `xklickd_lite` — minimal x.klickd context block (persona + 1–2 anchors).
- `xklickd_pro` — full bundle (persona + gates + memory anchors + active goals).

### Test B
- `no_memory` — each session is independent; no prior session text supplied.
- `prompt_history` — full prior-session transcripts are concatenated.
- `xklickd_compressed` — RFC-010 reference runtime: extract → link → retrieve
  → inject → erase. Compressed, structured context.
- `mem0` — optional. Only enabled if `MEM0_API_KEY` or a local Mem0
  installation is detected. The harness MUST NOT claim Mem0 compatibility
  if neither is present; the runner will mark it `skipped`.

---

## 4. Metrics

### Test A
| Metric              | Computed by                                  |
|---------------------|----------------------------------------------|
| tokens              | Provider response if available; else heuristic estimate (4 chars/token), labelled as such |
| quality             | Rubric score 0–4 (see `evaluator/rubrics.json`) |
| coherence           | Rubric score 0–4                              |
| gate_respect        | Boolean per gate-relevant prompt              |
| hallucination_rate  | Detected_facts vs known-false anchors          |
| time_ms             | Wall-clock per run (LLM mode only)            |
| clarifications      | Count of clarifying turns elicited            |
| usefulness          | Rubric score 0–4                              |

### Test B
| Metric                    | Computed by                                            |
|---------------------------|--------------------------------------------------------|
| recall@k                  | Whether session-k probe recovers session-(k-n) fact    |
| entity_linking_f1         | Against gold entity map                                |
| contradiction_handling    | Rubric: ignored / acknowledged / resolved              |
| retrieval_precision       | Of injected context, share that is actually relevant   |
| token_efficiency          | Useful_tokens / total_injected_tokens                  |
| temporal_consistency      | Time-ordered fact recall                               |
| false_memory_injection    | Recovers a fact never stated → flagged                 |

All metrics are written as machine-readable JSON. Rubric scoring is initially
heuristic/deterministic; LLM-as-judge is gated behind the same approval flow as
provider calls.

---

## 5. Cost and risk gates

- **Dry-run default.** Without explicit flags, the harness never calls a
  provider, never writes outside `benchmarks/v4.1/results/`, and never
  consumes paid resources.
- **Pilot run** (`pilot`): up to 10 users. Designed to be < $5 in provider
  cost at typical token rates. Requires `LLM_API_KEY` (or a provider-specific
  variable such as `GEMINI_API_KEY`) AND `--execute` AND a `--provider`
  selection; otherwise the runner produces a planned-run manifest. Pilot
  execution writes `raw_outputs.jsonl`, `errors.jsonl`,
  `metrics_summary.json`, and `run_manifest.json`. Concurrency is capped at
  8 with a default of 1; batches are spaced by `--sleep-between-batches`.
  Transient provider failures (`429`, `500/502/503/504`, `UNAVAILABLE`,
  `RESOURCE_EXHAUSTED`, `DEADLINE_EXCEEDED`, read timeouts) are retried
  with exponential, jittered backoff. Defaults: `--retry-max 5`,
  `--retry-backoff 2`, `--retry-backoff-max 30`, `--retry-jitter 0.25`.
  Permanent errors (auth, config, schema) abort immediately and are
  written to `errors.jsonl` without consuming retry budget. Every row in
  both files records the per-attempt trace, the final error class, the
  `retried_attempts` count, and the `cumulative_retry_delay_s`.
  Pilot runs are resumable via `--run-id`. After a pilot, run
  `runner/audit.py <run_dir>` to verify completeness, condition balance,
  hash coverage, model consistency, and to scan for secret-like patterns.
- **Full run** (`--full`): blocked unless ALL of the following:
  - CLI flag `--confirm-full-run`
  - Environment variable `XKLICKD_BENCHMARK_FULL_APPROVED=1`
  - Pre-flight snapshot exists at `benchmarks/v4.1/results/snapshots/<date>/`
- **Mem0 condition** is `skipped` unless explicitly detected. The README and
  this document state that no Mem0 compatibility claim is made by this repo.
- **Snapshot requirement:** Before a full run, the harness must dump fixture
  hashes, code SHAs, and a planned-cost estimate to the snapshot directory.

---

## 6. Why full runs require explicit approval and a snapshot

A 500-user / 5,000-session run can easily exceed five-figure-dollar token
spend at frontier-model rates, and produces results that may end up cited as
benchmarks. To prevent (a) accidental spend, (b) irreproducible results, and
(c) post-hoc parameter tuning, every full run must be approved by a human, and
the exact fixture set + code state must be snapshotted *before* execution. Any
result without a corresponding snapshot is considered unverified and will not
be promoted.

---

## 7. Determinism guarantees

- Fixture generation is byte-deterministic for a given seed.
- The evaluator is deterministic for a given input.
- The runner records the seed, fixture SHA-256, and harness git SHA in every
  results manifest.
- Re-running with the same seed and inputs must produce identical fixtures and
  identical results in dry-run mode.

---

## 8. Out of scope for this commit

- Running the full benchmarks.
- Publishing, tagging, releasing, Zenodo, npm, PyPI.
- Modifying the 42 v4.1 skills or the public x.klickd site.
- Production memory runtime (the RFC-010 implementation here is a *reference*).

## 9. Provider fairness rules

Across the three Test A conditions for a given (user, prompt_family):

- The user message is **byte-identical**.
- The generation config (`model`, `temperature`, `top_p`, `max_output_tokens`)
  is identical.
- Only the condition-specific context block prepended to the system
  prompt differs (`no_klickd` → empty; `xklickd_lite` → persona + anchors;
  `xklickd_pro` → persona + gates + anchors + active goals).

Every call records `prompt_hash` (SHA-256 of the `{system, user}` JSON);
every successful response records `output_hash`. These hashes let the
audit step detect accidental drift between conditions.
