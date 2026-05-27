# `examples/v4.1/chimera-skills/` — concrete Chimera v4.1 candidate skill artefacts

> **Status:** Concrete `candidate_mapped` artefacts. **Non-normative.** **Pre-release.**
>
> **Triggers no release.** No tag, no `latest` on npm or PyPI, no DOI on Zenodo, no IANA action, no SDK bump, no `/klickdskill` catalog change.

This directory ships **real, structured `.klickd` files** that are concrete realisations of the Chimera v4.1 candidate mapping documented in [`docs/chimera/V4_1_SKILL_CANDIDATE_MAPPING.md`](../../../docs/chimera/V4_1_SKILL_CANDIDATE_MAPPING.md). Every file is `candidate_mapped` (NOT `ship_ready`); none is GA; none is exposed on `/klickdskill`.

## Layout

| Path | Contents |
|---|---|
| [`lite/`](./lite/) | **Lot A (lightweight, user-lambda)** candidate skills. Compact (~6–7 KB), near-Chimera-size, fast-load; full manifest in prompt. **8 packs** + `manifest.json` (after 2026-05-27 audit rename + `crypto-lite` deferral). |
| [`pro/`](./pro/) | **Lot B (advanced, dev/pro)** candidate skills. Up to ~+50% larger (~8–12 KB), with `compact_index` loading strategy declared so the router can advertise gates / framework anchors / router_cost in prompt and lazy-load the full body on demand. **34 packs** + `manifest.json` (after 2026-05-27 audit rename, B19 `video-production-pipeline` follow-up, and the 2026-05-27 v4.1 expansion that added B20..B34 covering the majority of AI-assisted future jobs). |

> **Frozen counts.** The artefact set is exactly **8 Lite + 34 Pro = 42** `candidate_mapped` skills. The validator (`scripts/validate_v4_1_candidate_mapping.py`, `TIER_EXPECTED_COUNT`) rejects any drift from these counts. Promotion, demotion, or addition requires updating the planning doc, the validator constants, and the per-tier `manifest.json`. **Production-ready target**, NOT GA — `_pack_metadata.claims_v41_ga: false` everywhere; promotion past `candidate_mapped` still requires the ten-step gate of [RFC-009 §8](../../../docs/rfcs/RFC-009-chimera-v4.1.md).

> **Audit response 2026-05-27.** Filenames and canonical pack ids were aligned (filename stem == pack tail with underscores as dashes) per the audit's W-1 / BLOCKER finding. `crypto-lite` was demoted to `needs_mapping` because no EU SKOS-published crypto-asset-literacy framework exists with DigComp / NICE-comparable maturity. Full rename + defer table: [`docs/chimera/V4_1_SKILL_CANDIDATE_MAPPING.md`](../../../docs/chimera/V4_1_SKILL_CANDIDATE_MAPPING.md) §0.5. Each renamed file carries `_pack_metadata.renamed_from` with the prior filename for traceability.

## Tier sizing (descriptive, not normative)

| Tier | Audience | Approx. file size | `router_cost.tokens_estimate` | Loading strategy |
|---|---|---|---|---|
| **`lite`** | General public, learners, end-users. | ≤ ~7 KB | ≤ 900 | Full manifest in prompt. |
| **`pro`** | Developers, researchers, compliance officers, professional users. | ≤ ~11 KB (~+50% vs lite) | ≤ 1,350 | **`compact_index` in prompt + lazy body** via `decision_router` ([RFC-007](../../../docs/rfcs/RFC-007-usage-profile-skill-routing.md)). The compact_index carries `pack`, `frameworks[]` IDs, `competency_ids[]`, `gate_summaries[]`, `human_authority`, `router_cost`. Full body (mastery scales, evidence rules, framework subsets) loads on demand. |

## What every file carries

Every `.klickd` in this directory is a real structured JSON document on the v4.0 envelope. Inside `x_klickd_pack` each file carries (at minimum):

- `pack`, `pack_version`, `spec_ref`, `publisher`, `size_tier`
- `parent_packs[]` — composition with existing Chimera P0/P1 packs (`x.klickd/user`, `x.klickd/student`, `x.klickd/coding`, `x.klickd/research`, `x.klickd/security`, `x.klickd/legal`, `x.klickd/work`, `x.klickd/creator`, `x.klickd/gaming`, `x.klickd/bridge`, `x.klickd/mission`)
- `target_user` — plain-language carrier description (no PII)
- `frameworks[]` — authoritative framework registry references (ESCO / DigComp / LifeComp / EQF / CEFR / WEF / O*NET / NICE / ENISA / CIS / SFIA)
- `competency_mappings[]` / `competencies[]` — framework-anchored competency entries with `competency_ref`, `scheme`, `prefLabel`
- `base_transversal_core` — minimum cross-pack competency layer
- `levels[]` — EQF level anchors
- `memory_scope` + `memory_segments[]` + `structured_memory` — pack-scoped memory slice ([RFC-009 §5.6](../../../docs/rfcs/RFC-009-chimera-v4.1.md)). Carries no inline content; pointer-only.
- `gates`, `human_veto`, `human_authority` — RFC-002 verification gates default + carrier veto posture + final-decision owner. `raise_only: true`; non-lowerable floor declared.
- `evidence_policy`, `source_policy` — RFC-002 §8b grounding + RFC-003 `verification_artifacts[]` shape; `pointer_only: true`.
- `verification_gates` — concrete per-action gate definitions (block / confirm / silent) with reason text.
- `router_cost` — deterministic heuristic token-cost estimate consistent with RFC-003.
- `acceptance_criteria[]`, `tests.static[]`, `tests.review[]` — per-pack acceptance / test list a reviewer runs against the file.
- `forbidden_fields[]` — frozen literal enforcing the carrier-vs-skill split ([RFC-009 §5.1.1 / §8.10](../../../docs/rfcs/RFC-009-chimera-v4.1.md)).

Pro-tier files additionally carry:

- `loading_strategy` — declares `compact_index_plus_lazy_body` with the rationale and the router (RFC-007) reference.
- `compact_index` — the small block the router puts in prompt: `pack`, `frameworks[]` (scheme IDs only), `competency_ids[]`, `gate_summaries[]`, `human_authority`, `router_cost`.

## What every file is NOT

- **Not GA.** `_pack_metadata.claims_v41_ga: false` everywhere. `status: candidate_mapped`. No file in this directory is a `ship_ready` artefact; promotion past `candidate_mapped` requires a per-pack RFC + scaffold + bundle bytes + strict JSON Schema + round-trip vector per [RFC-009 §8](../../../docs/rfcs/RFC-009-chimera-v4.1.md).
- **Not personal data.** `_pack_metadata.contains_real_pii: false`, `_pack_metadata.contains_secrets: false`. No real user state; pointer-only.
- **Not Klickd.app product carriers.** No `klickdapp.lu/fr/be/de.klickd`. Those live under [`examples/v4/klickdapp-skills/`](../../v4/klickdapp-skills/) and are out of scope here.
- **Not Kai host-side skills.** No `skill.kai.*`, no `kai.tutor`, no `core.Kai.klickd`. Host-side skills live in the host runtime, never inside a `carrier_pack` ([RFC-009 §0.1, §5.1.1](../../../docs/rfcs/RFC-009-chimera-v4.1.md)).
- **Not catalog entries.** Until P0 + per-pack validation passes ([RFC-009 §7](../../../docs/rfcs/RFC-009-chimera-v4.1.md)), no `/klickdskill` listing is implied by anything in this directory.
- **Not renamed v4-preview personas.** Each file is authored from frameworks, not harvested from a persona ([RFC-009 §5.0](../../../docs/rfcs/RFC-009-chimera-v4.1.md)).

## How to verify

Offline verification of structure, field presence, tier ceilings, anti-PII guard, anti-host_skill guard, anti-Klickd.app-leak guard, and hash stability:

```bash
python3 scripts/validate_v4_1_candidate_mapping.py
pytest tests/test_v4_1_candidate_mapping.py
```

The validator parses every `.klickd` under `lite/` and `pro/`, checks the required Chimera fields, asserts the size-tier ceiling, enforces the frozen `forbidden_fields` literal, and refuses any leak of Klickd.app or Kai host-side names.

## Deferred candidates (NOT shipped as artefacts)

The four candidates flagged `needs_mapping` in [`docs/chimera/V4_1_SKILL_CANDIDATE_MAPPING.md`](../../../docs/chimera/V4_1_SKILL_CANDIDATE_MAPPING.md) §1 (A5 `personal-finance`, A6 `budget`, A14 `wellbeing-lite`, A15 `family`) are **deliberately absent** from this directory. They remain documented in the planning doc only; no `.klickd` is produced for them until the framework anchor / consent shape question is resolved. The validator enforces this — adding a `.klickd` file whose nickname matches one of the deferred candidates is rejected.

Two additional candidates from the planning doc are also absent here, by design:

- **A2 `language`** and **A3 `exam`** — these are explicit **sub-areas** of `x.klickd/student` ([`examples/v4/starter-skills/student.klickd`](../../v4/starter-skills/student.klickd) — `language_proficiency[]` and `exam_targets[]` blocks), not separate packs. They are NOT separate `.klickd` files and never will be under v4.1; the planning doc records them so reviewers do not propose them as siblings.

## File index

### `lite/` (8 packs)

| File | Pack | Parents | Working nickname |
|---|---|---|---|
| `work-assistant.klickd` | `x.klickd/work_assistant` | `user`, `work` | work-lite (A1) |
| `media-planner.klickd` | `x.klickd/media_planner` | `user`, `creator` | media-lite (A4) |
| `consumer-rights.klickd` | `x.klickd/consumer_rights` | `user`, `legal` | consumer-rights (A7) |
| `social-literacy.klickd` | `x.klickd/social_literacy` | `user` | social (A9) |
| `artist.klickd` | `x.klickd/artist` | `user`, `creator` | artist (A10) |
| `streaming-creator.klickd` | `x.klickd/streaming_creator` | `user`, `creator` | streamer-lite (A11) |
| `game-literacy.klickd` | `x.klickd/game_literacy` | `user`, `gaming` | game-literacy (A12) |
| `parent-gaming.klickd` | `x.klickd/parent_gaming` | `user`, `gaming`, `security` | parent-gaming (A13) |

> **`crypto-lite` (A8) — DEFERRED.** No artefact; row stays in the planning doc only. Reason: no EU SKOS-published crypto-asset-literacy framework with DigComp / NICE-comparable maturity (NICE / CIS cover security hygiene generically but do not anchor "crypto" as a distinct competency class).

### `pro/` (34 packs)

| File | Pack | Parents | Working nickname |
|---|---|---|---|
| `llm-agent-security.klickd` | `x.klickd/llm_agent_security` | `user`, `security`, `coding` | agent-security (B1) |
| `llm-agent-engineering.klickd` | `x.klickd/llm_agent_engineering` | `user`, `coding`, `llm_agent_security` | ai-agent-builder (B2) |
| `identity-access-management.klickd` | `x.klickd/identity_access_management` | `user`, `security` | iam-endpoint (B3) |
| `release-engineer.klickd` | `x.klickd/release_engineer` | `user`, `coding`, `security` | release-engineer (B4) |
| `trust-evidence.klickd` | `x.klickd/trust_evidence` | `user`, `research` | trust-evidence (B5) |
| `eu-ai-act.klickd` | `x.klickd/eu_ai_act` | `user`, `legal` | eu-ai-act (B6) |
| `gdpr-readiness.klickd` | `x.klickd/gdpr_readiness` | `user`, `legal` | gdpr-readiness (B7) |
| `contract-review.klickd` | `x.klickd/contract_review` | `user`, `legal` | contract-review (B8) |
| `privacy-product.klickd` | `x.klickd/privacy_product` | `user`, `legal`, `coding` | privacy-product (B9) |
| `evidence-desk.klickd` | `x.klickd/evidence_desk` | `user`, `research`, `trust_evidence` | evidence-desk (B10) |
| `policy-analyst.klickd` | `x.klickd/policy_analyst` | `user`, `research`, `legal` | policy-analyst (B11) |
| `second-brain.klickd` | `x.klickd/second_brain` | `user`, `research` | second-brain (B12) |
| `literature-review.klickd` | `x.klickd/literature_review` | `user`, `research` | literature-review (B13) |
| `project-operator.klickd` | `x.klickd/project_operator` | `user`, `work`, `mission` | project-operator (B14) |
| `drone-operator.klickd` | `x.klickd/drone_operator` | `user`, `security`, `legal` | drone (B15) |
| `mission-control.klickd` | `x.klickd/mission_control` | `user`, `mission`, `security` | mission-control (B16) |
| `game-design.klickd` | `x.klickd/game_design` | `user`, `creator`, `coding` | game-design (B17) |
| `rights-guard.klickd` | `x.klickd/rights_guard` | `user`, `legal`, `creator` | rights-guard (B18) |
| `video-production-pipeline.klickd` | `x.klickd/video_production_pipeline` | `user`, `media_planner`, `creator`, `research`, `legal` | video-production-pipeline (B19) |
| `product-manager.klickd` | `x.klickd/product_manager` | `user`, `work`, `coding` | product-manager (B20) |
| `ux-researcher.klickd` | `x.klickd/ux_researcher` | `user`, `research` | ux-researcher (B21) |
| `data-analyst.klickd` | `x.klickd/data_analyst` | `user`, `research` | data-analyst (B22) |
| `api-integrator.klickd` | `x.klickd/api_integrator` | `user`, `coding` | api-integrator (B23) |
| `devops-operator.klickd` | `x.klickd/devops_operator` | `user`, `coding`, `security` | devops-operator (B24) |
| `security-incident-response.klickd` | `x.klickd/security_incident_response` | `user`, `security` | security-incident-response (B25) |
| `sales-operator.klickd` | `x.klickd/sales_operator` | `user`, `work` | sales-operator (B26) |
| `customer-support-operator.klickd` | `x.klickd/customer_support_operator` | `user`, `work` | customer-support-operator (B27) |
| `finance-analyst.klickd` | `x.klickd/finance_analyst` | `user`, `work` | finance-analyst (B28) |
| `accounting-operator.klickd` | `x.klickd/accounting_operator` | `user`, `work`, `legal` | accounting-operator (B29) |
| `technical-writer.klickd` | `x.klickd/technical_writer` | `user`, `coding`, `research` | technical-writer (B30) |
| `learning-designer.klickd` | `x.klickd/learning_designer` | `user`, `research` | learning-designer (B31) |
| `sustainability-analyst.klickd` | `x.klickd/sustainability_analyst` | `user`, `research`, `legal` | sustainability-analyst (B32) |
| `healthcare-ai-safety-reviewer.klickd` | `x.klickd/healthcare_ai_safety_reviewer` | `user`, `research`, `legal`, `security` | healthcare-ai-safety-reviewer (B33) |
| `edge-ai-operator.klickd` | `x.klickd/edge_ai_operator` | `user`, `coding`, `security` | edge-ai-operator (B34) |

> **Candidate→candidate parent edges.** Three pro packs compose on other candidates: `llm-agent-engineering.klickd` lists `x.klickd/llm_agent_security` as a parent, `evidence-desk.klickd` lists `x.klickd/trust_evidence`, and `video-production-pipeline.klickd` lists `x.klickd/media_planner` (a lite Lot A candidate). All parents are themselves `candidate_mapped`; downstream loaders that resolve parents transitively will chain candidates onto candidates at this stage. Documented per audit W-2.

## See also

- [`docs/chimera/V4_1_SKILL_CANDIDATE_MAPPING.md`](../../../docs/chimera/V4_1_SKILL_CANDIDATE_MAPPING.md) — full candidate mapping (parent packs, target user, framework anchors, gates, evidence policy, size tier, status).
- [`docs/chimera/README_V4_1.md`](../../../docs/chimera/README_V4_1.md) — planning index, strict mapping rule, exclusion table, release-gating ladder.
- [`docs/chimera/V4_1_CANDIDATE_CHECKLIST.md`](../../../docs/chimera/V4_1_CANDIDATE_CHECKLIST.md) — per-candidate review checklist.
- [`docs/rfcs/RFC-009-chimera-v4.1.md`](../../../docs/rfcs/RFC-009-chimera-v4.1.md) — Chimera v4.1 RFC (P0/P1 sets, validation §8, no-catalog §7, carrier-vs-skill §5.1.1).
- [`examples/v4/starter-skills/`](../../v4/starter-skills/) — already-shipped P0 starter `.klickd` files (`user`, `student`, `research`, `coding`). NOT extended by this directory.
- [`examples/v4/klickdapp-skills/`](../../v4/klickdapp-skills/) — Klickd.app product carriers. Out of scope here; never referenced as candidate Chimera packs.
