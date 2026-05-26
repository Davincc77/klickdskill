# `x.klickd/student` — concrete pack spec scaffold

| | |
|---|---|
| **Pack id** | `x.klickd/student` |
| **Track** | `.klickd v4.1` — Chimera P0 (see [RFC-009](../../RFC-009-chimera-v4.1.md)) |
| **Status** | **Draft scaffold** · NON-NORMATIVE · shape sketch (no JSON Schema yet) |
| **Carrier** | A learner (typically a human student; equally usable for any self-directed learner) |
| **Persona anchor** | `examples/v4/personas/01-eleve-terminale-fr.klickd` — *inspiration only, NOT a competency pack* |
| **Companion (host-side) skill** | `skill.kai.tutor.socratic` (loaded by Klickd / Kai LLM, not in the pack) |
| **Created** | 2026-05-26 |
| **Triggers no release** | No schema, no SDK, no tag, no `latest` on npm/PyPI, **no Zenodo DOI**, no IANA action. |

> This is the **first concrete `x.klickd/<pack>` scaffold** under v4.1 Chimera. It demonstrates the carrier-vs-skill rule of [RFC-009 §5.1.1](../../RFC-009-chimera-v4.1.md): a pack carries the **learner's state**, never the teacher's method.

---

## 0. The two rules

> **Rule 1 — carrier-vs-skill.** `x.klickd/student` carries learner state. It does NOT carry teacher skill. The Socratic teacher / tutor skill is loaded by the **Klickd / Kai LLM** side (or any other host) as a host skill (`skill.kai.tutor.socratic`), not by the pack. The pack is what the LLM *consults*; the skill is what the LLM *applies*. Enforced by [RFC-009 §5.1.1](../../RFC-009-chimera-v4.1.md) + §8.10.
>
> **Rule 2 — v4.1-native, no legacy adapter.** This pack is built from authoritative frameworks (ESCO / DigComp / EQF, optionally O\*NET / WEF) under the SKOS/JSON-LD backbone of RFC-009 §5.7. It does **not** accept v4-preview persona fields (`knowledge.mastered[]`, `mastered_topics[]`, free-text `subjects[].mastery`, narrative `level: "advanced"` strings) as input. The persona `01-eleve-terminale-fr.klickd` is a **design anchor**, not a compatibility source. Enforced by [RFC-009 §5.0](../../RFC-009-chimera-v4.1.md) + §8.9.

If you find yourself writing `"pedagogy"`, `"how_to_teach"`, `"socratic_steps"`, `"prompt_strategy"`, `"intervention_policy"`, or `"tone_rules"` inside this pack — stop. That belongs in the host skill (Rule 1).

If you find yourself writing `"knowledge.mastered[]"`, `"mastered_topics"`, or harvesting fields from a v4-preview persona — stop. The pack is authored from frameworks, not from personas (Rule 2).

## 1. Why a concrete scaffold

[Letta `.af`](https://docs.letta.com/) and every prior "agent context format" diverged because the spec shipped without at least one **concrete, well-typed example** of the artefact. v4.1 Chimera ships with `x.klickd/student` as the worked example: it pins the shape, exercises the carrier-vs-skill rule, and gives `klickd.app` something it can actually import / round-trip without inventing fields.

## 2. What the pack carries (state, not skill)

Twelve sections. All are **carrier state**. None are teacher behaviour. All competency / level references are framework-anchored (§2.0).

### 2.0 `base_transversal_core` (mandatory, v4.1-native)

Every Chimera pack — `student` included — carries the **base transversal core**: a small cross-pack competency layer composed only of framework-anchored references. The base is what survives even when no other pack is active (RFC-009 §5.2).

For `x.klickd/student`, the base anchors are:

- **ESCO transversal skills** — communication, literacy, numeracy, problem solving, planning.
- **DigComp 2.2** — basic digital competence (information literacy, communication, content creation, safety, problem solving).
- **EQF** — qualifications framework, used for `level_label` resolution.

Wire-shape (illustrative):

```jsonc
"base_transversal_core": {
  "frameworks": [
    { "scheme": "esco",    "version": "v1.1.1", "iri_prefix": "http://data.europa.eu/esco/skill/" },
    { "scheme": "digcomp", "version": "2.2",    "iri_prefix": "https://joint-research-centre.ec.europa.eu/digcomp/" },
    { "scheme": "eqf",     "version": "2017",   "iri_prefix": "https://europa.eu/europass/eqf/" }
  ],
  "transversal_refs": [
    { "competency_ref": "esco:T1.1", "prefLabel": "Reading comprehension",      "scheme": "esco" },
    { "competency_ref": "esco:T2.3", "prefLabel": "Mathematical reasoning",     "scheme": "esco" },
    { "competency_ref": "digcomp:1.1", "prefLabel": "Browsing/searching/filtering data, information and digital content", "scheme": "digcomp" }
  ]
}
```

The base is **not** harvested from a persona's narrative description; it is declared against frameworks. A pack with an empty `base_transversal_core` fails RFC-009 §8.1 (top-level `frameworks[]` required).

### 2.1 `identity`
Minimal identification *within* the learning context, **distinct** from v4.0 `user.klickd` identity (which carries the human's identity). A pack `identity` is the role-shaped sub-identity (e.g. "Terminale S student, Lycée X, session 2026").

- `pack_role` — e.g. `"student"`.
- `display_name` — non-PII handle, optional.
- `school_or_institution_ref` — optional, opaque institution reference.
- `enrolment_period` — e.g. `"2025-2026"`.

### 2.2 `level`
Where the carrier is, *measured against an external framework* (never homegrown).

- `framework_ref` — e.g. ESCO / DigComp / EQF / national framework IRI.
- `level_label` — e.g. `"EQF level 4"` / `"Terminale (FR)"` / `"Year 13 (UK)"`.
- `effective_at` — ISO-8601 date the level was last assessed.

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

If `consent_to_disclose_to_agent` is `false`, the host skill MUST treat `accessibility` as **gated** (not injectable into the prompt verbatim).

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
The pack-local restatement of [RFC-009 §5.1](../../RFC-009-chimera-v4.1.md).

- `final_decision_owner` — MUST be `"human_carrier"` (or `"human_carrier_with_guardian"` for minors).
- `agent_role` — fixed value `"advisory"`. An agent MAY suggest pedagogy, NEVER decide enrolment, accommodations, or exam-target changes.
- `escalation` — for a minor, defaults to `"guardian_then_school"`.

## 3. What the pack does NOT carry

### 3.1 Forbidden host-side fields (Rule 1)

Explicitly **not** in this pack. These belong host-side (skill or agent core).

| Forbidden in pack | Lives where | Why |
|---|---|---|
| `pedagogy`, `teaching_method`, `socratic_steps`, `lesson_plan_template` | `skill.kai.tutor.socratic` (host) | Method changes faster than student state; portability requires the student carry only their own state. |
| `prompt_strategy`, `system_prompt_overrides` | host skill or `agent_core` (RFC-006) | Prompting is host policy, not user state. |
| `scoring_rubric`, `grading_curve` | host skill or external rubric ref | A pack can *cite* a rubric (`scale_ref`), never *define* one. |
| `intervention_policy`, `when_to_correct`, `when_to_praise` | host skill | Behaviour belongs with the actor; the pack is not an actor. |
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

## 4. Companion host skill — `skill.kai.tutor.socratic`

The Socratic tutor skill is **host-side**. This pack does **not** ship it. A sketch of what it would carry, in a separate artefact (Klickd / Kai repo, not here):

- Socratic question templates parameterised by `subject_ref` + `current_chapter_ref` from the pack.
- Backoff policy when the student's `pace_preference = "slow_with_examples"`.
- Accessibility adaptations triggered by `accessibility.needs[]` (only if `consent_to_disclose_to_agent = true`).
- Output rubric the skill itself satisfies (RFC-002 §8b verification artefacts referenced from the *agent*'s side, not the student's).

The pack and the skill are versioned independently. A student keeps their pack across tutor-skill upgrades. A tutor skill keeps its pedagogy across student additions / removals.

## 5. Illustrative shape sketch (NOT a JSON Schema)

Non-normative. Field names illustrative. **No additionalProperties contract** declared here — that arrives only when the RFC promotes past `Proposed`.

```jsonc
{
  "pack": "x.klickd/student",
  "pack_version": "0.1.0-draft",            // draft only; no release
  "spec_ref": "docs/rfcs/chimera/packs/student.md",
  "publisher": { "name": "klickd", "ref": "https://klickd.app" },

  // v4.1-native required: declared frameworks (RFC-009 §8.1)
  "frameworks": [
    { "scheme": "esco",    "version": "v1.1.1", "iri_prefix": "http://data.europa.eu/esco/skill/" },
    { "scheme": "digcomp", "version": "2.2",    "iri_prefix": "https://joint-research-centre.ec.europa.eu/digcomp/" },
    { "scheme": "eqf",     "version": "2017",   "iri_prefix": "https://europa.eu/europass/eqf/" }
  ],

  // RFC-009 §5.2 + this pack §2.0
  "base_transversal_core": {
    "transversal_refs": [
      { "competency_ref": "esco:T1.1",   "prefLabel": "Reading comprehension",  "scheme": "esco" },
      { "competency_ref": "esco:T2.3",   "prefLabel": "Mathematical reasoning", "scheme": "esco" },
      { "competency_ref": "digcomp:1.1", "prefLabel": "Information literacy",   "scheme": "digcomp" }
    ]
  },

  "identity": {
    "pack_role": "student",
    "display_name": null,
    "school_or_institution_ref": null,
    "enrolment_period": "2025-2026"
  },

  "level": {
    "framework_ref": "https://ec.europa.eu/esco/...",  // illustrative
    "level_label": "EQF level 4",
    "effective_at": "2026-05-26"
  },

  "curriculum_refs": [
    {
      "curriculum_id": "https://eduscol.education.fr/...",
      "jurisdiction": "FR",
      "track": "baccalaureat-general-spe-mathematiques",
      "as_of": "2025-09-01"
    }
  ],

  "subjects": [
    { "subject_ref": "esco:mathematics",  "prefLabel": "Mathématiques", "started_at": "2025-09-01" },
    { "subject_ref": "esco:physics",      "prefLabel": "Physique-Chimie", "started_at": "2025-09-01" }
  ],

  "competencies": [
    { "competency_ref": "esco:S1.2.3", "prefLabel": "Solving quadratic equations" }
  ],
  "mastery": [
    {
      "competency_ref": "esco:S1.2.3",
      "mastery_level": 2,
      "scale_ref": "digcomp:2.2/scale",
      "evidence_refs": ["assignment:chap-3-quiz#a17"],
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
    "verification_gates_default": { "raise_only": true, "claim_grounding_required": true },
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
    "frameworks_offline_bundle": "TODO: bundle ESCO+DigComp+EQF SKOS subset (criterion §8.6)",
    "allow_inline_definitions": false,
    "language_tags": ["fr", "en"]
  },

  // RFC-009 §8.7 — deterministic token-cost estimate (RFC-003 chimera_v41_extrapolation())
  "router_cost": {
    "tokens_estimate": null,           // TODO: fill from chimera_v41_extrapolation() row
    "baseline": "base_plus_one",
    "source_row": "TODO: benchmarks/context_cost/README.md#chimera_v41"
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

The scaffold above satisfies all ten validation criteria *in shape*. It does not yet satisfy them *in substance* (no real ESCO IRIs resolved, no SKOS bundle attached, no token-cost projection). Below is the checklist against which a real `x.klickd/student` MUST pass before any catalog exposure:

| # | Criterion (RFC-009 §8) | Status for this scaffold |
|---|---|---|
| 1 | Framework anchor (SKOS/JSON-LD into ESCO / WEF / O\*NET) | **Partial** — top-level `frameworks[]` declares ESCO + DigComp + EQF; per-competency IRIs still placeholders (`esco:S1.2.3`, `digcomp:1.1`). Real ESCO/EQF/DigComp IRIs are the remaining substance gap. |
| 2 | Gates declared (RFC-002 defaults + veto posture) | **Yes** in `gates` and `human_authority`. |
| 3 | Evidence rules (RFC-002 §8b grounding) | **Yes** — top-level `evidence_policy` (`pointer_only: true`) + `mastery[].evidence_refs[]` enforce pointer-based attestation. |
| 4 | No PII (publisher-owned, not user-owned) | **Yes** — `identity` is role-shaped; user PII stays in `user.klickd` v4.0. |
| 5 | Round-trip safe with v4.0-only readers | **Pending** — depends on final wire format; pack-scoped fields under `memory.x_klickd.student` (`memory_scope`) satisfy SPEC §33.7. |
| 6 | Offline-resolvable (SKOS subset bundled) | **TODO** — `source_policy.frameworks_offline_bundle` names the bundle; physical SKOS subset deferred to first real release. |
| 7 | Router-priceable (deterministic token-cost estimate) | **TODO** — `router_cost` block present with `tokens_estimate: null`; needs an actual `chimera_v41_extrapolation()` row. |
| 8 | Human-authority preserved (no pack default lowers user v4.0 gate) | **Yes** — `gates.verification_gates_default.raise_only: true`. |
| 9 | No persona reuse / no legacy adapter (RFC-009 §5.0) | **Yes** — §3.2 above lists rejected legacy keys (`knowledge.mastered[]`, `mastered_topics`, narrative `level`, …); persona `01-eleve-terminale-fr.klickd` is anchor-only, not a compatibility input. |
| 10 | Carrier-vs-skill separation (§5.1.1) | **Yes** — §3.1 lists forbidden host-side fields; `forbidden_fields` literal block makes the check mechanical; Socratic tutor skill lives host-side as `skill.kai.tutor.socratic`. |

Seven of ten satisfied in shape; three `TODO` items (real IRIs, SKOS offline bundle, router-cost row) are the substance gap and are explicitly tracked.

### 6.1 Compliance against the v4.1-native shape table (RFC-009 §8.1)

Cross-check of top-level fields the v4.1-native shape table mandates:

| §8.1 field | Present in this scaffold? | Notes |
|---|---|---|
| `pack` | ✅ `"x.klickd/student"` | P0 id (RFC-009 §3). |
| `pack_version` | ✅ `"0.1.0-draft"` | Pre-release tag; no release implied. |
| `spec_ref` | ✅ Points at this file. | — |
| `publisher` | ✅ `{name, ref}` | No PII. |
| `frameworks[]` | ✅ ESCO + DigComp + EQF declared. | Per-IRI resolution still TODO (criterion §8.1 schema). |
| `competencies[]` | ✅ Present (placeholder IRI). | Real IRIs TODO. |
| `mastery[]` | ✅ Present, scale-anchored. | `scale_ref: "digcomp:2.2/scale"` cited; no legacy `mastered_topics`. |
| `levels[]` (≈ `level` here) | ✅ Single-level object today. | Open decision §8.4 of this file may make it an array for multi-track learners. |
| `gates` | ✅ `raise_only: true`. | — |
| `human_authority` | ✅ `human_carrier` + `advisory`. | — |
| `memory_scope` | ✅ `"memory.x_klickd.student"`. | — |
| `evidence_policy` | ✅ `pointer_only: true`, attestation ref. | — |
| `source_policy` | ✅ Declared (bundle TODO). | — |
| `router_cost` | ✅ Block present; `tokens_estimate: null`. | Substance TODO. |
| `forbidden_fields` | ✅ Literal frozen list. | Used by the §3.1 / §3.2 static check. |

## 7. Integration with `klickd.app`

Notes for the `klickd.app` side; this file is the spec, not the implementation.

1. **Onboarding (R4-P0-1 wizard) MAY produce a `x.klickd/student` block** alongside the v4.0 user payload, only if the carrier opts into Chimera v4.1. Default for v4.0.0 GA users is **no pack** — opt-in only.
2. **Round-trip:** a v4.0-only reader (e.g. third-party agent that only speaks v4.0.0 GA) MUST preserve the `x.klickd/student` block verbatim and not degrade behaviour. Tested by the existing `roundtrip_v30.json` extended path once strict schema lands.
3. **Tutor skill loading:** `klickd.app` loads `skill.kai.tutor.socratic` from the Klickd/Kai skill registry (host-side). The skill reads the student pack but never writes the pack except via the user's explicit acceptance of a write (RFC-008-style proposal flow).
4. **Multi-host portability:** the same `x.klickd/student` payload, loaded by a non-Klickd host (e.g. a school's revision tool), MUST yield comparable behaviour with that host's own pedagogical skill. The pack is portable; the skill is not.
5. **`/klickdskill` catalog:** see [`../packs/README.md`](./README.md) for the explicit no-fake-catalog rule. This scaffold MUST NOT be served as a downloadable pack until §6 fully passes.

## 8. Open decisions (specific to this pack)

> Reviewers should treat these as gates on promoting `x.klickd/student` past `Draft scaffold`.

1. **`mastery[].scale_ref` mandatory or optional?** Current draft: required. Alternative: optional with a documented default rubric.
2. **`history[]` retention.** Bound by what? Calendar window, event-count cap, or compaction policy (RFC-005)?
3. **Minor / adult split.** Should `human_authority.escalation` be a closed enum (`guardian_then_school | self | school_only`) or open string with guidance?
4. **Multi-track learners** (e.g. a student following two curricula simultaneously). Does `curriculum_refs[]` length need a soft cap, or do we expect compositional packs (`x.klickd/student@FR` + `x.klickd/student@UK`)?
5. **Evidence storage.** Are `evidence_refs[]` always external pointers, or do we allow inline small attestations? Current draft: pointers only, to prevent the pack from growing unbounded.
6. **Relationship to `usage_profile`** (RFC-007). Does `x.klickd/student` *replace* `usage_profile: "learning"`, *compose with* it, or *imply* it? Current draft: composes; the router uses both.

## 9. Non-actions (scope discipline)

- No JSON Schema is shipped with this scaffold.
- No example `.klickd` file is published in `examples/v4/personas/` under this name (that directory remains anchors-only per RFC-009 §6).
- No package version bump, no release.
- **No Zenodo DOI.** Explicitly excluded per the v4.1 tonight delivery scope.
- No tag, no `latest` npm/PyPI, no IANA action.
- No modification to `klickd-ai/site`.
- No `/klickdskill` catalog entry yet (see [`../packs/README.md`](./README.md)).

## 10. See also

- [`../../RFC-009-chimera-v4.1.md`](../../RFC-009-chimera-v4.1.md) — full RFC (carrier-vs-skill rule in §5.1.1, validation in §8).
- [`../README.md`](../README.md) — Chimera companion summary.
- [`../packs/README.md`](./README.md) — pack index + `/klickdskill` later-notes + no-fake-catalog reminder.
- [`../../../use-cases/DOMAIN_PROFILE_CATALOG.md`](../../../use-cases/DOMAIN_PROFILE_CATALOG.md) — domain taxonomy precursor.
- [`../../RFC-006-agent-core.md`](../../RFC-006-agent-core.md) — `agent_core` composition rule.
- [`../../RFC-007-usage-profile-skill-routing.md`](../../RFC-007-usage-profile-skill-routing.md) — in-session skill routing.
- [`../../../../examples/v4/personas/01-eleve-terminale-fr.klickd`](../../../../examples/v4/personas/01-eleve-terminale-fr.klickd) — the anchor persona (inspiration only, not a competency pack).
