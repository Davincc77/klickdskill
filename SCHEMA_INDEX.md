# Schema Index

`.klickd` ships **two** JSON-Schema directories. They are intentionally distinct, not duplicates.

| Directory | Form | When to use |
|-----------|------|-------------|
| [`schema/`](./schema/) | **Unified** — one file per spec version validates the whole document. Files: `klickd-v1.json`, `klickd-v2.json`, `klickd-v3.4.schema.json`. | Single-pass validators, schema registries, third-party tooling. |
| [`schemas/`](./schemas/) | **Split** — separate envelope and payload schemas for v3. Files: `klickd-envelope-v3.schema.json`, `klickd-payload-v3.schema.json`. | Secure decoders that validate the envelope *before* decryption and the payload *after*. |

Both directories are normative for v3.x and are kept in sync. The split form (`schemas/`) is the canonical pre-/post-decrypt boundary; the unified form (`schema/`) is the convenience form for single-shot validation.

## Canonical type contracts (v3.5)

- `cipher.name` MUST be `"AES-256-GCM"` (canonical, uppercase). Legacy lowercase `"aes-256-gcm"` is accepted by readers with a deprecation warning; new producers MUST emit the canonical form.
- `user_preferences` canonical type is `string` (≤32 KiB UTF-8). The `object` form is retained for backward compatibility with pre-v3.4 files.

See [`SPEC.md`](./SPEC.md) for normative details.
