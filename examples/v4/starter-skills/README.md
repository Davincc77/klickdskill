# `examples/v4/starter-skills/` — Starter `.klickd` skills

> **Status:** Starter / sample artefacts. **Non-normative.** **Pre-release.**
>
> **Triggers no release.** No tag, no `latest` on npm or PyPI, no DOI on Zenodo, no IANA action, no SDK bump.

This directory ships four real, structured `.klickd` files — starter skills on top of the **v4.0 envelope**. They are downloadable starter `.klickd` files — not relabelled v4-preview personas and not host-side skills.

## Files

| File | Skill id | Domain | Hash (sha256_file) |
|---|---|---|---|
| [`user.klickd`](./user.klickd) | `x.klickd/user` | transversal (base) | `19121af045f6dd3537aa9bd4372edfaed5097b8436f026a8e9c585abbac6c80a` |
| [`student.klickd`](./student.klickd) | `x.klickd/student` | education | `ffea74552ecedc9076d6468cb10214586632163f073a8c7975642e272464dba4` |
| [`research.klickd`](./research.klickd) | `x.klickd/research` | research / evidence | `571bd07773caff23d08fe6857bbf696dd6e49f701aab750fa7b261345285ce63` |
| [`coding.klickd`](./coding.klickd) | `x.klickd/coding` | software engineering | `1aab06122d8b6c7ed45737aa3b6becad3ae33badb5ad893cc7788ad6dd1481f4` |
| [`manifest.json`](./manifest.json) | — | sha256 manifest of the four skills above | (regenerable via `scripts/verify_starter_skills.py`) |

## What these skills *are*

Each file is a real structured JSON document that carries:

- the **v4.0 envelope** (`klickd_version`, `payload_schema_version`, `domain`, `profile_kind`, `created_at`, `encrypted`) — so an existing v4.0 reader round-trips it without breaking;
- the **`x_klickd_pack` block** carrying:
  - `pack`, `pack_version`, `spec_ref`, `publisher`
  - `frameworks[]` (ESCO / DigComp / LifeComp / EQF / CEFR / SFIA depending on the skill)
  - `base_transversal_core`
  - domain-specific `competencies[]` anchored to authoritative framework IRIs
  - `levels[]` with framework-anchored `level_label` (e.g. `EQF level 4`, `EQF level 6`, `EQF level 7`)
  - `mastery[]` (empty in starter; pointer-only when populated by a carrier)
  - `source_policy`, `evidence_policy` (RFC-002 §8b)
  - `verification_gates` and per-skill `gates.verification_gates_default` (RFC-002, `raise_only: true`)
  - `human_authority` (`final_decision_owner: human_carrier`, `agent_role: advisory`)
  - `structured_memory` block scoped to `memory.x_klickd.<pack>`
  - `router_cost` (deterministic heuristic, RFC-003)
  - `forbidden_fields` literal (enforces the carrier-vs-skill split)

## What these skills are NOT

- **Stable v4.0 envelope.** `klickd_version: "4.0"`, `_pack_metadata.claims_v41_ga: false`. No public catalog is implied.
- **Not relabelled personas.** They are *new artefacts* authored against frameworks. They do **not** harvest `knowledge.mastered[]` / `mastered_topics` from the v4-preview persona fixtures under [`../personas/`](../personas/) (clean-architecture invariant).
- **Not host-side skills.** The `forbidden_fields` literal is the carrier-vs-skill firewall. Pedagogy, scoring rubrics, prompt strategies, tone rules — those belong in a `host_skill` on the agent side, not in the starter file.
- **Not personal data.** No PII, no secrets, no real user state. `display_name: null`, `school_or_institution_ref: null`, `mastery: []`, `history: []`. The starter files are *publisher-owned starter shapes* a carrier can adopt and personalise locally.

## How to verify

Offline verification of structure, fields, anti-PII guard, anti-host_skill guard, and hash stability:

```bash
python3 scripts/verify_starter_skills.py
# or via pytest
pytest tests/test_starter_skills.py
```

The general starter-pack validator (`scripts/validate_starter_packs.py`) by
default expects the structured fields at the top level of each file. For the
v4.0 starter `.klickd` files in this directory (which nest those fields
under `x_klickd_pack` so the v4.0 envelope round-trips unchanged) run it
with the `--v40-envelope` flag:

```bash
# v4.0-envelope mode — unwraps `x_klickd_pack` before validation
python3 scripts/validate_starter_packs.py \
    --dir examples/v4/starter-skills \
    --v40-envelope
```

The two scripts are complementary: `verify_starter_skills.py` covers the v4.0
envelope, persona-isolation, and hash-stability checks specific to this
directory; `validate_starter_packs.py --v40-envelope` covers the shared
field/forbidden-field/PII checks against the same files.

## How to use

These are downloadable starter `.klickd` files. A carrier can:

1. Open the file matching their context (`user.klickd` as the always-on base, plus one of `student.klickd` / `research.klickd` / `coding.klickd`).
2. Personalise *locally* — fill in `language_proficiency[]`, `subjects[].current_chapter_ref`, mastery entries (pointer-only), exam targets, etc. Personalisation never weakens gates (`raise_only: true`).
3. Carry the file between agents. `human_authority.final_decision_owner = "human_carrier"` is non-negotiable across hosts.

## Relation to internal spec work

These starter `.klickd` files sit on top of the **v4.0 envelope** and are non-normative starter artefacts for reviewers and integrators. Any future schema promotion and catalog surface remains gated by `ACCEPTANCE_CHECKLIST_V4.md`.

## Relation to existing personas

| `examples/v4/personas/*.klickd` | `examples/v4/starter-skills/*.klickd` |
|---|---|
| Persona anchors / v4-preview demo fixtures. | Starter `.klickd` skills on the v4.0 envelope. |
| Free-text `knowledge.mastered[]`, narrative `level`. | Framework-anchored `competencies[]`, framework-anchored `levels[]`. |
| Carry tutor-style fields (`teaching_mode`, `agent_instructions`). | Carry **state only**; `forbidden_fields` block forbids host-side skill fields. |
| Inspiration material for skill authors. | Real downloadable starter `.klickd` files. |

The personas remain non-normative anchors. The starter `.klickd` files in this directory are the canonical starter artefacts going forward.

## Release status

No tag, no release. The live npm package (`@klickd/core`) and PyPI package (`klickd`) **do not yet ship these starter `.klickd` files as package data** — a future patch release will be required to update those live pages. This directory and the GitHub raw URLs are the source of truth until then.
