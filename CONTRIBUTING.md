# Contributing to .klickd

The `.klickd` format is CC0 (public domain). All contributions are equally public domain — no CLA required.

---

## What we welcome

- **Bug reports** — incorrect behaviour in reference implementations, test vector failures, spec ambiguities
- **New test vectors** — especially for advanced payload blocks (ethics, growth, personality, whitehat)
- **Registry contributions** — new competency templates or personality vocabulary (see `registry/`)
- **New domain profiles** — `domain_schema_version` examples for new verticals
- **Cross-language implementations** — Rust, Go, Swift, Kotlin, C — conformance tested against `vectors_v30.json`
- **Documentation improvements** — typos, clarity, translations

---

## What we do NOT accept

- Changes that break v3.0 wire format compatibility without a major version bump
- Implementations that store `.klickd` files on any server
- Code that weakens the cryptographic defaults (Argon2id floors, GCM tag requirement)
- Ethics block modifications that would allow the locked actions list to be bypassed

---

## How to contribute

### Spec or documentation

1. Open an issue describing the problem or improvement
2. For minor fixes, submit a PR directly against `main`
3. For normative spec changes, open an issue first — breaking changes require a new major section in `SPEC_v30.md` and a changelog entry

### Registry (competencies / personality)

Registry contributions are the easiest way to contribute. They go in `registry/`:

```
registry/competencies/<domain>.json   — new competency template
registry/personality/traits.json      — add a trait to the vocabulary
registry/personality/values.json      — add a value
```

**Privacy rule:** Registry contributions MUST NOT contain any personal data. `contributor_hash` is either `null` or `SHA-256(device_fingerprint)[:16]` — never a name, email, or user ID.

Format your competency file following `registry/competencies/mathematics.json` as a template. Include multilingual labels (EN + at least one of FR, DE, LB) where possible.

### Code

1. Fork the repo
2. Make your changes
3. Run the full test suite before submitting:

```bash
pip install cryptography argon2-cffi
python verify_vectors.py          # must be 32/32

node verify_vectors.mjs           # must be 17/17 (Argon2 skip is expected)
```

4. Submit a PR with a clear description of what changed and why

---

## Style

- Spec language: RFC 2119 (MUST / SHOULD / MAY)
- Code: no external dependencies beyond `cryptography`, `argon2-cffi` (Python) and Web Crypto / hash-wasm (JS)
- JSON: 2-space indent, UTF-8, no trailing commas

---

## Contact

Questions? Open a GitHub issue or email **Luxlearn@pm.me**.
