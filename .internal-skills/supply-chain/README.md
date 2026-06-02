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

Each of these is `tool`: a runnable script with a passing test module and deterministic output. "Tool-backed" means the bytes and behaviour exist and are tested — it does **not** imply the end-to-end build runner exists.

## Planned stages (specified, not built)

| Stage | What it will do | Why it is not claimed yet |
|---|---|---|
| **Candidate generation** | Produce a candidate `carrier_pack` from a config-only build request (the build *runner*). | No runner is shipped; the *process* is specified, the executor is not. |
| **Promotion gate** | Pass/fail enforcement that blocks a candidate from being promoted unless all checks pass. | No gate enforces promotion today; checks run, but nothing blocks on them. |
| **Full PII / secrets scanner** | Scan candidate inputs/outputs for PII and secrets beyond the engineering source/license checks. | Current `source-check` is an engineering license/freshness check, **not** a compliance attestation or a PII scanner. |
| **Runtime enforcement** | Enforce guardrails in-loop at execution time, not just at build/audit time. | Build-time checks exist; runtime enforcement does not. |

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
