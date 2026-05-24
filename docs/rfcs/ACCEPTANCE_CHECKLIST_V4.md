# Acceptance Checklist — RFCs targeting `.klickd v4` GA

> **Status:** Draft · NON-NORMATIVE · governance document.
> **Scope:** defines the **explicit, verifiable criteria** that an RFC targeting
> `.klickd v4` GA MUST satisfy to be promoted from `Proposed` to `Accepted`,
> and from `Accepted` to `Implemented`.
>
> This document is **docs-only**. It does not introduce, modify, or remove
> any schema, SDK, vector, or normative SPEC wording. It triggers no publish
> (npm / PyPI / Zenodo), no tag, no release.
>
> Production-recommended format remains **v3.5.1**. Preview track remains
> **v4.0.0-preview.1** (additive, non-normative).

---

## 0. Why this document

After PR #30, three RFCs are in `Proposed`:

- [RFC-001 `media_profile` v1](./RFC-001-media-profile-v1.md)
- [RFC-002 `verification_gates` + `human_veto`](./RFC-002-verification-gates.md) (v1 core)
- [RFC-004 Migration & Backward Compatibility](./RFC-004-migration-backward-compatibility.md)

[`docs/roadmap/ROAD-TO-V4-GA.md`](../roadmap/ROAD-TO-V4-GA.md) §2.1 P0-1 makes
RFC-001/002/004 promotion to `Accepted` a **dependency** of the SPEC v4
normative work. But the [RFC lifecycle table](./README.md#lifecycle) only
states what `Accepted` *means* ("Approved for inclusion in the next normative
SPEC.md revision"), not *how* the decision is made or *what evidence* is
required.

That gap is the reason this checklist exists. Without it, `Proposed → Accepted`
becomes a judgement call dependent on a single maintainer's read of an RFC.
With it, any contributor can audit an RFC against a deterministic list and
either:

- assert the RFC is ready and open a promotion PR, or
- point at a specific unchecked item that must land first.

This is consistent with [`ROAD-TO-V4-GA.md`](../roadmap/ROAD-TO-V4-GA.md) §3.10
("Doc d'abord" — docs / promoted RFC precedes the code PR for any P0 chantier).

---

## 1. What this checklist is NOT

To keep promotion gated on substance rather than ceremony, this checklist
explicitly excludes the following:

- **Not a vote.** Promotion is a maintainer decision. The checklist makes the
  decision *legible*, not *automatic*.
- **Not a publication gate.** Promotion to `Accepted` does NOT trigger any
  npm / PyPI / Zenodo publish, any git tag, or any IANA action.
- **Not a backward-compat freeze.** An `Accepted` RFC can still be amended
  by a follow-up RFC (`Superseded by RFC-NNN`) if implementation experience
  reveals a gap.
- **Not a substitute for the RFC body.** The checklist is a gate; the RFC
  itself remains the authoritative source for normative wording.

---

## 2. Promotion lifecycle (reminder)

```
Draft  →  Proposed  →  Accepted  →  Implemented
                  ↘   ↘
              Withdrawn / Superseded by RFC-NNN
```

| Transition | Authority | This checklist | Reference |
|---|---|---|---|
| `Draft → Proposed` | Author + 1 maintainer | not required | RFCs §3, RFC author judgement |
| `Proposed → Accepted` | Maintainer (Vince) | **Required — §3 below** | this document |
| `Accepted → Implemented` | Maintainer | **Required — §4 below** | this document |

---

## 3. `Proposed → Accepted` — checklist

An RFC currently in `Proposed` MUST satisfy **every** item below before being
promoted to `Accepted`. Each item is intentionally objective: either it is
true of the RFC's current text, or it is not.

### 3.1 Normative discipline

- [ ] **C1. RFC 2119 language is explicit.** Every MUST / SHOULD / MAY is
      uppercased and clearly distinguishes normative requirements from
      illustrative examples.
- [ ] **C2. No "TBD" / "TODO" in normative sections.** Open decisions are
      explicitly listed in a dedicated section (e.g. `§N — Open decisions`)
      and tagged as **non-blocking** for `Accepted`.
- [ ] **C3. Status block reflects reality.** The RFC's top status table shows
      `Status: Accepted` only after the promotion PR merges. Until then it
      MUST stay `Proposed`.

### 3.2 Surface freeze

- [ ] **C4. The frozen surface is enumerated.** The RFC's "Status note"
      section names the sections that this promotion freezes (e.g. for
      RFC-001 the §4 decisions, §5 illustrative schema, §6 V-001…V-012,
      §9 error codes). A reader can answer the question "what is now frozen?"
      without ambiguity.
- [ ] **C5. Out-of-scope additions are explicit.** Anything **not** frozen
      by this promotion is named (e.g. RFC-002 §8b v2 additions remain
      `Draft`). No silent expansion of scope at `Accepted`.

### 3.3 Cross-RFC and cross-doc coherence

- [ ] **C6. Dependencies on other RFCs are stated.** If the RFC depends on
      another RFC's frozen surface (e.g. RFC-004 reader/writer matrix vs
      RFC-001 `media_profile`), the dependency is listed and the depended-on
      RFC is `Proposed` or later.
- [ ] **C7. [`SCHEMA_INDEX.md`](../../SCHEMA_INDEX.md) is consistent.** The
      schema-index page reflects the RFC's `Accepted` status (preview vs
      normative, `additionalProperties` policy). A docs-only update to
      `SCHEMA_INDEX.md` MAY ship in the same PR.
- [ ] **C8. [`docs/rfcs/README.md`](./README.md) is consistent.** The RFC
      index table reflects the new status, the date of promotion, and any
      "v1 core vs v2 draft" distinction (cf. RFC-002).
- [ ] **C9. [`CHANGELOG.md`](../../CHANGELOG.md) has a `docs-only` entry.**
      The promotion is recorded under the current `Unreleased — docs-only`
      block with the date, the RFCs affected, and an explicit statement that
      no SDK / schema / vector changed.

### 3.4 Reference material

- [ ] **C10. At least one non-normative example exists or is referenced.**
      Either `docs/rfcs/examples/*.json`, or a fixture in `tests/` that the
      RFC's authors can point to. The example is clearly labelled
      *non-normative*. (For RFC-004, "example" = a sample
      `migration_report` shape, not a real migrated file.)
- [ ] **C11. Open decisions section is preserved verbatim.** If §N "Open
      decisions" exists at `Proposed`, the same items remain listed at
      `Accepted` unless explicitly resolved in the same PR with a one-line
      rationale.

### 3.5 Safety invariants

- [ ] **C12. No `locked_*` change.** Promotion does not introduce or modify
      `locked_ethics`, `locked_actions`, or any other `locked_*` field. (Cf.
      [`ROAD-TO-V4-GA.md`](../roadmap/ROAD-TO-V4-GA.md) §3.9.)
- [ ] **C13. No unknown-field-preservation regression.** Any wording added or
      modified continues to require verbatim preservation of unknown fields
      across reader/writer boundaries. (Cf. SPEC §33.7, RFC-004 §7.)
- [ ] **C14. No publish trigger.** The promotion PR introduces no workflow,
      tag, or CI step that publishes to npm `latest`, PyPI stable, Zenodo,
      or IANA. (Cf. [`ROAD-TO-V4-GA.md`](../roadmap/ROAD-TO-V4-GA.md) §3.4.)

### 3.6 Reviewer attestation

- [ ] **C15. Maintainer sign-off.** A maintainer (Vince) leaves an explicit
      `Accept` comment on the promotion PR, referencing this checklist.
- [ ] **C16. CI is green.** All existing CI checks (`test-vectors`,
      `verify-npm-preview`, and any RFC-related lint) pass on the promotion
      PR head commit.

> **All 16 items MUST be checked.** A single failing item blocks the
> promotion. The author of the promotion PR is responsible for either
> checking the box or amending the RFC to make the box checkable.

---

## 4. `Accepted → Implemented` — checklist

An `Accepted` RFC becomes `Implemented` when its normative content is
reflected in `SPEC.md` AND in the reference SDKs AND in the test vectors.
This is the bar that produces real downstream effects.

- [ ] **I1. SPEC.md merge.** The RFC's normative text is incorporated into
      `SPEC.md` (or `SPEC_v4.md` if the maintainer chooses a separate file).
      The RFC keeps its `Implemented` status as a historical record but
      defers to SPEC for the canonical wording.
- [ ] **I2. Strict JSON Schema lands.** The relevant `schema/` and `schemas/`
      files declare the section under `additionalProperties: false` (or the
      explicitly motivated exception). Preview schemas remain available
      until sunset.
- [ ] **I3. Python SDK API exposes the section.** `packages/pypi/klickd/`
      offers a typed public API for the RFC's section. 100 % of the related
      vectors validate. v3.x regression remains zero.
- [ ] **I4. JS/TS SDK parity.** `packages/@klickd/core/` matches the Python
      SDK on the same vectors, cross-implementation tests are green.
- [ ] **I5. Strict vectors exist.** `tests/vectors_v40.json` (and / or
      `tests/negative_vectors_v40.json`) covers at least one positive and
      one negative vector for every MUST in the RFC.
- [ ] **I6. Migrator handles legacy.** RFC-004's pipeline preserves any
      pre-existing instance of the RFC's section verbatim; rollback works
      end-to-end. (Applies to RFCs that introduce new payload sections.)
- [ ] **I7. CHANGELOG promotes to a real version line.** The change leaves
      the `Unreleased — docs-only` block and lands under a versioned section
      (`v4.0.0-rc.*` or `v4.0.0`). This step happens **once per GA**, not per
      RFC.
- [ ] **I8. Maintainer sign-off for `Implemented` transition.** Same as C15
      but for the implementation PR (or PR series).
- [ ] **I9. No publish triggered by the transition itself.** GA publish
      (npm `latest`, PyPI stable, Zenodo, IANA) is a **separate manual
      decision** by the maintainer, gated on every `Accepted → Implemented`
      checklist being green for every P0 RFC. (Cf.
      [`ROAD-TO-V4-GA.md`](../roadmap/ROAD-TO-V4-GA.md) §3.4 and §4 step 10.)

---

## 5. How to use this checklist in a PR

A "promote RFC-NNN to `Accepted`" PR SHOULD follow this template:

```
Title: rfc(v4): promote RFC-NNN from Proposed to Accepted

Summary
- Promotes RFC-NNN (<short title>) from Proposed to Accepted (docs-only).
- No SDK / schema / vector changes.

Acceptance checklist (docs/rfcs/ACCEPTANCE_CHECKLIST_V4.md §3)
- [x] C1 RFC 2119 language explicit
- [x] C2 No TBD / TODO in normative sections
- [x] C3 Status block updated
- [x] C4 Frozen surface enumerated
- [x] C5 Out-of-scope additions explicit
- [x] C6 RFC dependencies stated
- [x] C7 SCHEMA_INDEX.md consistent
- [x] C8 docs/rfcs/README.md consistent
- [x] C9 CHANGELOG.md docs-only entry added
- [x] C10 Non-normative example referenced
- [x] C11 Open decisions preserved verbatim
- [x] C12 No locked_* change
- [x] C13 No unknown-field-preservation regression
- [x] C14 No publish trigger
- [x] C15 Maintainer sign-off requested
- [x] C16 CI green
```

A reviewer who finds any unchecked box is expected to **block merge** until
the box can be checked.

---

## 6. Open questions (non-blocking for this checklist)

- **Q1.** Should `Accepted` require a community review window (e.g. 7 days
  on `Proposed` before promotion)? Currently optional, left to maintainer
  judgement. May be added later if multiple promotions land too quickly.
- **Q2.** Should `Implemented` require a citation to the SPEC.md section
  (e.g. SPEC §34.2.1) in the RFC's status block? Probably yes once `SPEC v4`
  shape stabilises. Tracked under [P0-1](../roadmap/ROAD-TO-V4-GA.md#p0-1--spec-normative-v4).
- **Q3.** Should this checklist itself live under `docs/rfcs/` (current
  choice — close to the RFCs it gates) or under `docs/governance/`? Open
  to relocation if a wider governance directory appears.

These questions do not block the use of the checklist as written.

---

*Living document. Any change to the checklist itself MUST land via a PR,
referencing the rationale.*
