# `llm_x_klickd` — BLOCKED (no real run performed)

The real 200-task LLM lane has **not** been executed. No provider was called.
No `is_real_llm: true` results exist in this directory, and none were
fabricated.

## Exact blocker

The real run is gated by `BENCHMARK_PROTOCOL.md §7`. To proceed, a human must:

1. Pass `--execute` to `run_benchmark.py llm`.
2. Set `XKLICKD_BENCHMARK_FULL_APPROVED=1` (explicit approval of provider spend
   for 200 generations).
3. Provide a provider API key in the environment.
4. Implement `_call_provider` in `run_benchmark.py` with a **frozen, audited
   output→contract mapping** (see `scoring_rubric.md §"Mapping real LLM
   output"`). It ships unwired (`NotImplementedError`) on purpose so no
   accidental spend or mirage result can occur.
5. Pass the **secret-safety preflight**: `python run_benchmark.py preflight`
   green (provider key present by name only; `results/` clean) and
   `scripts/check_benchmark_secret_leakage.py` reporting no findings
   (`BENCHMARK_PROTOCOL.md §7` item 5, §10).

Items 1–3 were intentionally **not** satisfied in the PR that introduced this
harness, and item 4 is a deliberate, separately-reviewed step. The runner
demonstrably refuses and prints the blocker:

```
$ python run_benchmark.py llm
REFUSED: real LLM lane requires --execute (not supplied). No provider called.
Blocker: missing --execute flag.

$ python run_benchmark.py llm --execute
REFUSED: real LLM lane requires XKLICKD_BENCHMARK_FULL_APPROVED=1 ...
Blocker: XKLICKD_BENCHMARK_FULL_APPROVED not set to 1.
```

## Secret safety

The harness never reads a provider key value into any output: every envelope is
redacted and asserted secret-clean before it is written, and `preflight`
reports only env var **names**. No key, header, or token can be committed,
logged, or written to an artifact. See `BENCHMARK_PROTOCOL.md §10`.

## Required input to unblock

Explicit human go-ahead to spend provider budget on a 200-task run, plus a
reviewed implementation of the output→contract mapping, **and** a green
secret-safety preflight (item 5). Once those exist, run the gated command and
fill in `failure_analysis.md` from the scorer output.
