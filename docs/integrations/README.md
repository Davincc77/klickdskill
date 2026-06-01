# `.klickd` integrations

Each guide here specialises the same core pattern: **parse → validate → strip `_`-prefixed fields → build system prompt → inject → call the model**. The portable file is reusable; compatibility still depends on the reader implementing (or wrapping) that pattern. See [`generic.md`](generic.md) for the canonical pattern every other guide builds on.

> New to `.klickd`? Start with [`docs/getting-started.md`](../getting-started.md) (< 3 min) or the [5-minute developer path](../community/TRY_IT.md).

---

## Comparison

| Guide | Language | Injection point | Compatibility | Best for |
|---|---|---|---|---|
| [openai.md](openai.md) | Python | `system` message | Direct (native API) | GPT-4o / o-series via the OpenAI SDK |
| [anthropic.md](anthropic.md) | Python | top-level `system` param | Direct (native API) | Claude Opus / Sonnet via the Messages API |
| [groq.md](groq.md) | Python | `system` message | Direct (OpenAI-compatible) | Fast Llama / Qwen inference |
| [xai_grok.md](xai_grok.md) | Python | `system` message | Direct (OpenAI-compatible) | Grok via the OpenAI client + xAI `base_url` |
| [openrouter.md](openrouter.md) | Python | `system` message | Direct (OpenAI-compatible) | Multi-provider Soul Handoff across 200+ models |
| [mistral.md](mistral.md) | Python | `system` message | **Bridge-mediated, not native** | Mistral chat via the `mistralai` SDK; dry-run + live |
| [langchain.md](langchain.md) | Python | `system` in a chain | Direct (framework adapter) | Provider-agnostic chains; swap the chat model |
| [llamaindex.md](llamaindex.md) | Python | system prompt + index | Direct (framework adapter) | RAG / query engines that also need user state |
| [copilot.md](copilot.md) | hybrid | user-mediated / loader | **Complementary, not direct** | Pairing SKILL.md behaviour with `.klickd` memory |
| [universal-bridge.md](universal-bridge.md) | design + reference | runtime-injection layer | **Bridge-mediated, not native** | One injection layer fronting any compatible surface |
| [generic.md](generic.md) | any | `system` (recommended) | Pattern (you implement it) | Any provider or agent framework not listed above |
| [starter-skills.md](starter-skills.md) | — | — | — (payload pack) | Ready-made plain starter payloads to load and inject |

**Reading the Compatibility column.** *Direct* means the provider's own API accepts a system prompt and these guides inject `.klickd` content into it — no third party decrypts or auto-loads the file. *Complementary / Bridge-mediated* means there is no native `.klickd` support on that surface; compatibility is provided by a loader or injection layer you run. No third-party AI service decrypts or auto-loads a `.klickd` file today.

> Version labels in some guide titles (e.g. `v3.4`, `v4.0.0`) refer to the payload surface the snippet was last revised against. The wire envelope is unchanged (`klickd_version: "3.0"`); v4 readers preserve unknown fields verbatim, so the snippets remain valid against current files.

---

## The shared pattern

Every guide is a specialisation of these steps (full version in [`generic.md`](generic.md)):

1. **Parse** the file — plain JSON for an unencrypted payload, or the encrypted decoder (`load_klickd` / `loadKlickd` with a passphrase) for an encrypted envelope.
2. **Validate** against the schema if you need strictness (see [`../../SCHEMA_INDEX.md`](../../SCHEMA_INDEX.md)).
3. **Strip** `_`-prefixed fields (e.g. `_benchmark`) before injection — they are debug/benchmark only (SPEC §29).
4. **Build the system prompt** from `user_preferences` (+ optional `context`, gates). If `injection_target` is `user_message` / `both`, prepend the JSON Injection Guard (SPEC §25.3).
5. **Inject** in the `system` role and **call** the model.

`verification_gates` are surfaced to the model as instructions — enforce the actual gate semantics in your host application, not in the LLM.

---

## Contributing a new integration

New provider/framework guides are welcome (see the repo [`CONTRIBUTING.md`](../../CONTRIBUTING.md) for the general process). A good integration guide is short and follows the existing ones:

1. **Name the file** `docs/integrations/<provider>.md` (lowercase; underscores only if the provider name needs them, e.g. `xai_grok.md`).
2. **Header block** — link the provider SDK/docs and the install line(s). State the `.klickd` SDK install (`pip install klickd` / `npm install @klickd/core`) if the snippet uses it.
3. **Minimal example** — one copy-paste block that parses a `.klickd` file, builds a system prompt, and makes a single model call. Keep it under ~30 lines; prefer the `system` role.
4. **Honest compatibility note** — say plainly whether the provider is *direct* (native or OpenAI-compatible API), *framework adapter*, or *complementary / bridge-mediated*. Do **not** imply native `.klickd` support where none exists.
5. **Respect the SPEC rules** — strip `_`-prefixed fields, handle `injection_target`, and do not enforce `verification_gates` inside the LLM.
6. **Add two rows**: one to the table in [the main README](../../README.md#integrations) and one to the comparison table above.

Then open a PR against `main` (do not assert benchmark, GDPR/EU AI Act compliance, universal-support, or industry-standard claims — see the claim boundary in the [main README](../../README.md)).
