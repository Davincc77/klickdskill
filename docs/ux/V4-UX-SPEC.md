# `.klickd` v4 — UX / Product Spec (Preview, NON-NORMATIVE)

> **Status:** Draft · NON-NORMATIVE · companion to the `v4.0.0-preview.1` track.
> **Scope:** product/UX intent for future `.klickd` v4 interfaces (viewer,
> decryptor, validator, migrator, agent handoff). **No spec, schema, SDK,
> wire-format, or vector change is implied by this document.**
>
> The normative surface for v4 remains:
> - [`SPEC.md` §33 (v4 Preview, non-normative)](../../SPEC.md)
> - [`schemas/klickd-payload-v4-preview.schema.json`](../../schemas/klickd-payload-v4-preview.schema.json)
> - [`schema/klickd-v4-preview.schema.json`](../../schema/klickd-v4-preview.schema.json)
> - [`docs/rfcs/`](../rfcs/) — RFC-001/002/003/004 (Draft)
> - [`docs/releases/v4.0.0-preview.1.md`](../releases/v4.0.0-preview.1.md)

This document describes **how a user should *feel* when handling a `.klickd`
v4 file**, not how implementers should encode it. Treat it as a UX contract
between any future v4 client (web, desktop, CLI, IDE plugin, mobile) and
the user.

---

## 1. North star

A `.klickd` file is a **portable, encrypted, model-neutral state object**.
A v4 client must preserve a single user-visible promise:

> **Load context → inspect what matters → resume work.**

Everything else (ledger, WAL, JCS canonicalization, AAD, Argon2id
parameters, verification artifacts, claim sources, migration reports,
unknown-field preservation) is **plumbing**. Plumbing must be auditable
on demand but invisible by default.

---

## 2. Principles

| # | Principle | What it means in practice |
|---|---|---|
| P1 | **Simple by default** | First-run user sees a human summary, not a JSON tree. Zero jargon above the fold. |
| P2 | **Progressive disclosure** | Power features (ledger, evidence, gates internals, schema diffs) sit behind explicit reveals. |
| P3 | **Local-first** | Decryption, validation, migration, and rendering happen in the user's process. No upload, no telemetry, no remote key derivation. |
| P4 | **Privacy-first** | Passphrase never leaves the input field. Memory of derived keys is bounded and explicitly cleared. No analytics on payload content. |
| P5 | **Evidence-aware** | When a claim is shown, its provenance (source, timestamp, model, confidence) MUST be reachable in ≤ 1 click. |
| P6 | **Model-neutral** | UI never assumes Anthropic / OpenAI / Groq / OpenRouter / local. Adapter previews are equally first-class. |
| P7 | **Never break the soul** | Migration is opt-in, reversible, and preserves unknown fields verbatim (per RFC-004). The UI must make rollback obvious. |
| P8 | **Hard gates are loud** | `block` / `require-owner` verification gates (RFC-002) are never silently bypassable from the UI. |

---

## 3. Main user flows

Each flow is described as **user intent → UI response → exit state**. All
flows assume a v4-preview-capable client and a single `.klickd` file as
input.

### 3.1 Open & decrypt locally

- **Intent:** "I have a `.klickd` file. Show me what's inside."
- **Response:**
  1. File picker (or drag-drop). The file never leaves the client.
  2. Passphrase prompt with masked input; show entropy hint inline (≥ 16
     chars recommended, zxcvbn-style indicator allowed but optional).
  3. Argon2id derivation runs in-process. UI shows a small "decrypting…"
     state, not a spinner that implies network I/O.
  4. On success → land on **Summary** (§4.1). On failure → distinguish
     wrong-passphrase from tampered-AAD from unsupported-version.
- **Exit:** Summary view; key material held in memory for the session only,
  cleared on tab/window close.

### 3.2 Validate version & schema

- **Intent:** "Is this file safe to open with my current tools?"
- **Response:**
  - Detect `klickd_version` (envelope) and `payload_schema_version`
    (payload). Display both as a discreet badge in the header.
  - If payload is `4.0.0-preview.1`, show a small **PREVIEW** chip with a
    tooltip linking to the [v4 release notes](../releases/v4.0.0-preview.1.md).
  - If the schema is unknown or newer than the client, show a single,
    non-blocking banner: *"This file uses fields your viewer doesn't
    recognise. They will be preserved on save."* (per the dual-reader
    contract in SPEC §33.)
- **Exit:** User knows whether they're in production (v3.5.1) or preview
  (v4-preview) territory.

### 3.3 Inspect human summary

- **Intent:** "Tell me what this file *is* in one screen."
- **Response:** A read-mostly **Summary** view (§4.1) with:
  - One-line identity (role + voice tone)
  - Most recent memories (≤ 5, with timestamps)
  - Top growth signals (≤ 3 competencies)
  - Active gates count (e.g. "3 confirm, 1 block")
  - Last session feeling / mood, if present
  - File health (size, age, schema version, migration status)
- **Exit:** User can decide whether to resume work or dig deeper.

### 3.4 Review rules / gates before action

- **Intent:** "Before I let an agent act on this, what guardrails apply?"
- **Response:** A **Rules & Gates** view (§4.3) listing every
  `verification_gates[]` entry grouped by severity (silent / warn /
  confirm / block / require-owner) with the scope each one applies to.
  Hard gates (`block`, `require-owner`) are visually distinct (color +
  icon) and never collapsed by default.
- **Exit:** User can copy a single "active gates summary" string into a
  prompt or session preamble.

### 3.5 Inspect evidence / provenance

- **Intent:** "Why does the file say this?"
- **Response:** Any claim surfaced in Summary or Memory must expose, on
  click, the supporting **`claim_sources` / `verification_artifacts`**
  entries (RFC-002 v2 surface) with at minimum: source URI or label,
  timestamp, model name, and confidence. Empty provenance is shown as
  an explicit *"no provenance recorded"* — never as silence.
- **Exit:** User can trust, distrust, or annotate the claim.

### 3.6 Generate agent-ready injection / context slice

- **Intent:** "Give me the prompt I should paste into my agent."
- **Response:** A **Model Adapter / Injection Preview** view (§4.6) that:
  - Lets the user pick a target adapter
    ([anthropic](../integrations/anthropic.md) /
    [openai](../integrations/openai.md) / [groq](../integrations/groq.md) /
    [openrouter](../integrations/openrouter.md) /
    [generic](../integrations/generic.md)).
  - Shows the resulting system-prompt slice **before** it is copied,
    with a token estimate and an explicit "this is what your agent will
    see" framing.
  - Optionally produces a **scoped slice** (project / role) without
    forking the file — tracked as the future RFC-005 scoped-state
    primitive in the [ROADMAP](../../ROADMAP.md).
- **Exit:** A copy-to-clipboard action that never touches the network.

### 3.7 Upgrade an older file without data loss

- **Intent:** "I have a `v2.5` / `v3.x` / `v3.5.1` file. Bring it forward."
- **Response:** A **Migration / Health** view (§4.7) that follows
  [RFC-004](../rfcs/RFC-004-migration-backward-compatibility.md):
  1. Mandatory backup of the original file (offered as a download before
     any in-place change).
  2. Dry-run diff: what changes, what is preserved verbatim, what is
     legacy.
  3. Explicit user confirmation per migration step.
  4. `migration_report` rendered as a human-readable changelog, not raw
     JSON.
  5. Rollback action always visible until the user explicitly dismisses
     the report.
- **Exit:** New file saved locally; original backup retained.

### 3.8 Export / share a safe copy

- **Intent:** "I want to send this to a teammate / future me / another
  agent."
- **Response:** An **Export** action with three explicit modes:
  - **Full (encrypted):** the `.klickd` file as-is. Default.
  - **Scoped slice (encrypted):** a sub-profile (project / role), once
    RFC-005 lands. Until then, exporting a scoped slice is **disabled
    with a "planned" tooltip** rather than faked.
  - **Plain JSON (DANGER):** unencrypted dump, gated behind a typed
    confirmation and a banner that the file no longer protects the
    user's memory.
- **Exit:** File written to disk. Nothing transmitted.

---

## 4. Information architecture

Top-level navigation has **seven** sections, in this order. Sections 1–3
are visible by default; 4–7 are progressive-disclosure tabs.

### 4.1 Summary *(default landing)*
Identity, recent memory, top growth signals, active gates count, file
health. Read-mostly. No editing primitives above the fold.

### 4.2 Memory
`memory[]` entries (per SPEC §28), filterable by modality and tags.
Each row exposes provenance on click (§3.5). Soul-handoff fields
(SPEC §28.8) shown as a dedicated subsection.

### 4.3 Rules / Gates
`ethics`, `verification_gates`, `human_veto_policy`. Hard gates loud
(P8). Ethics block visibly marked **SYSTEM authority · immutable**.

### 4.4 Evidence
`claim_sources`, `verification_artifacts`, `error_journal` (planned
RFC-005). Sortable by timestamp, model, confidence.

### 4.5 Timeline
Append-only event view. The underlying ledger / WAL is **not** the
mental model exposed to the user; the user sees a chronology of
sessions, migrations, and gate events. Raw entries reachable behind a
"Show raw" toggle.

### 4.6 Model adapters / Injection preview
Per-adapter previews of the system-prompt slice (§3.6) with token
estimate and adapter-specific caveats linked from
[`docs/integrations/`](../integrations/).

### 4.7 Migration / Health
Schema version, file age, size, last migration, backup status. Entry
point for the upgrade flow (§3.7).

---

## 5. UX guardrails

The following are **must-not-do** rules. They are framed as guardrails
because a v4 client that violates them silently undermines the format's
trust model — independently of whether the wire format remains valid.

| # | Don't | Why |
|---|---|---|
| G1 | **Don't expose raw JSON first.** | P1/P2. A JSON tree as the landing screen makes the format feel like a database, not a memory. Raw view is a tab, not a default. |
| G2 | **Don't imply private memory is shared truth.** | Memory is the user's private state. The UI must never present it as a public knowledge base or as the model's "facts". Phrase: *"what you've told this file"*, not *"what is true"*. |
| G3 | **Don't hide hard gates.** | P8. `block` / `require-owner` gates must be visible in the header gate count and never collapsed by default. |
| G4 | **Don't send the file to a server.** | P3. No upload, no remote validation, no cloud key derivation, no telemetry of payload content. CI/health pings about *the app itself* are OK if disclosed; payload exfiltration is not. |
| G5 | **Don't log passphrases or secrets.** | P4. No console.log, no error report capture, no clipboard auto-copy of the passphrase. Crash reports MUST scrub the input field. |
| G6 | **Don't fake features that don't exist yet.** | If RFC-005 scoped slices, strict v4 validation, or migration tooling aren't implemented, surface them as **disabled with a "planned" tooltip** linking to the RFC — never simulate them. |
| G7 | **Don't normalize bypassing migration backups.** | P7. The "skip backup" path, if it exists, MUST be a typed confirmation, not a checkbox. |
| G8 | **Don't surface unknown fields as errors.** | Per SPEC §33 dual-reader contract: unknown fields are *preserved*, not flagged as corruption. UI may show "(unknown to viewer)" but MUST NOT suggest deletion. |

---

## 6. Adoption

### 6.1 Beginner mode (default)

- Single passphrase input, no KDF tuning knobs.
- Three visible sections: Summary, Memory, Rules/Gates.
- One copy-to-clipboard action: "Give my agent this context".
- All advanced tabs collapsed behind a single "Advanced" toggle.

### 6.2 Expert mode (opt-in)

Unlocks:
- Argon2id parameter preview (m / t / p, KDF block, cipher block).
- Raw JSON view (read-only by default; edit gated behind a second
  confirmation).
- Test-vector replay for the open file (calls into the same logic the
  reference SDKs use — local only).
- Adapter A/B preview (Anthropic vs OpenAI vs Groq vs OpenRouter vs
  generic), token deltas.
- Migration dry-run with full diff (per RFC-004).
- Ledger / WAL raw view (G3 still applies — gates remain loud).

### 6.3 What is *out of scope* for a v4-preview UI

- Cloud sync, account systems, multi-user shared truth.
- Server-side validation services.
- Vendor extensions that break CC0 compatibility.
- Any mechanism that allows `ethics.locked_actions` to be overridden at
  runtime (cross-ref [ROADMAP "Out of scope"](../../ROADMAP.md)).

---

## 7. Acceptance criteria for a v4-preview client

A client claiming "v4-preview UX-compliant" SHOULD:

1. Implement flows §3.1, §3.2, §3.3, §3.4, §3.6 fully.
2. Implement flows §3.5, §3.7, §3.8 at least in read / dry-run form.
3. Respect every guardrail in §5 (G1–G8).
4. Preserve unknown / preview fields on save (SPEC §33 dual-reader
   contract).
5. Ship beginner mode (§6.1) as the default; expert mode (§6.2) opt-in.
6. Not publish a `v4` stable claim — the underlying preview is
   explicitly **NOT GA** ([release notes](../releases/v4.0.0-preview.1.md)).

This list is intentionally short. UX-compliance is not a certification
program; it is a self-check.

---

## 8. Cross-references

- **Roadmap slot:** [`ROADMAP.md`](../../ROADMAP.md) — v4.0 (medium-term — GA target)
- **Preview boundaries:** [`docs/releases/v4.0.0-preview.1.md`](../releases/v4.0.0-preview.1.md), [`docs/releases/CHECKLIST_v4_preview.md`](../releases/CHECKLIST_v4_preview.md)
- **Normative spec hook:** [`SPEC.md` §33](../../SPEC.md)
- **RFC index:** [`docs/rfcs/README.md`](../rfcs/README.md)
- **Related RFCs:** [RFC-001](../rfcs/RFC-001-media-profile-v1.md) · [RFC-002](../rfcs/RFC-002-verification-gates.md) · [RFC-004](../rfcs/RFC-004-migration-backward-compatibility.md)
- **Acknowledgements:** [`ACKNOWLEDGEMENTS.md`](../../ACKNOWLEDGEMENTS.md)

---

*This document is docs-only and non-normative. It does not change the
wire format, schemas, SDKs, or test vectors. Promotion of any UX
requirement into a normative MUST/SHOULD requires a separate RFC.*
