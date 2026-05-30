# x.klickd v4.1 — Benchmark Harness

**DOI evidence pack:** the v4.1 benchmark evidence is archived on Zenodo under
version DOI [`10.5281/zenodo.20459934`](https://doi.org/10.5281/zenodo.20459934)
(record [zenodo.org/records/20459934](https://zenodo.org/records/20459934)).
This is candidate-track benchmark evidence only — it makes no claim of universal
native support, no automatic GDPR / EU AI Act compliance, and no superiority over
external benchmarks or competing systems.

**Status:** scaffolding + controlled pilot executor. No large/expensive LLM
batches have been run.
**Default mode:** dry-run. No provider calls happen without explicit human
approval, an environment variable, and a CLI flag.
**No publish / no tag / no release / no Zenodo / no npm / no PyPI.**

This harness implements the two approved v4.1 benchmark protocols (Test A,
Test B) described in [`BENCHMARK_PROTOCOL.md`](./BENCHMARK_PROTOCOL.md).

## Layout

```
benchmarks/v4.1/
  BENCHMARK_PROTOCOL.md     Protocol, metrics, rubrics, cost/risk gates
  README.md                 This file
  fixtures/
    generator.py            Deterministic fixture generator (JSONL)
    generated/              Generated fixtures (gitignored)
  runner/
    runner.py               Dry-run / pilot / full-run guard
    executor.py             Controlled pilot executor (logging, retries, resume)
    audit.py                Pilot output auditor (writes audit_report.md)
  providers/
    base.py                 Provider protocol + registry
    gemini_adapter.py       Gemini 2.5 Flash adapter (key from env)
    mock_provider.py        Deterministic in-process mock; never calls network
  prompts/
    test_a.py               Test A condition prompt builders + hashing
  evaluator/
    evaluator.py            Deterministic rubric scorer
    rubrics.json            Rubric definitions
  reference_runtime/
    rfc010_reference.py     NON-PRODUCTION RFC-010 reference runtime
  results/                  Outputs (gitignored except for .gitkeep)
  tests/                    Unit tests (provider is always mocked)
```

## Exact commands

### 1. Generate fixtures (no LLM)

```bash
python3 benchmarks/v4.1/fixtures/generator.py \
    --seed 4242 --users 500 --sessions-per-user 10 \
    --out benchmarks/v4.1/fixtures/generated
```

Produces `personas.jsonl`, `test_a_runs.jsonl`, `test_b_sessions.jsonl`,
`manifest.json`. Identical seeds produce byte-identical files.

### 2. Dry-run (never calls a provider)

```bash
python3 benchmarks/v4.1/runner/runner.py dry-run
```

Validates fixtures against the manifest, emits a planned-run manifest under
`benchmarks/v4.1/results/<date>/dry_run/planned_run.json`.

### 3. Pilot — plan only (no API calls)

```bash
python3 benchmarks/v4.1/runner/runner.py pilot --users 10
```

Without `--execute`, the runner emits a planned manifest only — even if
`GEMINI_API_KEY` is set.

### 4. Pilot — execute with Gemini (requires explicit approval)

After a human has reviewed the planned manifest:

```bash
export GEMINI_API_KEY=...   # or LLM_API_KEY / GOOGLE_API_KEY
python3 benchmarks/v4.1/runner/runner.py pilot \
    --users 10 \
    --provider gemini \
    --model gemini-2.5-flash \
    --temperature 0.2 \
    --max-output-tokens 512 \
    --concurrency 2 \
    --batch-size 10 \
    --sleep-between-batches 1.0 \
    --retry-max 5 \
    --retry-backoff 2 \
    --retry-backoff-max 30 \
    --retry-jitter 0.25 \
    --execute
```

`--users` is capped at 10. `--concurrency` is in `[1, 8]` (default `1`).
`--retry-max` is in `[0, 8]` (default `5`). Retries fire **only** on
transient provider errors — HTTP `429/500/502/503/504`, gRPC
`UNAVAILABLE` / `RESOURCE_EXHAUSTED` / `DEADLINE_EXCEEDED`, and read
timeouts. Permanent errors (auth, config, schema) abort immediately so
we do not waste quota. Backoff is exponential with jitter, base
`--retry-backoff` (default `2s`, cap `10s`), capped at
`--retry-backoff-max` (default `30s`, cap `30s`).
Pilot output lives under
`benchmarks/v4.1/results/<date>/pilot/<run_id>/` with these files:

| File | Description |
| ---- | ----------- |
| `raw_outputs.jsonl` | One line per successful call: `run_id`, `condition`, `model`, `prompt_hash`, `output_hash`, `output_text`, latency, tokens, timestamp, provider metadata, `retried_attempts`, `retry_attempts` (per-attempt error class/type/sleep), `cumulative_retry_delay_s` |
| `errors.jsonl` | One line per failed call after retries, including `attempts`, `final_error_class` (`transient` / `permanent` / `unhandled`), `retried_attempts`, `cumulative_retry_delay_s` |
| `metrics_summary.json` | Aggregate counts, latency, tokens, by-condition counts |
| `run_manifest.json` | Run id, mode, provider, config, execution settings, fixture manifest reference, repo commit, counts |

The executor is **resumable**: re-invoking with the same `--run-id`
makes zero new calls for any `run_id` already present in
`raw_outputs.jsonl`; only the missing rows are called.

### 5. Pilot — audit

```bash
python3 benchmarks/v4.1/runner/audit.py \
    benchmarks/v4.1/results/<date>/pilot/<run_id>
```

Writes `audit_report.md` and `audit_report.json` in the run directory.
Exits non-zero if any of these hard checks fail:

- Condition balance (`no_klickd` / `xklickd_lite` / `xklickd_pro` counts
  must be equal and non-zero across attempts).
- Missing `prompt_hash` or `output_hash`.
- Model id on a row differs from the manifest's model.
- Any output or manifest text matches a known secret pattern
  (`sk-...`, `AIza...`, `AKIA...`, `ghp_...`, Slack tokens, PEM keys).

Soft warnings (empty output text, missing provider tokens) appear in the
report but do not change the exit code.

### 6. Full run (500 users) — STILL refused

Full execution remains intentionally not wired in this commit. Even with
`--confirm-full-run`, `XKLICKD_BENCHMARK_FULL_APPROVED=1`, and a
pre-flight snapshot directory, the runner refuses and exits non-zero.

```bash
# Will refuse — by design. Do not run.
XKLICKD_BENCHMARK_FULL_APPROVED=1 \
    python3 benchmarks/v4.1/runner/runner.py full --confirm-full-run
```

### 7. Evaluate (rule-based)

```bash
python3 benchmarks/v4.1/evaluator/evaluator.py \
    --input  benchmarks/v4.1/results/<date>/pilot/<run_id>/raw_outputs.jsonl \
    --output benchmarks/v4.1/results/<date>/pilot/<run_id>/eval.jsonl
```

The evaluator is deterministic and rule-based. Token counts are
provider-reported when present, else heuristic (~4 chars/token) and labelled
as such.

## Fairness and determinism

- **Identical user prompt** across the three Test A conditions; only the
  condition-specific context block prepended to the system prompt differs.
- **Identical generation parameters** (model, temperature, top_p,
  max_output_tokens) for every call within a run.
- **`prompt_hash`** (SHA-256 of `{system, user}` JSON) recorded for every
  call; **`output_hash`** recorded for every successful call.
- The runner records the seed, fixture SHA-256, repo commit SHA, and full
  provider config in `run_manifest.json`.

## Test policy

```bash
python3 -m pytest benchmarks/v4.1/tests/ -v
```

Tests cover: fixture counts and determinism, no-LLM-in-dry-run, full-run
guard, no Mem0 claim, RFC-010 reference primitives, provider registry,
prompt-builder fairness and hash sensitivity, controlled-execution
artifacts, deterministic logs, concurrency validation, retry behaviour,
resumability, and audit detection of secret/model-mismatch issues. **No
network call is made by any test**, even if API keys are set.

## Bundle-based Test B — the "real project" design

The bundle Test B design evaluates **project continuity over time**
across multiple project types instead of testing every skill in
isolation. It is the design we recommend for any future Test B
publication.

| Item                  | Value                                                  |
| --------------------- | ------------------------------------------------------ |
| Project bundles       | 5 (AI App Launch, Video/Media, Security/Compliance, Research/Policy, Drone/Mission) |
| Sessions per bundle   | 150 (10 phases of 15 sessions)                         |
| Conditions            | 12 (see list below)                                    |
| Long pilot (1 bundle) | 1 × 150 × 12 = **1,800 outputs**                       |
| Full design           | 5 × 150 × 12 = **9,000 outputs**                       |

The 12 conditions all run the **same session scenario** for a given
(bundle, session). The user probe and generation config are
byte-identical across conditions; only the memory-architecture context
block changes. Conditions, in audit order:

1. `no_memory`
2. `prompt_history`
3. `manual_context_repetition`
4. `project_docs_only`
5. `xklickd_static_bundle`
6. `xklickd_compressed_bundle`
7. `xklickd_cross_session_resume`
8. `xklickd_cross_language`
9. `xklickd_cross_agent`
10. `xklickd_human_veto`
11. `xklickd_contradiction_handling`
12. `xklickd_ci_weakening_resistance`

Phases (1..150):

| Phase                       | Sessions |
| --------------------------- | -------- |
| scoping                     | 1–15     |
| requirements                | 16–30    |
| research/sources            | 31–45    |
| architecture/planning       | 46–60    |
| production/build            | 61–75    |
| language switch             | 76–90    |
| cross-agent/role handoff    | 91–105   |
| controlled contradictions   | 106–120  |
| security / human veto / CI  | 121–135  |
| final audit / delivery      | 136–150  |

### Scientific rationale

Memory architectures differ most where projects do: under contradictions,
role/agent handoffs, language switches, and security-driven veto
constraints. The 10-phase script is designed so each phase exercises a
different stressor; the 12 conditions probe a different memory
architecture against that same stressor sequence. Because the probe is
byte-identical across conditions and the only thing that differs is the
prepended context block, an LLM-as-judge or rubric evaluator can compare
conditions directly without confounding by prompt drift.

### Cost / throughput caution

A single long pilot (1 bundle × 150 sessions × 12 conditions = **1,800
outputs**) at frontier-model rates can already run into double-digit
US dollars depending on output length. The full 5-bundle design is
**9,000 outputs**. The runner therefore refuses to launch the full
design in a single command: full runs must be dispatched as **five
separate waves** (`--bundle-index 0..4`), each with explicit human
review of the prior wave's audit report before the next is launched.

### Generate the bundle fixtures (no LLM)

```bash
python3 benchmarks/v4.1/fixtures/bundles.py \
    --seed 4242 \
    --bundles 5 \
    --sessions-per-bundle 150 \
    --out benchmarks/v4.1/fixtures/generated_bundles
```

Identical seed produces byte-identical output (`test_b_bundle_sessions.jsonl`,
`test_b_bundle_facts.jsonl`, `test_b_bundles.jsonl`, `bundle_manifest.json`).

### Long pilot (one bundle, 1,800 outputs) — plan only

```bash
python3 benchmarks/v4.1/runner/runner.py pilot-test-b-bundles \
    --fixtures benchmarks/v4.1/fixtures/generated_bundles \
    --bundle-index 0 \
    --sessions-per-bundle 150 \
    --provider gemini \
    --concurrency 2
```

Without `--execute`, the runner emits a `planned_run.json` only — even
if `GEMINI_API_KEY` is set.

### Long pilot — execute with Gemini (after explicit human review)

```bash
export GEMINI_API_KEY=...
python3 benchmarks/v4.1/runner/runner.py pilot-test-b-bundles \
    --fixtures benchmarks/v4.1/fixtures/generated_bundles \
    --bundle-index 0 \
    --sessions-per-bundle 150 \
    --provider gemini \
    --model gemini-2.5-flash \
    --temperature 0.2 \
    --max-output-tokens 512 \
    --concurrency 2 \
    --batch-size 10 \
    --sleep-between-batches 2.0 \
    --retry-max 5 \
    --retry-backoff 2 \
    --retry-backoff-max 30 \
    --retry-jitter 0.25 \
    --execute
```

Caps enforced by the runner: `--bundles ≤ 1`, `--concurrency ∈ [1, 2]`,
`--sessions-per-bundle ≤ 150`, `--retry-max ≤ 8`. The full design flag
`--full-design` is intentionally refused.

The executor is **resumable**: re-invoking with the same `--run-id`
makes zero new calls for any `run_id` already present in
`raw_outputs.jsonl`.

### Audit the long pilot

```bash
python3 benchmarks/v4.1/runner/audit_b_bundles.py \
    benchmarks/v4.1/results/<date>/pilot_test_b_bundles/<run_id>
```

Hard checks: condition balance across all 12 conditions, bundle / phase
/ session / role coverage, hash completeness, secret scan, forbidden
claims, missing timestamps. Soft checks: per-condition cost curves and
session-depth token growth.

### CI dispatch (GitHub Actions)

The `Benchmark v4.1 — Gemini Test B Bundle Long Pilot (controlled)`
workflow (`.github/workflows/benchmark-v41-pilot-testb-bundles.yml`) is
**manual-only** (`workflow_dispatch`). It hard-caps `bundle_index` to
`[0, 4]`, `concurrency` to `[1, 2]`, and `sessions_per_bundle` to
`[1, 150]`. Default `execute` is `false` so the first dispatch only
emits a planned manifest. Five waves total are required for the full
design.

### Future full benchmark (5 waves)

The full 9,000-output design is intentionally **not** launchable from a
single command. To produce it, dispatch the workflow five times with
`bundle_index = 0, 1, 2, 3, 4` between manual audit reviews. Each
dispatch produces 1,800 outputs and a per-wave audit report. The
results from all five waves can then be aggregated offline.

## RFC-010 reference runtime (Test B)

`reference_runtime/rfc010_reference.py` implements minimum primitives needed
to run the `xklickd_compressed` Test B condition. It is **rule-based,
deterministic, and explicitly NON-PRODUCTION** — tagged
`rfc010-reference/0.1.0-nonprod`. Not a memory layer, not a Mem0
replacement.

## Mem0

This harness makes **no Mem0 compatibility claim**. The `mem0` Test B
condition is `skipped` unless a local Mem0 install or `MEM0_API_KEY` is
detected. See `tests/test_no_mem0_claim.py`.
