# `examples/v4/chimera-packs/` — Chimera-aligned starter `.klickd` packs

> **Status:** Starter / sample artefacts. **Non-normative.** **Pre-release.** **Not v4.1 GA.**
>
> **Triggers no release.** No tag, no `latest` on npm or PyPI, no DOI on Zenodo, no IANA action, no SDK bump.

This directory ships four real, structured `.klickd` files that show the **Chimera architecture** (RFC-009) realised on top of the **v4.0 envelope**. They are downloadable starter packs — not relabelled v4-preview personas, not host-side skills, not v4.1 GA packs.

## Files

| File | Pack id | Domain | Hash (sha256_file) |
|---|---|---|---|
| [`user.klickd`](./user.klickd) | `x.klickd/user` | transversal (base) | `36c790d6126ebf146649a3b692186da29945341ab62dfe42fce1b23d84f7fc80` |
| [`student.klickd`](./student.klickd) | `x.klickd/student` | education | `3a365c2a51a7152d006b4e1c05f37b23f84bb214b2bc6ebe5fce05368f123377` |
| [`research.klickd`](./research.klickd) | `x.klickd/research` | research / evidence | `a0325df37af7fc1b7df10000b361ee1b291001ae11868988401edbd8278d463d` |
| [`coding.klickd`](./coding.klickd) | `x.klickd/coding` | software engineering | `78f4710d4bdfc2e44926c25db6f6ec5a1d5901b22755aff5592078604a55a28f` |
| [`manifest.json`](./manifest.json) | — | sha256 manifest of the four packs above | (regenerable via `scripts/verify_chimera_packs.py`) |

## What these packs *are*

Each file is a real structured JSON document that carries:

- the **v4.0 envelope** (`klickd_version`, `payload_schema_version`, `domain`, `profile_kind`, `created_at`, `encrypted`) — so an existing v4.0 reader round-trips it without breaking;
- the **Chimera-aligned `x_klickd_pack` block** (RFC-009 §8.1 shape) carrying:
  - `pack`, `pack_version`, `spec_ref`, `publisher`
  - `frameworks[]` (ESCO / DigComp / LifeComp / EQF / CEFR / SFIA depending on the pack)
  - `base_transversal_core` (RFC-009 §5.2)
  - domain-specific `competencies[]` anchored to authoritative framework IRIs
  - `levels[]` with framework-anchored `level_label` (e.g. `EQF level 4`, `EQF level 6`, `EQF level 7`)
  - `mastery[]` (empty in starter; pointer-only when populated by a carrier)
  - `source_policy`, `evidence_policy` (RFC-002 §8b)
  - `verification_gates` and per-pack `gates.verification_gates_default` (RFC-002, `raise_only: true`)
  - `human_authority` (`final_decision_owner: human_carrier`, `agent_role: advisory`)
  - `structured_memory` block scoped to `memory.x_klickd.<pack>` (RFC-009 §5.6)
  - `router_cost` (deterministic heuristic, RFC-003 / RFC-009 §8.7)
  - `forbidden_fields` literal (RFC-009 §8.1, enforces the carrier-vs-skill split)

## What these packs are NOT

- **Not v4.1 GA.** `klickd_version: "4.0"`, `preview: "4.0.0-chimera-starter.1"`, `_pack_metadata.claims_v41_ga: false`. No public catalog is implied.
- **Not relabelled personas.** They are *new artefacts* authored against frameworks. They do **not** harvest `knowledge.mastered[]` / `mastered_topics` from the v4-preview persona fixtures under [`../personas/`](../personas/) (RFC-009 §5.0 clean-architecture invariant).
- **Not host-side skills.** The `forbidden_fields` literal is the carrier-vs-skill firewall (RFC-009 §5.1.1). Pedagogy, scoring rubrics, prompt strategies, tone rules — those belong in a `host_skill` on the agent side, not in the pack.
- **Not personal data.** No PII, no secrets, no real user state. `display_name: null`, `school_or_institution_ref: null`, `mastery: []`, `history: []`. The packs are *publisher-owned starter shapes* a carrier can adopt and personalise locally.

## How to verify

Offline verification of structure, fields, anti-PII guard, anti-host_skill guard, and hash stability:

```bash
python3 scripts/verify_chimera_packs.py
# or via pytest
pytest tests/test_chimera_starter_packs.py
```

## How to use

These are downloadable starter packs. A carrier can:

1. Open the file matching their context (`user.klickd` as the always-on base, plus one of `student.klickd` / `research.klickd` / `coding.klickd`).
2. Personalise *locally* — fill in `language_proficiency[]`, `subjects[].current_chapter_ref`, mastery entries (pointer-only), exam targets, etc. Personalisation never weakens gates (`raise_only: true`).
3. Carry the file between agents. `human_authority.final_decision_owner = "human_carrier"` is non-negotiable across hosts.

## Relation to RFC-009 (`Chimera v4.1`)

These packs implement the **shape** described in [`docs/rfcs/RFC-009-chimera-v4.1.md`](../../../docs/rfcs/RFC-009-chimera-v4.1.md) on top of the **v4.0 envelope**. They are starter artefacts for reviewers and integrators to see the Chimera architecture working end-to-end *before* the strict v4.1 schema is promoted past `Draft`. Promotion of the strict v4.1 schema and any catalog surface remains gated by `ACCEPTANCE_CHECKLIST_V4.md` and RFC-009 §8.

## Relation to existing personas

| `examples/v4/personas/*.klickd` | `examples/v4/chimera-packs/*.klickd` |
|---|---|
| Persona anchors / v4-preview demo fixtures. | Starter `competency_pack`s on the v4.0 envelope, Chimera-aligned. |
| Free-text `knowledge.mastered[]`, narrative `level`. | Framework-anchored `competencies[]`, framework-anchored `levels[]`. |
| Carry tutor-style fields (`teaching_mode`, `agent_instructions`). | Carry **state only**; `forbidden_fields` block forbids host-side skill fields. |
| Inspiration material for pack authors. | Real downloadable packs. |

The personas remain non-normative anchors. The packs in this directory are the canonical Chimera-aligned starter artefacts going forward.

## Release status

No tag, no release. The live npm package (`@klickd/core`) and PyPI package (`klickd`) **do not yet ship these packs as package data** — a future patch release will be required to update those live pages. This directory and the GitHub raw URLs are the source of truth until then.
