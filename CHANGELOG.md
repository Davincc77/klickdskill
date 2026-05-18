# Changelog — .klickd Format

All notable changes to the `.klickd` specification and reference implementations.

Format: `[version] — date — description`
Versions follow: `envelope_version (skill_revision)`.

---

## [3.0 / Skill v6.0] — 2026-05-18

### Added
- `personality` payload block (§18quater): `core_traits[]` (label + strength 0–1 + note), `temperament` (9 presets), `voice` (tone/formality/verbosity/uses_analogies/avoids), `values[]` (ordered, first = primary), `evolution` tracking
- `Knowledge Commons` registry (§18quinquies): `registry/` directory in repo — competency templates, personality presets, domain taxonomy, all CC0
- Registry seed files: `registry/REGISTRY_VERSION.txt` (1.0.0), `registry/domains/registry.json` (10 domains, EN/FR/DE/LB), 2 competency templates, 3 personality vocabulary files
- `growth.last_registry_sync` + `last_registry_sync_at` fields
- `AUDIT_v60.md` — full security audit dossier
- `SECURITY.md`, `CONTRIBUTING.md`, `ROADMAP.md`, `CHANGELOG.md`
- README.md updated with v3.0 banner, full feature table, accurate repo structure

### Security
- Agent MUST read `personality` block before first response; MUST NOT auto-modify it
- Network effect loop documented: privacy-preserving contribution protocol (strip personal fields → hash contributor → anonymous PR)

---

## [3.0 / Skill v5.0] — 2026-05-18

### Added
- `whitehat` swarm (§18): `role=whitehat` memory entries, 8-step audit checklist, 12 known prompt injection pattern categories, swarm coordination via encrypted payload, veille cadence (weekly / daily for finance+legal+health / critical on untrusted load)
- `growth` competency graph (§18bis): `competencies[]` with UUID, label, domain, subdomain, level 1–5, acquired_at, last_exercised_at, memory_refs, depends_on, tags. Max 2,000 entries. Level 5 requires ≥3 memory_refs.
- `ethics` block (§18ter): `locked_actions` at SYSTEM authority, `critical_systems_locked` (nuclear, power_grid, water_treatment, hospital_systems, financial_clearing, election_infrastructure, satellite_control), `owner_consent_required`, `immutable: true`
- §18ter.4: 7 absolute anti-blackhat prohibitions (spec-level, non-overridable)
- Authority hierarchy: `ethics > host system prompt > agent_instructions > user_preferences > in-session`

---

## [3.0 / Skill v4.0] — 2026-05-18 — BREAKING

### Breaking changes
- Envelope format v3.0 replaces v2.x. **v2.x readers MUST reject v3.0 files** (`KLICKD_E_VERSION`).
- `salt` and `iv` moved out of top-level envelope into structured `kdf` and `cipher` blocks
- `updated_at` field removed from envelope (not part of AAD)
- AAD expanded from 4 fields to 6 (adds `kdf` and `cipher` objects)

### Added
- **Argon2id** as default KDF (m=65536/t=3/p=1), replacing PBKDF2-SHA256 as default
- **RFC 8785 JCS** canonicalization for AAD — deterministic, cross-language (replaces Python-specific `json.dumps` with `sort_keys`)
- Structured `kdf` block: `{name, params, salt}`
- Structured `cipher` block: `{name, iv}`
- `payload_schema_version` and `domain_schema_version` in inner payload
- Full error taxonomy: `KLICKD_E_AUTH`, `KLICKD_E_VERSION`, `KLICKD_E_FORMAT`, `KLICKD_E_KDF`, `KLICKD_E_WEAK_PASS`, `KLICKD_E_SCHEMA`
- `agent_instructions` 32 KiB hard cap (§22), enforced in JSON Schema (`maxLength: 32768`)
- JSON Schema 2020-12: `schemas/klickd-envelope-v3.schema.json` + `schemas/klickd-payload-v3.schema.json`
- §17.4: v2.x backward-read AAD documented (4 fields: `created_at`, `domain`, `encrypted`, `klickd_version`)
- Argon2id parameter floor validation (decoder MUST reject m<1024, t<1, p<1 → `KLICKD_E_KDF`)
- `verify_vectors.mjs`: multi-version runner using hash-wasm WASM Argon2id — 17/17 + 1 documented skip
- Python test suite: 32/32 (v2.5 pos/neg + v3.0 pos/neg)
- GitHub Actions CI: `.github/workflows/test-vectors.yml`

### Fixed (Bankr audit — all 8 issues)
- BUG-1 (P0): `verify_vectors.mjs` was v2.5-only → multi-version runner with hash-wasm
- BUG-2: Self-retracted by Bankr
- BUG-3 (P1): `@klickd/core` Argon2id dependency → peerDeps `argon2` + `argon2-browser` (optional)
- BUG-4 (P1): §17 JCS key order hardcoded → algorithm-first rewrite (§17.1), informative note (§17.3)
- BUG-5 (P1): v2.x backward-read AAD undocumented → §17.4 added
- BUG-6 (P2): Cross-impl test gap → CI runs all 4 suites
- BUG-7 (P1): `agent_instructions` no size cap → §22 + JSON Schema `maxLength=32768`
- BUG-8 (P2): DOI 404 concern → confirmed 302→200 redirect, Zenodo live

---

## [2.5] — 2026-05-18

### Added
- Normative `memory[]` array (UUID v4, RFC 3339, modality, tags, hard limits)
- 18 test vectors (v2.5 pos + neg) — 18/18 PASS Python + JS

---

## [2.0] — 2026-05-18

### Added
- Universal release: multi-domain (education, work, finance, legal, creative, health, research, robotics, custom)
- CC0 1.0 license
- Robotics extension: `robot_profile`, USB/NFC handoff
- "Any body" framing
- DOI published: 10.5281/zenodo.20262530

---

## [1.0] — 2026-05-16

- Initial release: education domain only, PBKDF2-SHA256, flat envelope
