# `.klickd` ↔ Copilot bridge — reference implementation

> **Status:** reference scaffold. This is **not** a claim of native
> Copilot compatibility. GitHub Copilot and Microsoft 365 Copilot
> cannot directly read or decrypt `.klickd` files. This bridge enables
> a user-mediated workflow: load a `.klickd` profile locally, build a
> sanitized system/context block, and let the user (or a VS Code
> extension) paste/inject it into a Copilot Chat session.

See [`docs/integrations/copilot.md`](../../../../docs/integrations/copilot.md)
for the broader hybrid pattern and safe wording.

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
- ✅ "The bridge decrypts locally; the passphrase never leaves the
  device."
- ❌ Do **not** say "Copilot loads `.klickd` directly", "native Copilot
  compatibility", or "drop a `.klickd` file in `.github/skills/` and
  Copilot will read it." None of those are true today.
