# VS Code Extension — `.klickd` ↔ Copilot bridge (design)

> **Status:** design only. No extension is published. This document
> describes how an extension *would* wire the CLI bridge into VS Code so
> a user can load a local `.klickd` v4 profile into a GitHub Copilot
> Chat session with one command.
>
> This extension is the **first editor-side adapter of the Universal
> `.klickd` Bridge** (see
> [`docs/integrations/universal-bridge.md`](../../../../../docs/integrations/universal-bridge.md)).
> The same architecture applies to Cursor-like editors and other surfaces
> that expose a chat-input command. All compatibility provided is
> **bridge-mediated, not native support** — and **the AI model does not
> decrypt the `.klickd` file; the trusted local runtime does**.

## Why an extension and not direct compatibility

GitHub Copilot and Microsoft 365 Copilot **cannot directly load a
`.klickd` file**. From their perspective the file is an opaque blob.
Specifically:

- M365 Copilot ingests skills as `SKILL.md` / declarative agents and
  has no `.klickd` parser, no access to the user's passphrase, and no
  content-type allowlist that maps `*.klickd` to a known schema.
- GitHub Copilot Chat accepts skills, slash commands, and tools — but
  only through documented manifests, not by opening a binary-shaped
  user file.
- Encrypted `.klickd` envelopes require a user-held passphrase that
  must never reach a third-party service.

The extension therefore acts as a **user-mediated bridge**: the user
explicitly invokes it, the decryption happens on-device, and the
sanitized context block is injected into the Copilot conversation via
the user's clipboard or via Copilot's public chat-input API.

## Commands

| Command ID | Title | Behavior |
|---|---|---|
| `klickd.copilot.loadProfile` | `.klickd: Load profile into Copilot Chat` | Pick a `.klickd` file, prompt for passphrase if encrypted, build the sanitized block, and insert it into the active Copilot Chat session (or copy to clipboard with a notification if the chat API is unavailable). |
| `klickd.copilot.exportContextToClipboard` | `.klickd: Export profile as Copilot context (clipboard)` | Same loader, but always writes to the clipboard. Useful when the chat-input API surface is missing or the user wants to paste manually. |
| `klickd.copilot.exportContextToFile` | `.klickd: Export profile as Copilot context (file)` | Writes the block to `.copilot-context.md` in the workspace root (gitignored by default). |
| `klickd.copilot.dryRunRedaction` | `.klickd: Preview redacted context (dry-run)` | Skips decryption; shows the envelope-only block in a read-only editor pane. Useful for debugging redaction without exposing a passphrase. |
| `klickd.copilot.forgetSession` | `.klickd: Forget loaded profile` | Clears any in-memory references the extension may hold and notifies the user. |

## Settings

| Setting | Type | Default | Purpose |
|---|---|---|---|
| `klickd.copilot.defaultProfile` | string | `""` | Optional path to a `.klickd` file used by `loadProfile` when no picker is shown. |
| `klickd.copilot.memoryEntryLimit` | number | `10` | Max number of memory entries to include in the injected block. |
| `klickd.copilot.includeAgentInstructions` | boolean | `true` | Whether to include the `agent_instructions` section. |
| `klickd.copilot.askBeforeInjecting` | boolean | `true` | Show a confirmation with a preview before sending the block to Copilot. |

There is intentionally **no setting** to store a passphrase, a default
key, or any path that maps to a credential. The extension never offers
"remember my passphrase" — the system keyring is out of scope for this
design.

## Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│ VS Code extension host                                               │
│                                                                      │
│   activate()                                                         │
│      └── registerCommand('klickd.copilot.loadProfile', loadProfile)  │
│                                                                      │
│   loadProfile():                                                     │
│      1. window.showOpenDialog → pick .klickd file                    │
│      2. fs.readFile → bytes                                          │
│      3. if encrypted: window.showInputBox(password: true) for pass   │
│      4. await loadKlickd(bytes, { passphrase })  (RAM only)          │
│      5. buildContextBlock(payload)                                   │
│      6. if askBeforeInjecting: showPreviewWebview()                  │
│      7. inject:                                                      │
│           a) try vscode.commands.executeCommand(                      │
│                'workbench.action.chat.open', { query: block }) // GH │
│           b) fallback: env.clipboard.writeText(block) + toast        │
│      8. zero out passphrase reference (best-effort)                  │
└──────────────────────────────────────────────────────────────────────┘
```

Reusable building blocks (no Copilot dependency):

- `buildContextBlock` — the same function exported from
  `../typescript/contextBuilder.ts`. The extension imports it directly
  rather than reimplementing redaction.
- `loadKlickd` — `@klickd/core` v4 GA. The retired v3 name
  `decryptKlickd` is **not** used.

## Security properties

1. **Local-only.** The extension never makes network requests. The
   only output channels are the VS Code window, the clipboard, and the
   workspace filesystem when the user explicitly invokes `exportToFile`.
2. **No passphrase persistence.** Passphrases are read via
   `showInputBox({ password: true })`, held in a local variable for
   exactly one `loadKlickd` call, then dropped. The extension does not
   write to `vscode.SecretStorage`, the OS keyring, or workspace state.
3. **No env var passphrase.** The extension does not honor
   `KLICKD_PASSPHRASE` or any environment variable, mirroring the CLI's
   stance. CI/headless use is out of scope.
4. **Redaction before injection.** The Copilot input only ever sees the
   block produced by `buildContextBlock`, which strips `_`-prefixed
   debug/benchmark fields at every level and only emits a safe subset of
   `identity` (no `email`, `phone`, etc.).
5. **No provider API calls.** The extension never calls Copilot,
   OpenAI, Anthropic, etc. It only invokes Copilot through the
   user-facing chat-input command — i.e. it does what the user could do
   by pasting manually.
6. **Confirmation by default.** `askBeforeInjecting: true` shows the
   user the exact block that will be sent before any injection.

## Limitations (honest framing)

- **Not "native" Copilot integration.** This bridge cannot register a
  `.klickd` content type with Copilot, nor make Copilot auto-load a
  workspace `.klickd` file. The user must explicitly invoke a command.
- **Chat-input injection depends on Copilot Chat APIs that may change.**
  The fallback path (clipboard + paste) is the durable contract.
- **No GitHub Copilot Extension server.** Building Copilot Extensions
  requires a network-reachable HTTPS server and an Anthropic / GitHub
  app registration. That path is described in
  [`docs/integrations/copilot.md`](../../../../../docs/integrations/copilot.md)
  but deliberately out of scope for this reference extension.
- **M365 Copilot is currently out of reach.** M365 Copilot's extension
  surface (declarative agents, Copilot Studio actions) does not expose
  a chat-input injection point an editor extension can drive. The
  CLI's `--out` flag is the supported path there: export to a file,
  paste into the M365 Copilot Chat box.
- **MCP is the future-proof path.** Once Copilot Chat ships stable MCP
  client support, an MCP server exposing a `klickd.load_memory()` tool
  becomes a stronger integration than this extension. The extension is
  meant to bridge the gap until then.

## File layout (proposed)

```
copilot-bridge/vscode-extension-design/
├── EXTENSION_DESIGN.md       ← this file
├── package.json.example      ← extension manifest sketch
└── activation.ts.example     ← extension entry point sketch
```

The `.example` suffix is intentional: nothing here is meant to be built
and published as-is. Treat them as starting points for an
implementation.

## See also

- [`../python/klickd_copilot_bridge.py`](../python/klickd_copilot_bridge.py)
  — the canonical CLI that the extension wraps.
- [`../typescript/contextBuilder.ts`](../typescript/contextBuilder.ts)
  — the redaction module the extension reuses.
- [`docs/integrations/copilot.md`](../../../../../docs/integrations/copilot.md)
  — the broader hybrid pattern (SKILL.md + custom loader).
- [`docs/integrations/generic.md`](../../../../../docs/integrations/generic.md)
  — the universal `.klickd` reader pattern.
