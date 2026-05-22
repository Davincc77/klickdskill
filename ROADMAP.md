# Roadmap — .klickd Format

This is a living document. Items are aspirational, not committed.

---

## v3.0–v3.4.2 (shipped)

- [x] Argon2id default KDF (m=65536/t=3/p=1)
- [x] AES-256-GCM with RFC 8785 JCS canonicalization for AAD
- [x] Structured `kdf` + `cipher` envelope blocks
- [x] 6-field AAD (tamper-evident on all envelope parameters)
- [x] Normative `memory[]` array (UUID v4, modality, tags, hard limits)
- [x] `ethics` block at SYSTEM authority (immutable, anti-blackhat)
- [x] `growth` competency graph (levels 1–5, dependency arcs)
- [x] `personality` block (core_traits, temperament, voice, values, evolution)
- [x] `whitehat` swarm entries (audit/finding/patch/clear)
- [x] `agent_instructions` 32 KiB hard cap
- [x] JSON Schema 2020-12 (envelope + payload)
- [x] Python + JS cross-impl test vectors (32/32 + 17/17)
- [x] Knowledge Commons registry seed (CC0)
- [x] Soul Handoff transmission rules §28.8 (guaranteed fields, key:value format, 300-char cap)
- [x] `onboarding_trigger` field + §29b multilingual onboarding (v3.4)
- [x] 26 new payload fields — UX/emotional, accessibility, learning analytics, memory (v3.4)
- [x] §29c Privacy Guards — re-identification prohibition (v3.4.2)
- [x] §14bis.1 Verbosity Rule — on_new_agent max 120 chars (v3.4.2)
- [x] Benchmark scorer v3.5 — LLM-as-judge (llama-3.3-70b-versatile)
- [x] Python SDK `klickd 3.0.0` — wheel + sdist
- [x] TypeScript SDK `@klickd/core` — ESM + CJS dist
- [x] Benchmark results: lot 89 Δ+17.8, lot 91 Δ+10.8, lot 94 Δ+10.8

---

## v3.1 (near-term)

- [ ] IANA MIME type registration (`application/vnd.klickd+json`)
- [ ] Mandatory `whitehat` scan on every load from untrusted source (spec-level, not advisory)
- [ ] Passphrase strength: recommend 16+ chars; add zxcvbn-style entropy warning
- [x] Browser demo page (`/demo/`) — pure JS + WASM, encrypt/decrypt in-browser
- [x] Example `.klickd` files in `examples/` (unencrypted test vectors + agent integration)
- [x] Agent integration examples: minimal Python / JS system-prompt injection snippets
- [ ] Argon2id high-security preset: m=131072/t=4 (opt-in, documented)

---

## v3.5 (near-term)

- [ ] JOSS submission — paper.md + peer review
- [x] PyPI publish `klickd 3.0.0` — https://pypi.org/project/klickd/3.0.0/
- [x] npm publish `@klickd/core@3.0.1` — https://www.npmjs.com/package/@klickd/core
- [ ] DOI update to v3.4.2 Zenodo record
- [ ] IANA MIME type registration (`application/vnd.klickd+json`)
- [ ] Benchmark expansion — lots 95–100 (v3.5 scorer)
- [ ] `klickd.app/playground` — client-side JSON editor generating system prompt in real-time from .klickd file (zero server)

---

## v4.0 (medium-term)

- [ ] `media_profile` v1 — portable, encrypted media context (voice / image / document / embedding). Draft RFC: [`docs/rfcs/RFC-001-media-profile-v1.md`](./docs/rfcs/RFC-001-media-profile-v1.md)
- [ ] `verification_gates` + `human_veto` — UX-first guardrails for agent actions (silent / warn / confirm / block / require-owner). v1 targets v4-A; v2 (claim grounding + contract tests, additive, no new levels) targets v4-B. Draft RFC: [`docs/rfcs/RFC-002-verification-gates.md`](./docs/rfcs/RFC-002-verification-gates.md)
- [ ] WASM-native Argon2id everywhere (JS parity with Python — eliminate the CI skip)
- [ ] Counter-based IV scheme for high-volume producers (birthday bound protection)
- [ ] Domain schema registry: formal versioned schemas for `education`, `work`, `finance`, `legal`, `robotics`
- [ ] `memory` search index block (local, encrypted, BM25 or embedding — optional extension)
- [ ] Multi-passphrase / key-wrapping support (shared `.klickd` files for teams)
- [ ] Robotics profile: richer `robot_profile` with actuator trust scope + hardware fingerprint

---

## v5.0 (long-term / research)

- [ ] Forward secrecy: ephemeral device key wrapping (ECDH-based)
- [ ] Zero-knowledge passphrase verification (no oracle exposure)
- [ ] Threshold access: M-of-N passphrase shares (Shamir Secret Sharing)
- [ ] `.klickd` over USB / NFC for firmware handoff (robotics)
- [ ] Formal verification of AAD construction and error taxonomy

---

## Out of scope (by design)

- Server-side storage or sync of any kind
- Cloud key management
- Vendor-specific extensions that break CC0 compatibility
- Any mechanism that allows `ethics.locked_actions` to be overridden at runtime

---

*Contributions welcome — see [CONTRIBUTING.md](./CONTRIBUTING.md).*
