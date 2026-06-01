# Getting started — test `.klickd` in < 3 minutes

The shortest honest path from zero to "I loaded a `.klickd` file in code". No account, no server, no API key (this page does not call an LLM — it just installs the SDK and parses a file).

> Want the slightly longer guided version with verification and a model call? See the [5-minute developer path](community/TRY_IT.md).

---

## 1. Install (~30s)

Pick **one**. You do not need both.

**Python**
```bash
pip install klickd
```

**Node.js / TypeScript**
```bash
npm install @klickd/core
```

The packages have no network side-effects on import.

---

## 2. Load a starter skill (~1 min)

The bundled starter skills are **plain (unencrypted) payloads** on purpose, so the smoke test needs no passphrase. For an unencrypted payload the honest path is a plain JSON parse — *not* `load_klickd` / `loadKlickd`, which decode **encrypted** envelopes only and will reject a plain file.

**Python**
```python
import json
from klickd import get_starter_skill_bytes

payload = json.loads(get_starter_skill_bytes("coding.klickd"))
print(payload["x_klickd_pack"]["pack"])   # -> "x.klickd/coding"
print(payload["encrypted"])               # -> False
```

**TypeScript / Node**
```ts
import { getStarterSkillBytes } from "@klickd/core";

const payload = JSON.parse(new TextDecoder().decode(getStarterSkillBytes("coding.klickd")));
console.log(payload.x_klickd_pack.pack);   // -> "x.klickd/coding"
console.log(payload.encrypted);            // -> false
```

> The starter skills are non-normative and ship on the v4.0 envelope; they are **not** a v4.1 GA release. See [`examples/v4/starter-skills/README.md`](../examples/v4/starter-skills/README.md).

For an **encrypted** envelope (your own file with a passphrase), use the full decoder — `load_klickd(bytes, passphrase=...)` in Python, `await loadKlickd(buf, { passphrase })` in Node. A dual loader that handles both forms is in [`examples/v4/cli/klickd_cli.py`](../examples/v4/cli/klickd_cli.py).

---

## 3. Plug it into a model (~1 min)

A starter skill is designed to be dropped into a **system prompt**. Pick the provider you already have a key for — each guide is a copy-paste minimal example:

| Provider | Guide |
|---|---|
| OpenAI | [`integrations/openai.md`](integrations/openai.md) |
| Anthropic | [`integrations/anthropic.md`](integrations/anthropic.md) |
| Groq | [`integrations/groq.md`](integrations/groq.md) |
| OpenRouter | [`integrations/openrouter.md`](integrations/openrouter.md) |
| xAI Grok | [`integrations/xai_grok.md`](integrations/xai_grok.md) |
| LangChain | [`integrations/langchain.md`](integrations/langchain.md) |
| LlamaIndex | [`integrations/llamaindex.md`](integrations/llamaindex.md) |
| Copilot (hybrid) | [`integrations/copilot.md`](integrations/copilot.md) |
| Any other provider | [`integrations/generic.md`](integrations/generic.md) |

Full comparison of what each integration covers: [`integrations/README.md`](integrations/README.md).

---

## Next

- [5-minute developer path](community/TRY_IT.md) — adds hash verification and an end-to-end model call.
- [`SPEC.md`](../SPEC.md) — full normative specification (encryption, fields, Soul Handoff).
- [`SECURITY.md`](../SECURITY.md) — threat model and crypto choices.
- [Add a new integration](integrations/README.md#contributing-a-new-integration) — short contribution guide.

> **Claim boundary.** `.klickd` gives you portable, client-side-encrypted user state. It does **not** provide universal native support across AI clients (compatibility depends on the reader), and it does **not** confer automatic GDPR or EU AI Act compliance — that remains the operator's responsibility.
