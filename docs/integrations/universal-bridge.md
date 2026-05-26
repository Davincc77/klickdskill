# Universal `.klickd` Bridge

> **Status:** design + reference implementation. The Universal `.klickd`
> Bridge is the runtime-injection layer that turns a portable `.klickd`
> profile into a sanitized context block for any compatible AI surface.
> All compatibility provided through this layer is **bridge-mediated
> compatibility, not native support**. No third-party AI service decrypts
> or auto-loads `.klickd` files today.

## The four layers

`.klickd` is one piece of a larger picture. To avoid category confusion,
think in four distinct layers:

| Layer | What it carries | Examples |
|---|---|---|
| **Skills / behavior** (`SKILL.md`, agent manifests) | What the model is *allowed to do* — capabilities, tools, slash commands, behavior contracts. | GitHub Copilot Skills, Anthropic Skills, custom system prompts. |
| **Memory / identity / state** (`.klickd`) | Who the user is, what the project is, what was decided, where we left off — portable, user-owned, optionally encrypted. | `.klickd` v4 profile. |
| **Bridge / runtime injection** (this layer) | The local, user-mediated runtime that reads `.klickd`, decrypts it on-device, sanitizes it, and injects it into a target surface. | The Copilot bridge in `examples/v4/integrations/copilot-bridge/`, future adapters per surface. |
| **Tools / actions** (MCP, provider APIs) | How the model performs actions in the world. | MCP servers, OpenAI/Anthropic/Groq/xAI APIs, internal tool servers. |

`.klickd` **complements** skills — it does not replace them. A skill
declares what the model can *do*; a `.klickd` profile declares what it
should *remember* about this user, this project, and where the
conversation should resume.

## Security model (read this first)

The bridge is the only component that ever sees a passphrase. Concretely:

- **The AI model does not decrypt the `.klickd` file. The trusted local
  runtime does.** The model only ever sees the post-decrypt, sanitized
  context block — never the ciphertext, never the passphrase, never the
  `_`-prefixed debug fields.
- **The passphrase never leaves the device.** The CLI prompts via
  `getpass` from a TTY only. There is no `--passphrase` flag, no
  `$KLICKD_PASSPHRASE` env var, and no piped-stdin path. The VS Code
  design uses `showInputBox({ password: true })` and never writes to
  `SecretStorage` or the OS keyring.
- **Export policy is enforced before injection.** `_`-prefixed fields
  are stripped at every level (SPEC §29). Identity is reduced to a
  safe subset (`display_name`, `name`, `language`, `timezone`,
  `pronouns`, `role`) — contact data (`email`, `phone`, etc.) never
  reaches the prompt.
- **Sanitized context only.** What is injected is plain text that the
  user could have typed themselves; it is never executable, never a
  signed payload, never a new system instruction.

This security model is what makes "one integration, infinite reuse"
honest rather than aspirational: the same sanitized block is the only
artifact that ever crosses the bridge, regardless of which surface
consumes it.

## Compatibility matrix

Every entry below is **bridge-mediated compatibility, not native
support**. The user (or the bridge running on the user's machine) is the
one that injects the sanitized block; no third-party service reads
`.klickd` directly.

| Integration mode | What it looks like | Status in this repo | Honest framing |
|---|---|---|---|
| **Copy/paste system-prompt export** | CLI prints the sanitized block to stdout; the user pastes it into any chat box. | ✅ Implemented (`klickd_copilot_bridge.py`, `klickdCopilotBridge.ts`). | Works with any chat surface that accepts a pasted prompt. Zero coupling to a vendor. |
| **CLI pre-step** | `klickd-copilot-bridge profile.klickd --out .ctx.md` writes the block to a file that another tool consumes. | ✅ Implemented (`--out`). | The most portable mode. Used by CI, scripts, or as input to a chained tool. |
| **VS Code / editor extension** | Editor command picks a `.klickd` file, decrypts it locally, and injects the block into the chat input (clipboard fallback). | 📐 Design only (`vscode-extension-design/EXTENSION_DESIGN.md`). | First concrete adapter is the Copilot bridge. The same pattern fits Cursor-like editors. |
| **MCP server / tool** | A local MCP server exposes `klickd.load_memory()` and returns the sanitized block to any MCP-capable client. | 🚧 Not implemented in this repo. Design path documented. | Future-proof; depends on stable MCP client support in the target surface. |
| **API middleware** | Application server loads `.klickd` server-side or per-user, prepends the sanitized block to outbound prompts. | 🚧 Pattern documented in `docs/integrations/generic.md`. | Server-side keys must stay user-scoped; this mode is opt-in by the application owner. |
| **Web dropzone** | A browser page accepts a `.klickd` file, decrypts it locally (WASM or in-browser crypto), shows the sanitized block. | 🚧 Not implemented. Design constraints apply. | All decryption stays in the browser; no upload. |
| **Local LLM adapter** | Bridge feeds the sanitized block to a local model (Ollama, LM Studio, llama.cpp). | ✅ Same CLI; redirect into the local-model CLI. | The CLI's output is provider-agnostic, so this works today. |

## Surfaces reachable via the bridge

The following surfaces can consume a `.klickd`-derived context block
**through the bridge**. None of them load `.klickd` natively.

- **Hosted chat UIs**: GitHub Copilot Chat, Microsoft 365 Copilot Chat,
  ChatGPT, Claude.ai, Gemini, Grok, Perplexity.
- **Provider APIs**: OpenAI API, Anthropic API, Groq, xAI, OpenRouter.
- **Local model runtimes**: Ollama, LM Studio, llama.cpp-based stacks.
- **Editors / IDEs**: VS Code (via the extension design), Cursor-like
  editors that expose a chat-input command.
- **Agent surfaces**: MCP-compatible agents (via a future MCP server
  exposing `klickd.load_memory()`).

For each of these, the integration claim is the same: the bridge runs
on the user's device, decrypts locally if needed, sanitizes, and emits
a plain-text block that the surface accepts as ordinary chat input.

## Positioning

When describing this externally, the safe and accurate framing is:

> `.klickd` does not remove integration work — it makes it reusable.
> One integration. Infinite reuse. Across games, engines, platforms,
> apps, agents, robots, devices, and models.

Concretely:

- ✅ "Bridge-mediated compatibility with Copilot, ChatGPT, Claude,
  Gemini, Grok, Perplexity, OpenAI/Anthropic/Groq/xAI/OpenRouter,
  Ollama, LM Studio, VS Code, Cursor-like editors, and MCP-compatible
  agents."
- ✅ "The AI model does not decrypt the `.klickd` file. The trusted
  local runtime does."
- ✅ "`.klickd` complements `SKILL.md`-style behavior contracts."
- ❌ Do **not** claim "universal native support."
- ❌ Do **not** claim "automatic GDPR / EU AI Act compliance" — the
  bridge gives you the technical primitives (local decryption,
  passphrase isolation, redaction, sanitized export) that *help* a
  compliance program, but compliance is the operator's responsibility.
- ❌ Do **not** claim industry-standard adoption — `.klickd` is a
  community spec with reference implementations.

## First adapter: the Copilot bridge

The reference implementation in
[`examples/v4/integrations/copilot-bridge/`](../../examples/v4/integrations/copilot-bridge/)
is the **first concrete adapter** of the Universal `.klickd` Bridge. It
covers two of the modes above (copy/paste export and CLI pre-step) and
ships a design doc for a third (VS Code extension). Future adapters —
ChatGPT desktop, Claude desktop, an MCP server, a web dropzone — are
expected to share the same `build_context_block` core and the same
security properties.

The Copilot bridge's package and CLI names are kept stable for backward
compatibility. New adapters should live alongside it under
`examples/v4/integrations/<surface>-bridge/` and reuse
`context_builder` rather than re-implementing redaction.

## See also

- [`generic.md`](generic.md) — the universal `.klickd` reader pattern
- [`copilot.md`](copilot.md) — the Copilot-specific hybrid guide
- [`examples/v4/integrations/copilot-bridge/README.md`](../../examples/v4/integrations/copilot-bridge/README.md)
  — the first adapter's README
- [`examples/v4/integrations/copilot-bridge/vscode-extension-design/EXTENSION_DESIGN.md`](../../examples/v4/integrations/copilot-bridge/vscode-extension-design/EXTENSION_DESIGN.md)
  — the VS Code extension design
