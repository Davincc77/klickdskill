# .klickd — Portable Encrypted AI Context

**v2.0 — Production — 2026-05-18**  
**License:** CC0 1.0 Universal (Public Domain)  
**Author:** Vince C. — Klickd / Luxlearn.app — Luxembourg  
**Contact:** Luxlearn@pm.me

---

## One file. Zero cloud storage. Any AI.

`.klickd` is an open, encrypted file format that stores a user's AI context on their own device — permanently. No server. No account. No vendor lock-in.

When a user switches AI models (GPT → Claude → Gemini → Llama), or when a robot gets a firmware update, **context no longer dies at the boundary**. The `.klickd` file travels with the user, not the model.

---

## The problem it solves

Every AI provider today stores user context in their cloud:
- **Storage cost** that scales linearly with users — PBs/year at scale
- **GDPR liability** — the provider holds the data, owns the risk
- **Context loss** on model switch, firmware update, or device change

`.klickd` moves all three costs to zero.

---

## Properties

| Property | Value |
|---|---|
| Encryption | AES-256-GCM, key from user passphrase (PBKDF2, 600k iterations) |
| Generation | Client-side only — zero server call |
| Portability | Any model or agent that implements the spec |
| Ownership | File lives on user's hardware only |
| License | CC0 — free to implement for any provider or manufacturer |
| GDPR | Art. 20 compliant by architecture |
| MIME type | `application/vnd.klickd+json` |

---

## Domains

| Domain | Use case |
|---|---|
| `education` | Learner profile, competency tracking, session continuity |
| `work` | Project context, decisions, preferences across work tools |
| `legal` | Case context, constraints, prior decisions |
| `creative` | Creative project state, style, constraints |
| `personal` | Personal assistant memory, routines, preferences |
| `health` | Health context (user-controlled, zero server) |
| `finance` | Financial context, goals, constraints |
| `research` | Research context, sources, methodology |
| `robotics` | Robot user profile — survives firmware updates and unit replacements |

---

## Files

| File | Description |
|---|---|
| [SPEC.md](./SPEC.md) | Full technical specification — schema, encryption, field reference |
| [AGENT-SKILL.md](./AGENT-SKILL.md) | Installation guide for any AI agent — Python + JS + robotics |
| [schema/](./schema/) | JSON schema files |
| [curriculum/](./curriculum/) | Education domain curricula (LU, FR, BE, DE, NL, CH, PT) |
| [disclosure/](./disclosure/) | Invention disclosure (2026-05-16) |

---

## Quick start — any AI agent

```python
import json, base64
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

def load_klickd(file_path: str, passphrase: str) -> dict:
    with open(file_path) as f:
        envelope = json.load(f)
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32,
                     salt=base64.b64decode(envelope["salt"]),
                     iterations=600000)
    key = kdf.derive(passphrase.encode())
    raw = base64.b64decode(envelope["payload"])
    iv  = base64.b64decode(envelope["iv"])
    plaintext = AESGCM(key).decrypt(iv, raw, None)
    return json.loads(plaintext)
```

Then inject `payload["agent_instructions"]` at the top of your system prompt.

---

## Commercial model

The format is CC0 — free to implement. Klickd proposes revenue-sharing partnerships with AI providers and robot manufacturers based on documented infrastructure savings. Contact: Luxlearn@pm.me

---

## Invention disclosure

Filed: 2026-05-16  
Inventor: Vince C. — Klickd / Luxlearn.app — Luxembourg  
See [disclosure/](./disclosure/)

---

## Links

- App: [klickd.app](https://klickd.app)
- Web: [luxlearn.app](https://luxlearn.app)
- Contact: Luxlearn@pm.me
