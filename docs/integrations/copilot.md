# GitHub Copilot / Microsoft 365 Copilot — .klickd v4 Integration

> **Status:** Complementary, **not** directly compatible.
> Copilot Skills and `.klickd` solve different problems. They can be combined via a
> hybrid pattern (SKILL.md describes behavior, `.klickd` supplies user/project memory
> through a custom loader, CLI, or user-mediated prompt injection). Neither GitHub
> Copilot nor Microsoft 365 Copilot can decrypt or auto-load a `.klickd` file today.

## TL;DR

| | Copilot Skills (`SKILL.md`) | `.klickd` (portable memory) |
|---|---|---|
| Format | Markdown manifest (plain text) | JSON, optionally AES-256-GCM encrypted |
| Purpose | Declare a *skill / behavior* the model should expose | Carry *user + project memory* across sessions and providers |
| Loaded by | GitHub Copilot, Copilot Extensions, M365 Copilot Studio | Any client that implements the `.klickd` reader pattern |
| Trust boundary | Repo-level (Git, signed by org) | User-level (the user owns the file and key) |
| Decryption support | None for `.klickd` payloads | Required for `encrypted: true` files |

Copilot Skills tell Copilot *what it can do*. `.klickd` tells *any* model
*what it should remember about this user, this project, and where we left off*.
The two layers are orthogonal.

## Why direct loading does not work

- **M365 Copilot** ingests skills as `SKILL.md` (or declarative agents / Copilot
  Studio actions). It has no parser for `.klickd`, no access to the user's
  passphrase, and no allowlist that maps `*.klickd` to a known content type.
- **GitHub Copilot** chat / Copilot Extensions accept skills, slash commands,
  and tools — but again, only via documented manifests. A `.klickd` file in the
  repo is, from Copilot's perspective, an opaque blob.
- `.klickd` files may be encrypted. Even if a client could read the file,
  decryption requires a user-held key that must never reach a third-party
  service.

So the honest framing is: `.klickd` does not become a Copilot Skill, and a
Copilot Skill does not replace `.klickd`. They compose.

## Hybrid pattern (recommended)

```
┌──────────────────────────┐        ┌────────────────────────────┐
│  .github/skills/         │        │  ~/.klickd/profile.klickd  │
│    klickd-memory/        │        │  (user-owned, may be       │
│      SKILL.md            │        │   AES-256-GCM encrypted)   │
│  (behavior contract)     │        └─────────────┬──────────────┘
└────────────┬─────────────┘                      │
             │ Copilot loads                      │ loader/CLI/extension
             ▼                                    ▼
        ┌─────────────────────────────────────────────────┐
        │  Custom loader (Copilot Extension, VS Code      │
        │  extension, MCP server, or local CLI):          │
        │   1. parse + validate .klickd                   │
        │   2. decrypt locally if encrypted               │
        │   3. strip `_`-prefixed fields                  │
        │   4. build system / context block               │
        │   5. inject into Copilot conversation           │
        └─────────────────────────────────────────────────┘
```

Three viable integration surfaces today:

1. **Copilot Extension or MCP server** — a small server you control reads the
   `.klickd` file, decrypts it locally with the user's key, and exposes a tool
   like `klickd.load_memory()` that returns the stripped system block. The
   `SKILL.md` documents the behavior contract; the extension supplies the data.
2. **VS Code / editor extension** — same idea, but the extension injects the
   `.klickd`-derived context into the Copilot chat as a user-mediated prompt
   (e.g. a `/klickd load profile.klickd` slash command that pastes the
   stripped system block at the top of the conversation).
3. **CLI pre-step** — `klickd export --system > .copilot-context.md`, then the
   user pastes the file into Copilot chat. No extension required, fully
   user-mediated, no key ever leaves the device.

In all three cases the `.klickd` reader follows the universal pattern
documented in [`generic.md`](generic.md):
`parse → validate → strip → toSystemPrompt → inject → call`.

## Example `SKILL.md` (behavior contract)

A minimal SKILL.md is included at
[`examples/v4/integrations/copilot/SKILL.md`](../../examples/v4/integrations/copilot/SKILL.md).
It describes the behavior Copilot should expose; the actual data still comes
from a `.klickd` file loaded by a custom loader.

> The example **does not** claim Copilot can decrypt or auto-load `.klickd`.
> It documents the contract that a Copilot Extension, MCP server, or CLI
> pre-step would fulfil.

## Reference bridge implementation

A working reference of the CLI pre-step (option 3 above) and the VS Code
extension design (option 2) lives at
[`examples/v4/integrations/copilot-bridge/`](../../examples/v4/integrations/copilot-bridge/).
It is the **first concrete adapter of the Universal `.klickd` Bridge**;
the broader framing — four-layer model, compatibility matrix across
surfaces, and the security phrasing "the AI model does not decrypt the
`.klickd` file; the trusted local runtime does" — is in
[`universal-bridge.md`](universal-bridge.md). Copilot is the first
adapter; everything provided is bridge-mediated compatibility, not
native support.
It contains:

- A Python CLI (`klickd_copilot_bridge.py`) and a TypeScript CLI
  (`klickdCopilotBridge.ts`) that load a local `.klickd` v4 profile,
  prompt for the passphrase interactively if needed, and emit a
  sanitized system/context block to stdout or a file.
- A schema-tolerant context builder (Python + TypeScript mirror) that
  handles `identity`, `user_preferences`, `context`, `memory`,
  `decisions_locked`, `verification_gates`, `human_veto_policy`, and
  `agent_instructions`, strips `_`-prefixed fields at every level, and
  refuses to surface contact data from `identity`.
- A VS Code extension design doc with commands, settings,
  architecture, security properties, and honest limitations
  ([`EXTENSION_DESIGN.md`](../../examples/v4/integrations/copilot-bridge/vscode-extension-design/EXTENSION_DESIGN.md)).
- Tests for redaction and a CLI dry-run smoke test.

The bridge uses the v4 GA API names — `loadKlickd` in TypeScript and
`load_klickd` in Python. The retired v3 names (`decryptKlickd` /
`decrypt_klickd`) are not used anywhere.

## What to tell users

Safe wording when describing this integration externally:

- ✅ "`.klickd` is **complementary** to Copilot Skills."
- ✅ "Loading a `.klickd` file into Copilot requires a custom loader (Copilot
  Extension, MCP server, or CLI) or a user-mediated prompt injection."
- ✅ "Encrypted `.klickd` files are decrypted locally; the passphrase never
  reaches Copilot or any third-party service."
- ❌ Do **not** say "Copilot loads `.klickd` directly" or "drop a `.klickd`
  file in `.github/skills/` and Copilot will read it." Neither is true today.

## Validation checklist

- [ ] `SKILL.md` declares the behavior, not the data
- [ ] Custom loader (extension / MCP / CLI) performs parse + strip + decrypt
- [ ] Passphrase never sent to Copilot or any remote service
- [ ] `_`-prefixed fields stripped before injection (SPEC §29)
- [ ] Users informed that this is a hybrid pattern, not direct compatibility

## See also

- [`universal-bridge.md`](universal-bridge.md) — Universal `.klickd`
  Bridge: four-layer model, compatibility matrix, and the surfaces
  reachable through bridge-mediated compatibility
- [`generic.md`](generic.md) — the universal `.klickd` reader pattern
- [`anthropic.md`](anthropic.md), [`openai.md`](openai.md) — provider-specific
  injection examples that the custom loader can reuse
- [GitHub Copilot Extensions docs](https://docs.github.com/en/copilot/building-copilot-extensions)
- [Microsoft 365 Copilot — declarative agents](https://learn.microsoft.com/en-us/microsoft-365-copilot/extensibility/)
