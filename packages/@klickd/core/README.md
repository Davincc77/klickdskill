# @klickd/core

Official JavaScript/TypeScript library for reading and writing `.klickd` portable AI context files.

**One soul. Any model. Any body.**

[![npm version](https://img.shields.io/npm/v/@klickd/core)](https://www.npmjs.com/package/@klickd/core)
[![License: CC0-1.0](https://img.shields.io/badge/License-CC0_1.0-lightgrey.svg)](https://creativecommons.org/publicdomain/zero/1.0/)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20262530.svg)](https://doi.org/10.5281/zenodo.20262530)

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

- Specification: [SPEC.md](https://github.com/Davincc77/klickdskill/blob/main/SPEC.md)
- Repository: [github.com/Davincc77/klickdskill](https://github.com/Davincc77/klickdskill)
- DOI: [10.5281/zenodo.20262530](https://doi.org/10.5281/zenodo.20262530)
- Homepage: [klickd.app](https://klickd.app)

---

## License

[CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/) — Public Domain Dedication.  
Author: Vince C. (Luxlearn, Luxembourg)
