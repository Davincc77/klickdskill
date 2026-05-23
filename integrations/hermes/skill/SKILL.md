---
name: klickd-context-cost
description: Drive the .klickd RFC-003 context-cost dry-run benchmark from a Hermes Agent session, using .klickd as the portable state layer. Experimental POC — no provider API calls, no paid resources.
metadata:
  status: experimental
  scope: poc
  spec_refs:
    - benchmarks/context_cost/RFC.md
    - docs/rfcs/RFC-002-verification-gates.md
---

# Skill: `klickd-context-cost`

Hermes is the **workflow runner**. `.klickd` is the **portable state layer**.
This skill orchestrates the existing local dry-run benchmark in
`benchmarks/context_cost/` and reads its outputs — it does **not** call any
provider, does **not** spend tokens, and does **not** publish anything.

If anything in the runtime environment conflicts with the safety rules below,
**stop and report**. Do not "work around" a safety rule to make the demo run.

---

## What you are doing

1. Load the user's `.klickd` context (the portable state layer).
2. Validate the benchmark fixtures (`runner.py --check`).
3. Run the dry-run benchmark.
4. Inspect the generated `report.md`, `summary.csv`, and `artifacts/` copy.
5. Summarize results back to the user — point at file paths, do not re-paste
   large bodies of output.

You are *driving* the runner. The runner itself is the source of truth for
the numbers; do not invent or recompute them.

---

## Inputs

- The current repo root (assume CWD or detect with `git rev-parse --show-toplevel`).
- Optionally a `.klickd` payload provided by the user. If none is provided,
  use the fixture at
  `benchmarks/context_cost/fixtures/klickd/sample_context.json` as the demo
  state layer.

## Outputs

- A short text summary (≤ 10 lines) with:
  - Whether the `--check` step passed.
  - Whether the full run produced all four expected files.
  - The relative paths of `report.md`, `summary.csv`, `raw_runs.jsonl`, and the
    `artifacts/` directory.
- Do **not** dump the full `report.md` or CSV contents inline unless the user
  explicitly asks. The artifacts are the durable evidence (see *no re-runs*
  below).

---

## Procedure

1. **Load `.klickd` state.**
   - Read the payload (user-supplied or the fixture).
   - If it is encrypted, do not attempt to decrypt here — this POC operates on
     plaintext fixtures only. Report and stop.
   - Strip `_`-prefixed fields before any downstream use.

2. **Check for an existing dated result directory.**
   - Today's UTC date in `YYYY-MM-DD` format.
   - If `benchmarks/context_cost/results/<today>/report.md` already exists,
     **do not re-run** the benchmark. Read the existing artifacts and report
     their paths. This is the RFC-003 §1.2 *artifact-tee* rule: re-running an
     expensive command when its artifact already exists is a context-waste
     anti-pattern.

3. **Validate fixtures (`--check`).**
   - Invoke the wrapper:
     `python integrations/hermes/scripts/run_context_cost_benchmark.py --check`
   - On non-zero exit, stop and surface stderr.

4. **Run the dry-run benchmark.**
   - Invoke the wrapper:
     `python integrations/hermes/scripts/run_context_cost_benchmark.py`
   - On non-zero exit, stop and surface stderr.

5. **Inspect outputs.**
   - Locate `benchmarks/context_cost/results/<today>/`.
   - Confirm `summary.csv`, `raw_runs.jsonl`, `report.md`, and
     `artifacts/sample_test.log` exist.
   - Read only `report.md` to extract the per-condition totals.

6. **Summarize.** See *Outputs* above.

---

## Verification gates and human-veto

If the calling `.klickd` payload (or the Hermes session) declares
`verification_gates` or a `human_veto` per RFC-002:

- **Never bypass a gate** to make the benchmark run.
- If a gate is in the `pending` state for any step in this skill, halt and ask
  the human to resolve it. Do not silently proceed.
- If `human_veto` is set, treat it as a hard stop regardless of any other
  signal.

This is a POC, not a privileged path. The gates exist precisely so that
agent-driven workflows cannot quietly escalate.

---

## Do not re-run expensive commands

The RFC-003 *artifact-tee rule* (§1.2) treats re-execution as a first-class
source of context waste. Concretely, in this skill:

- If today's `report.md` exists, **read it; do not re-run**.
- If `artifacts/sample_test.log` exists in today's results dir, treat it as
  the verification artifact and reference it by path — do not re-execute the
  underlying check.
- If you need a fresh run (e.g. fixtures changed), say so explicitly in the
  summary and only then call the wrapper.

---

## Hard safety rules

- **No provider API calls** under any circumstances from this skill.
- **No paid resources.**
- **No secrets** in the `.klickd` payload should ever be logged or echoed.
- **No network requests.** The wrapper is local-only.
- **No SPEC / schema / SDK edits** from this skill.
- **No publishing** (no git push, no tag, no release, no artifact upload).
- If unsure, **stop and ask**.
