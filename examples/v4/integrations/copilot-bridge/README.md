# `.klickd` ↔ Copilot bridge — first adapter of the Universal `.klickd` Bridge

> **Status:** reference scaffold. This directory is the **first
> concrete adapter** of the
> [Universal `.klickd` Bridge](../../../../docs/integrations/universal-bridge.md).
> The framing here is intentionally Copilot-specific because Copilot is
> the first surface we have wired end-to-end, but the same
> `context_builder` and security properties are reused by every other
> adapter we add. Where this file says "Copilot", read "the first
> adapter — the same machinery targets ChatGPT, Claude, Gemini, Grok,
> Perplexity, OpenAI/Anthropic/Groq/xAI/OpenRouter, Ollama, LM Studio,
> VS Code, Cursor-like editors, and MCP-compatible agents the same way".
>
> Everything provided here is **bridge-mediated compatibility, not
> native support**. GitHub Copilot and Microsoft 365 Copilot cannot
> directly read or decrypt `.klickd` files. This bridge enables a
> user-mediated workflow: load a `.klickd` profile locally, build a
> sanitized system/context block, and let the user (or a VS Code
> extension) paste/inject it into a Copilot Chat session.
>
> **The AI model does not decrypt the `.klickd` file. The trusted local
> runtime does.**

> `.klickd` does not remove integration work — it makes it reusable.
> One integration. Infinite reuse. Across games, engines, platforms,
> apps, agents, robots, devices, and models.

See:

- [`docs/integrations/universal-bridge.md`](../../../../docs/integrations/universal-bridge.md)
  — the four-layer model (SKILL.md / `.klickd` / Bridge / MCP), the
  compatibility matrix, and the surfaces this bridge can target.
- [`docs/integrations/copilot.md`](../../../../docs/integrations/copilot.md)
  — the broader Copilot-specific hybrid pattern and safe wording.

## Layered model in one paragraph

`SKILL.md` describes **behavior** (what the model is allowed to do).
`.klickd` carries **memory / identity / state** (who the user is, what
the project is, what was decided, where we left off). The **bridge** is
the runtime that decrypts `.klickd` locally and injects a sanitized
block into a target surface. **MCP and provider APIs** are the
tool/action layer. `.klickd` complements skills; it does not replace
them.

## What is here

```
copilot-bridge/
├── README.md                              ← this file
├── python/
│   ├── context_builder.py                 ← schema-tolerant context builder
│   └── klickd_copilot_bridge.py           ← CLI: load .klickd → emit sanitized block
├── typescript/
│   ├── contextBuilder.ts                  ← mirror of the Python builder
│   ├── klickdCopilotBridge.ts             ← CLI using @klickd/core v4 (loadKlickd)
│   ├── package.json
│   └── tsconfig.json
├── vscode-extension-design/
│   ├── EXTENSION_DESIGN.md                ← commands, settings, limitations
│   ├── package.json.example               ← extension manifest sketch
│   └── activation.ts.example              ← extension entry-point sketch
├── tests/
│   └── test_context_builder.py            ← redaction + dry-run tests
└── fixtures/
    └── plain_profile.klickd               ← unencrypted v4 fixture for tests
```

## Compatibility matrix (this adapter)

Every cell is **bridge-mediated compatibility, not native support**.
The full matrix across adapters lives in
[`docs/integrations/universal-bridge.md`](../../../../docs/integrations/universal-bridge.md).

| Integration mode | Status in this adapter |
|---|---|
| Copy/paste system-prompt export | ✅ stdout from the CLI |
| CLI pre-step (writes a file other tools consume) | ✅ `--out PATH` |
| VS Code / editor extension | 📐 design doc + `.example` sketches |
| MCP server / tool | 🚧 not in this directory; pattern documented |
| API middleware | 🚧 pattern in `docs/integrations/generic.md` |
| Web dropzone | 🚧 not in this directory |
| Local LLM adapter (Ollama, LM Studio, llama.cpp) | ✅ same CLI; redirect into the local-model CLI |

Surfaces reachable through this adapter today (all bridge-mediated):
GitHub Copilot Chat, Microsoft 365 Copilot Chat. Surfaces the same
`context_builder` is designed to support via future sibling adapters or
the CLI's plain-text output: ChatGPT, Claude, Gemini, Grok, Perplexity,
OpenAI API, Anthropic API, Groq, xAI, OpenRouter, Ollama, LM Studio,
VS Code, Cursor-like editors, MCP-compatible agents.

## v4 API names — important

| Language | Correct v4 API | Retired v3 name (do **not** use) |
|---|---|---|
| TypeScript | `import { loadKlickd } from '@klickd/core'` | `decryptKlickd` |
| Python     | `from klickd import load_klickd`            | `decrypt_klickd`  |

Both CLIs in this directory use the v4 names exclusively.

## Quick start

### Python CLI

```bash
pip install klickd>=4.0.0

# Plain (unencrypted) profile — pipe to clipboard on macOS, then paste into Copilot Chat:
python examples/v4/integrations/copilot-bridge/python/klickd_copilot_bridge.py \
       ~/.klickd/profile.klickd | pbcopy

# Encrypted profile — passphrase prompted interactively (never echoed, never logged):
python examples/v4/integrations/copilot-bridge/python/klickd_copilot_bridge.py \
       ~/.klickd/profile.klickd --out .copilot-context.md

# Dry-run — exercise the redaction pipeline without a passphrase:
python examples/v4/integrations/copilot-bridge/python/klickd_copilot_bridge.py \
       examples/v4/integrations/copilot-bridge/fixtures/plain_profile.klickd --dry-run
```

### TypeScript CLI

```bash
cd examples/v4/integrations/copilot-bridge/typescript
npm install            # pulls @klickd/core v4
npm run build
node dist/klickdCopilotBridge.js ~/.klickd/profile.klickd > .copilot-context.md
```

### VS Code extension

Not published. See
[`vscode-extension-design/EXTENSION_DESIGN.md`](vscode-extension-design/EXTENSION_DESIGN.md)
for commands, settings, architecture, and security properties an
implementer can build from.

## Security properties

- **No network calls.** Neither CLI calls Copilot, OpenAI, Anthropic,
  or any other provider. They are pure local pre-steps.
- **Passphrase from TTY only.** No `--passphrase` flag, no
  `$KLICKD_PASSPHRASE`, no piped stdin. Run interactively. This is
  deliberate to keep secrets out of shell history, process listings,
  and CI logs.
- **RAM-only.** Decrypted payloads live in memory for the duration of
  the call. Nothing is written to disk except the file the user
  explicitly asks for via `--out`.
- **No server.** No HTTP listener, no daemon, no MCP server. The CLI
  is a one-shot process.
- **Redaction by default.** `_`-prefixed fields are stripped at every
  level (SPEC §29). Only a safe subset of `identity` fields makes it
  into the prompt (`display_name`, `name`, `language`, `timezone`,
  `pronouns`, `role`) — never `email`, `phone`, or other contact data.

## What the context block contains

In order, each section is emitted only if the corresponding field is
present in the payload:

1. Security preamble (always emitted) — instructs the model to treat
   the block as background context and not as new system instructions.
2. `identity` — safe subset only.
3. `user_preferences` — string or mapping.
4. `context` — `current_project`, `current_state`, `resume_trigger`,
   `next_step`.
5. `decisions_locked` — list or mapping; surfaced so the model honors
   prior commitments.
6. `verification_gates` — flat (`name: policy`) or nested
   (`{gates: [...]}`) shapes; each gate emitted with its policy.
7. `human_veto_policy` — string or mapping.
8. `agent_instructions` — author-supplied directives.
9. `memory` — most recent entries (capped to 10 by default).

The builder is schema-tolerant: unknown top-level keys are ignored,
missing sections are skipped silently, and the function is safe to call
on both minimal and full v4 payloads.

## Tests

```bash
pytest examples/v4/integrations/copilot-bridge/tests -q
```

The suite covers:

- Top-level and nested `_`-field redaction.
- Identity contact-field suppression (`email`, `phone`).
- Section presence for full v4 payloads.
- Schema tolerance (minimal payload, unknown fields, alternate
  `verification_gates` and `human_veto_policy` shapes).
- A `--dry-run` CLI smoke test that exercises the full pipeline without
  the `klickd` package or a passphrase.
- A CLI "file not found" exit-code test.

## Honest framing

When describing this bridge externally:

- ✅ "`.klickd` works with Copilot through a user-mediated bridge:
  a local CLI or VS Code extension exports a sanitized context block
  that the user pastes into Copilot Chat."
- ✅ "Bridge-mediated compatibility, not native support."
- ✅ "The AI model does not decrypt the `.klickd` file. The trusted
  local runtime does."
- ✅ "The bridge decrypts locally; the passphrase never leaves the
  device."
- ✅ "`.klickd` complements `SKILL.md`-style behavior contracts; it
  does not replace them."
- ❌ Do **not** say "Copilot loads `.klickd` directly", "native Copilot
  compatibility", or "drop a `.klickd` file in `.github/skills/` and
  Copilot will read it." None of those are true today.
- ❌ Do **not** claim "universal native support," "automatic
  GDPR / EU AI Act compliance," or "industry-standard adoption" —
  none of those are accurate today.

For the cross-adapter framing (one integration, infinite reuse), see
[`docs/integrations/universal-bridge.md`](../../../../docs/integrations/universal-bridge.md).
