# klickd-proof-protocol

**Privacy-first AI tutor personalization — zero server persistence.**

> *"The AI forgets everything. You don't."*

Published by [Klickd](https://klickd.app) — Luxembourg — May 16, 2026.  
Released to the public domain under **CC0 1.0 Universal**.

---

## What is this?

This repository describes an open protocol for personalizing AI tutors (or any conversational AI assistant) **without storing any user data on a server**.

Instead of saving session history in a database, the AI generates a small encrypted file — a `.klickd` file — directly on the user's device at the end of each session. Next time, the user loads that file and the AI picks up exactly where they left off: what the user has mastered, where they struggle, their preferred learning style.

**The server never sees the profile. It lives in the user's pocket.**

---

## The problem with current AI personalization

Every major AI assistant today (ChatGPT memory, Khanmigo, Duolingo Max, Google Gemini) stores your conversation history and learning profile on their servers to deliver personalization. This creates:

- **Privacy risks** — your learning data, mistakes, and struggles live in a corporate database
- **Regulatory complexity** — especially for minors (GDPR Article 8, COPPA)
- **Vendor lock-in** — your profile is trapped in one platform
- **Infrastructure cost** — scales linearly with user count

---

## The solution: client-side session continuity

```
SESSION 1
  User ↔ AI Tutor (learning)
  → Proof Mode: AI retests without showing answers
  → .klickd file generated locally (encrypted, never sent)
  → User downloads file to their device
  [Server: zero data retained]

SESSION 2
  User uploads their .klickd file
  → Decrypted locally
  → Injected into AI system prompt
  → AI resumes with full personalized context
  [Server: receives only the current message + injected context]
```

---

## Core concepts

### 1. The `.klickd` file

A small JSON file, AES-GCM 256-bit encrypted with a key derived from the user's password (PBKDF2 — never transmitted). Contains the user's learning profile:

```json
{
  "version": "1.0",
  "protocol": "klickd-proof-protocol",
  "created_at": "2026-05-16T17:00:00Z",
  "profile": {
    "subjects": ["mathematics", "physics"],
    "mastered": ["quadratic equations", "Ohm's law"],
    "weak_points": ["logarithms", "RC circuits"],
    "preferred_style": "socratic",
    "language": "fr",
    "session_count": 7,
    "last_topics": ["derivatives", "integrals"],
    "notes": "User prefers short explanations. Struggles with abstract notation."
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

See [`SPEC.md`](./SPEC.md) for the full technical specification.

### 2. Proof Mode

A verification mechanism where the AI:
1. **Suspends access** to previous explanations
2. **Retests the user** with open questions (no MCQ — no guessing)
3. **Updates the profile** based on what the user actually demonstrates
4. **Generates the `.klickd` file** reflecting real knowledge, not memorization

This ensures the profile accurately represents understanding, not exposure.

### 3. Portable by choice

The user decides:
- **Whether to save** the file at all
- **Where to store it** (device, USB, their own cloud)
- **Whether to share it** with another compatible AI or platform
- **Whether to delete it** at any time

No sync. No cloud. No account required to use Proof Mode.

---

## Why open source?

AI personalization should not require surrendering your data to a corporation.

This protocol is released to the public domain so that:
- Any AI developer can implement it
- Any user can benefit from it on any platform
- No single company can patent and restrict it
- The AI-human relationship becomes more private and more personal simultaneously

---

## Implementations

| Platform | Status | Link |
|---|---|---|
| **Klickd** (reference implementation) | ✅ Live | [klickd.app](https://klickd.app) |
| Your platform | Open | Submit a PR |

---

## For AI agent developers

See [`AGENT-SKILL.md`](./AGENT-SKILL.md) — a ready-to-install skill file for AI agents (Perplexity Computer, Claude Projects, GPT custom instructions, etc.) that teaches any AI assistant to implement this protocol.

---

## Files

```
klickd-proof-protocol/
├── README.md          — This file
├── SPEC.md            — Full technical specification
├── AGENT-SKILL.md     — Installable skill for AI agents
├── schema/
│   └── klickd-v1.json — JSON Schema for .klickd files
└── disclosure/
    └── invention-disclosure-2026-05-16.pdf  — Original dated disclosure
```

---

## License

**CC0 1.0 Universal — Public Domain Dedication**

This work has been dedicated to the public domain. You can copy, modify, distribute and use it, even for commercial purposes, without asking permission.

[Full license text](./LICENSE)

---

## Origin

Conceived and first implemented by **Enzo (Vince)**, founder of [Klickd](https://klickd.app), Luxembourg, on May 16, 2026.

The reference implementation is live at [klickd.app](https://klickd.app).

*"fir iech, mat iech"* — for you, with you.
