# R4-P0-4 — `.klickd` v4 Deprecation Policy (Normative)

> **Status:** NORMATIVE (V4 P0). Docs-only normative companion to
> [R4-P0-1](./R4-P0-1-onboarding-wizard.md),
> [R4-P0-2](./R4-P0-2-error-i18n-table.md), and to [SPEC.md](../../SPEC.md).
> This document uses **RFC 2119 / RFC 8174** key words (MUST, MUST NOT,
> SHALL, SHOULD, SHOULD NOT, MAY, RECOMMENDED) as defined therein.
>
> **Scope:** this document binds the **deprecation lifecycle** of every
> field, block, sub-field, enum value, and registry identifier that
> appears, has appeared, or will appear in a `.klickd` envelope or
> payload at any version starting with v4 (`klickd_version` major
> component `>= 4`). It defines what it means for a field to be
> `active`, `deprecated`, or `removed`; the conditions under which a
> field MAY transition between those states; the reader and writer
> behaviour required for each state; and how the registry layer
> (domain profiles, competency templates, personality vocabulary)
> interacts with the policy.
>
> It does **not** introduce any new on-the-wire field that is
> required by a reader to function. The informational
> `deprecated_fields[]` envelope block defined in §6 is **OPTIONAL**,
> **additive**, and MUST be silently ignored by readers that do not
> understand it (per §33.7 of [SPEC.md](../../SPEC.md) and per
> [RFC-004](../rfcs/RFC-004-migration-backward-compatibility.md)).
>
> **Out of scope (tracked elsewhere):** strict schema enforcement
> ([P0-2](../roadmap/ROAD-TO-V4-GA.md)), SDK alignment
> ([P0-3 / P0-4](../roadmap/ROAD-TO-V4-GA.md)), cross-impl vectors
> ([P0-6](../roadmap/ROAD-TO-V4-GA.md)), migration runtime
> ([RFC-004](../rfcs/RFC-004-migration-backward-compatibility.md)),
> the §33 field surface promotion itself ([R4-P0-1](../roadmap/ROAD-TO-V4-GA.md)).

---

## 1. Why this is normative now

`.klickd` v3.2 → v3.4 added 26 fields without an explicit exit
policy. The cost of that omission is now visible:

- agent readers hallucinate fields that were never specified because
  the schema offers no canonical list of fields **about to leave**;
- writers cannot signal to downstream readers that a field they emit
  is going away, forcing breaking removals or indefinite carriage of
  dead surface area;
- the schema grows monotonically — the textbook **A4 (schema
  inflation)** anti-pattern documented in
  [ROAD-TO-V4-GA §2.3 A4](../roadmap/ROAD-TO-V4-GA.md) and in
  [`V4-UX-DX-RESEARCH-NOTES.md`](../roadmap/V4-UX-DX-RESEARCH-NOTES.md) §2.

Promoting only the **deprecation lifecycle contract** to normative —
not new SDK APIs, not new required fields, not a schema strictness
upgrade — is the minimum intervention that gives v4 a credible exit
path for fields and unblocks the §33 field-surface promotion
([R4-P0-1](../roadmap/ROAD-TO-V4-GA.md)) and the future strict v4
schema ([P0-2](../roadmap/ROAD-TO-V4-GA.md)).

This policy is **forward-only**: it governs v4+ fields. v3.x
fields retain the *de facto* lifecycle they already had (see §11);
this document does not retroactively re-classify v3.x fields.

---

## 2. Terminology

- **Field.** Any named element addressable by a JSON pointer inside
  a `.klickd` envelope or payload. The term covers top-level keys
  (e.g. `memory`), nested keys (e.g. `ethics.locked_actions`), enum
  values (e.g. `verification_gates.factual_claim_about_person =
  "block"`), and registry identifiers (e.g. competency template ID
  `HSE:WM-001`). When this document says "field", it means any of
  these unless the text says otherwise.
- **Lifecycle state.** One of `active`, `deprecated`, `removed`.
  Defined in §3. A field is in exactly one lifecycle state at any
  given v4 version.
- **Carry version.** The `klickd_version` at which a field was
  introduced in the `active` state.
- **Deprecation version.** The `klickd_version` at which a field
  transitions from `active` to `deprecated`.
- **Removal version.** The `klickd_version` at which a field
  transitions from `deprecated` to `removed`.
- **Conforming v4 reader.** A reader that advertises support for
  `klickd_version` with major component `4`. A conforming v4 reader
  MUST implement every reader behaviour listed in §4 of this
  document.
- **Conforming v4 writer.** A writer that emits files with
  `klickd_version` major component `4`. A conforming v4 writer MUST
  implement every writer behaviour listed in §5 of this document.
- **Reference corpus.** The union of `tests/vectors_v40*.json`,
  `examples/v4/**`, and the registry under `registry/`. Usage
  measurement for §3.2 is performed against this corpus. No
  production telemetry is collected, ever (per
  [SPEC.md §33.10](../../SPEC.md) and
  [SECURITY.md](../../SECURITY.md)).
- **Safety / locked fields.** Fields explicitly enumerated in §9.
  These fields are governed by additional rules and MUST NOT be
  deprecated or removed via the ordinary lifecycle.

---

## 3. Lifecycle states

Every v4 field is in exactly one of three lifecycle states.

### 3.1 `active`

The default initial state of every newly introduced v4 field.

- Writers MAY emit the field. Whether the field is `OPTIONAL` or
  `REQUIRED` for a given profile is governed by the SPEC body and
  the strict schema (P0-2), not by this document.
- Readers MUST interpret the field per the SPEC definition.
- The field MUST appear in the canonical list maintained in the
  SPEC body (the section promoted via R4-P0-1) and, where
  applicable, in the strict v4 schema (P0-2).

### 3.2 `deprecated`

A field MAY transition from `active` to `deprecated` when **all** of
the following conditions are met. These conditions are normative
gates on the transition itself; they are not optional.

1. The field has been `active` for at least **two minor v4
   versions** counted from its carry version — i.e. its deprecation
   version's `minor` component MUST be at least `carry_version.minor
   + 2`. Phrased as the rule from the backlog: a field is eligible
   for `deprecated` marking **after Vx+2** versions.
2. The field's observed usage in the reference corpus is **strictly
   less than 10%** of the relevant denominator. The denominator is
   defined in §3.2.1.
3. A **migration path** is documented (§7), or the field's removal
   is information-preserving (i.e. the field's semantics are fully
   recoverable from other fields without loss; this MUST be argued
   explicitly in the deprecation PR).
4. The field is **not** a safety / locked field (§9).
5. A **RFC** or **R4-Pn-m** track exists that justifies the
   deprecation. The justification MUST cite the empirical usage
   measurement (the <10% number) and the migration path.

The "Vx+2 OR <10% usage" formulation in the backlog
([ROAD-TO-V4-GA §R4-P0-4](../roadmap/ROAD-TO-V4-GA.md))
is hereby normatively refined to "**Vx+2 AND <10% usage**": both
conditions MUST be met. The disjunction in the backlog text is
treated as an **example** of the threshold class, not as the
operative rule. Either of the two conditions alone is insufficient
to deprecate a field, because (a) age alone does not establish that
the field is unused, and (b) low usage in a young field is the
expected state during the introduction phase and MUST NOT trigger
premature deprecation. The combined gate prevents both
forms of premature removal.

The two conditions MAY be relaxed only by an explicit, dedicated
RFC that supersedes this section for a single field. Such an RFC
MUST be `Accepted` before the deprecation PR is opened.

#### 3.2.1 Usage measurement

The denominator for the <10% threshold is the number of distinct
**files** in the reference corpus that would be syntactically
eligible to carry the field (i.e. files of the right profile kind
and version). The numerator is the number of those files that
actually carry the field with a non-empty value.

- "Non-empty" means: not `null`, not `""`, not `[]`, not `{}` —
  unless the SPEC explicitly defines an empty value as semantically
  meaningful for that field, in which case the SPEC's definition
  governs.
- The measurement MUST be reproducible by running the corpus
  validation scripts under `tests/` and is RECOMMENDED to be
  recorded in the deprecation PR description (so reviewers can
  re-run it).
- No measurement is taken against real user files. The reference
  corpus is the only authoritative usage signal.

### 3.3 `removed`

A field MAY transition from `deprecated` to `removed` when **all**
of the following conditions are met:

1. The field has been `deprecated` for at least **two minor v4
   versions** counted from its deprecation version. A field
   deprecated at v4.x MAY be removed no earlier than v4.(x+2).
2. The migration path (§7) has shipped in at least one conforming
   v4 SDK (i.e. the migrator can rewrite the deprecated field into
   its replacement without user intervention).
3. The field is **not** a safety / locked field (§9).
4. No file in the reference corpus still carries the field with a
   non-empty value. (i.e. the migrator has run against the corpus
   and the deprecated field is gone from `examples/v4/**` and from
   the v4 vectors that are not specifically *deprecation
   regression* vectors.)
5. A **release notes** entry exists for the removal, naming the
   field, the deprecation version, the removal version, and the
   migration path used.

A removal MUST NOT skip the `deprecated` phase. The transition
`active → removed` directly is forbidden by this document. If a
field is judged dangerous and must leave immediately, the operative
move is to (a) deprecate it in the next minor and (b) ship the
migrator in the same release; the field still passes through
`deprecated` for at least one minor.

A field that has been `removed` MUST NOT be re-introduced under the
same name in a later v4 release. If the same semantic surface is
re-introduced, it MUST carry a different field name. This rule
prevents readers that still understand the removed field from
silently mis-interpreting a re-introduction with subtly different
semantics.

---

## 4. Reader behaviour

A conforming v4 reader MUST implement the behaviour defined in this
section for every field it encounters, regardless of whether the
reader has been updated to know about that field's specific
lifecycle state.

### 4.1 `active` fields

A v4 reader MUST interpret `active` fields per the SPEC.

### 4.2 `deprecated` fields

A v4 reader MUST:

1. **Read the field silently.** A conforming reader MUST accept a
   `deprecated` field as input and interpret its semantics per the
   SPEC definition in effect at the field's deprecation version.
   "Silently" means: the reader MUST NOT raise an error, MUST NOT
   refuse to open the file, and MUST NOT degrade the file's other
   semantics because of the deprecated field's presence.
2. **Preserve the field on round-trip.** If the reader re-emits the
   file (e.g. after editing other fields), it MUST carry the
   deprecated field through verbatim, byte-for-byte under JCS
   canonicalisation. This is a strict extension of the unknown-field
   preservation rule already required by
   [SPEC.md §33.7](../../SPEC.md) and reaffirmed in §10 below.
3. **Surface a developer-visible signal, never a user-visible
   error.** The reader MAY emit a deprecation log entry (level:
   `info` or `warn`, never `error`) addressed to the developer /
   operator. The reader MUST NOT surface a `KLICKD_E_*` user-facing
   error code (per
   [R4-P0-2](./R4-P0-2-error-i18n-table.md)) solely because a
   deprecated field is present. Deprecation is not a failure
   condition for the end-user.
4. **Treat the field's value as authoritative within its scope.** A
   reader MUST NOT silently rewrite a deprecated field's value to a
   replacement field's value at read time. Such a rewrite is a
   **migration** and is governed by
   [RFC-004](../rfcs/RFC-004-migration-backward-compatibility.md);
   it MUST be explicit, logged, and produce a `migration_report`.

A reader that fails to preserve a deprecated field on round-trip is
**non-conforming** with v4 and MUST NOT advertise v4 support.

### 4.3 `removed` fields

A v4 reader MUST:

1. **Preserve the field verbatim.** A removed field encountered in
   an input file MUST be carried through round-trip exactly like
   any other unknown field. The reader MUST NOT strip it. This
   protects against the case where the file was produced by an
   older v4 writer or by a parallel implementation that still
   knows the field.
2. **Not interpret the field's semantics.** Once removed, the
   field has no SPEC meaning for this reader. The reader MUST NOT
   apply the field's former semantics to the file's behaviour.
3. **Not surface a user-facing error.** As in §4.2, encountering a
   removed field is not, on its own, a failure condition for the
   end-user.
4. **Refer to the SPEC's removed-fields registry** (§8) when the
   reader's operator asks "what is this field?". The registry is
   the canonical place where removed fields are documented with
   their carry version, deprecation version, removal version, and
   migration path.

### 4.4 Strict mode

A v4 reader MAY offer an OPTIONAL **strict mode** that, when
explicitly enabled by the operator, treats the presence of a
deprecated or removed field as a non-fatal warning surfaced
programmatically (NOT as a `KLICKD_E_*` user-facing error). Strict
mode MUST NOT be the default. Strict mode MUST NOT refuse to open
the file solely because of the lifecycle state of one or more of
its fields.

---

## 5. Writer behaviour

A conforming v4 writer MUST implement the behaviour defined in this
section.

### 5.1 `active` fields

A v4 writer MAY emit `active` fields per the SPEC. The strict
schema (P0-2) governs which `active` fields are `REQUIRED` for a
given profile; this document does not.

### 5.2 `deprecated` fields

A v4 writer:

1. **MUST NOT emit a `deprecated` field in a newly authored file**
   when a replacement field exists and the writer is aware of it.
   "Newly authored" means: the file is produced from user input or
   from an importer that has no pre-existing v4 source file. A
   writer that emits a deprecated field in a newly authored file is
   non-conforming.
2. **MUST preserve a `deprecated` field on round-trip** when the
   input file already carried it. Preservation is byte-for-byte
   under JCS canonicalisation, and the obligation is strictly
   stronger than the §10 unknown-field rule: even a writer that
   knows the field is deprecated MUST NOT strip it on round-trip
   unless the writer is explicitly performing a migration (see §7).
3. **SHOULD emit a developer-visible deprecation log** when it
   round-trips a deprecated field, naming the field and pointing
   to the migration path. This log is for the developer / operator,
   never for the end-user.
4. **MAY** populate the informational `deprecated_fields[]`
   envelope block (§6) when round-tripping a file that carries
   deprecated fields. Populating the block is OPTIONAL and is never
   the reader's input signal for deciding whether a field is
   deprecated — the SPEC and the registry (§8) are.

### 5.3 `removed` fields

A v4 writer MUST NOT emit a removed field in a newly authored file.
On round-trip from a file that still carries the field, the writer
MUST preserve it verbatim (per §4.3) unless the writer is
performing a migration that explicitly rewrites the field.

### 5.4 Migration writers

A writer that performs a migration (e.g. v4.x → v4.(x+2) where a
field is removed) MUST follow the migration contract defined by
[RFC-004](../rfcs/RFC-004-migration-backward-compatibility.md):

- the source file MUST NOT be overwritten in place;
- a `migration_report` MUST be produced;
- a backup of the source file MUST be retained;
- the migration MUST be opt-in.

This document does not relax any of those obligations.

---

## 6. The informational `deprecated_fields[]` envelope block

The v4 envelope MAY carry an OPTIONAL top-level array
`deprecated_fields[]` whose purpose is **documentary**. Each entry
is an object naming a field that the writer believes is in the
`deprecated` lifecycle state at the file's `klickd_version`.

```json
{
  "klickd_version": "4.x.y",
  "deprecated_fields": [
    {
      "path": "memory.struggles",
      "deprecated_since": "4.2.0",
      "replacement": "memory.struggles_v2",
      "migration_ref": "RFC-004#memory-struggles-v2"
    }
  ]
}
```

### 6.1 Behaviour rules

`deprecated_fields[]` is:

1. **Informational only.** A reader MUST NOT reject a file solely
   because `deprecated_fields[]` lists or omits a given field.
2. **Non-authoritative.** The authoritative list of deprecated
   fields is the **SPEC body** and the **registry** (§8), not the
   per-file array. A reader MUST NOT consult `deprecated_fields[]`
   as the source of truth for lifecycle state.
3. **OPTIONAL and additive.** A v4 file is fully conforming with
   or without `deprecated_fields[]`. A v3.x reader MUST ignore the
   block per the existing unknown-field rule
   ([SPEC.md §6, §33.7](../../SPEC.md)).
4. **Self-describing only.** A writer that populates the block
   describes its own beliefs about the file it just wrote, not
   claims about other files or about the future.
5. **Never a rejection signal.** A reader MUST NOT use the block to
   refuse to open the file, to invalidate other fields, or to
   surface a user-facing error
   ([R4-P0-2](./R4-P0-2-error-i18n-table.md)).

### 6.2 Schema contribution

The informational `deprecated_fields[]` block is the **only** new
schema surface introduced by this document, and it is OPTIONAL.
This document does not add any required field, and it does not
modify any existing field's type or required-ness. Adding the block
to the strict v4 envelope schema (P0-2) is a docs-aligned schema
patch with `additionalProperties: true` semantics; it MUST NOT be
exploited to inflate the schema with sibling fields.

---

## 7. Migration guidance

When a v4 field is deprecated, the deprecation PR MUST document
exactly one of the following migration outcomes for the field:

### 7.1 Replacement field

The field is being superseded by another field with overlapping
semantics. The deprecation PR MUST:

- name the replacement field;
- specify whether the replacement is **field-equal**
  (same type, same semantics, different name — e.g. rename),
  **field-narrowing** (the replacement covers a subset and the
  remainder is no longer expressible), or **field-widening** (the
  replacement covers a superset and the deprecated field's values
  map injectively into it);
- specify the transformation rule between the two, in pseudocode
  precise enough that two independent implementations produce
  byte-equal post-migration files under JCS canonicalisation;
- supply at least one positive vector and one negative vector
  exercising the migration (added to
  [`tests/`](../../tests/) per the P0-6 contract).

### 7.2 Information-preserving removal

The field's semantics are recoverable from other fields without
loss. The deprecation PR MUST argue this point explicitly, naming
the carrying fields and showing the recovery rule. The argument
MUST be auditable: a reader implementing the recovery rule SHOULD
produce identical downstream behaviour to a reader still consuming
the deprecated field.

### 7.3 Information-lossy removal

The field's semantics are **not** fully recoverable. This case
requires an explicit **change of claim** in the deprecation PR:

- the PR MUST name the user-visible behaviour change;
- the PR MUST justify why the loss is acceptable (typically:
  privacy, safety, or a corrected over-promise);
- migrating writers MUST surface a user-facing notice (per
  R4-P0-2's error contract — `info` or `warn`, never silent) that
  the field's information is being discarded.

Information-lossy removals are the **exceptional** path, not the
default. The deprecation PR MUST justify why §7.1 and §7.2 were
not applicable.

### 7.4 Migration report

In all three cases, the migration runtime (when it runs) MUST emit
a `migration_report` per
[RFC-004](../rfcs/RFC-004-migration-backward-compatibility.md). The
report MUST name the deprecated field, the migration outcome
(§7.1 / §7.2 / §7.3), and the source / destination versions. This
is consistent with the **A2 (silent migration)** anti-pattern
guardrail in
[ROAD-TO-V4-GA §2.3 A2](../roadmap/ROAD-TO-V4-GA.md).

---

## 8. Removed-fields registry

The SPEC body (the section promoted via R4-P0-1) MUST maintain a
**removed-fields registry**: a table that lists, for every v4
field that has reached the `removed` state, the following columns:

| Column | Meaning |
|---|---|
| `path` | JSON pointer to the field. |
| `carry_version` | `klickd_version` at which the field was introduced. |
| `deprecated_at` | Deprecation version. |
| `removed_at` | Removal version. |
| `migration_outcome` | One of `replacement` (§7.1), `information_preserving` (§7.2), `information_lossy` (§7.3). |
| `migration_ref` | Stable reference to the migration rule (RFC anchor or PR commit). |

The registry is the **authoritative** answer to the reader question
"what does this field mean?". The per-file `deprecated_fields[]`
block (§6) is documentary only; the registry is normative.

Until the §33 field surface is promoted (R4-P0-1), the registry
lives in this document as an empty table to be filled by future
deprecation PRs:

| `path` | `carry_version` | `deprecated_at` | `removed_at` | `migration_outcome` | `migration_ref` |
|---|---|---|---|---|---|
| *(none yet — v4 has no removed fields at policy adoption.)* | | | | | |

The registry MUST be moved into the normative SPEC body in the same
PR that promotes §33 to normative (R4-P0-1 follow-up). At that
point, this section becomes a pointer to the SPEC body.

---

## 9. Safety / locked fields exception

The following fields are **safety-critical** or carry **locked
semantics** that the user has explicitly committed to. They are
exempt from the ordinary lifecycle defined in §3 and MUST NOT be
deprecated or removed via this document's mechanisms:

- `ethics.locked_actions` and every element therein (per
  [SPEC.md §240 / RFC-002 §275](../../SPEC.md) — `verification_gates`
  MUST NOT weaken `ethics.locked_actions`);
- `decisions_locked[]` (per [SPEC.md §240](../../SPEC.md));
- the envelope cryptographic blocks `kdf` and `cipher` and all
  their sub-fields (per [SPEC.md §33.10 invariant 2](../../SPEC.md));
- the `data_integrity.integrity_warning` field (per
  [SPEC.md §1221](../../SPEC.md) — safety-critical surface);
- the AAD canonical envelope-field set (per the v3.x envelope
  contract carried forward into v4).

Any proposal to retire or rename one of these fields is a
**dedicated RFC** that supersedes this document for the specific
field in question. Such an RFC MUST cite, at minimum, the §33.10
invariants ([SPEC.md](../../SPEC.md)) and the
[SECURITY.md](../../SECURITY.md) threat model, and MUST be
`Accepted` before any code change that touches the field is merged.
The dedicated RFC is **not** a relaxation of this document for the
field class; it is a separate normative track.

This rule is the operative form of **governance rule §9** in
[ROAD-TO-V4-GA §3](../roadmap/ROAD-TO-V4-GA.md) ("`locked` non
modifiable").

---

## 10. Interaction with unknown-field preservation

The unknown-field preservation rule already required by
[SPEC.md §6 and §33.7](../../SPEC.md) — "a v4-preview reader that
does not understand a field MUST carry it through verbatim, not
strip it" — composes with this document as follows:

| Reader's knowledge of the field | Lifecycle state | Reader behaviour |
|---|---|---|
| Known | `active` | Interpret per SPEC. Preserve on round-trip. |
| Known | `deprecated` | Interpret per SPEC (§4.2). Preserve on round-trip. MAY log developer-visible deprecation notice. |
| Known | `removed` | Do NOT interpret. Preserve verbatim on round-trip (§4.3). |
| Unknown | (any) | Preserve verbatim on round-trip per [SPEC.md §6, §33.7](../../SPEC.md). |

In other words: **preservation is unconditional**. The lifecycle
state changes whether the reader *interprets* a field, never
whether the reader *carries* it. This separation is what allows the
ecosystem to retire fields without breaking files in the wild and
without breaking the parallel-implementation contract.

A reader that strips a deprecated field, a removed field, or an
unknown field on round-trip is **non-conforming** with v4 and MUST
NOT advertise v4 support, regardless of which of the three buckets
the field falls into.

---

## 11. Semantic versioning rules for `.klickd` v4+

This document binds the following semantic versioning interpretation
to `klickd_version` for v4+. It refines, and does not replace, the
v3.x conventions documented in [SPEC.md §1 / §4](../../SPEC.md) and
in [CHANGELOG.md](../../CHANGELOG.md).

### 11.1 Major (`4.* → 5.*`)

A major version bump is REQUIRED when:

- a field changes type incompatibly without a deprecation path
  (forbidden in v4 by §3.3; only an emergency RFC can authorise
  this at a major boundary);
- the envelope cryptographic contract changes (KDF, cipher, AAD
  composition);
- the unknown-field preservation rule (§10) is amended;
- a safety / locked field (§9) is retired (forbidden by §9 unless
  a dedicated RFC is `Accepted` AND the change is timed for a
  major boundary).

A major bump is the ONLY place at which the parallel-implementation
contract may be broken. v4 readers MUST NOT be expected to read
v5 files. v5 readers MUST be able to read v4 files in read-only
compatibility mode (per [RFC-004](../rfcs/RFC-004-migration-backward-compatibility.md))
unless the major bump's RFC explicitly forbids this.

### 11.2 Minor (`4.x → 4.(x+1)`)

A minor version bump is REQUIRED when:

- a new `active` field is added;
- a field transitions `active → deprecated` (§3.2);
- a field transitions `deprecated → removed` (§3.3);
- the strict schema (P0-2) tightens a constraint in a way that
  rejects files that older v4 minor versions accepted.

A minor bump MUST NOT break the unknown-field preservation rule,
MUST NOT retire a safety / locked field, and MUST NOT change the
envelope cryptographic contract.

### 11.3 Patch (`4.x.y → 4.x.(y+1)`)

A patch version bump is REQUIRED when:

- a normative document (this one,
  [R4-P0-1](./R4-P0-1-onboarding-wizard.md),
  [R4-P0-2](./R4-P0-2-error-i18n-table.md), the §33 promotion)
  changes prose without adding or removing schema surface;
- a bug in a reference implementation is fixed without changing
  the wire format;
- additional vectors are added that document existing behaviour.

Patch bumps MUST NOT alter the lifecycle state of any field.

### 11.4 Pre-release suffixes

Pre-release suffixes (`-preview.1`, `-rc.1`) MAY appear during the
v4 P0 chantier per the existing convention. A pre-release version
is **outside** the deprecation lifecycle of this document: fields
introduced in a pre-release MAY be removed before the corresponding
GA minor with no deprecation cycle, **provided** the removal ships
before GA. Once GA ships, this document governs.

---

## 12. Change proposal process

A proposal to transition a field's lifecycle state is governed by
the following process. The process is intentionally aligned with
the existing RFC / R4-Pn-m discipline so that no new governance
machinery is created.

### 12.1 `active → deprecated`

1. Open an RFC (status `Draft`) or a backlog item under
   [ROAD-TO-V4-GA](../roadmap/ROAD-TO-V4-GA.md) explicitly naming
   the field, the deprecation rationale, the measured corpus usage,
   and the migration outcome (§7.1 / §7.2 / §7.3).
2. The RFC / backlog item MUST be `Accepted` before the
   deprecation PR is opened.
3. The deprecation PR updates the SPEC body (or this document, for
   fields under the registry) to mark the field `deprecated` and
   adds the field to the removed-fields registry (§8) with
   `removed_at` left blank.
4. The deprecation PR MUST update [CHANGELOG.md](../../CHANGELOG.md)
   and MUST cite the corpus usage measurement.
5. The deprecation PR MUST add at least one positive vector
   verifying that a v4 reader still reads files carrying the
   deprecated field without error.

### 12.2 `deprecated → removed`

1. Verify that all §3.3 conditions are met. The verification MUST
   be reproducible (re-run the corpus check).
2. Open the removal PR. The PR MUST update the removed-fields
   registry with the removal version and MUST cite the migration
   PR(s) that shipped the migrator.
3. The removal PR MUST add at least one positive vector verifying
   that a v4 reader still **preserves** the now-removed field on
   round-trip (per §4.3 / §10).
4. The removal PR MUST update [CHANGELOG.md](../../CHANGELOG.md).
5. The removal PR MUST NOT delete prior vectors that exercise the
   field's former semantics; those become **deprecation regression
   vectors** and are retained for the audit trail.

### 12.3 Emergency removal

If a field is judged dangerous (privacy leak, safety incident,
cryptographic flaw), the field MAY be deprecated immediately in
the next available release **and** the migrator MAY ship in the
same release. The field still passes through `deprecated` for at
least one minor version (per §3.3) — i.e. the field MUST NOT skip
the `deprecated` phase, but the dwell time at `deprecated` MAY be
the minimum permitted by §3.3. The emergency RFC justifying the
expedited timeline MUST cite the safety incident or the
cryptographic / privacy threat that motivates the expedited path
and SHOULD reference [SECURITY.md](../../SECURITY.md).

### 12.4 Withdrawn deprecations

A deprecation MAY be withdrawn (the field returns to `active`)
before its removal version if and only if (a) the corpus usage
measurement is re-run and shows the field is no longer below the
10% threshold, or (b) a new use case for the field is documented
in an `Accepted` RFC. A withdrawn deprecation MUST update the
removed-fields registry to remove the field's entry and MUST cite
the withdrawal in CHANGELOG.md.

---

## 13. Registry extension behaviour

The `.klickd` registry (under [`registry/`](../../registry/) —
competency templates, personality vocabulary, domain profiles) is
the **first** lever for adding new identifiers without inflating
the schema. This document binds the following rules on registry
identifier lifecycle:

### 13.1 Registry identifiers ARE fields

A registry identifier (e.g. competency ID `HSE:WM-001`,
personality trait `curious`, domain `gaming`) is a "field" within
the meaning of §2. The lifecycle states of §3 apply to it.

### 13.2 Preferred channel for new surface

When a candidate field can be expressed as a **registry entry**
(an identifier from a controlled vocabulary, governed by the
existing registry mechanics) instead of as a **schema field** (a
new key in the envelope or payload), the candidate field MUST be
expressed as a registry entry. This is the operative form of the
**A4 (schema inflation)** guardrail. A PR that adds a schema
field where a registry entry would have sufficed is non-conforming
with this document and MUST be revised.

### 13.3 Registry deprecation

A registry identifier is deprecated by the same process as a
schema field (§3.2, §12.1). The deprecation marker lives in the
registry file itself (e.g. an `"deprecated": true` flag on the
entry, with `"deprecated_since"` and `"replacement"` fields). A
reader that consumes the registry MUST honour those markers per
§4.2 — i.e. a deprecated registry identifier is still read and
preserved; the marker is informational, not exclusionary.

### 13.4 Registry removal

A registry identifier is removed by the same process as a schema
field (§3.3, §12.2). Removed registry identifiers MUST remain in
the registry file marked `"removed": true` with `"removed_at"`,
so that readers encountering historical files can still resolve
the identifier to its former meaning for documentation purposes.
Physical deletion of the entry from the registry file is
forbidden during the v4 line; the entry leaves the registry only
at a major version boundary (§11.1).

### 13.5 Registry vs schema growth budget

This document does not impose a numeric cap on the number of
registry entries that v4 may carry. It imposes the qualitative
**A4** guardrail: registry growth is unbounded as long as each
new entry is a member of a well-defined controlled vocabulary;
schema growth is bounded by the deprecation discipline of this
document.

---

## 14. Anti-pattern A4 (schema inflation) — operative guardrails

This section is the operative restatement of the **A4** guardrail
from
[ROAD-TO-V4-GA §2.3 A4](../roadmap/ROAD-TO-V4-GA.md):
*"Pas d'ajout de champ sans politique de dépréciation associée
(R4-P0-4)."*

Every PR that adds a v4 field MUST satisfy **all** of the
following gates:

1. **Justification gate.** The PR description MUST argue, in one
   paragraph or less, why the field cannot be expressed as a
   registry entry (§13.2). If the field can be expressed as a
   registry entry, the PR MUST be revised to do so.
2. **Lifecycle gate.** The PR MUST place the field in the
   `active` lifecycle state and MUST cite this document by
   anchor. No field is added "outside" the lifecycle.
3. **Sunset gate.** The PR MUST name a plausible deprecation
   trigger condition: "this field is expected to be deprecated
   when X". The trigger is not a binding commitment to deprecate,
   but it forces the author to think about exit at entry time. If
   the author cannot articulate any plausible exit condition, the
   field is probably mis-scoped and the PR MUST be revised.
4. **Replacement gate.** If the new field overlaps with an existing
   field, the PR MUST either deprecate the existing field (§3.2)
   in the same PR or argue why both fields must coexist
   indefinitely. "Both" is the exceptional case, not the default.
5. **Vector gate.** The PR MUST add at least one positive vector
   exercising the new field's semantics. (This is the existing
   A5 guardrail — "spec-first sans exemples" — restated here for
   adjacency.)
6. **Schema gate.** If a strict v4 schema (P0-2) is in force, the
   PR MUST extend the strict schema to describe the new field.
   Adding a field without strict-schema coverage is a hidden
   regression.

A PR that adds a v4 field without satisfying gates 1–6 is
non-conforming with this document and MUST be revised before
merge.

This document does **not** impose a numeric cap on the v4 schema
size. The discipline it imposes is qualitative: every field has a
named lifecycle state, every addition has a named exit condition,
and registry-expressible surfaces stay in the registry.

---

## 15. Status

This document is **normative** for `.klickd` v4 from its merge
date. It is **docs-only** and does not introduce any required
on-the-wire field, schema strictness change, SDK API, vector,
package version, Git tag, npm / PyPI / Zenodo release, or DOI.
The OPTIONAL `deprecated_fields[]` block (§6) is documentary;
shipping it is not required of any conforming reader or writer.

Until the §33 field surface is promoted to the normative SPEC
body ([R4-P0-1](../roadmap/ROAD-TO-V4-GA.md)), the operative scope
of this document is **forward-looking**: v4 has no `deprecated`
or `removed` fields at adoption time (§8). The first deprecation
PR that lands after R4-P0-4 is what populates the registry.

This document does **not** modify or relax the §33.7
forward-compatibility contract, the §33.10 privacy invariants,
the v3.x SDK behaviour, the existing envelope contract, or any
field defined by the v3.x SPEC.
