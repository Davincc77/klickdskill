# `integrations/hermes/` — Hermes Agent ↔ `.klickd` POC scaffold

> **Status:** Experimental POC for the *Build With Hermes Agent* challenge.
> **Not production.** Not part of the `.klickd` normative spec.
> No provider API calls. No paid resources. No CI integration. No release.

This directory hosts a small, self-contained scaffold that demonstrates:

- **Hermes Agent** as the *workflow runner* (orchestrates the steps).
- **`.klickd`** as the *portable state layer* (carries identity, context,
  decisions, verification artifact pointers across runs).

The concrete demo is to drive the existing **RFC-003 context-cost dry-run
benchmark** (`benchmarks/context_cost/runner.py`) from inside a Hermes session
and inspect its outputs, without making any provider calls.

---

## What's in this folder

```
integrations/hermes/
├── README.md                              # this file
├── skill/
│   └── SKILL.md                           # Hermes-facing skill instructions
├── plugin/
│   ├── plugin.yaml                        # plugin manifest (experimental)
│   └── __init__.py                        # plugin entry-point skeleton
├── scripts/
│   └── run_context_cost_benchmark.py      # wrapper script (no Hermes needed)
└── tests/
    ├── __init__.py
    └── test_wrapper.py                    # smoke tests for the wrapper
```

The wrapper script in `scripts/` works **without** Hermes — you can run it
directly and it just shells out to `benchmarks/context_cost/runner.py`.
The `skill/` and `plugin/` pieces are what a Hermes Agent would load.

---

## Prerequisites

- Python 3.10+ (same as the rest of the repo).
- A local clone of this repository.
- *Optional:* a working Hermes installation (`~/.hermes/`) — only needed if you
  actually want to drive the wrapper from inside a Hermes session. The wrapper
  and tests do **not** require Hermes.

This scaffold deliberately does not pin a Hermes version. The plugin manifest
declares itself `experimental`. If the local Hermes plugin API differs from
what's sketched here, treat `plugin/__init__.py` as pseudocode and adapt.

---

## Installing into a local Hermes

> Only do this if you have a local Hermes install and want to run the demo
> end-to-end. Skipping this section is fine — the wrapper still works.

```bash
# from the repo root

# 1. Copy (or symlink) the skill into your local Hermes skills directory.
mkdir -p ~/.hermes/skills/klickd-context-cost
cp integrations/hermes/skill/SKILL.md ~/.hermes/skills/klickd-context-cost/SKILL.md

# 2. Copy (or symlink) the plugin.
mkdir -p ~/.hermes/plugins/klickd-context-cost
cp -r integrations/hermes/plugin/* ~/.hermes/plugins/klickd-context-cost/
```

Symlinks are recommended during development so edits in the repo flow through
without re-copying:

```bash
ln -s "$PWD/integrations/hermes/skill"  ~/.hermes/skills/klickd-context-cost
ln -s "$PWD/integrations/hermes/plugin" ~/.hermes/plugins/klickd-context-cost
```

---

## Running the dry-run benchmark

The wrapper validates fixtures first (`runner.py --check`), then runs the full
dry-run, then prints the paths to the generated artifacts.

```bash
# from the repo root
python integrations/hermes/scripts/run_context_cost_benchmark.py

# validate only, no writes
python integrations/hermes/scripts/run_context_cost_benchmark.py --check
```

Outputs are written to `benchmarks/context_cost/results/<YYYY-MM-DD>/`:

- `summary.csv`
- `raw_runs.jsonl`
- `report.md`
- `artifacts/sample_test.log` (artifact-tee copy from the fixture)

See [`benchmarks/context_cost/README.md`](../../benchmarks/context_cost/README.md)
for what each file means and why the token numbers are a **whitespace proxy**,
not provider tokens.

---

## What this POC is — and isn't

**Is:**

- A scaffold showing how a Hermes Agent could call a `.klickd`-aware workflow.
- A safe, offline-only demonstration of the *runner-vs-state-layer* split.

**Is not:**

- A blessed Hermes plugin. The plugin API may not match exactly; treat it as
  experimental.
- A production integration. No retries, no error recovery, no telemetry.
- A benchmark of model behaviour. The wrapped runner is itself a dry-run
  whose numbers are whitespace approximations (RFC-003 §10).

---

## Safety constraints (hard rules for this POC)

- **No secrets.** No API keys, tokens, or credentials anywhere in this folder.
- **No network calls.** The wrapper only invokes the local dry-run runner.
- **No provider API calls.** Not in code, not in tests, not in CI.
- **No paid resources.**
- **No publishing / tagging / releasing** from this scaffold.
- **Do not modify SPEC / schemas / SDKs** to make this work.
- **Respect `verification_gates` and `human_veto`** (RFC-002) if the Hermes
  caller surfaces them — never bypass a gate to "make the demo run."
- **Don't re-run expensive commands** if their artifact already exists; read
  the artifact (RFC-003 §1.2 *artifact-tee rule*).

If a future change to this folder requires loosening any of the rules above,
that change belongs in a separate RFC, not here.
