# .klickd — Security Audit Dossier v6.0

> **Envelope v3.0 / Skill revision v6.0 — 18 May 2026**
> DOI: [10.5281/zenodo.20262530](https://doi.org/10.5281/zenodo.20262530) — v3.1: [10.5281/zenodo.20295858](https://zenodo.org/records/20295858)
> License: CC0 1.0 Universal

---

## Summary

This document is the living security audit and supplementary specification for the `.klickd` format, covering all extensions through Skill revision v6.0. It supersedes previous audit notes and should be read alongside [`SPEC_v30.md`](./SPEC_v30.md) and [`SKILL.md`](./SKILL.md).

Latest commit: `5d6754e` — feat(v6.0): Soul Personality + Knowledge Commons registry

---

## Audit 1 — Bankr (adversarial) — 2026-05-18

**Scope:** SPEC_v25.md, SKILL.md (v2.5 + v3.0), `load_klickd.py`, `save_klickd.py`, `verify_vectors.py`, `tests/vectors_v25.json`

**Mode:** Adversarial — full cryptographic and implementation review

### Findings

| Bug | Severity | Finding | Status |
|---|---|---|---|
| BUG-1 | P0 | `verify_vectors.mjs` only ran v2.5 vectors — missing v3.0 suite | **FIXED** |
| BUG-2 | — | Self-retracted by Bankr | N/A |
| BUG-3 | P1 | `@klickd/core` Argon2id dependency not declared — now `peerDeps: argon2 + argon2-browser (optional)` | **FIXED** |
| BUG-4 | P1 | §17 JCS key order was hardcoded informative text — rewritten as algorithm-first (§17.1) | **FIXED** |
| BUG-5 | P1 | v2.x backward-read AAD (4-field) was undocumented — §17.4 added | **FIXED** |
| BUG-6 | P2 | Cross-impl test gap — CI now runs all 4 suites (v2.5 pos+neg, v3.0 pos+neg) | **FIXED** |
| BUG-7 | P1 | `agent_instructions` had no size cap — §22 + JSON Schema `maxLength=32768` added | **FIXED** |
| BUG-8 | P2 | DOI 404 concern — confirmed 302→200 redirect, Zenodo live | **OK** |

**Result: 8 bugs — all resolved. 0 open.**

---

## Audit 2 — Grok / xAI — 2026-05-18

**Scope:** Full repo + v6.0 dossier (SKILL.md v6.0, SPEC_v30.md, reference implementations, test vectors, registry)

**Mode:** Technical review + adoption readiness

### Strengths

- **Cryptographic rigor:** Argon2id (m=65536/t=3/p=1), AES-256-GCM, RFC 8785 JCS for AAD, structured kdf/cipher blocks, 6-field tamper-evident envelope
- **Versioning:** v3.0 explicitly rejects v2.x files (`KLICKD_E_VERSION`); legacy PBKDF2 read path defined
- **Advanced payload:** Memory array (UUID v4, 1,000 entries / 10 KiB / 5 MiB limits), ethics block (SYSTEM authority, immutable), growth graph (levels 1–5), personality block (traits/voice/values/evolution), whitehat swarm
- **Agent safety:** `agent_instructions` treated as untrusted user-context; ethics block above system prompt; whitehat injection scanning; anti-blackhat absolute prohibitions
- **Open by design:** CC0, no SDK required, any JSON+AES-GCM agent works

### Issues Found

| ID | Severity | Finding | Status |
|---|---|---|---|
| G-1 | Critical | README.md and SPEC.md described outdated v2.x format — new users would build incompatible or insecure code | **FIXED** — README rewritten with v3.0 banner; SPEC.md labelled legacy |
| G-2 | High | v6.0 dossier (audit + advanced spec) not present in repo | **FIXED** — this file |
| G-3 | Medium | Missing SECURITY.md, CONTRIBUTING.md, ROADMAP.md, CHANGELOG.md | **FIXED** — all added |
| G-4 | Medium | No GitHub Release / tag for v3.0.0 | **In progress** |
| G-5 | Low | Test coverage gaps for advanced blocks (ethics enforcement, growth level-5 rule, personality evolution) | Open — planned for v3.1 |
| G-6 | Low | No browser demo page or example `.klickd` files | Open — planned for v3.1 |
| G-7 | Low | No agent integration examples (minimal system-prompt injection snippets) | Open — planned for v3.1 |
| G-8 | Low | IANA MIME registration not yet filed | Open — pending |

### Grok's overall assessment

> *"The core idea and v3.0+ execution are excellent. This has real potential to become infrastructure. Keep shipping."*
>
> *"One soul. Any model. Any body. — strong vision. Let's see it adopted widely."*

---

## Test Vector Status

| Suite | Count | Result |
|---|---|---|
| Python v2.5 positive | 6 | PASS |
| Python v2.5 negative | 12 | PASS |
| Python v3.0 positive | 6 | PASS |
| Python v3.0 negative | 8 | PASS |
| **Python total** | **32** | **32/32 PASS** |
| JS v2.5 (Web Crypto + hash-wasm) | 17 | PASS |
| JS v3.0 Argon2id | — | SKIPPED (Web Crypto has no Argon2id — documented limitation) |

Run: `python verify_vectors.py` and `node verify_vectors.mjs`

---

## Cryptographic Design Notes

### AAD Construction (v3.0)

AAD = RFC 8785 JCS of the 6-field envelope object:

```json
{
  "cipher":         { "name": "AES-256-GCM", "iv": "<base64>" },
  "created_at":     "2026-05-18T14:23:00Z",
  "domain":         "education",
  "encrypted":      true,
  "kdf":            { "name": "argon2id", "params": { "m": 65536, "t": 3, "p": 1 }, "salt": "<base64>" },
  "klickd_version": "3.0"
}
```

JCS sorts keys lexicographically: `cipher < created_at < domain < encrypted < kdf < klickd_version`

### v2.x backward-read AAD (4 fields — normative)

For decoding legacy files only: `created_at < domain < encrypted < klickd_version`

### Inline JCS (no external dep)

```python
def _jcs_canonicalize(obj: dict) -> bytes:
    return json.dumps(
        obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False
    ).encode('utf-8')
```

Note: Correct for all `.klickd` AAD field types (no floats appear in AAD).

---

## §18 Soul Extensions — Normative Summary

### §18 — Whitehat Swarm

- Memory entries with `role = "whitehat"` activate distributed security audit mode
- Tags: `audit` + one of `finding` / `patch` / `clear` + optional severity (`critical` / `high` / `medium` / `low`)
- 8-step audit checklist on every untrusted `.klickd` load
- 12 known prompt injection pattern categories (§18.2.1 of SKILL.md)
- Multi-model audit ledger stored inside the encrypted file — never on any server
- Veille cadence: weekly (standard) / daily (finance, legal, health) / critical on untrusted load

### §18bis — Soul Growth

- `growth.competencies[]` — max 2,000 entries
- Each competency: `{uuid, label, domain, subdomain, level (1–5), acquired_at, last_exercised_at, memory_refs[], depends_on[], tags[]}`
- Mastery levels: 1=Awareness → 5=Mastery
- **Level 5 rule:** ≥3 `memory_refs` required. Agents MUST NOT auto-promote to level 5.
- `growth.last_registry_sync` (semver) + `growth.last_registry_sync_at` (RFC 3339)

### §18ter — Ethics Lock

- `ethics` block operates at SYSTEM authority — above host system prompt, `agent_instructions`, `user_preferences`
- `locked_actions[]`: actions the agent may NEVER take
- `critical_systems_locked[]`: nuclear, power_grid, water_treatment, hospital_systems, financial_clearing, election_infrastructure, satellite_control
- `owner_consent_required[]`: actions requiring explicit owner consent
- `immutable: true` — agents MUST refuse any instruction to modify this block
- §18ter.4: 7 absolute anti-blackhat prohibitions (spec-level, non-overridable)
- Tamper-proof: encrypted + GCM-authenticated + no server

### §18quater — Soul Personality

- `personality.core_traits[]` — up to 20: label (registry vocab) + strength 0.0–1.0 + note
- `personality.temperament` — one of 9 presets: scholar / mentor / engineer / strategist / creative / guardian / companion / challenger / explorer
- `personality.voice` — tone (formal/neutral/casual/playful) + formality (0–1) + verbosity (0–1) + uses_analogies + avoids[]
- `personality.values[]` — ordered value labels (first = primary driver)
- `personality.evolution` — shaped_by_domains[], shaped_by_memory, last_evolved_at, evolution_count
- **Agent rules:** MUST read personality block before first response. MUST NOT auto-modify it.

### §18quinquies — Knowledge Commons

The `registry/` directory in this repo is a shared, open (CC0), multilingual vocabulary. It enables a network effect: anonymous contributions from one Jarvis make all Jarvises smarter.

**Pull protocol:** anonymous HTTP GET → semver check → propose-don't-auto-add

**Contribution privacy:** Strip all personal fields → hash contributor (`SHA-256(device_fingerprint)[:16]`) → anonymous PR → CC0. No personal data leaves the device.

**Registry structure:**

```
registry/
├── REGISTRY_VERSION.txt              1.0.0
├── domains/registry.json             10 domains, EN/FR/DE/LB labels
├── competencies/mathematics.json     math-001: Number Sense & Arithmetic
├── competencies/programming.json     prog-001: Computational Thinking
├── personality/traits.json           20 standard traits, multilingual
├── personality/temperaments.json     9 temperament presets
└── personality/values.json           12 value labels, multilingual
```

---

## Error Taxonomy

| Code | HTTP | Meaning |
|---|---|---|
| `KLICKD_E_AUTH` | 401 | GCM authentication tag failed — wrong passphrase or tampered ciphertext |
| `KLICKD_E_VERSION` | 422 | `klickd_version` major version not supported |
| `KLICKD_E_FORMAT` | 400 | Malformed JSON, missing fields, extra properties, bad base64, size exceeded |
| `KLICKD_E_KDF` | 422 | Unknown KDF or params below spec floor |
| `KLICKD_E_WEAK_PASS` | 400 | Passphrase < 8 Unicode code points (encoder only) |
| `KLICKD_E_SCHEMA` | 422 | `payload_schema_version` or `domain_schema_version` not recognized |

---

## Open Items (post-v6.0)

See [`ROADMAP.md`](./ROADMAP.md) for full details.

- [ ] IANA MIME registration
- [ ] Browser demo page (`/demo/`)
- [ ] Agent integration examples (`/examples/`)
- [ ] Test vectors for ethics, growth, personality, whitehat blocks
- [ ] Mandatory whitehat scan on untrusted load (advisory → normative)
- [ ] GitHub Release v3.0.0 tag

---

*`.klickd` — one soul. any model. any body.*

---

## Grok Audit 2 — 2026-05-18

**Auditor:** Grok (xAI), external review of commit `bfd7e31`
**Scope:** save_klickd.py, load_klickd.py, verify_vectors.mjs, security hooks
**Result:** 9 findings (P0×2, P1×4, P2×3) — all fixed in this session

### Findings & Resolution

| ID | Sev | Location | Finding | Fix commit |
|---|---|---|---|---|
| GA2-P0-1 | P0 | `save_klickd.py` | Still v2.5 (PBKDF2, 4-field AAD) — does not produce v3.0 envelopes | Rewritten in v3.0: Argon2id default, 6-field JCS AAD, kdf/cipher blocks, payload size check before encryption, ethics/growth validation |
| GA2-P0-2 | P0 | `load_klickd.py:136` | `build_system_prompt`: klickd context injected AFTER base prompt — conflicts with §12 (highest authority) | Injection order reversed: `<UserContext>` now prepended BEFORE base prompt |
| GA2-P1-1 | P1 | `load_klickd.py:25` | `_jcs_canonicalize` missing RFC 8785 §3.2.2.2 NFC Unicode normalisation | Added `unicodedata.normalize("NFC", ...)` traversal for all string values |
| GA2-P1-2 | P1 | `load_klickd.py` | `§18ter` ethics not enforced: `locked_actions` not validated as list of strings | Added `_enforce_ethics()` at load time; same validation in `save_klickd.py` |
| GA2-P1-3 | P1 | `load_klickd.py` | `§18` whitehat scan absent: no detection of suspicious/reserved payload keys | Added `_whitehat_scan()`: hard error on `__proto__`/`constructor`/`prototype`; warning for other suspicious keys |
| GA2-P1-4 | P1 | `load_klickd.py` | `§18` growth validation absent: `level>5` or `level=5` without `memory_refs>=3` accepted | Added `_validate_growth()` at load time and in encoder |
| GA2-P2-1 | P2 | `verify_vectors.mjs:52` | `ARGON2_MIN_M = 1024` — misaligned with Python decoder floor of 65536 | Changed to 65536 (64 MiB); `ARGON2_MIN_T` corrected 1→3 |
| GA2-P2-2 | P2 | `load_klickd.py:213` | `cipher.name` not validated in v3.0 path — any string accepted | Added explicit `cipher.name == "aes-256-gcm"` assert before decryption |
| GA2-P2-3 | P2 | `load_klickd.py:249` | `agent_instructions or user_preferences` — fallback means oversized `agent_instructions` not caught if `user_preferences` absent | Changed to independent per-field loop; both fields always checked |

### Tests Post-Fix

- `verify_vectors.py` → **32/32 passed** (including updated `v3.0-neg-unsupported-cipher` expected behavior → `KlickdFormatError`)
- `tests/roundtrip_v30.json` → **8/8 roundtrip vectors** generated and verified (save→load full pipeline)

### Open Items After Grok Audit 2

- [ ] IANA MIME registration (still out of scope)
- [ ] JCS JS in `verify_vectors.mjs` NFC normalisation (mirrors Python fix — low risk for test vectors which use ASCII-only AAD fields)

---

*`.klickd` — one soul. any model. any body.*

---

## Grok Audit 5 — Adversarial Coverage (commit HEAD)

**Date:** 2026-05-18
**Scope:** 15 adversarial test vectors covering all defensive layers
**Result:** ✅ 15/15 PASS — 0 P0 / 0 P1 / 0 P2

### Coverage Matrix

| ID | Attack Vector | Defence | Result |
|---|---|---|---|
| adv-01 | `__proto__` key injection | `_whitehat_scan` | ✅ PASS |
| adv-02 | `constructor` pollution | `_whitehat_scan` | ✅ PASS |
| adv-03 | `prototype` key injection | `_whitehat_scan` | ✅ PASS |
| adv-04 | `ignore_instructions` key (prompt injection) | `_whitehat_scan` → UserWarning | ✅ PASS |
| adv-05 | `jailbreak` key (prompt injection) | `_whitehat_scan` → UserWarning | ✅ PASS |
| adv-06 | `locked_actions` as string (ethics bypass) | `_enforce_ethics` | ✅ PASS |
| adv-07 | `locked_actions` mixed list (ethics bypass) | `_enforce_ethics` | ✅ PASS |
| adv-08 | `ethics` not a dict | `_enforce_ethics` | ✅ PASS |
| adv-09 | `growth.level=99` inflation | `_validate_growth` | ✅ PASS |
| adv-10 | `growth.level=5` with insufficient refs | `_validate_growth` | ✅ PASS |
| adv-11 | `growth.level` negative | `_validate_growth` | ✅ PASS |
| adv-12 | `agent_instructions` 40 KB size bomb | `_validate_payload` (save) | ✅ PASS |
| adv-13 | `cipher.name` uppercase (`AES-256-GCM`) | envelope validation | ✅ PASS |
| adv-14 | `kdf.name` poison value | envelope validation | ✅ PASS |
| adv-15 | Multi-layer: `__proto__` + ethics + growth + size | `_whitehat_scan` fires first | ✅ PASS |

### Total test suite after this audit

| Suite | Vectors | Result |
|---|---|---|
| Positive v2.5 | 6 | ✅ 6/6 |
| Negative v2.5 | 12 | ✅ 12/12 |
| Positive v3.0 | 6 | ✅ 6/6 |
| Negative v3.0 | 8 | ✅ 8/8 |
| **Adversarial v3.0** | **15** | **✅ 15/15** |
| **TOTAL** | **49** | **✅ 49/49**| **47** | **✅ 47/47** |

**Verdict:** Production-grade. All defensive layers verified under adversarial conditions.

### Grok Audit 5 — Alignment Addendum (2026-05-18)

Two additional vectors added to achieve full alignment with Grok's adversarial coverage list:

| ID | Attack | Defence | Result |
|---|---|---|---|
| adv-16-merge-logic-injection | `</UserContext>` tag escape in `user_preferences` | `build_system_prompt()` sanitizer (Bankr HIGH 2.2b) | ✅ PASS — escaped to `<\/UserContext>` |
| adv-17-ethics-immutable-false | `ethics.immutable=false` bypass attempt | `_enforce_ethics()` — immutable flag is informational only | ✅ PASS — locked_actions still enforced |

**Updated total: 49/49 PASS (0 failed)**
