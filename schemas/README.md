# `schemas/` — Split v3 envelope + payload schemas

This directory contains the **split** JSON Schemas for `.klickd` v3:

| File | Scope |
|------|-------|
| `klickd-envelope-v3.schema.json` | Outer JSON envelope (encrypted). Validates `klickd_version`, `kdf`, `cipher`, `ciphertext`, AAD-relevant fields. |
| `klickd-payload-v3.schema.json` | Inner decrypted payload. Validates `identity`, `agent_instructions`, `user_preferences`, `context`, `knowledge`, `memory`, etc. |
| `klickd-payload-v4-preview.schema.json` | **v4.0.0-preview.1 payload (PREVIEW, non-normative, NOT GA).** Permissive (`additionalProperties: true`) acceptance schema for draft v4 payloads with top-level hooks for `media_profile` / `verification_gates` / `human_veto_policy` / `claim_sources` / `verification_artifacts` / `migration` / `context_cost` / `profile_kind`. See SPEC.md §33. |
| `klickd-payload-v4.schema.json` | **v4 GA strict candidate (P0-2).** Strict payload schema: `verification_gates` (v1 enum), `human_veto_policy`, `claim_sources` (v1), `media_profile` (RFC-001 v1, `version`+`entries[]`, BLAKE3 hash strict), `migration` (RFC-004 v1 frozen fields). RFC-002 v2-additive fields (`reversibility`, `blast_radius`, `contract_tests`, `success_criteria`, `verification_artifacts`) remain permissive while Draft. Top-level `additionalProperties: true` preserved (SPEC.md §33.7). Coexists with the preview schema — does NOT supersede it. |

**Use this split form** when you need to validate the envelope *before* decryption and the payload *after* decryption as two independent steps (typical of secure decoders that fail-fast on the envelope).

For the unified single-file schemas (v1, v2, v3.4 combined), see [`../schema/`](../schema/).

## Canonical type contracts (v3.5)

- `cipher.name` MUST be `"AES-256-GCM"` (canonical, uppercase). Legacy lowercase `"aes-256-gcm"` SHOULD be accepted by readers with a deprecation warning, but MUST NOT be emitted by new producers.
- `user_preferences` canonical type is `string` (≤32 KiB UTF-8). The `object` form is retained for backward compatibility with pre-v3.4 files.

See [`SPEC.md`](../SPEC.md) for the normative specification.
