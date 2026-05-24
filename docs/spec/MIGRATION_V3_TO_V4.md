# R4-P0-5 — `.klickd` v3.x → v4 GA Migration (Normative)

> **Status:** NORMATIVE (V4 P0). Docs-only normative companion to
> [DEPRECATION_POLICY_V4](./DEPRECATION_POLICY_V4.md), to the strict
> payload schemas in [`schemas/`](../../schemas/), and to
> [SPEC.md](../../SPEC.md). Uses **RFC 2119 / RFC 8174** key words.
>
> **Scope:** this document specifies the **non-destructive** in-place
> migration of a `.klickd` v3.x payload to the **v4 GA** payload shape
> defined by `schemas/klickd-payload-v4.schema.json` (P0-2). It binds
> the reference migrator surface shipped by the Python and TypeScript
> SDKs in P0-5.
>
> **Out of scope (tracked elsewhere):** strict cross-impl vectors
> ([P0-6](../roadmap/ROAD-TO-V4-GA.md)); the encrypted-envelope
> rotation policy and key-rolling story (RFC-004 v2, Draft);
> destructive transforms (any change that loses information from
> the source payload); registry / vocabulary remaps; SDK release
> publication (no GA tag, no npm/PyPI/Zenodo publish).

---

## 1. Why a migrator now

The v4 GA strict schema (P0-2) introduces additive surface — RFC-001
v1 `media_profile`, RFC-002 v1 `verification_gates` / `human_veto_policy`
/ `claim_sources` / `risk_thresholds`, RFC-004 v1 `migration`, plus the
top-level `profile_kind` discriminator — but it deliberately keeps
**top-level `additionalProperties: true`** so that existing v3.x
payloads validate against the v4 GA schema *with no edits* (see
SPEC.md §33.7 forward-compatibility invariant).

In practice writers still want a deterministic, reviewable transform
that:

1. **Lifts** the implicit v3 profile to the explicit v4 GA
   `profile_kind: "learner"` discriminator;
2. **Stamps** the `payload_schema_version` to `"4.0"` so downstream
   readers can route on the GA strict track without sniffing fields;
3. **Records** an auditable `migration` block (RFC-004 v1 frozen
   surface: `source_version`, `migrated_at`, optional pointer refs)
   so that the provenance of the v4 file is recoverable;
4. **Preserves** every unknown / unrecognized field byte-for-byte
   (§33.7), every locked safety field (`ethics.locked_actions`, the
   v3.x `injection_target` floor), and every block that does not
   have an explicit migration rule below.

The reference migrator implements the minimum transform that
satisfies (1)–(4). It does **not** invent new safety surface, it
does **not** drop or rewrite v3 fields, and it does **not** touch
the encrypted wire envelope.

---

## 2. Wire envelope contract (unchanged)

The migrator operates on the **decrypted payload only**. The outer
JSON envelope keeps `klickd_version: "3.0"` on disk for v4 GA files
written by the reference SDKs in P0-5; only the inner payload
advertises `payload_schema_version: "4.0"`. This matches the
preview-track invariant already documented in
[`CONTRIBUTING.md`](../../CONTRIBUTING.md) and SPEC.md §33:

> *The wire envelope stays at `klickd_version="3.0"` — only the
> inner payload uses `payload_schema_version="4.0"` (or the
> preview-era `"4.0.0-preview.1"`).*

A future P1 RFC MAY promote the wire envelope to `klickd_version:
"4.0"`; until then the migrator MUST NOT mutate `klickd_version`,
`kdf`, `cipher`, `encrypted`, `ciphertext`, `created_at`, `domain`,
or any other envelope-AAD field. Doing so would break authenticated
decryption of any pre-existing file.

---

## 3. Migrator contract

### 3.1 Surface

Both reference SDKs expose two entry points:

| Surface | Python | TypeScript |
|---|---|---|
| In-place payload migration | `klickd.migrate_payload(payload, *, source_version=None, migrated_at=None, profile_kind="learner", migration_report_ref=None, backup_ref=None) -> dict` | `migratePayload(payload, { sourceVersion?, migratedAt?, profileKind?, migrationReportRef?, backupRef? }) => Record<string, unknown>` |
| Detect whether migration is required | `klickd.needs_migration(payload) -> bool` | `needsMigration(payload) => boolean` |

Both functions are **pure** (no I/O), **non-destructive** (return a
new dict; do not mutate input), and **idempotent** (running the
migrator twice produces the same payload as running it once, modulo
the `migrated_at` timestamp which a caller MAY pin).

### 3.2 Detection — `needs_migration`

A payload "needs migration" iff **all** of the following hold:

- it is a JSON object;
- its `payload_schema_version` is missing OR matches the v3 pattern
  (`"3.0"`, `"3.1"`, `"3.2"`, …, or absent entirely on v3.x files
  that pre-date the field);
- it does **not** already carry `payload_schema_version: "4.0"` or
  `"4.0.0-preview.1"`.

A payload that already advertises a v4 `payload_schema_version`
MUST NOT be re-migrated; `migrate_payload` MUST instead **return
the input unchanged** (with only an optional refresh of the
`migration` block when the caller explicitly passes
`migration_report_ref` or `backup_ref`).

### 3.3 Transform rules (deterministic, narrow)

For each rule below, the migrator MUST apply the rule exactly once
and MUST NOT touch fields outside the rule's scope.

| # | Rule | Source (v3.x) | Target (v4 GA) | Notes |
|---|---|---|---|---|
| R1 | **Stamp payload version** | absent OR `payload_schema_version` ∈ {`"3.0"`,`"3.1"`,`"3.2"`,`"3.3"`,`"3.4"`,`"3.5"`} | `payload_schema_version = "4.0"` | If a non-v3 value is present (e.g. `"4.0.0-preview.1"`), see R8. |
| R2 | **Stamp profile kind** | `profile_kind` absent | `profile_kind = "learner"` (or caller-supplied) | v3.x is implicitly "learner" per `schemas/klickd-payload-v4.schema.json#/properties/profile_kind`. |
| R3 | **Preserve `domain_schema_version`** | present (v3 `"{domain}-{major}.{minor}"`) | unchanged | The v4 GA pattern accepts both v3 and bare-semver forms. |
| R4 | **Insert migration block** | absent | `migration = { source_version, migrated_at, migration_report_ref?, backup_ref? }` | `source_version` defaults to the v3 `payload_schema_version` if present, else `"3.x"`. `migrated_at` defaults to `now()` in RFC 3339 UTC (`...Z`). |
| R5 | **Preserve identity** | `identity.{name,language,timezone,communication_style,…}` | unchanged | Both `name` and `display_name` are accepted by the v4 GA schema; the migrator MUST NOT rename either. |
| R6 | **Preserve all other v3 blocks verbatim** | `context`, `knowledge`, `memory`, `agent_instructions`, `user_preferences`, `archived_sessions`, `companion_identity`, `ethics`, `learning_goal`, `injection_target`, `onboarding_trigger`, every `x_*` extension key | unchanged | This is §33.7 forward-compat: unknown / additive fields round-trip verbatim. |
| R7 | **Do NOT synthesize new safety surface** | absent | absent | The migrator MUST NOT invent `verification_gates`, `human_veto_policy`, `claim_sources`, `risk_thresholds`, `preflight_checks`, `error_journal`, `media_profile`, `verification_artifacts`, `reversibility`, `blast_radius`, `contract_tests`, or `success_criteria`. Those blocks are caller-authored. |
| R8 | **Idempotency / non-v3 source** | `payload_schema_version ∈ {"4.0","4.0.0-preview.1"}` | unchanged | The migrator returns the input unchanged. It MAY still update the `migration` block iff the caller passes explicit pointer refs; otherwise it MUST NOT mutate the input. |
| R9 | **Locked safety fields** | `ethics.locked_actions`, the v3.x `decisions_locked` list inside `context` | unchanged | Migrator MUST NOT remove, reorder, or rewrite these. |
| R10 | **Unknown top-level keys** | any key not enumerated in the v3 or v4 schema | unchanged | Round-trip preservation is mandatory (§33.7). |

### 3.4 What the migrator MUST NOT do

- It MUST NOT touch the encrypted envelope (`klickd_version`,
  `kdf`, `cipher`, `ciphertext`, `created_at`, `domain`,
  `encrypted`, salt, IV, GCM tag).
- It MUST NOT decrypt or re-encrypt anything; if the caller has only
  the envelope, they MUST decrypt first, then migrate the payload,
  then re-encrypt out-of-band (the migrator is payload-only).
- It MUST NOT drop, rename, or coerce v3 fields — including
  fields that were marked legacy in v3.4 (e.g. the `object`-form
  `user_preferences`).
- It MUST NOT bump or rewrite `domain_schema_version`.
- It MUST NOT add `verification_gates`, `human_veto_policy`,
  `claim_sources`, `media_profile`, or any other RFC-002 / RFC-001
  block. Those are authored by the human operator or by a separate
  wizard surface (R4-P0-1).
- It MUST NOT add `_example_metadata`, `deprecated_fields`,
  `gaming_profile`, `context_cost`, or any other v4-additive block
  that was not present in the source.
- It MUST NOT redact or rewrite values that look like PII or
  secrets. Sanitization is a separate concern (out of scope).

### 3.5 Manual-review conditions

The migrator MUST raise / return a warning (without aborting) when
any of the following hold in the source payload, because they
typically need a human decision before the resulting v4 GA file is
considered production-ready:

- the v3 payload carries `ethics.locked_actions` that conflict with
  an existing `human_veto_policy.applies_to` (cannot happen on a
  pure v3 source, but is possible when migrating a partially-v4
  file with `human_veto_policy` already set — see R8);
- the v3 `decisions_locked` array contains entries longer than
  1024 characters (truncated downstream by some readers — surface,
  don't truncate);
- the source `payload_schema_version` is `"3.x"` and there is no
  `domain_schema_version` field (rare in practice — most v3
  writers stamp one).

Both reference SDKs surface these warnings via a separate
`migrate_payload_iter_warnings` (Python) / `migratePayloadIterWarnings`
(TypeScript) helper that returns a list of `(path, message)` tuples
without mutating the payload.

### 3.6 Error handling

The migrator raises `KLICKD_E_SCHEMA` (Python `KlickdError`,
TypeScript `KlickdError`) when the input is not a JSON object or
when it carries a `payload_schema_version` that the migrator does
not recognize (i.e. neither v3.x nor v4). All other anomalies are
surfaced as warnings (§3.5) — the migrator never silently drops
data.

---

## 4. Compatibility guarantees

- **Forward-compat:** a v4 GA payload produced by the migrator MUST
  validate against `schemas/klickd-payload-v4.schema.json` and
  against `schemas/klickd-payload-v4-preview.schema.json`. Both
  schemas coexist (§33.7); the preview schema is permissive and
  always accepts a strict-conformant file.
- **Backward-compat:** a v4 GA payload produced by the migrator
  remains readable by a v3.x reader for every block that a v3.x
  reader understands (identity, context, knowledge, memory,
  agent_instructions, user_preferences, learning_goal,
  companion_identity, ethics, archived_sessions). Unknown blocks
  (`migration`, `profile_kind`, …) MUST be silently ignored by v3
  readers per SPEC.md §33.7.
- **Round-trip:** running the migrator twice on the same input
  produces the same output (modulo `migrated_at` when not pinned
  by the caller).
- **Wire envelope:** the encrypted v3 envelope is preserved
  bit-for-bit. A consumer can decrypt → migrate → re-encrypt with
  a fresh IV/salt and the resulting file MUST verify under the
  same passphrase.

---

## 5. Reference SDK surface (P0-5)

### 5.1 Python (`klickd>=4.0.0a2`)

```python
from klickd import migrate_payload, needs_migration

if needs_migration(payload):
    v4 = migrate_payload(
        payload,
        source_version=payload.get("payload_schema_version", "3.x"),
        # migrated_at defaults to datetime.now(timezone.utc) in RFC 3339
        # profile_kind defaults to "learner"
        # migration_report_ref / backup_ref default to None
    )
    # v4["payload_schema_version"] == "4.0"
    # v4["profile_kind"]            == "learner"
    # v4["migration"]               == {"source_version": "3.4", "migrated_at": "..."}
```

`migrate_payload_iter_warnings(payload)` returns a list of
`(json_pointer_path, message)` tuples — empty when no manual review
is required.

### 5.2 TypeScript (`@klickd/core>=4.0.0-preview.2`)

```ts
import { migratePayload, needsMigration } from "@klickd/core";

if (needsMigration(payload)) {
  const v4 = migratePayload(payload, {
    sourceVersion: payload.payload_schema_version ?? "3.x",
    // migratedAt defaults to new Date().toISOString()
    // profileKind defaults to "learner"
  });
}
```

`migratePayloadIterWarnings(payload)` is the non-throwing
warning surface (parity with Python).

---

## 6. Non-goals

- **No registry remap.** Competency / vocabulary registry IDs are
  preserved verbatim; the migrator does not touch
  `registry/` content.
- **No release.** P0-5 ships a migrator and tests only. No
  GitHub release, no npm / PyPI / Zenodo publish, no SDK
  `version` bump beyond what is already on `main`.
- **No strict-only enforcement.** The migrator targets the v4 GA
  strict schema, but a payload that fails strict validation
  (because the caller authored bad RFC-002 / RFC-001 surface
  by hand) is still emitted — the caller is expected to run
  `validate(..., strict=True)` separately.
- **No wire-envelope rotation.** Re-encryption, salt rotation,
  and KDF parameter bumps are deferred to a future RFC.

---

## 7. References

- [SPEC.md](../../SPEC.md) §33 — v4 payload surface and forward-compat invariant.
- [DEPRECATION_POLICY_V4.md](./DEPRECATION_POLICY_V4.md) — field lifecycle contract.
- [`schemas/klickd-payload-v3.schema.json`](../../schemas/klickd-payload-v3.schema.json) — v3 payload contract.
- [`schemas/klickd-payload-v4.schema.json`](../../schemas/klickd-payload-v4.schema.json) — v4 GA strict candidate schema (P0-2).
- [`packages/pypi/klickd/src/klickd/migrate.py`](../../packages/pypi/klickd/src/klickd/migrate.py) — Python reference implementation.
- [`packages/@klickd/core/src/migrate.ts`](../../packages/@klickd/core/src/migrate.ts) — TypeScript reference implementation.
