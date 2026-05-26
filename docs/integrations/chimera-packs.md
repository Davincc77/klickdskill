# Starter `.klickd` skills (v4.0 envelope)

> **Status:** Non-normative starter artefacts. Pre-release. Not v4.1 GA.
>
> **Triggers no release.** No tag, no npm `latest`, no PyPI release, no DOI, no IANA action, no SDK bump.

This doc points integrators at the four downloadable starter `.klickd` skills under [`examples/v4/chimera-packs/`](../../examples/v4/chimera-packs/) and explains how they compose with the existing integration patterns described elsewhere in this directory.

## The four starter skills

| File | Skill id | Domain | When to load |
|---|---|---|---|
| [`user.klickd`](../../examples/v4/chimera-packs/user.klickd) | `x.klickd/user` | transversal (base) | Always-on base layer for any carrier. |
| [`student.klickd`](../../examples/v4/chimera-packs/student.klickd) | `x.klickd/student` | education | Tutoring, exam preparation, learner-state carrying flows. |
| [`research.klickd`](../../examples/v4/chimera-packs/research.klickd) | `x.klickd/research` | research / evidence | Claim-grounding-heavy work; gates `factual_claim_without_citation` to `block`. |
| [`coding.klickd`](../../examples/v4/chimera-packs/coding.klickd) | `x.klickd/coding` | software engineering | Pair-programming flows; gates `force_push`, `secret_handling`, `production_deploy`. |

SHA-256 manifest: [`manifest.json`](../../examples/v4/chimera-packs/manifest.json). Offline verifier: [`scripts/verify_chimera_packs.py`](../../scripts/verify_chimera_packs.py). Pytest wrapper: [`tests/test_chimera_starter_packs.py`](../../tests/test_chimera_starter_packs.py).

## What changes vs. the v4-preview personas

The starter skills follow the **carrier-vs-skill split**: they carry *carrier state* (competencies, mastery, levels, gates, accessibility), never *host method* (pedagogy, scoring rubric, prompt strategy). The matching method lives on the host side as a `host_skill` — for example `skill.kai.tutor.socratic` consults `x.klickd/student`, `skill.coding.assistant` consults `x.klickd/coding`, `skill.research.assistant` consults `x.klickd/research`.

The skills additionally carry, on top of the v4.0 envelope:

- `base_transversal_core` (ESCO / DigComp / LifeComp / EQF anchors)
- framework-anchored `competencies[]` (no homegrown competency without an external IRI)
- framework-anchored `levels[]` (e.g. `EQF level 4` / `EQF level 6` / `EQF level 7`)
- `evidence_policy` with `pointer_only: true` (RFC-002 §8b)
- `source_policy` pointing at the offline SKOS/JSON-LD bundle
- per-skill `gates` and a global `verification_gates` list (`raise_only: true`)
- `human_authority.final_decision_owner = "human_carrier"`
- `structured_memory` slice scoped to `memory.x_klickd.<pack>`
- `router_cost` (deterministic heuristic, RFC-003)
- `forbidden_fields` literal (carrier-vs-skill firewall)

## How to integrate

The starter `.klickd` files round-trip through any v4.0 reader; readers that do not understand the `x_klickd_pack` block preserve it verbatim (SPEC §33.7).

A host that *does* understand the block can use it to:

1. **Pick gates.** Read `x_klickd_pack.verification_gates.gates[]` and apply at least the listed levels — never lower (`raise_only: true`).
2. **Pick a host_skill.** Use the `pack` id to select a matching host-side skill (`x.klickd/student` → `skill.kai.tutor.socratic`, `x.klickd/coding` → `skill.coding.assistant`, `x.klickd/research` → `skill.research.assistant`).
3. **Honour human authority.** `final_decision_owner = "human_carrier"`; `agent_role = "advisory"`. The user wins every conflict.
4. **Resolve framework IRIs offline.** Use the SKOS/JSON-LD bundles under `docs/rfcs/chimera/frameworks/` referenced by each starter file's `source_policy.frameworks_offline_bundle`.

## Release status

The starter `.klickd` skills are **not yet published** as npm or PyPI package data. The live `@klickd/core` and `klickd` packages do **not** ship these files; a future patch release (`@klickd/core@4.0.x` and `klickd==4.0.x`) will be required to update the live pages.

Until then, fetch the starter `.klickd` files directly from the GitHub source URL under [`examples/v4/chimera-packs/`](../../examples/v4/chimera-packs/).
