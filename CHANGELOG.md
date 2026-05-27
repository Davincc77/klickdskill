# Changelog — .klickd Format

All notable changes to the `.klickd` specification and reference implementations.

Format: `[version] — date — description`
Versions follow: `envelope_version (skill_revision)`.

---

## packaging 4.0.3 — 2026-05-27 — align Python runtime `__version__` with package metadata; npm parity

> **Packaging-only patch.** Stable `.klickd` spec release remains v4.0.0
> (DOI, GitHub Release). 4.0.3 supersedes 4.0.2 for both the `@klickd/core`
> npm distribution and the `klickd` PyPI distribution. The wire envelope,
> JSON schemas, payload semantics, and starter `.klickd` files are unchanged.

### PyPI — `klickd` 4.0.2 → 4.0.3 (fix)

- **Fix:** `klickd.__version__` was still `"4.0.1"` in the 4.0.2 wheel and
  sdist, so consumers calling `klickd.__version__` (e.g. logging, support
  diagnostics, downstream version pinning) saw a value that disagreed with
  the PyPI release. The `__init__.py` constant is now bumped in lock-step
  with `pyproject.toml`. PyPI 4.0.2 cannot be overwritten (immutable
  release), so this hotfix ships as a new 4.0.3 patch.

### npm — `@klickd/core` 4.0.2 → 4.0.3 (parity)

- **Chore:** bump `@klickd/core` to 4.0.3 so the npm `latest` and PyPI
  `latest` advertise the same patch level. No code, schema, or starter-pack
  changes. The CJS+ESM tarball smoke test (`scripts/verify-tarball.mjs`)
  remains the publish-time guard.

### Starter `.klickd` files (unchanged)

- `user.klickd`, `student.klickd`, `research.klickd`, `coding.klickd` ship
  byte-identical to 4.0.2, with the same SHA-256 manifest.

### Scope guarantees (intentional non-goals)

- No GitHub Release
- No git tag
- No Zenodo DOI / `.zenodo.json` change
- No v4.1 / "Chimera" public claim — wire format, schemas, and spec are
  unchanged from v4.0.0

---

## packaging 4.0.2 — 2026-05-26 — fix CJS require() of @klickd/core; PyPI publishing path

> **Packaging-only patch.** Stable `.klickd` spec release remains v4.0.0
> (DOI, GitHub Release). 4.0.2 supersedes 4.0.1 for the `@klickd/core`
> npm distribution and the `klickd` PyPI distribution.

### npm — `@klickd/core` 4.0.1 → 4.0.2 (fix)

- **Fix:** `listStarterSkills()` (and every other helper that called
  `starterSkillsDir()`) threw `TypeError [ERR_INVALID_ARG_TYPE]:
  fileURLToPath path undefined` under CommonJS `require()` because tsup
  rewrites `import.meta.url` to an empty object in the CJS bundle. The
  helper now probes `__dirname` first and falls back to
  `fileURLToPath(import.meta.url)` so both module systems resolve the
  directory correctly.
- **Fix:** the ESM bundle re-emitted JSON imports without
  `with { type: 'json' }`, so `import '@klickd/core'` failed on Node 20+
  with `ERR_IMPORT_ASSERTION_TYPE_MISSING`. The bundled JSON schemas are
  now inlined into the ESM and CJS outputs (no `--loader .json=copy`).
- **New:** `scripts/verify-tarball.mjs` — packs the published artifact and
  installs it into scratch CJS and ESM projects, exercising the helper
  API the way real consumers will. Wired into the patch publish workflow
  before `npm publish` runs.

### PyPI — `klickd` 4.0.1 → 4.0.2 (publish path)

- **Fix:** the 4.0.1 publish was driven by a new workflow file
  `publish-pypi-4.0.1.yml`. PyPI Trusted Publishing matches on workflow
  filename, and the existing `klickd` trusted publisher only trusts the
  pre-existing `publish-pypi.yml`. The new workflow file has been
  removed; `publish-pypi.yml` already supports `workflow_dispatch` with a
  `ref` input and is used to publish 4.0.2 directly from `main`.

### Scope guarantees (intentional non-goals)

- No GitHub Release
- No git tag
- No Zenodo DOI / `.zenodo.json` change
- No v4.1 / Chimera public claim — wire format, schemas, and spec are
  unchanged from v4.0.0

---

## v4.0.1 — 2026-05-26 — superseded by 4.0.2

Initial packaging-only patch that bundled the four v4.0-envelope starter
`.klickd` skills. Superseded by 4.0.2; do not depend on `@klickd/core@4.0.1`
under CommonJS (`require()`) or under modern Node.js ESM (JSON import
attribute missing). The npm `latest` dist-tag is moved back to 4.0.0
until 4.0.2 publishes.

---

## v4.0.0 (GA) — 2026-05-25 — final v4 general availability (release-prep, not published)

> **Status: RELEASE-PREP (PR open).** No git tag, no GitHub Release, no npm
> publish (no `latest` dist-tag flip), no PyPI publish, no Zenodo deposit yet.
> Those remain final gated public actions after maintainer review.
>
> v4.0.0 is the first general-availability release of the v4 track. The wire
> envelope stays at `klickd_version: "3.0"` (crypto, AAD and KDF unchanged);
> v4 is signalled inside the payload via
> `payload_schema_version: "4.0"` (the canonical v4 GA value; release label
> is `v4.0.0`). v3.x readers MUST ignore unknown fields; v4 readers MUST
> preserve them verbatim.
>
> **Positioning (v4).** `.klickd` is positioned as an open-source security
> and continuity layer for every actor in AI: users (privacy / ownership /
> memory portability), agents (structured context / verified constraints),
> developers (schemas / SDKs / migration) and industry (controlled,
> opt-in interoperability). Tagline: *One soul. Any model. Any agent.*
> v4.0.0 makes this layer normative and strict; it does not claim adoption
> as an industry standard or universal cross-product compatibility.

### What ships in v4.0.0

- **SPEC normative v4** — `SPEC.md` promoting v4 wording from preview to
  normative; `klickd_version: "3.0"` stays the wire identifier; the v4
  surface is signalled via `payload_schema_version`.
- **Strict JSON Schemas (Draft 2020-12)** — `schemas/klickd-payload-v4.schema.json`
  and `schema/klickd-v4.schema.json`; coexist with v4 preview schemas for
  one cycle.
- **Reference SDKs aligned to v4 GA strict** — Python `klickd==4.0.0`
  (`packages/pypi/klickd/`) and TypeScript `@klickd/core@4.0.0`
  (`packages/@klickd/core/`). Public surface for v4 sections, strict
  validation entrypoint, and preservation of unknown fields.
- **Non-destructive v3.x → v4 payload migrator** (RFC-004) — exposed in
  both SDKs; produces a `migration_report` and never overwrites caller-set
  v4 fields.
- **Strict cross-implementation v4 test vectors** — positive and adversarial,
  verified by `verify_vectors.py` (Python) and `verify_vectors.mjs` (Node).
- **Community files** — CODE_OF_CONDUCT, issue templates, PR template
  (landed in #47).

### Distribution version mapping (release-prep)

| Channel    | Version target                                       | Notes                                                                       |
|------------|------------------------------------------------------|-----------------------------------------------------------------------------|
| git tag    | `v4.0.0`                                             | NOT created in this PR; final gated action.                                 |
| npm        | `@klickd/core@4.0.0`                                 | NOT published in this PR; `latest` flip is a final gated action.            |
| PyPI       | `klickd==4.0.0`                                      | NOT published in this PR; final gated action.                               |
| Zenodo     | new version of concept DOI `10.5281/zenodo.20262530` | NOT deposited in this PR; final gated action.                               |

### Backward compatibility

- Wire envelope unchanged (`klickd_version: "3.0"`); v3.x readers continue
  to load v4 files and MUST ignore unknown payload fields.
- v3.5.1 deposit on Zenodo remains valid and citeable; v4.0.0 declares a
  `isNewVersionOf` relationship to it.
- The Python `klickd==3.x` series continues to load v4 payloads (round-trip)
  but does not enforce the strict v4 schema; upgrading to `klickd==4.0.0`
  is recommended to opt in to strict validation and to use the migrator.

### Documentation

- Release notes: [`docs/releases/v4.0.0.md`](docs/releases/v4.0.0.md).
- Migration guide: [`docs/spec/MIGRATION_V3_TO_V4.md`](docs/spec/MIGRATION_V3_TO_V4.md).
- Roadmap status: P0-1 to P0-6 all landed prior to this release-prep PR.

### Not in this PR

- No git tag.
- No GitHub Release.
- No npm publish, no `@klickd/core` `latest` dist-tag flip.
- No PyPI publish.
- No Zenodo deposit; no v4.0.0 version-specific DOI yet.
- No public announcements.

---

## Unreleased — docs-only — RFC promotions toward v4 GA

> **Status: DOCS-ONLY / NON-NORMATIVE.** No SDK, schema, or vector change.
> No publish (npm / PyPI / Zenodo), no tag, no announcement.
> Production-recommended format remains **v3.5.1**. Preview track remains
> **v4.0.0-preview.1**.

### 2026-05-24 — RFC-001 / RFC-002 (v1 core) / RFC-004 promoted `Proposed → Accepted`

- **RFC-001 (`media_profile` v1)** — promoted to `Accepted`. The §4 decisions,
  the §5 illustrative schema, the §6 V-001…V-012 validation checklist, and the
  §9 error codes are approved for inclusion in the next normative `SPEC.md`
  revision. Open questions (§11) are preserved verbatim and do not block
  acceptance.
- **RFC-002 (`verification_gates` + `human_veto`)** — v1 core promoted to
  `Accepted`: five gate levels (§6), `human_veto_policy`, `claim_sources`
  (v1 fields only), `error_journal`, `risk_thresholds`, `preflight_checks`,
  §4 decisions, §6 level semantics, and §9 G-001…G-006 conformance intent.
  v2 §8b additions (`claim_status`, `contract_tests`, `success_criteria`,
  `reversibility`, `blast_radius`, `verification_artifacts`,
  `error_journal[].rule_created`, extended `claim_sources.records[]`) **stay
  `Draft`** and may still iterate without affecting the v1 Accepted surface.
- **RFC-004 (Migration & Backward Compatibility — "Never break the soul")**
  — promoted to `Accepted`. The §3 sub-principles, §4 decisions, §5.4 staged
  pipeline (`v2.5 → v3.x → v3.5.1 → v4`), §6 reader-vs-writer matrix, §7
  legacy / unknown / `x_*` rules, and §8 rollback model are approved.
  Reference migrator (T-401 / T-402), `migration_report` schema (T-405), and
  rollback CLI (T-406) remain future work, gated on `Implemented`.
- **Promotion gate.** Each RFC was assessed against
  [`docs/rfcs/ACCEPTANCE_CHECKLIST_V4.md`](docs/rfcs/ACCEPTANCE_CHECKLIST_V4.md)
  §3 C1–C16. The acceptance evidence table lives in the promotion PR body.
- **What does NOT change.** No SPEC, schema, SDK, vector, envelope, AAD, KDF,
  or crypto change. No npm / PyPI / Zenodo / IANA publish. No tag, no release,
  no announcement. v3.5.1 remains the production-recommended format;
  v4.0.0-preview.1 remains the only preview release with permissive schemas.
- **What this unblocks.** The v4 GA P0 chantiers listed in
  [`docs/roadmap/ROAD-TO-V4-GA.md`](docs/roadmap/ROAD-TO-V4-GA.md) §2.1 (P0-1
  SPEC normative v4, P0-2 strict JSON Schema, P0-3 Python SDK, P0-4 JS/TS SDK,
  P0-5 reference migrator, P0-6 strict vectors) may now begin against the
  frozen v1 surface, per §4 step 3 ("SPEC normative v4") and §5 step 4
  ("PR « spec(v4): begin promoting §33 preview wording toward normative »").

### 2026-05-24 — V4 RFC acceptance checklist (`Proposed → Accepted` gate)

- **New governance doc** [`docs/rfcs/ACCEPTANCE_CHECKLIST_V4.md`](docs/rfcs/ACCEPTANCE_CHECKLIST_V4.md).
  Defines the explicit, verifiable criteria (C1–C16) required to promote a
  v4 RFC from `Proposed` to `Accepted`, and the criteria (I1–I9) required
  to later mark it `Implemented`. Closes the gap between
  [`docs/rfcs/README.md`](docs/rfcs/README.md) (which only stated what
  `Accepted` *means*) and
  [`docs/roadmap/ROAD-TO-V4-GA.md`](docs/roadmap/ROAD-TO-V4-GA.md) §2.1 P0-1
  (which depends on RFC-001 / RFC-002 v1 core / RFC-004 reaching `Accepted`
  before SPEC v4 normative work begins).
- **[`docs/rfcs/README.md`](docs/rfcs/README.md)** — adds a "Promotion gate"
  callout pointing at the new checklist, plus a Companion docs table row.
- **No SPEC, schema, SDK, or vector touched.** RFC statuses are unchanged
  (RFC-001 / RFC-002 v1 core / RFC-004 stay `Proposed`; RFC-003 / RFC-002
  §8b v2 additions / RFC-006 stay `Draft`).
- **No publish.** No npm / PyPI / Zenodo / IANA action, no tag, no release.

### 2026-05-23 — RFC-001 / RFC-002 (v1 core) / RFC-004 promoted `Draft → Proposed`

- **RFC-001 (`media_profile` v1)** — promoted to `Proposed`. Freezes the §4
  decisions, the §5 illustrative schema, the §6 V-001…V-012 validation
  checklist, and the §9 error codes for community review and prototype
  implementations. Open questions (§11) remain open and do not block the
  promotion.
- **RFC-002 (`verification_gates` + `human_veto`)** — v1 core promoted to
  `Proposed` (five gate levels, `human_veto_policy`, `claim_sources`,
  `error_journal`, `risk_thresholds`, `preflight_checks`, §4 decisions, §6
  level semantics, §9 G-001…G-006 conformance intent). v2 §8b additions
  (`claim_status`, `contract_tests`, `success_criteria`, `reversibility`,
  `blast_radius`, `verification_artifacts`, `error_journal[].rule_created`)
  remain `Draft` and may still iterate.
- **RFC-004 (Migration & Backward Compatibility — "Never break the soul")**
  — promoted to `Proposed`. Freezes the §3 sub-principles, the §4 decisions,
  the §5.4 staged pipeline (`v2.5 → v3.x → v3.5.1 → v4`), the §6
  reader-vs-writer matrix, the §7 legacy / unknown / `x_*` rules, and the
  §8 rollback model. Open decisions (§12) remain open and do not block the
  promotion.
- **RFC-003 (Context Cost Benchmark)** — unchanged, stays `Draft` pending
  benchmark execution (Road-to-V4-GA item P1-3).
- **RFC-006 (`agent_core`)** — unchanged, stays `Draft` (post-GA / future
  work, Road-to-V4-GA item P1-7).

This promotion is the recommended next step from
[`docs/roadmap/ROAD-TO-V4-GA.md`](docs/roadmap/ROAD-TO-V4-GA.md) §5: it freezes
the conceptual surface **before** the strict v4 JSON Schema (P0-2) and
normative SPEC v4 (P0-1) work begins, avoiding a schema-first / RFC-after
divergence.

**What does NOT change:**
- No schema files touched (`schema/`, `schemas/`).
- No SDK code touched (`packages/pypi/klickd`, `packages/@klickd/core`).
- No test vectors touched.
- No envelope, AAD, KDF, or crypto change.
- v3.5.1 remains the production-recommended format.
- v4.0.0-preview.1 remains the only preview release, with the same
  `additionalProperties: true` permissive schemas.

---

## v4.0.0-preview.1 (preview, NOT GA) — 2026-05-23 — v4 preview track

> **Status: PREVIEW / NON-NORMATIVE / NOT GA.**
> Stable, recommended production format remains **v3.5.1** (unchanged).
> This entry summarises the additive v4 preview track. The wire envelope,
> crypto, and AAD construction are unchanged: `klickd_version` stays at
> `"3.0"`; only the inner payload may opt in via
> `payload_schema_version = "4.0.0-preview.1"`.

### Distribution version mapping

A single preview milestone is shipped across two registries with registry-native
prerelease syntax:

| Channel  | Identifier               | Notes                                                   |
| -------- | ------------------------ | ------------------------------------------------------- |
| git tag  | `v4.0.0-preview.1`       | annotated, GitHub Release marked **Pre-release**        |
| npm      | `@klickd/core@4.0.0-preview.1` | published under the `preview` dist-tag, NOT `latest` |
| PyPI     | `klickd==4.0.0a1`        | PEP 440 pre-release; `pip install klickd` resolves to **3.5.1** |
| Zenodo   | *(deferred)*             | no DOI minted for the preview; pending field-by-field validation |

`pip install klickd` continues to resolve to **3.5.1** because PEP 440 excludes
pre-releases by default. Opt in explicitly with `pip install --pre klickd` or
`pip install klickd==4.0.0a1`. Likewise `npm install @klickd/core` continues to
resolve to **3.5.1**; the preview must be requested with
`@klickd/core@preview` or `@klickd/core@4.0.0-preview.1`.

### Specification

- **SPEC §33 — `.klickd` v4 Preview** (non-normative, additive over v3.5.1).
  Introduces the preview payload surface, the unknown-field preservation rule
  (`must_preserve_fields`), the dual-reader contract (v3.x readers MUST ignore
  preview fields; v4-preview readers MUST round-trip unknown fields), and the
  preview deprecation/sunset policy.

### Schemas (permissive)

- `schemas/klickd-payload-v4-preview.schema.json` and
  `schema/klickd-v4-preview.schema.json` — JSON Schema Draft 2020-12, deliberately
  permissive (`additionalProperties: true`). No strict business validation, no
  migration enforcement.

### SDKs — round-trip preservation (additive)

- Python (`packages/pypi/klickd`) and TypeScript (`packages/@klickd/core`) decode
  paths preserve unknown / preview fields verbatim on read and re-emit them on
  write. v3.x consumers are unaffected.
- No new public API surface for v4 validation. No migration helpers. Preview
  fields are opaque to the libraries.

### Test vectors

- `tests/vectors_v40_preview.json` (7 positive vectors) exercising the v4
  preview payload surface: minimal payload, `media_profile`,
  `verification_gates`, `claim_sources` + `verification_artifacts`,
  `migration` report, `context_cost`, and unknown-field passthrough.
- Wire envelope stays at `klickd_version="3.0"` (v3 envelope crypto/AAD); the
  inner payload alone carries `payload_schema_version="4.0.0-preview.1"`.
- Byte-stable regeneration via `scripts/generate_v40_preview_vectors.py`
  (fixed salts/IVs).
- `verify_vectors.py` and `verify_vectors.mjs` each gain a v4 preview suite
  asserting decrypt success, `payload_schema_version` match, and deep-equality
  of `must_preserve_fields` after round-trip. Existing v2.5 / v3.0 / negative /
  adversarial suites are unchanged. The TS verifier skips gracefully when
  `hash-wasm` is not installed.

### Benchmarks — Context Cost (RFC-003)

- `benchmarks/context_cost/` — fixtures-only benchmark scaffold for measuring
  context-cost trade-offs of `.klickd` profiles vs raw prompts.
- Local **dry-run** runner (`runner.py`) — no provider calls, no network, no
  API keys. Produces deterministic local artefacts only.
- Optional edge-case fixtures: migration, tool-failure, multi-session.
- Status: Draft. Not yet wired to provider scoring.

### Integrations — Hermes Agent POC

- `integrations/hermes/` — experimental POC scaffold demonstrating Hermes Agent
  as a workflow runner with `.klickd` as portable state. **Local dry-run only**;
  not a production integration. No live provider calls.

### Design documents (drafts, non-normative)

- **RFC-001** — `media_profile` (draft, v4-preview surface).
- **RFC-002** — `verification_gates` + `human_veto`, plus `verification_artifacts`
  / artifact-tee rule (v2 draft).
- **RFC-003** — Context Cost Benchmark (draft, fixtures + dry-run runner).
- **RFC-004** — Migration & Backward Compatibility (draft, docs-only).
- All RFCs live under `docs/rfcs/` and are explicitly non-normative until
  promoted by a future GA release.

### Release artefacts (this PR)

- `docs/releases/v4.0.0-preview.1.md` — release notes draft, suitable for a
  future GitHub release / Zenodo deposit when (and only when) the project
  decides to publish a preview build.
- `docs/releases/CHECKLIST_v4_preview.md` — preview publication checklist
  (tagging, `npm publish --tag preview`, PyPI prerelease, Zenodo
  field-by-field validation).

### Compatibility & guarantees

- Preview track is **additive and permissive**: no strict v4 business
  validation, no migration enforcement, no breaking change to v3.x.
- Unknown preview fields MUST be preserved on decode (`must_preserve_fields`).
- Existing invalid-envelope rejection rules continue to apply.
- v3.5.1 remains the stable, current production format and the only version
  carrying a published DOI, npm package, and PyPI distribution.

### Not in this preview

- No Zenodo deposit and no DOI minted for the preview (deferred pending
  field-by-field validation; concept DOI `10.5281/zenodo.20262530` is unchanged).
- No strict v4 validator or migration runner.

---

## v3.5.1 — 2026-05-22 — P0 conformance fixes

ATLAS-audit P0 alignment across schemas, libs, vectors, and docs.

### cipher.name casing — canonical = `"AES-256-GCM"` (uppercase)

- **Canonical**: `cipher.name` MUST be `"AES-256-GCM"` (matches `schema/klickd-v3.4.schema.json` enum and `schemas/klickd-envelope-v3.schema.json` const, npm package type, and SPEC.md normative pseudocode).
- **Legacy compat**: readers MUST accept `"aes-256-gcm"` (lowercase) with a deprecation warning. Old vectors keep loading.
- **Producers**: `save_klickd.py`, `scripts/generate_v30_vectors.py`, `scripts/generate_advanced_vectors.py` now emit the canonical uppercase form.
- **Test vectors**: `tests/vectors_v30.json` and `tests/vectors_v31_advanced.json` regenerated. Adversarial `adv-13` flipped from "reject uppercase" to "reject mixed-case `Aes-256-Gcm`".

### `user_preferences` canonical type = `string`

- Canonical type aligned with SPEC.md §22.6, `schema/klickd-v3.4.schema.json`, examples, and `load_klickd.py`: **string**, max 32,768 bytes UTF-8.
- `schemas/klickd-payload-v3.schema.json`, `packages/@klickd/core/src/types.ts`, `packages/pypi/klickd/src/klickd/_types.py` updated to accept `string | object` (canonical = string; object retained for backward compatibility with pre-v3.4 files).
- `load_klickd.build_system_prompt()` now JSON-serialises dict-form `user_preferences` before prompt injection.

### Schema directory disambiguation

- Added `SCHEMA_INDEX.md` (root) and `schema/README.md`, `schemas/README.md` distinguishing the **unified** vs **split** v3 schema directories.

---

## v3.4.2-patch1 — 2026-05-20

### Bug fix — `load_klickd.py` v3.3

**BUG:** `build_system_prompt()` was injecting the onboarding loader block twice when `onboarding_trigger = "on_new_agent"` AND `agent_instructions` already contained the same block (as embedded by the Klickd app generator). Result: any agent loading a Klickd-generated `.klickd` file would ask the user for their profile file **twice** in the same system prompt.

**FIX:** Added a `_loader_already_present` guard that checks `combined` (merged `user_preferences` + `agent_instructions`) for 5 language-specific markers before injecting the §29b block:
- `".klickd Profile Loader"` (EN/DE/LB header)
- `"On First Message"` (EN app generator)
- `".klickd à charger"` (FR)
- `".klickd-Profil"` (DE)
- `".klickd-Fichier"` (LB)

If any marker is found → skip §29b injection entirely. The block from `agent_instructions` is kept as-is.

**Verified:** Both cases tested — file with embedded loader (no duplicate), file without loader (block injected correctly).

---

## v3.4.1 — 2026-05-20

### Soul Handoff Transmission Rules (normative)

#### New section: SPEC §28.8
- **Guaranteed transmission fields** (7 fields that MUST always appear in any Soul Handoff, regardless of `compression_policy` or length pressure): `context.resume_trigger`, `error_patterns` (top 2), `mood`, `learning_goal.achieved` (if true), `data_integrity.integrity_warning` (if true), `known_disabilities` active flags, `preferred_session_length.hard_limit` (if true)
- **Mandatory semi-structured format**: Soul Handoff MUST use `key:value` format — free prose prohibited. Length targets: 60 chars minimum · 100–200 recommended · 300 hard cap
- **`compression_policy.mode` interaction table**: standard (all §28.8.2 fields) / selective (`priority_fields` order after guaranteed) / aggressive (guaranteed fields only)
- **Agent B required behaviour on reading handoff**: `integrity_warning` before any content, `achieved: true` triggers congratulation before advice, disability flags trigger format adaptation, `hard_limit` enforced on full response
- **3 concrete handoff examples** (aggressive / standard / full-flags)

#### Benchmark results (v3.4 final)
- 105 profils valides across 21 lots (19 standard + 2 Soul Handoff dedicated)
- Global delta: **+19.4 pts average** (43.1/50 WITH vs 23.7/50 WITHOUT)
- Soul Handoff v3.4: **+22.3 pts** (40.7/50 WITH vs 18.4/50 WITHOUT) — up from +16.0 in v3.3 (+39%)
- Best case: SHB-P05 TDAH+dyslexie SVT — **+38 pts** (39/50 vs 1/50)
- Perfect scores: avocat junior, CrossFit coaching, maths prépa socratic, philosophie socratic (4× 50/50)

#### SKILL.md §14 update (v6.1)
- "Soul Handoff summary" subsection added as implementer quick-reference
- Guaranteed fields table with priority ordering
- Agent B reading rules (7 normative behaviours)
- Cross-reference to SPEC §28.8

#### Option B — onboarding_trigger (v3.4)
- New field `onboarding_trigger`: `on_new_agent | manual | auto_inject`
- SPEC §29b: full specification with 4-language prompts (FR/EN/DE/LB)
- SKILL.md §14bis: "New Agent Onboarding" — flow diagram, rules, multilingual prompt
- `load_klickd.py`: `build_system_prompt()` injects "Profile Loader" block if `onboarding_trigger == on_new_agent`
- `KaiPersonnel.tsx`: `handleExport` auto-injects `onboarding_trigger: on_new_agent` + i18n block in `agent_instructions`
- Principle: instruction travels in `agent_instructions` → works on any agent without native field support

---

## v3.3 — 2026-05-19

### Security (Phase 1)

#### New fields
- `injection_resistance_level` (top-level enum: `strict | moderate | permissive`, default `permissive`)
  Resolves benchmark vuln: level override via user_message (Lot 10 P7) + JSON injection bypass (Lot 9 P10)
- `companion_identity` (top-level object: `name`, `persona`, `teaching_mode`, `updated_at`)
  Persistent AI companion identity across model switches. Agent reads only, never writes.
- `teaching_mode` within `companion_identity` (enum: `direct | socratic | coaching | adaptive`)
  Socratic mode: agent responds with guiding questions, never direct answers.

#### Security fixes
- §24.10 updated: JSON injection guard added as normative requirement for `user_message` injection
- §25.3: JSON Injection Guard — MUST prepend security instruction to system prompt when injection_target includes user_message

#### Phase 3 — Universal competency layer
- `occupational_competencies` (§26) — ISCO-08 backbone, 7 frameworks, 7 competency types
- New competency types: `physical`, `safety`, `civic`, `sustainability`
- 23 world frameworks referenced (EU, USA, Asia-Pacific, International, Sectoral)

#### Phase 4 — Format refinements
- `numerical_results[].data_type` enum: scalar | vector | formula | equation
- Resumption rule: top-3 numerical_results MUST be cited in first response (normative)
- `knowledge.struggles[].category` enum: conceptual | procedural | linguistic | motivational
- `archived_sessions[].key_numerical_results` array (max 5 per archived session)
- `subject_change_detected` extended to enum: none | detected | confirmed | reverted
- `context.interruption_points` array (§24.11) — multiple checkpoints per session

#### Breaking changes
- None. All new fields are optional and default-backward-compatible.

#### Benchmark evidence
- 100 profiles across 10 domains (v3.2 re-benchmark ×10)
- Global score AVEC .klickd: 8.52/10 vs 3.84/10 SANS (delta +4.68)
- resume_trigger: 97% | numerical_results verbatim: 96% | hallucinations: 0% AVEC
- Soul Handoff (Agent A → Agent B): delta +16 pts
- Full results: benchmarks/v32/RAPPORT_CONSOLIDÉ_V32.md

---

## [3.2] — 2026-05-19

### 12 Benchmark-Driven Improvements

- **numerical_results** (`context`): Array of `{label, value, unit?, formula?}` objects (max 200). Agents MUST cite these values verbatim when resuming sessions.
- **interruption_point** (`context`): Object capturing the precise point of session interruption — `ts`, `last_message_excerpt` (512 chars), `topic`, `subtopic`, `completion_pct` (0–100). Agents MUST resume from this exact point.
- **resume_trigger** (`context`): Exact phrase the agent MUST output at the start of a resumed session to signal continuity.
- **knowledge.struggles**: Array of `{concept, severity, context}` objects (max 100). Severity enum: `minor | moderate | blocking`. Agents MUST NOT re-explain mastered content but SHOULD revisit struggles.
- **vocabulary_used** (`knowledge`): Array of domain-specific terms (max 500, 128 chars each). Agents MUST reuse this exact vocabulary in resumed sessions.
- **context.mode**: Enum `full | lightweight` (default: `full`). Lightweight mode reduces overhead for simple sessions.
- **archived_sessions** (top-level): Array of compressed past-session summaries (max 50). Bounds file growth by archiving old sessions out of active `memory[]`.
- **language_switch_detected** (`context`): Boolean flag — context survives language switches.
- **subject_change_detected** (`context`): Boolean flag — agent SHOULD acknowledge previous session pause and create a new context branch.
- **injection_target** (top-level): Enum `system_prompt | user_message | both` (default: `system_prompt`). `user_message` may improve verbatim recall for some models.
- **§23 Model-Specific Behaviors** (SPEC.md): Documents Gemini implicit assimilation, small-model cautious posture, and gemma2-9b-it deprecation.
- **domain_schema_version** example bump: `education-1.0` → `education-1.2`; new fields documented in SKILL.md.

### Updated Files
- `schemas/klickd-payload-v3.schema.json` — bumped title to v3.2, `$id` URL to v3.2, all new fields added
- `SPEC.md` — v3.2 header, §23 Model-Specific Behaviors added, all new fields documented
- `SKILL.md` — usage examples for `numerical_results`, `interruption_point`, `resume_trigger`, `vocabulary_used`
- `load_klickd.py` — `build_system_prompt` handles all new context fields
- `klickd_v320_spec.pdf` — updated specification PDF

---

## [v6.0] - 2026-05-18

### Security & Hardening (Grok Audits 2–5)

- **Major security release** — All P0 and P1 issues from five adversarial audits resolved.
- Rewrote `save_klickd.py` to full v3.0 (Argon2id default, 6-field JCS AAD, structured `kdf`/`cipher` blocks).
- Fixed `build_system_prompt` injection order — `.klickd` context now correctly placed **before** base system prompt (§12).
- Added proper RFC 8785 JCS with NFC Unicode normalisation in both Python and JavaScript.
- Implemented layered defensive controls:
  - `_whitehat_scan()` — prototype pollution + suspicious keyword detection (hard fail on `__proto__`, `constructor`, `prototype`)
  - `_enforce_ethics()` — `locked_actions` must be `list[str]`
  - `_validate_growth()` — enforces level ≤ 5 and `memory_refs ≥ 3` at level 5
- `cipher.name` and `kdf.name` now strictly validated (case-sensitive).
- `build_system_prompt` now safely merges both `user_preferences` **and** `agent_instructions` when both are present.
- Added `ensure_ascii=False` for UTF-8 consistency in envelope writing.

### Testing

- All previous tests passing (32/32).
- Added **15 new adversarial test vectors** in `tests/adversarial/` covering every defensive layer (prototype pollution, ethics bypass, growth inflation, size bombs, merge logic attacks, multi-layer stress tests, etc.).
- Final Grok Audit 5 (adversarial payload testing) — **0 critical or high-severity bypasses** found.

### Final Status

**v6.0 is now shipping.**  
The format has been thoroughly stress-tested and is considered production-ready.

**Grok Final Verdict**: Secure, spec-compliant, and battle-hardened.

---

## [3.0 / Skill v6.0] — 2026-05-18

### Added
- `personality` payload block (§18quater): `core_traits[]` (label + strength 0–1 + note), `temperament` (9 presets), `voice` (tone/formality/verbosity/uses_analogies/avoids), `values[]` (ordered, first = primary), `evolution` tracking
- `Knowledge Commons` registry (§18quinquies): `registry/` directory in repo — competency templates, personality presets, domain taxonomy, all CC0
- Registry seed files: `registry/REGISTRY_VERSION.txt` (1.0.0), `registry/domains/registry.json` (10 domains, EN/FR/DE/LB), 2 competency templates, 3 personality vocabulary files
- `growth.last_registry_sync` + `last_registry_sync_at` fields
- `AUDIT_v60.md` — full security audit dossier
- `SECURITY.md`, `CONTRIBUTING.md`, `ROADMAP.md`, `CHANGELOG.md`
- README.md updated with v3.0 banner, full feature table, accurate repo structure

### Security
- Agent MUST read `personality` block before first response; MUST NOT auto-modify it
- Network effect loop documented: privacy-preserving contribution protocol (strip personal fields → hash contributor → anonymous PR)

---

## [3.0 / Skill v5.0] — 2026-05-18

### Added
- `whitehat` swarm (§18): `role=whitehat` memory entries, 8-step audit checklist, 12 known prompt injection pattern categories, swarm coordination via encrypted payload, veille cadence (weekly / daily for finance+legal+health / critical on untrusted load)
- `growth` competency graph (§18bis): `competencies[]` with UUID, label, domain, subdomain, level 1–5, acquired_at, last_exercised_at, memory_refs, depends_on, tags. Max 2,000 entries. Level 5 requires ≥3 memory_refs.
- `ethics` block (§18ter): `locked_actions` at SYSTEM authority, `critical_systems_locked` (nuclear, power_grid, water_treatment, hospital_systems, financial_clearing, election_infrastructure, satellite_control), `owner_consent_required`, `immutable: true`
- §18ter.4: 7 absolute anti-blackhat prohibitions (spec-level, non-overridable)
- Authority hierarchy: `ethics > host system prompt > agent_instructions > user_preferences > in-session`

---

## [3.0 / Skill v4.0] — 2026-05-18 — BREAKING

### Breaking changes
- Envelope format v3.0 replaces v2.x. **v2.x readers MUST reject v3.0 files** (`KLICKD_E_VERSION`).
- `salt` and `iv` moved out of top-level envelope into structured `kdf` and `cipher` blocks
- `updated_at` field removed from envelope (not part of AAD)
- AAD expanded from 4 fields to 6 (adds `kdf` and `cipher` objects)

### Added
- **Argon2id** as default KDF (m=65536/t=3/p=1), replacing PBKDF2-SHA256 as default
- **RFC 8785 JCS** canonicalization for AAD — deterministic, cross-language (replaces Python-specific `json.dumps` with `sort_keys`)
- Structured `kdf` block: `{name, params, salt}`
- Structured `cipher` block: `{name, iv}`
- `payload_schema_version` and `domain_schema_version` in inner payload
- Full error taxonomy: `KLICKD_E_AUTH`, `KLICKD_E_VERSION`, `KLICKD_E_FORMAT`, `KLICKD_E_KDF`, `KLICKD_E_WEAK_PASS`, `KLICKD_E_SCHEMA`
- `agent_instructions` 32 KiB hard cap (§22), enforced in JSON Schema (`maxLength: 32768`)
- JSON Schema 2020-12: `schemas/klickd-envelope-v3.schema.json` + `schemas/klickd-payload-v3.schema.json`
- §17.4: v2.x backward-read AAD documented (4 fields: `created_at`, `domain`, `encrypted`, `klickd_version`)
- Argon2id parameter floor validation (decoder MUST reject m<1024, t<1, p<1 → `KLICKD_E_KDF`)
- `verify_vectors.mjs`: multi-version runner using hash-wasm WASM Argon2id — 17/17 + 1 documented skip
- Python test suite: 32/32 (v2.5 pos/neg + v3.0 pos/neg)
- GitHub Actions CI: `.github/workflows/test-vectors.yml`

### Fixed (Bankr audit — all 8 issues)
- BUG-1 (P0): `verify_vectors.mjs` was v2.5-only → multi-version runner with hash-wasm
- BUG-2: Self-retracted by Bankr
- BUG-3 (P1): `@klickd/core` Argon2id dependency → peerDeps `argon2` + `argon2-browser` (optional)
- BUG-4 (P1): §17 JCS key order hardcoded → algorithm-first rewrite (§17.1), informative note (§17.3)
- BUG-5 (P1): v2.x backward-read AAD undocumented → §17.4 added
- BUG-6 (P2): Cross-impl test gap → CI runs all 4 suites
- BUG-7 (P1): `agent_instructions` no size cap → §22 + JSON Schema `maxLength=32768`
- BUG-8 (P2): DOI 404 concern → confirmed 302→200 redirect, Zenodo live

---

## [2.5] — 2026-05-18

### Added
- Normative `memory[]` array (UUID v4, RFC 3339, modality, tags, hard limits)
- 18 test vectors (v2.5 pos + neg) — 18/18 PASS Python + JS

---

## [2.0] — 2026-05-18

### Added
- Universal release: multi-domain (education, work, finance, legal, creative, health, research, robotics, custom)
- CC0 1.0 license
- Robotics extension: `robot_profile`, USB/NFC handoff
- "Any body" framing
- DOI published: 10.5281/zenodo.20262530

---

## [1.0] — 2026-05-16

- Initial release: education domain only, PBKDF2-SHA256, flat envelope
