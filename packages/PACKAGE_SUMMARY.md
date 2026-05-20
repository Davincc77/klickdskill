# Klickd Package Scaffolds — Summary

**Format:** .klickd v3.0 | **License:** CC0-1.0 | **Author:** Vince C. (Luxlearn, Luxembourg)
**Repo:** https://github.com/Davincc77/klickdskill | **DOI:** https://doi.org/10.5281/zenodo.20262530

---

## Files Created

### npm @klickd/core (`packages/@klickd/core/`)

| File | Description |
|------|-------------|
| `package.json` | Package manifest — name, version 3.0.0, ESM+CJS dual export, peer deps |
| `tsconfig.json` | TypeScript compiler config (target ES2020, strict mode) |
| `jest.config.cjs` | Jest config with ts-jest and ESM support |
| `LICENSE` | CC0 1.0 Universal full text |
| `README.md` | Install, quick start, crypto spec table, error code table, links |
| `src/index.ts` | Public API barrel export |
| `src/types.ts` | All TypeScript interfaces and types (KlickdPayload, KlickdEnvelope, etc.) |
| `src/errors.ts` | KlickdError class, KlickdErrorCode union type, HTTP_STATUS map |
| `src/encode.ts` | `saveKlickd()` — Argon2id key derivation + AES-256-GCM encryption + JCS AAD |
| `src/decode.ts` | `loadKlickd()` — envelope parsing, version check, KDF dispatch, AES-256-GCM decryption |
| `src/__tests__/roundtrip.test.ts` | 6 Jest tests: save/load roundtrip, wrong passphrase, weak passphrase, malformed JSON, legacy KDF guard, error shape |

### PyPI klickd (`packages/pypi/klickd/`)

| File | Description |
|------|-------------|
| `pyproject.toml` | Hatchling build config, classifiers, deps (cryptography, argon2-cffi, jcs) |
| `README.md` | Install, quick start, crypto spec table, error code table, links |
| `src/klickd/__init__.py` | Public API exports |
| `src/klickd/_types.py` | TypedDict definitions (KlickdPayload, KlickdEnvelope, etc.) |
| `src/klickd/errors.py` | KlickdErrorCode enum, HTTP_STATUS dict, KlickdError exception |
| `src/klickd/encode.py` | `save_klickd()` — Argon2id via argon2-cffi + AES-256-GCM via cryptography + JCS AAD |
| `src/klickd/decode.py` | `load_klickd()` — full decode with version check, KDF dispatch (Argon2id + PBKDF2 legacy), GCM decrypt |
| `tests/__init__.py` | Empty init for test package |
| `tests/test_roundtrip.py` | 8 pytest tests: roundtrip, wrong passphrase, weak passphrase, malformed JSON, missing schema, legacy KDF guard, version mismatch, probabilistic encryption |

---

## Publish Commands

### npm

```bash
# From packages/@klickd/core/

# 1. Install dependencies
npm install

# 2. Install Argon2id peer dep (Node.js)
npm install argon2

# 3. Build (ESM + CJS + type declarations)
npm run build

# 4. Run tests
npm test

# 5. Publish to npm (requires npm login + scoped access)
npm publish --access public
```

### PyPI

```bash
# From packages/pypi/klickd/

# 1. Install build tools
pip install build twine

# 2. Install package in editable mode with deps
pip install -e ".[dev]"
# or: pip install cryptography argon2-cffi jcs

# 3. Run tests
pip install pytest
pytest tests/

# 4. Build wheel + sdist
python -m build

# 5. Upload to PyPI (requires ~/.pypirc or TWINE_USERNAME/TWINE_PASSWORD)
twine upload dist/*

# For TestPyPI first:
twine upload --repository testpypi dist/*
```

---

## Dependencies to Install Before Publishing

### npm @klickd/core

| Package | Purpose | Install |
|---------|---------|---------|
| `argon2` | Argon2id KDF (Node.js) | `npm install argon2` (peer dep, Node) |
| `argon2-browser` | Argon2id KDF (browser) | `npm install argon2-browser` (peer dep, browser) |
| `canonicalize` | RFC 8785 JCS | bundled in `dependencies` |
| `tsup` | Build tool | bundled in `devDependencies` |
| `typescript` | TypeScript compiler | bundled in `devDependencies` |
| `jest` + `ts-jest` | Test runner | bundled in `devDependencies` |

### PyPI klickd

| Package | Version | Purpose |
|---------|---------|---------|
| `cryptography` | >=41.0 | AES-256-GCM cipher |
| `argon2-cffi` | >=23.1 | Argon2id KDF |
| `jcs` | >=0.3 | RFC 8785 JSON Canonicalization |
| `build` | latest | Build wheel/sdist |
| `twine` | latest | Upload to PyPI |
| `pytest` | latest | Run tests |

---

## Cryptographic Specification (v3.0)

| Parameter | Value |
|-----------|-------|
| KDF (default) | Argon2id — m=65536, t=3, p=1 |
| KDF (legacy) | PBKDF2-SHA256 / 600 000 iterations |
| Cipher | AES-256-GCM |
| AAD | RFC 8785 JCS over `{klickd_version, encrypted, domain, created_at, kdf, cipher}` |
| Base64 | RFC 4648 §4 standard padded |
| Salt | 16 bytes (CSPRNG, fresh per file) |
| IV | 12 bytes (CSPRNG, fresh per file) |
| Key length | 32 bytes (256-bit) |
| GCM tag | 16 bytes (appended to ciphertext) |
