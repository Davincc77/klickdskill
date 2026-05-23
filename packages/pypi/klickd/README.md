# klickd

Official Python library for reading and writing `.klickd` portable AI context files.

**One soul. Any model. Any body.**

Official page for the open `.klickd` format → **[klickd.app/klickdskill](https://klickd.app/klickdskill)**

[![PyPI version](https://img.shields.io/pypi/v/klickd)](https://pypi.org/project/klickd/)
[![Python](https://img.shields.io/pypi/pyversions/klickd)](https://pypi.org/project/klickd/)
[![License: CC0-1.0](https://img.shields.io/badge/License-CC0_1.0-lightgrey.svg)](https://creativecommons.org/publicdomain/zero/1.0/)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20320480.svg)](https://doi.org/10.5281/zenodo.20320480)

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

## `.klickd` v4 preview fields (additive, non-GA)

This library currently targets the **v3** envelope and is **stable at v3.5.1**.
The v4 preview track (`v4.0.0-preview.1`, NOT GA) introduces additive payload
fields such as `profile_kind`, `media_profile`, `verification_gates`,
`claim_sources`, `verification_artifacts`, `migration`, and `context_cost`.

These fields are **preserved verbatim** on round-trip — `load_klickd` returns
the raw decrypted JSON object and `save_klickd` re-encrypts it without
filtering unknown keys. Strict v4 validation, migrations, and business-logic
helpers are intentionally **not** implemented yet.

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
- DOI: [10.5281/zenodo.20320480](https://doi.org/10.5281/zenodo.20320480) (v3.5) · concept DOI (all versions): [10.5281/zenodo.20262530](https://doi.org/10.5281/zenodo.20262530)
- Homepage: [klickd.app](https://klickd.app)

---

## License

[CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/) — Public Domain Dedication.  
Author: Vince C. (Luxlearn, Luxembourg)
