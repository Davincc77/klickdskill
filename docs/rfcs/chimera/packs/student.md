# `x.klickd/student` — concrete `competency_pack` scaffold

| | |
|---|---|
| **`carrier_pack` id** | `x.klickd/student` |
| **Taxonomy class** | `competency_pack` / `domain_pack` (carrier-side); see [RFC-009 §0.1](../../RFC-009-chimera-v4.1.md) |
| **Track** | `.klickd v4.1` — Chimera P0 (see [RFC-009](../../RFC-009-chimera-v4.1.md)) |
| **Status** | **Draft scaffold** · NON-NORMATIVE · shape sketch (no JSON Schema yet) |
| **Carrier** | A learner (typically a human student; equally usable for any self-directed learner) |
| **Persona anchor** | `examples/v4/personas/01-eleve-terminale-fr.klickd` — *example / inspiration only, NEITHER a `competency_pack` NOR a `host_skill`* |
| **Companion `host_skill`** | `skill.kai.tutor.socratic` (loaded by Klickd / Kai LLM as a `host_skill`, NOT in the pack) |
| **Created** | 2026-05-26 |
| **Triggers no release** | No schema, no SDK, no tag, no `latest` on npm/PyPI, **no Zenodo DOI**, no IANA action. |

> This is the **first concrete `competency_pack` scaffold** under v4.1 Chimera. It demonstrates the carrier-vs-skill rule of [RFC-009 §5.1.1](../../RFC-009-chimera-v4.1.md): a `carrier_pack` carries the **learner's state**, never the teacher's method (which lives in a `host_skill`).

---

## 0. The two rules

> **Rule 1 — carrier-vs-skill.** `x.klickd/student` is a `competency_pack` that carries learner state. It does NOT carry teacher method. The Socratic teacher / tutor method is loaded by the **Klickd / Kai LLM** side (or any other host) as a `host_skill` named `skill.kai.tutor.socratic` — not by the pack. The `competency_pack` is what the LLM *consults*; the `host_skill` is what the LLM *applies*. Enforced by [RFC-009 §5.1.1](../../RFC-009-chimera-v4.1.md) + §8.10. Canonical vocabulary: [RFC-009 §0.1](../../RFC-009-chimera-v4.1.md).
>
> **Rule 2 — v4.1-native, no legacy adapter.** This pack is built from authoritative frameworks (ESCO / DigComp / EQF, optionally O\*NET / WEF) under the SKOS/JSON-LD backbone of RFC-009 §5.7. It does **not** accept v4-preview persona fields (`knowledge.mastered[]`, `mastered_topics[]`, free-text `subjects[].mastery`, narrative `level: "advanced"` strings) as input. The persona `01-eleve-terminale-fr.klickd` is a **design anchor**, not a compatibility source. Enforced by [RFC-009 §5.0](../../RFC-009-chimera-v4.1.md) + §8.9.

If you find yourself writing `"pedagogy"`, `"how_to_teach"`, `"socratic_steps"`, `"prompt_strategy"`, `"intervention_policy"`, or `"tone_rules"` inside this pack — stop. That belongs in the host skill (Rule 1).

If you find yourself writing `"knowledge.mastered[]"`, `"mastered_topics"`, or harvesting fields from a v4-preview persona — stop. The pack is authored from frameworks, not from personas (Rule 2).

## 1. Why a concrete scaffold

[Letta `.af`](https://docs.letta.com/) and every prior "agent context format" diverged because the spec shipped without at least one **concrete, well-typed example** of the artefact. v4.1 Chimera ships with `x.klickd/student` as the worked example: it pins the shape, exercises the carrier-vs-skill rule, and gives `klickd.app` something it can actually import / round-trip without inventing fields.

## 2. What the pack carries (state, not skill)

Twelve sections. All are **carrier state**. None are teacher behaviour. All competency / level references are framework-anchored (§2.0).

### 2.0 `base_transversal_core` (mandatory, v4.1-native)

Every Chimera `carrier_pack` — `student` included — carries the **`base_transversal_core`** (canonical term, see [RFC-009 §0.1](../../RFC-009-chimera-v4.1.md)): a small cross-pack competency layer composed only of framework-anchored references. The `base_transversal_core` is what survives even when no other pack is active (RFC-009 §5.2).

For `x.klickd/student`, the base anchors are pinned to the canonical Chimera framework registry — see [`../frameworks/README.md`](../frameworks/README.md) §1 and §2.1 for the per-scheme stable URLs and the full `base_transversal_core` default set:

- **ESCO v1.1.1 transversal skills** — IRI prefix `http://data.europa.eu/esco/skill/`, canonical URL `https://esco.ec.europa.eu/en`, distribution `https://esco.ec.europa.eu/en/use-esco/download`. Covers communication, literacy, numeracy, problem solving, planning (anchors include `esco:S1.0.0` "Communication, collaboration and creativity", `esco:S2.0.0` "Information skills", `esco:S5.0.0` "Working with computers").
- **DigComp 2.2** — IRI prefix `https://joint-research-centre.ec.europa.eu/digcomp/2.2/`, canonical URL `https://joint-research-centre.ec.europa.eu/digcomp_en`, distribution `https://publications.jrc.ec.europa.eu/repository/handle/JRC128415`. 5 areas × 21 competences (`digcomp:1.1` .. `digcomp:5.4`).
- **LifeComp 2020** — IRI prefix `https://joint-research-centre.ec.europa.eu/lifecomp/2020/`, canonical URL `https://joint-research-centre.ec.europa.eu/lifecomp_en`, distribution `https://publications.jrc.ec.europa.eu/repository/handle/JRC120911`. Personal / Social / Learning-to-learn (`lifecomp:P1`, `lifecomp:L1`, `lifecomp:L2`).
- **EQF 2017 (current consolidated)** — IRI prefix `https://europa.eu/europass/eqf/`, canonical URL `https://europa.eu/europass/en/europass-tools/european-qualifications-framework`, level descriptors at `https://europa.eu/europass/en/description-eight-eqf-levels`. Used for `level.level_label` resolution.
- **CEFR Companion Volume 2020** — canonical URL `https://www.coe.int/en/web/common-european-framework-reference-languages`, distribution `https://rm.coe.int/common-european-framework-of-reference-for-languages-learning-teaching/16809ea0d4`. Used by `language_proficiency[]` (separate from EQF qualification level).

Wire-shape (illustrative; mirrors [`../frameworks/README.md`](../frameworks/README.md) §2.1):

```jsonc
"base_transversal_core": {
  "frameworks": [
    {
      "scheme": "esco",
      "version": "v1.1.1",
      "iri_prefix": "http://data.europa.eu/esco/skill/",
      "canonical_url": "https://esco.ec.europa.eu/en/classification/skill_main",
      "distribution_url": "https://esco.ec.europa.eu/en/use-esco/download",
      "distribution_sha256": "TBD-at-bundle-generation"
    },
    {
      "scheme": "digcomp",
      "version": "2.2",
      "iri_prefix": "https://joint-research-centre.ec.europa.eu/digcomp/2.2/",
      "canonical_url": "https://joint-research-centre.ec.europa.eu/digcomp_en",
      "distribution_url": "https://publications.jrc.ec.europa.eu/repository/handle/JRC128415",
      "distribution_sha256": "TBD-at-bundle-generation"
    },
    {
      "scheme": "lifecomp",
      "version": "2020",
      "iri_prefix": "https://joint-research-centre.ec.europa.eu/lifecomp/2020/",
      "canonical_url": "https://joint-research-centre.ec.europa.eu/lifecomp_en",
      "distribution_url": "https://publications.jrc.ec.europa.eu/repository/handle/JRC120911",
      "distribution_sha256": "TBD-at-bundle-generation"
    },
    {
      "scheme": "eqf",
      "version": "2017",
      "iri_prefix": "https://europa.eu/europass/eqf/",
      "canonical_url": "https://europa.eu/europass/en/europass-tools/european-qualifications-framework",
      "distribution_url": "https://europa.eu/europass/en/description-eight-eqf-levels",
      "distribution_sha256": "TBD-at-bundle-generation"
    }
  ],
  "transversal_refs": [
    { "competency_ref": "esco:S1.0.0",  "scheme": "esco",     "prefLabel": "Communication, collaboration and creativity" },
    { "competency_ref": "esco:S2.0.0",  "scheme": "esco",     "prefLabel": "Information skills" },
    { "competency_ref": "esco:S5.0.0",  "scheme": "esco",     "prefLabel": "Working with computers" },
    { "competency_ref": "digcomp:1.1",  "scheme": "digcomp",  "prefLabel": "Browsing, searching, filtering data, information and digital content" },
    { "competency_ref": "digcomp:1.2",  "scheme": "digcomp",  "prefLabel": "Evaluating data, information and digital content" },
    { "competency_ref": "lifecomp:L1",  "scheme": "lifecomp", "prefLabel": "Growth mindset" },
    { "competency_ref": "lifecomp:L2",  "scheme": "lifecomp", "prefLabel": "Critical thinking" },
    { "competency_ref": "lifecomp:L3",  "scheme": "lifecomp", "prefLabel": "Managing learning" }
  ]
}
```

The IRIs above are **stable framework IDs**, not invented surrogates. `S1.0.0`, `S2.0.0`, `S5.0.0` are the top-level ESCO skill-pillar codes; `digcomp:1.1`, `digcomp:1.2` are the actual DigComp 2.2 competence codes; `lifecomp:L1..L3` are the published LifeComp 2020 Learning-to-learn codes. `distribution_sha256` is the literal placeholder `"TBD-at-bundle-generation"` because no offline bundle ships under this RFC (only the shape; see [`../frameworks/README.md`](../frameworks/README.md) §1.1).

The base is **not** harvested from a persona's narrative description; it is declared against frameworks. A pack with an empty `base_transversal_core` fails RFC-009 §8.1 (top-level `frameworks[]` required).

### 2.1 `identity`
Minimal identification *within* the learning context, **distinct** from v4.0 `user.klickd` identity (which carries the human's identity). A pack `identity` is the role-shaped sub-identity (e.g. "Terminale S student, Lycée X, session 2026").

- `pack_role` — e.g. `"student"`.
- `display_name` — non-PII handle, optional.
- `school_or_institution_ref` — optional, opaque institution reference.
- `enrolment_period` — e.g. `"2025-2026"`.

### 2.2 `level` (and `language_proficiency[]`)
Where the carrier is, *measured against an external framework* (never homegrown).

- `framework_ref` — stable IRI in a declared `frameworks[]` scheme; for qualification level this is typically EQF (`https://europa.eu/europass/eqf/` prefix), with the level descriptor at `https://europa.eu/europass/en/description-eight-eqf-levels`.
- `level_label` — a value from the cited framework. EQF levels are the closed set `"EQF level 1"` .. `"EQF level 8"`. National-framework equivalents (`"Terminale (FR)"`, `"Year 13 (UK)"`) are accepted only if the cited `framework_ref` is a national qualifications framework registered against EQF.
- `effective_at` — ISO-8601 date the level was last assessed.

Language proficiency is **separate** from qualification level and is anchored to CEFR (`https://www.coe.int/en/web/common-european-framework-reference-languages`, Companion Volume 2020). A learner may be EQF-4 with French C2 and English B2 simultaneously. See [`../schema-fragments/README.md`](../schema-fragments/README.md) §7 (`language_proficiency_array`).

### 2.3 `curriculum_refs[]`
References to the external curriculum the carrier is following. **Refs, not copies.**

- `curriculum_id` — stable IRI (e.g. `eduscol.fr/programmes/...`, `cambridge.org/...`).
- `jurisdiction` — e.g. `"FR-LU"`, `"EU"`, `"UK"`.
- `track` — e.g. `"baccalaureat-general-spe-mathematiques"`.
- `as_of` — version date.

### 2.4 `subjects[]`
The subjects the carrier is studying *now*. One entry per subject.

- `subject_ref` — ESCO / curriculum IRI.
- `prefLabel` — human-readable.
- `started_at`, `current_chapter_ref` (optional), `coursework_pointer` (optional).

### 2.5 `competencies[]` and `mastery[]`
The **competency anchors** (from §5.7 of RFC-009 — ESCO / WEF / O\*NET via SKOS/JSON-LD) and the carrier's measured mastery against each.

`competencies[].entry`:
- `competency_ref` — SKOS `inScheme` + IRI.
- `prefLabel` — multilingual ok.
- `acquired_at` (optional).

`mastery[].entry`:
- `competency_ref` — matches a `competencies[]` entry.
- `mastery_level` — small ordinal scale (e.g. `0..4`) **with an explicit `scale_ref`** declaring which rubric is in use (DigComp / EQF / Bloom / local).
- `evidence_refs[]` — pointers to artefacts (assignments, tests) that justify the level. **Pointers, not copies.**
- `assessed_at`, `assessed_by_ref` (teacher, self, peer, agent — discriminated).

### 2.6 `preferences`
Learning preferences as **carrier-declared facts**, not teacher instructions.

- `preferred_languages[]` — IETF language tags.
- `pace_preference` — e.g. `"slow_with_examples"` (a carrier label, not an instruction).
- `modality_preference[]` — e.g. `["text", "diagram"]`.
- `feedback_cadence_preference` — e.g. `"after_each_exercise"`.
- `time_budget_per_week_minutes` (optional).

> A host skill MAY interpret these preferences when choosing pedagogy. The pack just *states* them.

### 2.7 `accessibility`
The carrier's accessibility needs and accommodations. **Carrier-owned, never host-generated.**

- `needs[]` — e.g. `"dyslexia"`, `"low_vision"`, `"adhd"`, `"hearing_impairment"`.
- `accommodations[]` — official accommodations granted (e.g. `"tier_amenage_30pc"`, `"reader_software"`).
- `consent_to_disclose_to_agent` — boolean, `false` by default.

If `consent_to_disclose_to_agent` is `false`, the `host_skill` MUST treat `accessibility` as **gated** (not injectable into the prompt verbatim).

### 2.8 `exam_targets[]`
What the carrier is preparing for.

- `exam_ref` — IRI / canonical id (`bac-2026-mathematiques-fr`, `igcse-2026-physics`, …).
- `target_date`, `target_grade` (optional), `mock_history[]` (optional pointers to past results).
- `consent_to_share_grade` — boolean, default `false`.

### 2.9 `history[]`
A short, append-only trace of learning events. **Pack-scoped memory slice** (RFC-009 §5.6 — `memory.x_klickd.student`). Not the user's main `memory[]`.

- Entry: `{ at, kind, ref, mastery_delta?, agent_ref? }` where `kind` is one of `chapter_completed | exercise_completed | mock_taken | feedback_received | self_reflection`.
- Length is bounded by the carrier's compaction policy (RFC-005 placeholder); old entries roll up into mastery, not memory creep.

### 2.10 `gates`
Pack-default `verification_gates` (RFC-002 v1) and `human_veto_policy` for student-side actions.

- Defaults SHOULD set: high reversibility threshold for actions affecting `mastery[]` writes by an agent; require human veto on `consent_to_share_grade` becoming `true`; require artefact attestation (RFC-002 §8b) for any claim that the student "has mastered" a competency.
- Gates here MAY only **raise** the user's v4.0 gates, never lower them (RFC-009 §5.1).

### 2.11 `human_authority`
The pack-local restatement of the `human_authority_layer` ([RFC-009 §0.1, §5.1](../../RFC-009-chimera-v4.1.md)).

- `final_decision_owner` — MUST be `"human_carrier"` (or `"human_carrier_with_guardian"` for minors).
- `agent_role` — fixed value `"advisory"`. An agent MAY suggest pedagogy, NEVER decide enrolment, accommodations, or exam-target changes.
- `escalation` — for a minor, defaults to `"guardian_then_school"`.

## 3. What the pack does NOT carry

### 3.1 Forbidden host-side fields (Rule 1)

Explicitly **not** in this `competency_pack`. These belong host-side (in a `host_skill` or `agent_core`).

| Forbidden in pack | Lives where | Why |
|---|---|---|
| `pedagogy`, `teaching_method`, `socratic_steps`, `lesson_plan_template` | `skill.kai.tutor.socratic` (a `host_skill`) | Method changes faster than student state; portability requires the student carry only their own state. |
| `prompt_strategy`, `system_prompt_overrides` | `host_skill` or `agent_core` (RFC-006) | Prompting is host policy, not user state. |
| `scoring_rubric`, `grading_curve` | `host_skill` or external rubric ref | A pack can *cite* a rubric (`scale_ref`), never *define* one. |
| `intervention_policy`, `when_to_correct`, `when_to_praise` | `host_skill` | Behaviour belongs with the actor; the pack is not an actor. |
| `tone_rules`, `persona_voice` | `agent_core` (RFC-006) | Already the agent core's job. |
| Hidden curriculum claims, predictive grades | nowhere (not allowed) | Predictions about the student must be agent-emitted with RFC-002 §8b grounding, not pack-asserted. |

### 3.2 Forbidden legacy / persona fields (Rule 2 — v4.1-native, RFC-009 §5.0)

Also explicitly **not** in this pack. These are v4-preview persona shapes; v4.1 packs do not accept them as input or alias.

| Forbidden legacy key | Why rejected | What replaces it (v4.1-native) |
|---|---|---|
| `knowledge.mastered[]` (persona-style "I have mastered topic X") | Not framework-anchored; cannot resolve to an external IRI. | `mastery[]` entries each with `competency_ref` into ESCO / DigComp + `scale_ref` + `evidence_refs[]`. |
| `mastered_topics: ["..."]` (free-string array) | Same as above; loses provenance and scale. | Same as above. |
| Narrative `level: "advanced"` / `"expert"` strings | Not resolvable against EQF / ESCO. | `level.level_label` from a declared framework (e.g. `"EQF level 4"` with `framework_ref` IRI). |
| Persona-style `subjects[].mastery` free text | Conflates subject with competency and scale. | `subjects[]` (subject IRI only) + separate `competencies[]` + `mastery[]`. |
| Hand-written `accommodations: "more time"` strings | Loses provenance; no consent posture. | `accessibility.accommodations[]` against an external scheme + `consent_to_disclose_to_agent`. |
| Free-text `curriculum: "FR bac"` strings | Loses curriculum versioning. | `curriculum_refs[]` with `curriculum_id` IRI + `jurisdiction` + `track` + `as_of`. |

A reader MUST NOT silently map a legacy key into a pack field. If a `examples/v4/personas/01-eleve-terminale-fr.klickd` block appears next to a `x.klickd/student` block, the persona stays a persona — it is not harvested into the pack. There is **no migration tool**, and writing one is out of scope for v4.1.

## 4. Companion `host_skill` — `skill.kai.tutor.socratic`

The Socratic tutor `host_skill` is **host-side**. This `competency_pack` does **not** ship it. A sketch of what it would carry, in a separate artefact (Klickd / Kai repo, not here):

- Socratic question templates parameterised by `subject_ref` + `current_chapter_ref` from the pack.
- Backoff policy when the student's `pace_preference = "slow_with_examples"`.
- Accessibility adaptations triggered by `accessibility.needs[]` (only if `consent_to_disclose_to_agent = true`).
- Output rubric the skill itself satisfies (RFC-002 §8b verification artefacts referenced from the *agent*'s side, not the student's).

The `competency_pack` and the `host_skill` are versioned independently. A student keeps their pack across `host_skill` upgrades. A tutor `host_skill` keeps its pedagogy across student additions / removals.

## 5. Illustrative shape sketch (NOT a JSON Schema)

Non-normative. Field names illustrative. **No additionalProperties contract** declared here — that arrives only when the RFC promotes past `Proposed`. For the schema-intent companion fragments (per-block `required` / `forbidden` keys), see [`../schema-fragments/README.md`](../schema-fragments/README.md).

```jsonc
{
  "pack": "x.klickd/student",
  "pack_version": "0.1.0-draft",            // draft only; no release
  "spec_ref": "docs/rfcs/chimera/packs/student.md",
  "publisher": { "name": "klickd", "ref": "https://klickd.app" },

  // v4.1-native required: declared frameworks (RFC-009 §8.1). Stable URLs from
  // docs/rfcs/chimera/frameworks/README.md §1.
  "frameworks": [
    {
      "scheme": "esco",
      "version": "v1.1.1",
      "iri_prefix": "http://data.europa.eu/esco/skill/",
      "canonical_url": "https://esco.ec.europa.eu/en/classification/skill_main",
      "distribution_url": "https://esco.ec.europa.eu/en/use-esco/download",
      "distribution_sha256": "TBD-at-bundle-generation"
    },
    {
      "scheme": "digcomp",
      "version": "2.2",
      "iri_prefix": "https://joint-research-centre.ec.europa.eu/digcomp/2.2/",
      "canonical_url": "https://joint-research-centre.ec.europa.eu/digcomp_en",
      "distribution_url": "https://publications.jrc.ec.europa.eu/repository/handle/JRC128415",
      "distribution_sha256": "TBD-at-bundle-generation"
    },
    {
      "scheme": "lifecomp",
      "version": "2020",
      "iri_prefix": "https://joint-research-centre.ec.europa.eu/lifecomp/2020/",
      "canonical_url": "https://joint-research-centre.ec.europa.eu/lifecomp_en",
      "distribution_url": "https://publications.jrc.ec.europa.eu/repository/handle/JRC120911",
      "distribution_sha256": "TBD-at-bundle-generation"
    },
    {
      "scheme": "eqf",
      "version": "2017",
      "iri_prefix": "https://europa.eu/europass/eqf/",
      "canonical_url": "https://europa.eu/europass/en/europass-tools/european-qualifications-framework",
      "distribution_url": "https://europa.eu/europass/en/description-eight-eqf-levels",
      "distribution_sha256": "TBD-at-bundle-generation"
    },
    {
      "scheme": "cefr",
      "version": "2020",
      "iri_prefix": "https://www.coe.int/cefr/",
      "canonical_url": "https://www.coe.int/en/web/common-european-framework-reference-languages",
      "distribution_url": "https://rm.coe.int/common-european-framework-of-reference-for-languages-learning-teaching/16809ea0d4",
      "distribution_sha256": "TBD-at-bundle-generation"
    }
  ],

  // RFC-009 §5.2 + this pack §2.0
  "base_transversal_core": {
    "frameworks": [
      { "scheme": "esco",     "version": "v1.1.1", "iri_prefix": "http://data.europa.eu/esco/skill/" },
      { "scheme": "digcomp",  "version": "2.2",    "iri_prefix": "https://joint-research-centre.ec.europa.eu/digcomp/2.2/" },
      { "scheme": "lifecomp", "version": "2020",   "iri_prefix": "https://joint-research-centre.ec.europa.eu/lifecomp/2020/" },
      { "scheme": "eqf",      "version": "2017",   "iri_prefix": "https://europa.eu/europass/eqf/" }
    ],
    "transversal_refs": [
      { "competency_ref": "esco:S1.0.0",  "scheme": "esco",     "prefLabel": "Communication, collaboration and creativity" },
      { "competency_ref": "esco:S2.0.0",  "scheme": "esco",     "prefLabel": "Information skills" },
      { "competency_ref": "esco:S5.0.0",  "scheme": "esco",     "prefLabel": "Working with computers" },
      { "competency_ref": "digcomp:1.1",  "scheme": "digcomp",  "prefLabel": "Browsing, searching, filtering data, information and digital content" },
      { "competency_ref": "digcomp:1.2",  "scheme": "digcomp",  "prefLabel": "Evaluating data, information and digital content" },
      { "competency_ref": "lifecomp:L2",  "scheme": "lifecomp", "prefLabel": "Critical thinking" },
      { "competency_ref": "lifecomp:L3",  "scheme": "lifecomp", "prefLabel": "Managing learning" }
    ]
  },

  "identity": {
    "pack_role": "student",
    "display_name": null,
    "school_or_institution_ref": null,
    "enrolment_period": "2025-2026"
  },

  "levels": [
    {
      "framework_ref": "https://europa.eu/europass/eqf/level/4",
      "level_label": "EQF level 4",
      "effective_at": "2026-05-26"
    }
  ],

  "language_proficiency": [
    {
      "language_tag": "fr",
      "cefr_level": "C2",
      "scheme_ref": "https://www.coe.int/en/web/common-european-framework-reference-languages"
    },
    {
      "language_tag": "en",
      "cefr_level": "B2",
      "scheme_ref": "https://www.coe.int/en/web/common-european-framework-reference-languages"
    }
  ],

  "curriculum_refs": [
    {
      "curriculum_id": "https://eduscol.education.fr/programme/bac/spe-mathematiques",
      "jurisdiction": "FR",
      "track": "baccalaureat-general-spe-mathematiques",
      "as_of": "2025-09-01"
    }
  ],

  "subjects": [
    {
      "subject_ref": "http://data.europa.eu/esco/isced-f/0541",
      "prefLabel": "Mathematics",
      "started_at": "2025-09-01"
    },
    {
      "subject_ref": "http://data.europa.eu/esco/isced-f/0533",
      "prefLabel": "Physics",
      "started_at": "2025-09-01"
    }
  ],

  // Anchored against ESCO + DigComp. Competency IRIs are stable framework codes.
  "competencies": [
    { "competency_ref": "esco:S2.0.0",  "scheme": "esco",     "prefLabel": "Information skills" },
    { "competency_ref": "digcomp:1.2",  "scheme": "digcomp",  "prefLabel": "Evaluating data, information and digital content" },
    { "competency_ref": "digcomp:3.1",  "scheme": "digcomp",  "prefLabel": "Developing digital content" }
  ],
  "mastery": [
    {
      "competency_ref": "digcomp:1.2",
      "mastery_level": 3,
      "scale_ref": "digcomp:2.2/scale",
      "evidence_refs": ["urn:klickd:evidence:assignment:chap-3-quiz#a17"],
      "assessed_at": "2026-04-12",
      "assessed_by_ref": "teacher:lycee-x"
    }
  ],

  "preferences": {
    "preferred_languages": ["fr", "en"],
    "pace_preference": "slow_with_examples",
    "modality_preference": ["text", "diagram"],
    "feedback_cadence_preference": "after_each_exercise"
  },

  "accessibility": {
    "needs": [],
    "accommodations": [],
    "consent_to_disclose_to_agent": false
  },

  "exam_targets": [
    {
      "exam_ref": "fr:bac-2026:mathematiques",
      "target_date": "2026-06-15",
      "target_grade": null,
      "consent_to_share_grade": false
    }
  ],

  "history": [
    { "at": "2026-05-20T18:00:00Z", "kind": "chapter_completed", "ref": "mathematiques/derivees" }
  ],

  "gates": {
    "verification_gates_default": { "raise_only": true, "claim_grounding_required": true, "reversibility_threshold": "medium" },
    "human_veto_policy": { "owner": "human_carrier", "scope": ["mastery_writes", "exam_target_changes", "accommodations_changes"] }
  },

  "human_authority": {
    "final_decision_owner": "human_carrier",
    "agent_role": "advisory",
    "escalation": "guardian_then_school"
  },

  // RFC-009 §5.6 — pack-scoped memory slice; never the v4.0 main memory[]
  "memory_scope": "memory.x_klickd.student",

  // RFC-009 §8.1 — evidence and source policies are required v4.1-native fields
  "evidence_policy": {
    "required_for_claims": true,
    "pointer_only": true,
    "attestation_shape_ref": "rfc-002#8b"
  },
  "source_policy": {
    "frameworks_offline_bundle": "docs/rfcs/chimera/frameworks/README.md#3",
    "allow_inline_definitions": false,
    "language_tags": ["fr", "en"]
  },

  // RFC-009 §8.7 — deterministic token-cost estimate (RFC-003 chimera_v41_extrapolation()).
  // Heuristic = len(canonical_json)//4. See ./router_cost.md §3.2 for the derivation.
  "router_cost": {
    "tokens_estimate": 850,
    "baseline": "base_plus_one",
    "source_row": "docs/rfcs/chimera/packs/router_cost.md#32-xklickdstudent-derivation",
    "pack_token_costs_entry": "core.Edu"
  },

  // RFC-009 §5.0 + §5.1.1 — frozen literal list; presence of any of these as a TOP-LEVEL key fails validation
  "forbidden_fields": [
    "pedagogy", "teaching_method", "socratic_steps",
    "prompt_strategy", "scoring_rubric", "intervention_policy",
    "tone_rules", "system_prompt_overrides",
    "knowledge.mastered", "mastered_topics"
  ]
}
```

## 6. Validation against RFC-009 §8

The scaffold above satisfies all ten validation criteria **at spec / shape level**. The remaining gap is substance: physically generating and shipping the offline SKOS bundle. Below is the checklist against which a real `x.klickd/student` MUST pass before any catalog exposure:

| # | Criterion (RFC-009 §8) | Status for this scaffold |
|---|---|---|
| 1 | Framework anchor (SKOS/JSON-LD into ESCO / WEF / O\*NET) | **Satisfied at spec level** — top-level `frameworks[]` declares ESCO v1.1.1 + DigComp 2.2 + LifeComp 2020 + EQF 2017 + CEFR 2020 with stable URL prefixes; per-competency IRIs use real framework codes (`esco:S2.0.0`, `digcomp:1.2`, `digcomp:3.1`, `lifecomp:L2`, `lifecomp:L3`). Concrete distribution URLs and `distribution_sha256` placeholders documented in [`../frameworks/README.md`](../frameworks/README.md) §1. |
| 2 | Gates declared (RFC-002 defaults + veto posture) | **Satisfied** in `gates` and `human_authority`. |
| 3 | Evidence rules (RFC-002 §8b grounding) | **Satisfied** — top-level `evidence_policy` (`required_for_claims: true`, `pointer_only: true`, `attestation_shape_ref: "rfc-002#8b"`) + `mastery[].evidence_refs[]` enforce pointer-based attestation. Schema-intent fragment: [`../schema-fragments/README.md`](../schema-fragments/README.md) §11. |
| 4 | No PII (publisher-owned, not user-owned) | **Satisfied** — `identity` is role-shaped; user PII stays in `user.klickd` v4.0. |
| 5 | Round-trip safe with v4.0-only readers | **Satisfied at spec level** — `memory_scope` uses the `memory.x_klickd.student` slice shape; a v4.0 reader preserves the pack manifest verbatim per SPEC §33.7. Final confirmation requires a v4.0-vs-v4.1 round-trip vector, deferred to the schema-promotion PR. |
| 6 | Offline-resolvable (SKOS subset bundled) | **Satisfied at spec level** — `source_policy.frameworks_offline_bundle` points at [`../frameworks/README.md#3`](../frameworks/README.md#3-offline-bundle-shape-per-pack), which pins the directory layout, `manifest.json` shape, per-scheme `concepts.jsonld` shape, crosswalk, and licensing rules. **Substance TODO:** generate the physical bundle bytes (out of scope for this RFC; explicitly listed as a substance follow-up). |
| 7 | Router-priceable (deterministic token-cost estimate) | **Satisfied at spec level** — `router_cost.tokens_estimate = 850` for `x.klickd/student`, baseline `base_plus_one`, derivation row in [`./router_cost.md` §3.2](./router_cost.md#32-xklickdstudent-derivation). Compatible with `chimera_v41_extrapolation(pack_token_costs={...})` in `benchmarks/context_cost/runner.py`. |
| 8 | Human-authority preserved (no pack default lowers user v4.0 gate) | **Satisfied** — `gates.verification_gates_default.raise_only: true`; `human_authority.final_decision_owner = "human_carrier"`; `agent_role = "advisory"`. |
| 9 | No persona reuse / no legacy adapter (RFC-009 §5.0) | **Satisfied** — §3.2 above lists rejected legacy keys (`knowledge.mastered[]`, `mastered_topics`, narrative `level`, …); persona `01-eleve-terminale-fr.klickd` is anchor-only, not a compatibility input. |
| 10 | Carrier-vs-skill separation (§5.1.1) | **Satisfied** — §3.1 lists forbidden host-side fields; `forbidden_fields` literal block makes the check mechanical; Socratic tutor skill lives host-side as `skill.kai.tutor.socratic`. |

**Ten of ten satisfied at spec / shape level.** Remaining blockers, honestly tracked:

- **Substance — offline bundle bytes.** The directory layout, `manifest.json` shape, `concepts.jsonld` shape, and per-scheme licensing are pinned in [`../frameworks/README.md`](../frameworks/README.md). Physically generating the SKOS subset from upstream ESCO RDF / DigComp annex / LifeComp annex / EQF descriptors / CEFR Companion Volume is a substance follow-up. `distribution_sha256` remains the literal `"TBD-at-bundle-generation"` until that PR lands.
- **Substance — round-trip vector.** A v4.0-vs-v4.1 round-trip test vector (extending `verify_vectors.py` / `verify_vectors.mjs`) lands with the schema-promotion PR, not under this Draft.
- **Substance — JSON Schema.** A strict schema (with `$schema`, `$id`, `additionalProperties`) lands only when the RFC promotes past `Proposed` (RFC-009 §10). The schema-intent fragments under [`../schema-fragments/`](../schema-fragments/) are the bridge until then.

These three are **substance gaps under known shapes**, not unresolved design questions.

### 6.1 Compliance against the v4.1-native shape table (RFC-009 §8.1)

Cross-check of top-level fields the v4.1-native shape table mandates:

| §8.1 field | Present in this scaffold? | Notes |
|---|---|---|
| `pack` | ✅ `"x.klickd/student"` | P0 id (RFC-009 §3). |
| `pack_version` | ✅ `"0.1.0-draft"` | Pre-release tag; no release implied. |
| `spec_ref` | ✅ Points at this file. | — |
| `publisher` | ✅ `{name, ref}` | No PII. |
| `frameworks[]` | ✅ ESCO v1.1.1 + DigComp 2.2 + LifeComp 2020 + EQF 2017 + CEFR 2020 declared with stable URLs. | Distribution URLs + `distribution_sha256` placeholders per [`../frameworks/README.md`](../frameworks/README.md) §1. |
| `competencies[]` | ✅ Present with real framework IRIs (`esco:S2.0.0`, `digcomp:1.2`, `digcomp:3.1`). | No homegrown competency. |
| `mastery[]` | ✅ Present, scale-anchored. | `scale_ref: "digcomp:2.2/scale"` cited; no legacy `mastered_topics`. |
| `levels[]` | ✅ Array shape (single EQF level entry today). | Schema fragment [`../schema-fragments/README.md`](../schema-fragments/README.md) §6 confirms array form for future multi-framework cases. |
| `language_proficiency[]` | ✅ Optional, CEFR-anchored (`fr` C2, `en` B2). | Separate from `levels[]`. |
| `gates` | ✅ `raise_only: true`, `reversibility_threshold: "medium"`. | — |
| `human_authority` | ✅ `human_carrier` + `advisory` + `guardian_then_school`. | Closed enum (see §8.3 below). |
| `memory_scope` | ✅ `"memory.x_klickd.student"`. | — |
| `evidence_policy` | ✅ `required_for_claims: true`, `pointer_only: true`, `attestation_shape_ref: "rfc-002#8b"`. | — |
| `source_policy` | ✅ Declared; bundle pointer is `docs/rfcs/chimera/frameworks/README.md#3`. | Spec-level satisfied; physical bundle bytes are substance TODO. |
| `router_cost` | ✅ `tokens_estimate: 850`, `baseline: "base_plus_one"`, `source_row` named. | See [`./router_cost.md` §3.2](./router_cost.md#32-xklickdstudent-derivation). |
| `forbidden_fields` | ✅ Literal frozen list. | Used by the §3.1 / §3.2 static check. |

## 7. Integration with `klickd.app`

Notes for the `klickd.app` side; this file is the spec, not the implementation.

1. **Onboarding (R4-P0-1 wizard) MAY produce a `x.klickd/student` block** alongside the v4.0 user payload, only if the carrier opts into Chimera v4.1. Default for v4.0.0 GA users is **no pack** — opt-in only.
2. **Round-trip:** a v4.0-only reader (e.g. third-party agent that only speaks v4.0.0 GA) MUST preserve the `x.klickd/student` block verbatim and not degrade behaviour. Tested by the existing `roundtrip_v30.json` extended path once strict schema lands.
3. **`host_skill` loading:** `klickd.app` loads `skill.kai.tutor.socratic` from the Klickd/Kai `host_skill` registry (host-side). The `host_skill` reads the student `competency_pack` but never writes the pack except via the user's explicit acceptance of a write (RFC-008-style proposal flow).
4. **Multi-host portability:** the same `x.klickd/student` payload, loaded by a non-Klickd host (e.g. a school's revision tool), MUST yield comparable behaviour with that host's own pedagogical `host_skill`. The `competency_pack` is portable; the `host_skill` is not.
5. **`/klickdskill` catalog:** see [`../packs/README.md`](./README.md) for the explicit no-fake-catalog rule. This scaffold MUST NOT be served as a downloadable pack until §6 fully passes.

## 8. Open decisions (specific to this pack)

> Several decisions previously open in this list are now **narrowed** by the schema-intent fragments under [`../schema-fragments/`](../schema-fragments/), the framework registry under [`../frameworks/`](../frameworks/), and the router-cost rows under [`./router_cost.md`](./router_cost.md). What remains is genuinely open and gates promotion past `Draft scaffold`.

### 8.1 Narrowed (resolved at spec level)

1. **`mastery[].scale_ref` mandatory or optional?** **Resolved: required.** Pack `mastery[]` entries MUST cite a `scale_ref` (`digcomp:2.2/scale`, `eqf:2017/scale`, `bloom:1956/scale`). Free-form rubrics rejected. See [`../schema-fragments/README.md`](../schema-fragments/README.md) §5.
2. **Evidence storage.** **Resolved: pointers only.** `evidence_policy.pointer_only: true` is required for v4.1-native packs. Inline attestations forbidden (size + privacy). See [`../schema-fragments/README.md`](../schema-fragments/README.md) §11.
3. **Minor / adult split.** **Resolved (narrowed):** `human_authority.escalation` is a **closed enum** with values `self | guardian_then_school | school_only | professional_then_self | operator_then_self`. New values require an RFC bump. See [`../schema-fragments/README.md`](../schema-fragments/README.md) §9. The `human_carrier` vs `human_carrier_with_guardian` distinction on `final_decision_owner` is the orthogonal minor/adult axis.
4. **Relationship to `usage_profile` (RFC-007).** **Resolved (narrowed): composes.** `x.klickd/student` composes with `usage_profile: "learning"` (does not replace, does not imply). The `decision_router` (RFC-009 §5.5, RFC-007) uses both signals — `usage_profile` drives the initial active set, and the pack's declared competencies drive per-turn re-routing.
5. **Multi-track learners.** **Resolved (narrowed): single pack with multiple `curriculum_refs[]`.** A learner following two curricula carries one `x.klickd/student` pack with `curriculum_refs[]` length > 1. Compositional `x.klickd/student@FR` + `x.klickd/student@UK` is **rejected** — it would double-count base transversal core and break the seven-pack ceiling (RFC-009 §5.3). Soft cap on `curriculum_refs[]` length: 3 (advisory, not schema-enforced).

### 8.2 Still open (gates on promotion)

1. **`history[]` retention policy.** Calendar window vs event-count cap vs compaction policy (RFC-005). Current draft: bounded by a per-pack compaction policy that rolls old entries up into `mastery[]` deltas. The exact cadence (rolling 90 days? 200 events? RFC-005-driven?) is unresolved and depends on RFC-005 landing.
2. **`x.klickd/student` vs `x.klickd/user`** at the qualification-level boundary. `x.klickd/user` carries the base transversal core; `x.klickd/student` *also* carries the base transversal core (per RFC-009 §5.2 — base is always-on in every pack). Does this duplicate state when both packs are active simultaneously? Current draft: yes by design, and the `decision_router` deduplicates at load time. A more efficient sharing model is a future RFC.
3. **Per-language `mastery[]`.** Should `mastery[]` entries carry a language tag for the assessment language (e.g. a maths concept assessed in French vs English)? Current draft: no — `mastery_level` is language-agnostic; if the language matters, the assessor records it via `assessed_by_ref` discriminator. Reviewers may push back if pedagogy/host_skill testing argues otherwise.
4. **Cross-curriculum mastery roll-up.** When two `curriculum_refs[]` cover overlapping competencies (e.g. French `lycée` mathematics and UK `A-level` mathematics both touch `esco:S1.2.0`), does the pack carry one mastery entry per `(competency_ref, curriculum_ref)` pair, or one merged entry? Current draft: one merged entry; curriculum-specific evidence lives in `evidence_refs[]`.

## 9. Non-actions (scope discipline)

- No JSON Schema is shipped with this scaffold. Schema-intent fragments under [`../schema-fragments/`](../schema-fragments/) are the bridge until promotion past `Proposed`.
- No physical SKOS/JSON-LD bundle bytes ship under this RFC. The bundle directory layout, `manifest.json` shape, and per-scheme licensing rules are pinned in [`../frameworks/README.md`](../frameworks/README.md) §3; generating the actual bytes is a substance follow-up.
- No example `.klickd` file is published in `examples/v4/personas/` under this name (that directory remains anchors-only per RFC-009 §6).
- No package version bump, no release.
- **No Zenodo DOI.** Explicitly excluded per the v4.1 delivery scope.
- No tag, no `latest` npm/PyPI, no IANA action.
- No modification to `klickd-ai/site`.
- No `/klickdskill` catalog entry yet (see [`./README.md`](./README.md)).
- No change to `benchmarks/context_cost/runner.py`. The `router_cost` rows in [`./router_cost.md`](./router_cost.md) plug into the existing `chimera_v41_extrapolation(pack_token_costs=...)` argument without touching the runner.

## 10. See also

- [`../../RFC-009-chimera-v4.1.md`](../../RFC-009-chimera-v4.1.md) — full RFC (carrier-vs-skill rule in §5.1.1, validation in §8, v4.1-native shape table in §8.1).
- [`../README.md`](../README.md) — Chimera companion summary.
- [`./README.md`](./README.md) — pack index + `/klickdskill` later-notes + no-fake-catalog reminder.
- [`../frameworks/README.md`](../frameworks/README.md) — canonical framework registry (ESCO / DigComp / LifeComp / EQF / CEFR / WEF / O\*NET / NICE / ENISA / CIS / SFIA) and offline SKOS/JSON-LD bundle shape.
- [`../schema-fragments/README.md`](../schema-fragments/README.md) — schema-intent fragments for the pack manifest, `base_transversal_core`, `competencies`, `mastery`, `evidence_policy`, `source_policy`, `gates`, `human_authority`, structured memory, `router_cost`, `forbidden_fields`.
- [`./router_cost.md`](./router_cost.md) — deterministic heuristic token-cost rows for `x.klickd/user` and `x.klickd/student`, RFC-003-compatible.
- [`../../../use-cases/DOMAIN_PROFILE_CATALOG.md`](../../../use-cases/DOMAIN_PROFILE_CATALOG.md) — domain taxonomy precursor.
- [`../../RFC-006-agent-core.md`](../../RFC-006-agent-core.md) — `agent_core` composition rule.
- [`../../RFC-007-usage-profile-skill-routing.md`](../../RFC-007-usage-profile-skill-routing.md) — in-session skill routing.
- [`../../../../benchmarks/context_cost/README.md`](../../../../benchmarks/context_cost/README.md) — Context Cost Benchmark and `chimera_v41_extrapolation()` function.
- [`../../../../examples/v4/personas/01-eleve-terminale-fr.klickd`](../../../../examples/v4/personas/01-eleve-terminale-fr.klickd) — the anchor persona / example (inspiration only — **neither a `competency_pack` nor a `host_skill`**; see [RFC-009 §0.1, §6](../../RFC-009-chimera-v4.1.md)).
