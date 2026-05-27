# `examples/v4/klickdapp-skills/` — Klickd.app student `.klickd` carrier examples

> **Status:** App-specific carrier examples. **Non-normative.** **Pre-release.**
>
> **Triggers no release.** No tag, no `latest` on npm or PyPI, no DOI on Zenodo, no IANA action, no SDK bump.

This directory contains four real, structured `.klickd` files that show how the
Klickd.app product would serialise a **student carrier** for four European
country scopes on top of the **v4.0 envelope**. They are app-specific carrier
examples — not public starter skills, not relabelled v4-preview personas, and
not bundled into the npm or PyPI packages as starter data.

## Files

| File | Country scope | Languages in `language_proficiency` / `source_policy` |
|---|---|---|
| [`klickdapp.lu.klickd`](./klickdapp.lu.klickd) | LU (Luxembourg) | `lb`, `fr`, `de`, `en` |
| [`klickdapp.fr.klickd`](./klickdapp.fr.klickd) | FR (France) | `fr`, `en` |
| [`klickdapp.be.klickd`](./klickdapp.be.klickd) | BE (Belgium) | `fr`, `nl`, `de`, `en` |
| [`klickdapp.de.klickd`](./klickdapp.de.klickd) | DE (Germany) | `de`, `en` |

No other country files (MA, SN, NL, CH, PT, CA, …) are in scope for this batch.

## What these files *are*

Each file is a real structured JSON document carrying:

- the **v4.0 envelope** (`klickd_version: "4.0"`, `payload_schema_version`,
  `created_at`, `encrypted: false`, `domain: "education"`,
  `profile_kind: "learner"`) so existing v4.0 readers round-trip them unchanged;
- a `_pack_metadata` block flagging them as `kind: "app_student_carrier"` for
  `app: "klickd.app"`, with `country_scope` set and
  `claims_v41_ga: false`, `contains_real_pii: false`,
  `contains_secrets: false`;
- the **`x_klickd_pack` block** carrying learner-state-only fields:
  - `pack`, `pack_version`, `spec_ref`, `publisher`
  - `frameworks[]` — ESCO / DigComp / LifeComp / EQF / CEFR plus the
    country-specific curriculum scheme (MENJE-LU, Éducation nationale FR,
    FW-B + Vlaanderen-onderwijs BE, KMK DE)
  - `base_transversal_core`
  - `identity` (with `country_ref`, `display_name: null`,
    `school_or_institution_ref: null`)
  - `language_proficiency[]` — country-appropriate languages with CEFR refs
  - `curriculum_refs[]` — country-specific authoritative curriculum pointers
  - `subjects[]` with `coursework_pointer: null` (pointer-only)
  - `mastery: []` plus a `mastery_delta_policy`
    (`raise_only: true`, `human_confirmation_required: true`,
    `evidence_pointer_required: true`, `max_delta_per_session: 0.1`)
  - `progression` (current/next stage refs, last evaluated timestamp — all null
    in the publisher-owned starter shape)
  - `session_evidence` — pointer-only, `entries: []`
  - `gates` (with `human_veto_policy` covering mastery writes, exam targets,
    accommodations, curriculum-ref changes, progression writes)
  - `human_authority` — `final_decision_owner: human_carrier`,
    `agent_role: advisory`, `escalation: guardian_then_school`
  - `evidence_policy` (`pointer_only: true`)
  - `source_policy` with the country-appropriate `language_tags`
  - `verification_gates` (`raise_only` via `gates.verification_gates_default`,
    plus per-action gates: `exam-claim` confirm, `mastery-write` confirm,
    `progression-write` confirm, `public-post` block)
  - `router_cost`
  - `forbidden_fields` literal (enforces the carrier-vs-skill split)

## What these files are NOT

- **Not public starter skills.** Those live under
  [`../starter-skills/`](../starter-skills/). These four files are app-specific
  carrier examples for Klickd.app and are not bundled as npm/PyPI package
  starter data.
- **Not host-side skills.** No pedagogy, teaching method, socratic steps,
  prompt strategy, scoring rubric, intervention policy, tone rules, or
  system-prompt overrides anywhere. The `forbidden_fields` literal enforces
  this on every file.
- **Not full Kai or host behaviour.** No host-side intelligence/understanding
  scoring lives in these files.
- **Not RFC / Chimera / v4.1 public spec text.** No public Chimera, v4.1, or
  RFC wording is reproduced here. `_pack_metadata.claims_v41_ga: false`.
- **Not personal data.** No PII, no secrets, no real user state.
  `display_name: null`, `school_or_institution_ref: null`, `mastery: []`,
  `history: []`, `session_evidence.entries: []`. Each file is a
  publisher-owned starter shape a Klickd.app carrier can adopt and
  personalise locally without weakening gates (`raise_only: true`).

## How to verify

Offline verification with the existing v4.0-envelope validator:

```bash
python3 scripts/validate_starter_packs.py \
    --dir examples/v4/klickdapp-skills \
    --v40-envelope
```

A focused pytest is provided alongside this directory's structure check:

```bash
pytest tests/test_klickdapp_student_carriers.py
```

The test verifies, for each of the four files:

- the v4.0 envelope is present and well-formed;
- the `_pack_metadata.kind` is `app_student_carrier` and the country scope
  matches the filename;
- `x_klickd_pack` carries the learner state surface required by the task
  (state, progression, curriculum_refs, country, language_proficiency,
  session_evidence, mastery_delta_policy, human authority and gates);
- the `language_proficiency[]` languages match the country matrix above;
- the `forbidden_fields` literal is present and the file contains no
  host-side pedagogy / Kai / intelligence-scoring fields and no public
  Chimera/v4.1/RFC wording.

## Relation to other directories

| Directory | What it carries |
|---|---|
| [`../starter-skills/`](../starter-skills/) | Publisher-owned public starter `.klickd` skills (`user`, `student`, `research`, `coding`) on the v4.0 envelope. Non-normative. |
| [`../personas/`](../personas/) | v4-preview persona anchors / demo fixtures (free-text `knowledge.mastered[]`, narrative levels). Non-normative. |
| `./` (this directory) | **App-specific student carrier examples for Klickd.app.** Country-scoped. Framework-anchored. State-only. |

## Release status

No tag, no release, no Zenodo DOI, no IANA action, no SDK bump, no
`latest` on npm or PyPI. These files are app-specific carrier examples and
are intentionally not bundled into the public packages.
