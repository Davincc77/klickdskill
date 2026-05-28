# `.klickd v4.1 — Chimera` — per-candidate review checklist

| | |
|---|---|
| **Status** | **Draft · NON-NORMATIVE · review tool only** |
| **Track** | `.klickd v4.1` — Chimera (post-`v4.0.0` GA) |
| **Created** | 2026-05-27 |
| **Use** | Reviewer runs this checklist on every row of [`V4_1_SKILL_CANDIDATE_MAPPING.md`](./V4_1_SKILL_CANDIDATE_MAPPING.md) before agreeing it is `candidate_mapped`. |

> **Non-normative.** No release artefact, no schema change. This is a reviewer aid; the authoritative validation contract for `ship_ready` is [RFC-009 §8 / §8.1](../rfcs/RFC-009-chimera-v4.1.md).

---

## How to use

For each candidate row, mark each check as `[x]` (passes), `[ ]` (does not pass — candidate stays `needs_mapping`), or `[~]` (not applicable, with a one-line justification). A candidate is `candidate_mapped` only when **C-001 through C-009** are `[x]` (or `[~]` with justification) and **C-010 through C-012** are `[x]`. `ship_ready` requires additionally **C-013 through C-022** per [RFC-009 §8](../rfcs/RFC-009-chimera-v4.1.md) and is out of scope for this PR.

---

## Required-field checks (C-001 .. C-009 — promote from `needs_mapping` to `candidate_mapped`)

- [ ] **C-001 — Parent pack(s).** The candidate names at least one parent `carrier_pack` from the existing P0 set (`x.klickd/user`, `x.klickd/student`, `x.klickd/coding`, `x.klickd/research`, `x.klickd/security`, `x.klickd/legal`) or P1 set (`x.klickd/work`, `x.klickd/creator`, `x.klickd/gaming`, `x.klickd/bridge`, `x.klickd/mission`). Composition with multiple parents is explicit (no implicit inheritance).
- [ ] **C-002 — Namespace.** The proposed canonical filename is `x.klickd/<name>` exactly. Not `core.*`, not `klickdapp.*`, not `kai.*`, not `skill.*`.
- [ ] **C-003 — Filename.** The proposed canonical filename does not collide with an existing entry under [`examples/v4/starter-skills/manifest.json`](../../examples/v4/starter-skills/manifest.json) unless the candidate is explicitly a sub-profile of that pack (e.g. `work-assistant` composes with `x.klickd/work`, NOT a redefinition). For artefacts under `examples/v4.1/x-klickd-skills/{lite,pro}/`, **filename stem MUST equal pack tail with underscores converted to dashes** (validator-enforced; audit W-1 fix). Sub-profile divergence requires an explicit allow-list entry.
- [ ] **C-004 — Target carrier.** The candidate names a target carrier (a real, plausible person — learner, developer, operator, parent, …). No org-only / fleet-only / B2B-only carriers. No PII fields in the candidate description.
- [ ] **C-005 — Competencies / framework anchors.** The candidate cites at least one authoritative framework from the canonical registry ([`docs/rfcs/chimera/frameworks/README.md`](../rfcs/chimera/frameworks/README.md) §1 — `esco`, `digcomp`, `lifecomp`, `eqf`, `cefr`, `wef`, `onet`, `nice`, `enisa`, `cis`, `sfia`). Citation references (e.g. EU AI Act, GDPR, MiCA, PRISMA, Berne) are flagged as **citation-only**, NOT as top-level `frameworks[]` schemes.
- [ ] **C-006 — No homegrown taxonomy.** The candidate does not invent a new framework scheme (no `klickd:*` IRI prefix, no homegrown level scale, no homegrown competency list). If a needed concept is missing, the candidate is `needs_mapping` and an `Open` line says so.
- [ ] **C-007 — Gates declared.** The candidate states its RFC-002 `verification_gates` defaults and `human_authority` posture. `raise_only: true` against the carrier's v4.0 gates is preserved.
- [ ] **C-008 — Source / evidence policy.** The candidate cites RFC-002 §8b grounding posture and RFC-003 `verification_artifacts[]` shape (pointer-only by default). Any deviation from `pointer_only: true` is explicit.
- [ ] **C-009 — Size tier + status.** The candidate is placed in Lot A or Lot B per [`V4_1_SKILL_CANDIDATE_MAPPING.md`](./V4_1_SKILL_CANDIDATE_MAPPING.md) §0.3. The status field is one of `needs_mapping` / `candidate_mapped` / `ship_ready`.

## Architectural-invariant checks (C-010 .. C-012 — always required, also for `candidate_mapped`)

- [ ] **C-010 — Carrier-vs-skill (RFC-009 §5.1.1).** The candidate is described as **state, not behaviour**. The candidate description does NOT contain `pedagogy`, `teaching_method`, `socratic_steps`, `prompt_strategy`, `scoring_rubric`, `intervention_policy`, `tone_rules`, `system_prompt_overrides`. The matching `host_skill` (if discussed) is named separately as `skill.<host>.<domain>.<method>` and is **not** part of the pack.
- [ ] **C-011 — Clean-architecture (RFC-009 §5.0).** The candidate is NOT a renamed v4-preview persona (`examples/v4/personas/01-eleve-terminale-fr.klickd`, …). It does NOT carry `knowledge.mastered[]`, `mastered_topics[]`, narrative `level: "advanced"`, free-text `subjects[].mastery`. It is authored from frameworks, not harvested from a persona file.
- [ ] **C-012 — No Klickd.app leakage.** The candidate description does NOT mention `klickdapp.lu.klickd` / `klickdapp.fr.klickd` / `klickdapp.be.klickd` / `klickdapp.de.klickd` (or any other country scope), `kai.tutor`, `Kai Tutor`, `Kai Mentor`, `skill.kai.*`, `core.Kai.klickd`, or any other Klickd.app product / Kai host-side artefact as if it were a candidate Chimera pack. The exclusion table of [`README_V4_1.md`](./README_V4_1.md) §3 applies in full.

## `ship_ready` checks (C-013 .. C-022 — out of scope for this PR, mirrors RFC-009 §8)

- [ ] **C-013 — Framework anchor resolved (§8.1).** Every cited competency resolves to a SKOS/JSON-LD reference into the canonical framework registry.
- [ ] **C-014 — Gates declared per action (§8.2).**
- [ ] **C-015 — Evidence rules per claim (§8.3).**
- [ ] **C-016 — No PII (§8.4).**
- [ ] **C-017 — Round-trip safe (§8.5).**
- [ ] **C-018 — Offline-resolvable bundle (§8.6).**
- [ ] **C-019 — Router-priceable (§8.7).**
- [ ] **C-020 — Human authority preserved (§8.8).**
- [ ] **C-021 — No persona reuse, no legacy adapter (§8.9).**
- [ ] **C-022 — Carrier-vs-skill separation, frozen `forbidden_fields` literal (§8.10).**

A candidate is `ship_ready` only when **C-001 through C-022** all pass, the mandatory QA protocol [`V4_1_SKILL_QA_PROTOCOL.md`](./V4_1_SKILL_QA_PROTOCOL.md) clears (all 14 gates PASS, no open BLOCKER, every WARN acknowledged), and pair-reviewer sign-off exists per [`docs/rfcs/ACCEPTANCE_CHECKLIST_V4.md`](../rfcs/ACCEPTANCE_CHECKLIST_V4.md). The QA protocol is the merge gate: a skill that flips to `ship_ready` without a QA scoring + sign-off record is rolled back to `candidate_mapped`.

---

## See also

- [`README_V4_1.md`](./README_V4_1.md) — planning index.
- [`V4_1_SKILL_CANDIDATE_MAPPING.md`](./V4_1_SKILL_CANDIDATE_MAPPING.md) — candidate mapping table.
- [`V4_1_SKILL_QA_PROTOCOL.md`](./V4_1_SKILL_QA_PROTOCOL.md) — **mandatory** pre-ship QA gates and sign-offs (merge gate for `ship_ready`).
- [`V4_1_COMPETENCY_IDENTIFICATION_PROTOCOL.md`](./V4_1_COMPETENCY_IDENTIFICATION_PROTOCOL.md) — competency selection method.
- [`docs/rfcs/RFC-009-chimera-v4.1.md`](../rfcs/RFC-009-chimera-v4.1.md) §8 / §8.1 — validation contract.
- [`docs/rfcs/chimera/frameworks/README.md`](../rfcs/chimera/frameworks/README.md) — canonical framework registry.
- [`docs/rfcs/ACCEPTANCE_CHECKLIST_V4.md`](../rfcs/ACCEPTANCE_CHECKLIST_V4.md) — promotion gate (pair-reviewer rule).
