# `.klickd v4.1 — Chimera` — competency identification protocol

| | |
|---|---|
| **Status** | **Draft · NON-NORMATIVE · planning + reviewer aid** |
| **Track** | `.klickd v4.1` — Chimera (post-`v4.0.0` GA) |
| **Created** | 2026-05-27 |
| **Companion** | [`V4_1_SKILL_CANDIDATE_MAPPING.md`](./V4_1_SKILL_CANDIDATE_MAPPING.md) · [`V4_1_CANDIDATE_CHECKLIST.md`](./V4_1_CANDIDATE_CHECKLIST.md) · [`README_V4_1.md`](./README_V4_1.md) |
| **Validator** | [`scripts/validate_v4_1_candidate_mapping.py`](../../scripts/validate_v4_1_candidate_mapping.py) — competency-coherence + anti-clone checks |

> **Non-normative.** This document records the **method** used to select competencies for every Chimera v4.1 candidate skill. It does **not** introduce any new schema, change `frameworks[]`/`competencies[]` shape, or alter the v4.0 envelope. It is the merge gate for [RFC-009](../rfcs/RFC-009-chimera-v4.1.md) §8 §8.1 (framework-anchor) and §8.2 (carrier-vs-skill).

This protocol exists because the user asked, on 2026-05-27, for an explicit and auditable method: **competencies must not be thrown randomly into a skill**. Every skill must be a coherent blend of (a) a shared transversal base and (b) a small set of domain-specific competencies, each anchored to an authoritative framework.

---

## 0. Why this protocol

Three concrete risks if there is no documented method:

1. **Random stuffing.** A reviewer adds "WEF complex problem solving" to every skill because it sounds plausible, and the catalog turns into noise.
2. **Clones.** Two skills accumulate the same six ESCO ids and end up indistinguishable except by name.
3. **Homegrown taxonomy creep.** A reviewer invents `klickd:my-skill` because nothing in ESCO fits, in violation of [RFC-009 §5.7](../rfcs/RFC-009-chimera-v4.1.md).

This document defines the **method** used to reject all three. The validator enforces a mechanical subset; the rest is reviewer discipline.

---

## 1. Admissible source hierarchy

Competencies are anchored ONLY to the canonical framework registry of [`docs/rfcs/chimera/frameworks/README.md`](../rfcs/chimera/frameworks/README.md) §1. Two distinct shapes:

### 1.1 Framework anchors (registered in `frameworks[]`)

These are the only schemes a `competency_ref` may reference. SKOS-published or equivalent (stable IRI prefix + a public canonical URL):

| Scheme | Source | Use |
|---|---|---|
| **ESCO** v1.1.1 | European Commission — `http://data.europa.eu/esco/skill/` | Generic skill / occupation anchor; broad coverage. |
| **DigComp** 2.2 | EU JRC | Digital competence (information, communication, content, safety, problem-solving). |
| **LifeComp** 2020 | EU JRC | Personal / social / learning-to-learn competence (transversal). |
| **EQF** 2017 | EU | Qualification level (1..8) — used in `levels[]`, not `competencies[]`. |
| **CEFR** 2020 | Council of Europe | Language proficiency — used in `language_proficiency[]`. |
| **WEF** Future of Jobs 2023 | World Economic Forum | Transversal skills (analytical thinking, leadership, etc.). |
| **O\*NET** 28.0 | US Department of Labor | Occupation cross-walk. |
| **NICE** NIST SP 800-181r1 | NIST | Cybersecurity workforce. |
| **ENISA** ECSF 1.0 | ENISA | Cybersecurity workforce (EU). |
| **CIS** v8 | CIS | Cyber-security controls. |
| **SFIA** 8 | SFIA Foundation | ICT competency by id-link only unless a licence is held. |

A scheme not in this list (or not yet SKOS-published with comparable maturity) is **citation-only**, NOT a framework anchor (see §1.2).

### 1.2 Citation-only references (NOT in `frameworks[]`)

Regulations, standards, methodologies, and trade frameworks that are referenced for context but are not registered competency taxonomies. They live in `citation_only_references[]` (when present) — never in `frameworks[]` and never as the `scheme` of a `competency_ref`.

Examples already used in the catalog:

- EU AI Act (Regulation (EU) 2024/1689)
- EU Medical Device Regulation (Regulation (EU) 2017/745)
- GDPR (Regulation (EU) 2016/679)
- EU Consumer Rights Directive 2011/83/EU
- EU Copyright Directive 2019/790, Berne Convention, Creative Commons 4.0
- CSRD / ESRS / GHG Protocol
- WHO Ethics and Governance of AI for Health
- PRISMA 2020, ENISA Privacy by Design, EDPB guidelines
- OWASP (Top 10, ASVS, LLM Top 10)
- FFmpeg, SRT, MoneyPrinterTurbo (technical references)

OWASP is a special case: the OWASP **competency model** is not SKOS-published at registry-comparable maturity, so OWASP enters as citation-only. Specific OWASP controls and threat-class names may be cited in pack notes; the underlying competency MUST still anchor to NICE / ENISA / CIS / ESCO.

### 1.3 Forbidden anchors

- Homegrown taxonomies (`klickd:*` IRI, internal competency lists, narrative `level: "advanced"`).
- Persona-harvested fields (`knowledge.mastered[]`, `mastered_topics[]`, free-text mastery).
- Method / pedagogy / prompting-strategy fields (forbidden by RFC-009 §5.1.1 and frozen in `forbidden_fields[]`).
- Klickd.app product carriers (`klickdapp.*`) and Kai host-side skills (`kai.*`, `skill.kai.*`, `core.Kai.klickd`).

---

## 2. Selection method (per skill, per competency)

For each candidate skill, the author runs this six-step decomposition. Reviewers verify it during the C-001..C-012 checklist run.

### Step 1 — Job / task decomposition

Decompose the target carrier into the 6–12 day-to-day **tasks** they actually perform. Tasks are verb-led ("design the eval harness", "triage the incoming incident", "reconcile the AR ledger"). Anything that is not a task (background knowledge, "general curiosity", "good at writing") is dropped.

### Step 2 — Competency candidates

For each task, list the 1–3 competencies the carrier needs to perform it. Use everyday language at this step ("knows how to design an evaluation rubric for a multi-turn LLM agent"). Avoid jargon and avoid premature framework labels.

### Step 3 — Framework anchor

For each candidate competency, find the **closest** matching entry in the §1.1 registry. If two entries fit, pick the one with the **narrowest** scope. If nothing fits within a maturity-comparable framework, the competency is **deferred** (no anchor → no inclusion → either the skill itself is `needs_mapping` or the competency is moved to a `Open questions` row in the planning doc).

### Step 4 — Relevance score

Score each anchored competency on three axes (each 0–2):

| Axis | 0 | 1 | 2 |
|---|---|---|---|
| **Task coverage** | covers <30 % of one task | covers one task fully | covers multiple tasks |
| **Distinctiveness** | already covered by base transversal | already covered by parent pack | adds capability not in base/parent |
| **Stability** | scheme contested / under revision | scheme stable but rare in catalog | scheme stable + already in catalog |

A competency with **total ≥ 4** is included; **2–3** is included only if the skill would otherwise fall below the §3.1 floor; **0–1** is dropped.

This score is a reviewer aid, NOT a number written into the artefact. The audit trail lives in the planning doc commit message + the candidate's row in `V4_1_SKILL_CANDIDATE_MAPPING.md`.

### Step 5 — Risk / safety gates

For every included competency, ask:

- Does the task it covers touch **regulated advice** (financial, legal, medical, tax)? If yes, the skill MUST carry a `block`-level gate on output that resembles such advice, with mandatory escalation. If the gate cannot be designed (because the very purpose of the skill IS to give regulated advice), the skill is **deferred**, not shipped.
- Does the task involve **third-party PII** (other employees, customers, minors, patients)? If yes, the pack MUST be pointer-only and consent-shape-aware. If a consent shape cannot be designed, the skill is deferred.
- Does the task touch **irreversible / safety-critical action** (production deploy, public disclosure, agent deployment, drone flight, statutory filing)? If yes, the skill MUST carry a `confirm` or `block` gate on the action class, and the gate is on `non_lowerable_floor[]`.

### Step 6 — Memory / evidence impact

For every included competency, declare:

- Which `memory_segment` (operational, evidence, …) carries the relevant carrier state — pointer-only, per RFC-009 §5.6.
- Which `evidence_policy.attestation_shape_ref` applies (defaults to RFC-002 §8b).
- Whether `evidence_policy.pointer_only` MUST stay `true` (almost always yes).

If a competency would require inline content (notes, transcripts, raw PII), it is **deferred** — Chimera packs carry state, not content.

---

## 3. Coherence rules

Every shipped artefact under `examples/v4.1/chimera-skills/{lite,pro}/` MUST satisfy:

### 3.1 Tier-specific competency-count range

The total `competencies[]` count (transversal **base** + domain-specific) MUST land inside the tier's range. Counts include both `competency_mappings[]` and `competencies[]` (which are equal-shape per RFC-009 §5.5).

| Tier | Minimum `competencies[]` | Maximum `competencies[]` | Target |
|---|---|---|---|
| **Lite** | 2 | 8 | 3–6 |
| **Pro** | 3 | 12 | 5–10 |

Below the minimum the skill is too thin to justify a separate pack (fold it into a parent). Above the maximum the skill is over-stuffed and probably needs to split. Target ranges are not enforced; they are reviewer guidance. **Enforced floors and ceilings are the min / max columns**, matching the as-shipped 2026-05-27 catalog.

### 3.2 Common transversal base

Every artefact MUST carry `base_transversal_core.transversal_refs[]` with **at least one** entry drawn from the transversal layer of the registry (ESCO S1 / S2 / S3 cross-cutting, LifeComp Personal / Social, WEF transversal, DigComp transversal). The transversal base is the "shared" half of the user's coherent-blend requirement.

In practice the catalog uses:

- `esco:S2` (information skills) — most knowledge / research / engineering packs.
- `esco:S1` / `esco:S1.3` / `esco:S1.4` (communication, collaboration) — work / customer / sales packs.
- `lifecomp:P1` / `lifecomp:S1` / `lifecomp:S2` / `lifecomp:L1` / `lifecomp:L3` (self-regulation, empathy, collaboration, growth mindset, managing learning) — pedagogy-adjacent packs.

The validator counts the transversal layer and rejects any artefact with zero entries.

### 3.3 Domain-specific competencies = `competencies[]` minus the transversal base

The "domain-specific" set is what is left after subtracting `base_transversal_core.transversal_refs[]` ids from `competencies[]`. This is the **distinctive** half of the blend.

- For Lite, the domain-specific set is 1–6 entries (target 2–4).
- For Pro, the domain-specific set is 2–11 entries (target 4–9).

The validator does not enforce a hard floor on the domain-specific count (because some narrow regulation-anchored Pro packs legitimately ship with three anchors plus a stricter gate set), but the **anti-clone rule of §3.4** does: if a skill's domain-specific set is identical to another skill's, the validator fails.

### 3.4 Anti-clone rule

For any two artefacts A and B in the catalog:

- The full `competencies[]` set of A and B (compared as a Python `frozenset` over `competency_ref` strings) MUST NOT be identical. A failure here means one of the two is a duplicate that should be merged or removed.
- The domain-specific set (full set minus transversal base) of A and B MUST NOT be identical either, unless both A and B have a **task boundary** that justifies overlap (e.g. an author-side and a reader-side pack — `game_design` vs `game_literacy`). The validator emits a warning, not a hard fail, when this exception is recorded in the planning doc.

In the 2026-05-27 catalog, **no two artefacts share an identical competency set** (verified offline; see commit message for the audit table).

### 3.5 Carrier-vs-skill discipline

Forbidden keys (frozen list, enforced by validator):

```
pedagogy, teaching_method, socratic_steps, prompt_strategy,
scoring_rubric, intervention_policy, tone_rules,
system_prompt_overrides, knowledge.mastered, mastered_topics
```

These belong to `host_skill` artefacts (RFC-009 §5.1.1), not to `carrier_pack`s. No competency may describe a teaching method or a prompting strategy; it must describe a **capability** the carrier holds.

---

## 4. Exclusion rules (when a candidate is deferred, not shipped)

A skill is **deferred** (status `needs_mapping`, no `.klickd` artefact) when **any** of these conditions holds:

1. **No framework anchor.** No scheme in §1.1 covers the candidate's distinctive task with SKOS-comparable maturity. Examples: `crypto-lite` (no crypto-asset-literacy framework with DigComp / NICE maturity), `personal-finance` (no SKOS-published financial-literacy framework), `wellbeing-lite` (WHO health-literacy not SKOS-published).
2. **Regulated advice that cannot be gated.** The candidate's whole purpose is to deliver regulated financial / legal / medical / tax advice that, by law, requires a licensed professional. Gates can `block` outputs that resemble such advice; they cannot substitute for the licence. If the skill cannot exist without producing the advice, defer.
3. **Belongs elsewhere.** The candidate is in fact a Klickd.app product carrier (`klickdapp.*`) or a Kai host-side skill (`kai.*`, `skill.kai.*`, `core.Kai.klickd`). Validator rejects.
4. **Task duplication.** The candidate's task set overlaps an already-shipped skill ≥ 70 % and there is no clean task-boundary distinction (author vs reader, design vs operate, cloud vs edge, attack vs defend, intake vs disclosure). Merge instead of cloning.
5. **Inline content required.** The skill cannot do its job without storing inline notes, transcripts, raw PII, or content excerpts. Chimera packs are pointer-only; defer until the design admits a pointer-only shape.

When deferred, the candidate stays in [`V4_1_SKILL_CANDIDATE_MAPPING.md`](./V4_1_SKILL_CANDIDATE_MAPPING.md) §1 / §2 with a clear `Open` line naming the missing anchor / gate / boundary; no `.klickd` is produced; the validator's `DEFERRED_NICKNAMES` set rejects any future attempt to add one.

---

## 5. Validator support

The validator [`scripts/validate_v4_1_candidate_mapping.py`](../../scripts/validate_v4_1_candidate_mapping.py) enforces the mechanical subset of this protocol:

| Rule | Validator check | Test |
|---|---|---|
| §1.1 (admissible schemes only) | `frameworks[]` non-empty + SKOS-shaped (`scheme` present) | `test_every_artefact_passes_validator` |
| §1.3 (forbidden anchors) | `forbidden_fields` literal frozen; no Klickd.app/Kai patterns | `test_no_klickdapp_or_kai_in_any_artefact` |
| §3.1 (tier-specific count range) | `TIER_COMPETENCY_RANGE = {"lite": (2, 8), "pro": (3, 12)}` enforced | `test_competency_count_in_tier_range` |
| §3.2 (common transversal base) | `base_transversal_core.transversal_refs[]` non-empty | `test_every_artefact_carries_transversal_base` |
| §3.4 (anti-clone) | No two artefacts share identical `competencies[]` sets | `test_no_two_artefacts_share_competency_set` |
| §3.5 (carrier-vs-skill) | `forbidden_fields` frozen + no forbidden key paths in body | (existing) `test_every_artefact_passes_validator` |
| §4.1 (deferred candidates) | `DEFERRED_NICKNAMES` set | `test_no_deferred_candidate_has_an_artefact` |

The protocol's review-level steps (§2 step 4 relevance score, §2 step 6 memory impact, §3.3 domain-specific target ranges) are **not** machine-checkable in general and stay reviewer-owned.

### Schema impact

**None.** This protocol does NOT add or change any field in the v4.0 envelope or the `x_klickd_pack` payload. It uses existing fields (`base_transversal_core.transversal_refs[]`, `competency_mappings[]`, `competencies[]`, `frameworks[]`, `citation_only_references[]`) that every artefact already carries. There is no migration. The 42 already-shipped artefacts pass the new validator without edits (audit-verified 2026-05-27).

---

## 6. As-shipped catalog audit (2026-05-27)

The 42 candidate artefacts (8 Lite + 34 Pro) pass all mechanical checks introduced by this protocol:

- 42 / 42 carry `frameworks[]` with at least one scheme from §1.1.
- 42 / 42 carry `base_transversal_core.transversal_refs[]` with ≥ 1 entry.
- 42 / 42 land inside `TIER_COMPETENCY_RANGE` (Lite 2–8 total competencies, Pro 3–12).
- 42 / 42 unique `competencies[]` sets — **no clones detected**.
- 5 / 5 deferred nicknames (`personal-finance`, `budget`, `crypto-lite`, `wellbeing-lite`, `family`) have no artefact, per §4.1.

The audit table that produced these counts is in the commit message that introduced this protocol. Reviewers running `python3 scripts/validate_v4_1_candidate_mapping.py` reproduce it locally.

---

## 7. See also

- [`V4_1_SKILL_CANDIDATE_MAPPING.md`](./V4_1_SKILL_CANDIDATE_MAPPING.md) — the candidate roster + framework anchors per skill.
- [`V4_1_CANDIDATE_CHECKLIST.md`](./V4_1_CANDIDATE_CHECKLIST.md) — per-candidate review checklist (C-001..C-012). This protocol provides the **method** the checklist verifies.
- [`README_V4_1.md`](./README_V4_1.md) — planning index, strict mapping rule, exclusion table.
- [`docs/rfcs/RFC-009-chimera-v4.1.md`](../rfcs/RFC-009-chimera-v4.1.md) — Chimera RFC (P0/P1, validation §8, no-catalog §7, carrier-vs-skill §5.1.1).
- [`docs/rfcs/chimera/frameworks/README.md`](../rfcs/chimera/frameworks/README.md) — canonical framework registry (the §1.1 list above).
- [`scripts/validate_v4_1_candidate_mapping.py`](../../scripts/validate_v4_1_candidate_mapping.py) — the validator enforcing the mechanical subset.
