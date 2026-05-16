# .klickd Protocol — Technical Specification v1.0

**Protocol:** `klickd-proof-protocol`  
**Version:** 1.0  
**Date:** 2026-05-16  
**License:** CC0 1.0 Universal (Public Domain)  
**Origin:** [Klickd](https://klickd.app) — Luxembourg

---

## 1. Overview

The `.klickd` format is a portable, encrypted session profile for AI tutors. It enables personalized AI behavior across sessions without any server-side storage of user data.

A `.klickd` file is:
- Generated **client-side** (browser or native app) at the end of a session
- **Encrypted** with a key derived from the user's password — never transmitted
- **Owned exclusively** by the user — the operator never sees its contents
- **Portable** — loadable on any device, any compatible AI implementation

---

## 2. File Structure

### 2.1 Container format

A `.klickd` file is a JSON object with two top-level fields:

```json
{
  "meta": { ... },
  "payload": "<base64url-encoded encrypted blob>"
}
```

### 2.2 Meta (plaintext)

```json
{
  "meta": {
    "protocol": "klickd-proof-protocol",
    "version": "1.0",
    "created_at": "2026-05-16T17:00:00Z",
    "updated_at": "2026-05-16T17:45:00Z",
    "session_count": 7,
    "hint": "optional user-defined label e.g. 'Math S3 2026'"
  }
}
```

`meta` is **never encrypted** — it allows the user to identify the file without decrypting it. It must NOT contain any personal data.

### 2.3 Payload (encrypted)

The payload is the base64url-encoded result of AES-GCM encryption of the following JSON object:

```json
{
  "profile": {
    "subjects": ["mathematics", "physics"],
    "mastered": ["quadratic equations", "Ohm's law"],
    "weak_points": ["logarithms", "RC circuits"],
    "preferred_style": "socratic",
    "language": "fr",
    "last_topics": ["derivatives", "integrals"],
    "notes": "Prefers short explanations. Struggles with abstract notation.",
    "custom": {}
  },
  "proof_results": [
    {
      "topic": "quadratic equations",
      "score": 0.92,
      "date": "2026-05-16T16:45:00Z",
      "method": "open_question"
    }
  ]
}
```

---

## 3. Encryption

### 3.1 Algorithm

| Parameter | Value |
|---|---|
| Algorithm | AES-GCM |
| Key length | 256 bits |
| IV length | 12 bytes (96 bits), random per encryption |
| Tag length | 128 bits |
| KDF | PBKDF2-SHA256 |
| Iterations | 310,000 (OWASP 2023 recommendation) |
| Salt length | 16 bytes, random per file |

### 3.2 Key derivation

```
key = PBKDF2(
  password = user_password,       // never transmitted
  salt     = random_16_bytes,     // stored in encrypted_blob header
  iterations = 310000,
  hash     = SHA-256,
  keylen   = 32                   // 256 bits
)
```

### 3.3 Encrypted blob structure

The raw bytes of the encrypted blob (before base64url encoding):

```
[ salt (16 bytes) ][ iv (12 bytes) ][ ciphertext + GCM tag (variable) ]
```

### 3.4 Web Crypto API reference implementation

```javascript
// Encrypt
async function encryptProfile(profile, password) {
  const salt = crypto.getRandomValues(new Uint8Array(16));
  const iv   = crypto.getRandomValues(new Uint8Array(12));
  const enc  = new TextEncoder();

  const keyMaterial = await crypto.subtle.importKey(
    "raw", enc.encode(password), "PBKDF2", false, ["deriveKey"]
  );
  const key = await crypto.subtle.deriveKey(
    { name: "PBKDF2", salt, iterations: 310000, hash: "SHA-256" },
    keyMaterial,
    { name: "AES-GCM", length: 256 },
    false, ["encrypt"]
  );

  const ciphertext = await crypto.subtle.encrypt(
    { name: "AES-GCM", iv },
    key,
    enc.encode(JSON.stringify(profile))
  );

  // Concatenate salt + iv + ciphertext
  const blob = new Uint8Array(salt.length + iv.length + ciphertext.byteLength);
  blob.set(salt, 0);
  blob.set(iv, salt.length);
  blob.set(new Uint8Array(ciphertext), salt.length + iv.length);

  return btoa(String.fromCharCode(...blob))
    .replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, ''); // base64url
}

// Decrypt
async function decryptProfile(payload, password) {
  const raw  = Uint8Array.from(atob(
    payload.replace(/-/g, '+').replace(/_/g, '/')
  ), c => c.charCodeAt(0));

  const salt       = raw.slice(0, 16);
  const iv         = raw.slice(16, 28);
  const ciphertext = raw.slice(28);
  const enc        = new TextEncoder();

  const keyMaterial = await crypto.subtle.importKey(
    "raw", enc.encode(password), "PBKDF2", false, ["deriveKey"]
  );
  const key = await crypto.subtle.deriveKey(
    { name: "PBKDF2", salt, iterations: 310000, hash: "SHA-256" },
    keyMaterial,
    { name: "AES-GCM", length: 256 },
    false, ["decrypt"]
  );

  const plaintext = await crypto.subtle.decrypt(
    { name: "AES-GCM", iv }, key, ciphertext
  );

  return JSON.parse(new TextDecoder().decode(plaintext));
}
```

---

## 4. AI Context Injection

When the user loads a `.klickd` file, the decrypted profile is injected into the AI system prompt. Reference template:

```
You are a personal AI tutor. The user has loaded their session profile.

LEARNING PROFILE:
- Subjects: {{subjects}}
- Mastered topics: {{mastered}}
- Weak points: {{weak_points}}
- Preferred style: {{preferred_style}}
- Language: {{language}}
- Last session topics: {{last_topics}}
- Notes: {{notes}}

PROOF RESULTS (last verified knowledge):
{{proof_results}}

INSTRUCTIONS:
- Resume from where the user left off
- Focus attention on weak points without mentioning them explicitly
- Match the user's preferred teaching style
- At the end of this session, offer to generate an updated .klickd file
- Never store this profile outside of the current session context
```

---

## 5. Proof Mode

Proof Mode is the verification mechanism that ensures the profile reflects real understanding.

### 5.1 Trigger conditions
- Explicitly requested by the user ("test me")
- Automatically offered at end of session
- After a topic has been explained 3+ times

### 5.2 Rules
- AI asks **open questions only** — no multiple choice
- AI does **not repeat** the explanation before asking
- AI does **not confirm** the answer until the user has fully responded
- Score: 0.0 (no recall) → 1.0 (perfect recall + application)

### 5.3 Profile update logic
```
if score >= 0.8  → move topic from weak_points to mastered
if score < 0.5   → add topic to weak_points, increase weight
if 0.5 ≤ score < 0.8 → keep in weak_points, add note
```

---

## 6. Privacy guarantees

| Guarantee | Mechanism |
|---|---|
| Profile never sent to server | Generated and decrypted client-side only |
| Operator cannot access profile | AES-GCM encryption with user-derived key |
| No tracking across sessions | No session ID, no cookie, no fingerprint |
| User can delete at any time | It's a local file — delete it like any file |
| Portable between platforms | Open format, open spec |

---

## 7. Versioning

The `version` field in `meta` follows semantic versioning. Breaking changes increment the major version. Implementations MUST reject files with an unsupported major version.

Current versions:
- `1.0` — Initial release (this document)

---

## 8. Contributing

This spec is in the public domain (CC0). Open a PR or issue to propose improvements.

Maintained by the community. Originally published by [Klickd](https://klickd.app).
