# `core.klickd` for organisations — B2B / developer use-case

| | |
|---|---|
| **Status** | **Draft · NON-NORMATIVE · concept doc** |
| **Track** | `.klickd v4+` — future RFC / extension (not P0 GA) |
| **Author** | Vince C. (Klickd / Luxlearn, Luxembourg) |
| **Created** | 2026-05-23 |
| **Audience** | B2B prospects, integrators, developers exploring `.klickd` for org-level agent context |
| **Relates to** | [`docs/roadmap/ROAD-TO-V4-GA.md`](../roadmap/ROAD-TO-V4-GA.md) §2.3 P2 · [`docs/rfcs/README.md`](../rfcs/README.md) |

> **This document is non-normative and aspirational.** It formalises a use-case
> pattern. It does **not** describe a shipping product. No runtime builder, no
> SaaS, no hosted service, no npm / PyPI / Zenodo publication is implied. The
> only artefact this PR ships is *this document*.
>
> The production-recommended version of `.klickd` remains **v3.5.1**. The
> preview track is **v4.0.0-preview.1**. The B2B `core.klickd` pattern below
> would be promoted to an RFC and a normative spec section only after the v4
> GA gates listed in [`ROAD-TO-V4-GA.md`](../roadmap/ROAD-TO-V4-GA.md) are met.

---

## 1. The pattern in one paragraph

A `.klickd` file today is, in practice, a **portable memory of a person** —
their preferences, their style, their ethical guardrails. The same envelope can
also carry a **portable operating context for an organisation or an agent**:
not who *the user* is, but *how this agent is allowed to think, talk, decide,
and escalate, on behalf of this organisation*. We call that second use the
`core.klickd` pattern. It is a deliberate separation of two concerns that
agentic apps tend to silently fuse:

| Concept | What it carries | Who owns it | Travels with |
|---|---|---|---|
| **`user.klickd`** | Private memory of an end-user / client (preferences, history, soul). | The user. | The user, across agents and devices. |
| **`core.klickd`** | Operating context of an organisation / agent role (rules, workflow, tone, gates, evidence policy, escalation). | The organisation. | The deployment, across users and sessions. |

`user.klickd` and `core.klickd` are two `.klickd` files. Same format, same
envelope, same cryptography — different intent. They compose at runtime:
`core.klickd` defines the contract the agent operates under; `user.klickd`
supplies the user's soul; the agent is the merge point. Neither file is
authoritative for the other's content.

> Configure your agent's operating context once. Run it anywhere.
> Bring your rules, not your client data.

## 2. Vocabulary

The pattern reuses existing `.klickd` mechanics. Names below are conceptual,
not schema-bound; the actual field placement would be the subject of a future
RFC (see §8).

- **`user.klickd`** — a `.klickd` file authored by, and belonging to, an
  end-user. This is the existing, normative use of the format.
- **`core.klickd`** — a `.klickd` file authored by, and belonging to, an
  *organisation* or *agent owner*. Same envelope, same crypto, distinct intent
  declared in metadata.
- **`domain.klickd` / `profile`** — the substantive payload of a `core.klickd`:
  the **business rules, workflows, compliance constraints, tool policy, tone,
  evidence rules, and human-approval gates** that define how the agent
  operates inside that domain.
- **Operating context** — the runtime composition of `core.klickd` + the
  current `user.klickd` (if any) + the agent runtime. The composition rule is
  intentionally simple: `core.klickd` constrains; `user.klickd` personalises;
  neither replaces the other.

### 2.1 Hard rule — no client data in the core

> **A `core.klickd` MUST NOT contain client PII, customer transcripts, case
> data, patient data, tickets, or any user-specific memory.**

The whole point of the separation is that a `core.klickd` is *portable,
inspectable, and shareable across an organisation* — including with auditors,
new hires, integrators, and clients. If client data leaks into the core, the
core becomes radioactive: it cannot be inspected, cannot be versioned in a
shared repo, cannot be shipped to a new deployment. Keep client data in
`user.klickd` (or in the agent's normal data plane). Keep rules in
`core.klickd`. The boundary is the product.

## 3. Worked examples

The five examples below are illustrative. They sketch the *shape* of a
`core.klickd` per domain, not a normative schema. Each example highlights what
**must be present** (rules, gates, tone, evidence policy) and what **must
never be present** (client data).

### 3.1 Law firm — `core.klickd` for a legal practice

- **Rules.** Approved clause library reference (by ID, not by content);
  jurisdiction scope (e.g. LU / FR / EU); allowed/forbidden practice areas;
  conflict-of-interest checks before drafting.
- **Tone & style.** House drafting style; mandatory disclaimers; formality
  register per document type.
- **Evidence rules.** Every legal assertion MUST cite a source (statute, case,
  internal memo ID); no claim without a citation slot filled.
- **Approval gates.** No outgoing legal advice without a named lawyer's
  validation. A `verification_gate` (RFC-002 shape) blocks any agent reply
  classified as `legal_advice` until human sign-off.
- **Tool policy.** Allowed tools: case-law search, internal KB, redline diff.
  Forbidden: any tool that auto-sends to a client.
- **Never in core.** Client names, matter numbers, transcripts, drafts.

### 3.2 Dev team — `core.klickd` for an engineering org

- **Rules.** Coding standards reference, repo conventions, branch / PR
  policy, license allow-list, dependency policy.
- **Tone & style.** Commit message convention, PR description template,
  review tone.
- **Evidence rules.** Performance / security claims must link a benchmark
  or test artefact.
- **Approval gates.** CI must be green before merge; release tags require a
  named approver; force-push to protected branches blocked.
- **Tool policy.** Allowed tools: repo, CI, package registry read. Forbidden:
  direct production deploys without a release ticket.
- **Never in core.** Source code, secrets, customer issue text, internal
  incident transcripts.

### 3.3 Customer support — `core.klickd` for a support org

- **Rules.** Refund policy thresholds, escalation matrix, SLA tiers,
  knowledge-base pointers (IDs, not content).
- **Tone & style.** House voice, empathy register, banned phrases, language
  per region.
- **Evidence rules.** Every promise (refund, replacement, exception) must
  reference a policy ID.
- **Approval gates.** Refunds above threshold require a named supervisor;
  any compensation outside policy goes to a human.
- **Tool policy.** Allowed: ticketing read/write within scope, KB read.
  Forbidden: direct billing system writes.
- **Never in core.** Tickets, customer names, transcripts, account IDs.

### 3.4 Finance — `core.klickd` for a finance / advisory team

- **Rules.** Allowed instrument universe, source requirements for any
  number (price, ratio, projection), risk-disclaimer requirement on any
  forward-looking statement, regulator-aligned wording.
- **Tone & style.** Formal, hedged, non-advice register for non-licensed
  agent outputs.
- **Evidence rules.** Every figure MUST carry a source (provider, timestamp,
  identifier). No naked numbers.
- **Approval gates.** Any recommendation, allocation suggestion, or
  forward-looking projection requires a licensed human approval.
- **Tool policy.** Allowed: market-data read, internal research KB.
  Forbidden: trade execution, account writes.
- **Never in core.** Client portfolios, balances, identities.

### 3.5 Healthcare — `core.klickd` for a clinical / health-adjacent team

- **Rules.** Safety escalation triggers (red flags → human now), scope
  limitation (no diagnosis, no prescription), clinician oversight contract.
- **Tone & style.** Patient-safe register, plain language, accessibility
  rules.
- **Evidence rules.** Any clinical claim must cite a guideline or internal
  protocol ID; non-cited claims are blocked.
- **Approval gates.** A clinician MUST review any output classified as
  clinical guidance before it reaches a patient.
- **Tool policy.** Allowed: protocol KB read, triage workflow. Forbidden:
  prescription tools, EHR writes.
- **Never in core.** Patient data, identifiers, transcripts, images.

## 4. The B2B / developer narrative

The five examples above share a single value proposition. We state it here in
the form a B2B / developer landing page would use — keeping the document
honest about what is shipped today (the pattern) vs. what is future work
(tooling, builder, viewer).

- **Configure your agent's operating context once. Run it anywhere.** A
  `core.klickd` is a file. It travels with the deployment, not with the
  vendor. You can ship the same operating context to your own runtime, to a
  partner's runtime, to a future model, without re-explaining your rules.
- **Bring your rules, not your client data.** The boundary between
  `core.klickd` (org rules) and `user.klickd` (user soul) is the product. It
  keeps the core inspectable and shareable, and keeps client data inside the
  customer's perimeter.
- **Versioned.** Same envelope as a personal `.klickd`. The org can keep
  `core.klickd` in a private repo, branch it, diff it, review it, roll it
  back. Rule changes are commits.
- **Signed.** The same cryptographic envelope that protects a personal
  `.klickd` protects a `core.klickd`: integrity, authenticity, optional
  encryption at rest. A consumer of the core can verify it came from the
  organisation it claims to come from.
- **Portable.** No vendor lock-in. The format is open. Any compliant
  reader/writer can consume an org's `core.klickd`.
- **Inspectable.** Auditors, new hires, integrators, and — when the org
  chooses — clients themselves can read the operating context the agent
  runs under. No black-box prompt. No hidden system message.

Plain reading: **you bring your contract; the agent honours it; the runtime
proves it.** No `core.klickd`, no contract.

## 5. Composition with `user.klickd`

At runtime the two files compose, they do not merge. A reference composition
rule (subject to RFC):

1. **Load `core.klickd`** — apply rules, gates, tool policy, tone. These are
   *constraints* on the agent's behaviour for this deployment.
2. **Load `user.klickd`** (if present) — apply user soul (preferences,
   personality, memory). These are *personalisation* inputs.
3. **Conflict rule.** When `core.klickd` and `user.klickd` disagree, **the
   core wins on safety-relevant fields** (gates, forbidden tools, evidence
   requirements, escalation). The user wins on personalisation (tone within
   the org's allowed range, language preference, format preferences).
4. **No write-back.** The agent MUST NOT modify the core at runtime. It MUST
   NOT write client-derived content into the core. Updates to the core are
   an org-side, versioned, reviewed action — the same as a code change.
5. **Audit.** Every gate firing, every refusal, every escalation references
   the `core.klickd` version (hash + version field) it was decided against.

## 6. What `core.klickd` is *not*

To avoid the usual category confusions:

- **Not a system prompt.** A system prompt is one string per model call. A
  `core.klickd` is a versioned artefact with structured sections (rules,
  gates, evidence, tone, tool policy). A runtime *may* compile parts of it
  into a system prompt — that is an implementation detail.
- **Not a knowledge base.** The core points *at* KB IDs; it does not embed
  the KB. KB content lives in the customer's data plane.
- **Not a memory.** A core does not learn from sessions. It changes only by
  explicit org action.
- **Not a policy engine.** The core *expresses* policy in a portable shape;
  the runtime is responsible for enforcing it. A runtime that ignores the
  core is non-compliant, not the core's fault.
- **Not a substitute for legal / clinical / financial professional
  oversight.** The whole point of approval gates is that the core *requires*
  named human accountability for the calls a non-licensed agent must not
  make alone.

## 7. Risks & failure modes

The pattern is only useful if its risks are stated honestly. The list below
is deliberately conservative; future RFC work should expand it with mitigations.

1. **Governance drift.** Without a clear owner per `core.klickd`, rules
   stagnate or fork. *Mitigation (future RFC):* a `governance` section with
   named owner, last-review date, review cadence.
2. **Liability misalignment.** A core that says "agent may give legal
   advice" creates liability for the org regardless of disclaimers.
   *Mitigation:* approval-gate primitives are first-class; absence of a gate
   on a sensitive operation is a lint warning, not silence.
3. **Stale rules.** A core that is six months out of compliance is worse
   than no core (false sense of safety). *Mitigation:* explicit
   `valid_until` / `last_reviewed` metadata; runtime warns when expired.
4. **Licensing of embedded references.** A core that embeds clauses,
   guidelines, or KB excerpts may inherit third-party licensing constraints.
   *Mitigation:* reference by ID, not by content; keep the core a
   *pointer-graph*, not a content store.
5. **Overclaim in marketing.** "Signed, portable, inspectable" must not
   become "certified, audited, regulator-approved." *Mitigation:* keep the
   B2B narrative scoped to format properties, not regulatory claims.
6. **Secrets in core.** A core is shareable — that is the value. Anything
   that should not be shareable (API keys, internal endpoints, customer
   identifiers) does not belong in it. *Mitigation (future RFC):* a lint
   rule that rejects any field matching a secrets shape; encryption at rest
   does not justify storing secrets in a portable artefact.
7. **Prompt injection through the core itself.** A maliciously crafted core
   could attempt to subvert the runtime (e.g. instructing the agent to
   ignore gates). *Mitigation:* the runtime treats the core as *data*, not
   as instructions; structured fields, not free text; verification of the
   signing identity before load.
8. **Client-data contamination.** A team accidentally pastes a transcript
   into the core to "illustrate a case". The core leaves the perimeter.
   *Mitigation:* §2.1 hard rule, plus a future-RFC lint that flags
   free-text fields exceeding a threshold or matching PII patterns.
9. **False portability.** A core that depends on vendor-specific tool names
   is not actually portable. *Mitigation:* tool policy expressed as
   *capabilities* (e.g. "may read internal KB") and resolved per runtime.
10. **Inspectability used against the org.** A fully public core gives
    competitors a complete operating playbook. *Mitigation:* the format
    supports encryption; inspectability is a *capability*, not a default
    posture. The org chooses who can read.

## 8. Relationship to the v4 roadmap

This document **does not change** the v4 GA scope. The current P0 items in
[`ROAD-TO-V4-GA.md`](../roadmap/ROAD-TO-V4-GA.md) (normative SPEC, strict
schemas, SDKs, migrator, vectors) remain the bar for `v4.0.0`. The B2B
`core.klickd` pattern is positioned as a **future RFC / extension** in the
P2 tier, alongside `P2-6 — Domain schemas formels` which already
anticipates `legal`, `finance`, etc.

Concretely, the promotion path would be:

1. **This doc** (here): captures the use-case and vocabulary so future
   conversations have a shared reference.
2. **Future RFC** (post-v4-GA): a normative RFC defining
   - the `core_klickd` declaration field (or a distinct `intent: "core"`
     envelope marker),
   - the `domain.klickd` / `profile` section shape,
   - the composition rule with `user.klickd`,
   - the lint rules (no PII, no secrets, no client data).
3. **Domain schemas** (RFC follow-ups): per-domain shapes derived from the
   P2-6 placeholder (`legal`, `finance`, `healthcare`, `support`,
   `engineering`).
4. **SDK / tooling**: only after the RFC lands; this document does not
   imply a builder, viewer, or SaaS.

Until those steps happen, **implementors MUST NOT rely on this document**.
It is a use-case formalisation, not a contract.

## 9. Open questions

- Should `core.klickd` be a distinct file type (different MIME), a flag in
  the envelope, or a structural pattern with no format-level marker?
- Should the composition rule (`core` constrains, `user` personalises) be
  normative or left to the runtime, with the format only providing the
  building blocks?
- How does the signature model handle org-level keys vs. user-level keys
  without confusing the two?
- What is the minimum lint surface that prevents the most common foot-guns
  (PII paste, secret paste, stale `valid_until`) without becoming a full
  policy engine?
- How does a `core.klickd` interact with RFC-001 media and RFC-002 gates —
  is the gate set in the core authoritative over a gate set in the user
  file? (Current expectation: yes, on safety-relevant gates.)

These questions are explicitly **out of scope** for this document. They are
the agenda for the future RFC.

---

*Document vivant. Toute modification passe par une PR. This is a concept
note, not a specification.*
