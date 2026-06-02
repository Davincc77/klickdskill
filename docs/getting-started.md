# 5 minutes to Hello World

**Load one x.klickd starter skill, turn it into model context, and see the output — no account, no server, no API key.**

The quick path below does not call an LLM: it installs the SDK and parses a bundled starter skill so you get a real result on the first run.

---

## 1. Install (~30s)

Pick **one**.

```bash
pip install klickd            # Python
```
```bash
npm install @klickd/core      # Node / TypeScript
```

No network side-effects on import.

---

## 2. Hello World (~1 min, dry-run)

The bundled starter skills are **plain (unencrypted) payloads** on purpose, so this needs no passphrase. Parse one with plain JSON — *not* `load_klickd` / `loadKlickd`, which decode **encrypted** envelopes only.

**Python**

```python
import json
from klickd import get_starter_skill_bytes

payload = json.loads(get_starter_skill_bytes("coding.klickd"))
print(payload["x_klickd_pack"]["pack"])   # -> x.klickd/coding
print(payload["encrypted"])               # -> False
```

**TypeScript / Node**

```ts
import { getStarterSkillBytes } from "@klickd/core";

const payload = JSON.parse(new TextDecoder().decode(getStarterSkillBytes("coding.klickd")));
console.log(payload.x_klickd_pack.pack);   // -> x.klickd/coding
console.log(payload.encrypted);            // -> false
```

Expected output:

```text
x.klickd/coding
False
```

That's a real x.klickd skill loaded as model context. You're done with the smoke test.

---

## 2b. Load the 42 x.klickd v4.1 skill packs (optional)

Beyond the four starter skills, the repo ships **42 x.klickd v4.1 candidate
skill packs** (8 Lite + 34 Pro). The SDK can list them and load any one with a
SHA-256 check against the published manifest:

**Python**

```python
import klickd

skill = klickd.load_xklickd_skill_pack("llm-agent-engineering")
assert skill["artifact_loaded"] and skill["sha256_matches_manifest"]
print(skill["tier"], skill["pack"])   # -> pro x.klickd/llm_agent_engineering
```

**TypeScript / Node**

```ts
import { loadXKlickdSkillPack } from "@klickd/core";

const skill = loadXKlickdSkillPack("x.klickd/llm_agent_engineering");
if (!skill.artifact_loaded || !skill.sha256_matches_manifest) throw new Error("verify failed");
console.log(skill.tier, skill.pack);  // -> pro x.klickd/llm_agent_engineering
```

A pack is only "used" once `artifact_loaded` **and** `sha256_matches_manifest`
are both true — these are JSON artifacts, not native skills in any assistant.
Full details, the no-install CLI, and the truth boundary:
[`integrations/skill-loader-protocol.md`](integrations/skill-loader-protocol.md).

---

## 2c. Dev-preview: resume an interrupted task, with vs without x.klickd (~5 min)

Want to *see* what carried structure buys you, still with no API key? The
dev-preview runs a deterministic, offline simulation of an agent **resuming a
complex task after an interruption** — once on the bare prompt, once with
x.klickd memory + skill gates — and prints a scorecard.

```bash
git clone https://github.com/Davincc77/klickdskill
cd klickdskill
python -m venv .venv && source .venv/bin/activate
pip install -e .
python examples/dev-preview/hello_skill.py
python examples/dev-preview/run_demo.py
```

`pip install -e .` from the repo root installs the same published `klickd`
package (source under `packages/pypi/klickd/`). The demo calls **no LLM** — it
is a *deterministic local demo, not a model benchmark*. Full writeup, the
generated scorecard, and the truth boundary:
[`examples/dev-preview/README.md`](../examples/dev-preview/README.md).

---

## 3. Plug it into a model (~1 min)

A starter skill is built to drop into a **system prompt**. Pick the provider you already have a key for — each guide is a copy-paste minimal example:

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
- Encrypted envelopes — use `load_klickd(bytes, passphrase=...)` (Python) or `await loadKlickd(buf, { passphrase })` (Node). A dual loader is in [`examples/v4/cli/klickd_cli.py`](../examples/v4/cli/klickd_cli.py). Compressed memory is optional.
- [`SPEC.md`](../SPEC.md) — full normative specification (encryption, fields, Soul Handoff).
- [`SECURITY.md`](../SECURITY.md) — threat model and crypto choices.

> The starter skills are non-normative and ship on the v4.0 envelope; they are **not** a v4.1 GA release. See [`examples/v4/starter-skills/README.md`](../examples/v4/starter-skills/README.md).

> **Claim boundary.** `.klickd` gives you portable, client-side-encrypted user state. It does **not** provide universal native support across AI clients (compatibility depends on the reader), and it does **not** confer automatic GDPR or EU AI Act compliance — that remains the operator's responsibility.
