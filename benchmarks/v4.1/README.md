# x.klickd v4.1 — Benchmark Harness

**Status:** scaffolding only. No large/expensive LLM batches have been run.
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
  evaluator/
    evaluator.py            Deterministic rubric scorer
    rubrics.json            Rubric definitions
  reference_runtime/
    rfc010_reference.py     NON-PRODUCTION RFC-010 reference runtime
  results/                  Outputs (gitignored except for .gitkeep)
  tests/                    Unit tests
```

## 1. Generate fixtures (no LLM)

```bash
python3 benchmarks/v4.1/fixtures/generator.py \
    --seed 4242 --users 500 --sessions-per-user 10 \
    --out benchmarks/v4.1/fixtures/generated
```

This produces:

- `personas.jsonl` — 500 personas
- `test_a_runs.jsonl` — 500 × 6 prompt families × 3 conditions = 9,000 run specs (Test A coverage exceeds the ~3,000 target so subsampling is supported)
- `test_b_sessions.jsonl` — 500 × 10 sessions = 5,000 session specs
- `manifest.json` — counts, seed, SHA-256 of each fixture file

Identical seeds produce byte-identical files.

## 2. Dry-run

```bash
python3 benchmarks/v4.1/runner/runner.py dry-run
```

Validates fixtures against the manifest, emits a planned-run manifest under
`benchmarks/v4.1/results/<date>/dry_run/planned_run.json`. **Never calls a
provider.**

## 3. Pilot (up to 10 users)

```bash
# With no API key: writes a planned manifest only.
python3 benchmarks/v4.1/runner/runner.py pilot --users 10

# With an LLM key set, still requires --execute to actually call:
LLM_API_KEY=sk-... python3 benchmarks/v4.1/runner/runner.py pilot --users 10 --execute
```

`--users` is capped at 10 by the harness. Without `--execute`, the runner
emits a planned manifest even if a key is present. The actual provider adapter
is intentionally not wired in this commit — a human must review and add it
before any real pilot.

## 4. Full run (500 users) — heavily gated

A full run requires ALL of:

1. CLI flag `--confirm-full-run`
2. Environment variable `XKLICKD_BENCHMARK_FULL_APPROVED=1`
3. A pre-flight snapshot directory at
   `benchmarks/v4.1/results/snapshots/<YYYY-MM-DD>/`

```bash
# This will refuse — by design — until all conditions are met
# AND a human has wired the provider adapter.
XKLICKD_BENCHMARK_FULL_APPROVED=1 \
    python3 benchmarks/v4.1/runner/runner.py full --confirm-full-run
```

See `BENCHMARK_PROTOCOL.md §6` for why a snapshot is required.

## 5. Evaluate

```bash
python3 benchmarks/v4.1/evaluator/evaluator.py \
    --input  benchmarks/v4.1/results/<date>/pilot/raw_runs.jsonl \
    --output benchmarks/v4.1/results/<date>/pilot/eval.jsonl
```

The evaluator is deterministic and rule-based. Token counts are
provider-reported when present, else heuristic (~4 chars/token) and labelled
as such.

## 6. RFC-010 reference runtime (Test B)

`reference_runtime/rfc010_reference.py` implements the minimum primitives
(`extract_facts`, `link_entities`, `retrieve`, `build_injection_context`,
`erase`) needed to run the `xklickd_compressed` Test B condition. It is
**rule-based, deterministic, and explicitly NON-PRODUCTION** — tagged
`rfc010-reference/0.1.0-nonprod`. It is not a memory layer, and not a Mem0
replacement.

## 7. Mem0

This harness makes **no Mem0 compatibility claim**. The `mem0` Test B
condition is `skipped` unless a local Mem0 install or `MEM0_API_KEY` is
detected; even when detected, it is reported as `mem0_present=true` without
asserting compatibility. See tests/test_no_mem0_claim.py.

## 8. Tests

```bash
python3 -m pytest benchmarks/v4.1/tests/ -v
```

Covers: fixture counts, determinism, no-LLM-in-dry-run, full-run guard,
no Mem0 claim, RFC-010 reference primitives.
