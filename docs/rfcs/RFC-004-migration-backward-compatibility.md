# RFC-004 — Migration & Backward Compatibility ("Never break the soul")

| | |
|---|---|
| **RFC** | 004 |
| **Title** | Migration & Backward Compatibility for older `.klickd` files |
| **Target** | `.klickd v4` (migration policy applies retroactively to `v2.5 → v3.x → v3.5.1 → v4`) |
| **Status** | **Proposed** |
| **Author** | Vince C. (Klickd / Luxlearn, Luxembourg) |
| **Created** | 2026-05-22 |
| **Revised** | 2026-05-22 |
| **Promoted to Proposed** | 2026-05-23 |
| **Supersedes** | — |

> **This RFC is non-normative.** Nothing in this document binds any current SDK, schema, reader, or writer. It defines the *intended* migration model for older `.klickd` files at the moment a future v4 release lands. Until promoted into `SPEC.md` and the relevant schemas, the rules below MUST NOT be relied on for implementation.
>
> **Status note (Proposed).** The "Never break the soul" principle (§3), the staged pipeline (§5.4), the reader-vs-writer behaviour matrix (§6), the legacy/unknown/`x_*` handling (§7), and the rollback model (§8) are frozen for community review and for the reference migrator design work (T-401 / T-402). Open decisions (§12) remain open and do not block this promotion.

---

## 1. Motivation

The `.klickd` format has shipped real, in-use versions: `v2.5`, the `v3.x` line (through `v3.4.2`), and `v3.5.1`. Users have created `.klickd` files under each of these versions and carry them across agents and devices today. A v4 release will add new envelope fields, new payload sections (RFC-001 media, RFC-002 gates, RFC-003 benchmarks), and tightened semantics around verification and provenance.

The single hardest failure mode of a format evolution is **losing the user's soul**: a file written under v2.5 or v3.x silently degraded into a v4 shape that drops a field, rewrites a value, or invents a default the user never chose. The `.klickd` format exists precisely so a user does not have to re-explain who they are every time a tool changes. A migration that quietly mutates `personality`, `ethics`, `memory[]`, `growth`, `whitehat[]`, `agent_instructions`, or `onboarding_trigger` would defeat the entire purpose.

The guiding principle of this RFC is therefore:

> **Never break the soul.** A migration MUST be lossless, reversible, opt-in, and auditable. When in doubt, the migration MUST preserve the original and refuse to write, not invent a value.

## 2. Scope

**In scope (v4 migration policy):**

- Version detection on read for any `.klickd` file claiming `klickd_version` `2.5`, `3.0`, `3.1`, `3.2`, `3.3`, `3.4`, `3.4.2`, `3.5`, `3.5.1`, or `4.0`.
- A defined migration pipeline `v2.5 → v3.x → v3.5.1 → v4` with explicit intermediate hops (no direct `v2.5 → v4` jump in v1 of this policy).
- Mandatory **backup-before-write**: any migrating writer MUST persist the original file bytes before producing the migrated artefact.
- A `migration_report` artefact emitted alongside the migrated file.
- Additive defaults only: a missing field MUST become absent (or, if a schema requires presence, a documented neutral default), never an invented value.
- A **user-confirmation gate** for any non-trivial migration (anything beyond pure additive envelope bumps).
- **No data loss**: every field present in the source file MUST appear in the migrated file, the `migration_report`, or both — never neither.
- **Opt-in migration**: readers MAY read older files in place without migrating. Migration is a separate, user-initiated action.
- Distinct **reader vs writer** behaviour rules.
- Preservation of **legacy fields** (including deprecated names) under a documented `legacy.*` path.
- Handling of **unknown fields** introduced by extensions (`x_*`) or by future versions read by older readers.
- A **rollback** path that restores the pre-migration file from the mandatory backup.

**Out of scope (v1 of this RFC):**

- Cryptographic re-keying or KDF parameter upgrades (covered by future work in v4.x KDF policy).
- Cross-user / multi-recipient migration (interacts with RFC-001 and is deferred).
- Automatic migration without user confirmation, even for "trivial" version bumps. v1 deliberately keeps a human in the loop.
- A normative wire format for `migration_report` — v1 sketches the shape; normalisation happens when the policy is promoted into `SPEC.md`.
- Migration *from* v4 *back* to v3.x as a supported workflow. v3.x readers MUST be able to read v4 files by ignoring unknown fields (per RFC-001 §3, RFC-002 §3), but a writer-side downgrade is not in scope.

## 3. Principle: "Never break the soul"

Five sub-principles operationalise the headline principle. They are listed here so reviewers can challenge the *right* baseline.

1. **Lossless by default.** A migration MUST NOT drop a field. If a field cannot be carried into the new shape, it MUST be preserved under `legacy.<original_path>` and called out in `migration_report.warnings[]`.
2. **Additive, never substitutive.** A migration MUST NOT replace a user-chosen value with a "better" one. If v4 introduces a richer representation, the original value SHOULD be preserved alongside the new one (e.g. `personality.voice` → both `personality.voice` and `personality.voice_v4_extended`).
3. **Backup before write.** Before writing a migrated file to the same path, the original bytes MUST be persisted to a sibling location (e.g. `<file>.klickd.bak-<source_version>-<iso8601>`). A writer that cannot create the backup MUST refuse the migration.
4. **Confirmation before commit.** A migration that crosses a minor version boundary (e.g. `3.4 → 3.5`) MAY be silent; a migration that crosses a major boundary (`3.x → 4`) MUST surface a one-screen summary (added fields, preserved fields, warnings) and require an explicit user action to commit.
5. **Reader-side opt-in.** A v4 reader encountering a v3.x file MUST be able to operate on it *in place* without migrating. Migration is a writer-side, user-initiated act, not a side effect of reading.

## 4. Decisions already resolved

These are the baseline. They are listed so reviewers can attack the right target rather than re-litigating them.

1. **Pipeline is staged, not direct.** `v2.5 → v3.x → v3.5.1 → v4`. A v2.5 file does not jump straight to v4; the writer runs the intermediate hops so each step is auditable.
2. **No automatic migration on first read.** Reading a v3.x file in a v4 reader MUST NOT trigger a write. The user explicitly invokes migration (CLI flag, UI action, SDK call).
3. **Backups are mandatory and local.** The backup MUST be on the same storage medium as the original. A migrator MUST NOT silently upload backups anywhere.
4. **`migration_report` is an artefact, not a field.** It is a sibling JSON document, not a payload section embedded in the migrated file. Embedding it would itself be a soul-touching mutation.
5. **Unknown fields are kept, not stripped.** A v3.x file containing `x_*` extensions or fields a v4 reader does not understand MUST round-trip them into the migrated v4 file unchanged.
6. **Deprecated names are aliased, not renamed.** If a v3.x field is renamed in v4, the migrated file MUST carry both names for at least one major version, with the new name authoritative and the old name marked `deprecated` in `migration_report`.
7. **Failure is loud.** A migration that cannot satisfy these rules MUST fail with a structured error and leave the original file untouched. There is no "best-effort" partial migration.
8. **Migration is reversible from backup.** "Rollback" is defined as "delete the migrated file, restore the backup". v1 does not define a smarter delta-rollback.
9. **CC0 compatible.** Nothing in the migration policy requires proprietary tooling. A user with `jq` and a text editor MUST be able to inspect the `migration_report` and the backup.
10. **Human veto interacts with migration.** If `human_veto_policy.applies_to` (RFC-002) includes a class touched by the migration (e.g. `consent_change`, `identity_assertion`), the migration MUST escalate to `require-owner` regardless of the default confirmation level.

## 5. Schema (illustrative — non-normative)

### 5.1 `migration_report` (sibling artefact)

```json
{
  "migration_report": {
    "schema": "klickd.migration_report/v1-draft",
    "generated_at": "2026-05-22T10:00:00Z",
    "source_version": "3.4.2",
    "target_version": "4.0",
    "strategy": "staged",
    "hops": ["3.4.2 -> 3.5.1", "3.5.1 -> 4.0"],
    "backup_required": true,
    "backup_path": "./alice.klickd.bak-3.4.2-2026-05-22T10-00-00Z",
    "user_confirmation_required": true,
    "user_confirmed_at": "2026-05-22T10:00:42Z",
    "added_fields": [
      "media_profile",
      "verification_gates",
      "claim_sources",
      "human_veto_policy"
    ],
    "preserved_fields": [
      "personality",
      "ethics",
      "growth",
      "memory",
      "whitehat",
      "agent_instructions",
      "onboarding_trigger"
    ],
    "renamed_fields": [],
    "warnings": [
      {
        "code": "legacy_field_preserved",
        "path": "legacy.personality.voice_v3",
        "reason": "v4 introduces voice_v4_extended; original v3 value preserved unchanged."
      }
    ],
    "requires_user_review": false
  }
}
```

### 5.2 Proposed top-level fields (for the migration policy itself)

| Field | Type | Meaning |
|---|---|---|
| `migration.source_version` | string | Exact `klickd_version` read from the source file. |
| `migration.target_version` | string | The `klickd_version` produced by the migration. |
| `migration.strategy` | enum `staged` \| `direct` \| `manual` | `staged` is the default; `direct` is reserved; `manual` indicates a user-edited file outside the migrator. |
| `migration.backup_required` | bool | MUST be `true` for any cross-major migration. |
| `migration.user_confirmation_required` | bool | MUST be `true` for any cross-major migration; MAY be `false` for additive minor bumps. |
| `migration.added_fields[]` | string[] | Paths added by the migration. Each MUST be additive (no value invented for an existing path). |
| `migration.preserved_fields[]` | string[] | Paths copied verbatim from source to target. |
| `migration.warnings[]` | object[] | Structured non-fatal issues (`code`, `path`, `reason`). |
| `migration.requires_user_review` | bool | If `true`, the migrated file SHOULD NOT be used in production until the user has read `migration_report`. |

These fields live in the `migration_report` sibling artefact, NOT in the migrated `.klickd` payload itself.

### 5.3 Version detector — illustrative pseudocode

```python
def detect_version(envelope: dict) -> str:
    v = envelope.get("klickd_version")
    if not v:
        # v2.5 files predate explicit envelope versioning in some writers.
        # Use heuristic: presence of memory[] in legacy shape, absence of ethics.locked_actions.
        return "2.5" if looks_like_v25(envelope) else "unknown"
    if v in {"3.0", "3.1", "3.2", "3.3", "3.4", "3.4.2"}:
        return v
    if v in {"3.5", "3.5.1"}:
        return v
    if v == "4.0":
        return v
    return "unknown"
```

A migrator MUST refuse to operate on a file whose detected version is `unknown` and MUST emit a `migration_report` with `warnings[].code = "unknown_source_version"`.

### 5.4 Migration pipeline — staged hops

```
v2.5 ──► v3.0 ──► v3.4.2 ──► v3.5.1 ──► v4.0
        (envelope    (additive    (v3.5    (RFC-001 / 002 /
         bump)       fields,      benchmark fields,
                     §29c privacy guards) etc.)
```

Each hop is its own function, with its own preserved-field list. A hop MUST be idempotent on a file already at its target.

## 6. Reader vs writer behaviour

| Actor | Behaviour |
|---|---|
| **v4 reader, v3.x file** | MUST read in place. MUST NOT mutate. MUST ignore absent v4 fields without inventing defaults. MAY surface a non-blocking "migration available" hint. |
| **v4 reader, v2.5 file** | MUST read in place if it can parse the envelope; otherwise MUST refuse with a clear error and a pointer to a migrator. MUST NOT mutate. |
| **v4 writer, v3.x source** | MUST run the staged pipeline. MUST write the backup before producing the migrated file. MUST emit `migration_report`. MUST surface user confirmation for the v3 → v4 hop. |
| **v3.x reader, v4 file** | MUST ignore unknown v4 fields (RFC-001 §3, RFC-002 §3). MUST NOT delete them on write-back. MUST NOT migrate v4 → v3. |
| **v3.x writer, v4 file** | MUST refuse to write. A v3.x writer cannot safely down-write a v4 file. |

## 7. Legacy fields, unknown fields, and `x_*` extensions

- **Legacy fields** (renamed or restructured): preserved under `legacy.<original_path>` in the migrated file, listed in `migration_report.preserved_fields[]`, and the new path is authoritative for the new reader.
- **Unknown fields** (not in the spec for either source or target version): preserved verbatim, listed in `migration_report.warnings[]` with `code = "unknown_field_preserved"`. Never dropped.
- **`x_*` extensions** (reverse-DNS prefixed custom fields): always preserved verbatim. Not counted as warnings.
- **`deprecated`-tagged fields**: copied to the target file *and* called out in `migration_report` so a future migrator can remove them with the user's consent.

## 8. Rollback

Rollback is intentionally simple in v1:

1. Verify the backup exists at `migration_report.backup_path` and that its hash matches the value recorded in `migration_report` (a hash field SHOULD be added by the writer; v1 does not normatively require it).
2. Delete or rename the migrated file.
3. Restore the backup to the original path.
4. Optionally retain the `migration_report` for audit.

A writer MUST NOT offer rollback as a "smart" operation that re-derives the v3 file from the v4 file. The backup is the authoritative source of truth for rollback.

## 9. Interaction with other RFCs

- **RFC-001 (`media_profile`)**: a v3.x file has no `media_profile`. Migration to v4 MUST NOT invent one. `migration_report.added_fields[]` MUST list `media_profile` only if the user explicitly opted in to creating one during the migration UX.
- **RFC-002 (`verification_gates`)**: a v3.x file has no gates. The migrated v4 file MAY include a permissive default gate profile (per RFC-002 §3) only when `verification_gates.user_default = "silent"`; the user MUST be informed via `migration_report.added_fields[]`.
- **RFC-003 (Context Cost Benchmark)**: benchmark fields are research-track and SHOULD NOT be added by an unattended migration.

## 10. Tickets for future implementation

These are *future* tickets. Nothing here is committed.

- **T-401 — Reference migrator (Python)**: implement `klickd migrate <file>` in the Python SDK with staged hops, mandatory backup, and `migration_report` emission.
- **T-402 — Reference migrator (JS/TS)**: equivalent CLI / function in `@klickd/core`. Output must be byte-identical to the Python migrator for the shared test vectors.
- **T-403 — Version detector**: shared detector library (Python + JS) covering the heuristics in §5.3, with golden fixtures for each known historical shape.
- **T-404 — Backup-before-write enforcement**: linter rule in both SDKs that fails a unit test if a migrator code path can write a migrated file before a backup is confirmed on disk.
- **T-405 — `migration_report` schema**: formalise `klickd.migration_report/v1` under `schemas/` once the RFC is `Accepted`.
- **T-406 — Rollback CLI**: `klickd migrate --rollback <file>` that consumes `migration_report` and restores the backup with a hash check.
- **T-407 — Unknown-field round-trip**: regression suite that loads, migrates, and re-serialises a file containing `x_*` and unknown future fields and asserts byte-for-byte preservation of those fields.
- **T-408 — UX text**: short, translatable confirmation strings for the cross-major migration prompt (CC0, in the existing locale set under `curriculum/`).
- **T-409 — Soul Handoff interaction**: extend §28.8 documentation (not the guaranteed-fields list) with a note that a freshly migrated file MAY include a `migration_report` reference in its handoff context.
- **T-410 — Human-veto interaction**: integration test that a `human_veto_policy` covering `consent_change` blocks a silent migration of a v3.x file that would otherwise be silent.

## 11. Tests (planned, non-normative)

Concrete test fixtures land alongside T-401/T-402. v1 of this RFC sketches the *intent* only:

- **Round-trip tests**: every historical fixture in `tests/` (v2.5, v3.0, v3.4.2, v3.5.1) migrates to v4 and back via backup rollback with no diff against the original.
- **Lossless field coverage**: for each historical version, an explicit enumeration of fields and an assertion that each appears in the migrated file, in `legacy.*`, or in `migration_report.preserved_fields[]`.
- **Backup enforcement**: a migrator invoked with a read-only target directory MUST refuse and leave no partial artefacts.
- **Confirmation gate**: a v3 → v4 migration invoked without the `--yes` confirmation flag MUST refuse to write.
- **Unknown-field preservation**: a fixture containing `x_com_example_custom` and a synthetic `future_field_v5` round-trips unchanged.
- **Reader-side non-mutation**: a v4 reader opening a v3.x file MUST leave mtime and bytes untouched.
- **Rollback correctness**: post-rollback file hash equals pre-migration file hash.
- **Pipeline staging**: a v2.5 fixture migrated to v4 MUST produce an audit trail listing every intermediate hop in order.

## 12. Open decisions

1. **Backup hashing**: SHOULD v1 normatively require a backup hash in `migration_report`, or is path-based reference enough? Leaning toward requiring SHA-256 once promoted.
2. **`migration_report` retention**: does the writer retain the report indefinitely, or is it a one-shot artefact the user can delete after review? Current draft: retain by default, document deletion.
3. **Silent additive bumps**: is a `3.4 → 3.4.2` hop allowed to be silent, or does every migration require confirmation? Current draft: silent for same-minor; confirmation for same-major; explicit for cross-major.
4. **Multi-passphrase files (roadmap v4.0)**: migration interaction with key-wrapping is deferred to a follow-up RFC, but should be flagged here.
5. **Version detector heuristics for unversioned v2.5 files**: how aggressive should the heuristic be before we refuse? Current draft: refuse on ambiguity, do not guess.

## 13. References

- [SPEC.md](../../SPEC.md) — current normative specification.
- [SPEC_v30.md](../../SPEC_v30.md) — historical v3.0 specification.
- [SKILL.md](../../SKILL.md), [SKILL_v30.md](../../SKILL_v30.md), [SKILL_v25.md](../../SKILL_v25.md) — historical skill documents.
- [RFC-001](./RFC-001-media-profile-v1.md), [RFC-002](./RFC-002-verification-gates.md), [RFC-003](../../benchmarks/context_cost/RFC.md).
- [ROADMAP.md](../../ROADMAP.md) — v4.0 milestone.

---

*This RFC is **Draft** and **non-normative**. It defines intent, not implementation. Promotion into `SPEC.md` requires a separate PR after community review.*
