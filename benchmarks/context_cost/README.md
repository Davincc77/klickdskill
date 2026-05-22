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
5. Writes outputs to `results/<YYYY-MM-DD>/`:
   - `summary.csv` — per-message proxy counts and totals.
   - `raw_runs.jsonl` — one record per (condition, message).
   - `report.md` — human-readable summary.
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

## Don't make the agent re-run the test suite to find the failure

The benchmark treats **re-running an expensive command to recover lost output** as a first-class context-waste source (see [`RFC.md` §1.1](./RFC.md#11-sources-of-repeated-context--computation-waste-v1-catalogue)). Concretely:

- The runner tees stdout / stderr of every expensive verification command into a deterministic artifact path — `.test-output/<scenario-id>/<command-slug>.<ext>` for ad-hoc runs, or `benchmarks/context_cost/results/YYYY-MM-DD[-N]/artifacts/...` inside a dated run. See [`RFC.md` §1.2](./RFC.md#12-artifact-tee-rule-normative-for-benchmark-runs-only) for the rule.
- Each artifact is referenced from `run.json` with the same shape as RFC-002 §8b.8 `verification_artifacts[]` (`id`, `command`, `artifact_path`, `status`, `query_hint`, `checked_at`, `retention`, `scope`) so downstream steps can answer "did this pass?" by reading the artifact instead of re-executing.
- Re-execution inside the same run is reported as `commands_executed - commands_reused_from_artifact > distinct_commands_required` and flags the run `methodology: invalid`.

This is the benchmark-runner analogue of RFC-002 §8b.8: the `.klickd` payload carries the *pointer* to durable evidence, and the runner is the producer that writes the bytes.
