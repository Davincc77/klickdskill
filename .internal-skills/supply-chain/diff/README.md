# Supply-chain logical diff (stage: diff report)

This directory holds the output of the **logical diff** stage of the x.klickd
skill/pack supply chain. It is one tool-backed stage, not the full pipeline,
and makes **no claim of total automation**.

## What it does

`scripts/generate_supply_chain_diff.py` compares a previous version of a
skill/pack candidate (`--before`) against a new version (`--after`) and
classifies the changes that matter for governance, security and claim
discipline — not just raw JSON/text line changes.

It is meant to help a human/agent reviewer decide:

- candidate acceptable,
- premium pass required,
- immediate rejection,
- rollback / deprecation required.

## Usage

```bash
python scripts/generate_supply_chain_diff.py \
  --before path/to/before.json \
  --after  path/to/after.json \
  --out    .internal-skills/supply-chain/diff/report.json
```

- Prints the report to stdout (suppress with `--quiet`).
- Writes the report to `--out` when given.
- Standard library only. No network, no provider calls, no paid resources.

## Change classification

`added`, `removed`, `changed`, `unchanged`, `risk_raised`,
`guardrail_lowered`, `evidence_changed`, `governance_changed`,
`memory_policy_changed`, `public_boundary_changed`, `claim_boundary_changed`.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | no blocking finding |
| 1 | at least one **blocking** finding (guardrail lowered, claim-boundary, or public/private-boundary violation) |
| 2 | usage / input error (missing or unparseable input) |

## Blocking (hard-fail) conditions

Per the supply-chain rules, any **lowering of a non-lowerable safeguard** is a
hard fail rather than a silent change. Blocking findings include:

- a verification gate weakened (`block` → `confirm` → `silent`) or removed;
- a `human_veto.non_lowerable_floor` entry removed, or `raise_only` disabled;
- `evidence_policy.required_for_claims` / `pointer_only` turned off;
- `human_authority.final_decision_owner` moved off `human_carrier`;
- `_pack_metadata.claims_v41_ga` flipped to `true`, or `non_normative` dropped;
- a banned public claim introduced (e.g. "universal standard", "automatic
  GDPR / EU AI Act compliance", "proven benchmark superiority");
- an internal codename leaking into the candidate;
- `contains_real_pii` / `contains_secrets` flipped to `true`;
- the `encrypted` flag downgraded `true` → `false`;
- a `forbidden_fields` entry removed.

Non-blocking but flagged: memory-policy changes, evidence-policy shape
changes, agent-role escalation (`risk_raised`), and generic added/removed/
changed pack keys.

## Determinism

`deterministic_diff_id` is a `sha256:` over the before/after input hashes plus
the sorted, normalized findings. It does not depend on the clock, host, or run
order. Two runs over identical inputs produce an identical id. Any clock-based
marker a caller adds lives in `non_deterministic_zone` and is excluded from the
hash.

## Tool-vs-planned matrix (this stage)

| Capability | State |
|---|---|
| logical diff classification (governance/guardrail/memory/evidence/claim/public boundary) | **tool** (this stage) |
| deterministic diff id + report | **tool** (this stage) |
| hard-fail on guardrail lowering / claim / public-boundary violation | **tool** (this stage) |
| threat model, license check, source-freshness, full PII/secrets scanner | **planned** |
| candidate-skill generation, context-graph generation | **planned** |
| premium pass | **manual** (human/agent, post-diff) |

## Known limits

- The diff understands the documented x.klickd pack shape. Renamed or
  restructured roots are reported as generic `changed` rather than mapped to a
  semantic class.
- The banned-claim and codename checks are substring tripwires on the
  candidate document, not a general-purpose PII/secrets scanner.
- This stage does not generate, promote, release, tag or publish anything.
