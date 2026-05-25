# .klickd — One soul. Any model. Any body.

**An open encrypted file format for portable AI identity**

.klickd / klickd.app — Luxembourg — 2026
DOI: [10.5281/zenodo.20262530](https://doi.org/10.5281/zenodo.20262530)

---

## The problem

Every AI model has amnesia.

You spend twenty sessions building context with GPT. You switch to Claude. You start from zero. Every preference, every decision, every project state — gone.

This is not a cloud sync problem. It's an identity problem.

There is no standard way for a user's AI identity to persist across models, sessions, or physical platforms. Every AI system you use starts by knowing nothing about you. You re-explain yourself constantly. The intelligence multiplies. The context doesn't.

---

## The insight

A user's AI context is not a server-side resource. It's a personal file.

Like a passport. Like a USB drive with your work on it. It belongs to the person — not to the platform.

The file travels with the user. The model reads it. The conversation resumes.

---

## The solution

`.klickd` is an open, encrypted, client-side file format that carries a user's AI context across model switches, sessions, and platforms.

**One file. Three properties.**

**One soul** — your identity, preferences, decisions, and project state, distilled into a single portable file. Not a raw conversation log. A curated briefing, written by the outgoing agent for the incoming agent.

**Any model** — GPT, Claude, Gemini, Llama, Grok, Mistral, or any custom agent. No SDK required. Any system that can parse JSON and run AES-256-GCM can implement `.klickd` support.

**Any body** — software agents today. Physical robots tomorrow. The same `.klickd` file that carries your context from GPT to Claude will carry it from your phone to Optimus to Figure. Firmware resets. The soul doesn't.

---

## How it works

```
Session ends on GPT
    → GPT writes agent_instructions + full context to .klickd
    → Encrypts client-side with your passphrase (AES-256-GCM, PBKDF2-SHA256)
    → Delivers file to you — never touches a server

Next session on Claude
    → You upload .klickd, enter passphrase
    → Claude decrypts locally, injects agent_instructions as <UserContext>
    → Conversation resumes — no re-explanation
```

No account. No cloud. No vendor lock-in. The file is yours.

---

## What the file carries

| Field | Purpose |
|---|---|
| `identity` | Name, language, timezone, communication style |
| `agent_instructions` | Plain-text briefing for the incoming agent — the key field |
| `context.current_state` | Exact state of work — what's done, what's next |
| `context.decisions_locked` | Constraints that must survive model switches |
| `context.artifacts` | Files, documents, deliverables produced |
| `knowledge` | What the user knows, what they don't, what's next |
| `[domain]_profile` | Domain-specific extension (finance, robotics, legal, ...) |

---

## Security

- **AES-256-GCM** — authenticated encryption, tamper-proof
- **PBKDF2-SHA256 @ 600,000 iterations** — OWASP 2023 floor
- **4-field AAD** — envelope fields are sealed; flipping `encrypted: false` fails
- **Zero server** — file never leaves the user's device via network
- **No SDK** — any JSON parser + AES-GCM implementation suffices
- **CC0** — public domain; no vendor can lock the standard

---

## The robotics case

Every firmware update on a home robot resets the user relationship. The robot forgets your name, your routines, your preferences, your rules.

`.klickd` on a USB drive solves this permanently.

The robot reads the file on boot. Relationship restored. No manufacturer account required. No cloud. GDPR Art. 20 compliant by architecture — the user holds the data, not the manufacturer.

When Optimus ships to 10 million homes, `.klickd` is how those homes keep their identity across firmware versions.

---

## Test status

**CLEAN PASS** — independently verified in two implementations:

- Python (spec-only implementation, no reference code read)
- JavaScript (Web Crypto API, Bankr AI agent)

4 vectors. 3 security rejection tests. Zero failures.

---

## Academic status

Preprint published on Zenodo under CC0:

> Vince C. (2026). *.klickd: An Open Encrypted File Format for Portable AI User Context.* Zenodo. DOI: 10.5281/zenodo.20262530

Submitted for consideration: IEEE LTSC, 1EdTech CLR WG, xAI Partnerships.

---

## Why open standard

`.klickd` is CC0 — public domain, no restrictions.

This is a deliberate choice, not a default.

A portable identity format only works if every model supports it. Vendor lock-in is the failure mode. Open is the only way this becomes universal infrastructure.

The goal is adoption. If `.klickd` becomes the standard, every AI user on earth wins — including every user of every platform that implements it.

---

## The pitch in one sentence

*A user's AI identity should be as portable as a passport — encrypted, owned by the person, readable by any model, on any device, in any body.*

---

## Contact

Vincenzo Cirilli (.klickd) — klickd.app, Luxembourg
hello@klickd.app
https://github.com/Davincc77/klickdskill
DOI: 10.5281/zenodo.20262530

---

*`.klickd` — one soul. any model. any body.*
