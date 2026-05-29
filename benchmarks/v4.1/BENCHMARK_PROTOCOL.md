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

## 9. Bundle-based Test B ("real project" final design)

This section supersedes the earlier per-user Test B description for any
future Test B publication. The earlier per-user variant remains in the
harness for backwards compatibility with existing tests, but the
**bundle design is the recommended Test B**.

### 9.1. Goal

Evaluate **real project continuity over time** across multiple project
types. The goal is not to test 42 skills individually but to stress
memory architecture under a realistic 150-session, 10-phase project
lifecycle, repeated across 5 project bundles.

### 9.2. Bundles

| Bundle ID                       | Title                       | Roles |
| ------------------------------- | --------------------------- | ----- |
| `b01_ai_app_launch`             | AI App Launch               | product-manager, project-operator, llm-agent-engineering, privacy-product, trust-evidence, security-incident-response, technical-writer |
| `b02_video_media_campaign`      | Video/Media Campaign        | media-planner, video-production-pipeline, rights-guard, social-literacy, evidence-desk, project-operator, technical-writer |
| `b03_security_compliance`       | Security/Compliance         | llm-agent-security, identity-access-management, gdpr-readiness, eu-ai-act, privacy-product, trust-evidence, security-incident-response |
| `b04_research_policy_publication` | Research/Policy Publication | literature-review, evidence-desk, policy-analyst, technical-writer, privacy-product, trust-evidence, social-literacy |
| `b05_drone_mission_ops`         | Drone/Mission Ops           | drone-operator, mission-control, edge-ai-operator, security-incident-response, rights-guard, trust-evidence, technical-writer |

### 9.3. Phases (per bundle, 150 sessions)

| Phase | Label                          | Sessions |
| ----- | ------------------------------ | -------- |
| p01   | scoping                        | 1–15     |
| p02   | requirements                   | 16–30    |
| p03   | research/sources               | 31–45    |
| p04   | architecture/planning          | 46–60    |
| p05   | production/build               | 61–75    |
| p06   | language switch                | 76–90    |
| p07   | cross-agent/role handoff       | 91–105   |
| p08   | controlled contradictions      | 106–120  |
| p09   | security/human veto/CI         | 121–135  |
| p10   | final audit/delivery/postmortem | 136–150 |

### 9.4. Conditions (12, applied identically to every session)

1. `no_memory` — no prior context.
2. `prompt_history` — full prior session turns concatenated.
3. `manual_context_repetition` — user-style restatement of recent decisions.
4. `project_docs_only` — structured project doc snapshot, no transcripts.
5. `xklickd_static_bundle` — full bundle definition embedded.
6. `xklickd_compressed_bundle` — RFC-010 compressed facts + bundle anchors.
7. `xklickd_cross_session_resume` — resume marker + last-phase snapshot.
8. `xklickd_cross_language` — compressed facts + language-switch policy.
9. `xklickd_cross_agent` — compressed facts + role-handoff policy.
10. `xklickd_human_veto` — compressed facts + human-veto policy.
11. `xklickd_contradiction_handling` — compressed facts + contradiction rule.
12. `xklickd_ci_weakening_resistance` — compressed facts + CI policy.

For a given (bundle, session), the **user probe is byte-identical
across the 12 conditions**, and the generation config is identical.
The only thing that varies is the system-prompt context block.

### 9.5. Output counts

| Run mode         | Outputs                          |
| ---------------- | -------------------------------- |
| Long pilot       | 1 bundle × 150 sessions × 12 conditions = **1,800** |
| Full design      | 5 bundles × 150 sessions × 12 conditions = **9,000** |

The full design is **not** a single launch. It is **five waves** of the
long pilot, one per bundle, each separated by manual review of the
prior wave's audit report.

### 9.6. Cost and throughput caution

At Gemini 2.5 Flash rates the long pilot is feasible as a paid run, but
the full design at frontier-model output rates can be substantial. The
runner enforces concurrency ≤ 2, a default 2 s inter-batch sleep, and
exponential backoff with jitter (defaults: `--retry-max 5`,
`--retry-backoff 2`, `--retry-backoff-max 30`, `--retry-jitter 0.25`,
hard caps `[8, 10, 30, 1]`). Resumability is per-run-id.

### 9.7. Audit

`runner/audit_b_bundles.py` runs the following **hard checks** (each
must pass for the audit to PASS):

- Condition balance across all 12 bundle conditions.
- Bundle / phase / session coverage matches manifest expectations.
- Role coverage — every role from the manifest appears.
- Hash completeness (`prompt_hash`, `output_hash`).
- Secret scan (no API key, PEM, or token strings in outputs/manifest).
- Forbidden claims — outputs and manifest must not assert
  memory-vendor compatibility, "full benchmark result", or
  similarly-overreaching claims.
- Missing timestamps — every row has `timestamp_utc`.

Soft checks (warnings, not failures): per-condition cost curves
(tokens, latency), session-depth token growth per condition, empty
output text, missing provider tokens.

### 9.8. Exact dispatch command for the long pilot

```bash
gh workflow run benchmark-v41-pilot-testb-bundles.yml \
    -f bundle_index=0 \
    -f sessions_per_bundle=150 \
    -f concurrency=2 \
    -f seed=4242 \
    -f provider=gemini \
    -f execute=true \
    -f retry_max=5 \
    -f retry_backoff=2 \
    -f retry_backoff_max=30 \
    -f sleep_between_batches=2
```

To launch a plan-only dry run, set `execute=false`. To launch the full
design (5 bundles), dispatch the workflow **five times** with
`bundle_index = 0, 1, 2, 3, 4`, reviewing each wave's audit report
before launching the next.

---

## 11. Provider fairness rules

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
