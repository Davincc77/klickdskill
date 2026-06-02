# Reproducibility — Continuity-Hell v1 / coding-200

Everything here is reproducible offline except the gated real-LLM lane.

## Environment

- Python 3.10+ (CI uses the repo's default).
- The `klickd` SDK installed editable from the repo root: `pip install -e .`
  (source: `packages/pypi/klickd/`). The harness falls back to reading the
  repo artifact directly if the SDK is not importable, so a bare checkout also
  works.
- No network, no API key, no account needed for the dataset, the dry-run
  lanes, or scoring.

## Dataset reproducibility

`tasks.json` is **byte-stable** for a fixed seed (default `20260602`):

```bash
cd benchmarks/continuity-hell-v1/coding-200
python generate_tasks.py            # regenerate
python generate_tasks.py --check    # exit 0 iff on-disk == fresh generation
```

The dataset records the seed, the target skill `pack_version`, and a snapshot
of the real `coding.klickd` governance (`veto_scope`, gate action classes), so
the exact artifact tested is always traceable.

## Dry-run lanes (deterministic, offline)

```bash
python run_benchmark.py baseline    # -> results/baseline_dry_run.json
python run_benchmark.py xklickd     # -> results/x_klickd_dry_run.json
python score_outputs.py results/baseline_dry_run.json --out results/scored_baseline_dry_run.json
python score_outputs.py results/x_klickd_dry_run.json --out results/scored_x_klickd_dry_run.json
```

Expected, reproducibly:
- `baseline_dry_run` task pass-rate **0.00** (trips every trap).
- `x_klickd_dry_run` task pass-rate **1.00** (honours all gates).

These are floor/ceiling references, **not** model measurements.

## Validation tests

Run from the repo root (CI runs `pytest tests/ -q`):

```bash
python -m pytest tests/test_continuity_coding200.py -q
```

These assert: exactly 200 tasks, unique ids, ≥ 3 vectors each, no easy tasks,
schema validity, dataset byte-stability, deterministic scorer behaviour on
fixtures, both dry-run lanes diverge, and no forbidden public/claim language
leaks into the benchmark files.

## Real-LLM lane (gated — currently BLOCKED)

Reproducing the real measurement requires the human-gated steps in
`BENCHMARK_PROTOCOL.md §7`. Record in any real run:

- exact model id (`--model` / `XKLICKD_BENCH_MODEL`),
- temperature (frozen at `0.0`),
- prompt-template hash,
- provider `usage` when returned (token counts are heuristic otherwise, and
  labelled as such).

No real run has been performed in this PR; the lane is reported as BLOCKED.
