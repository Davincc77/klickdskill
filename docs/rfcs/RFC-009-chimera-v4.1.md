# RFC-009 — `.klickd v4.1 — Chimera` (portable competence architecture)

| | |
|---|---|
| **RFC** | 009 |
| **Title** | `.klickd v4.1 — Chimera`: real competency packs on top of v4.0 portable persona / governance memory |
| **Target** | `.klickd v4.1` (post-v4.0.0 GA; pack track, NOT in scope for `v4.0.0` GA P0) |
| **Status** | **Draft** |
| **Author** | Vince C. (Klickd / Luxlearn, Luxembourg) |
| **Created** | 2026-05-26 |
| **Supersedes** | — |
| **Relates to** | RFC-001 (`media_profile`), RFC-002 (`verification_gates`, `human_veto_policy`), RFC-003 (Context Cost Benchmark, §"Chimera.klickd v4.1 — forward-looking extrapolation"), RFC-004 (Migration), RFC-006 (`agent_core`), RFC-007 (`usage_profile` & in-session skill routing), RFC-008 (`core_update_watch`), SPEC §33 (v4-preview), [`docs/use-cases/DOMAIN_PROFILE_CATALOG.md`](../use-cases/DOMAIN_PROFILE_CATALOG.md) |

> **This RFC is non-normative.** It is a **Draft** and is **docs-only**. It does **not** modify any current `SPEC.md` section, schema (`schemas/klickd-payload-v4.schema.json`, `schemas/klickd-payload-v4-preview.schema.json`), SDK, vector, lock file, or RFC status. It introduces **no** new normative field. It does **not** trigger any release: **no** tag, **no** `latest` on npm or PyPI, **no** DOI on Zenodo, **no** IANA action, **no** SDK bump.
>
> The production-recommended `.klickd` remains **v3.5.1**. The GA track is **v4.0.0** (portable persona / governance memory). Chimera (**v4.1**) is the next minor and is described here so reviewers can compare it against the v4.0.0 surface *before* any normative wording or schema lands.

---

## 0. TL;DR — what v4.1 is and is not

- **v4.0.0 GA = portable persona / governance memory.** One `.klickd` file carries a human's identity, memory, preferences, growth, accessibility, ethics, gates, and human-veto policy. This is the format's normative core today (SPEC §33).
- **v4.1 Chimera = real competency packs / portable competence architecture.** On top of the v4.0 base, a user (or an agent) MAY load up to **seven** signed `competency_pack`s (`x.klickd/<pack>`) that declare what the carrier *can do* in a domain: **competencies** (anchored to ESCO / WEF / O\*NET via SKOS/JSON-LD — note that those frameworks use the term "skill" for their entries; in Chimera vocabulary that is a *competency anchor*, not a `host_skill`), expected verifications, allowed tools, escalation gates, and evidence rules. The user keeps the soul; Chimera adds portable competence.
- **Five things v4.1 does NOT do:** (1) it does not become a new envelope, (2) it does not redefine `agent_core` from RFC-006, (3) it does not introduce a public catalog, (4) it does not retire the v4 *personas* (those remain anchors / inspiration only — see §6), (5) it does not change human authority: the human always wins (§5.1).
- **One thing v4.1 *adds* on top of v4.0 that didn't exist before:** the **carrier-vs-skill split** (§5.1.1). A `carrier_pack` (e.g. `x.klickd/student`) carries the carrier's *state* in a domain; the matching *method / behaviour* (how to teach, how to review code, how to reason legally) lives **host-side** as a `host_skill` — e.g. `skill.kai.tutor.socratic`, `skill.coding.assistant`, `skill.research.assistant` — not in the user's file. This is the architectural rule that lets `x.klickd/student` be portable across tutors, exam tools, and parent dashboards. Canonical Chimera vocabulary is fixed in §0.1.
- **Clean-architecture invariant (§5.0).** v4.1 packs are **v4.1-native**. They are built from authoritative skill frameworks (ESCO / WEF / O\*NET / DigComp / EQF) under the SKOS/JSON-LD backbone, not adapted from v4-preview persona fixtures. There is **no compatibility path** by which an old `examples/v4/personas/*.klickd` block (or any legacy `knowledge.mastered[]` / `mastered_topics[]` / persona-shaped `subjects[].mastery` payload) becomes a Chimera pack. Personas remain v4-preview anchors / inspiration; packs are new artefacts. Reviewers MUST treat any "let this old persona key map to a pack field" proposal as a §8 validation failure.

---

## 0.1 Taxonomy (normative term table)

The terms below are the **canonical Chimera v4.1 vocabulary**. Reviewers and implementers MUST use these terms when discussing artefacts under this RFC. Ambiguous phrases like "skill file", "student skill", "domain skill", or "competency skill" — when referring to a `.klickd` carrier artefact — are **forbidden**; use `competency_pack`, `domain_pack`, `carrier_pack`, or `host_skill` (whichever fits) instead.

| Term | What it names | Side (carrier vs host) | Example |
|---|---|---|---|
| `base_transversal_core` | The small cross-pack competency layer (literacy, numeracy, communication, basic digital, gate reasoning) that every Chimera carrier loads, even when no other pack is active. Defined in §5.2. Authored against ESCO transversal + DigComp + EQF. | **Carrier** (always-on) | `x.klickd/user`'s base layer; ESCO `T1.1` reading comprehension. |
| `carrier_pack` | The generic name for **any** `x.klickd/<name>` artefact loaded by a carrier (synonym superset of `competency_pack` + `domain_pack` + temporary overlay variants). Used when a statement applies to *all* `.klickd` packs regardless of subtype. | **Carrier** | Any `x.klickd/<name>` block. |
| `competency_pack` | A `carrier_pack` whose role is to declare what the carrier **can do** in a domain — competencies, mastery, evidence rules, gates. All P0/P1 packs of §3 / §4 are competency packs. | **Carrier** | `x.klickd/student`, `x.klickd/coding`, `x.klickd/legal`. |
| `domain_pack` | Synonymous with `competency_pack` when emphasising the **domain scope** (education, software, law, security, …). Use `domain_pack` when the surrounding sentence is about *which domain*; use `competency_pack` when it is about *what competence*. The two are the same artefact class. | **Carrier** | `x.klickd/legal` viewed as the legal **domain** pack. |
| `temporary_overlay` | A `carrier_pack` loaded with a declared expiry (turn / time / artefact boundary) — see §5.4. Counts against the seven-pack ceiling **while active**, never writes back to v4.0 memory without explicit user consent. | **Carrier** (ephemeral) | `x.klickd/legal` loaded for one document review only. |
| `host_skill` | A **host-side behaviour module** loaded by the LLM / agent (Klickd, Kai, or any other host). Carries method, pedagogy, tone, prompting strategy, scoring rubric, intervention policy. Names follow `skill.<host>.<domain>.<method>` (e.g. `skill.kai.tutor.socratic`, `skill.coding.assistant`, `skill.research.assistant`). A `host_skill` is **never** part of a `carrier_pack`. | **Host** | `skill.kai.tutor.socratic`, `skill.coding.assistant`, `skill.research.assistant`. |
| `decision_router` | The conceptual component (same as RFC-007 §"in-session skill routing") that picks the initial active pack set from `usage_profile`, swaps packs in/out per turn, and logs each swap as a `decisions[]` record (§5.5). Advisory, not coercive — the user can pin or veto. | **Host** (advisory) | The runtime that activates `x.klickd/legal` when the user asks a contract question. |
| `human_authority_layer` | The non-negotiable invariant of §5.1: the user always wins. Composed of v4.0 veto + consent + gates + (in Chimera) the per-pack `human_authority` block (§8.1). A pack MAY raise gates; it MUST NOT lower them. Mirrors RFC-002 §6 + RFC-006 §6. | **Carrier** (authoritative) | `final_decision_owner = "human_carrier"`; `raise_only: true`. |

### 0.1.1 What is NOT a pack and NOT a skill

- **Persona anchors / examples.** The five `examples/v4/personas/*.klickd` files and `student-multi-provider` are **persona anchors** (also referred to as "examples" or "v4-preview demo fixtures"). They are **neither** `carrier_pack`s **nor** `host_skill`s. They are inspiration material for pack authors. See §6 and [`examples/v4/personas/README.md`](../../examples/v4/personas/README.md).
- **Framework "skills" (ESCO / WEF / O\*NET vocabulary).** When ESCO or WEF call a competency a "skill" (their term), that is **external framework vocabulary** the pack *anchors against*. It is not a `host_skill`. To avoid the ambiguity, this RFC uses **"competency"** when referring to the framework-anchored item inside a pack, and **`host_skill`** only for host-side behaviour modules.

### 0.1.2 Forbidden ambiguous phrasings

When discussing a `.klickd` carrier artefact, the following phrases MUST NOT be used; pick the precise term instead.

| Forbidden phrase | Why ambiguous | Use instead |
|---|---|---|
| "skill file" (for a `.klickd` artefact) | Conflates host method with carrier state. | `carrier_pack` / `competency_pack` / `domain_pack` |
| "student skill" (for `x.klickd/student`) | Implies the pack carries teacher method. | `x.klickd/student` competency pack, or "the student pack"; the Socratic tutor is `skill.kai.tutor.socratic` (a `host_skill`). |
| "domain skill" (for `x.klickd/<domain>`) | Same conflation, domain-shaped. | `domain_pack` / `competency_pack` |
| "competency skill" | Tautology + conflation. | `competency_pack` (the artefact) or "competency anchor" (the framework reference inside). |
| "pack skill" | Self-contradictory under the carrier-vs-skill split. | `host_skill` (if host-side) or `competency_pack` (if carrier-side). |

These forbidden phrasings are **docs-only style rules**; they do not introduce new normative fields and they do not change any schema.

---

## 1. Motivation

Vince's review of the previous v4.1 attempt rejected two things explicitly:

1. **A too-narrow 6-pack MVP** that did not cover the actual user surface — every real user we have observed needs at minimum the `user` + `student` + `coding` triad, plus a research / security / legal stance, before any "professional" pack is even meaningful.
2. **A fake site catalog** — proposing `/klickdskill` downloads of the current `examples/v4/personas/*.klickd` files relabelled as "competency packs". Those files are personas/demos/fixtures (see [`examples/v4/personas/README.md`](../../examples/v4/personas/README.md), R4-P0-3). They are **not** competency packs. Publishing them as if they were would lock the format into a wrong taxonomy and would mislead third-party implementers (the exact failure mode [`DOMAIN_PROFILE_CATALOG.md`](../use-cases/DOMAIN_PROFILE_CATALOG.md) §0 warned about).

Chimera v4.1 is the corrected direction: a small, well-typed pack architecture, anchored on authoritative skill frameworks, with a P0 set that matches actual users and a P1 set that arrives only **after** the P0 set passes validation — and **never** a public catalog of demo personas mis-cast as packs.

The architecture is also the operational reading of three already-existing pieces of the v4 surface:

- **RFC-006 `agent_core`** — Chimera packs are the things an agent core *imports*.
- **RFC-007 `usage_profile` & in-session skill routing** — the same router that picks a `usage_profile` at first run is the one that activates / deactivates packs per turn.
- **RFC-003 §"Chimera.klickd v4.1 — forward-looking extrapolation"** — the context-cost projection that already names `Chimera.klickd v4.1` as the upper/lower bound study for `base + N packs` vs router-selected activation.

This RFC names that direction, fixes its P0/P1 scope, and pins the no-catalog rule.

## 2. v4.0 vs v4.1 — sharp boundary

| Layer | v4.0.0 GA | v4.1 Chimera |
|---|---|---|
| **What the file carries** | Portable persona / governance memory of *one human*: identity, memory, preferences, growth, accessibility, ethics, gates, human-veto, consent. | The v4.0 base **plus** up to seven competency packs (`x.klickd/<pack>`) declaring what the carrier can *do* in a domain. |
| **Ownership** | The person. | The person; each pack carries its own publisher provenance (org / community) and is verified independently. |
| **Normative core** | SPEC §33, schemas `klickd-payload-v4*.schema.json`. | This RFC; promotion path goes through `ACCEPTANCE_CHECKLIST_V4.md`. No schema in this RFC. |
| **Human authority** | User veto wins (RFC-002). | User veto **still** wins, over *every* pack default (§5.1). |
| **Failure mode if missed** | A model that ignores v4.0 still talks to "a generic user". Annoying, not unsafe. | A model that ignores v4.1 packs may attempt actions outside the carrier's declared competence — Chimera's gates exist to make that visible (§5.3). |

The boundary is intentional: **v4.0 is who you are; v4.1 is what you can do.** Reviewers should be able to point at any field in this RFC and answer "competence" — if the answer is "identity / memory / consent", the field belongs in v4.0, not here.

## 3. P0 packs — revised scope (six)

Per Vince's review, the v4.1 P0 set covers the **minimum surface a real user needs across personal, learning, professional, and safety vectors**, before any catalog discussion is meaningful:

| Pack id | Anchors competence in | Why P0 |
|---|---|---|
| `x.klickd/user` | The carrier as a *competent autonomous human* (literacy, numeracy, communication, basic digital, civic, transversal soft skills). | Every other pack composes on top of this. Maps to ESCO transversal skills + DigComp 2.2. |
| `x.klickd/student` | **Learner state**: identity, level, curriculum refs, subjects, competencies + mastery, preferences, accessibility, exam targets, history, gates, human authority. **NOT teacher skill** (see §5.1.1 carrier-vs-skill rule). Concrete spec: [`chimera/packs/student.md`](./chimera/packs/student.md). | Largest single user segment; anchor persona `01-eleve-terminale-fr` already validates the shape (anchor only — see §4 / §6). |
| `x.klickd/coding` | Software engineering competence: language fluency, code review discipline, test/typecheck rigour, security hygiene, supply-chain awareness. | Anchored by `03-fullstack-developer-en`; this is also the pack `.klickd` itself eats — Chimera must work for the people building it. |
| `x.klickd/research` | Evidence-handling competence: claim grounding, citation, replication, falsifiability, RFC-002 §8b verification artefact discipline. | The pack that disambiguates "the model said so" from "the carrier verified it"; required by RFC-003 §1.2. |
| `x.klickd/security` | Threat modelling, blast-radius reasoning, secrets hygiene, reversibility awareness, escalation defaults. | Cuts across every other P0 pack; declaring it as P0 prevents it from being "optional security" later. Maps to NICE + ENISA + CIS frameworks. |
| `x.klickd/legal` | Jurisdictional awareness (FR/LU/EU baseline), data protection (GDPR/AI-Act), licensing, professional secrecy gates, escalation to a human professional. | A v4.1 carrier without `legal` invariants will leak compliance — `legal` is therefore *constraint*, not feature. |

P0 is **six packs**, not five and not seven, by design — `security` and `legal` are *not* optional, they are part of the floor.

### 3.1 Why six and not the previous narrow set

The previous "6-pack MVP" Vince rejected lacked `security` and `legal` (or folded them into `user`) and over-indexed on professional-creator packs. That ordering let competence ship before constraint. The corrected P0 inverts the priority: constraints (`security`, `legal`) ship with `user` / `student` / `coding` / `research`; creator / work / gaming come **only** after validation (§4).

## 4. P1 fast-follow — five packs, *only after* P0 validation

P1 lands only when every P0 pack has passed the validation criteria of §6 and the no-catalog rule of §7 is still respected.

| Pack id | Anchors competence in | Persona anchor (inspiration only) |
|---|---|---|
| `x.klickd/work` | Professional / team competence: project management, stakeholder communication, deliverable discipline. | `02-chef-projet-pme-fr` |
| `x.klickd/creator` | Media production competence: editorial responsibility, source/rights handling, RFC-001 `media_profile` discipline. | `04-createur-media-fr` |
| `x.klickd/gaming` | Game competence: rule comprehension, opponent / NPC modelling, RFC-002 reversibility intuition (low-stakes proving ground). | `05-rpg-gamer-en` |
| `x.klickd/bridge` | Cross-provider / multi-provider competence: provider-neutral prompting, capability negotiation, fallback discipline. | `student-multi-provider` |
| `x.klickd/mission` | Mission / project-scoped competence: declaring objective, scope, deliverable, time-box, exit conditions. Distinct from `work` (mission ≠ job). | — (no current persona; first pack without a v4 anchor, intentionally) |

P1 is **five packs**, bringing the long-run total to 11. Together with `x.klickd/user` always-on, the **per-session active set is capped at seven** (see §5.4) regardless of how many packs a carrier owns.

## 5. Architecture

### 5.0 Clean-architecture invariant (normative intent) — *new in v4.1*

> **v4.1 packs are v4.1-native. There is no compatibility path from v4-preview personas to Chimera packs.**

Concretely:

1. A Chimera pack (`x.klickd/<pack>`) is a **new artefact** built from authoritative skill frameworks (ESCO / WEF / O\*NET / DigComp / EQF) via the SKOS/JSON-LD backbone (§5.7). Its fields are defined by this RFC and by the per-pack scaffolds under [`chimera/packs/`](./chimera/packs/), not by any prior persona shape.
2. **No legacy adapter.** The pack reader MUST NOT accept v4-preview persona blocks (`knowledge.mastered[]`, `mastered_topics[]`, free-text `subjects[].mastery`, narrative `level: "advanced"` strings, etc.) as substitutes for pack fields. A v4-preview persona that "looks like" a pack is still a persona; it is not loaded as a pack.
3. **No silent upgrade.** A v4.0 reader that encounters a `x.klickd/<pack>` block round-trips it verbatim (§5.6, SPEC §33.7). It does **not** synthesise pack state from v4.0 fields.
4. **Personas remain anchors.** The five `examples/v4/personas/*.klickd` files and `student-multi-provider` stay v4-preview anchors per §6 / [`examples/v4/personas/README.md`](../../examples/v4/personas/README.md). They are inspiration for what state a pack should carry; they are **not** transformed into packs.
5. **Reviewer rule.** Any PR that proposes "let `knowledge.mastered[]` from the persona populate `mastery[]` in the pack" — or any equivalent compatibility shim — MUST be rejected as a §8 validation failure (criteria #1, #9, and #10 fail together). A new `x.klickd/<pack>` is authored from frameworks; it is never harvested from a persona file.

The invariant exists because every prior agent-context attempt that allowed legacy adapters ended up with the adapter shape locking the canonical shape. v4.1 ships clean or not at all.

### 5.1 Human authority invariant (normative intent) — the `human_authority_layer`

> **The human always wins.** A `carrier_pack` MAY declare defaults (gates, tools, escalation). The user's v4.0 veto, consent, and gates — together the `human_authority_layer` (§0.1) — take precedence on every conflict. No pack can lower a user's gate; a pack MAY raise it. This invariant is non-negotiable and mirrors RFC-002 §6 + RFC-006 §6.

### 5.1.1 Carrier-vs-skill rule (normative intent) — *new in v4.1*

> **A pack describes what the *carrier* knows about itself, not what the *LLM* should do with the carrier.**
>
> A `.klickd v4.1` `competency_pack` carries **state, not behaviour**: who the carrier is in this domain, what they have demonstrated, what they consent to, what gates apply. The matching **`host_skill`** (how to *teach* a student, how to *review* code, how to *prosecute* a legal argument — names like `skill.kai.tutor.socratic`, `skill.coding.assistant`, `skill.research.assistant`) lives on the LLM / agent side, loaded by the host (Klickd, Kai, or any other runtime). Canonical vocabulary: §0.1.

The split is hard:

| Side | Carries | Owner | Example |
|---|---|---|---|
| **`carrier_pack` (`x.klickd/<name>`)** — `competency_pack` / `domain_pack` / `temporary_overlay` | Carrier state, history, mastery, preferences, consent, gates, accessibility, exam/role targets. | The carrier (user). | A 17-year-old student's level in maths, exam target, accommodations, the chapters they've covered. |
| **`host_skill` (host-side)** — `skill.<host>.<domain>.<method>` | Method, pedagogy, tone, prompting strategy, scoring rubric, intervention policy. | The Klickd/Kai LLM, or any other host. | `skill.kai.tutor.socratic` *uses* the student pack to ask the right next question; `skill.coding.assistant` consults `x.klickd/coding`; `skill.research.assistant` consults `x.klickd/research`. |

#### Why this rule exists

If a student pack carried the teacher skill, then:

1. Every student would walk around with a "how to teach me" payload that the LLM might over-trust ("the pack told me to teach this way"). That collapses pedagogy into the user's file and locks it out of update by the platform.
2. Teacher quality would be fixed at whatever the pack author shipped, with no way for Klickd/Kai to improve pedagogy without touching every user file.
3. The user could no longer take the same pack to a different agent (an exam-board tool, a parent-side dashboard, a different tutor) and have *that* agent apply its own appropriate skill on top of the same learner state. Portability dies.

#### Consequences

- **`x.klickd/student` carries learner state** — identity, level, curriculum refs, subjects, competencies/mastery, preferences, accessibility, exam targets, history, gates, human authority. See [`chimera/packs/student.md`](./chimera/packs/student.md).
- **The Socratic teacher/tutor `host_skill` is host-side** — Klickd/Kai's LLM side loads `skill.kai.tutor.socratic` (or any other tutor `host_skill`) and consults the student `competency_pack` to personalise. The `host_skill` is *not* in the pack. Other examples: `skill.coding.assistant` consults `x.klickd/coding`; `skill.research.assistant` consults `x.klickd/research`.
- **All P0/P1 `competency_pack`s follow the same rule.** `x.klickd/coding` carries developer state (languages, projects, code-review history, gates), NOT a "code review skill". `x.klickd/legal` carries jurisdictional state and consent posture, NOT a "legal reasoning skill". The matching method is always a `host_skill`.
- **Validation criterion §8.10 enforces it** (added to §8 below).
- **Composition rule (the `human_authority_layer` always wins):** `host_skill` constrains *how to act*, `agent_core` (RFC-006) constrains *operating context*, `carrier_pack` declares *carrier state*, `user.klickd` (v4.0) *personalises*. Four layers, no overlap. See §0.1 for the canonical vocabulary.

### 5.2 Base transversal core — `base_transversal_core`

A `.klickd v4.1` file always carries a **`base_transversal_core`** (§0.1) on top of v4.0: the small set of cross-pack competencies (literacy, numeracy, communication, basic digital, RFC-002-style gate reasoning, RFC-001 media-handling awareness). The `base_transversal_core` is implicit in `x.klickd/user` and is loaded even when no other `carrier_pack` is active. Other `competency_pack`s MAY refine the `base_transversal_core`; they MUST NOT shadow it silently.

### 5.3 Up to seven packs active per session

A session's effective context = v4.0 base + base transversal core + **up to seven** active packs. Loading more than seven SHOULD trigger an explicit router decision (§5.5), not a silent truncation. Seven is a cost ceiling (see RFC-003 §"Chimera.klickd v4.1 — forward-looking extrapolation": `base_plus_seven` is the upper bound) and an attention ceiling.

### 5.4 Temporary overlays — `temporary_overlay`

A `carrier_pack` MAY be loaded as a **`temporary_overlay`** (§0.1) — a single turn, a single artefact, a single project — without becoming part of the carrier's persistent active set. A `temporary_overlay`:

- expire deterministically (turn / time / artefact boundary, declared at load),
- never write back to the v4.0 memory unless the user explicitly accepts the write,
- count against the seven-pack ceiling **while active**.

Overlays exist so that "I need legal context for this one document" does not require permanently adopting `x.klickd/legal`.

### 5.5 Decision router — `decision_router`

The **`decision_router`** (§0.1) is the same conceptual component as RFC-007 §"in-session skill routing":

- at first run, the router picks an initial active set from the carrier's declared `usage_profile`,
- per turn, the router MAY swap packs in/out based on the user's prompt, the agent core's policy, and the seven-pack ceiling,
- every swap is logged as a decision (RFC-003 `decisions[]`-shaped record), so the carrier can audit "why was `legal` active when I asked X".

The `decision_router` is **advisory**, not coercive: the `human_authority_layer` (§5.1) lets the user pin or veto a pack at any time.

### 5.6 Extended structured memory

v4.0's `memory[]` is one ordered list. v4.1 extends it (additively, no rewrite) with **pack-scoped memory slices** — a pack MAY append to its own slice without touching the user's main memory. The user's main memory remains the single source of truth for identity and consent; pack slices are competence trace, not persona.

- A pack slice MUST be addressable as `memory.x_klickd.<pack>` (illustrative only — no schema in this RFC).
- A reader that does not understand pack slices MUST preserve them verbatim on round-trip (SPEC §33.7 already covers this).

### 5.7 ESCO / WEF / O\*NET + SKOS/JSON-LD offline backbone

Pack competencies are anchored to **authoritative skill frameworks**, not to a homegrown Klickd taxonomy (the failure mode `DOMAIN_PROFILE_CATALOG.md` §0 named):

- ESCO (EU) — primary occupational / skill backbone, multilingual, public licence.
- WEF Future of Jobs taxonomy — transversal / "future skills" layer.
- O\*NET (US) — cross-check for occupational depth where ESCO is sparse.
- SKOS / JSON-LD — the wire shape: each competency carries a `skos:Concept`-shaped reference with `inScheme` (which framework), `prefLabel`, and a stable IRI.

The backbone is **offline-capable**: a pack ships with the SKOS/JSON-LD subset it references, so a carrier that opens the file on an air-gapped machine sees full labels and definitions without a network call. This is also the constraint that keeps packs auditable: every claim about competence resolves to an external, dated framework reference.

## 6. Persona anchors (inspiration only, NOT `competency_pack`s and NOT `host_skill`s)

The five `examples/v4/personas/*.klickd` files and the `student-multi-provider` walkthrough exist as v4-preview **persona anchors / demo fixtures / examples** (§0.1.1). They are **neither** `carrier_pack`s **nor** `host_skill`s. They are the right input to design `competency_pack`s against, and they are the wrong artefact to publish *as* `competency_pack`s. The mapping is:

| Current v4 persona (anchor only) | Future Chimera pack (this RFC) | Track |
|---|---|---|
| `01-eleve-terminale-fr` | `x.klickd/student` | P0 |
| `02-chef-projet-pme-fr` | `x.klickd/work` | P1 |
| `03-fullstack-developer-en` | `x.klickd/coding` | P0 |
| `04-createur-media-fr` | `x.klickd/creator` | P1 |
| `05-rpg-gamer-en` | `x.klickd/gaming` | P1 |
| `student-multi-provider` (demo walkthrough) | `x.klickd/bridge` | P1 |

**Normative intent:** these personas MUST NOT be renamed, repackaged, or republished as `x.klickd/*` competency packs. They remain non-normative v4-preview examples per [`examples/v4/personas/README.md`](../../examples/v4/personas/README.md). When a real pack ships, it MUST be a new artefact derived from authoritative frameworks (§5.7), not a relabelled persona.

Per §5.0 (clean-architecture invariant), the personas are also **not** a compatibility input. No field, key, or value from a `examples/v4/personas/*.klickd` file is loaded into a pack at runtime. The persona may be **read as a design reference** by a pack author, but the pack itself is authored against frameworks. There is no `persona → pack` migration tool, no `mastered_topics` adapter, and no implicit promotion of persona narrative into pack fields.

## 7. No-catalog rule

> **Until a real Chimera pack passes validation (§8), `/klickdskill` MUST NOT expose any "competency pack" catalog, listing, or download surface.**

Concretely:

- Current files under `examples/v4/personas/`, `examples/v4/student-walkthrough/`, `examples/`, and `registry/competencies/` are **not** competency packs and MUST NOT be re-served as such.
- Any future catalog surface (web index, API endpoint, registry entry) is **out of scope until P0 validation passes**.
- A pack is "real" only after it satisfies the validation criteria of §8 — relabelling, prettifying, or aggregating existing v4 fixtures does not satisfy those criteria.
- No `latest` / `next` channel, no DOI, no IANA action, no npm / PyPI release of a "klickdskill" pack bundle is permitted under this RFC.

The no-catalog rule exists because shipping a fake catalog locks the taxonomy before reviewers can audit it — exactly the surface-creep failure `DOMAIN_PROFILE_CATALOG.md` §0 warned about.

## 8. Validation criteria (pre-promotion)

A pack is **not** ready for catalog exposure (§7) until **all** of the following are satisfied. The criteria are docs-only and intentionally framework-anchored; they do not introduce new schema.

1. **Framework anchor.** Every competency in the pack resolves to a SKOS/JSON-LD reference into ESCO, WEF, or O\*NET (§5.7). No homegrown competency without an external anchor.
2. **Gates declared.** Every action the pack enables declares its RFC-002 `verification_gates` defaults and `human_veto_policy` posture. No silently bypassable action.
3. **Evidence rules.** Every claim the pack lets the agent emit declares its grounding rule (RFC-002 §8b claim grounding, RFC-003 `verification_artifacts[]` shape). Packs that emit unsourced claims fail validation.
4. **No PII.** A pack file is publisher-owned, not user-owned. It MUST NOT contain user PII, user memory, user sessions, or user consent (mirrors RFC-006 §6).
5. **Round-trip safe.** A v4.0-only reader that ignores the pack MUST preserve it verbatim on round-trip and MUST NOT degrade v4.0 behaviour.
6. **Offline-resolvable.** The pack ships its SKOS/JSON-LD subset; opening it on an air-gapped machine yields full labels and definitions (§5.7).
7. **Router-priceable.** The pack publishes a deterministic token-cost estimate consistent with RFC-003's `chimera_v41_extrapolation()` shape, so router activation can be reasoned about.
8. **Human-authority preserved.** No pack default lowers a user's v4.0 gate (§5.1). Static review of the pack MUST verify this.
9. **No persona reuse / no legacy adapter (§5.0).** The pack is not a renamed `examples/v4/personas/*` file (§6) and does **not** accept persona-shaped legacy keys (`knowledge.mastered[]`, `mastered_topics[]`, narrative `level` strings, etc.) as substitutes for pack fields. A pack's `mastery[]` is populated from framework-anchored evidence, not harvested from a persona block.
10. **Carrier-vs-skill separation (§5.1.1).** The pack contains **state, not behaviour**. It MUST NOT carry method, pedagogy, prompting strategy, tone rules, scoring rubrics, or intervention policy. Any "skill" the agent applies on top of the pack lives on the host side (Klickd/Kai skill, agent core, or external skill registry). Static review verifies the pack declares no instructions that read like *"teach the user by …"*, *"review the user's code by …"*, *"prosecute the case by …"*.

A pack passing all **ten** is **eligible** for promotion to a real `x.klickd/<pack>` artefact via a future RFC + checklist gate. Passing validation does **not** trigger catalog exposure (§7); catalog exposure is its own decision.

### 8.1 v4.1-native shape (validation table, NOT a JSON Schema)

A "true" Chimera pack is v4.1-native: every required field below is present, framework-anchored where applicable, and free of legacy persona-shaped keys. This table is the **validation contract** reviewers run against a candidate pack. It is **not** a JSON Schema (no `additionalProperties`, no `$id`, no `$schema`); a real schema lands only if and when the RFC promotes past `Proposed`.

| Field (top-level) | Type | Required | Source | v4.1-native rule |
|---|---|---|---|---|
| `pack` | string | **yes** | author | MUST equal `x.klickd/<name>` where `<name>` is a P0/P1 id (§3, §4). Free-form names rejected. |
| `pack_version` | semver string | **yes** | author | SemVer. Pre-release tag `-draft` allowed before validation passes. No release artefact implied (§7). |
| `spec_ref` | path/URL | **yes** | author | Points at the pack's canonical scaffold under `docs/rfcs/chimera/packs/<name>.md`. |
| `publisher` | object `{name, ref}` | **yes** | author | Publisher is **not** the carrier. No PII (§8.4). |
| `frameworks[]` | array of `{scheme, version, iri_prefix}` | **yes** | author | Declares which authoritative frameworks the pack anchors to (ESCO / WEF / O\*NET / DigComp / EQF). MUST be non-empty. |
| `competencies[]` | array of `{competency_ref, prefLabel, scheme}` | **yes** | author | Each `competency_ref` MUST be a stable IRI in a declared `frameworks[]` scheme. No homegrown competency. |
| `mastery[]` | array of `{competency_ref, mastery_level, scale_ref, evidence_refs[], assessed_at, assessed_by_ref}` | optional (carrier state) | carrier | If present, every entry MUST reference a `competencies[]` IRI and a `scale_ref` (DigComp / EQF / Bloom / declared rubric). Pointer-only `evidence_refs[]`. **No** persona-shaped `mastered: true` / `mastered_topics: [...]` accepted. |
| `levels[]` | array of `{framework_ref, level_label, effective_at}` | **yes** for student/work/coding/research/security/legal | carrier | `level_label` MUST be a value from the cited framework (e.g. `EQF level 4`), not a free-text narrative ("advanced", "expert"). |
| `gates` | object (RFC-002 shape) | **yes** | author + carrier | Declares `verification_gates_default` and `human_veto_policy`. `raise_only: true` MUST hold against the carrier's v4.0 gates (§5.1, §8.8). |
| `human_authority` | object `{final_decision_owner, agent_role, escalation}` | **yes** | author | `final_decision_owner ∈ {human_carrier, human_carrier_with_guardian}`, `agent_role = "advisory"`. |
| `memory_scope` | string | **yes** | author | MUST equal `memory.x_klickd.<name>` (pack-scoped slice; §5.6). MUST NOT alias `memory[]` (the v4.0 main memory). |
| `evidence_policy` | object `{required_for_claims, pointer_only, attestation_shape_ref}` | **yes** | author | Mirrors RFC-002 §8b. `pointer_only: true` is the v4.1 default (no inline copies of student work). |
| `source_policy` | object `{frameworks_offline_bundle, allow_inline_definitions, language_tags[]}` | **yes** | author | Names the SKOS/JSON-LD subset shipped offline (§5.7, §8.6). |
| `router_cost` | object `{tokens_estimate, baseline, source_row}` | **yes** | author | Deterministic token-cost estimate consistent with RFC-003 `chimera_v41_extrapolation()`. Pack without a `router_cost` row fails §8.7. |
| `forbidden_fields` | array (literal, frozen) | **yes** | author | MUST literally include `["pedagogy", "teaching_method", "socratic_steps", "prompt_strategy", "scoring_rubric", "intervention_policy", "tone_rules", "system_prompt_overrides", "knowledge.mastered", "mastered_topics"]`. Used by the §8.10 / §5.1.1 static check and the §5.0 no-legacy-adapter check. |

Notes:

- A pack file containing any key listed in `forbidden_fields` fails validation immediately (carrier-vs-skill + clean-architecture). This is the static check §8.10 performs.
- Fields not in the table above are **out of scope for v4.1-native validation**. Reviewers MUST NOT accept "but we also need field X for legacy reasons" — see §5.0.
- This table is a **contract, not a schema.** A strict JSON Schema arrives only post-Proposed. Until then, validation is reviewer-driven against this table and against the per-pack scaffold (e.g. [`chimera/packs/student.md`](./chimera/packs/student.md) §6).

## 9. Composition with existing RFCs

| Existing RFC | Relation to Chimera v4.1 |
|---|---|
| RFC-001 (`media_profile`) | A pack MAY refine `media_profile` defaults (e.g. `x.klickd/creator`). The pack's defaults compose under user veto (RFC-002). |
| RFC-002 (`verification_gates`, `human_veto_policy`) | Foundation. Every pack declares gate defaults; user veto wins. |
| RFC-003 (Context Cost Benchmark) | Chimera is the operational reading of `chimera_v41_extrapolation()`. The seven-pack ceiling (§5.3) matches `base_plus_seven`. |
| RFC-004 (Migration) | A v4.0 → v4.1 migration is additive (`memory.x_klickd.*` and pack manifest fields are new keys); no break to v4.0 readers. |
| RFC-006 (`agent_core`) | An agent core MAY import packs. Composition rule (`core` constrains, `pack` declares competence, `user` personalises) extends `DOMAIN_PROFILE_CATALOG.md` §1.1. |
| RFC-007 (`usage_profile` & skill routing) | The router (§5.5) is the same component RFC-007 sketches; Chimera names its pack-aware behaviour. |
| RFC-008 (`core_update_watch`) | Pack updates follow the same "veille → propose → user accepts" pattern; pack updates MUST NOT touch user memory (§5.6). |

## 10. Out of scope (v1 of this RFC)

- Concrete JSON Schema for `x.klickd/<pack>` files. Strict schema arrives only if and when the RFC promotes past `Proposed`. A first **shape sketch** (illustrative, not a schema) ships with the concrete pack at [`chimera/packs/student.md`](./chimera/packs/student.md).
- The wire format of a `pack_manifest` block. Sketched conceptually here; normalised in a future RFC.
- Catalog UX, discovery, marketplace, ratings, signing key infrastructure. (See §7 no-catalog.)
- Concrete ESCO / WEF / O\*NET subset bundles per pack. Listed as a validation criterion (§8), not shipped here.
- Any change to `v4.0.0` GA. v4.1 is strictly post-GA.

## 11. Open decisions

> Listed explicitly so reviewers can spot accidental assumptions (per `docs/rfcs/README.md` §"How to write one" #4).

1. **`x.klickd/` namespace literal.** Is `x.` the right prefix (mirrors RFC IETF "experimental" convention), or should packs live under `pack.klickd/<name>` to mirror `core.<agent>.klickd` from RFC-006? Current draft: `x.klickd/<pack>`; open to either.
2. **`mission` as P1, not P0.** `x.klickd/mission` is the first pack without a persona anchor. Should it move to P0 to make "scoped session" a first-class primitive? Current draft: keep P1, on the grounds that mission semantics ride on top of `user` + `work` competence.
3. **Seven-pack ceiling.** Seven matches RFC-003's `base_plus_seven` cost study. Reviewers may prefer four or five if router-cost data argues for tighter activation; revisit after the first real benchmark run.
4. **Offline SKOS/JSON-LD bundling.** Shipping the SKOS subset with each pack is auditable but duplicates label data across packs. A shared `frameworks/` registry might be cleaner; deferred.
5. **Validation §8 owners.** Who runs the validation? Current draft: author + one independent reviewer per pack, mirroring `ACCEPTANCE_CHECKLIST_V4.md`. Open to a stricter rule.
6. **Relation to `DOMAIN_PROFILE_CATALOG.md`.** That doc lists *domains*; this RFC lists *packs*. Should the next iteration of the catalog be rewritten in pack terms, or kept as a separate "domain seed list"? Current draft: keep separate until P0 validation passes.

## 12. Status & next steps

This RFC is **Draft**. It is **docs-only**. It does not change any current normative surface, schema, SDK, vector, or release artefact. Promotion to `Proposed` follows `ACCEPTANCE_CHECKLIST_V4.md`. Promotion to `Accepted` requires (at minimum) the open decisions of §11 to be resolved and one P0 pack draft to exist as a worked example demonstrating §8 is achievable.

**Worked-example pack (concrete scaffold, ships with this RFC):** [`docs/rfcs/chimera/packs/student.md`](./chimera/packs/student.md) — `x.klickd/student`. Demonstrates the carrier-vs-skill rule (§5.1.1) by carrying learner state only; the Socratic tutor skill lives host-side.

**Companion docs:**

- [`docs/rfcs/chimera/README.md`](./chimera/README.md) — pack scope table and validation criteria summary.
- [`docs/rfcs/chimera/packs/README.md`](./chimera/packs/README.md) — concrete pack index, `/klickdskill` later-notes, no-fake-catalog reminder.
- [`docs/rfcs/chimera/frameworks/README.md`](./chimera/frameworks/README.md) — canonical framework registry (ESCO v1.1.1, DigComp 2.2, LifeComp 2020, EQF 2017, CEFR 2020, WEF, O\*NET, NICE, ENISA, CIS, SFIA) with stable URLs / IRI prefixes / distribution URLs / SHA-256 placeholders, plus the offline SKOS/JSON-LD bundle shape.
- [`docs/rfcs/chimera/schema-fragments/README.md`](./chimera/schema-fragments/README.md) — schema-intent fragments (NOT a JSON Schema) for the pack manifest, `base_transversal_core`, `competencies`, `mastery`, `levels`, `language_proficiency`, `evidence_policy`, `source_policy`, `gates`, `human_authority`, structured memory, `router_cost`, `forbidden_fields`.
- [`docs/rfcs/chimera/packs/router_cost.md`](./chimera/packs/router_cost.md) — deterministic heuristic token-cost rows for `x.klickd/user` and `x.klickd/student`, compatible with RFC-003 `chimera_v41_extrapolation()`.
