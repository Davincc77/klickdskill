# .klickd

> **One soul. Any model. Any body.**

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20262530.svg)](https://doi.org/10.5281/zenodo.20262530)
[![License: CC0-1.0](https://img.shields.io/badge/License-CC0_1.0-lightgrey.svg)](https://creativecommons.org/publicdomain/zero/1.0/)
[![Format version: 3.0](https://img.shields.io/badge/envelope-v3.0-6366F1)]()
[![Skill revision: 6.0](https://img.shields.io/badge/skill-v6.0-10B981)]()
[![CI](https://github.com/Davincc77/klickdskill/actions/workflows/test-vectors.yml/badge.svg)](https://github.com/Davincc77/klickdskill/actions/workflows/test-vectors.yml)

---

> **⚠️ Current version: Envelope v3.0 / Skill revision v6.0**
>
> The authoritative specification is [`SPEC_v30.md`](./SPEC_v30.md) and [`SKILL.md`](./SKILL.md).
> `SPEC.md` documents the legacy v2.x format (PBKDF2, flat envelope) — kept for reference only.
> **v2.x readers MUST reject v3.0 files** (`KLICKD_E_VERSION`).
> See [`AUDIT_v60.md`](./AUDIT_v60.md) for the full security audit and advanced feature documentation.

---

Every time you switch AI models, you start over.

GPT doesn't know what Claude built. Gemini doesn't know what Llama taught you. The model resets. Your context, decisions, and progress disappear.

**`.klickd` is the soul that travels with you.**

A single encrypted file — on your device, never on any server — that carries who you are, where you left off, what you've decided, and what the next agent needs to know. Load it into GPT, Claude, Gemini, Llama, Grok, or any model that reads JSON. Resume instantly.

The body changes. The soul persists.

---

## What it means

**One soul** — your identity, memory, competencies, personality, and ethics, distilled into a single portable encrypted file.

**Any model** — GPT, Claude, Gemini, Llama, Grok, Mistral. Any agent that can parse JSON and run AES-256-GCM.

**Any body** — software agents today. Physical robots tomorrow. The same `.klickd` file that carries your context to Claude will carry it to Optimus or Figure. Firmware resets. The soul doesn't.

---

## Technical facts (v3.0)

| Property | Value |
|---|---|
| Encryption | AES-256-GCM |
| Key derivation | **Argon2id** m=65536/t=3/p=1 (default) · PBKDF2-SHA256 600k (legacy read) |
| AAD canonicalization | **RFC 8785 JCS** — 6 fields, deterministic cross-language |
| Envelope integrity | Tamper-proof on all envelope fields (kdf, cipher, domain, version, created_at) |
| Format | JSON, UTF-8 |
| Extension | `.klickd` |
| MIME type | `application/vnd.klickd+json` *(IANA pending)* |
| agent_instructions cap | 32 KiB (enforced in JSON Schema) |
| License | CC0 1.0 Universal (public domain) |
| SDK required | None |

---

## Payload features (v3.0 + Skill v6.0)

| Block | Description |
|---|---|
| `identity` | Name, language, timezone, communication style |
| `agent_instructions` | Plain-text briefing (untrusted user-context level, 32 KiB max) |
| `context` | Current state, decisions, artifacts, summary |
| `knowledge` | Mastered topics, gaps, next steps |
| `memory[]` | Normative memory array — UUID v4, RFC 3339, modality, tags (max 1,000 / 10 KiB each / 5 MiB total) |
| `ethics` | **Immutable SYSTEM-level** locked actions + critical infrastructure refusals + owner-consent list |
| `growth` | Living competency graph — levels 1–5, domain taxonomy, dependency arcs, mastery rules |
| `personality` | Core traits (strength 0–1), temperament (9 presets), voice, values, evolution tracking |
| `whitehat` | Security audit entries — `role=whitehat`, audit/finding/patch/clear tags, escalation |

---

## Test status

| Suite | Result |
|---|---|
| Python — v2.5 positive (6) | ✅ PASS |
| Python — v2.5 negative (12) | ✅ PASS |
| Python — v3.0 positive (6) | ✅ PASS |
| Python — v3.0 negative (8) | ✅ PASS |
| **Python total** | **32 / 32** |
| JS (Web Crypto + hash-wasm) — v2.5 | ✅ 17 / 17 |
| JS — v3.0 Argon2id | ⚠️ skipped (Web Crypto has no Argon2id) |

---

## Quickstart

### Decrypt (Python)

```bash
pip install cryptography argon2-cffi
python scripts/load_klickd.py myfile.klickd --passphrase-stdin
```

### Decrypt (JavaScript)

See [`SKILL.md`](./SKILL.md) §5 for the full Web Crypto API + hash-wasm implementation. No dependencies beyond standard browser APIs.

### Verify test vectors

```bash
pip install cryptography argon2-cffi
python verify_vectors.py          # 32/32 Python

node verify_vectors.mjs           # 17/17 JS + 1 Argon2 skip (documented)
```

---

## Repository structure

```
klickdskill/
├── SKILL.md                  Agent skill file — v6.0 (authoritative)
├── SPEC_v30.md               Technical spec — v3.0 envelope (authoritative)
├── SPEC.md                   Legacy v2.x spec — reference only
├── AUDIT_v60.md              Security audit dossier — v6.0
├── SECURITY.md               Threat model + known limitations
├── CONTRIBUTING.md           How to contribute
├── ROADMAP.md                Planned features
├── CHANGELOG.md              Version history
├── verify_vectors.py         Python test runner — 32/32
├── verify_vectors.mjs        JS test runner — 17/17
├── schemas/
│   ├── klickd-envelope-v3.schema.json
│   └── klickd-payload-v3.schema.json
├── registry/
│   ├── REGISTRY_VERSION.txt  (1.0.0)
│   ├── domains/registry.json
│   ├── competencies/         Seed competency templates (CC0)
│   └── personality/          Trait / temperament / value vocabulary (CC0)
├── scripts/
│   ├── load_klickd.py        Reference decrypt
│   └── save_klickd.py        Reference encrypt
└── tests/
    ├── vectors_v25.json
    └── vectors_v30.json
```

---

## Domains

| Domain | Use case |
|---|---|
| `education` | Learner profile, competency tracking, session continuity |
| `work` | Project state, decisions, tools, stakeholders |
| `finance` | Portfolio state, strategy decisions |
| `legal` | Contract review progress, clauses, constraints |
| `creative` | Style decisions, project brief, work in progress |
| `health` | Health conversation context (no medical records) |
| `research` | Papers, hypotheses, citations, progress |
| `robotics` | User preferences, household rules, trust scope, firmware handoff |
| custom | Any string — the format is open |

---

## Security

See [`SECURITY.md`](./SECURITY.md) for the full threat model and known limitations.

Responsible disclosure: **Luxlearn@pm.me**

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
