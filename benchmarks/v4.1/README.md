# x.klickd v4.1 — Benchmark Harness

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
    --retry-max 2 \
    --execute
```

`--users` is capped at 10. `--concurrency` is in `[1, 8]` (default `1`).
Pilot output lives under
`benchmarks/v4.1/results/<date>/pilot/<run_id>/` with these files:

| File | Description |
| ---- | ----------- |
| `raw_outputs.jsonl` | One line per successful call: `run_id`, `condition`, `model`, `prompt_hash`, `output_hash`, `output_text`, latency, tokens, timestamp, provider metadata |
| `errors.jsonl` | One line per failed call after retries |
| `metrics_summary.json` | Aggregate counts, latency, tokens, by-condition counts |
| `run_manifest.json` | Run id, mode, provider, config, execution settings, fixture manifest reference, repo commit, counts |

The executor is **resumable**: re-invoking with the same `--run-id` skips
already-completed `run_id`s recorded in `raw_outputs.jsonl`.

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
