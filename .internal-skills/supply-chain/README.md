# `.internal-skills/supply-chain/` — internal supply-chain stages (integration index)

| | |
|---|---|
| **Status** | **Internal · NON-NORMATIVE · no release / no publish / no merge to main** |
| **Created** | 2026-06-02 |
| **Companion spec** | [`docs/rfcs/chimera/SUPPLY_CHAIN.md`](../../docs/rfcs/chimera/SUPPLY_CHAIN.md) (process spec) |
| **Rules of engagement** | [`MASTER_BRIEF.md`](../../MASTER_BRIEF.md) (anti-mirage rules, v4.1/v4.2 boundary) |

> This directory holds **internal** supply-chain artefacts and the audit/diff/source-check records produced by the tool-backed stages. Nothing here is a public release, a normative spec, a schema, or an SDK contract. Read every stage label **literally** (`tool` / `planned`). A catalog entry or stub is **never** a loaded executable skill — see the loaded-skill gate in §"Loaded-skill gate".

This README is the integration index that brings the supply-chain components together. It is the human-readable map of which stages are **real and tool-backed today** versus **planned**.

---

## Real, tool-backed stages (shipped + tested)

| Stage | Tool | Internal artefacts | Tests |
|---|---|---|---|
| **Audit / determinism** | `scripts/generate_supply_chain_audit.py` | `audit/audit_trail_index.json`, `audit/determinism_record.json` | `tests/test_supply_chain_audit.py` |
| **Logical diff** | `scripts/generate_supply_chain_diff.py` | `diff/` (report output) | `tests/test_supply_chain_diff.py` (+ `tests/fixtures/supply_chain_diff/`) |
| **Source freshness + license** | `scripts/check_supply_chain_sources.py` | `source-check/example_source_manifest.json` | `tests/test_supply_chain_sources.py` (+ `tests/fixtures/supply_chain_sources/`) |
| **Threat model** | `scripts/generate_supply_chain_threat_model.py` | (report output) · doc: `docs/supply-chain/THREAT_MODEL_GENERATOR.md` | `tests/test_supply_chain_threat_model.py` (+ `tests/fixtures/threat-model/`) |
| **Candidate generation** | `scripts/generate_supply_chain_candidate.py` | `candidates/` (example: `candidates/xklickd-research-reader.json`) | `tests/test_supply_chain_candidate.py` (+ `tests/fixtures/supply_chain_candidate/`) |
| **Promotion gate** | `scripts/run_supply_chain_promotion_gate.py` | `promotion-gate/` (example: `promotion-gate/xklickd-research-reader.gate.json` + `.md`) | `tests/test_supply_chain_promotion_gate.py` |

Each of these is `tool`: a runnable script with a passing test module and deterministic output. "Tool-backed" means the bytes and behaviour exist and are tested — it does **not** imply the supply chain is complete, that any candidate is a loaded skill, or that a public release exists.

### Candidate generator scope (read literally)

`generate_supply_chain_candidate.py` emits the **internal v4.2 target shape** from a config-only `build_request`. Emitting the shape is **not** a claim that every lifecycle stage is implemented or verified — and a generated candidate is **not** a loaded executable skill (it fails the loaded-skill gate below). When domain information is missing, the runner marks `requires_human_premium_pass` rather than inventing competencies, risk, or sources. Sources come **only** from the `build_request` / referenced `source_manifest`.

### Promotion gate scope (read literally)

`run_supply_chain_promotion_gate.py` orchestrates the tool-backed checks (threat model always; source/license when a manifest is given; logical diff when a `--before` is given) plus candidate shape checks and forbidden-claim / public-private boundary tripwires. It classifies **ACCEPT / ACCEPT_WITH_REVIEW / BLOCK** and **reports** whether a human premium pass is required — it does **not** run that pass, and makes no compliance/security/benchmark claim. A check that could not run is recorded `not_run` with a reason, never as `pass`.

## Planned stages (specified, not built)

| Stage | What it will do | Why it is not claimed yet |
|---|---|---|
| **Full PII / secrets scanner** | Scan candidate inputs/outputs for PII and secrets beyond the engineering source/license checks. | Current `source-check` is an engineering license/freshness check, **not** a compliance attestation or a PII scanner. The gate's boundary tripwire is a coarse guard, not a full scanner. |
| **Runtime enforcement** | Enforce guardrails in-loop at execution time, not just at build/audit time. | Build-time checks + the promotion gate exist; runtime enforcement does not. |

---

## Loaded-skill gate

A pack/skill is "loaded" or "used" **only** when:

```
artifact_loaded == true  AND  sha256_matches_manifest == true
```

per [`docs/integrations/skill-loader-protocol.md`](../../docs/integrations/skill-loader-protocol.md). Anything short of that — a manifest row, a stub, a routing placeholder — is **not** a loaded skill and must not be described as one.

## Boundary reminder

- Public artefacts remain **v4.1**. **No public v4.2 claim.** v4.2 is an internal target only (`docs/internal/`).
- No release, publish, tag, DOI, external communication, merge to main, or PR approval from supply-chain work.
- Do not touch `Davincc77/klickd-ai`.
