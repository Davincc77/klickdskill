# klickd

Official Python library for reading and writing `.klickd` portable AI context files.

**One soul. Any model. Any agent.** — open-source security and continuity layer for every actor in AI.

Official page for the open `.klickd` format → **[klickd.app/klickdskill](https://klickd.app/klickdskill)**

[![PyPI version](https://img.shields.io/pypi/v/klickd)](https://pypi.org/project/klickd/)
[![Python](https://img.shields.io/pypi/pyversions/klickd)](https://pypi.org/project/klickd/)
[![License: CC0-1.0](https://img.shields.io/badge/License-CC0_1.0-lightgrey.svg)](https://creativecommons.org/publicdomain/zero/1.0/)
[![DOI (v4.0.0)](https://zenodo.org/badge/DOI/10.5281/zenodo.20383133.svg)](https://doi.org/10.5281/zenodo.20383133)

---

## Install

```bash
pip install klickd
```

---

## Quick start

### Load (decrypt) a `.klickd` file

```python
from klickd import load_klickd

with open("context.klickd", "rb") as f:
    payload = load_klickd(f.read(), passphrase="my-passphrase")

print(payload["identity"]["name"])
print(payload["memory"])
```

### Save (encrypt) a `.klickd` file

```python
from klickd import save_klickd

payload = {
    "payload_schema_version": "3.0.0",
    "domain_schema_version": "1.0.0",
    "identity": {"name": "Alice", "language": "en", "timezone": "Europe/Luxembourg"},
    "agent_instructions": "Be concise.",
    "memory": [],
}

klickd_bytes = save_klickd(payload, passphrase="my-passphrase", domain="education")

with open("context.klickd", "wb") as f:
    f.write(klickd_bytes)
```

### Legacy v2.x files (PBKDF2)

```python
payload = load_klickd(file_bytes, passphrase="my-passphrase", legacy=True)
```

---

## `.klickd` v4 — GA strict + preview fields

This library targets the **v3** envelope on the wire (envelope crypto contract
is frozen at v3 per SPEC.md §33.10 #2) and ships the **v4 GA strict candidate
payload schema** for validation. The v4 preview track (`v4.0.0-preview.1`)
remains accepted in parallel.

The v4 additive payload fields — `profile_kind`, `media_profile`,
`verification_gates`, `human_veto_policy`, `claim_sources`,
`verification_artifacts`, `migration`, `context_cost`, `deprecated_fields` —
are **preserved verbatim** on round-trip (SPEC.md §33.7). `load_klickd`
returns the raw decrypted JSON object; `save_klickd` re-encrypts it without
filtering unknown keys.

### Optional v4 schema validation

Install the optional `validate` extra to enable strict / preview schema
validation against the bundled v4 JSON schemas (RFC-001 v1, RFC-002 v1
core, RFC-004 v1):

```bash
pip install klickd[validate]
```

```python
from klickd import validate, validate_iter_errors

payload = {
    "payload_schema_version": "4.0",
    "verification_gates": {
        "version": 1,
        "gates": [
            {"action_class": "public_post", "level": "block"},
        ],
    },
}

validate(payload, strict=True)  # raises KlickdError(KLICKD_E_SCHEMA) on fail

# Non-raising variant that returns every (path, message):
errors = validate_iter_errors(payload, strict=True)
```

`validate(..., strict=False)` selects the permissive v4 preview schema.
`validate(..., target="unified")` selects the unified envelope+payload
schema. The strict schema accepts both `"4.0"` and `"4.0.0-preview.1"`
in `payload_schema_version` so preview files round-trip without rewriting.

```python
v4_preview_payload = {
    "payload_schema_version": "4.0.0-preview.1",
    "domain_schema_version": "1.0.0",
    "profile_kind": "learner",
    "verification_gates": {"public_post": "confirm"},
    # ... any additional v4 preview fields are preserved on save/load
}
recovered = load_klickd(save_klickd(v4_preview_payload, "passphrase"), passphrase="passphrase")
assert recovered == v4_preview_payload
```

See `SPEC.md §33` and `examples/v4-preview/` for the preview-track details.

### Starter `.klickd` skills (v4.0 envelope — non-normative)

Four real, structured, downloadable starter `.klickd` skills ship under [`examples/v4/starter-skills/`](https://github.com/Davincc77/klickdskill/tree/main/examples/v4/starter-skills):

- [`user.klickd`](https://github.com/Davincc77/klickdskill/blob/main/examples/v4/starter-skills/user.klickd) — `x.klickd/user` (transversal base)
- [`student.klickd`](https://github.com/Davincc77/klickdskill/blob/main/examples/v4/starter-skills/student.klickd) — `x.klickd/student` (education)
- [`research.klickd`](https://github.com/Davincc77/klickdskill/blob/main/examples/v4/starter-skills/research.klickd) — `x.klickd/research` (research / evidence discipline)
- [`coding.klickd`](https://github.com/Davincc77/klickdskill/blob/main/examples/v4/starter-skills/coding.klickd) — `x.klickd/coding` (software engineering)

Each skill carries `base_transversal_core`, framework-anchored `competencies[]` (ESCO / DigComp / LifeComp / EQF / CEFR / SFIA), `levels[]`, `mastery[]` (pointer-only), `source_policy`, `evidence_policy`, `verification_gates`, `human_authority`, and a `structured_memory` slice scoped to `memory.x_klickd.<pack>`. They are **non-normative**, **do not claim v4.1 GA**, and trigger **no release**. SHA-256 manifest in [`manifest.json`](https://github.com/Davincc77/klickdskill/blob/main/examples/v4/starter-skills/manifest.json); offline verifier `scripts/verify_starter_skills.py`.

#### Bundled in `klickd` 4.0.1

Starting with **`klickd` 4.0.1** (a packaging-only patch — the stable spec
release remains **v4.0.0**), these four starter `.klickd` skills ship inside
the wheel and sdist as `klickd/starter_skills/*.klickd` and are accessible
via a small helper API. The on-the-wire `.klickd` format, the bundled JSON
schemas, and the spec are unchanged from v4.0.0. This patch does **not** ship
any v4.1 material and does **not** carry any Chimera branding.

```python
from klickd import (
    list_starter_skills,
    get_starter_skill_bytes,
    get_starter_skills_manifest,
    get_starter_skills_dir,
)

list_starter_skills()
# → ['coding.klickd', 'research.klickd', 'student.klickd', 'user.klickd']

raw = get_starter_skill_bytes("user.klickd")
manifest = get_starter_skills_manifest()
path = get_starter_skills_dir()  # importlib.resources Traversable as str
```

---

## Cryptographic specification (v3.0)

| Parameter     | Value                                   |
|---------------|-----------------------------------------|
| KDF (default) | Argon2id — m=65536, t=3, p=1           |
| KDF (legacy)  | PBKDF2-SHA256 / 600 000 iterations      |
| Cipher        | AES-256-GCM                             |
| AAD           | RFC 8785 JCS over 6 canonical fields    |
| Base64        | RFC 4648 §4 standard padded             |
| Salt          | 16 bytes (CSPRNG)                       |
| IV            | 12 bytes (CSPRNG)                       |

---

## Error codes

| Code                  | HTTP | Meaning                                  |
|-----------------------|------|------------------------------------------|
| `KLICKD_E_AUTH`       | 401  | Wrong passphrase / GCM tag mismatch      |
| `KLICKD_E_VERSION`    | 400  | Unsupported `klickd_version` major       |
| `KLICKD_E_FORMAT`     | 400  | Malformed JSON envelope / missing fields |
| `KLICKD_E_KDF`        | 400  | Unknown or unavailable KDF               |
| `KLICKD_E_WEAK_PASS`  | 422  | Passphrase shorter than 8 characters     |
| `KLICKD_E_SCHEMA`     | 400  | Missing `payload_schema_version`         |

```python
from klickd import KlickdError, KlickdErrorCode

try:
    payload = load_klickd(data, passphrase="wrong")
except KlickdError as e:
    print(e.code)         # KlickdErrorCode.AUTH
    print(e.http_status)  # 401
```

---

## Links

- Format page: [klickd.app/klickdskill](https://klickd.app/klickdskill)
- Specification: [SPEC.md](https://github.com/Davincc77/klickdskill/blob/main/SPEC.md)
- Repository: [github.com/Davincc77/klickdskill](https://github.com/Davincc77/klickdskill)
- DOI: [10.5281/zenodo.20383133](https://doi.org/10.5281/zenodo.20383133) (v4.0.0) · concept DOI (all versions): [10.5281/zenodo.20262530](https://doi.org/10.5281/zenodo.20262530)
- Homepage: [klickd.app/klickdskill](https://klickd.app/klickdskill)

---

## License

[CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/) — Public Domain Dedication.  
Author: Vincenzo Cirilli (.klickd / klickd.app, Luxembourg)
