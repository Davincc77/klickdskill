# Copilot × `.klickd` — example bridge

This directory holds an **example** `SKILL.md` showing how a Copilot Skill
could be paired with a custom loader (Copilot Extension, MCP server, or CLI)
to expose `.klickd` portable memory inside a Copilot conversation.

It is **not** a drop-in skill. GitHub Copilot and Microsoft 365 Copilot
cannot parse or decrypt `.klickd` files directly. The `SKILL.md` only
documents the behavior contract; the data must come from a loader you
supply.

See [`docs/integrations/copilot.md`](../../../../docs/integrations/copilot.md)
for the full hybrid pattern, three viable integration surfaces (Extension /
MCP / CLI), and safe wording when describing this integration externally.

## Files

| File | Purpose |
|---|---|
| [`SKILL.md`](SKILL.md) | Example Copilot Skill manifest — declares behavior, not data |

## Quick reference

```
SKILL.md         → describes WHAT Copilot should do when memory is loaded
.klickd file     → carries the actual user/project memory (user-owned)
custom loader    → bridges the two; decrypts locally; strips `_`-fields
```

The loader is the part you have to build. See
[`docs/integrations/generic.md`](../../../../docs/integrations/generic.md)
for the canonical `.klickd` reader pattern that the loader should implement.
