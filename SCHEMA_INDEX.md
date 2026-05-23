# Schema Index

`.klickd` ships **two** JSON-Schema directories. They are intentionally distinct, not duplicates.

| Directory | Form | When to use |
|-----------|------|-------------|
| [`schema/`](./schema/) | **Unified** — one file per spec version validates the whole document. Files: `klickd-v1.json`, `klickd-v2.json`, `klickd-v3.4.schema.json`. | Single-pass validators, schema registries, third-party tooling. |
| [`schemas/`](./schemas/) | **Split** — separate envelope and payload schemas for v3. Files: `klickd-envelope-v3.schema.json`, `klickd-payload-v3.schema.json`. | Secure decoders that validate the envelope *before* decryption and the payload *after*. |

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
- **Strict v4 validation?** Not in this preview. A future PR will introduce strict v4 schemas; until then, the preview schemas are deliberately loose.
- **Unknown fields?** A v4-preview reader MUST preserve unknown fields verbatim when round-tripping. See SPEC.md §33.7.

See [SPEC.md §33](./SPEC.md) and the RFCs under [`docs/rfcs/`](./docs/rfcs/) for the design source.
