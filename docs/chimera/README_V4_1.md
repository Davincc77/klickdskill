# `.klickd v4.1 — Chimera` — planning index (v4.1 candidate catalog)

| | |
|---|---|
| **Status** | **Draft · NON-NORMATIVE · planning only** |
| **Track** | `.klickd v4.1` — Chimera (post-`v4.0.0` GA) |
| **Created** | 2026-05-27 |
| **Authoritative spec** | [`docs/rfcs/RFC-009-chimera-v4.1.md`](../rfcs/RFC-009-chimera-v4.1.md) |

> **This document is non-normative and triggers no release.** No tag, no `latest` on npm/PyPI, no DOI on Zenodo, no IANA action, no schema change, no SDK bump. There are **no GA-readiness claims** anywhere in this directory. Promotion to `Accepted` is owned by the RFC track, not by this planning index.
>
> **Update 2026-05-27:** the repo now also ships **concrete `candidate_mapped` `.klickd` artefacts** for the candidates whose framework anchors are sufficiently resolved. They live under [`examples/v4.1/chimera-skills/`](../../examples/v4.1/chimera-skills/) in two tiers — `lite/` (8 packs) and `pro/` (34 packs after the v4.1 expansion below, all with `compact_index` loading strategy). The 5 deferred (`needs_mapping`) candidates and the 2 sub-area-only nicknames intentionally have **no** artefacts. See §5 below.
>
> **Update 2026-05-27 (audit response):** filenames and canonical pack ids were aligned (filename stem == pack tail with underscores as dashes) and `crypto-lite` was demoted to `needs_mapping` because no EU SKOS-published crypto-asset-literacy framework with DigComp / NICE-comparable maturity exists. Rename table is in [`V4_1_SKILL_CANDIDATE_MAPPING.md`](./V4_1_SKILL_CANDIDATE_MAPPING.md) §0.5; the validator now enforces filename↔pack-id consistency.
>
> **Update 2026-05-27 (v4.1 expansion):** the Pro tier was extended from 19 to **34 packs** with 15 new Lot B candidates (B20..B34) — `product-manager`, `ux-researcher`, `data-analyst`, `api-integrator`, `devops-operator`, `security-incident-response`, `sales-operator`, `customer-support-operator`, `finance-analyst`, `accounting-operator`, `technical-writer`, `learning-designer`, `sustainability-analyst`, `healthcare-ai-safety-reviewer`, `edge-ai-operator`. Each is anchored to authoritative-framework competencies (ESCO / SFIA / O\*NET / NICE / ENISA / CIS / DigComp / LifeComp / WEF) covering the majority of AI-assisted future jobs. The frozen artefact count is now **8 Lite + 34 Pro = 42**, enforced by `scripts/validate_v4_1_candidate_mapping.py` (`TIER_EXPECTED_COUNT`). No GA claim; no `/klickdskill` catalog change; no release.
>
> **Update 2026-05-27 (size budgets):** byte-size ceilings for artefacts under `examples/v4.1/chimera-skills/{lite,pro}/` were raised to **Lite ≤ 12 KB** and **Pro ≤ 24 KB** (decimal KB). The new ceilings are a **capacity envelope** (upper bound), not a target — artefacts stay compact as their framework-anchored content allows. Token-cost protections (`router_cost.tokens_estimate ≤ 900` Lite / `≤ 1 350` Pro) and the Pro `compact_index` + lazy-body discipline are unchanged. The new budget applies only to public Chimera v4.1 catalog artefacts; **Klickd.app student carriers and Kai host-side skills are out of scope**.
>
> **Update 2026-05-27 (competency identification protocol):** the formal method for **how competencies are selected and combined inside each skill** is now documented in [`V4_1_COMPETENCY_IDENTIFICATION_PROTOCOL.md`](./V4_1_COMPETENCY_IDENTIFICATION_PROTOCOL.md). Every skill is a coherent blend of a shared transversal base (`base_transversal_core.transversal_refs[]`) and a small set of domain-specific competencies anchored to the canonical framework registry. The protocol covers admissible source hierarchy, the six-step selection method (job decomposition → anchor → relevance score → risk gates → memory impact), coherence rules (tier-specific count range, anti-clone), and exclusion rules. The validator enforces the mechanical subset (`TIER_COMPETENCY_RANGE`, transversal-base presence, anti-clone). All 42 already-shipped artefacts pass the new checks without modification.

---

## 0. What `docs/chimera/` is and is not

`docs/chimera/` is a **planning directory** for `.klickd v4.1` Chimera candidate work. It is the place where:

- mapping decisions about candidate `carrier_pack`s are recorded **before** any scaffold lands under [`docs/rfcs/chimera/packs/`](../rfcs/chimera/packs/);
- review checklists for individual candidates live so reviewers do not have to re-derive them per PR;
- the strict mapping rule, the size tiers, and the gating ladder are stated once and linked back from individual candidate docs.

`docs/chimera/` is **not**:

- a catalog. No file in this directory is a `carrier_pack` artefact. No `.klickd` file ships from here.
- a substitute for an RFC. Every promotion past `candidate_mapped` requires either an addition to [RFC-009](../rfcs/RFC-009-chimera-v4.1.md) or a new per-pack RFC.
- a substitute for the per-pack scaffolds under [`docs/rfcs/chimera/packs/`](../rfcs/chimera/packs/). Once a candidate clears mapping, the work moves to a scaffold there.
- a place to publish Klickd.app product carriers. Klickd.app-specific files (`klickdapp.lu/fr/be/de.klickd`, any `kai.*` host-side skill) belong to the Klickd.app product and live under [`examples/v4/klickdapp-skills/`](../../examples/v4/klickdapp-skills/) only. The strict mapping rule below excludes them from any `docs/chimera/` candidate listing.

---

## 1. Strict mapping rule (mirrors RFC-009 §0.1, §5.0, §5.1.1, §7, §8)

Every candidate in [`V4_1_SKILL_CANDIDATE_MAPPING.md`](./V4_1_SKILL_CANDIDATE_MAPPING.md) MUST carry, at a minimum:

1. a **parent `carrier_pack`** (or set of parents — composition is explicit; no implicit inheritance);
2. a **namespace** — strictly `x.klickd/<name>` (no `core.*`, no `klickdapp.*`, no `kai.*`);
3. a **proposed canonical filename** under that namespace (`<name>.klickd`);
4. a **target user / carrier** statement (who actually carries this pack — no PII);
5. a **list of competencies to map** against authoritative frameworks ([`docs/rfcs/chimera/frameworks/README.md`](../rfcs/chimera/frameworks/README.md) §1 — ESCO / WEF / O\*NET / DigComp / EQF / CEFR / LifeComp / NICE / ENISA / CIS / SFIA);
6. a **gates + human veto posture** (RFC-002 defaults, `raise_only: true`, `final_decision_owner ∈ {human_carrier, human_carrier_with_guardian}`);
7. an explicit **source / evidence policy** reference (RFC-002 §8b, RFC-003 `verification_artifacts[]` shape; pointer-only by default);
8. a **size tier** (Lot A or Lot B per [`V4_1_SKILL_CANDIDATE_MAPPING.md`](./V4_1_SKILL_CANDIDATE_MAPPING.md) §0.3);
9. a **readiness status** (`needs_mapping` / `candidate_mapped` / `ship_ready`).

A candidate that lacks **any** of those nine fields is `needs_mapping`, not `candidate_mapped`. Pretending otherwise is a §8 validation failure.

The mapping rule does **not** invent new framework anchors. If the candidate needs a competency that does not resolve into the canonical framework registry, the candidate stays `needs_mapping` and an `Open` line names the missing framework — it does not create a homegrown Klickd taxonomy ([RFC-009 §5.7](../rfcs/RFC-009-chimera-v4.1.md)).

The mapping rule also does **not** carry method into the pack. The carrier-vs-skill rule of [RFC-009 §5.1.1](../rfcs/RFC-009-chimera-v4.1.md) applies: `carrier_pack`s carry **state, not behaviour**. Any candidate that smells like a `host_skill` (pedagogy, prompting strategy, scoring rubric, intervention policy, tone rules) MUST be rejected at mapping time — the matching `host_skill` is named (e.g. `skill.research.assistant`) and the candidate is dropped from the mapping list.

---

## 2. Size tiers (planning hint, not a normative limit)

The two size tiers in [`V4_1_SKILL_CANDIDATE_MAPPING.md`](./V4_1_SKILL_CANDIDATE_MAPPING.md) §0.3 are **descriptive planning hints**, not normative ceilings. They exist so reviewers can spot a candidate that would blow the seven-pack ceiling of [RFC-009 §5.3](../rfcs/RFC-009-chimera-v4.1.md) when loaded alongside the always-on `x.klickd/user` and a typical secondary pack.

| Tier | Audience | `tokens_estimate` ceiling | Loading strategy |
|---|---|---|---|
| **Lot A — lightweight / user-lambda** | General public, learners, end-users. | ≤ ~900 tokens. | Full manifest in prompt. |
| **Lot B — advanced / dev / pro** | Developers, researchers, compliance, professional. | ≤ ~1,350 tokens (Lot A + 50%). | Compact index in prompt; full body lazy-loaded via `decision_router`. |

A candidate whose final `router_cost` row exceeds these ceilings MUST split into two packs (one for the compact index, one for the lazy body) or move to a `temporary_overlay` model ([RFC-009 §5.4](../rfcs/RFC-009-chimera-v4.1.md)) — never break the ceiling.

---

## 3. What is NOT included in v4.1 candidate planning

The following are explicitly **not** v4.1 Chimera candidates and MUST NOT appear in [`V4_1_SKILL_CANDIDATE_MAPPING.md`](./V4_1_SKILL_CANDIDATE_MAPPING.md), in any `/klickdskill` listing surface, or in `examples/v4/starter-skills/`:

| Excluded item | Where it lives instead |
|---|---|
| Klickd.app product student carriers — `klickdapp.lu.klickd`, `klickdapp.fr.klickd`, `klickdapp.be.klickd`, `klickdapp.de.klickd` (or any other country scope) | [`examples/v4/klickdapp-skills/`](../../examples/v4/klickdapp-skills/) — Klickd.app product only, explicitly NOT a starter `.klickd`. |
| Kai-side host skills — `skill.kai.tutor.socratic`, `skill.kai.assistant.base`, `skill.kai.dev.review`, `kai.tutor`, any other `kai.*` / `skill.kai.*` | Klickd / Kai host runtime. `host_skill`s are never `carrier_pack`s ([RFC-009 §0.1, §5.1.1](../rfcs/RFC-009-chimera-v4.1.md)). |
| Agent-core artefacts — `core.Kai.klickd`, `core.<Agent>.klickd` | [RFC-006 `agent_core`](../rfcs/RFC-006-agent-core.md). They constrain operating context; they are not `carrier_pack`s. |
| Generic `host_skill` names — `skill.<host>.<domain>.<method>` | Host runtime. Listed in scaffolds (e.g. [`docs/rfcs/chimera/packs/student.md`](../rfcs/chimera/packs/student.md)) under "Companion `host_skill`" only. |
| v4-preview persona anchors — `examples/v4/personas/01-eleve-terminale-fr.klickd` et al. | They are anchors / inspiration, **not** packs ([RFC-009 §6, §5.0](../rfcs/RFC-009-chimera-v4.1.md)). The clean-architecture invariant forbids harvesting fields from them. |
| Existing P0 starter `.klickd` files — `user.klickd`, `student.klickd`, `research.klickd`, `coding.klickd` | Already shipped under [`examples/v4/starter-skills/`](../../examples/v4/starter-skills/). This document does not modify or extend them. |

---

## 4. Release gating (no GA claim)

This is the gating ladder for v4.1 Chimera. **No step below is satisfied by this PR.** This PR adds planning documents only.

1. **Mapping phase (this PR).** Candidates listed with all nine required fields. Status: `candidate_mapped` for those with resolved framework anchors, `needs_mapping` for those without.
2. **Per-pack RFC phase.** For each `candidate_mapped` candidate, an extension to [RFC-009](../rfcs/RFC-009-chimera-v4.1.md) (or a new per-pack RFC) declares the candidate's slot in P1+ (P0 is closed — six packs, fixed in [RFC-009 §3](../rfcs/RFC-009-chimera-v4.1.md)). Output: a per-pack RFC text under `docs/rfcs/`.
3. **Scaffold phase.** A scaffold lands under [`docs/rfcs/chimera/packs/<name>.md`](../rfcs/chimera/packs/) mirroring [`docs/rfcs/chimera/packs/student.md`](../rfcs/chimera/packs/student.md): framework anchors fully resolved, offline SKOS/JSON-LD bundle shape pinned, deterministic `router_cost` row published, `forbidden_fields` literal frozen.
4. **Substance phase.** Physical SKOS/JSON-LD bundle bytes, strict JSON Schema fragment under `docs/rfcs/chimera/schema-fragments/`, round-trip fixture under `docs/rfcs/chimera/packs/fixtures/`.
5. **Validation phase.** Author + one independent reviewer (two for `security` / `legal` composes) sign off against all ten criteria of [RFC-009 §8](../rfcs/RFC-009-chimera-v4.1.md). Output: a `validation_record` in the per-pack scaffold.
6. **`ship_ready` phase.** Candidate is eligible for a future promotion RFC + checklist gate at [`docs/rfcs/ACCEPTANCE_CHECKLIST_V4.md`](../rfcs/ACCEPTANCE_CHECKLIST_V4.md). **Catalog exposure is a separate decision** per [RFC-009 §7](../rfcs/RFC-009-chimera-v4.1.md).
7. **Catalog exposure phase.** Only after **all** P0 packs pass §8, AND the candidate itself passes §8, MAY `/klickdskill` (or any equivalent surface) consider listing the candidate. Per [`docs/rfcs/chimera/packs/README.md`](../rfcs/chimera/packs/README.md) §5, the shape of catalog entries is sketched but not committed.

There is **no** "v4.1 GA" claim implied by anything in `docs/chimera/`. The track-level GA decision belongs to the RFC track and to [`docs/rfcs/ACCEPTANCE_CHECKLIST_V4.md`](../rfcs/ACCEPTANCE_CHECKLIST_V4.md), not to this directory.

---

## 5. Files in this directory + companion artefacts

### Planning docs (this directory)

| File | Purpose |
|---|---|
| [`README_V4_1.md`](./README_V4_1.md) | (this file) Planning index — strict mapping rule, size tiers, exclusions, gating ladder. |
| [`V4_1_SKILL_CANDIDATE_MAPPING.md`](./V4_1_SKILL_CANDIDATE_MAPPING.md) | Per-candidate mapping table — Lot A (lightweight) and Lot B (advanced). All nine required fields per row. |
| [`V4_1_CANDIDATE_CHECKLIST.md`](./V4_1_CANDIDATE_CHECKLIST.md) | Per-candidate review checklist. Reviewer runs this against any new candidate before promoting it past `candidate_mapped`. |

### Concrete artefacts (companion directory, **`candidate_mapped`** only)

| Path | Purpose |
|---|---|
| [`examples/v4.1/chimera-skills/lite/`](../../examples/v4.1/chimera-skills/lite/) | **Lot A** real `.klickd` files (lightweight, **capacity envelope ≤ 12 KB** per the 2026-05-27 budget update — current artefacts 5.9–7.3 KB; `router_cost.tokens_estimate ≤ 900`). **8 packs** (after 2026-05-27 audit rename + crypto-lite deferral): `work-assistant`, `media-planner`, `consumer-rights`, `social-literacy`, `artist`, `streaming-creator`, `game-literacy`, `parent-gaming`. Includes `manifest.json` with `sha256_file` + `sha256_canonical_json` per pack. |
| [`examples/v4.1/chimera-skills/pro/`](../../examples/v4.1/chimera-skills/pro/) | **Lot B** real `.klickd` files (advanced, **capacity envelope ≤ 24 KB** per the 2026-05-27 budget update — current artefacts 8.1–12.0 KB; `router_cost.tokens_estimate ≤ 1,350`) with `loading_strategy.mode = compact_index_plus_lazy_body` and a `compact_index` block in every file. **34 packs** (after 2026-05-27 audit rename, B19 `video-production-pipeline`, and the 2026-05-27 v4.1 expansion that added B20..B34): `llm-agent-security`, `llm-agent-engineering`, `identity-access-management`, `release-engineer`, `trust-evidence`, `eu-ai-act`, `gdpr-readiness`, `contract-review`, `privacy-product`, `evidence-desk`, `policy-analyst`, `second-brain`, `literature-review`, `project-operator`, `drone-operator`, `mission-control`, `game-design`, `rights-guard`, `video-production-pipeline`, `product-manager`, `ux-researcher`, `data-analyst`, `api-integrator`, `devops-operator`, `security-incident-response`, `sales-operator`, `customer-support-operator`, `finance-analyst`, `accounting-operator`, `technical-writer`, `learning-designer`, `sustainability-analyst`, `healthcare-ai-safety-reviewer`, `edge-ai-operator`. Includes `manifest.json`. |
| [`examples/v4.1/chimera-skills/README.md`](../../examples/v4.1/chimera-skills/README.md) | Reader doc for the artefact directory — what each file carries, what is NOT included, how to verify offline. |

**No artefacts for deferred candidates.** A5 `personal-finance`, A6 `budget`, **A8 `crypto-lite`** (demoted by the 2026-05-27 audit), A14 `wellbeing-lite`, A15 `family` remain `needs_mapping` in [`V4_1_SKILL_CANDIDATE_MAPPING.md`](./V4_1_SKILL_CANDIDATE_MAPPING.md) and have **no** `.klickd` file under either tier. The validator (`scripts/validate_v4_1_candidate_mapping.py`) refuses to accept an artefact whose nickname matches one of those five (or one of the two `student`-sub-area nicknames `language` / `exam`), and additionally enforces filename↔pack-id consistency so future PRs cannot ship a `foo.klickd` declaring `pack: x.klickd/bar`.

**No artefacts for the existing P0 starter packs.** The four canonical files (`user.klickd`, `student.klickd`, `research.klickd`, `coding.klickd`) already live under [`examples/v4/starter-skills/`](../../examples/v4/starter-skills/) and are NOT duplicated here.

---

## 6. See also

- [`docs/rfcs/RFC-009-chimera-v4.1.md`](../rfcs/RFC-009-chimera-v4.1.md)
- [`docs/rfcs/chimera/README.md`](../rfcs/chimera/README.md)
- [`docs/rfcs/chimera/packs/README.md`](../rfcs/chimera/packs/README.md)
- [`docs/rfcs/chimera/packs/student.md`](../rfcs/chimera/packs/student.md) — first concrete pack scaffold (`x.klickd/student`).
- [`docs/rfcs/chimera/frameworks/README.md`](../rfcs/chimera/frameworks/README.md)
- [`docs/rfcs/chimera/packs/router_cost.md`](../rfcs/chimera/packs/router_cost.md)
- [`docs/rfcs/ACCEPTANCE_CHECKLIST_V4.md`](../rfcs/ACCEPTANCE_CHECKLIST_V4.md)
- [`examples/v4/starter-skills/`](../../examples/v4/starter-skills/) — already-shipped P0 starter `.klickd` files (not extended by this PR).
- [`examples/v4/klickdapp-skills/`](../../examples/v4/klickdapp-skills/) — Klickd.app product carriers (out of scope; never `/klickdskill` catalog candidates).
