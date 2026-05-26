# `docs/rfcs/chimera/packs/` — concrete `carrier_pack` scaffolds

> **Status:** Draft · NON-NORMATIVE · scaffolds only.
> **Track:** `.klickd v4.1` Chimera (see [RFC-009](../../RFC-009-chimera-v4.1.md)).
> **Triggers no release.** No schema, no SDK, no tag, no `latest` on npm/PyPI, **no Zenodo DOI**, no IANA action, no `klickd-ai/site` change.

This directory is where concrete per-pack specs live. They are **scaffolds**, not catalogs: each file describes the **shape** of one `x.klickd/<name>` `carrier_pack` (a `competency_pack` / `domain_pack`), exercises the carrier-vs-skill rule ([RFC-009 §5.1.1](../../RFC-009-chimera-v4.1.md)), and lists what is missing before the pack is real.

> **Canonical vocabulary:** see [RFC-009 §0.1](../../RFC-009-chimera-v4.1.md). A `carrier_pack` is a `.klickd` artefact (the file in this directory). A `host_skill` (`skill.<host>.<domain>.<method>`, e.g. `skill.kai.tutor.socratic`, `skill.coding.assistant`, `skill.research.assistant`) is a host-side behaviour module and is **never** part of a pack. Persona anchors under `examples/v4/personas/` are **neither** packs **nor** skills — they are examples.

## 1. Index

| `carrier_pack` | Spec | Track | Status | Companion `host_skill` (NOT in pack) |
|---|---|---|---|---|
| `x.klickd/student` | [`student.md`](./student.md) | P0 | **Draft scaffold (all ten criteria satisfied at spec / shape level)** (2026-05-26) | `skill.kai.tutor.socratic` |
| `x.klickd/user` | — (router-cost row in [`router_cost.md`](./router_cost.md)) | P0 | Not yet scaffolded; router-cost row published | `skill.kai.assistant.base` (TBD) |
| `x.klickd/coding` | — | P0 | Not yet scaffolded | `skill.coding.assistant` / `skill.kai.dev.review` (TBD) |
| `x.klickd/research` | — | P0 | Not yet scaffolded | `skill.research.assistant` / `skill.kai.research.ground` (TBD) |
| `x.klickd/security` | — | P0 | Not yet scaffolded | `skill.kai.security.threatmodel` (TBD) |
| `x.klickd/legal` | — | P0 | Not yet scaffolded | `skill.kai.legal.advise` (TBD) |
| `x.klickd/work` | — | P1 | Not yet scaffolded (P0 must pass first) | TBD |
| `x.klickd/creator` | — | P1 | Not yet scaffolded (P0 must pass first) | TBD |
| `x.klickd/gaming` | — | P1 | Not yet scaffolded (P0 must pass first) | TBD |
| `x.klickd/bridge` | — | P1 | Not yet scaffolded (P0 must pass first) | TBD |
| `x.klickd/mission` | — | P1 | Not yet scaffolded (P0 must pass first) | TBD |

> The "Companion `host_skill`" column lists the **method** the LLM / agent applies *on top of* the pack. It is **not** part of the pack. See [RFC-009 §0.1, §5.1.1](../../RFC-009-chimera-v4.1.md) and `student.md` §3 for what is forbidden inside a pack.

## 2. The two architectural rules

### 2.1 Carrier-vs-skill (Rule 1)

> **`carrier_pack`s carry state. Hosts carry `host_skill`s.**
>
> A `carrier_pack` describes what the carrier *is* in a domain (learner, developer, researcher, …). The matching pedagogy / method / behaviour (how to *teach*, *review*, *prosecute*, *coach*) is loaded host-side as a `host_skill` (e.g. `skill.kai.tutor.socratic`, `skill.coding.assistant`, `skill.research.assistant`), never embedded in the pack.

This separation is what makes `carrier_pack`s portable across hosts and what lets `host_skill` pedagogy improve without touching user files.

### 2.2 v4.1-native, no legacy adapter (Rule 2)

> **Packs are authored from authoritative frameworks, not adapted from v4-preview personas.**

No `knowledge.mastered[]`, no `mastered_topics[]`, no narrative `level` strings, no implicit `persona → pack` migration. Personas under `examples/v4/personas/` stay v4-preview anchors per [RFC-009 §5.0 / §6](../../RFC-009-chimera-v4.1.md).

## 3. Validation criteria

A scaffold becomes a **real** pack only after satisfying all **ten** criteria of [RFC-009 §8](../../RFC-009-chimera-v4.1.md):

1. Framework anchor (SKOS/JSON-LD into ESCO / WEF / O\*NET).
2. Gates declared (RFC-002 defaults + veto posture).
3. Evidence rules (RFC-002 §8b claim grounding).
4. No PII (publisher-owned, not user-owned).
5. Round-trip safe with v4.0-only readers.
6. Offline-resolvable (SKOS subset bundled).
7. Router-priceable (deterministic token-cost estimate).
8. Human-authority preserved (no pack default lowers user v4.0 gate).
9. No persona reuse (`examples/v4/personas/*` files stay anchors).
10. Carrier-vs-skill separation (no method / pedagogy / prompting / scoring rubric / intervention policy in the pack).

A scaffold that satisfies the rule and the shape but lacks the resolved framework refs, the SKOS bundle, the cost estimate, or the offline-resolvable subset is **not** a real pack. The `student.md` scaffold now satisfies **all ten criteria at spec / shape level**: real framework refs (ESCO v1.1.1 + DigComp 2.2 + LifeComp 2020 + EQF 2017 + CEFR 2020) with stable URLs, offline bundle shape pinned in [`../frameworks/`](../frameworks/), router-cost row published in [`./router_cost.md`](./router_cost.md). The remaining substance blockers are: (1) physical SKOS bundle bytes, (2) strict JSON Schema, (3) round-trip vector.

For the v4.1-native shape contract (top-level fields, types, required, framework anchoring, frozen `forbidden_fields` list), see [RFC-009 §8.1](../../RFC-009-chimera-v4.1.md) and the schema-intent fragments under [`../schema-fragments/`](../schema-fragments/). A candidate pack is reviewed against both.

## 4. The no-fake-catalog rule (explicit)

> **Until a pack passes all ten validation criteria, it MUST NOT be exposed as a download, listing, or catalog entry.**

Concretely, **none** of the following are permitted by this RFC:

- Serving `examples/v4/personas/*.klickd` (or any v4 fixture) as a "competency pack" under `/klickdskill`, `klickd.app/catalog`, or any other surface. Those files are non-normative v4-preview personas and stay so. (See [`examples/v4/personas/README.md`](../../../../examples/v4/personas/README.md).)
- Renaming, repackaging, or aggregating existing fixtures and labelling them `x.klickd/<pack>`.
- Standing up a `/klickdskill` listing page, search index, or API endpoint for "competency packs" before P0 packs satisfy §8.
- Publishing a pack-bundle artefact to npm / PyPI / a public registry with `latest` or `next` channels.
- Depositing any pack to Zenodo or assigning a DOI.
- Adding any pack-related entry to IANA.

These prohibitions are **architectural**, not merely procedural: a fake catalog locks the taxonomy before reviewers can audit it, and the cost of unwinding a published taxonomy is far higher than the cost of waiting.

## 5. Notes for `/klickdskill` (later, not now)

When P0 validation eventually passes, **and only then**, a `/klickdskill` catalog surface MAY be considered. The expected shape, sketched here so reviewers can disagree early:

- One entry per pack, never per persona.
- Each entry links to the canonical pack spec under `docs/rfcs/chimera/packs/<pack>.md`.
- Each entry exposes the pack's framework anchors (ESCO / WEF / O\*NET IRIs), gate defaults, and router-cost estimate (RFC-003 row).
- Each entry MUST NOT bundle user PII. Packs are publisher-owned.
- Each entry MUST be versioned independently of `.klickd` itself; bumping the format does not bump every pack.
- Anchor personas (`01-eleve-terminale-fr`, …) remain **separate** v4-preview fixtures; they MUST NOT appear in the catalog as packs.
- No DOI / Zenodo deposit is implied by catalog presence.

These are notes, not commitments. The first real catalog decision is gated by P0 packs passing §8.

## 6. Persona anchors are anchors

Current v4 personas live at [`examples/v4/personas/`](../../../../examples/v4/personas/) and are non-normative. The mapping to future packs is documented in [RFC-009 §6](../../RFC-009-chimera-v4.1.md):

| Persona (anchor only) | Future pack |
|---|---|
| `01-eleve-terminale-fr` | `x.klickd/student` |
| `02-chef-projet-pme-fr` | `x.klickd/work` |
| `03-fullstack-developer-en` | `x.klickd/coding` |
| `04-createur-media-fr` | `x.klickd/creator` |
| `05-rpg-gamer-en` | `x.klickd/gaming` |
| `student-multi-provider` | `x.klickd/bridge` |

Anchor ≠ pack. A pack is built **from authoritative frameworks**, not from a renamed persona.

## 7. See also

- [`../../RFC-009-chimera-v4.1.md`](../../RFC-009-chimera-v4.1.md) — Chimera RFC (carrier-vs-skill in §5.1.1, validation in §8, no-catalog in §7).
- [`../README.md`](../README.md) — Chimera companion summary.
- [`./student.md`](./student.md) — first concrete pack scaffold.
- [`./router_cost.md`](./router_cost.md) — deterministic heuristic token-cost rows for `x.klickd/user` and `x.klickd/student`, RFC-003-compatible.
- [`../frameworks/README.md`](../frameworks/README.md) — canonical framework registry + offline SKOS/JSON-LD bundle shape.
- [`../schema-fragments/README.md`](../schema-fragments/README.md) — schema-intent fragments for the pack manifest and its constituent blocks.
- [`../../../use-cases/DOMAIN_PROFILE_CATALOG.md`](../../../use-cases/DOMAIN_PROFILE_CATALOG.md) — domain taxonomy precursor (not a catalog).
