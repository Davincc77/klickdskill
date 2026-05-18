# SPEC.md — The .klickd File Format Specification
## Version 3.0 · Normative Technical Specification

**DOI:** 10.5281/zenodo.20262530  
**Status:** Current  
**License:** CC0 1.0 Universal (see §29)  
**Replaces:** v2.x (deprecated), v1.0 (legacy)

---

## Table of Contents

1. [Abstract](#1-abstract)
2. [Status of This Document](#2-status-of-this-document)
3. [Terminology](#3-terminology)
4. [File Format Overview](#4-file-format-overview)
5. [File Recognition](#5-file-recognition)
6. [Envelope Structure — v3.0](#6-envelope-structure--v30)
7. [Encrypted Payload — Internal Schema](#7-encrypted-payload--internal-schema)
8. [Identity Object](#8-identity-object)
9. [Context Object](#9-context-object)
10. [Knowledge Object](#10-knowledge-object)
11. [Memory Array](#11-memory-array)
12. [user_preferences Object](#12-user_preferences-object)
13. [domain_schema_version](#13-domain_schema_version)
14. [Key Derivation — Argon2id (Default)](#14-key-derivation--argon2id-default)
15. [Key Derivation — PBKDF2-SHA256 (Legacy)](#15-key-derivation--pbkdf2-sha256-legacy)
16. [Cipher — AES-256-GCM](#16-cipher--aes-256-gcm)
17. [AAD Construction](#17-aad-construction)
18. [Encryption Process](#18-encryption-process)
19. [Decryption Process](#19-decryption-process)
20. [JSON Schema 2020-12](#20-json-schema-2020-12)
21. [Error Codes](#21-error-codes)
22. [Size Limits](#22-size-limits)
23. [Versioning Policy](#23-versioning-policy)
24. [Threat Model](#24-threat-model)
25. [Test Vectors](#25-test-vectors)
26. [MIME Type Registration](#26-mime-type-registration)
27. [Conformance](#27-conformance)
28. [References](#28-references)
29. [License](#29-license)
30. [Changelog](#30-changelog)

---

## 1. Abstract

The `.klickd` file format is a portable, encrypted, self-describing container for AI agent identity, context, knowledge, memory, and user preferences. A `.klickd` file consists of a single UTF-8 JSON document (the *envelope*) whose confidential payload is encrypted with AES-256-GCM, with a key derived from a user passphrase via Argon2id. The format is domain-aware, versioned, and designed for deterministic, cross-language implementation. This document is the normative specification for version 3.0 of the format, which introduces JCS (RFC 8785) canonicalization for authenticated additional data (AAD), a structured `kdf`/`cipher` envelope, Argon2id as the default key-derivation function, and a versioned inner payload schema.

---

## 2. Status of This Document

This document defines version 3.0 of the `.klickd` file format. It is the authoritative specification for implementers building encoders, decoders, validators, or tooling in any programming language. Compliance with the MUST-level requirements in §27 is required for a conformant implementation. SHOULD-level requirements are strongly recommended.

Version 3.0 is **not backward-compatible** with version 2.x at the envelope level. Decoder implementations MUST NOT silently accept a v2.x envelope as a v3.0 envelope. Implementations that support both versions MUST branch on `klickd_version` before applying any parsing logic.

Errata and clarifications will be tracked at https://klickd.app/spec/v3/errata.

---

## 3. Terminology

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in [RFC 2119] and [RFC 8174] when, and only when, they appear in all capitals.

The following terms are used throughout this specification:

| Term | Definition |
|---|---|
| **Envelope** | The outer JSON document stored on disk with the `.klickd` extension. |
| **Payload** | The inner JSON document produced by decrypting the envelope's `ciphertext` field. |
| **AAD** | Authenticated Additional Data — the canonical byte string authenticated by AES-256-GCM but not encrypted. |
| **KDF** | Key Derivation Function — a one-way function used to derive a symmetric key from a passphrase. |
| **JCS** | JSON Canonicalization Scheme — the deterministic serialization algorithm defined in RFC 8785. |
| **GCM tag** | The 128-bit (16-byte) authentication tag appended to the ciphertext by AES-256-GCM. |
| **Domain** | A semantic category string that identifies the application context of the payload. |
| **CSPRNG** | Cryptographically Secure Pseudo-Random Number Generator. |
| **Implementer** | Any person or system writing software that reads or writes `.klickd` files. |
| **Encoder** | An implementation that creates `.klickd` files. |
| **Decoder** | An implementation that reads and decrypts `.klickd` files. |

---

## 4. File Format Overview

A `.klickd` file is a single UTF-8 JSON document (the *envelope*). In encrypted mode (`"encrypted": true`), the envelope contains:

- Metadata fields identifying the format version, domain, creation time, and algorithm parameters.
- A `kdf` object describing the key derivation algorithm and its parameters.
- A `cipher` object describing the symmetric cipher and its parameters.
- A `ciphertext` field containing the base64-encoded AES-256-GCM ciphertext concatenated with the 16-byte GCM authentication tag.

The confidential *payload* is the plaintext obtained by decrypting `ciphertext`. The payload is a UTF-8 JSON document encoding identity, context, knowledge, memory, and preferences.

### 4.1 Design Goals

1. **Portability.** A `.klickd` file is a single file, transferable across operating systems and platforms without modification.
2. **Determinism.** The AAD byte string MUST be identical regardless of which conformant encoder produced it, enabling reliable GCM authentication across implementations.
3. **Algorithm agility.** The `kdf.name` and `cipher.name` fields allow future algorithm negotiation without a major version bump (within major version compatibility rules defined in §23).
4. **Domain awareness.** The `domain` field and `domain_schema_version` field allow domain-specific payload schemas to evolve independently of the envelope format.
5. **Auditability.** All non-secret algorithm parameters are stored in plaintext in the envelope and are authenticated via AAD.

### 4.2 Non-Goals

The format does not provide:

- Key exchange or public-key encryption (the format is symmetric, passphrase-based only in v3.0).
- Multi-recipient encryption.
- Streaming or chunked encoding.
- Compression (implementers MAY compress the inner payload before encryption but this is not standardized).

---

## 5. File Recognition

### 5.1 File Extension

Conformant `.klickd` files MUST use the file extension `.klickd` (lowercase). Case-insensitive filesystems MAY accept `.KLICKD` but encoders MUST write lowercase.

### 5.2 MIME Type

The registered MIME type for `.klickd` files is:

```
application/vnd.klickd+json
```

IANA registration is pending (see §26).

### 5.3 Content Detection

A file SHOULD be identified as a `.klickd` v3.0 file when:

1. It is valid UTF-8.
2. It is valid JSON at the top level (an object).
3. The top-level JSON object contains the key `"klickd_version"` with a string value beginning with `"3."`.

Implementations MUST NOT use the file extension alone as the sole means of format identification. The `klickd_version` key MUST be checked.

### 5.4 BOM

The UTF-8 byte order mark (BOM, U+FEFF encoded as 0xEF 0xBB 0xBF) MUST NOT appear at the start of a `.klickd` file. Decoders encountering a BOM MUST return `KLICKD_E_FORMAT`.

---

## 6. Envelope Structure — v3.0

The envelope is the top-level JSON object stored on disk. In encrypted mode all fields listed in the table below are REQUIRED.

### 6.1 Field Table

| Field | Type | Required | Constraints |
|---|---|---|---|
| `klickd_version` | string | MUST | MUST match pattern `^3\.` for v3.0 files. Decoders MUST reject unknown major versions with `KLICKD_E_VERSION`. |
| `encrypted` | boolean | MUST | MUST be `true` in encrypted mode. |
| `domain` | string | MUST | One of the registered values (see §6.2) or any non-empty string for custom domains. MUST NOT be empty. |
| `created_at` | string | MUST | RFC 3339 UTC timestamp. MUST use `Z` suffix. Pattern: `^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$`. Fractional seconds are NOT permitted. |
| `kdf` | object | MUST | See §6.3. |
| `cipher` | object | MUST | See §6.4. |
| `ciphertext` | string | MUST | RFC 4648 §4 standard base64 (padded) encoding of `ciphertext_bytes ‖ gcm_tag_bytes`. Minimum decoded length: 16 bytes (tag only, zero-length plaintext). |

`additionalProperties` are NOT permitted in the envelope. Decoders receiving an envelope with additional top-level keys MUST return `KLICKD_E_FORMAT`.

### 6.2 Registered Domain Values

The following domain values are defined in v3.0:

| Value | Description |
|---|---|
| `education` | Learning, tutoring, curriculum, progress tracking |
| `work` | Professional tasks, project management, workflows |
| `finance` | Personal or organizational financial planning |
| `legal` | Legal research, document review, compliance |
| `creative` | Writing, art, design, ideation |
| `health` | Health tracking, medical information, wellness |
| `research` | Academic or scientific research |
| `robotics` | Robotic systems, embedded agents, control loops |

Custom domain strings are permitted and MUST be treated as opaque by decoders that do not recognize them. Unknown domain values MUST NOT cause a decoding failure.

### 6.3 The `kdf` Object

| Field | Type | Required | Constraints |
|---|---|---|---|
| `name` | string | MUST | `"argon2id"` or `"pbkdf2-sha256"`. Other values MAY be supported in future minor versions; unknown values MUST trigger `KLICKD_E_KDF`. |
| `params` | object | MUST | Algorithm-specific parameters. See §14 and §15. |
| `salt` | string | MUST | RFC 4648 §4 standard base64 (padded). MUST decode to at least 16 bytes. Encoders MUST generate 16 bytes from a CSPRNG. |

`additionalProperties` are NOT permitted in the `kdf` object.

### 6.4 The `cipher` Object

| Field | Type | Required | Constraints |
|---|---|---|---|
| `name` | string | MUST | MUST be `"AES-256-GCM"`. |
| `iv` | string | MUST | RFC 4648 §4 standard base64 (padded). MUST decode to exactly 12 bytes. Encoders MUST generate 12 bytes from a CSPRNG. |

`additionalProperties` are NOT permitted in the `cipher` object.

### 6.5 Reference Envelope Example

```json
{
  "klickd_version": "3.0",
  "encrypted": true,
  "domain": "education",
  "created_at": "2026-05-18T14:23:00Z",
  "kdf": {
    "name": "argon2id",
    "params": {"m": 65536, "t": 3, "p": 1},
    "salt": "dGVzdHNhbHQxMjM0NTY="
  },
  "cipher": {
    "name": "AES-256-GCM",
    "iv": "dGVzdGl2MTIz"
  },
  "ciphertext": "<base64(ciphertext || 16-byte GCM tag)>"
}
```

---

## 7. Encrypted Payload — Internal Schema

The payload is the JSON document obtained after successful decryption and GCM authentication. It MUST be a valid UTF-8 JSON object. The BOM MUST NOT appear. Decoders MUST NOT parse the payload JSON until GCM authentication has succeeded (see §19).

### 7.1 Field Table

| Field | Type | Required | Constraints |
|---|---|---|---|
| `payload_schema_version` | string | MUST | MUST be `"3.0"` for payloads produced by a v3.0 encoder. |
| `domain_schema_version` | string | MUST | Pattern `^[a-z][a-z0-9_-]*-\d+\.\d+$` (e.g., `"education-1.0"`). See §13. |
| `identity` | object | SHOULD | See §8. MAY be omitted for anonymous payloads. |
| `agent_instructions` | string | SHOULD | System-prompt injection string. See §7.2. |
| `user_preferences` | object | SHOULD | See §12. Advisory only. |
| `context` | object | SHOULD | See §9. |
| `knowledge` | object | SHOULD | See §10. |
| `memory` | array | SHOULD | See §11. Maximum 1000 entries. |

`additionalProperties` are permitted in the payload for forward compatibility within a major version, provided they are not in conflict with reserved field names.

### 7.2 agent_instructions vs. user_preferences

`agent_instructions` is a **plain string** intended for direct injection into an AI system's system prompt. It is an imperative directive to the agent and MUST be treated as authoritative by consuming agents.

`user_preferences` is an **object** expressing user preferences that SHOULD influence agent behavior but are ADVISORY ONLY (see §12). An agent MAY override user_preferences in service of safety, correctness, or legal compliance.

### 7.3 Reference Payload Example

```json
{
  "payload_schema_version": "3.0",
  "domain_schema_version": "education-1.0",
  "identity": {
    "name": "Alex",
    "language": "en",
    "timezone": "America/New_York",
    "communication_style": "concise"
  },
  "agent_instructions": "You are a personalized math tutor for Alex. Prioritize step-by-step explanations and Socratic questioning.",
  "user_preferences": {
    "response_length": "short",
    "avoid_topics": ["politics"]
  },
  "context": {
    "current_state": "Studying differential equations",
    "decisions_locked": [],
    "artifacts": [],
    "summary": "Alex is working through first-order ODEs."
  },
  "knowledge": {
    "mastered": ["algebra", "trigonometry"],
    "gaps": ["integration by parts"],
    "next_steps": ["Practice separation of variables"]
  },
  "memory": []
}
```

---

## 8. Identity Object

The `identity` object encodes persistent, user-declared identity attributes used to personalize agent behavior. All fields are OPTIONAL.

| Field | Type | Constraints |
|---|---|---|
| `name` | string | Human-readable display name. MAY be a pseudonym. Maximum 256 characters. |
| `language` | string | BCP 47 language tag (e.g., `"en"`, `"fr-CA"`). Decoders SHOULD use this to configure language-sensitive agent behavior. |
| `timezone` | string | IANA time zone identifier (e.g., `"America/New_York"`, `"UTC"`). |
| `communication_style` | string | Advisory preference for response style. Examples: `"concise"`, `"verbose"`, `"formal"`, `"casual"`. |

`additionalProperties` are permitted in the `identity` object for domain-specific extensions.

---

## 9. Context Object

The `context` object captures the current operational state of the agent session. All fields are OPTIONAL.

| Field | Type | Constraints |
|---|---|---|
| `current_state` | string | Free-text description of the current working state or task. Maximum 2048 characters. |
| `decisions_locked` | array of strings | List of decisions that MUST NOT be revisited in the session. Each element is a plain-text decision statement. |
| `artifacts` | array of objects | Session artifacts (documents, outputs, etc.). Each element SHOULD have `"id"` (string), `"type"` (string), and `"ref"` (string) fields. |
| `summary` | string | Concise plain-text summary of the session context for agent priming. Maximum 4096 characters. |

`additionalProperties` are permitted for domain-specific context extensions.

---

## 10. Knowledge Object

The `knowledge` object encodes structured knowledge state about the user or session subject. All fields are OPTIONAL.

| Field | Type | Constraints |
|---|---|---|
| `mastered` | array of strings | Topics or skills the user has demonstrated mastery of. Each element is a plain-text label. Maximum 500 entries. |
| `gaps` | array of strings | Topics or skills identified as knowledge gaps. Each element is a plain-text label. Maximum 500 entries. |
| `next_steps` | array of strings | Recommended next actions or learning objectives. Each element is a plain-text instruction. Maximum 100 entries. |

`additionalProperties` are permitted for domain-specific knowledge extensions.

---

## 11. Memory Array

The `memory` field is a JSON array of memory entry objects. It provides a structured, portable conversation and event log.

### 11.1 Limits (Normative)

| Limit | Value |
|---|---|
| Maximum entries | 1000 |
| Maximum size per entry | 10,240 bytes (10 KiB), measured as the UTF-8 byte length of the serialized JSON entry object |
| Maximum total memory array size | 5,242,880 bytes (5 MiB), measured as the UTF-8 byte length of the serialized JSON array |

Encoders MUST enforce these limits and MUST return `KLICKD_E_FORMAT` if any limit would be violated. Decoders MUST validate these limits and MUST return `KLICKD_E_FORMAT` if any limit is exceeded.

### 11.2 Memory Entry Field Table

Each element of the `memory` array MUST be a JSON object conforming to the following schema:

| Field | Type | Required | Constraints |
|---|---|---|---|
| `id` | string | MUST | UUID version 4, formatted as `xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx` (RFC 4122). Case-insensitive on read; encoders MUST write lowercase. |
| `ts` | string | MUST | RFC 3339 UTC timestamp with `Z` suffix. Pattern: `^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z$`. Fractional seconds are OPTIONAL. |
| `role` | string | MUST | One of: `"user"`, `"assistant"`, `"system"`. |
| `content` | string | MUST | The text or serialized content of the memory entry. Maximum 10,240 bytes when UTF-8 encoded. |
| `modality` | string | MUST | One of: `"text"`, `"image"`, `"audio"`, `"tool_call"`. |
| `tags` | array of strings | OPTIONAL | Zero or more plain-text tags for categorization. Each tag MUST NOT exceed 64 bytes (UTF-8). Maximum 32 tags per entry. |

`additionalProperties` are permitted in memory entry objects for forward compatibility.

### 11.3 Ordering

Memory entries SHOULD be ordered by `ts` ascending (oldest first). Decoders MUST NOT assume any particular ordering and SHOULD sort by `ts` before use.

### 11.4 Example Memory Entry

```json
{
  "id": "a1b2c3d4-e5f6-4789-abcd-ef0123456789",
  "ts": "2026-05-18T14:30:00Z",
  "role": "user",
  "content": "Explain the difference between separation of variables and integrating factors.",
  "modality": "text",
  "tags": ["ode", "question"]
}
```

---

## 12. user_preferences Object

The `user_preferences` object encodes user-declared preferences that SHOULD influence agent behavior. Decoders and consuming agents MUST treat the entire `user_preferences` object as **ADVISORY ONLY**.

An agent:
- MUST NOT treat `user_preferences` as security-sensitive policy.
- MAY override any `user_preferences` value for safety, legal, accuracy, or correctness reasons.
- SHOULD log any preference override for auditability.

`user_preferences` uses open-ended properties; no fixed schema is mandated. Known preference keys include:

| Key | Type | Description |
|---|---|---|
| `response_length` | string | Advisory response length: `"short"`, `"medium"`, `"long"`. |
| `avoid_topics` | array of strings | Topics the user wishes to avoid. Advisory; safety overrides apply. |
| `preferred_format` | string | Advisory output format: `"markdown"`, `"plain"`, `"html"`. |
| `locale` | string | BCP 47 locale string (may overlap with `identity.language`). |

`additionalProperties` are explicitly permitted. Implementations MUST NOT reject a payload because `user_preferences` contains unrecognized keys.

---

## 13. domain_schema_version

### 13.1 Format

`domain_schema_version` MUST conform to the pattern:

```
^[a-z][a-z0-9_-]*-\d+\.\d+$
```

The string consists of a domain label, a hyphen, and a `major.minor` semver-like version. Examples:

| Value | Meaning |
|---|---|
| `education-1.0` | Education domain, schema version 1.0 |
| `work-2.1` | Work domain, schema version 2.1 |
| `robotics-1.0` | Robotics domain, schema version 1.0 |

### 13.2 Evolution Rules

- A **minor version increment** (e.g., `1.0` → `1.1`) indicates backward-compatible additions: new OPTIONAL fields or new OPTIONAL enum values. Decoders built for `1.0` MUST be able to process `1.1` payloads (unknown fields are ignored).
- A **major version increment** (e.g., `1.x` → `2.0`) indicates breaking changes. Decoders built for `1.x` are not required to process `2.0` payloads and SHOULD return `KLICKD_E_SCHEMA` for unrecognized major versions.
- The `domain_schema_version` is independent of `klickd_version`. A domain schema may increment without any change to the envelope format.

### 13.3 Custom Domains

Custom domain labels (not in the registered list in §6.2) are permitted. The `domain_schema_version` for custom domains is controlled by the defining party. Decoders MUST NOT reject a payload solely because the domain label is unrecognized.

---

## 14. Key Derivation — Argon2id (Default)

Argon2id [RFC 9106] is the default KDF for v3.0. Encoders MUST use Argon2id unless the implementation environment does not support it (see §15 for the legacy alternative).

### 14.1 Parameters

| Parameter | Field | Minimum | Default | Description |
|---|---|---|---|---|
| Memory cost | `m` | 65536 | 65536 | Memory usage in kibibytes (64 MiB minimum) |
| Time cost (iterations) | `t` | 1 | 3 | Number of passes |
| Parallelism | `p` | 1 | 1 | Degree of parallelism |
| Output length | — | 32 | 32 | Bytes; fixed at 32 for AES-256 |
| Salt length | `salt` | 16 | 16 | Bytes |

Encoders MUST NOT use values below the stated minimums. Encoders SHOULD use the stated defaults. Higher values SHOULD be used in security-sensitive deployments.

### 14.2 `kdf.params` for Argon2id

```json
{
  "name": "argon2id",
  "params": {"m": 65536, "t": 3, "p": 1},
  "salt": "<base64(16 random bytes)>"
}
```

### 14.3 Key Derivation Call

```
key = Argon2id(
  password = passphrase_utf8_bytes,
  salt     = base64_decode(kdf.salt),
  m        = kdf.params.m,
  t        = kdf.params.t,
  p        = kdf.params.p,
  taglen   = 32
)
```

The passphrase MUST be encoded as UTF-8 before passing to Argon2id. The derived `key` is 32 bytes.

### 14.4 Passphrase Requirements

Encoders MUST reject a passphrase shorter than 8 characters (measured in Unicode code points) and MUST return `KLICKD_E_WEAK_PASS`. Decoders SHOULD warn (but MUST NOT reject) when the passphrase is shorter than 12 characters.

---

## 15. Key Derivation — PBKDF2-SHA256 (Legacy)

PBKDF2-SHA256 [RFC 8018] is a legacy KDF supported for environments where Argon2id is unavailable. **Encoders MUST use Argon2id by default.** Encoders MAY emit `pbkdf2-sha256` only when Argon2id is genuinely unavailable in the target environment (e.g., restricted WASM environments). Decoders MAY accept `pbkdf2-sha256` in v3.0 envelopes for migration compatibility. New implementations MUST NOT select PBKDF2-SHA256 unless Argon2id is genuinely unavailable.

### 15.1 Parameters

| Parameter | Field | Minimum | Description |
|---|---|---|---|
| Iterations | `iterations` | 600000 | Iteration count |
| PRF | — | HMAC-SHA-256 | Fixed |
| Output length | — | 32 | Bytes; fixed at 32 |
| Salt length | `salt` | 16 | Bytes |

Encoders MUST use at least 600,000 iterations. Decoders MUST return `KLICKD_E_KDF` if `iterations` is below this minimum.

### 15.2 `kdf.params` for PBKDF2-SHA256

```json
{
  "name": "pbkdf2-sha256",
  "params": {"iterations": 600000},
  "salt": "<base64(16 random bytes)>"
}
```

### 15.3 Key Derivation Call

```
key = PBKDF2-HMAC-SHA256(
  password   = passphrase_utf8_bytes,
  salt       = base64_decode(kdf.salt),
  iterations = kdf.params.iterations,
  dklen      = 32
)
```

---

## 16. Cipher — AES-256-GCM

All v3.0 `.klickd` files use AES-256-GCM (NIST SP 800-38D) for authenticated encryption.

### 16.1 Parameters

| Parameter | Value |
|---|---|
| Algorithm | AES-256-GCM |
| Key size | 256 bits (32 bytes) |
| IV size | 96 bits (12 bytes) |
| Tag size | 128 bits (16 bytes) |
| Tag position | Appended to ciphertext |

### 16.2 Ciphertext Encoding

The `ciphertext` field encodes:

```
base64_standard( encrypt_output_bytes || gcm_tag_16_bytes )
```

The GCM authentication tag is appended directly to the raw ciphertext bytes before base64 encoding. Decoders MUST split off the last 16 bytes as the GCM tag before passing to the AES-GCM decrypt primitive.

Decoders MUST return `KLICKD_E_FORMAT` if the decoded `ciphertext` field is shorter than 16 bytes.

### 16.3 IV Uniqueness

Encoders MUST generate a fresh IV from a CSPRNG for every encryption operation. Encoders MUST NOT reuse a (key, IV) pair under any circumstances. IV reuse under AES-GCM catastrophically compromises both confidentiality and authenticity.

---

## 17. AAD Construction

The Authenticated Additional Data (AAD) byte string MUST be constructed using RFC 8785 JSON Canonicalization Scheme (JCS). This ensures that AAD is byte-for-byte identical across all conformant implementations regardless of language or platform.

### 17.1 Fields Included in AAD

**Algorithm:** The AAD is produced by applying JCS (RFC 8785) to the sub-object of the envelope that contains all fields **except** `ciphertext` and any payload-internal fields. Concretely, for v3.0 this is the object with exactly these 6 keys:

```
klickd_version, encrypted, domain, created_at, kdf, cipher
```

The `ciphertext` field is NOT included in AAD — it is already authenticated by the GCM tag.

Implementers MUST apply JCS to derive the canonical byte string. **Implementers MUST NOT hardcode a specific field order** — the order is determined by JCS and will shift if new fields are added in future minor versions. Always build the input object and let JCS sort it.

### 17.2 JCS Canonicalization

Given the envelope object `E`, construct the AAD input object as:

```json
{
  "klickd_version": E.klickd_version,
  "encrypted":      E.encrypted,
  "domain":         E.domain,
  "created_at":     E.created_at,
  "kdf":            E.kdf,
  "cipher":         E.cipher
}
```

Apply RFC 8785 JCS to produce the canonical byte string. JCS rules:

- Keys are sorted lexicographically by Unicode code point value.
- No insignificant whitespace.
- String values use `\uXXXX` escaping only where required by RFC 8785 §3.2.2.2.
- Numbers use the shortest decimal representation.
- The output is UTF-8 encoded.

**klickd NFC extension (normative):** Before applying JCS, all string values in the AAD input object MUST be Unicode-normalized to NFC (Canonical Decomposition followed by Canonical Composition, per Unicode Standard Annex #15). This is a klickd-specific requirement beyond RFC 8785, which does not mandate Unicode normalization. Without NFC normalization, implementations using decomposed forms (e.g., `"cafe\u0301"` vs `"caf\u00E9"`) would produce different AAD bytes and fail GCM authentication. All conformant klickd JCS implementations MUST apply NFC normalization before canonicalization.

The resulting UTF-8 byte string is used directly as the AAD parameter to AES-256-GCM.

### 17.3 Observed JCS Output Order (Informative)

For the 6 AAD fields defined in v3.0, JCS lexicographic sort of the key names produces the following output order:

```
cipher, created_at, domain, encrypted, kdf, klickd_version
```

This is an **informative observation**, not a normative requirement. The normative requirement is §17.2: apply RFC 8785 JCS. If a future minor version (v3.1) adds a field to the AAD set (e.g., `aad_extension`), the JCS output order will change, and implementations relying on the hardcoded v3.0 order will silently produce incorrect AAD. Always apply JCS; never template the AAD byte string.

### 17.4 v2.x Backward-Read AAD Field Set

When a conformant v3.0 implementation reads a **v2.x envelope** (i.e., `klickd_version` starts with `"2"`), it MUST use the **v2.x AAD field set**, not the v3.0 6-field set. The v2.x AAD is computed from exactly 4 fields:

```
klickd_version, encrypted, domain, created_at
```

Apply the same JCS algorithm to these 4 fields. The JCS output order for these keys is:

```
created_at, domain, encrypted, klickd_version
```

A v3.0 implementation that uses the 6-field AAD (including `kdf` and `cipher`) when decrypting a v2.x file **will always fail GCM authentication**, because the `kdf` and `cipher` blocks did not exist in v2.x envelopes. Implementations MUST branch on the major version number before constructing AAD.

### 17.5 AAD Construction Example

Input object (before JCS):
```json
{
  "klickd_version": "3.0",
  "encrypted": true,
  "domain": "education",
  "created_at": "2026-05-18T14:23:00Z",
  "kdf": {"name": "argon2id", "params": {"m": 65536, "t": 3, "p": 1}, "salt": "dGVzdHNhbHQxMjM0NTY="},
  "cipher": {"name": "AES-256-GCM", "iv": "dGVzdGl2MTIz"}
}
```

After JCS canonicalization, the output will be a compact, key-sorted UTF-8 string. Implementers MUST verify their JCS output against the test vectors in §25.

---

## 18. Encryption Process

The following steps describe the normative encryption process for a v3.0 `.klickd` file.

1. **Validate passphrase.** Count Unicode code points in the passphrase. If fewer than 8, return `KLICKD_E_WEAK_PASS`.

2. **Serialize the payload.** Encode the inner payload object as a compact UTF-8 JSON string, without BOM, without insignificant whitespace. Verify the resulting byte string does not exceed 4,194,304 bytes (4 MiB); if exceeded, return `KLICKD_E_FORMAT`.

3. **Generate salt.** Generate 16 cryptographically random bytes using a CSPRNG. Base64-encode (RFC 4648 §4, padded) to produce `kdf.salt`.

4. **Generate IV.** Generate 12 cryptographically random bytes using a CSPRNG. Base64-encode (RFC 4648 §4, padded) to produce `cipher.iv`.

5. **Construct the partial envelope.** Build the envelope JSON object with all fields except `ciphertext`, using `klickd_version: "3.0"` and the generated `kdf` and `cipher` objects.

6. **Derive the key.** Apply the KDF (Argon2id or PBKDF2-SHA256) as specified in §14 or §15 to produce a 32-byte key.

7. **Construct AAD.** Apply JCS to the 6-field object `{klickd_version, encrypted, domain, created_at, kdf, cipher}` (see §17). The result is a UTF-8 byte string.

8. **Encrypt.** Apply AES-256-GCM:
   ```
   (ciphertext_bytes, tag_bytes) = AES-256-GCM-Encrypt(
     key     = derived_key,
     iv      = base64_decode(cipher.iv),
     aad     = aad_bytes,
     plaintext = payload_utf8_bytes
   )
   ```

9. **Encode ciphertext.** Concatenate `ciphertext_bytes || tag_bytes` (tag appended). Base64-encode (RFC 4648 §4, padded) to produce `ciphertext`.

10. **Finalize envelope.** Add the `ciphertext` field to the envelope object.

11. **Serialize envelope.** Encode the complete envelope as a UTF-8 JSON string. Verify the resulting byte string does not exceed 1,048,576 bytes (1 MiB); if exceeded, return `KLICKD_E_FORMAT`.

12. **Zero the key.** Overwrite the derived key bytes from memory as soon as possible after use.

---

## 19. Decryption Process

The following steps describe the normative decryption process for a v3.0 `.klickd` file.

1. **Read the file.** Read the file as UTF-8. Return `KLICKD_E_FORMAT` if a BOM is detected, if the file is not valid UTF-8, or if the file is not valid JSON.

2. **Check envelope size.** Return `KLICKD_E_FORMAT` if the raw file byte length exceeds 1,048,576 bytes (1 MiB).

3. **Parse envelope.** Parse the JSON as an object. Return `KLICKD_E_FORMAT` if any required field is missing or if any disallowed additional property is present.

4. **Check version.** Extract `klickd_version`. Return `KLICKD_E_VERSION` if the major version (the integer before the first `.`) is not recognized by the implementation.

5. **Validate algorithm.** Check `kdf.name`. If unknown or unsupported, return `KLICKD_E_KDF`. Check `kdf.params` against the minimums in §14.1 or §15.1 as appropriate.

6. **Decode base64 fields.** Decode `kdf.salt`, `cipher.iv`, and `ciphertext` using RFC 4648 §4 standard base64. Return `KLICKD_E_FORMAT` for any malformed base64 string. Verify:
   - `kdf.salt` decodes to at least 16 bytes.
   - `cipher.iv` decodes to exactly 12 bytes.
   - `ciphertext` decodes to at least 16 bytes.
   Return `KLICKD_E_FORMAT` if any check fails.

7. **Derive the key.** Apply the KDF using the passphrase and `kdf` parameters.

8. **Construct AAD.** Apply JCS to the 6-field object `{klickd_version, encrypted, domain, created_at, kdf, cipher}` exactly as in §17.

9. **Split ciphertext and tag.** The last 16 bytes of the decoded `ciphertext` are the GCM tag. The remaining bytes are the ciphertext.

10. **Decrypt and authenticate.** Apply AES-256-GCM-Decrypt:
    ```
    plaintext_bytes = AES-256-GCM-Decrypt(
      key        = derived_key,
      iv         = decoded_iv,
      aad        = aad_bytes,
      ciphertext = ciphertext_bytes,
      tag        = tag_bytes
    )
    ```
    If GCM authentication fails, return `KLICKD_E_AUTH`. Implementations MUST NOT return any partial plaintext on authentication failure.

11. **Parse payload.** Parse `plaintext_bytes` as UTF-8 JSON. Return `KLICKD_E_FORMAT` if the result is not a valid UTF-8 JSON object. Verify `payload_schema_version` matches expectations; return `KLICKD_E_SCHEMA` for unrecognized versions.

12. **Validate payload size.** Return `KLICKD_E_FORMAT` if the plaintext byte length exceeds 4,194,304 bytes (4 MiB).

13. **Zero the key.** Overwrite the derived key bytes from memory as soon as possible after use.

---

## 20. JSON Schema 2020-12

This section contains the normative JSON Schema 2020-12 definitions for both the envelope and the payload. These schemas are the authoritative reference for format validation.

The schemas are also available at the following canonical URLs:

- **Envelope:** https://klickd.app/schemas/v3/klickd-envelope.schema.json
- **Payload:** https://klickd.app/schemas/v3/klickd-payload.schema.json

### 20.1 Envelope Schema

**File:** `klickd-envelope-v3.schema.json`

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://klickd.app/schemas/v3/klickd-envelope.schema.json",
  "title": "klickd Envelope v3.0",
  "description": "Normative schema for the .klickd envelope (outer JSON structure, encrypted mode).",
  "type": "object",
  "required": [
    "klickd_version",
    "encrypted",
    "domain",
    "created_at",
    "kdf",
    "cipher",
    "ciphertext"
  ],
  "additionalProperties": false,
  "properties": {
    "klickd_version": {
      "type": "string",
      "pattern": "^3\\.",
      "description": "Format version. MUST be '3.x' for v3.0 files."
    },
    "encrypted": {
      "type": "boolean",
      "description": "MUST be true in encrypted mode."
    },
    "domain": {
      "type": "string",
      "minLength": 1,
      "description": "Semantic domain category. Registered values or any non-empty string for custom domains."
    },
    "created_at": {
      "type": "string",
      "pattern": "^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}Z$",
      "description": "RFC 3339 UTC timestamp, Z-suffix only. Fractional seconds are NOT permitted."
    },
    "kdf": {
      "type": "object",
      "required": ["name", "params", "salt"],
      "additionalProperties": false,
      "description": "Key derivation function descriptor.",
      "properties": {
        "name": {
          "type": "string",
          "enum": ["argon2id", "pbkdf2-sha256"],
          "description": "KDF algorithm identifier."
        },
        "params": {
          "description": "Algorithm-specific KDF parameters.",
          "oneOf": [
            {
              "title": "Argon2id parameters",
              "type": "object",
              "required": ["m", "t", "p"],
              "additionalProperties": false,
              "properties": {
                "m": {
                  "type": "integer",
                  "minimum": 65536,
                  "description": "Memory cost in kibibytes. Minimum 65536 (64 MiB)."
                },
                "t": {
                  "type": "integer",
                  "minimum": 1,
                  "description": "Time cost (number of passes). Minimum 1."
                },
                "p": {
                  "type": "integer",
                  "minimum": 1,
                  "description": "Parallelism (number of lanes). Minimum 1."
                }
              }
            },
            {
              "title": "PBKDF2-SHA256 parameters",
              "type": "object",
              "required": ["iterations"],
              "additionalProperties": false,
              "properties": {
                "iterations": {
                  "type": "integer",
                  "minimum": 600000,
                  "description": "PBKDF2 iteration count. Minimum 600000."
                }
              }
            }
          ]
        },
        "salt": {
          "type": "string",
          "description": "RFC 4648 §4 standard base64 (padded). Decodes to at least 16 bytes."
        }
      }
    },
    "cipher": {
      "type": "object",
      "required": ["name", "iv"],
      "additionalProperties": false,
      "description": "Cipher descriptor.",
      "properties": {
        "name": {
          "type": "string",
          "const": "AES-256-GCM",
          "description": "Cipher algorithm. MUST be 'AES-256-GCM'."
        },
        "iv": {
          "type": "string",
          "description": "RFC 4648 §4 standard base64 (padded). Decodes to exactly 12 bytes."
        }
      }
    },
    "ciphertext": {
      "type": "string",
      "description": "RFC 4648 §4 standard base64. Encodes ciphertext_bytes || 16-byte GCM tag. Minimum decoded length: 16 bytes."
    }
  }
}
```

### 20.2 Payload Schema

**File:** `klickd-payload-v3.schema.json`

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://klickd.app/schemas/v3/klickd-payload.schema.json",
  "title": "klickd Payload v3.0",
  "description": "Normative schema for the .klickd inner decrypted payload.",
  "type": "object",
  "required": ["payload_schema_version", "domain_schema_version"],
  "unevaluatedProperties": true,
  "properties": {
    "payload_schema_version": {
      "type": "string",
      "const": "3.0",
      "description": "Payload schema version. MUST be '3.0' for v3.0 payloads."
    },
    "domain_schema_version": {
      "type": "string",
      "pattern": "^[a-z][a-z0-9_-]*-\\d+\\.\\d+$",
      "description": "Domain-specific schema version in '{domain}-{major}.{minor}' format (e.g., 'education-1.0')."
    },
    "identity": {
      "type": "object",
      "description": "Persistent user identity attributes.",
      "unevaluatedProperties": true,
      "properties": {
        "name": {
          "type": "string",
          "maxLength": 256,
          "description": "Human-readable display name or pseudonym."
        },
        "language": {
          "type": "string",
          "description": "BCP 47 language tag (e.g., 'en', 'fr-CA')."
        },
        "timezone": {
          "type": "string",
          "description": "IANA time zone identifier (e.g., 'America/New_York', 'UTC')."
        },
        "communication_style": {
          "type": "string",
          "description": "Advisory communication style preference (e.g., 'concise', 'verbose', 'formal', 'casual')."
        }
      }
    },
    "agent_instructions": {
      "type": "string",
      "description": "System-prompt injection string. Treated as authoritative directive to the agent."
    },
    "user_preferences": {
      "type": "object",
      "description": "Advisory user preferences. MUST be treated as advisory only by consuming agents.",
      "unevaluatedProperties": true,
      "properties": {
        "response_length": {
          "type": "string",
          "enum": ["short", "medium", "long"],
          "description": "Advisory response length preference."
        },
        "avoid_topics": {
          "type": "array",
          "items": {"type": "string"},
          "description": "Topics the user wishes to avoid. Advisory."
        },
        "preferred_format": {
          "type": "string",
          "enum": ["markdown", "plain", "html"],
          "description": "Advisory output format preference."
        },
        "locale": {
          "type": "string",
          "description": "BCP 47 locale string."
        }
      }
    },
    "context": {
      "type": "object",
      "description": "Current operational state of the agent session.",
      "unevaluatedProperties": true,
      "properties": {
        "current_state": {
          "type": "string",
          "maxLength": 2048,
          "description": "Free-text description of current working state."
        },
        "decisions_locked": {
          "type": "array",
          "items": {"type": "string"},
          "description": "Decisions that MUST NOT be revisited in the session."
        },
        "artifacts": {
          "type": "array",
          "items": {
            "type": "object",
            "unevaluatedProperties": true,
            "properties": {
              "id": {"type": "string"},
              "type": {"type": "string"},
              "ref": {"type": "string"}
            }
          },
          "description": "Session artifacts (documents, outputs, etc.)."
        },
        "summary": {
          "type": "string",
          "maxLength": 4096,
          "description": "Concise session context summary for agent priming."
        }
      }
    },
    "knowledge": {
      "type": "object",
      "description": "Structured knowledge state.",
      "unevaluatedProperties": true,
      "properties": {
        "mastered": {
          "type": "array",
          "items": {"type": "string"},
          "maxItems": 500,
          "description": "Topics or skills the user has mastered."
        },
        "gaps": {
          "type": "array",
          "items": {"type": "string"},
          "maxItems": 500,
          "description": "Identified knowledge gaps."
        },
        "next_steps": {
          "type": "array",
          "items": {"type": "string"},
          "maxItems": 100,
          "description": "Recommended next actions or learning objectives."
        }
      }
    },
    "memory": {
      "type": "array",
      "maxItems": 1000,
      "description": "Conversation and event log. Maximum 1000 entries, 10 KiB per entry, 5 MiB total.",
      "items": {
        "type": "object",
        "required": ["id", "ts", "role", "content", "modality"],
        "unevaluatedProperties": true,
        "properties": {
          "id": {
            "type": "string",
            "pattern": "^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
            "description": "UUID v4 (lowercase)."
          },
          "ts": {
            "type": "string",
            "pattern": "^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}(\\.\\d+)?Z$",
            "description": "RFC 3339 UTC timestamp with Z suffix. Fractional seconds are optional."
          },
          "role": {
            "type": "string",
            "enum": ["user", "assistant", "system"],
            "description": "Message role."
          },
          "content": {
            "type": "string",
            "description": "Entry content. Maximum 10,240 bytes (UTF-8)."
          },
          "modality": {
            "type": "string",
            "enum": ["text", "image", "audio", "tool_call"],
            "description": "Content modality."
          },
          "tags": {
            "type": "array",
            "items": {
              "type": "string",
              "maxLength": 64
            },
            "maxItems": 32,
            "description": "Optional categorization tags. Maximum 32 tags, each max 64 bytes (UTF-8)."
          }
        }
      }
    }
  }
}
```

---

## 21. Error Codes

Implementations MUST use the following error codes when returning errors related to `.klickd` processing. Each code maps to a suggested HTTP status code for implementations that expose an HTTP API.

| Error Code | HTTP Equivalent | Description | Triggered By |
|---|---|---|---|
| `KLICKD_E_AUTH` | 401 Unauthorized | GCM authentication tag verification failed. Wrong passphrase or tampered ciphertext. | Step 10 of §19 |
| `KLICKD_E_VERSION` | 422 Unprocessable Entity | `klickd_version` major version is not supported by this implementation. | Step 4 of §19 |
| `KLICKD_E_FORMAT` | 400 Bad Request | Structural or encoding error in the envelope or payload: malformed JSON, missing required fields, additional prohibited properties, malformed base64, BOM present, size limit exceeded, or ciphertext too short. | Steps 1–3, 6 of §19; §11.1; §22 |
| `KLICKD_E_KDF` | 422 Unprocessable Entity | Unknown or unsupported `kdf.name`, or `kdf.params` values below required minimums. | Step 5 of §19 |
| `KLICKD_E_WEAK_PASS` | 400 Bad Request | Passphrase is shorter than 8 Unicode code points. Encoder-only error. | Step 1 of §18 |
| `KLICKD_E_SCHEMA` | 422 Unprocessable Entity | `payload_schema_version` or `domain_schema_version` major version is unrecognized or incompatible. | Step 11 of §19 |

Implementations SHOULD surface the error code in error responses and logs. Implementations MUST NOT surface decryption oracle information — specifically, `KLICKD_E_AUTH` MUST be returned without indicating whether the failure was due to wrong passphrase or ciphertext tampering.

---

## 22. Size Limits

The following size limits are normative. Violations MUST result in `KLICKD_E_FORMAT`.

| Object | Limit | Measurement |
|---|---|---|
| Envelope file | 1,048,576 bytes (1 MiB) | UTF-8 byte length of the serialized envelope JSON |
| Payload plaintext | 4,194,304 bytes (4 MiB) | UTF-8 byte length of the serialized payload JSON |
| Memory array | 1000 entries | Count of elements in the `memory` array |
| Memory entry | 10,240 bytes (10 KiB) | UTF-8 byte length of the serialized entry JSON object |
| Memory array total | 5,242,880 bytes (5 MiB) | UTF-8 byte length of the serialized `memory` JSON array |
| `identity.name` | 256 bytes | Unicode code point count |
| `context.current_state` | 2,048 characters | Unicode code point count |
| `context.summary` | 4,096 characters | Unicode code point count |
| Memory `content` per entry | 10,240 bytes | UTF-8 byte length |
| Memory `tags` per entry | 32 tags, each ≤ 64 bytes | Tag count and UTF-8 byte length per tag |
| `knowledge.mastered` | 500 entries | Array element count |
| `knowledge.gaps` | 500 entries | Array element count |
| `knowledge.next_steps` | 100 entries | Array element count |
| `agent_instructions` | 32,768 bytes (32 KiB) | UTF-8 byte length of the string value |

The `agent_instructions` limit is a context-window DoS mitigation. Encoders MUST reject values exceeding 32 KiB with `KLICKD_E_FORMAT`. Decoders MUST validate this limit after GCM authentication succeeds and MUST return `KLICKD_E_FORMAT` if exceeded.

---

## 23. Versioning Policy

### 23.0 Version Numbering Scheme

The `.klickd` project uses three distinct version namespaces that MUST NOT be conflated:

| Namespace | Location | Meaning |
|---|---|---|
| Wire format version | `klickd_version` field in envelope | The binary/JSON format version. Controls parsing, AAD field set, and KDF algorithm selection. Currently `"3.0"`. |
| Release version | `version` in root `package.json` and `@klickd/core/package.json` | The release version of the reference implementation and npm package. May advance faster than the wire format version. Currently `3.1.2`. |
| Manifest revision | `version` in `SKILL.md` frontmatter | The revision of the skill manifest, tracking agent-platform compatibility. May differ from both of the above. |

Auditors and installers MUST NOT treat these as equivalent. A `package.json` version of `3.1.2` does not imply wire format `3.1` — the wire format is always authoritative via the `klickd_version` envelope field.

### 23.1 Current Version

**Version 3.0** is the current wire format version. New implementations MUST produce v3.0 envelopes (i.e., `klickd_version: "3.0"`).

The current reference implementation release is **v3.1.2** (see `package.json`).

### 23.2 Legacy Versions

| Version | Status | Notes |
|---|---|---|
| 1.0 | Legacy | Single-field salt/iv, PBKDF2 only. No AAD structure. |
| 2.x | Deprecated | Flat salt/iv fields, Python `json.dumps` AAD (non-deterministic across implementations). |
| 3.0 | **Current** | Structured `kdf`/`cipher` blocks, JCS AAD, Argon2id default. |

Implementations MAY support v1.0 and v2.x for reading purposes only. Implementations MUST NOT produce v1.0 or v2.x files.

### 23.3 Within v3.x

A **minor version increment** within v3.x (e.g., 3.0 → 3.1) indicates backward-compatible additions:
- New OPTIONAL envelope or payload fields.
- New OPTIONAL algorithm options for `kdf.name` (implementations that encounter an unknown `kdf.name` MUST return `KLICKD_E_KDF`; this is handled via the existing error path).

A decoder that conforms to 3.0 MUST be able to read 3.1 files, ignoring unrecognized OPTIONAL fields.

### 23.4 Breaking Changes

A major version increment (e.g., 3.x → 4.0) is required for any of the following:
- Changes to the AAD construction algorithm.
- Removal of required fields.
- Changes to the ciphertext encoding format.
- Changes to the size limit semantics.

### 23.5 Version Detection

Decoders MUST extract the integer portion before the first `.` in `klickd_version` and use it as the major version. If the major version is not supported, return `KLICKD_E_VERSION`.

---

## 24. Threat Model

### 24.1 What This Format Protects Against

1. **Unauthorized access to payload contents.** AES-256-GCM provides confidentiality for all payload data. An attacker without the passphrase cannot recover the plaintext.

2. **Ciphertext tampering.** The GCM authentication tag covers the ciphertext bytes and the AAD. Any modification to the ciphertext or AAD will cause authentication to fail (`KLICKD_E_AUTH`).

3. **Metadata tampering.** Because the AAD includes all non-secret envelope fields (`klickd_version`, `encrypted`, `domain`, `created_at`, `kdf`, `cipher`), any modification to these fields will cause GCM authentication to fail.

4. **IV reuse within a single file.** A fresh IV is generated per encryption operation.

5. **Weak passphrase at encoding time.** Encoders MUST reject passphrases shorter than 8 code points (`KLICKD_E_WEAK_PASS`).

6. **KDF parameter downgrade.** KDF parameters are included in the AAD and authenticated. An attacker cannot reduce the iteration count or memory cost without the decryption failing.

### 24.2 What This Format Does NOT Protect Against

1. **Passphrase brute force.** While Argon2id is intentionally expensive, a weak passphrase remains vulnerable to offline dictionary attacks. Implementers SHOULD encourage strong passphrases.

2. **Compromise of the runtime environment.** This format does not protect against an attacker with access to the process memory during decryption.

3. **Side-channel attacks.** No protection against timing, power, or cache-based side-channel attacks is specified. Implementations SHOULD use constant-time comparison for GCM tag verification.

4. **Metadata confidentiality.** `klickd_version`, `encrypted`, `domain`, `created_at`, and the KDF/cipher parameters are stored in plaintext and are visible to anyone who can read the file.

5. **File integrity without decryption.** The envelope format does not include a file checksum that can be verified without a passphrase.

6. **Multi-user or multi-party access.** There is no public-key or key-wrapping mechanism. Access requires knowledge of the shared passphrase.

7. **Forward secrecy.** Disclosure of the passphrase compromises all past and future files encrypted with that passphrase.

8. **Rollback / replay attacks.** A `.klickd` file does not contain a monotonic counter or a server-issued nonce. An attacker who possesses an older copy of a user's `.klickd` file can replay it to a compatible agent — the agent will decrypt successfully and load stale context. The `created_at` timestamp in the envelope is authenticated (it is part of the AAD) but is set by the encoder and is not externally verified. Mitigations: (a) applications SHOULD display `created_at` to the user before trusting context; (b) agents SHOULD maintain a local high-watermark of the most recently loaded `created_at` per identity and WARN if a file's `created_at` is earlier than the watermark; (c) for high-security deployments, pair `.klickd` files with an out-of-band version token (e.g., a user-visible version number incremented on each save).

### 24.3 Mitigations Recommended for High-Security Deployments

- Use Argon2id with `m ≥ 131072` (128 MiB), `t ≥ 4`.
- Use passphrases of at least 20 characters.
- Store `.klickd` files in an access-controlled location independent of passphrase storage.
- Implement rate-limiting on decryption attempts.
- Zero the passphrase from memory immediately after key derivation.

---

## 25. Test Vectors

Test vectors are provided in the repository at:

```
tests/vectors.json
```

Each test vector is an object with the following fields:

| Field | Description |
|---|---|
| `description` | Human-readable description of the test case |
| `passphrase` | The passphrase used for encryption (string) |
| `envelope` | The complete envelope JSON object |
| `expected_aad_hex` | Hex-encoded bytes of the JCS-canonical AAD string |
| `expected_payload_sha256` | SHA-256 hash of the JCS-canonical payload |
| `expected_plaintext` | The expected decrypted payload JSON object |

### 25.1 expected_payload_sha256 Computation

The `expected_payload_sha256` field is computed as follows:

1. Take the expected plaintext payload as a JSON object.
2. Apply JCS (RFC 8785) to produce the canonical UTF-8 byte string.
3. Compute SHA-256 of the canonical byte string.
4. Encode the result as lowercase hexadecimal.

This allows test suites to verify the correctness of decryption without embedding the full plaintext in the test vector, and to verify JCS canonicalization independently.

### 25.2 AAD Test Vector

Implementations MUST verify their AAD construction against at least one test vector before production use. The `expected_aad_hex` field provides the ground truth for the AAD byte string for each test case.

---

## 26. MIME Type Registration

The MIME type `application/vnd.klickd+json` is pending IANA registration under the `vnd` (vendor) subtype tree per [RFC 6838]. Until registration is complete, implementations SHOULD use this type string and MAY fall back to `application/json` for systems that do not recognize `vnd.klickd+json`.

**Intended usage:** LIMITED USE

**Restrictions on usage:** None

**Author:** klickd.app project

**Change controller:** klickd.app project

---

## 27. Conformance

### 27.1 Encoder MUST

1. Use Argon2id (§14) or PBKDF2-SHA256 (§15) as specified; declare the chosen algorithm in `kdf.name`.
2. Use a CSPRNG to generate `kdf.salt` (minimum 16 bytes) and `cipher.iv` (exactly 12 bytes).
3. NEVER reuse a (key, IV) pair.
4. Set `created_at` to an RFC 3339 UTC timestamp using only the `Z` suffix (no offset notation).
5. Include the `kdf` object (with `name`, `params`, and `salt`) and the `cipher` object (with `name` and `iv`) in the AAD object and construct the AAD via JCS as specified in §17.
6. Reject any passphrase shorter than 8 Unicode code points and return `KLICKD_E_WEAK_PASS`.
7. Use RFC 4648 §4 standard base64 with padding for all base64-encoded fields (`kdf.salt`, `cipher.iv`, `ciphertext`).
8. Encode the inner payload JSON as UTF-8 without a BOM.
9. Enforce the payload size limit (4 MiB) and memory array limits (§11.1) before encrypting.
10. Enforce the envelope size limit (1 MiB) after serialization.

### 27.2 Decoder MUST

1. Reject any `klickd_version` with an unsupported major version and return `KLICKD_E_VERSION`.
2. Reject any decoded `ciphertext` shorter than 16 bytes and return `KLICKD_E_FORMAT`.
3. Reject any malformed base64 in `kdf.salt`, `cipher.iv`, or `ciphertext` and return `KLICKD_E_FORMAT`.
4. Reject any envelope missing required fields or containing prohibited additional properties and return `KLICKD_E_FORMAT`.
5. Reconstruct the AAD using JCS over exactly the 6 fields: `{klickd_version, encrypted, domain, created_at, kdf, cipher}`.
6. Authenticate the GCM tag BEFORE parsing or returning any plaintext; on failure, return `KLICKD_E_AUTH` without any partial plaintext.
7. Treat `user_preferences` as ADVISORY ONLY; MUST NOT use `user_preferences` as a security or access control mechanism.
8. Return `KLICKD_E_FORMAT` if the file begins with a UTF-8 BOM.
9. Reject any `kdf.params.m` below 65536 (for Argon2id) or `kdf.params.iterations` below 600000 (for PBKDF2-SHA256) and return `KLICKD_E_KDF`.
10. Reject an envelope with byte length exceeding 1,048,576 bytes and return `KLICKD_E_FORMAT`.

### 27.3 Decoder SHOULD

1. Warn when the passphrase is shorter than 12 Unicode code points.
2. Zero the derived key bytes from memory immediately after use.
3. Implement rate-limiting on decryption attempts to impede brute-force attacks.
4. Use constant-time comparison when verifying the GCM authentication tag.
5. Sort `memory` entries by `ts` before returning them to the caller.

---

## 28. References

### Normative References

| Reference | Title | URL |
|---|---|---|
| [RFC 2119] | Key words for use in RFCs to Indicate Requirement Levels | https://www.rfc-editor.org/rfc/rfc2119 |
| [RFC 3339] | Date and Time on the Internet: Timestamps | https://www.rfc-editor.org/rfc/rfc3339 |
| [RFC 4122] | A Universally Unique IDentifier (UUID) URN Namespace | https://www.rfc-editor.org/rfc/rfc4122 |
| [RFC 4648] | The Base16, Base32, and Base64 Data Encodings | https://www.rfc-editor.org/rfc/rfc4648 |
| [RFC 8174] | Ambiguity of Uppercase vs Lowercase in RFC 2119 Key Words | https://www.rfc-editor.org/rfc/rfc8174 |
| [RFC 8785] | JSON Canonicalization Scheme (JCS) | https://www.rfc-editor.org/rfc/rfc8785 |
| [RFC 9106] | Argon2 Memory-Hard Function for Password Hashing and Proof-of-Work Applications | https://www.rfc-editor.org/rfc/rfc9106 |
| [NIST SP 800-38D] | Recommendation for Block Cipher Modes of Operation: Galois/Counter Mode (GCM) and GMAC | https://csrc.nist.gov/publications/detail/sp/800-38d/final |
| [JSON Schema 2020-12] | JSON Schema: A Media Type for Describing JSON Documents (Draft 2020-12) | https://json-schema.org/draft/2020-12/json-schema-core.html |

### Informative References

| Reference | Title | URL |
|---|---|---|
| [RFC 6838] | Media Type Specifications and Registration Procedures | https://www.rfc-editor.org/rfc/rfc6838 |
| [RFC 8018] | PKCS #5: Password-Based Cryptography Specification Version 2.1 | https://www.rfc-editor.org/rfc/rfc8018 |
| [BCP 47] | Tags for Identifying Languages | https://www.rfc-editor.org/rfc/rfc5646 |

---

## 29. License

This specification is released under the **Creative Commons Zero v1.0 Universal (CC0 1.0)** public domain dedication.

To the extent possible under law, the klickd.app project has waived all copyright and related or neighboring rights to this specification. This work is published from the klickd.app project.

Full license text: https://creativecommons.org/publicdomain/zero/1.0/

**DOI:** 10.5281/zenodo.20262530

---

## 30. Changelog

### v3.0 (Current)

**Breaking changes from v2.x:**

- **AAD construction:** Replaced Python `json.dumps` serialization with RFC 8785 JCS canonicalization. AAD is now deterministic across all conformant implementations regardless of programming language.
- **Envelope structure:** Replaced flat `salt` and `iv` top-level fields with structured `kdf` and `cipher` objects. The `kdf` object contains `name`, `params`, and `salt`; the `cipher` object contains `name` and `iv`.
- **Default KDF:** Argon2id (m=65536, t=3, p=1) replaces PBKDF2-SHA256 as the default key derivation function. PBKDF2-SHA256 with ≥600,000 iterations is retained as a legacy option (MAY).
- **AAD fields:** AAD now covers exactly 6 fields: `klickd_version`, `encrypted`, `domain`, `created_at`, `kdf`, `cipher`. The `ciphertext` field is excluded from AAD.
- **Inner payload versioning:** `payload_schema_version` (required, `"3.0"`) and `domain_schema_version` (required, pattern `{domain}-{major}.{minor}`) are now required in the inner payload.
- **user_preferences:** New top-level object in the payload. Replaces the role previously served by ad-hoc preference fields. `agent_instructions` is retained as the system-prompt injection string.
- **Memory array:** Normative field schema defined (id, ts, role, content, modality, tags). Limits enforced: max 1000 entries, 10 KiB per entry, 5 MiB total.

**New features:**

- Algorithm agility: `kdf.name` and `cipher.name` allow future algorithm additions without a major version bump.
- Formal error code taxonomy: `KLICKD_E_AUTH`, `KLICKD_E_VERSION`, `KLICKD_E_FORMAT`, `KLICKD_E_KDF`, `KLICKD_E_WEAK_PASS`, `KLICKD_E_SCHEMA`.
- Normative JSON Schema 2020-12 for both envelope and payload (§20).
- Explicit size limits for envelope (1 MiB) and payload (4 MiB).
- `domain_schema_version` evolution rules.
- Threat model section (§24).
- Test vector format with `expected_payload_sha256` via JCS.

### v2.x (Deprecated)

- Flat `salt` and `iv` fields at envelope top level.
- AAD constructed via Python `json.dumps` (non-deterministic across implementations).
- PBKDF2-SHA256 only.

### v1.0 (Legacy)

- Initial format.
- No structured AAD.
- PBKDF2-SHA256 only.
- No domain_schema_version.

---

*End of SPEC.md v3.0*
