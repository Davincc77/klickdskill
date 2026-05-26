# `.klickd v4.1 — Chimera` — pack scope & validation summary

> **Status:** Draft · NON-NORMATIVE · companion to [`RFC-009-chimera-v4.1.md`](../RFC-009-chimera-v4.1.md).
> **Track:** `.klickd v4.1` (post-`v4.0.0` GA).
> **Triggers no release.** No tag, no `latest` on npm/PyPI, no DOI on Zenodo, no IANA action, no schema change.

This document is a short, scannable reference for reviewers. The normative-intent prose lives in [RFC-009](../RFC-009-chimera-v4.1.md); this is the table-and-criteria view.

## 0. Taxonomy (one-line restatement of RFC-009 §0.1)

Canonical Chimera v4.1 vocabulary. **Use these terms; do not invent "skill file" / "student skill" / "domain skill" for `.klickd` artefacts.**

| Term | Side | Means |
|---|---|---|
| `base_transversal_core` | carrier | Cross-pack competency floor; always-on. |
| `carrier_pack` | carrier | Any `x.klickd/<name>` artefact (superset of the next three). |
| `competency_pack` | carrier | A `carrier_pack` declaring competence in a domain (e.g. `x.klickd/student`). |
| `domain_pack` | carrier | Same artefact class as `competency_pack`, emphasised by domain (e.g. `x.klickd/legal`). |
| `temporary_overlay` | carrier | A `carrier_pack` loaded with declared expiry; counts vs the seven-pack ceiling while active. |
| `host_skill` | host | Host-side behaviour module (e.g. `skill.kai.tutor.socratic`, `skill.coding.assistant`, `skill.research.assistant`). Never inside a `carrier_pack`. |
| `decision_router` | host | Advisory router (RFC-007) that swaps packs in/out per turn under user veto. |
| `human_authority_layer` | carrier | The invariant that the user always wins (v4.0 veto + consent + gates + pack `human_authority`). |

Persona anchors (`examples/v4/personas/*.klickd`, `student-multi-provider`) are **neither** packs **nor** skills — they are examples / inspiration. See [RFC-009 §0.1, §6](../RFC-009-chimera-v4.1.md).

## 1. v4.0 vs v4.1 in one line

- **v4.0.0** = portable persona / governance memory (who you are).
- **v4.1 Chimera** = real `competency_pack`s on top of v4.0 (what you can do), consulted by `host_skill`s on the LLM side.

The v4.0 surface is unchanged by v4.1. A v4.0-only reader MUST round-trip v4.1 fields verbatim (SPEC §33.7).

## 1.1 The carrier-vs-skill rule (one-line restatement)

> **`carrier_pack`s carry state. Hosts carry `host_skill`s.**
>
> A `carrier_pack` (`x.klickd/<name>`) describes what the carrier *is* in a domain (learner state, developer state, …). The matching **`host_skill`** — method / pedagogy / behaviour, named `skill.<host>.<domain>.<method>` — is loaded by the Klickd / Kai LLM (or any other host), never embedded in the `carrier_pack`.

Worked examples: `x.klickd/student` (a `competency_pack`) carries learner state; the Socratic tutor `host_skill` `skill.kai.tutor.socratic` lives host-side. Similarly, `x.klickd/coding` is consulted by `skill.coding.assistant`; `x.klickd/research` by `skill.research.assistant`. See [`packs/student.md`](./packs/student.md) and [RFC-009 §0.1, §5.1.1](../RFC-009-chimera-v4.1.md).

## 1.2 Clean-architecture invariant (one-line restatement)

> **v4.1 packs are v4.1-native. There is no compatibility path from v4-preview personas.**

A pack is authored from authoritative frameworks (ESCO / WEF / O\*NET / DigComp / EQF) via SKOS/JSON-LD. It does **not** accept legacy persona keys (`knowledge.mastered[]`, `mastered_topics[]`, narrative `level: "advanced"`, free-text `subjects[].mastery`) as input or alias. Personas remain v4-preview anchors. See [RFC-009 §5.0](../RFC-009-chimera-v4.1.md) and `packs/student.md` §3.2.

## 2. Pack scope table

### P0 — six packs (must ship together; no catalog before all six validate)

| Pack id | Anchors competence in | Framework backbone (§5.7 of RFC-009) | Persona anchor (inspiration only) |
|---|---|---|---|
| `x.klickd/user` | Competent autonomous human — literacy, numeracy, communication, basic digital, civic. | ESCO transversal + DigComp 2.2 | — |
| `x.klickd/student` | Study skills, source evaluation, exam discipline, self-assessment. | ESCO (education), DigComp | `01-eleve-terminale-fr` |
| `x.klickd/coding` | Software engineering — language fluency, code review, test/typecheck rigour, security hygiene. | ESCO ICT + SFIA cross-check | `03-fullstack-developer-en` |
| `x.klickd/research` | Evidence-handling, claim grounding, citation, falsifiability. | ESCO research / WEF "analytical thinking" | — |
| `x.klickd/security` | Threat modelling, blast radius, secrets hygiene, escalation defaults. | NICE + ENISA + CIS | — |
| `x.klickd/legal` | Jurisdictional awareness (FR/LU/EU), GDPR/AI-Act, licensing, escalation to a human professional. | ESCO legal occupations + EU AI Act references | — |

### P1 — five fast-follow packs (only after P0 validation; never before)

| Pack id | Anchors competence in | Framework backbone | Persona anchor (inspiration only) |
|---|---|---|---|
| `x.klickd/work` | Project management, stakeholder communication, deliverable discipline. | ESCO (management), WEF future skills | `02-chef-projet-pme-fr` |
| `x.klickd/creator` | Media production, editorial responsibility, rights handling, RFC-001 `media_profile` discipline. | ESCO creative occupations, RFC-001 | `04-createur-media-fr` |
| `x.klickd/gaming` | Rule comprehension, opponent / NPC modelling, low-stakes reversibility proving ground. | ESCO leisure / WEF "complex problem solving" | `05-rpg-gamer-en` |
| `x.klickd/bridge` | Cross-provider competence — provider-neutral prompting, capability negotiation, fallback discipline. | WEF "technology literacy" | `student-multi-provider` (demo walkthrough) |
| `x.klickd/mission` | Mission-scoped objective + scope + deliverable + time-box + exit conditions. | WEF "active learning" + ESCO transversal | — (first pack without a v4 anchor) |

> **Persona anchors are inspiration only.** They are v4-preview non-normative fixtures (see [`examples/v4/personas/README.md`](../../../examples/v4/personas/README.md)). They MUST NOT be renamed, repackaged, or republished as competency packs. See RFC-009 §6.

## 3. No-catalog rule (mirrors RFC-009 §7)

> Until a real Chimera pack passes validation (§4 below), `/klickdskill` MUST NOT expose any "competency pack" catalog, listing, or download surface.

- Current files under `examples/v4/personas/`, `examples/v4/student-walkthrough/`, `examples/`, and `registry/competencies/` are **not** competency packs and MUST NOT be re-served as such.
- No public catalog, no DOI, no IANA action, no `latest` channel for packs is permitted under this RFC.

## 4. Validation criteria (pre-catalog)

A pack is **not** ready for catalog exposure until **all ten** criteria below are satisfied (mirrors RFC-009 §8):

1. **Framework anchor.** Every competency resolves to a SKOS/JSON-LD reference into ESCO / WEF / O\*NET. No homegrown competency without an external anchor.
2. **Gates declared.** Every action declares RFC-002 `verification_gates` defaults and `human_veto_policy` posture.
3. **Evidence rules.** Every emitted claim declares its grounding rule (RFC-002 §8b, RFC-003 `verification_artifacts[]` shape).
4. **No PII.** Packs are publisher-owned, never user-owned. No user PII, memory, sessions, or consent inside a pack file.
5. **Round-trip safe.** A v4.0-only reader that ignores the pack MUST preserve it verbatim and MUST NOT degrade v4.0 behaviour.
6. **Offline-resolvable.** The pack ships its SKOS/JSON-LD subset; air-gapped open yields full labels.
7. **Router-priceable.** Pack publishes a deterministic token-cost estimate consistent with RFC-003 `chimera_v41_extrapolation()`.
8. **Human-authority preserved.** No pack default lowers a user's v4.0 gate. Static review verifies this.
9. **No persona reuse.** Pack is not a renamed `examples/v4/personas/*` file.
10. **Carrier-vs-skill separation.** The pack carries **state, not behaviour**. No `pedagogy`, `prompt_strategy`, `scoring_rubric`, `intervention_policy`, or `tone_rules` fields. The matching method lives host-side as a Klickd/Kai skill.

A pack passing all ten is eligible for a future promotion RFC + checklist gate. Passing validation does **not** trigger catalog exposure — that is a separate decision.

### 4.0 v4.1-native shape table (validation contract, NOT a JSON Schema)

For the actual per-field validation contract (top-level keys, types, required, framework anchoring, frozen `forbidden_fields` list, etc.), see [RFC-009 §8.1](../RFC-009-chimera-v4.1.md). Reviewers run a candidate pack against that table; this companion only restates the ten criteria.

## 4.1 Concrete scaffolds shipped with this RFC

| Pack | Spec | Status against §4 |
|---|---|---|
| `x.klickd/student` | [`packs/student.md`](./packs/student.md) | Carrier-vs-skill rule satisfied; gates/evidence/no-PII/no-persona-reuse satisfied; framework IRIs, SKOS bundle, router-cost row deferred (explicitly TODO). |

See [`packs/README.md`](./packs/README.md) for the full index, no-fake-catalog reminder, and `/klickdskill` later-notes.

## 5. Architecture quick-reference

- **`human_authority_layer`** — the user always wins; `carrier_pack` defaults compose under user veto.
- **`base_transversal_core`** — small cross-pack competency layer (literacy, numeracy, communication, basic digital, gate reasoning) loaded even when no other `carrier_pack` is active.
- **Up to seven active `carrier_pack`s** per session (matches RFC-003 `base_plus_seven` cost ceiling).
- **`temporary_overlay`** — load a `carrier_pack` for one turn / artefact / project without persistent adoption.
- **`decision_router`** — same component as RFC-007 in-session skill routing; logs each swap as a `decisions[]` record.
- **Extended structured memory** — pack-scoped slices (`memory.x_klickd.<pack>`) addable without touching user main memory.
- **Offline backbone** — ESCO / WEF / O\*NET via SKOS/JSON-LD, bundled per `carrier_pack`. (Framework "skills" in ESCO/WEF vocabulary are *competency anchors*, never `host_skill`s.)

## 6. Pointers

- Full RFC: [`docs/rfcs/RFC-009-chimera-v4.1.md`](../RFC-009-chimera-v4.1.md)
- Concrete pack scaffolds: [`packs/`](./packs/) (index: [`packs/README.md`](./packs/README.md))
- First concrete pack: [`packs/student.md`](./packs/student.md) — `x.klickd/student`
- Cost projection that names v4.1: [`benchmarks/context_cost/README.md`](../../../benchmarks/context_cost/README.md) §"Chimera.klickd v4.1 — forward-looking extrapolation"
- Persona anchors (NOT packs): [`examples/v4/personas/README.md`](../../../examples/v4/personas/README.md)
- Domain taxonomy precursor: [`docs/use-cases/DOMAIN_PROFILE_CATALOG.md`](../../use-cases/DOMAIN_PROFILE_CATALOG.md)
- Composition with agent cores: [`docs/rfcs/RFC-006-agent-core.md`](../RFC-006-agent-core.md)
- Routing model: [`docs/rfcs/RFC-007-usage-profile-skill-routing.md`](../RFC-007-usage-profile-skill-routing.md)
- Pack update veille: [`docs/rfcs/RFC-008-core-update-watch.md`](../RFC-008-core-update-watch.md)
