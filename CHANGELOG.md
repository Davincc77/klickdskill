# Changelog — .klickd Format

All notable changes to the `.klickd` specification and reference implementations.

Format: `[version] — date — description`
Versions follow: `envelope_version (skill_revision)`.

---

## v3.3 — 2026-05-19

### Security (Phase 1)

#### New fields
- `injection_resistance_level` (top-level enum: `strict | moderate | permissive`, default `permissive`)
  Resolves benchmark vuln: level override via user_message (Lot 10 P7) + JSON injection bypass (Lot 9 P10)
- `companion_identity` (top-level object: `name`, `persona`, `teaching_mode`, `updated_at`)
  Persistent AI companion identity across model switches. Agent reads only, never writes.
- `teaching_mode` within `companion_identity` (enum: `direct | socratic | coaching | adaptive`)
  Socratic mode: agent responds with guiding questions, never direct answers.

#### Security fixes
- §24.10 updated: JSON injection guard added as normative requirement for `user_message` injection
- §25.3: JSON Injection Guard — MUST prepend security instruction to system prompt when injection_target includes user_message

#### Phase 3 — Universal competency layer
- `occupational_competencies` (§26) — ISCO-08 backbone, 7 frameworks, 7 competency types
- New competency types: `physical`, `safety`, `civic`, `sustainability`
- 23 world frameworks referenced (EU, USA, Asia-Pacific, International, Sectoral)

#### Phase 4 — Format refinements
- `numerical_results[].data_type` enum: scalar | vector | formula | equation
- Resumption rule: top-3 numerical_results MUST be cited in first response (normative)
- `knowledge.struggles[].category` enum: conceptual | procedural | linguistic | motivational
- `archived_sessions[].key_numerical_results` array (max 5 per archived session)
- `subject_change_detected` extended to enum: none | detected | confirmed | reverted
- `context.interruption_points` array (§24.11) — multiple checkpoints per session

#### Breaking changes
- None. All new fields are optional and default-backward-compatible.

#### Benchmark evidence
- 100 profiles across 10 domains (v3.2 re-benchmark ×10)
- Global score AVEC .klickd: 8.52/10 vs 3.84/10 SANS (delta +4.68)
- resume_trigger: 97% | numerical_results verbatim: 96% | hallucinations: 0% AVEC
- Soul Handoff (Agent A → Agent B): delta +16 pts
- Full results: benchmarks/v32/RAPPORT_CONSOLIDÉ_V32.md

---

## [3.2] — 2026-05-19

### 12 Benchmark-Driven Improvements

- **numerical_results** (`context`): Array of `{label, value, unit?, formula?}` objects (max 200). Agents MUST cite these values verbatim when resuming sessions.
- **interruption_point** (`context`): Object capturing the precise point of session interruption — `ts`, `last_message_excerpt` (512 chars), `topic`, `subtopic`, `completion_pct` (0–100). Agents MUST resume from this exact point.
- **resume_trigger** (`context`): Exact phrase the agent MUST output at the start of a resumed session to signal continuity.
- **knowledge.struggles**: Array of `{concept, severity, context}` objects (max 100). Severity enum: `minor | moderate | blocking`. Agents MUST NOT re-explain mastered content but SHOULD revisit struggles.
- **vocabulary_used** (`knowledge`): Array of domain-specific terms (max 500, 128 chars each). Agents MUST reuse this exact vocabulary in resumed sessions.
- **context.mode**: Enum `full | lightweight` (default: `full`). Lightweight mode reduces overhead for simple sessions.
- **archived_sessions** (top-level): Array of compressed past-session summaries (max 50). Bounds file growth by archiving old sessions out of active `memory[]`.
- **language_switch_detected** (`context`): Boolean flag — context survives language switches.
- **subject_change_detected** (`context`): Boolean flag — agent SHOULD acknowledge previous session pause and create a new context branch.
- **injection_target** (top-level): Enum `system_prompt | user_message | both` (default: `system_prompt`). `user_message` may improve verbatim recall for some models.
- **§23 Model-Specific Behaviors** (SPEC.md): Documents Gemini implicit assimilation, small-model cautious posture, and gemma2-9b-it deprecation.
- **domain_schema_version** example bump: `education-1.0` → `education-1.2`; new fields documented in SKILL.md.

### Updated Files
- `schemas/klickd-payload-v3.schema.json` — bumped title to v3.2, `$id` URL to v3.2, all new fields added
- `SPEC.md` — v3.2 header, §23 Model-Specific Behaviors added, all new fields documented
- `SKILL.md` — usage examples for `numerical_results`, `interruption_point`, `resume_trigger`, `vocabulary_used`
- `load_klickd.py` — `build_system_prompt` handles all new context fields
- `klickd_v320_spec.pdf` — updated specification PDF

---

## [v6.0] - 2026-05-18

### Security & Hardening (Grok Audits 2–5)

- **Major security release** — All P0 and P1 issues from five adversarial audits resolved.
- Rewrote `save_klickd.py` to full v3.0 (Argon2id default, 6-field JCS AAD, structured `kdf`/`cipher` blocks).
- Fixed `build_system_prompt` injection order — `.klickd` context now correctly placed **before** base system prompt (§12).
- Added proper RFC 8785 JCS with NFC Unicode normalisation in both Python and JavaScript.
- Implemented layered defensive controls:
  - `_whitehat_scan()` — prototype pollution + suspicious keyword detection (hard fail on `__proto__`, `constructor`, `prototype`)
  - `_enforce_ethics()` — `locked_actions` must be `list[str]`
  - `_validate_growth()` — enforces level ≤ 5 and `memory_refs ≥ 3` at level 5
- `cipher.name` and `kdf.name` now strictly validated (case-sensitive).
- `build_system_prompt` now safely merges both `user_preferences` **and** `agent_instructions` when both are present.
- Added `ensure_ascii=False` for UTF-8 consistency in envelope writing.

### Testing

- All previous tests passing (32/32).
- Added **15 new adversarial test vectors** in `tests/adversarial/` covering every defensive layer (prototype pollution, ethics bypass, growth inflation, size bombs, merge logic attacks, multi-layer stress tests, etc.).
- Final Grok Audit 5 (adversarial payload testing) — **0 critical or high-severity bypasses** found.

### Final Status

**v6.0 is now shipping.**  
The format has been thoroughly stress-tested and is considered production-ready.

**Grok Final Verdict**: Secure, spec-compliant, and battle-hardened.

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
