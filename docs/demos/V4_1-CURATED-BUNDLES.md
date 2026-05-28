# `.klickd v4.1` Chimera — curated bundles & demo agent counts

| | |
|---|---|
| **Status** | **Draft · NON-NORMATIVE · planning only** |
| **Track** | `.klickd v4.1` — Chimera (post-`v4.0.0` GA) |
| **Created** | 2026-05-27 |
| **Companion to** | [`docs/ux/V4_1-PRESENTATION-STRATEGY.md`](../ux/V4_1-PRESENTATION-STRATEGY.md) |

> **Non-normative.** No release, tag, Zenodo DOI, npm/PyPI publish, IANA action, schema change, or website edit is implied. This file proposes **demo bundles** to seed the future `/klickdskill` "Bundle builder" tray (see presentation strategy §5.6). Every pack referenced below exists in [`examples/v4.1/x-klickd-skills/`](../../examples/v4.1/x-klickd-skills/) or [`examples/v4/starter-skills/`](../../examples/v4/starter-skills/) at the head of PR #75 as a `candidate_mapped` artefact; **none is `ship_ready` yet** and no bundle below may appear on the live catalog until each of its packs clears [RFC-009 §8](../rfcs/RFC-009-chimera-v4.1.md).
>
> **No Klickd.app, no `kai.*`, no `core.*`, no v4-preview persona anchors** appear in any bundle below. The strict exclusion of [`docs/ux/V4_1-PRESENTATION-STRATEGY.md`](../ux/V4_1-PRESENTATION-STRATEGY.md) §0 is binding here.
>
> **Recommended agent counts are demonstrative.** They reflect a "one carrier per agent + named coordinator" pattern that fits within the seven-pack ceiling of [RFC-009 §5.3](../rfcs/RFC-009-chimera-v4.1.md) once `x.klickd/user` is implicit. Production deployments may differ; these are demo defaults.

---

## 0. Bundle conventions

- **Bundle ≠ carrier.** A bundle is a list of canonical pack ids + versions, not a composed `.klickd` file. The catalog never composes a real carrier on a visitor's behalf ([`docs/ux/V4_1-PRESENTATION-STRATEGY.md`](../ux/V4_1-PRESENTATION-STRATEGY.md) §5.6).
- **Implicit pack:** every agent carries `x.klickd/user` implicitly. It is not counted toward the seven-pack ceiling and not listed below.
- **P0 starter packs ≠ Pro tier.** The starter packs `user`, `student`, `research`, `coding` (under [`examples/v4/starter-skills/`](../../examples/v4/starter-skills/)) are **starter skills**, not Pro-tier catalog entries. When they appear in a column labelled "Pro" in a bundle below, that column reflects the audience the bundle targets, not the pack's catalog tier; the underlying pack remains a P0 starter and is **not** counted toward the 8 Lite + 34 Pro catalog totals tracked in [`docs/ux/V4_1-PRESENTATION-STRATEGY.md`](../ux/V4_1-PRESENTATION-STRATEGY.md) §1. They are surfaced through the **C9 Foundations** affordance on `/klickdskill`, not as Pro cards.
- **Bundle size window:** every bundle is sized for **3–7 packs** total (per [`docs/ux/V4_1-PRESENTATION-STRATEGY.md`](../ux/V4_1-PRESENTATION-STRATEGY.md) §7a). Bundle 1 deliberately overflows to 8 to demonstrate the agent-split resolution path; production bundles MUST stay in 3–7.
- **Composition graph:** every bundle MUST form an acyclic composition graph rooted on `x.klickd/user`. If two listed packs both name the other as a parent, the bundle is rejected.
- **Token estimate:** each bundle row gives a coarse `Σ tokens_estimate` based on the size tiers (Lite ≤ 900, Pro ≤ 1,350). Exact router_cost lives in each pack's own file.
- **Agent count rationale:** the table at the end of each bundle states "why N agents" — splitting by responsibility boundary (who owns the artifact, who reviews it, who escalates) and by `final_decision_owner` per RFC-002.
- **Human authority:** every bundle assumes `raise_only: true` and `final_decision_owner = human_carrier` (or `human_carrier_with_guardian` where guardianship is in scope). No bundle below downgrades a gate.

---

## 1. Bundle: **Startup A → Z** (founder + first 3 hires)

**Goal.** From idea to shipped EU-compliant product, by a 2–4 person team without a dedicated legal or security hire.

| Role | Pack(s) | Category | Tier | Why |
|---|---|---|---|---|
| Founder / generalist | `x.klickd/work_assistant` + `x.klickd/project_operator` | Work | Lite + Pro | Day-to-day + multi-track project ownership without a senior PM seat. |
| Engineer | `x.klickd/coding` (P0 starter, see §0) + `x.klickd/llm_agent_engineering` | Developer/AI | P0 starter + Pro | Coding baseline + LLM-agent build discipline (tool-use, evals, sandboxing). |
| Designer / creator | `x.klickd/media_planner` + `x.klickd/artist` | Creator/Media | Lite | Plans the comms surface; ships visual identity without a senior brand lead. |
| Compliance hat (worn by founder) | `x.klickd/gdpr_readiness` + `x.klickd/eu_ai_act` | Legal/Compliance | Pro | Two highest-risk EU regimes for a SaaS shipping AI features. |

**Σ packs (excluding `user`):** 8 — exceeds the seven-pack-per-agent ceiling. **Resolve by splitting into 3 agents** that each load ≤ 3 packs and share via the agent-handoff surface of [RFC-009 §5.3](../rfcs/RFC-009-chimera-v4.1.md). (See the agent table immediately below.)

**Recommended agent count:** **3 agents.**

| Agent | Packs | Final decision owner |
|---|---|---|
| **Builder** | `coding` + `llm_agent_engineering` + `work_assistant` | human_carrier (founding engineer). |
| **Shipper** | `project_operator` + `media_planner` + `artist` | human_carrier (founder). |
| **Compliance** | `gdpr_readiness` + `eu_ai_act` | human_carrier (founder), with escalation note for first DPA contact. |

**Why 3 not 1:** the three responsibility boundaries (build / ship / comply) have different review cadences and different escalation paths. Collapsing them into one agent makes the compliance gates either constantly loud (annoying) or silently softened (dangerous).

---

## 2. Bundle: **AI app, EU-compliant** (regulated AI feature in a SaaS)

**Goal.** Ship an LLM-backed feature that passes a real DPIA and an EU AI Act risk classification, with traceable evidence.

| Pack | Category | Tier |
|---|---|---|
| `x.klickd/llm_agent_engineering` | Developer/AI | Pro |
| `x.klickd/llm_agent_security` | Security/Trust | Pro |
| `x.klickd/identity_access_management` | Security/Trust | Pro |
| `x.klickd/eu_ai_act` | Legal/Compliance | Pro |
| `x.klickd/gdpr_readiness` | Legal/Compliance | Pro |
| `x.klickd/privacy_product` | Legal/Compliance | Pro |
| `x.klickd/trust_evidence` | Security/Trust | Pro |

**Σ packs:** 7 (at ceiling). All Pro, all `compact_index_plus_lazy_body`. **Σ tokens (compact):** ~6.5 k worst case.

**Recommended agent count:** **4 agents.**

| Agent | Packs | Final decision owner |
|---|---|---|
| **AI Engineer** | `llm_agent_engineering` + `llm_agent_security` | human_carrier (lead engineer). |
| **IAM / Platform** | `identity_access_management` + `trust_evidence` | human_carrier (SRE / platform). |
| **DPO** | `gdpr_readiness` + `privacy_product` | human_carrier (DPO or acting DPO). |
| **AI Act lead** | `eu_ai_act` | human_carrier (compliance lead). |

**Why 4 not 2:** the AI Act and GDPR regimes have distinct evidence chains (`eu_ai_act` references the conformity assessment surface; `gdpr_readiness` references DPIA + records of processing). Bundling them under one agent dilutes the evidence trail; splitting keeps `trust_evidence` clean.

---

## 3. Bundle: **Video marketing campaign**

**Goal.** Plan, produce, ship, and measure a multi-channel video campaign with reusable cutdowns.

| Pack | Category | Tier |
|---|---|---|
| `x.klickd/media_planner` | Creator/Media | Lite |
| `x.klickd/video_production_pipeline` | Creator/Media | Pro |
| `x.klickd/streaming_creator` | Creator/Media | Lite |
| `x.klickd/artist` | Creator/Media | Lite |
| `x.klickd/rights_guard` | Legal/Compliance | Pro |
| `x.klickd/project_operator` | Work | Pro |

**Σ packs:** 6.

**Recommended agent count:** **3 agents.**

| Agent | Packs | Final decision owner |
|---|---|---|
| **Producer** | `media_planner` + `project_operator` | human_carrier (campaign lead). |
| **Studio** | `video_production_pipeline` + `artist` | human_carrier (head of production). |
| **Distribution** | `streaming_creator` + `rights_guard` | human_carrier (channel manager), with escalation to legal on any third-party clip. |

**Why 3:** producer/studio/distribution map onto distinct review boards (creative review, technical review, rights clearance). `rights_guard` lives with distribution because that is where third-party clips actually land.

---

## 4. Bundle: **Research article**

**Goal.** From literature review to a publishable draft, traceable claims, no fabricated citations.

| Pack | Category | Tier |
|---|---|---|
| `x.klickd/research` (P0 starter, see §0) | C9 Foundations affordance (audience: Research/Knowledge) | P0 starter |
| `x.klickd/literature_review` | Research/Knowledge | Pro |
| `x.klickd/second_brain` | Research/Knowledge | Pro |
| `x.klickd/policy_analyst` | Research/Knowledge | Pro |
| `x.klickd/evidence_desk` | Security/Trust | Pro |

**Σ packs:** 5.

**Recommended agent count:** **2 agents.**

| Agent | Packs | Final decision owner |
|---|---|---|
| **Researcher** | `research` + `literature_review` + `second_brain` | human_carrier (lead author). |
| **Evidence reviewer** | `policy_analyst` + `evidence_desk` | human_carrier (peer reviewer or co-author), `raise_only: true` on every attribution gate. |

**Why 2 not 1:** keeping the reviewer agent separate is the cheapest way to enforce the RFC-002 §8b grounding rule — the writer agent cannot self-approve its own citations.

---

## 5. Bundle: **Creator solo** (one human, one agent stack)

**Goal.** A solo creator who writes, shoots, edits, and ships across platforms — the most common "everyday user" case.

| Pack | Category | Tier |
|---|---|---|
| `x.klickd/artist` | Creator/Media | Lite |
| `x.klickd/streaming_creator` | Creator/Media | Lite |
| `x.klickd/media_planner` | Creator/Media | Lite |
| `x.klickd/social_literacy` | Everyday | Lite |
| `x.klickd/consumer_rights` | Everyday | Lite |

**Σ packs:** 5, all Lite. **Σ tokens:** ~4.0 k (fits comfortably under a single small-model context).

**Recommended agent count:** **1 agent.**

| Agent | Packs | Final decision owner |
|---|---|---|
| **Solo studio** | all five | human_carrier (the creator). |

**Why 1:** the solo creator IS the carrier. Splitting into multiple agents adds coordination overhead without changing the review boundary (there is no second human reviewer). This bundle is the canonical demonstration that Lite-only stacks are first-class on `/klickdskill`.

---

## 6. Bundle: **Security review** (independent red-team / audit)

**Goal.** An external reviewer audits an AI-touching product before launch.

| Pack | Category | Tier |
|---|---|---|
| `x.klickd/llm_agent_security` | Security/Trust | Pro |
| `x.klickd/identity_access_management` | Security/Trust | Pro |
| `x.klickd/trust_evidence` | Security/Trust | Pro |
| `x.klickd/evidence_desk` | Security/Trust | Pro |
| `x.klickd/release_engineer` | Developer/AI | Pro |
| `x.klickd/contract_review` | Legal/Compliance | Pro |

**Σ packs:** 6.

**Recommended agent count:** **3 agents.**

| Agent | Packs | Final decision owner |
|---|---|---|
| **Red-team** | `llm_agent_security` + `release_engineer` | human_carrier (lead reviewer). |
| **IAM / evidence** | `identity_access_management` + `trust_evidence` | human_carrier (platform reviewer). |
| **Contract / evidence reviewer** | `contract_review` + `evidence_desk` | human_carrier (independent reviewer, MUST NOT be the same human as red-team for `security` composes per [RFC-009 §8](../rfcs/RFC-009-chimera-v4.1.md)). |

**Why 3:** the two-reviewer rule for `security` composes is mechanical, not aesthetic. Two independent humans is the gate; collapsing into one agent collapses into one human and breaks §8.

---

## 7. Bundle: **Game / NPC prototype**

**Goal.** Prototype a small game with one or more NPCs that have framework-anchored carriers (no homegrown personality blob).

| Pack | Category | Tier |
|---|---|---|
| `x.klickd/game_design` | Creator/Media | Pro |
| `x.klickd/game_literacy` | Everyday | Lite |
| `x.klickd/rights_guard` | Legal/Compliance | Pro |
| `x.klickd/parent_gaming` | Everyday | Lite |
| `x.klickd/coding` (P0 starter, see §0) | C9 Foundations affordance (audience: Developer/AI) | P0 starter |

**Σ packs:** 5.

**Recommended agent count:** **2 agents + N NPC agents (demo: 2).**

| Agent | Packs | Final decision owner |
|---|---|---|
| **Designer** | `game_design` + `coding` | human_carrier (designer / engineer). |
| **Player-safety** | `game_literacy` + `parent_gaming` + `rights_guard` | human_carrier (community / safety lead). |
| **NPC #1, #2** | each: a single non-host carrier (do **not** ship behaviour in the carrier — the NPC's behaviour belongs in the host game runtime, per [RFC-009 §5.1.1](../rfcs/RFC-009-chimera-v4.1.md)). | human_carrier (designer signs off on each NPC carrier). |

**Why 2 + 2:** game design and player safety are different review boards (one shapes the game, one shapes the constraint). NPC agents are demoed at 2 to make the "non-host_skill" boundary visible — adding more NPCs is a host-runtime decision, not a `/klickdskill` decision.

---

## 8. Bundle: **Drone / mission ops**

**Goal.** A small drone or robotics team running a real-world operation (mapping, inspection, delivery) with audit-grade logs.

| Pack | Category | Tier |
|---|---|---|
| `x.klickd/drone_operator` | Operations/Mission | Pro |
| `x.klickd/mission_control` | Operations/Mission | Pro |
| `x.klickd/identity_access_management` | Security/Trust | Pro |
| `x.klickd/trust_evidence` | Security/Trust | Pro |
| `x.klickd/gdpr_readiness` | Legal/Compliance | Pro |

**Σ packs:** 5.

**Recommended agent count:** **3 agents.**

| Agent | Packs | Final decision owner |
|---|---|---|
| **Pilot** | `drone_operator` | human_carrier (the pilot — `raise_only: true`, no automated launch). |
| **Ground control** | `mission_control` + `identity_access_management` | human_carrier (mission supervisor). |
| **Compliance / log keeper** | `trust_evidence` + `gdpr_readiness` | human_carrier (operations compliance, especially for any over-flight of inhabited areas). |

**Why 3:** the pilot's gates ("clear to launch", "abort") are loud and binary; the ground controller's are operational; the compliance agent's are audit-bound. Three boundaries → three agents. This is the bundle where `final_decision_owner = human_carrier` matters most viscerally.

---

## 9. Bundle: **Support / sales ops**

**Goal.** Run a small support + sales operation across a few channels with carrier-grade hand-off notes (no host-side tone or pedagogy in the pack).

| Pack | Category | Tier |
|---|---|---|
| `x.klickd/work_assistant` | Work | Lite |
| `x.klickd/project_operator` | Work | Pro |
| `x.klickd/consumer_rights` | Everyday | Lite |
| `x.klickd/contract_review` | Legal/Compliance | Pro |
| `x.klickd/customer_support_operator` | Work | Pro |
| `x.klickd/sales_operator` | Work | Pro |

**Σ packs:** 6 (all 6 are `candidate_mapped` at the head of PR #75; none is `ship_ready` yet — see [`docs/ux/V4_1-PRESENTATION-STRATEGY.md`](../ux/V4_1-PRESENTATION-STRATEGY.md) §1.2).

**Recommended agent count:** **3 agents.**

| Agent | Packs | Final decision owner |
|---|---|---|
| **Support** | `work_assistant` + `consumer_rights` + `customer_support_operator` | human_carrier (support lead). |
| **Sales** | `project_operator` + `sales_operator` | human_carrier (sales lead). |
| **Contracts** | `contract_review` | human_carrier (deal desk / legal). |

**Why 3:** support, sales, and contracts have different review cycles and different consent surfaces; in particular, `contract_review` MUST live with a human empowered to refuse a deal.

---

## 10. Demo summary table

| Bundle | Packs | Agents | All `ship_ready` today? |
|---|---:|---:|---|
| 1. Startup A → Z | 8 | 3 | no — all `candidate_mapped`; none `ship_ready` yet |
| 2. AI app EU-compliant | 7 | 4 | no — all `candidate_mapped`; none `ship_ready` yet |
| 3. Video marketing campaign | 6 | 3 | no — all `candidate_mapped`; none `ship_ready` yet |
| 4. Research article | 5 | 2 | no — all `candidate_mapped`; none `ship_ready` yet |
| 5. Creator solo | 5 | 1 | no — all `candidate_mapped`; none `ship_ready` yet |
| 6. Security review | 6 | 3 | no — all `candidate_mapped`; none `ship_ready` yet |
| 7. Game / NPC prototype | 5 | 2 + 2 NPC | no — all `candidate_mapped`; none `ship_ready` yet |
| 8. Drone / mission ops | 5 | 3 | no — all `candidate_mapped`; none `ship_ready` yet |
| 9. Support / sales ops | 6 | 3 | no — all `candidate_mapped` (incl. PR #75's `customer_support_operator` / `sales_operator`); none `ship_ready` yet |

**None of the 42 v4.1 catalog packs is `ship_ready` yet.** Every bundle above forms an acyclic composition graph rooted on `x.klickd/user`, respects the seven-pack ceiling at the agent (not bundle) level, and is reproducible from the `.klickd` artefacts in [`examples/v4.1/x-klickd-skills/`](../../examples/v4.1/x-klickd-skills/) and [`examples/v4/starter-skills/`](../../examples/v4/starter-skills/). No bundle below appears on the live `/klickdskill` catalog until **each** of its packs clears [RFC-009 §8](../rfcs/RFC-009-chimera-v4.1.md).

---

## 11. What these bundles are NOT

- **They are not endorsements.** No bundle is "the right way" to do a job; they are demonstrations of how the catalog composes.
- **They are not products.** None of these bundles is wrapped, branded, or sold.
- **They are not benchmarks.** Token sums are coarse demo numbers; the normative router_cost lives in each pack.
- **They are not pre-composed `.klickd` files.** A bundle is a list; composition happens at the host.

---

## 12. See also

- [`docs/ux/V4_1-PRESENTATION-STRATEGY.md`](../ux/V4_1-PRESENTATION-STRATEGY.md)
- [`docs/community/V4_1-CHALLENGE-CHIMERA-CUP.md`](../community/V4_1-CHALLENGE-CHIMERA-CUP.md)
- [`docs/chimera/README_V4_1.md`](../chimera/README_V4_1.md)
- [`docs/rfcs/RFC-009-chimera-v4.1.md`](../rfcs/RFC-009-chimera-v4.1.md)
- [`examples/v4.1/x-klickd-skills/`](../../examples/v4.1/x-klickd-skills/)
- [`examples/v4/starter-skills/`](../../examples/v4/starter-skills/)
