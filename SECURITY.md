# Security Policy — .klickd Format

## Responsible Disclosure

If you discover a security vulnerability in the `.klickd` specification, reference implementations, or test vectors, please report it **privately** before any public disclosure:

**Email:** Luxlearn@pm.me  
**Subject:** `[SECURITY] .klickd — <brief description>`

We aim to respond within 72 hours and to publish a fix or advisory within 30 days of a confirmed issue.

Do **not** open a public GitHub issue for security vulnerabilities.

---

## Threat Model

### What `.klickd` protects against

| Threat | Protection |
|---|---|
| Unauthorized payload access | AES-256-GCM — without the passphrase, plaintext is unrecoverable |
| Ciphertext tampering | GCM tag covers ciphertext + AAD — any byte flip → `KLICKD_E_AUTH` |
| Envelope metadata tampering | AAD covers all 6 envelope fields (kdf, cipher, domain, version, created_at, encrypted) |
| KDF parameter downgrade attack | kdf.params are inside AAD and authenticated — cannot be weakened post-encryption |
| Weak passphrase at encode time | Encoder MUST reject < 8 Unicode code points (`KLICKD_E_WEAK_PASS`) |
| IV reuse within a file | Fresh 12-byte IV per encryption via CSPRNG |
| Salt reuse | Fresh 16-byte salt per encryption via CSPRNG |
| Prompt injection via agent_instructions | Spec mandates `agent_instructions` treated as untrusted user-context (never system-level) |
| Ethics block tampering | Encrypted + GCM-authenticated + no server copy — modification is detectable |

### What `.klickd` does NOT protect against

| Limitation | Notes |
|---|---|
| Weak passphrase brute force | Argon2id is intentionally expensive, but a short or common passphrase remains vulnerable. Recommend 16+ characters. |
| Runtime memory disclosure | Plaintext is present in process memory during decryption. No spec-level protection against memory dumps. |
| Side-channel attacks | No constant-time requirement for tag comparison beyond what the underlying library provides (Python `cryptography`, Web Crypto). |
| Metadata confidentiality | `klickd_version`, `domain`, `created_at`, `kdf`, and `cipher` parameters are plaintext in the envelope. |
| Multi-user access | No public-key or key-wrapping mechanism. Single passphrase only. |
| Forward secrecy | Passphrase disclosure compromises all files encrypted with that passphrase. |
| Endpoint compromise | If the device or agent runtime is compromised, plaintext can be extracted during decryption. |
| Rollback / replay | No monotonic counter or trusted timestamp. An attacker with the passphrase could replay an older file. |

---

## Cryptographic Parameters

### Argon2id (v3.0 default)

| Parameter | Minimum (spec floor) | Default | Recommended (high-security) |
|---|---|---|---|
| m (memory, KiB) | 1,024 | 65,536 (64 MiB) | ≥ 131,072 (128 MiB) |
| t (iterations) | 1 | 3 | ≥ 4 |
| p (parallelism) | 1 | 1 | 1–4 |

Decoders MUST reject files with kdf.params below the spec floor (`KLICKD_E_KDF`).

### PBKDF2-SHA256 (v2.x legacy — read path only)

| Parameter | Minimum | v2.x default |
|---|---|---|
| iterations | 600,000 | 600,000 |
| salt length | 16 bytes | 16 bytes |

### AES-256-GCM

- Key: 256 bits derived from KDF
- IV: 12 bytes, fresh CSPRNG per encryption
- Tag: 16 bytes, appended to ciphertext blob
- AAD: RFC 8785 JCS of the 6-field envelope object

---

## Known Limitations & Open Issues

1. **No IV reuse protection at scale** — In high-volume automated contexts (e.g., agent generating thousands of `.klickd` files per day), the birthday paradox applies at ~2^32 encryptions with a random 96-bit IV. Mitigate with a counter-based IV scheme for high-volume producers (not yet in spec).

2. **No forward secrecy** — A single compromised passphrase unlocks all files. Future versions may introduce key-wrapping via a separate device key.

3. **agent_instructions injection risk** — Any content in `agent_instructions` is controlled by the file creator, not the host model. Implementations MUST treat this field as untrusted user input (never elevate to system prompt). The `whitehat` swarm entries (§18 of SKILL.md) scan for known injection patterns on load.

4. **Passphrase strength** — The spec rejects passphrases < 8 characters and warns below 12. We recommend 16+ for production use. No zxcvbn-style entropy check is currently mandated.

5. **No IANA MIME registration yet** — `application/vnd.klickd+json` is used by convention; registration is pending.

---

## Versions & Patching

| Version | Status | Notes |
|---|---|---|
| v3.0 (envelope) / v6.0 (skill) | **Current** | Argon2id, JCS AAD, structured blocks |
| v2.5 | Legacy read-only | PBKDF2, flat envelope, 4-field AAD |
| v2.0 and earlier | Deprecated | Do not implement |

Security fixes are applied to the current version only. Legacy v2.x is not patched.

---

## Audit History

| Date | Auditor | Scope | Result |
|---|---|---|---|
| 2026-05-18 | Bankr (adversarial) | v2.5 + v3.0 spec, load_klickd.py, verify_vectors | 8 issues found — all fixed (see `AUDIT_v60.md`) |
| 2026-05-18 | Grok / xAI | v3.0 + v6.0 dossier review | Doc fragmentation flagged — fixed in this release |
