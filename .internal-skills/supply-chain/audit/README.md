# x.klickd supply-chain — audit-trail index + determinism record

**Status:** NON-NORMATIVE. Not a v4.1 GA release artefact. No publish / deploy /
merge / tag / release performed by this stage.

This directory holds the **first tool-backed automation stage** of the x.klickd
supply-chain protocol. It does **not** automate the full pipeline. It turns two
traceability elements from spec into artefacts that are actually generated,
hashed, and re-checkable by a script:

| File | What it is |
|---|---|
| `audit_trail_index.json` | A consultable index of the verifiable artifacts the supply chain operates on, the declared validation commands, an append-style event list, and a per-stage automation map. |
| `determinism_record.json` | Input file hashes, output file hashes, and a `deterministic_run_id` derived **only** from inputs, so identical inputs yield an identical id across runs and hosts. |

## Generate / re-check

```bash
# Write (or refresh) both artefacts:
python scripts/generate_supply_chain_audit.py

# Verify the on-disk artefacts are still in sync with current inputs (no write):
python scripts/generate_supply_chain_audit.py check
```

`generate` exits non-zero if a critical invariant fails (missing or changed
input, hash mismatch against the manifest, banned public-claim string, or an
obvious secret/PII pattern in the generated output). `check` exits non-zero on
any drift in the deterministic core.

## Determinism

- The inputs are the 42 NON-NORMATIVE x.klickd v4.1 candidate skill packs plus
  their manifest under `examples/v4.1/x-klickd-skills/` (43 inputs total).
- An input is counted **only** when its bytes exist on disk **and** hash-match
  the manifest — the same `artifact_loaded` + `sha256_matches_manifest` gate
  enforced by `scripts/verify_xklickd_skill_packs.py`. A catalogue entry alone
  is not a loaded skill.
- `deterministic_run_id` and `checked_artifacts_hash_summary` are computed over
  `(relative_path, sha256)` pairs only. They do **not** depend on timestamps,
  host, or run order.
- The only non-deterministic field, `generated_at`, is quarantined under
  `non_deterministic_zone` and is **excluded** from every hash.

## What is real vs. planned

`stage_automation` in `audit_trail_index.json` labels each pipeline stage:

- `tool` — backed by shipped, runnable automation (audit-trail index,
  determinism record, reproducibility check, pack hash verification, candidate
  mapping validation).
- `partial` — a tripwire, not a full implementation (the PII/secrets scan here
  guards only this stage's own generated output).
- `planned` — spec-only; no automation yet (diff report, threat model, license
  check, source-freshness check, private/public boundary check, context-graph
  generation, candidate-skill generation).
- `manual` — human/agent premium pass.

`validation_results` is intentionally **empty**: this generator records the
declared validation commands but does not run them, so it does not assert their
outcomes. Pre-filled "pass" values would be a mirage. The operator runs the
commands; the audit / CI captures the outcomes.

## Relation to the supply-chain spec

The full 18-stage build-process specification is documented separately in the
supply-chain RFC under `docs/rfcs/` (the docs-only spec PR; not merged here).
This stage is the narrow, executable slice of stage **15 (determinism /
reproducibility)** and the **audit-trail index** from that spec. Everything else
in the pipeline remains `planned` until separately implemented.
