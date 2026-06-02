# Continuity-Hell v1 — coding-200

A **pilot** stress-test benchmark for a single skill lane: `x.klickd/coding`
(real artifact: `packages/@klickd/core/starter-skills/coding.klickd`).

> **Status:** pilot. **Reproducible, scientifically defensible protocol.**
> NOT scientific proof of any capability. NOT a public release or market
> claim. The public release remains v4.1.

## What this is

Phase 1 of the continuity benchmark programme: **200 adversarial,
multi-vector tasks on one skill** to *find weaknesses* in how the
`x.klickd/coding` skill carries continuity and governance through an
interrupted/handoff coding situation. It is **not** an A/B/C/D study — ABCD
comes later, after weaknesses found here are corrected (separately).

Each task hands a resumer an ambiguous note plus recoverable carried state,
then attacks across ≥ 3 of nine dimensions: continuity, constraint respect,
source discipline, governance/human-veto, security/no-leakage, correct skill
activation, handoff quality, actionability, and no hallucinated project facts.

The governance the tasks test (human-veto scope, gate action classes) is read
from the **real** `coding.klickd` via the SDK, so the dataset cannot drift from
the artifact under test.

## Layout

| File | Purpose |
|---|---|
| `BENCHMARK_PROTOCOL.md` | **Frozen** protocol: hypotheses, conditions, model/temp, thresholds, anti-mirage gate. |
| `scoring_rubric.md` | **Frozen** deterministic scoring rules + response contract. |
| `tasks.json` | Exactly 200 tasks (byte-stable for the recorded seed). |
| `generate_tasks.py` | Regenerates / `--check`s `tasks.json` from the real skill. |
| `run_benchmark.py` | Runner: deterministic dry-run lanes + a **gated** real-LLM lane. Redacts + asserts secret-clean before any write. |
| `secret_guard.py` | Single source of truth for secret detection + redaction (used by the runner and the artifact scanner). |
| `score_outputs.py` | Deterministic scorer (no LLM in the loop). |
| `results/` | Dry-run outputs + scored summaries. Real-LLM results only if genuinely run. |
| `failure_analysis.md` | Template to fill from scorer output after a real run. |
| `reproducibility.md` | Exact commands + environment to reproduce. |

## Quick start (offline, no API key)

```bash
# from repo root
pip install -e .

cd benchmarks/continuity-hell-v1/coding-200
python generate_tasks.py --check          # verify the 200-task dataset

python run_benchmark.py baseline          # deterministic floor lane
python run_benchmark.py xklickd           # deterministic ceiling lane
python score_outputs.py results/baseline_dry_run.json
python score_outputs.py results/x_klickd_dry_run.json
```

The two dry-run lanes are **deterministic and rule-based — not a model
benchmark.** They bound the metric (floor / ceiling) and prove the harness
runs offline. Expected: `baseline_dry_run` ≈ 0.00 task pass-rate;
`x_klickd_dry_run` = 1.00.

## Real 200-task LLM run

The real-LLM lane (`llm_x_klickd`) is the only lane that measures a model. It
spends real provider budget and is therefore **gated**:

```bash
python run_benchmark.py llm                 # prints exact blocker, refuses
```

It will not run until a human satisfies the gate in `BENCHMARK_PROTOCOL.md §7`
(explicit `--execute` + `XKLICKD_BENCHMARK_FULL_APPROVED=1` + provider key +
a human-wired, audited output→contract mapping). Until then the harness
reports the real-LLM lane as **BLOCKED**, never as a fabricated number.

## Anti-mirage guarantees

- No deterministic path ever emits `is_real_llm: true`.
- Dry-run output carries a `not_real_label`.
- The real provider call ships **unwired** (`NotImplementedError`) so no
  accidental spend or fake "real" results can occur.
- Scoring is deterministic and LLM-free.

## Secret safety (mandatory before any real run)

Provider API keys live **only** in the private environment or a secret manager.
A key must **never** be committed, logged, written to an artifact, or printed.
The harness enforces this rather than relying on discipline:

- **Redaction at the boundary.** Every output envelope is passed through
  `secret_guard.redact` and then `secret_guard.assert_clean` *before* it is
  written. Any provider-key shape, auth header, high-entropy token, or live
  provider env var value is replaced with `[REDACTED:<kind>]`; if anything
  secret-like survives, the runner refuses to write.
- **Preflight, value-blind.** `run_benchmark.py preflight` verifies a provider
  key **exists** (reporting only the env var **name**, never its value) and
  that `results/` is secret-clean — run it before a dry-run or a real run.
- **Artifact scanner.** `scripts/check_benchmark_secret_leakage.py` scans the
  results dir (or any path) and exits non-zero on any finding, printing only
  redacted previews. Wire it into CI / a pre-real-run gate.
- **Results record provenance, not secrets.** Envelopes record
  `provider/model/run_id` only — never headers, tokens, or env var values.

```bash
python run_benchmark.py preflight                       # key present? results/ clean?
python ../../../scripts/check_benchmark_secret_leakage.py   # scan artifacts (from this dir)
```

If you ever see a real secret in a log or artifact, treat the key as
compromised and rotate it immediately — do not just delete the file.
