# .klickd v2 — Technical Specification

**Version:** 2.0  
**License:** CC0 1.0 Universal (Public Domain)  
**Maintainer:** Klickd / Luxlearn (Luxembourg)  
**Status:** Production — v2.0 released 2026-05-18

---

## Overview

`.klickd` is an open file format for portable AI context. It enables a user's conversational history, preferences, expertise state, and project continuity to travel with them across AI models and sessions — without any server involvement.

**v1** addressed AI memory in the educational domain: learner profiles, competency tracking, session continuity between Klickd/Kai sessions.

**v2** generalises the format to all domains and solves a universal problem: when a user switches AI models (GPT → Claude → Gemini → Llama), the new model starts from zero. With `.klickd v2`, context follows the user, not the model.

---

## Core Philosophy

| Principle | Description |
|---|---|
| **Zero server** | The file is generated and encrypted entirely client-side, using the Web Crypto API (AES-256-GCM). No data transits through any server at any point. |
| **Portable** | Compatible with any AI model or agent: GPT-4, Claude, Gemini, Mistral, Llama, or any custom agent that can read a JSON payload and inject a system prompt. |
| **Privacy-first** | The user owns the file. The encryption key is derived from a user-supplied passphrase using PBKDF2. No third party can decrypt the file without that passphrase. |
| **Open standard** | CC0. No vendor lock-in. No SDK required. Any agent can implement support using a plain JSON parser and a standard AES-256-GCM implementation. |

---

## File Format

A `.klickd` file is a JSON document. When `encrypted: true`, the `payload` field contains a base64-encoded AES-256-GCM ciphertext. All other top-level fields remain in plaintext to allow routing and version detection without decryption.

### Encryption envelope (when `encrypted: true`)

```json
{
  "klickd_version": "2.0",
  "generated_at": "2025-01-15T14:32:00Z",
  "encrypted": true,
  "encryption": "AES-256-GCM",
  "domain": "work",
  "payload": "<base64-encoded AES-256-GCM ciphertext>",
  "iv": "<base64-encoded 12-byte initialisation vector>",
  "salt": "<base64-encoded 16-byte PBKDF2 salt>"
}
```

### Decrypted payload structure

Once decrypted, the payload is a UTF-8 JSON string conforming to the full schema below.

---

## Full Schema

```json
{
  "klickd_version": "2.0",
  "generated_at": "2025-01-15T14:32:00Z",
  "encrypted": true,
  "encryption": "AES-256-GCM",
  "domain": "work",

  "identity": {
    "display_name": "Marie Dupont",
    "language": "fr",
    "communication_style": "tutoiement",
    "timezone": "Europe/Luxembourg"
  },

  "context": {
    "summary": "Marie est cheffe de projet dans une PME luxembourgeoise. Nous travaillons depuis 3 sessions sur la refonte de son processus de reporting mensuel. Elle a une bonne maîtrise d'Excel mais préfère des solutions no-code. Le ton est direct et pragmatique.",
    "current_project": "Refonte reporting mensuel RH",
    "current_state": "Le template Excel v3 est validé. Prochaine étape : automatiser l'import des données depuis l'outil RH (BambooHR) via Zapier.",
    "artifacts": [
      "reporting_template_v3.xlsx",
      "process_flow_diagram.png",
      "zapier_integration_notes.md"
    ],
    "decisions_locked": [
      "Ne pas proposer de solutions nécessitant du code Python ou JavaScript",
      "Ne jamais suggérer de modifier le système RH en place",
      "Toujours présenter les options sous forme de tableau comparatif"
    ],
    "preferences": [
      "Réponses courtes et structurées en bullet points",
      "Exemples concrets tirés du contexte RH/PME",
      "Pas de jargon technique non expliqué",
      "Toujours proposer une option gratuite en premier"
    ]
  },

  "knowledge": {
    "expertise_level": "intermediate",
    "domain_ontology": "custom",
    "mastered": [
      "Excel formulas (VLOOKUP, INDEX/MATCH, pivot tables)",
      "Google Sheets collaboration",
      "Notion workspace setup",
      "Zapier basic automations (2-step zaps)"
    ],
    "gaps": [
      "Multi-step Zapier workflows with filters and formatters",
      "API webhooks concepts",
      "Data visualisation beyond Excel charts"
    ],
    "next_steps": [
      "Build Zapier zap: BambooHR → Google Sheets (monthly headcount export)",
      "Review and validate data mapping table",
      "Train team on new reporting template"
    ]
  },

  "session_history": {
    "total_sessions": 3,
    "last_session": "2025-01-14T16:45:00Z",
    "key_milestones": [
      "2025-01-05 — Session 1 : Audit du processus existant, identification des 4 points de friction",
      "2025-01-10 — Session 2 : Design du nouveau template Excel, 2 iterations",
      "2025-01-14 — Session 3 : Validation finale template v3, choix de l'outil d'automatisation (Zapier vs Make)"
    ]
  },

  "agent_instructions": "Tu reprends une conversation en cours avec Marie Dupont, cheffe de projet RH dans une PME au Luxembourg. Nous travaillons sur la refonte de son reporting mensuel RH. Le template Excel v3 est finalisé et validé. La prochaine étape concrète est de configurer un Zapier pour automatiser l'import mensuel depuis BambooHR vers Google Sheets. Marie préfère les solutions no-code, les réponses courtes en bullet points, et les options gratuites en priorité. Ne jamais proposer de code. Toujours utiliser le tutoiement. Reprends comme si tu avais été là depuis le début."
}
```

---

## Field Reference

### Top-level fields

| Field | Type | Required | Description |
|---|---|---|---|
| `klickd_version` | string | Yes | Version of the .klickd format. Must be `"2.0"` for v2 files. |
| `generated_at` | string (ISO 8601) | Yes | Timestamp of file generation, in UTC. |
| `encrypted` | boolean | Yes | Whether the payload is AES-256-GCM encrypted. If `false`, all fields are inline in plaintext (not recommended for personal data). |
| `encryption` | string | Conditional | Encryption algorithm identifier. Required when `encrypted: true`. Value must be `"AES-256-GCM"`. |
| `domain` | string | Yes | Semantic category of the context. Defined values: `education`, `work`, `legal`, `creative`, `personal`, `health`, `finance`, `research`, `robotics`. Custom strings are permitted. |
| `payload` | string (base64) | Conditional | AES-256-GCM ciphertext of the full inner JSON. Required when `encrypted: true`. |
| `iv` | string (base64) | Conditional | 12-byte initialisation vector used for AES-GCM. Required when `encrypted: true`. |
| `salt` | string (base64) | Conditional | 16-byte PBKDF2 salt used to derive the AES key from the user passphrase. Required when `encrypted: true`. |

---

### `identity` object

Describes who the user is and how they communicate. All fields optional, but the more populated, the better the handoff quality.

| Field | Type | Description |
|---|---|---|
| `display_name` | string | How the agent should address the user. Optional; some users prefer anonymity. |
| `language` | string (BCP 47) | Primary language for interaction. Examples: `fr`, `en`, `de`, `lb`, `pt`. |
| `communication_style` | string | Tone and register. Suggested values: `formal`, `casual`, `tutoiement`, `vouvoiement`, `technical`, `plain-language`. Custom values permitted. |
| `timezone` | string (IANA TZ) | User's local timezone. Used to interpret dates and schedule-related context. Example: `Europe/Luxembourg`. |

---

### `context` object

The operational heart of the file. Describes the current state of work.

| Field | Type | Description |
|---|---|---|
| `summary` | string | A narrative paragraph describing who the user is, what domain they work in, and what has been accomplished in prior sessions. This is written for the incoming agent to read as background. |
| `current_project` | string | Short label for the active project or topic. |
| `current_state` | string | Precise description of where the work currently stands — what is done, what is in progress, what is immediately next. Should be specific enough that a new agent can act on it immediately. |
| `artifacts` | array of strings | List of files, documents, or outputs produced. May include relative paths, URLs, or plain descriptions. |
| `decisions_locked` | array of strings | Hard constraints the agent must never violate. These are prior explicit decisions or user-stated rules that must survive model switches. Format: active imperative sentences ("Ne jamais faire X"). |
| `preferences` | array of strings | Softer stylistic and behavioural preferences. Format, tone, output structure, level of detail. |

---

### `knowledge` object

Captures what the user knows and does not know within the current domain. Particularly relevant for the `education` and `work` domains, but applicable to any context where expertise level shapes the interaction.

| Field | Type | Description |
|---|---|---|
| `expertise_level` | string | Self-reported or inferred expertise. Defined values: `beginner`, `intermediate`, `advanced`, `expert`. |
| `domain_ontology` | string | The competency framework used to structure `mastered` and `gaps`. Defined values: `EQF` (European Qualifications Framework), `ESCO` (European Skills taxonomy), `CEFR` (language proficiency), `custom`. |
| `mastered` | array of strings | Concepts, tools, or skills the user has demonstrated competency in. |
| `gaps` | array of strings | Identified weaknesses, misconceptions, or areas requiring further development. |
| `next_steps` | array of strings | Recommended or agreed-upon next learning or action steps. Ordered by priority when possible. |

---

### `session_history` object

Lightweight audit trail of prior sessions.

| Field | Type | Description |
|---|---|---|
| `total_sessions` | integer | Total number of sessions recorded in this file's history. |
| `last_session` | string (ISO 8601) | Timestamp of the most recent session in UTC. |
| `key_milestones` | array of strings | Important events, decisions, or deliverables, each prefixed with an ISO date. Example: `"2025-01-10 — Template Excel v2 validé"`. |

---

### `agent_instructions` field

**This is the most critical field in the v2 format.**

`agent_instructions` is a plain-text string intended to be injected verbatim at the beginning of the system prompt of the incoming AI agent. It must:

- Be written as a direct briefing to the new agent in second person
- Summarise context, current state, and constraints concisely (recommended: under 300 words)
- Include the user's communication preferences
- End with an explicit instruction to continue as if the agent had been there from the start

The quality of the handoff is entirely determined by the quality of this field. Agents generating a `.klickd` file should treat authoring `agent_instructions` as a deliberate summarisation task, not an automated dump of raw history.

**Example:**

```
Tu reprends une conversation en cours avec Marie. Nous travaillons sur la refonte de son reporting RH dans une PME luxembourgeoise. Le template Excel v3 est finalisé. La prochaine étape est de configurer un Zapier BambooHR → Google Sheets. Marie préfère les solutions no-code. Réponds en français, tutoiement, bullet points courts. Ne propose jamais de code. Reprends comme si tu avais été présent depuis le début.
```

---

## Encryption Implementation

Key derivation and encryption must use the Web Crypto API (browser) or equivalent (Node.js `crypto.subtle`, Python `cryptography` library, etc.).

### Key derivation

```
key = PBKDF2(
  password  = user_passphrase (UTF-8),
  salt      = random 16 bytes,
  iterations = 600000,
  hash      = SHA-256,
  keylen    = 256 bits
)
```

PBKDF2 iteration count: minimum 600,000 (OWASP 2023 recommendation for SHA-256).

### Encryption

```
ciphertext, tag = AES-256-GCM(
  key   = derived_key,
  iv    = random 12 bytes,
  data  = JSON.stringify(inner_payload) encoded as UTF-8
)
```

The 16-byte GCM authentication tag is appended to the ciphertext before base64 encoding:

```
payload = base64(ciphertext || tag)
```

### Decryption

```
raw       = base64_decode(payload)
ciphertext = raw[0 : len-16]
tag        = raw[len-16 : len]
plaintext  = AES-256-GCM-Decrypt(key, iv, ciphertext, tag)
inner_json = JSON.parse(UTF-8 decode(plaintext))
```

---

## Versioning

The `klickd_version` field governs format compatibility.

| Version | Status | Notes |
|---|---|---|
| `1.0` | Stable | Education-only, Klickd/Kai internal format |
| `2.0` | Draft | Multi-domain, open standard, this specification |

Agents receiving a v1 file should reject it with a clear error unless they implement a v1→v2 migration path.

---

## MIME Type and File Extension

| Property | Value |
|---|---|
| File extension | `.klickd` |
| Suggested MIME type | `application/vnd.klickd+json` |
| Encoding | UTF-8 |

---

## License

This specification is released under **CC0 1.0 Universal (Creative Commons Public Domain Dedication)**.  
You may copy, modify, distribute and implement this specification without permission and without any conditions.  
See: https://creativecommons.org/publicdomain/zero/1.0/
