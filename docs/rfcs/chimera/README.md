# `.klickd v4.1 — Chimera` — pack scope & validation summary

> **Status:** Draft · NON-NORMATIVE · companion to [`RFC-009-chimera-v4.1.md`](../RFC-009-chimera-v4.1.md).
> **Track:** `.klickd v4.1` (post-`v4.0.0` GA).
> **Triggers no release.** No tag, no `latest` on npm/PyPI, no DOI on Zenodo, no IANA action, no schema change.

This document is a short, scannable reference for reviewers. The normative-intent prose lives in [RFC-009](../RFC-009-chimera-v4.1.md); this is the table-and-criteria view.

## 1. v4.0 vs v4.1 in one line

- **v4.0.0** = portable persona / governance memory (who you are).
- **v4.1 Chimera** = real competency packs on top of v4.0 (what you can do).

The v4.0 surface is unchanged by v4.1. A v4.0-only reader MUST round-trip v4.1 fields verbatim (SPEC §33.7).

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

A pack is **not** ready for catalog exposure until **all nine** criteria below are satisfied (mirrors RFC-009 §8):

1. **Framework anchor.** Every competency resolves to a SKOS/JSON-LD reference into ESCO / WEF / O\*NET. No homegrown competency without an external anchor.
2. **Gates declared.** Every action declares RFC-002 `verification_gates` defaults and `human_veto_policy` posture.
3. **Evidence rules.** Every emitted claim declares its grounding rule (RFC-002 §8b, RFC-003 `verification_artifacts[]` shape).
4. **No PII.** Packs are publisher-owned, never user-owned. No user PII, memory, sessions, or consent inside a pack file.
5. **Round-trip safe.** A v4.0-only reader that ignores the pack MUST preserve it verbatim and MUST NOT degrade v4.0 behaviour.
6. **Offline-resolvable.** The pack ships its SKOS/JSON-LD subset; air-gapped open yields full labels.
7. **Router-priceable.** Pack publishes a deterministic token-cost estimate consistent with RFC-003 `chimera_v41_extrapolation()`.
8. **Human-authority preserved.** No pack default lowers a user's v4.0 gate. Static review verifies this.
9. **No persona reuse.** Pack is not a renamed `examples/v4/personas/*` file.

A pack passing all nine is eligible for a future promotion RFC + checklist gate. Passing validation does **not** trigger catalog exposure — that is a separate decision.

## 5. Architecture quick-reference

- **Human authority invariant** — the user always wins; pack defaults compose under user veto.
- **Base transversal core** — small cross-pack competency layer (literacy, numeracy, communication, basic digital, gate reasoning) loaded even when no pack is active.
- **Up to seven active packs** per session (matches RFC-003 `base_plus_seven` cost ceiling).
- **Temporary overlays** — load a pack for one turn / artefact / project without persistent adoption.
- **Decision router** — same component as RFC-007 in-session skill routing; logs each swap as a `decisions[]` record.
- **Extended structured memory** — pack-scoped slices (`memory.x_klickd.<pack>`) addable without touching user main memory.
- **Offline backbone** — ESCO / WEF / O\*NET via SKOS/JSON-LD, bundled per pack.

## 6. Pointers

- Full RFC: [`docs/rfcs/RFC-009-chimera-v4.1.md`](../RFC-009-chimera-v4.1.md)
- Cost projection that names v4.1: [`benchmarks/context_cost/README.md`](../../../benchmarks/context_cost/README.md) §"Chimera.klickd v4.1 — forward-looking extrapolation"
- Persona anchors (NOT packs): [`examples/v4/personas/README.md`](../../../examples/v4/personas/README.md)
- Domain taxonomy precursor: [`docs/use-cases/DOMAIN_PROFILE_CATALOG.md`](../../use-cases/DOMAIN_PROFILE_CATALOG.md)
- Composition with agent cores: [`docs/rfcs/RFC-006-agent-core.md`](../RFC-006-agent-core.md)
- Routing model: [`docs/rfcs/RFC-007-usage-profile-skill-routing.md`](../RFC-007-usage-profile-skill-routing.md)
- Pack update veille: [`docs/rfcs/RFC-008-core-update-watch.md`](../RFC-008-core-update-watch.md)
