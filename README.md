# .klickd

> **One soul. Any model. Any body.**

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20262530.svg)](https://doi.org/10.5281/zenodo.20262530)
[![License: CC0-1.0](https://img.shields.io/badge/License-CC0_1.0-lightgrey.svg)](https://creativecommons.org/publicdomain/zero/1.0/)
[![Format version: 2.0](https://img.shields.io/badge/format-v2.0-6366F1)]()

---

Every time you switch AI models, you start over.

GPT doesn't know what Claude built. Gemini doesn't know what Llama taught you. The model resets. Your context, decisions, and progress disappear.

**`.klickd` is the soul that travels with you.**

A single encrypted file — on your device, never on any server — that carries who you are, where you left off, what you've decided, and what the next agent needs to know. Load it into GPT, Claude, Gemini, Llama, Grok, or any model that reads JSON. Resume instantly.

The body changes. The soul persists.

---

## What it means

**One soul** — your identity, preferences, decisions, and project state, distilled into a single portable file.

**Any model** — GPT, Claude, Gemini, Llama, Grok, Mistral. Any agent that can parse JSON and run AES-256-GCM.

**Any body** — software agents today. Physical robots tomorrow. The same `.klickd` file that carries your context to Claude will carry it to Optimus or Figure. Firmware resets. The soul doesn't.

---

## How it works

1. At the end of a session, your AI generates a `.klickd` file and hands it to you
2. The file is encrypted client-side with your passphrase — it never touches a server
3. Next session, on any model: upload the file, enter your passphrase, resume instantly

No account. No cloud. No vendor lock-in. The file is yours.

---

## Technical facts

| Property | Value |
|---|---|
| Encryption | AES-256-GCM |
| Key derivation | PBKDF2-SHA256, 600,000 iterations (OWASP 2023) |
| Envelope integrity | AES-GCM AAD on 4 fields — tamper-proof |
| Format | JSON, UTF-8 |
| Extension | `.klickd` |
| MIME type | `application/vnd.klickd+json` *(IANA pending)* |
| License | CC0 1.0 Universal (public domain) |
| SDK required | None |

---

## Cross-implementation test status

✅ **CLEAN PASS** — verified independently in Python and JavaScript (Web Crypto API)

- All 4 test vectors pass (unencrypted + 2 encrypted + short-passphrase)
- Tamper test: correctly rejected (`InvalidTag`)
- Wrong passphrase: correctly rejected (`InvalidTag`)
- 5-field AAD (added `updated_at`): correctly rejected on all 3 encrypted vectors
- Short-passphrase warning fires at `len < 12`

---

## Quickstart

### Decrypt (Python)

```python
pip install cryptography

python scripts/load_klickd.py myfile.klickd --passphrase-stdin
```

### Decrypt (JavaScript)

See `SKILL.md` §5 for the full Web Crypto API implementation — no dependencies, runs in any modern browser or Node.js environment.

### Verify test vectors

```bash
python scripts/generate_vector.py  # regenerates tests/vectors.json with fresh crypto material
```

---

## File structure

```
.klickd envelope (always in plaintext)
├── klickd_version   "2.0"
├── encrypted        true | false
├── domain           "finance" | "education" | "work" | "legal" | "robotics" | ...
├── created_at       ISO 8601 UTC
├── updated_at       ISO 8601 UTC  (not sealed — changes on every re-encrypt)
├── salt             base64(16 random bytes)
├── iv               base64(12 random bytes)
└── payload          base64(AES-256-GCM(inner_json))

Decrypted payload
├── identity         name, language, timezone, communication_style
├── agent_instructions  plain-text briefing for the incoming agent
├── context          current_state, decisions_locked, artifacts, summary
├── knowledge        mastered, gaps, next_steps
└── [domain]_profile  domain-specific extension (e.g. robot_profile)
```

---

## Domains

| Domain | Use case |
|---|---|
| `education` | Learner profile, competency tracking, session continuity |
| `work` | Project state, decisions, tools, stakeholders |
| `finance` | Portfolio state, strategy decisions, amounts |
| `legal` | Contract review progress, clauses, constraints |
| `creative` | Style decisions, project brief, work in progress |
| `health` | Context for health conversations (no medical data) |
| `research` | Papers, hypotheses, citations, progress |
| `robotics` | User preferences, household rules, trust scope |
| custom | Any string — the format is open |

---

## Repository structure

```
klickdskill/
├── SKILL.md              Agent skill file (how to implement .klickd support)
├── SPEC.md               Full technical specification
├── README.md             This file
├── scripts/
│   ├── load_klickd.py    Reference decrypt implementation
│   └── generate_vector.py  Test vector generator
├── tests/
│   └── vectors.json      4 test vectors for cross-impl verification
└── schema/               JSON Schema files
```

---

## Academic reference

> Vince C. (Klickd / Luxlearn, Luxembourg). *".klickd: An Open Encrypted File Format for Portable AI User Context"*. Zenodo, 2026. DOI: [10.5281/zenodo.20262530](https://doi.org/10.5281/zenodo.20262530)

---

## License

**CC0 1.0 Universal — public domain.**

No restrictions. No attribution required. Copy, fork, implement, commercialise freely.

The goal is adoption, not ownership. If `.klickd` becomes a universal standard, every AI user wins.

> To the extent possible under law, Klickd / Luxlearn has waived all copyright and related rights to the `.klickd` format specification. Published from Luxembourg.

https://creativecommons.org/publicdomain/zero/1.0/

---

*`.klickd` — one soul. any model. any body.*
