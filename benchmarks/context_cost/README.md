# `benchmarks/context_cost/` — Context Cost Benchmark (RFC-003)

This directory hosts the in-progress **Context Cost Benchmark** for `.klickd`.

- Specification: [`RFC.md`](./RFC.md) — RFC-003, Draft.
- Status: docs-only. No runner, no fixtures, no results yet.
- Companion to the existing quality benchmark in [`../README.md`](../README.md).

When the runner lands in a follow-up PR, results will be written to:

```
benchmarks/context_cost/results/YYYY-MM-DD/
```

See [RFC.md §10 — Next steps](./RFC.md#10-next-steps).

## Don't make the agent re-run the test suite to find the failure

The benchmark treats **re-running an expensive command to recover lost output** as a first-class context-waste source (see [`RFC.md` §1.1](./RFC.md#11-sources-of-repeated-context--computation-waste-v1-catalogue)). Concretely:

- The runner tees stdout / stderr of every expensive verification command into a deterministic artifact path — `.test-output/<scenario-id>/<command-slug>.<ext>` for ad-hoc runs, or `benchmarks/context_cost/results/YYYY-MM-DD[-N]/artifacts/...` inside a dated run. See [`RFC.md` §1.2](./RFC.md#12-artifact-tee-rule-normative-for-benchmark-runs-only) for the rule.
- Each artifact is referenced from `run.json` with the same shape as RFC-002 §8b.8 `verification_artifacts[]` (`id`, `command`, `artifact_path`, `status`, `query_hint`, `checked_at`, `retention`, `scope`) so downstream steps can answer "did this pass?" by reading the artifact instead of re-executing.
- Re-execution inside the same run is reported as `commands_executed - commands_reused_from_artifact > distinct_commands_required` and flags the run `methodology: invalid`.

This is the benchmark-runner analogue of RFC-002 §8b.8: the `.klickd` payload carries the *pointer* to durable evidence, and the runner is the producer that writes the bytes.
