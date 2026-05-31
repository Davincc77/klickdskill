# Schema Index

`.klickd` ships **two** JSON-Schema directories. They are intentionally distinct, not duplicates. For the full repository layout and the rationale behind preserved paths, see [`docs/STRUCTURE.md`](./docs/STRUCTURE.md).

| Directory | Form | When to use |
|-----------|------|-------------|
| [`schema/`](./schema/) | **Unified** — one file per spec version validates the whole document. Files: `klickd-v1.json`, `klickd-v2.json`, `klickd-v3.4.schema.json`, `klickd-v4-preview.schema.json` (preview), `klickd-v4.schema.json` (GA strict candidate). | Single-pass validators, schema registries, third-party tooling. |
| [`schemas/`](./schemas/) | **Split** — separate envelope and payload schemas. Files: `klickd-envelope-v3.schema.json`, `klickd-payload-v3.schema.json`, `klickd-payload-v4-preview.schema.json` (preview), `klickd-payload-v4.schema.json` (GA strict candidate). | Secure decoders that validate the envelope *before* decryption and the payload *after*. |

Both directories are **normative for v3.x (production, current and recommended)** and are kept in sync. The split form (`schemas/`) is the canonical pre-/post-decrypt boundary; the unified form (`schema/`) is the convenience form for single-shot validation.

## Canonical type contracts (v3.5)

- `cipher.name` MUST be `"AES-256-GCM"` (canonical, uppercase). Legacy lowercase `"aes-256-gcm"` is accepted by readers with a deprecation warning; new producers MUST emit the canonical form.
- `user_preferences` canonical type is `string` (≤32 KiB UTF-8). The `object` form is retained for backward compatibility with pre-v3.4 files.

See [`SPEC.md`](./SPEC.md) for normative details.

---

## v4 Preview schemas (NON-NORMATIVE, NOT GA)

In addition to the normative v3 schemas, the repository ships **permissive preview schemas** targeting `.klickd v4.0.0-preview.1`. These are part of the same `.klickd` standard family — the next **preview track**, not a separate standard.

| File | Form | Status | When to use |
|------|------|--------|-------------|
| [`schemas/klickd-payload-v4-preview.schema.json`](./schemas/klickd-payload-v4-preview.schema.json) | **Split — payload** | **PREVIEW, non-normative** | Accept and round-trip draft v4 payloads (`media_profile`, `verification_gates`, `human_veto_policy`, `claim_sources`, `verification_artifacts`, `migration`, `context_cost`, `profile_kind`). |
| [`schema/klickd-v4-preview.schema.json`](./schema/klickd-v4-preview.schema.json) | **Unified** | **PREVIEW, non-normative** | Single-pass acceptance of a draft v4 document, including the optional preview hooks. |

**These schemas are PERMISSIVE.** They use `additionalProperties: true` and only declare top-level hooks for the preview fields. They are intended to **accept and preserve** draft v4 structures, not to perform strict validation. They MUST NOT be used to reject a file that is otherwise a valid v3.5.1 file.

- **Normative for production?** No. Production validation MUST use `schema/klickd-v3.4.schema.json` or the split v3 schemas under `schemas/`.
- **Strict v4 validation?** See the **v4 GA strict schemas** section below.
- **Unknown fields?** A v4-preview reader MUST preserve unknown fields verbatim when round-tripping. See SPEC.md §33.7.

See [SPEC.md §33](./SPEC.md) and the RFCs under [`docs/rfcs/`](./docs/rfcs/) for the design source.

---

## v4 GA strict schemas (P0-2 — coexist with preview, do NOT supersede it)

To unblock the GA track described in [`docs/roadmap/ROAD-TO-V4-GA.md` §P0-2](./docs/roadmap/ROAD-TO-V4-GA.md), the repository now also ships **strict v4 schemas**. The preview schemas remain in place unchanged: both pairs coexist until the preview sunset is announced separately.

| File | Form | Status | When to use |
|------|------|--------|-------------|
| [`schemas/klickd-payload-v4.schema.json`](./schemas/klickd-payload-v4.schema.json) | **Split — payload** | **GA strict candidate (normative target)** | Strict validation of a `.klickd` v4 decrypted payload: `verification_gates` (v1 core enum), `human_veto_policy`, `claim_sources` (v1), `media_profile` (RFC-001 v1, `version`+`entries[]`, hash strict), `migration` (RFC-004 v1 frozen fields), plus carry-over v3 surface. RFC-002 v2-additive fields (`reversibility`, `blast_radius`, `contract_tests`, `success_criteria`, `verification_artifacts`) remain permissive while Draft. |
| [`schema/klickd-v4.schema.json`](./schema/klickd-v4.schema.json) | **Unified** | **GA strict candidate (normative target)** | Strict validation of a full v4 document. Encrypted files MUST carry `kdf` + `cipher` + `ciphertext` (envelope-v3 contract unchanged per §33.10 #2). |

**Coexistence rules:**

- Preview schemas (`*-v4-preview.schema.json`) remain authoritative for **preview** files (`preview: "v4.0.0-preview.1"`). They MUST continue to accept all preview vectors.
- Strict schemas (`klickd-payload-v4.schema.json`, `klickd-v4.schema.json`) are the **GA strict target**. They accept both `payload_schema_version: "4.0"` (GA) and the legacy preview value `"4.0.0-preview.1"` so the 5 persona examples and preview vectors round-trip against them.
- **Top-level `additionalProperties: true` is preserved.** SPEC.md §33.7 (unknown-field preservation) is unconditional and not relaxed by the strict schemas.
- **No SDK is bumped.** No npm / PyPI / Zenodo release is triggered. No git tag is created.

**Validation:** see [`scripts/validate_v4_schemas.py`](./scripts/validate_v4_schemas.py) for the canonical local validation runner.

**Cross-impl strict vectors (P0-6 — PR candidate):**

- Positive: [`tests/vectors_v40_ga.json`](./tests/vectors_v40_ga.json) — 5 persona payloads (`profile_kind` learner/team/agent/creator/learner+gaming) covering the v1 frozen surface of `verification_gates` (structured + flat-map), `human_veto_policy`, `claim_sources`, `media_profile`, `migration`, plus one unified `encrypted=true` envelope (envelope-v3 contract retained per SPEC §33.10 #2).
- Negative: [`tests/negative_vectors_v40_ga.json`](./tests/negative_vectors_v40_ga.json) — 12 rejection cases pinning each frozen rule (gate-level enum, missing/unknown `payload_schema_version`, `media_profile` v1 hash/modality strictness, `human_veto_policy.min_level`, encrypted envelope completeness, `klickd_version` major range, `migration.migrated_at` RFC 3339 Z, `gateEntry` / `human_veto_policy` `additionalProperties: false`).
- Runners: [`verify_vectors.py`](./verify_vectors.py) (canonical `jsonschema` validation + structural assertions) and [`verify_vectors.mjs`](./verify_vectors.mjs) (structural rule checker mirroring the strict schema — no Ajv dep required at root). Both implementations validate the same fixtures and reject the same negatives without divergence. Preview vectors ([`tests/vectors_v40_preview.json`](./tests/vectors_v40_preview.json)) remain intact.
