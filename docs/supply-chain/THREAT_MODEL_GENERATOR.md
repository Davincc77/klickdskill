# Supply-chain threat-model generator (v0.1, internal / draft)

**Status:** internal draft, NON-NORMATIVE. Not a release, not a public claim,
not a v4.2 GA artefact. The 42 public x.klickd artefacts remain v4.1.

This document describes `scripts/generate_supply_chain_threat_model.py`, a
deterministic, offline, stdlib-only static analyser for x.klickd
skill/candidate manifests.

## What it does

Given a candidate manifest JSON, the generator:

1. parses the manifest (`xklickd.candidate.v0.1`, or a minimal subset of its
   keys);
2. computes a deterministic `candidate_hash` (sha256 over canonical JSON
   bytes);
3. classifies declared threats by category;
4. emits `required_mitigations`;
5. produces a deterministic report JSON;
6. **blocks** (exit code 1) when any unmitigated `high` or `critical`
   finding is present.

Same input bytes → identical report bytes.

## Usage

```bash
python scripts/generate_supply_chain_threat_model.py \
    --candidate tests/fixtures/threat-model/candidate_low_risk_ok.json \
    --out .internal-skills/supply-chain/threat-model/report.json
```

- `--candidate PATH` (required): candidate manifest JSON.
- `--out PATH` (optional): write the report; otherwise print to stdout.
- `--no-block` (optional): report findings but always exit 0.

Exit codes: `0` no blocking finding · `1` blocked (unmitigated high/critical) ·
`2` usage / I/O / parse error.

## Threat categories

`authority_escalation`, `human_veto_bypass`, `tool_boundary_violation`,
`memory_poisoning`, `private_public_leak`, `evidence_weakening`,
`unsourced_claim`, `unsafe_external_action`, `irreversible_action`,
`compliance_overclaim`, `stale_or_unlicensed_source_dependency`.

Severities: `low` / `medium` / `high` / `critical`.

## Report shape (minimum fields)

`schema_version`, `candidate_path`, `candidate_hash`,
`deterministic_threat_model_id`, `summary` (counts), `threats`,
`required_mitigations`, `blocked_findings`, `recommendations`,
`non_deterministic_zone`, `claim_boundaries`.

## Blocking examples (see `tests/fixtures/threat-model/`)

| Fixture | Category | Result |
| --- | --- | --- |
| `candidate_low_risk_ok` | — | pass (exit 0) |
| `candidate_no_veto_sensitive_action` | `human_veto_bypass` | block |
| `candidate_external_action_no_gate` | `unsafe_external_action` | block |
| `candidate_longterm_memory_no_promotion` | `memory_poisoning` | block |
| `candidate_private_public_leak` | `private_public_leak` | block |
| `candidate_evidence_false_public_claims` | `evidence_weakening` + `unsourced_claim` | block |
| `candidate_compliance_overclaim` | `compliance_overclaim` | block |

## Claim boundaries (do NOT widen)

This tool is **not** a security certification. It does **not** establish GDPR
or EU AI Act compliance, makes **no** benchmark-superiority or universal-standard
claim, does **not** prove the candidate is a loaded/executable skill, and is
**not** full automation. Findings reflect only what the manifest *declares*
about itself. Human review remains required.

## Limits / what is tool-backed vs planned

- **Tool-backed:** manifest parsing, deterministic hashing, the rule-based
  classification above, deterministic report rendering, the block decision,
  and the fixture-driven test suite.
- **Planned / out of scope:** runtime/behavioural analysis of a loaded
  candidate, network scanning, legal/compliance assessment, integration into a
  promotion gate, and richer source freshness/license resolution (the related
  source-freshness work lives in a separate PR and is not depended on here).
