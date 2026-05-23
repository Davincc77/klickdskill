# `schema/` — Unified single-file schemas (v1, v2, v3.4)

This directory contains **unified** JSON Schemas — each file validates a complete `.klickd` document (envelope + inline-or-encrypted payload) for one spec version:

| File | Spec version | Notes |
|------|--------------|-------|
| `klickd-v1.json` | v1.x | Legacy. Single-block encryption metadata. |
| `klickd-v2.json` | v2.x | PBKDF2-SHA256 + 4-field AAD. |
| `klickd-v3.4.schema.json` | v3.4 (current) | Argon2id + RFC 8785 JCS AAD + `kdf`/`cipher` blocks. Forward-compatible with v3.5 fields. |
| `klickd-v4-preview.schema.json` | **v4.0.0-preview.1 (PREVIEW, non-normative, NOT GA)** | Permissive (`additionalProperties: true`) acceptance schema for draft v4 documents with top-level hooks for `media_profile` / `verification_gates` / `human_veto_policy` / `claim_sources` / `verification_artifacts` / `migration` / `context_cost` / `profile_kind`. See SPEC.md §33. |

**Use these files** when a single-schema validation is sufficient (CI tooling, third-party integrations, schema registries).

For the **split** v3 envelope/payload schemas (envelope validated before decryption, payload after), see [`../schemas/`](../schemas/).

## Canonical type contracts (v3.5)

- `cipher.name` MUST be `"AES-256-GCM"` (canonical, uppercase). Legacy lowercase `"aes-256-gcm"` SHOULD be accepted by readers with a deprecation warning, but MUST NOT be emitted by new producers.
- `user_preferences` canonical type is `string` (≤32 KiB UTF-8). The `object` form is retained for backward compatibility with pre-v3.4 files.

See [`SPEC.md`](../SPEC.md) for the normative specification.
