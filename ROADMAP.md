# Roadmap — .klickd Format

This is a living document. Items are aspirational, not committed.

---

## v3.0 (current — shipped)

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

---

## v3.1 (near-term)

- [ ] IANA MIME type registration (`application/vnd.klickd+json`)
- [ ] Mandatory `whitehat` scan on every load from untrusted source (spec-level, not advisory)
- [ ] Passphrase strength: recommend 16+ chars; add zxcvbn-style entropy warning
- [ ] Browser demo page (`/demo/`) — pure JS + WASM, encrypt/decrypt in-browser
- [ ] Example `.klickd` files in `examples/` (unencrypted test vectors + agent integration)
- [ ] Agent integration examples: minimal Python / JS system-prompt injection snippets
- [ ] Argon2id high-security preset: m=131072/t=4 (opt-in, documented)

---

## v4.0 (medium-term)

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
