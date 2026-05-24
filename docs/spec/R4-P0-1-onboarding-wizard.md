# R4-P0-1 — `user.klickd` Onboarding Wizard (Normative, v4 P0)

> **Status:** NORMATIVE (V4 P0). Docs-only promotion of [SPEC §33](../../SPEC.md)
> R4-P0-1 preview wording toward the normative `.klickd` v4 surface. This
> document uses **RFC 2119 / RFC 8174** key words (MUST, MUST NOT, SHALL,
> SHOULD, SHOULD NOT, MAY) as defined therein.
>
> **Scope:** this document binds the user-visible onboarding flow that any
> conforming v4 `user.klickd` writer (web, desktop, CLI, mobile, IDE
> plugin) MUST expose to a first-time non-developer user. It does **not**
> bind SDK internals, schema strictness, wire-format, vectors, or
> packaging. No SDK, schema, vector, npm / PyPI / Zenodo / DOI / Git tag
> release is implied or required by this document.
>
> **Out of scope (kept for clarity, tracked elsewhere):** error message
> i18n table ([R4-P0-2](../roadmap/ROAD-TO-V4-GA.md#r4-p0-2--messages-derreur-klickd_e_-i18n-orientés-utilisateur)),
> downloadable example profiles ([R4-P0-3](../roadmap/ROAD-TO-V4-GA.md#r4-p0-3--profils-dexemple-téléchargeables-5-personas)),
> deprecation policy ([R4-P0-4](../roadmap/ROAD-TO-V4-GA.md#r4-p0-4--politique-de-dépréciation-v4-formelle)),
> QR / deeplink onboarding trigger ([R4-P1-5 / R4-P2-1](../roadmap/ROAD-TO-V4-GA.md#r4-p1-5--r4-p2-1--qr--deeplink-onboarding-trigger-conditionnel)
> and [`V4-ONBOARDING-QR-DEEPLINK.md`](../ux/V4-ONBOARDING-QR-DEEPLINK.md)),
> `media.klickd` continuity ([RFC-001](../rfcs/RFC-001-media-profile-v1.md)),
> `project.klickd` AGENTS.md export ([R4-P1-2](../roadmap/ROAD-TO-V4-GA.md#r4-p1-2--projectklickd-minimal--export-agentsmd)),
> `gaming.klickd` baseline ([R4-P1-4](../roadmap/ROAD-TO-V4-GA.md#r4-p1-4--gamingklickd-baseline-optionnelle-registry-based)).

---

## 1. Why this is normative now

Empirical UX convergence (1Password, Bitwarden, Obsidian, KeePassXC,
Letta `.af` first-run flows — see
[`V4-UX-DX-RESEARCH-NOTES.md`](../roadmap/V4-UX-DX-RESEARCH-NOTES.md))
shows that a `.klickd` v4 file generated **without** a guided wizard and
**without** a mandatory reload verification ends up unreadable by its
own author. Anti-pattern A1 (raw JSON wall) and anti-pattern A6
(non-actionable errors) are then locked in at onboarding time and
cannot be recovered downstream.

Promoting only the **onboarding wizard contract** to normative — not the
underlying schema, not the SDK, not the wire-format — is the minimum
intervention that prevents the format from regressing to a
developer-only artefact at V4 GA. Schema strictness (P0-2), SDK
alignment (P0-3 / P0-4), and vectors (P0-6) remain on their own
tracks. This document only constrains what a conforming `user.klickd`
writer **shows the user**.

---

## 2. Terminology

- **`user.klickd` writer**: any client (web component, desktop app,
  mobile app, CLI, IDE plugin) that produces a `user.klickd` v4 file
  intended for an end-user, non-developer audience.
- **Wizard**: the guided first-run flow described in §3.
- **Reload verification** (step 6 — see §3.6): mandatory re-open of the
  just-written file inside the same wizard, before the user is allowed
  to exit the flow with a "success" terminal state.
- **`user.klickd` vs `<x>.klickd`**: `user.klickd` is the personal
  identity / state profile for a single human end-user. Other
  `<x>.klickd` profiles (`project.klickd`, `agent.klickd`,
  `media.klickd`, `gaming.klickd`, `core.klickd`) are advanced /
  domain-specific and **MUST NOT** be reachable from the `user.klickd`
  wizard's main path. They MAY be reachable via a separate, advanced,
  progressive-disclosure entry (out of scope for this document).
- **Dominant choice**: at each wizard step, exactly one action is
  visually primary; the rest are secondary or hidden under
  progressive-disclosure controls.
- **Raw payload**: the JSON / CBOR / binary bytes of the produced
  `.klickd` file or any in-memory payload tree representation.

---

## 3. Normative wizard contract (R4-P0-1)

A conforming `user.klickd` writer **MUST** implement the seven steps
described in §3.1–§3.7, in order, with the constraints listed for each
step. The writer **MAY** present additional informational screens
before, between, or after these steps (e.g., a welcome screen, a
language selector, a final share / export prompt), but it **MUST NOT**
remove, merge, reorder, or skip any of the seven normative steps in the
`user.klickd` main path.

The writer **MUST NOT** expose the raw payload at any wizard step
described below. Inspection of the raw payload is out of scope for the
`user.klickd` main path; it **MAY** be reachable through a separate
"advanced" view that is not part of the wizard.

### 3.1 Step 1 — Welcome & explicit intent

- The writer **MUST** present a single explanatory screen stating, in
  the detected UI language: (a) what a `user.klickd` file is in one
  sentence, (b) that the file will live locally on the user's device
  by default, (c) that no account, server, or upload is involved.
- The dominant choice **MUST** be a single primary action ("Create my
  `user.klickd`" or equivalent). A secondary action **MAY** be
  provided ("I already have a `user.klickd` file → import").
- The writer **MUST NOT** require the user to read more than three
  short paragraphs before reaching the primary action.

### 3.2 Step 2 — Identity (minimum viable profile)

- The writer **MUST** collect, at minimum, the inputs that map to the
  `user.klickd` mandatory payload fields as defined by the current
  normative v4 schema track (P0-2; until P0-2 is GA, the writer
  **MUST** target the `user.klickd` minimum surface described in
  [SPEC §33](../../SPEC.md#33--klickd-v4-preview-non-normative)).
- The writer **MUST NOT** require any field that is not strictly
  required by the schema. Optional fields **MAY** be offered behind
  progressive disclosure.
- The writer **MUST NOT** collect personal data that is not used by
  the produced payload. In particular, the writer **MUST NOT** ask
  for an email, phone number, or legal name unless the schema or a
  user-selected optional facet explicitly requires it.

### 3.3 Step 3 — Preferences (one screen, dominant defaults)

- The writer **MUST** present preference choices (UI language, tone,
  verification-gate friction profile if relevant, `human_veto_policy`
  default if relevant) on a single screen with sensible defaults
  pre-selected.
- The dominant choice **MUST** be "Continue with defaults". Each
  preference **MUST** have a default value that is safe for a
  non-developer end-user.
- The writer **MUST NOT** require the user to understand
  `verification_gates`, `human_veto_policy`, `claim_sources`, or any
  other v4 internal field name to complete this step.

### 3.4 Step 4 — Passphrase

- The writer **MUST** require the user to enter a passphrase used by
  the file's Argon2id KDF (per the v3.x envelope contract that remains
  in force under §33.7).
- The writer **MUST** display an entropy indicator (visual hint
  acceptable; numeric score acceptable; the precise estimator is
  unspecified).
- The writer **MUST** require confirmation of the passphrase by a
  second entry, or by a "reveal once" interaction with explicit
  user-typed confirmation. The writer **MUST NOT** silently accept a
  single-entry passphrase without confirmation.
- The writer **MUST NOT** transmit the passphrase off-device by any
  channel (network, cross-tab, clipboard auto-copy, telemetry, error
  reporter). The passphrase **MUST** be cleared from memory after key
  derivation, except for the explicit re-derivation needed at step 6
  (reload verification).
- On failure to confirm, the writer **MUST** produce a user-oriented
  error message (i18n table defined by [R4-P0-2](../roadmap/ROAD-TO-V4-GA.md#r4-p0-2--messages-derreur-klickd_e_-i18n-orientés-utilisateur);
  if R4-P0-2 has not landed at the time of implementation, the writer
  **SHOULD** ship a minimal English fallback for each failure code).

### 3.5 Step 5 — Generate & save locally

- The writer **MUST** produce the `user.klickd` file entirely on the
  user's device. No network call **MAY** be required to complete this
  step.
- The writer **MUST** offer the user a clear, local destination for
  the file (download, save-as dialog, local app storage, OS keychain
  if applicable). The chosen destination **MUST NOT** be a third-party
  cloud upload by default. A future PR **MAY** add an opt-in
  cloud-backup facet; that opt-in is **NOT** part of the V4 P0
  normative onboarding path.
- The writer **MUST** display the resulting file's local path or
  storage location to the user before moving to step 6.
- The writer **MUST NOT** treat step 5 success as the end of the
  wizard. Reaching step 6 is mandatory (see §3.6).

### 3.6 Step 6 — Mandatory reload verification (non-negotiable)

- The writer **MUST** re-open the file produced at step 5 inside the
  same wizard process, and **MUST** require the user to re-enter the
  passphrase chosen at step 4 to decrypt it.
- The writer **MUST NOT** skip, hide, defer, or make optional the
  reload verification. The "Skip verification" path **MUST NOT**
  exist in a conforming `user.klickd` main path.
- If reload succeeds (file decrypts, payload parses, mandatory fields
  present): the writer **MUST** show an explicit success state ("Your
  `user.klickd` file is valid and re-openable.") and **MUST** advance
  to step 7.
- If reload fails (wrong passphrase, decryption error, missing
  mandatory field, payload parse error): the writer **MUST** show a
  user-oriented error message identifying the failure class (per
  R4-P0-2 when available; minimal English fallback otherwise) and
  **MUST** offer at least one user-actionable next step that does
  **NOT** require contacting support (e.g., "re-enter passphrase",
  "regenerate from step 4", "open the local file picker manually").
- The writer **MUST NOT** mark the produced file as "valid" or
  "ready to use" until step 6 has completed successfully.

### 3.7 Step 7 — Next steps (closing the loop)

- The writer **MUST** present a final screen telling the user, in the
  detected UI language: (a) where the file is now stored locally, (b)
  what the file is for in one sentence ("paste it into a `.klickd`-
  aware agent to resume your context"), (c) at least one explicit
  next action (open agent, copy local path, export a non-secret
  fingerprint, etc.).
- The writer **MUST NOT** auto-upload, auto-share, or auto-publish
  the file to any third party at step 7.
- The writer **MAY** offer optional onward actions (configure an
  agent integration, create a project profile, generate a backup
  reminder). These onward actions are out of scope for R4-P0-1 and
  **MUST NOT** block exit from the wizard.

---

## 4. Conformance requirements (cross-cutting)

A conforming `user.klickd` writer:

1. **MUST** keep the seven steps in the main `user.klickd` path
   linear and step-by-step. Free-form / power-user dashboards
   **MUST NOT** replace the wizard for first-time `user.klickd`
   creation.
2. **MUST NOT** expose raw payload bytes, raw JSON, raw CBOR, raw
   binary buffers, schema field names, or internal envelope fields
   (`kdf`, `cipher`, AAD, salt, nonce, ciphertext, MAC) inside the
   wizard UI. These **MAY** be reachable via a separate, opt-in
   "advanced view" reached from outside the wizard.
3. **MUST NOT** require any network call to complete steps 1–7. A
   future opt-in facet (cloud backup, sync, telemetry, crash
   reporting) **MUST** be off by default and **MUST NOT** be
   pre-checked at any wizard step.
4. **MUST** preserve unknown fields verbatim on any subsequent edit
   or re-save, per the §33.7 forward-compatibility contract.
5. **MUST** keep step 6 (reload verification) reachable on every
   first-time creation. Subsequent edits of an existing file
   **SHOULD** also offer a reload verification gesture, but this is
   **NOT** required by R4-P0-1.
6. **MUST NOT** introduce a separate `<x>.klickd` advanced flow
   (e.g., `project.klickd`, `agent.klickd`) into the `user.klickd`
   main path. Advanced profiles **MAY** be reached from a separate
   progressive-disclosure entry point.
7. **MUST NOT** add a QR-code or deeplink import path into steps 1–7
   of the `user.klickd` main flow as part of V4 P0. Any QR /
   deeplink trigger is governed by
   [`V4-ONBOARDING-QR-DEEPLINK.md`](../ux/V4-ONBOARDING-QR-DEEPLINK.md)
   and remains P1 conditional / P2.

---

## 5. Non-goals (explicit out-of-scope for R4-P0-1)

To avoid scope creep at V4 P0, R4-P0-1 explicitly does **NOT**:

- Define the underlying strict schema for `user.klickd`. That is
  P0-2.
- Define SDK APIs for writer / reader of `user.klickd`. That is P0-3
  (Python) and P0-4 (TypeScript).
- Define the cross-implementation vector set for `user.klickd`. That
  is P0-6.
- Bump any package version, mint any Git tag, cut any GitHub release,
  publish to npm / PyPI / Zenodo, or update any DOI.
- Replace, supersede, or weaken the §33.7 forward-compatibility
  contract or the §33.10 privacy invariants.
- Define `media.klickd`, `project.klickd`, `agent.klickd`,
  `gaming.klickd`, `core.klickd`, or any other domain profile.
  Those remain on their own RFC tracks (RFC-001, RFC-006, RFC-007,
  RFC-008) and **MUST NOT** be inserted into the `user.klickd`
  wizard's main path by R4-P0-1.
- Define the QR / deeplink onboarding trigger. That decision lives in
  [`V4-ONBOARDING-QR-DEEPLINK.md`](../ux/V4-ONBOARDING-QR-DEEPLINK.md)
  and remains P1 conditional → P2.
- Define the `KLICKD_E_*` error code i18n table. That is
  [R4-P0-2](../roadmap/ROAD-TO-V4-GA.md#r4-p0-2--messages-derreur-klickd_e_-i18n-orientés-utilisateur),
  which this document references but does not redefine.

---

## 6. Relationship to SPEC §33

This document is the **normative** counterpart to the R4-P0-1 item
tracked under [§2.4 of the V4 GA roadmap](../roadmap/ROAD-TO-V4-GA.md#r4-p0-1--wizard-userklickd-7-étapes-avec-rechargement-de-vérification).
The roadmap entry remains the planning artefact; this document is the
binding contract for any future v4 `user.klickd` writer.

[`SPEC.md` §33](../../SPEC.md#33--klickd-v4-preview-non-normative)
remains **preview / non-normative** for the on-the-wire field surface.
A future PR (P0-1 SPEC promotion proper) will lift the §33 field
surface into the normative SPEC body. R4-P0-1 (this document) is the
**UX onboarding contract** part of that wider P0-1 effort; it lands
first because it is independent of schema strictness (P0-2) and
SDK alignment (P0-3 / P0-4), and because the empirical UX research
([`V4-UX-DX-RESEARCH-NOTES.md`](../roadmap/V4-UX-DX-RESEARCH-NOTES.md))
shows it is the load-bearing piece that determines whether
non-developer adoption is possible at all.

When the §33 field surface is promoted into the normative SPEC body,
the cross-reference in §3.2 of this document **MUST** be updated to
point at the new normative SPEC section instead of §33.

---

## 7. Next recommended branch after R4-P0-1

Per the roadmap §2.4 and ["Suggested next branches" §3](../roadmap/ROAD-TO-V4-GA.md#3-suggested-next-branches),
the recommended next docs/spec branch after R4-P0-1 lands is
**R4-P0-2** — the `KLICKD_E_*` i18n error table — because R4-P0-1
already depends on it for step 4 (passphrase confirmation failure)
and step 6 (reload verification failure) error messaging. R4-P0-2 is
docs-only and unblocks the wizard's error contract without touching
SDK, schema, or vectors.
