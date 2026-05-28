# `x.klickd` skill QA protocol — mandatory pre-ship gates

| | |
|---|---|
| **Status** | **Draft · NON-NORMATIVE · merge-gate for `ship_ready` promotion** |
| **Track** | `x.klickd v4.1` candidate catalog (post-`v4.0.0` GA) |
| **Created** | 2026-05-28 |
| **Companions** | [`README_V4_1.md`](./README_V4_1.md) · [`V4_1_SKILL_CANDIDATE_MAPPING.md`](./V4_1_SKILL_CANDIDATE_MAPPING.md) · [`V4_1_CANDIDATE_CHECKLIST.md`](./V4_1_CANDIDATE_CHECKLIST.md) · [`V4_1_COMPETENCY_IDENTIFICATION_PROTOCOL.md`](./V4_1_COMPETENCY_IDENTIFICATION_PROTOCOL.md) |
| **Validator** | [`scripts/validate_v4_1_candidate_mapping.py`](../../scripts/validate_v4_1_candidate_mapping.py) — mechanical subset |

> **Mandatory.** No `x.klickd` skill — Lite or Pro — moves from `candidate_mapped` to `ship_ready`, and no skill is exposed in any `/klickdskill` surface, until **every PASS gate** below is signed off and **no BLOCKER** is open. Skipping this protocol invalidates the promotion: a skill that ships without the QA record is treated as `needs_mapping` until the record is produced.
>
> **Non-normative.** This document is a process gate, not a schema change. It introduces no new fields, no envelope change, no migration. It composes with — and does not replace — [RFC-009 §8](../rfcs/RFC-009-chimera-v4.1.md) (`ship_ready` criteria) and the existing reviewer checklist [`V4_1_CANDIDATE_CHECKLIST.md`](./V4_1_CANDIDATE_CHECKLIST.md).
>
> **Public wording.** This protocol refers to candidate skills as **`x.klickd`** skills. The internal track name (Chimera) MUST NOT appear in public-facing skill descriptions, catalog entries, or `/klickdskill` UI. Internal planning docs may use either term.

---

## 0. Why this protocol exists

Three concrete failure modes the protocol is built to prevent:

1. **Near-clones in the catalog.** Two skills with the same competency set, the same gates, and the same memory segments — distinguishable only by a different `prefLabel` — degrade catalog quality, dilute the framework-anchored signal, and confuse human carriers picking a pack.
2. **Profile/behaviour drift.** A skill nicknamed `customer-support-operator` whose competencies and gates actually describe a `sales-operator` profile. The competency set says one thing; the carrier-state says another; the public description says a third. The catalog cannot police itself; reviewers must.
3. **Unsafe regulated output.** A skill that produces (or appears to produce) regulated financial / legal / medical / tax advice without the gate posture and disclaimers that EU law requires. Anti-clone is not enough; profile coherence is not enough; regulated-output disclaimers are their own gate.

The QA protocol is the merge gate that catches all three before a skill ships.

---

## 1. Mandatory gates (PASS / BLOCKER / WARN)

Each gate has a status: **PASS** (gate clears), **BLOCKER** (ship is blocked until resolved), or **WARN** (reviewer-acknowledged risk; ship may proceed only with the sign-off captured in §3). The mechanical subset is enforced by [`scripts/validate_v4_1_candidate_mapping.py`](../../scripts/validate_v4_1_candidate_mapping.py); the rest is reviewer-owned.

### QA-G01 — Profile coherence

The skill's `prefLabel`, target carrier statement, competencies, gates, memory segments, and public description MUST tell **one coherent story**. Reviewer answers in one sentence: *"What does the carrier of this skill actually do?"* — the answer MUST match every field independently.

- **BLOCKER** when: the `prefLabel` names one role (e.g. `customer-support-operator`) and the dominant competencies describe another (e.g. outbound sales pitching).
- **WARN** when: the carrier statement covers two adjacent roles (e.g. ops + light sales) without an explicit task-boundary justification.
- **PASS** when: one reviewer + one independent reviewer can each, in isolation, summarise the skill in one sentence that matches the other's summary.

### QA-G02 — Competency-source traceability

Every entry in `competencies[]` and `competency_mappings[]` MUST resolve to a SKOS-published (or maturity-comparable) framework in the §1.1 registry of [`V4_1_COMPETENCY_IDENTIFICATION_PROTOCOL.md`](./V4_1_COMPETENCY_IDENTIFICATION_PROTOCOL.md). Reviewer can open the canonical URL and read the matching entry.

- **BLOCKER**: any competency with a `klickd:*` IRI prefix, homegrown taxonomy, narrative `level: "advanced"`, or unresolvable scheme.
- **PASS**: 100 % of competencies trace to ESCO / DigComp / LifeComp / EQF / CEFR / WEF / O\*NET / NICE / ENISA / CIS / SFIA.

### QA-G03 — Shared transversal base present

The skill MUST carry `base_transversal_core.transversal_refs[]` with **at least one** entry drawn from the transversal layer (ESCO S1/S2/S3 cross-cutting, LifeComp Personal/Social, WEF transversal, DigComp transversal) — see [§3.2 of the competency protocol](./V4_1_COMPETENCY_IDENTIFICATION_PROTOCOL.md).

- **BLOCKER**: `transversal_refs[]` empty or missing.
- **PASS**: validator-enforced (`test_every_artefact_carries_transversal_base`).

### QA-G04 — Domain-specific competency fit

The domain-specific set (full `competencies[]` minus the transversal base) MUST be the **distinctive** half of the coherent blend — not a re-statement of the transversal layer, not a near-duplicate of any sibling skill's domain set.

- **BLOCKER**: domain-specific set is identical to another skill's (validator anti-clone §3.4).
- **WARN**: domain-specific Jaccard overlap ≥ 0.80 with another skill (validator near-duplicate heuristic — see §5 below). Reviewer MUST record a one-line task-boundary justification (e.g. author-vs-reader, design-vs-operate, attack-vs-defend) or split/merge.
- **PASS**: domain-specific set is unique modulo legitimate task boundaries.

### QA-G05 — Memory segment fit

The skill's `memory_segments[]` MUST match the carrier state the competencies imply, with `evidence_policy.pointer_only: true` (§5.6 RFC-009) and no inline content.

- **BLOCKER**: memory segment carries inline transcripts, raw PII, or content excerpts; `pointer_only` is `false` without an explicit RFC waiver.
- **PASS**: every segment is pointer-only and each segment is referenced by at least one competency.

### QA-G06 — Gates and human veto fit

`gates.verification_gates_default.raise_only: true` and `human_veto.raise_only: true` and `human_authority.final_decision_owner ∈ {human_carrier, human_carrier_with_guardian}` MUST hold. Action classes the competencies imply MUST each carry a `confirm` or `block` gate where appropriate (RFC-002 §8b).

- **BLOCKER**: any of the three flags is `false`; any irreversible / safety-critical action class lacks a `confirm`/`block` gate.
- **PASS**: validator-enforced for the three flags; reviewer-verified for action-class coverage.

### QA-G07 — Source / evidence policy fit

`evidence_policy.pointer_only: true` and `source_policy.allow_inline_definitions: false` MUST hold; `verification_artifacts[]` shape follows RFC-003.

- **BLOCKER**: any deviation without an explicit waiver in the per-pack RFC.
- **PASS**: validator-enforced.

### QA-G08 — Regulated-output disclaimers

For any competency that touches **regulated advice** (financial, legal, medical, tax, child-safety, drug-interaction, statutory filing), the skill MUST carry:

1. A `block`-level gate on output that resembles such advice, with mandatory escalation to a licensed professional.
2. A documented disclaimer in the carrier-facing description: *"This skill carries carrier-state only; it does not substitute for licensed professional advice."*
3. A `human_authority.final_decision_owner = human_carrier_with_guardian` posture when the carrier may be a minor (e.g. `parent-gaming`, `student.exam_targets`).

- **BLOCKER**: any of the three is missing for a skill whose competencies touch regulated advice.
- **PASS**: gate + disclaimer + authority posture present and consistent.

### QA-G09 — Anti-clone / near-duplicate check

No two shipped skills may be identical or near-identical (Vince's hard requirement).

- **BLOCKER (exact clone)**: two skills share identical `competencies[]` sets (validator §3.4, `test_no_two_artefacts_share_competency_set`).
- **WARN (near-duplicate)**: two skills, in the same tier, share Jaccard overlap ≥ 0.80 on `competencies[]`, or ≥ 0.75 on `competencies[] ∪ gate_summaries` — see §5 below for the heuristic. Reviewer MUST record a one-line task-boundary justification or split/merge.
- **PASS**: no BLOCKER and every WARN has a documented justification.

### QA-G10 — Size budget

`router_cost.tokens_estimate` and file bytes MUST fit the tier ceilings: Lite ≤ 900 tokens / ≤ 12 000 bytes, Pro ≤ 1 350 tokens / ≤ 24 000 bytes (decimal KB).

- **BLOCKER**: any overflow without an explicit split into `compact_index` + lazy body.
- **PASS**: validator-enforced.

### QA-G11 — No PII / no secrets

Artefact text MUST NOT contain real PII (emails, IBAN, phone numbers outside citation URLs), private keys, API tokens, or any secret. `_pack_metadata.contains_real_pii: false` and `_pack_metadata.contains_secrets: false` MUST hold.

- **BLOCKER**: any pattern hit from the validator's `SECRET_PATTERNS` / `PII_PATTERNS` sweep that is not on the publisher-allow-list.
- **PASS**: validator-enforced.

### QA-G12 — No forbidden public wording

Public-facing surfaces of the skill (`prefLabel`, carrier-facing description, catalog entry text) MUST use `x.klickd` wording. The internal track name (Chimera) MUST NOT appear in any public-facing string.

- **BLOCKER**: any public-facing string contains the literal substring `Chimera` (case-insensitive).
- **PASS**: only internal planning docs and RFC text reference the track name.

### QA-G13 — No Klickd.app / Kai host-side leakage

No artefact may reference Klickd.app product carriers (`klickdapp.<scope>`) or Kai host-side skills (`kai.tutor`, `skill.kai.*`, `core.Kai.klickd`).

- **BLOCKER**: any match against `ARTEFACT_FORBIDDEN_PATTERNS` / `ARTEFACT_FORBIDDEN_REGEXES`.
- **PASS**: validator-enforced.

### QA-G14 — Acceptance tests

The artefact MUST carry `acceptance_criteria[]` and `tests[]` with at least one criterion that maps each competency to an observable carrier-state shape. The criteria MUST be reviewable offline (no live network calls, no licensed-corpus dependency).

- **BLOCKER**: `acceptance_criteria[]` or `tests[]` empty; criteria not reviewable offline.
- **PASS**: every competency mapped to at least one acceptance criterion.

---

## 2. Scoring checklist (per skill, per ship attempt)

Reviewer fills one row per gate. A skill is `ship_ready` only when **all 14 gates are PASS** and any WARN has the sign-off recorded.

| Gate | Status | Sign-off owner | Notes |
|---|---|---|---|
| QA-G01 — Profile coherence | PASS / BLOCKER / WARN | Architecture + UX | one-sentence summary attached |
| QA-G02 — Competency-source traceability | PASS / BLOCKER | Architecture | links opened, anchors resolved |
| QA-G03 — Shared transversal base | PASS / BLOCKER | Architecture | validator output attached |
| QA-G04 — Domain-specific fit | PASS / BLOCKER / WARN | Architecture | overlap report attached if WARN |
| QA-G05 — Memory segment fit | PASS / BLOCKER | Architecture + Security | pointer-only check |
| QA-G06 — Gates + human veto fit | PASS / BLOCKER | Security | action-class coverage table |
| QA-G07 — Source / evidence policy | PASS / BLOCKER | Security | validator output attached |
| QA-G08 — Regulated-output disclaimers | PASS / BLOCKER | Legal/Claims | gate + disclaimer + authority posture |
| QA-G09 — Anti-clone / near-duplicate | PASS / BLOCKER / WARN | Architecture + QA | clone-detector output attached |
| QA-G10 — Size budget | PASS / BLOCKER | Architecture | validator bytes + tokens |
| QA-G11 — No PII / no secrets | PASS / BLOCKER | Security | validator scan output |
| QA-G12 — No forbidden public wording | PASS / BLOCKER | UX + Legal/Claims | grep `(?i)chimera` on public strings |
| QA-G13 — No Klickd.app / Kai leakage | PASS / BLOCKER | Architecture | validator scan output |
| QA-G14 — Acceptance tests | PASS / BLOCKER | QA | criteria-to-competency map |

---

## 3. Required sign-offs

A skill is `ship_ready` only when each of the five sign-off owners records `agreed` against their gates above. Sign-off is one line per owner in the per-pack RFC validation record:

| Owner | Scope (gates) | Sign-off line shape |
|---|---|---|
| **Architecture** | G01, G02, G03, G04, G05, G09, G10, G13 | `architecture: agreed — <reviewer> 2026-MM-DD` |
| **Security** | G05, G06, G07, G11 | `security: agreed — <reviewer> 2026-MM-DD` |
| **Legal / Claims** | G08, G12 | `legal: agreed — <reviewer> 2026-MM-DD` |
| **UX** | G01, G12 | `ux: agreed — <reviewer> 2026-MM-DD` |
| **QA** | G09, G14, full-checklist re-run | `qa: agreed — <reviewer> 2026-MM-DD` |

One human MAY hold multiple owner roles, but each role MUST be signed off independently — a single reviewer cannot self-pair. For `security` / `legal` composes, two distinct reviewers are required (mirrors RFC-009 §8 pair-reviewer rule).

WARN status on any gate requires the relevant owner to record an explicit `acknowledged: <reason>` line; otherwise the WARN escalates to BLOCKER.

---

## 4. Mandatory ordering

The QA protocol runs **after** the C-001..C-012 mapping checklist clears (skill is at `candidate_mapped`) and **before** any `ship_ready` flip. Ordering:

1. **C-001..C-012** clear → status `candidate_mapped`. (Done in [`V4_1_CANDIDATE_CHECKLIST.md`](./V4_1_CANDIDATE_CHECKLIST.md).)
2. **QA-G01..QA-G14** clear → status eligible for `ship_ready`. (This document.)
3. **RFC-009 §8 / §8.1** signed off in the per-pack RFC → status `ship_ready`.
4. **Catalog exposure** is a separate decision (RFC-009 §7).

A skill that reaches step 3 without a complete §2 scoring table + §3 sign-off block in its per-pack RFC is rolled back to `candidate_mapped` automatically — the QA protocol is the merge gate, not an advisory.

---

## 5. Near-duplicate heuristic (validator + manual review)

The validator's exact-clone check (`validate_no_competency_clones`, protocol §3.4) catches the BLOCKER case. The QA protocol additionally requires a **near-duplicate** review.

### 5.1 Mechanical heuristic

The validator computes Jaccard overlap on `competencies[]` (as a frozenset of `competency_ref` strings) for every pair of artefacts **inside the same tier** (Lite vs Lite, Pro vs Pro — cross-tier pairs are not flagged because a Lite/Pro re-anchoring is a legitimate tier shift). Thresholds:

| Overlap | Status | Action |
|---|---|---|
| `1.00` | BLOCKER (exact clone) | merge or remove one of the two |
| `≥ 0.80` | WARN (near-duplicate) | reviewer records task-boundary justification or splits/merges |
| `< 0.80` | PASS | no action |

The heuristic is intentionally simple (set Jaccard, not a tuned embedding distance) to keep false positives low and reviewer trust high. Warnings are advisory — a reviewer who records a justification (author-vs-reader, design-vs-operate, attack-vs-defend, cloud-vs-edge, intake-vs-disclosure) clears the WARN.

The heuristic is implemented as `validate_near_duplicate_competency_sets()` in [`scripts/validate_v4_1_candidate_mapping.py`](../../scripts/validate_v4_1_candidate_mapping.py). The function returns WARN lines (not BLOCKER lines); the validator exit code stays `0` when only WARNs are present, so `ship_ready` promotion is not auto-blocked but the WARN MUST be acknowledged in §2.

### 5.2 Manual near-clone review

Beyond the Jaccard heuristic, the QA reviewer MUST also compare:

- **Gate summaries.** Two skills with identical gate-summary lists are suspect even if their competency sets diverge.
- **Memory segment names.** Two skills with identical segment names + identical pointer schemes are suspect.
- **Carrier statement.** Two skills whose carrier statements collapse to the same role under paraphrase are suspect.

The manual review is a one-minute side-by-side scan; the reviewer attaches the comparison table to the §2 scoring row of G09.

### 5.3 False-positive policy

Near-duplicate WARNs are expected and acceptable; a green near-duplicate report is **not** a sign of validator weakness. A legitimate near-duplicate (e.g. `game-design` author-side vs `game-literacy` reader-side, or `llm-agent-security` defender vs `llm-agent-engineering` builder) is cleared by the task-boundary justification — the WARN exists to force the reviewer to write the justification down, not to block the ship.

---

## 6. As-shipped audit (2026-05-28)

The 42 already-published candidate artefacts (8 Lite + 34 Pro) under [`examples/v4.1/chimera-skills/{lite,pro}/`](../../examples/v4.1/chimera-skills/) are at status `candidate_mapped`, not `ship_ready`. None of them has run the §2 scoring + §3 sign-off pass yet; **none of them is eligible for `/klickdskill` catalog exposure** until that pass exists per per-pack RFC.

The mechanical subset of the QA protocol (G02, G03, G04 BLOCKER half, G06 flags, G07, G09 BLOCKER half, G10, G11, G13) already passes — see the validator output in [`V4_1_COMPETENCY_IDENTIFICATION_PROTOCOL.md`](./V4_1_COMPETENCY_IDENTIFICATION_PROTOCOL.md) §6.

The reviewer-owned half (G01, G05, G06 action-class coverage, G08, G09 WARN half, G12, G14) is the work the per-pack RFC promotion phase will perform — one skill at a time, never as a batch.

---

## 7. See also

- [`README_V4_1.md`](./README_V4_1.md) — planning index, strict mapping rule.
- [`V4_1_SKILL_CANDIDATE_MAPPING.md`](./V4_1_SKILL_CANDIDATE_MAPPING.md) — candidate roster.
- [`V4_1_CANDIDATE_CHECKLIST.md`](./V4_1_CANDIDATE_CHECKLIST.md) — C-001..C-022 reviewer checklist.
- [`V4_1_COMPETENCY_IDENTIFICATION_PROTOCOL.md`](./V4_1_COMPETENCY_IDENTIFICATION_PROTOCOL.md) — competency selection method (admissible sources, coherence rules, anti-clone).
- [`docs/rfcs/RFC-009-chimera-v4.1.md`](../rfcs/RFC-009-chimera-v4.1.md) §8 — `ship_ready` validation contract.
- [`docs/rfcs/ACCEPTANCE_CHECKLIST_V4.md`](../rfcs/ACCEPTANCE_CHECKLIST_V4.md) — promotion gate.
- [`docs/releases/CHECKLIST_v4_preview.md`](../releases/CHECKLIST_v4_preview.md) — release pre-flight checklist.
- [`scripts/validate_v4_1_candidate_mapping.py`](../../scripts/validate_v4_1_candidate_mapping.py) — validator (mechanical subset of QA protocol).
