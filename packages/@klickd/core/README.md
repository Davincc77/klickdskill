# @klickd/core

Official JavaScript/TypeScript library for reading and writing `.klickd` portable AI context files.

**One soul. Any model. Any agent.** — open-source security and continuity layer for every actor in AI.

Official page for the open `.klickd` format → **[klickd.app/klickdskill](https://klickd.app/klickdskill)**

[![npm version](https://img.shields.io/npm/v/@klickd/core)](https://www.npmjs.com/package/@klickd/core)
[![License: CC0-1.0](https://img.shields.io/badge/License-CC0_1.0-lightgrey.svg)](https://creativecommons.org/publicdomain/zero/1.0/)
[![DOI (v4.0.0)](https://zenodo.org/badge/DOI/10.5281/zenodo.20383133.svg)](https://doi.org/10.5281/zenodo.20383133)

---

## Install

```bash
npm install @klickd/core
```

### Argon2id dependency

The v3 format uses **Argon2id** for key derivation. Install the appropriate package for your environment:

- **Node.js**: `npm install argon2`
- **Browser / bundler**: `npm install argon2-browser`

---

## Quick start

### Load (decrypt) a `.klickd` file

```typescript
import { loadKlickd } from '@klickd/core';
import { readFileSync } from 'node:fs';

const fileBytes = readFileSync('context.klickd');
const payload = await loadKlickd(fileBytes, { passphrase: 'my-passphrase' });

console.log(payload.identity?.name);
console.log(payload.memory);
```

### Save (encrypt) a `.klickd` file

```typescript
import { saveKlickd } from '@klickd/core';
import { writeFileSync } from 'node:fs';
import type { KlickdPayload } from '@klickd/core';

const payload: KlickdPayload = {
  payload_schema_version: '3.0.0',
  domain_schema_version: '1.0.0',
  identity: { name: 'Alice', language: 'en', timezone: 'Europe/Luxembourg' },
  agent_instructions: 'Be concise.',
  memory: [],
};

const envelope = await saveKlickd(payload, {
  passphrase: 'my-passphrase',
  domain: 'education',
});

writeFileSync('context.klickd', envelope, 'utf8');
```

### Legacy v2.x files (PBKDF2)

To read files created with the v2.x PBKDF2-SHA256/600k KDF, pass `legacy: true`:

```typescript
const payload = await loadKlickd(fileBytes, {
  passphrase: 'my-passphrase',
  legacy: true,
});
```

---

## `.klickd` v4 preview fields (additive, non-GA)

This library currently targets the **v3** envelope and is **stable at v3.5.1**.
The v4 preview track (`v4.0.0-preview.1`, NOT GA) introduces additive payload
fields such as `profile_kind`, `media_profile`, `verification_gates`,
`claim_sources`, `verification_artifacts`, `migration`, and `context_cost`.

These fields are **preserved verbatim** on round-trip — `loadKlickd` returns
the raw decrypted JSON object and `saveKlickd` re-encrypts it without
filtering unknown keys. The `KlickdPayload` type carries an open
`[key: string]: unknown` index signature so v4 preview fields type-check as
additive properties. Strict v4 validation, migrations, and business-logic
helpers are intentionally **not** implemented yet.

```typescript
const v4PreviewPayload: KlickdPayload = {
  payload_schema_version: '4.0.0-preview.1',
  domain_schema_version: '1.0.0',
  profile_kind: 'learner',
  verification_gates: { public_post: 'confirm' },
  // ... any additional v4 preview fields are preserved on save/load
};

const recovered = await loadKlickd(
  await saveKlickd(v4PreviewPayload, { passphrase: 'my-passphrase' }),
  { passphrase: 'my-passphrase' },
);
// recovered deep-equals v4PreviewPayload
```

See `SPEC.md §33` and `examples/v4-preview/` for preview-track details.

### Starter `.klickd` skills (v4.0 envelope — non-normative)

Four real, structured, downloadable starter `.klickd` skills ship under [`examples/v4/starter-skills/`](https://github.com/Davincc77/klickdskill/tree/main/examples/v4/starter-skills):

- [`user.klickd`](https://github.com/Davincc77/klickdskill/blob/main/examples/v4/starter-skills/user.klickd) — `x.klickd/user` (transversal base)
- [`student.klickd`](https://github.com/Davincc77/klickdskill/blob/main/examples/v4/starter-skills/student.klickd) — `x.klickd/student` (education)
- [`research.klickd`](https://github.com/Davincc77/klickdskill/blob/main/examples/v4/starter-skills/research.klickd) — `x.klickd/research` (research / evidence discipline)
- [`coding.klickd`](https://github.com/Davincc77/klickdskill/blob/main/examples/v4/starter-skills/coding.klickd) — `x.klickd/coding` (software engineering)

Each skill carries `base_transversal_core`, framework-anchored `competencies[]` (ESCO / DigComp / LifeComp / EQF / CEFR / SFIA), `levels[]`, `mastery[]` (pointer-only), `source_policy`, `evidence_policy`, `verification_gates`, `human_authority`, and a `structured_memory` slice scoped to `memory.x_klickd.<pack>`. They are **non-normative**, **do not claim v4.1 GA**, and trigger **no release**. SHA-256 manifest in [`manifest.json`](https://github.com/Davincc77/klickdskill/blob/main/examples/v4/starter-skills/manifest.json); offline verifier `scripts/verify_starter_skills.py`.

> These starter skills are **not yet included as npm package data**. Updating this live npm page to include them as `package.json#files` will require a future patch release of `@klickd/core`. Until then, fetch them directly from the GitHub source above.

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

| Code                | HTTP | Meaning                                  |
|---------------------|------|------------------------------------------|
| `KLICKD_E_AUTH`     | 401  | Wrong passphrase / GCM tag mismatch      |
| `KLICKD_E_VERSION`  | 400  | Unsupported `klickd_version` major       |
| `KLICKD_E_FORMAT`   | 400  | Malformed JSON envelope / missing fields |
| `KLICKD_E_KDF`      | 400  | Unknown or unavailable KDF               |
| `KLICKD_E_WEAK_PASS`| 422  | Passphrase shorter than 8 characters     |
| `KLICKD_E_SCHEMA`   | 400  | Missing `payload_schema_version`         |

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
