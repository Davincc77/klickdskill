# Try `.klickd` in 5 minutes

This is the shortest honest path from "I just cloned the repo" to "I loaded a `.klickd` file in code". It is not a tutorial on the full spec — it is the smoke test.

> **Prereqs:** Python 3.10+ **or** Node.js 18+. No accounts. No API keys (the smoke example does not call an LLM; it just parses a file).

---

## 1. Install (~30s)

Pick one. You do not need both.

**Python**

```bash
pip install klickd==4.0.0
```

**Node.js / TypeScript**

```bash
npm install @klickd/core
```

The packages have no network side-effects on import.

---

## 2. Pick a starter skill (~30s)

Four downloadable starter `.klickd` files ship in the repo:

| File | Skill id | Domain |
|---|---|---|
| [`user.klickd`](../../examples/v4/starter-skills/user.klickd) | `x.klickd/user` | transversal base |
| [`student.klickd`](../../examples/v4/starter-skills/student.klickd) | `x.klickd/student` | education |
| [`research.klickd`](../../examples/v4/starter-skills/research.klickd) | `x.klickd/research` | research / evidence |
| [`coding.klickd`](../../examples/v4/starter-skills/coding.klickd) | `x.klickd/coding` | software engineering |

Pick one. `coding.klickd` is the most natural fit if you are a developer reading this.

You can also use the minimal example: [`examples/minimal.klickd`](../../examples/minimal.klickd).

---

## 3. Load it (~1 min)

**Python**

```python
from klickd import load_klickd

payload = load_klickd("examples/v4/starter-skills/coding.klickd")
print(payload["payload_schema_version"])  # -> "4.0"
print(payload.get("x_klickd_pack", {}).get("pack"))  # -> "x.klickd/coding"
```

`load_klickd` parses bytes and returns a `dict`. It does not call out to the network. It does not decrypt anything that is not encrypted.

**TypeScript / Node**

```ts
import { readFileSync } from "node:fs";
import { parseKlickd } from "@klickd/core";

const buf = readFileSync("examples/v4/starter-skills/coding.klickd");
const payload = parseKlickd(buf);
console.log(payload.payload_schema_version); // -> "4.0"
```

If the import or parse fails, that is interesting — see step 5 ("If something broke") below.

---

## 4. Verify the starter skills (~1 min, optional)

The starter skills ship with a sha256 manifest and an offline verifier:

```bash
python scripts/verify_starter_skills.py
```

Expected output: each file matches the hash declared in `examples/v4/starter-skills/manifest.json`. This confirms you have the files we shipped, not a tampered copy.

---

## 5. Now plug it into a model (~2 min)

The starter skills are designed to be dropped into a system prompt. Pick the provider you already have an API key for:

| Provider | Guide |
|---|---|
| OpenAI (GPT-4o, o1, …) | [`docs/integrations/openai.md`](../integrations/openai.md) |
| Anthropic (Claude Opus, Sonnet, …) | [`docs/integrations/anthropic.md`](../integrations/anthropic.md) |
| Groq (Llama, Qwen, …) | [`docs/integrations/groq.md`](../integrations/groq.md) |
| OpenRouter (multi-provider) | [`docs/integrations/openrouter.md`](../integrations/openrouter.md) |
| xAI Grok | [`docs/integrations/xai_grok.md`](../integrations/xai_grok.md) |
| LangChain | [`docs/integrations/langchain.md`](../integrations/langchain.md) |
| LlamaIndex | [`docs/integrations/llamaindex.md`](../integrations/llamaindex.md) |
| Copilot (hybrid) | [`docs/integrations/copilot.md`](../integrations/copilot.md) |
| Any other provider | [`docs/integrations/generic.md`](../integrations/generic.md) |

The shortest useful end-to-end demo is [`examples/v4/cli/`](../../examples/v4/cli/) (Python, ~100 lines).

---

## If something broke

This is the part we most want to hear about. The 5-minute path should actually take ~5 minutes; if it took longer, that is a bug in the docs or the package, not in you.

- Open [`docs/community/FEEDBACK.md`](./FEEDBACK.md) and answer the short list there.
- Or open an issue using `.github/ISSUE_TEMPLATE/bug_report.yml`.
- Or start a thread in GitHub Discussions (once we open them — see [`DISCUSSION_PROMPTS.md`](./DISCUSSION_PROMPTS.md)).

Please include: OS, Python or Node version, package version, exact error message. Skip stack-trace prose — paste the trace.

---

## What this 5-minute path deliberately does **not** cover

- **Encryption end-to-end.** The starter skills are unencrypted on purpose so the smoke test does not require a passphrase. See [`SPEC.md`](../../SPEC.md) §encryption for AES-256-GCM + Argon2id usage.
- **Cross-model Soul Handoff.** Covered in the integration guides and in [`SPEC.md`](../../SPEC.md).
- **Migration from v3.x.** See [`docs/spec/MIGRATION_V3_TO_V4.md`](../spec/MIGRATION_V3_TO_V4.md).
- **v4.1 Chimera candidate work.** Non-normative, no release — see [`docs/chimera/README_V4_1.md`](../chimera/README_V4_1.md) if you are curious, but it is not part of the 5-minute path.

---

## Where to read next

- [`SPEC.md`](../../SPEC.md) — full normative specification.
- [`SECURITY.md`](../../SECURITY.md) — threat model, crypto choices, what is and is not in scope.
- [`CONTRIBUTING.md`](../../CONTRIBUTING.md) — what we welcome, what we do not.
- [`docs/community/FEEDBACK.md`](./FEEDBACK.md) — short list of questions we would like answered.
