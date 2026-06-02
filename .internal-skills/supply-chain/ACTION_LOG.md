# `.internal-skills/supply-chain/ACTION_LOG.md` — append-only internal action log

> Internal · NON-NORMATIVE. Append-only. Records actions, validations, and
> limitations for supply-chain runner/gate work. No external action is recorded
> here because none was taken (no release, tag, DOI, publish, deploy, or
> communication). The private repo `Davincc77/klickd-ai` was not touched.

---

## 2026-06-02 — candidate generator + promotion gate (v0.1)

- **Branch:** `feat/supply-chain-runner-gate`, stacked on
  `integration/supply-chain-cumulative` (PR #121).
- **Base for PR:** `integration/supply-chain-cumulative` (NOT `main`).

### Added
- `scripts/generate_supply_chain_candidate.py` — internal candidate generator
  (runner). Config-only `build_request` JSON → candidate skill in the internal
  v4.2 target shape under `.internal-skills/supply-chain/candidates/` or
  `--out`. Deterministic: `candidate_id` / `candidate_hash` / `run_id` derived
  only from canonical build_request bytes (+ resolved source manifest hash).
  No `generated_at` in the hashed core. Sources come only from the
  build_request / referenced source_manifest; missing domain info →
  `requires_human_premium_pass`, never hallucinated.
- `scripts/run_supply_chain_promotion_gate.py` — combined promotion gate.
  Orchestrates threat model (always), source/license (when `--source-manifest`),
  logical diff (when `--before`), candidate shape checks, and forbidden-claim /
  public-private boundary tripwires. Classifies ACCEPT / ACCEPT_WITH_REVIEW /
  BLOCK. Exit 0 acceptable, 1 BLOCK, 2 usage. `deterministic_gate_id` excludes
  the clock (`eval_date`). Reports — does not run — premium pass. `not_run`
  checks recorded with a reason, never as `pass`.
- `tests/test_supply_chain_candidate.py` (20 tests),
  `tests/test_supply_chain_promotion_gate.py` (19 tests).
- `tests/fixtures/supply_chain_candidate/` — `build_request_clean.json`,
  `build_request_missing_domain.json`, `source_manifest_ok.json`.
- Example artefacts: `candidates/xklickd-research-reader.json`,
  `promotion-gate/xklickd-research-reader.gate.json` + `.gate.md`.
- Updated `README.md` integration index: moved Candidate generation + Promotion
  gate from "planned" to tool-backed, with literal scope notes.

### Commands run (local, offline, stdlib-only)
- `python scripts/generate_supply_chain_candidate.py --build-request <req> --out <path>`
- `python scripts/run_supply_chain_promotion_gate.py --candidate <cand> [--source-manifest <m>] [--before <prev>] --out <path> --md <path> --eval-date 2026-06-02`
- `python -m pytest tests/test_supply_chain_*.py` → 102 passed.
- `python -m pytest tests/` → 283 passed, 1 unrelated DeprecationWarning
  (jsonschema.__version__), 0 failures.
- `python scripts/verify_xklickd_skill_packs.py verify` → rc 0.
- `python scripts/validate_v4_schemas.py` → rc 0.
- `python scripts/validate_v4_1_candidate_mapping.py` → rc 0.
- Forbidden-claims / codename grep over committed `candidates/` and
  `promotion-gate/` artefacts → CLEAN (no banned substring). Internal track name
  `xklickd_internal_skill_v4_2` appears only inside the candidate's
  `internal_target` block, as designed.

### Validations / behaviour confirmed
- Deterministic repeatability: identical build_request → identical
  candidate_id/hash; identical candidate → identical gate_id, stable across
  differing `--eval-date`.
- Missing domain info → `requires_human_premium_pass=true` with named gaps;
  no competencies/sources hallucinated.
- Clean candidate → gate ACCEPT (exit 0).
- Missing-domain candidate → gate ACCEPT_WITH_REVIEW (exit 0),
  premium_pass_required=true.
- Forbidden claim, internal codename, private→public leak, public v4.2
  over-claim, missing v4.2 layer, completeness claim → gate BLOCK (exit 1).

### Limitations (no mirage)
- Emitting the v4.2 target shape is NOT a claim of supply-chain completeness; a
  generated candidate is NOT a loaded executable skill (fails the loaded-skill
  gate: requires artifact_loaded AND sha256_matches_manifest).
- The gate's boundary tripwire is a coarse guard, not a full PII/secrets
  scanner (still a planned stage). Runtime enforcement remains planned.
- No legal/compliance, security-certification, or benchmark-superiority claim.
- Premium pass is reported as required where applicable but is NOT executed.

### Explicitly NOT done
- No release, tag, DOI, npm/PyPI publish, GitHub Release, or deploy.
- No merge to `main`.
- No external communication.
- No change to `Davincc77/klickd-ai`.
- No public artefact promoted to v4.2 (public stays v4.1 candidates).
