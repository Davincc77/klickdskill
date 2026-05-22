# `schemas/` — Split v3 envelope + payload schemas

This directory contains the **split** JSON Schemas for `.klickd` v3:

| File | Scope |
|------|-------|
| `klickd-envelope-v3.schema.json` | Outer JSON envelope (encrypted). Validates `klickd_version`, `kdf`, `cipher`, `ciphertext`, AAD-relevant fields. |
| `klickd-payload-v3.schema.json` | Inner decrypted payload. Validates `identity`, `agent_instructions`, `user_preferences`, `context`, `knowledge`, `memory`, etc. |

**Use this split form** when you need to validate the envelope *before* decryption and the payload *after* decryption as two independent steps (typical of secure decoders that fail-fast on the envelope).

For the unified single-file schemas (v1, v2, v3.4 combined), see [`../schema/`](../schema/).

## Canonical type contracts (v3.5)

- `cipher.name` MUST be `"AES-256-GCM"` (canonical, uppercase). Legacy lowercase `"aes-256-gcm"` SHOULD be accepted by readers with a deprecation warning, but MUST NOT be emitted by new producers.
- `user_preferences` canonical type is `string` (≤32 KiB UTF-8). The `object` form is retained for backward compatibility with pre-v3.4 files.

See [`SPEC.md`](../SPEC.md) for the normative specification.
