# RFC-002 — `verification_gates` + `human_veto` (v1 → v2 draft)

| | |
|---|---|
| **RFC** | 002 |
| **Title** | `verification_gates` + `human_veto` — UX-first guardrails for agent actions |
| **Target** | `.klickd v4-A` (v1 core) · `.klickd v4-B` (v2 claim grounding & contracts) |
| **Status** | **Draft (v2)** |
| **Author** | Vince C. (Klickd / Luxlearn, Luxembourg) |
| **Created** | 2026-05-22 |
| **Revised** | 2026-05-22 (v2 draft: claim grounding + contract tests, additive) |
| **Supersedes** | — |

> **This RFC is non-normative.** It targets future `.klickd v4-A` and `v4-B` releases. No part of this document is binding on any current v3.x reader or writer. v3.x readers MUST ignore any `verification_gates`, `claim_sources`, `human_veto_policy`, `error_journal`, `risk_thresholds`, `preflight_checks`, `contract_tests`, `success_criteria`, `reversibility`, or `blast_radius` field they encounter — see [Forward compatibility](#forward-compatibility).
>
> **v2 additions are strictly additive over v1.** v2 introduces no new gate levels and no new UX surfaces. It refines *how* a gate decides — by grounding factual claims (`claim_status`, source provenance) and by attaching machine-checkable `contract_tests` and `success_criteria` to action classes — without changing the silent-by-default UX contract from v1 §4. A v4-A reader that does not understand v4-B fields MUST ignore them and behave exactly as the v1 resolution rules describe.

---

## 1. Motivation

`.klickd v3.x` lets a user carry **who they are** (identity, knowledge, personality, ethics) across agents. It does not yet let the user carry **when they want the agent to slow down**.

In practice, three failure modes recur across deployments:

1. **Silent overreach.** An agent acts on a fuzzy intent ("make me a video about X"), confidently produces a result, and the user discovers a hallucination, a wrong fact, or an embarrassing public artefact *after* publication.
2. **Compliance-form UX.** The reflex fix — "ask the user to confirm every action" — turns generative tools into legal-form fillers. Users disengage, click through, and the guard becomes noise.
3. **Loss of judgment across handoffs.** A user has learned "this agent should always double-check dates before posting to LinkedIn". The next agent does not know that, and the lesson is lost.

`verification_gates` v1 carries the user's **preferred friction profile** — when they want the agent to be silent, when to warn, when to stop and ask, when to refuse — and a small set of supporting fields that make those gates auditable and adjustable.

The design principle is **UX-first, invisible by default**:

- The agent interrupts the user **only on meaningful risk**.
- Confirmations, when they happen, are **one-click and short**, not multi-field forms.
- Defaults are **inherited** from the user's general profile; per-action overrides are the exception, not the rule.
- The format MUST NOT push agents toward compliance-form UX for ordinary creative work (e.g. casual media generation).

## 2. Scope

**In scope (v1):**

- A payload-level `verification_gates` object: a list of named gates, each binding an action class to a level.
- A `claim_sources` object: where the agent SHOULD ground factual claims (e.g. `prefer: ["user_supplied", "tool:web_search"]`).
- A `human_veto_policy` object: the user's standing rules about when a human MUST be in the loop, regardless of agent confidence.
- An append-only `error_journal[]`: lessons learned that should influence future gate evaluation (e.g. "the agent posted a wrong date on 2026-04-12 — always re-check dates for public posts").
- A `risk_thresholds` block: numeric / categorical knobs (e.g. `public_reach: "low|medium|high"`, `financial_amount_eur_max_silent: 0`).
- A `preflight_checks` list: small, named checks an agent SHOULD run *before* acting on certain classes (e.g. `date_freshness`, `recipient_identity`, `media_consent`).
- Five gate levels: `silent` · `warn` · `confirm` · `block` · `require-owner`.

**Out of scope (v1, deferred to v2+):**

- A normative DSL for matching an action to a gate (matching is reader-defined in v1; the format only carries declarative intent).
- Cryptographic attestation that a gate fired (covered by the existing `whitehat[]` log; integration sketched in §9, not normative).
- Cross-user / team veto policies (multi-recipient envelopes are an RFC-001 / v4 concern).
- Automatic learning of gates from `error_journal[]` — v1 is human-curated.

**Added in v2 (targets `.klickd v4-B`, still additive, still non-normative):**

- `claim_status` on every factual emission: `executed` (a tool actually ran and produced this), `inspected` (the agent read a source and is repeating it), or `assumed` (the agent inferred it without grounding).
- Extended `claim_sources` fields: `source_query`, `source_url`, `checked_at` — so a downstream reader (or auditor, or the user later) can re-run the check.
- `contract_tests`: a list of small, named, machine-checkable assertions bound to an action class. A `confirm` / `block` gate MAY reference a contract test instead of forcing the user to read prose.
- `success_criteria`: declarative statements of what "this action succeeded" means for a class — used by the agent to self-check before surfacing a result.
- `reversibility` and `blast_radius`: two coarse axes (`reversible | costly_to_reverse | irreversible`; `local | external_party | public`) that feed gate resolution without introducing new gate levels.
- `error_journal[].rule_created`: a structured pointer to the gate or contract test an entry caused to exist, so the journal is causally linked to the rule set instead of being free-text only.

## 3. Forward compatibility

This RFC targets `klickd_version: "4.0"` (shared envelope bump with RFC-001). Until v4 is normatively published in `SPEC.md`:

- v3.x **readers MUST IGNORE** `verification_gates`, `claim_sources`, `human_veto_policy`, `error_journal`, `risk_thresholds`, `preflight_checks`, `contract_tests`, `success_criteria`, `reversibility`, `blast_radius` if they appear in a v3.x payload.
- v3.x **writers MUST NOT emit** these fields.
- v4 **readers MUST be able to read v3.x files** by treating all of these fields as absent (not `null`, not `{}`).
- A v4-A reader that encounters a v4 file without `verification_gates` MUST behave as if a permissive default profile were present (see §5.1) — i.e. **absence MUST NOT trigger blocking behaviour**.
- A v4-A reader that encounters v4-B fields (`contract_tests`, `success_criteria`, `reversibility`, `blast_radius`, `claim_status`, extended `claim_sources.*` fields, `error_journal[].rule_created`) MUST ignore them and fall back to v1 gate resolution. Treating "I don't understand this v2 field" as a block is forbidden — silent ignore is the only conforming behaviour.

## 4. Decisions already resolved

The following decisions are taken and form the baseline of v1. They are listed here so reviewers can attack the **right** target.

1. **UX-first, invisible by default.** Agents MUST NOT interrupt the user for routine generative actions (a casual image, a draft email, a brainstorm). The gates carry *exceptions* to silence, not silence as the exception.
2. **Five levels, fixed enum.** `silent` · `warn` · `confirm` · `block` · `require-owner`. No `info`, no `soft-warn`, no per-channel variant. If the gate is between `silent` and `warn`, the producer picks one.
3. **One-click confirmations.** A `confirm`-level gate MUST be answerable with a single affirmative action (button, voice "yes", typed "y"). Producers MUST NOT require the user to fill a form to clear a `confirm` gate.
4. **Inheritance, not duplication.** Per-action overrides are sparse. The reader resolves a gate by: explicit override → action class default → user-level default → format-level default (`silent` for low-risk, `confirm` for irreversible).
5. **Block ≠ refuse forever.** `block` means "the agent stops and surfaces the reason to the user". The user MAY raise the gate to `require-owner` (a second-party check) or lower it to `confirm` for this session, with the change journaled.
6. **Human veto is sacred.** `human_veto_policy` overrides everything below `require-owner`. If a user has set `human_veto_policy.applies_to` to include "public_post", no level lower than `require-owner` may publish on their behalf — even if a per-action gate says `silent`. Conflicts resolve in favour of the stricter rule.
7. **Error journal is append-only.** Entries are time-stamped, opaque to non-owners, and the reader MUST NOT silently delete them. Removal requires a journaled "retraction" entry (mirrors `whitehat[]` semantics).
8. **No compliance-form UX.** Producers MUST NOT translate gates into multi-field legal disclaimers for routine media generation. A `confirm` gate's surface MUST be short: a sentence of *why*, a one-line *what*, and a single primary action.
9. **CC0 compatible.** Nothing in `verification_gates` requires proprietary risk taxonomies. The action class enum at v1 is a small, public list (§5.2); extensions live under `x_*`.
10. **Soul Handoff interaction.** §28.8 guaranteed-fields list is **not extended** in v1. An Agent B receiving a v4 file MAY surface gate summaries but is not required to.

## 5. Schema (illustrative — non-normative)

### 5.1 `verification_gates`

```json
{
  "verification_gates": {
    "version": 1,
    "user_default": "silent",
    "gates": [
      {
        "id": "public-post-default",
        "action_class": "public_post",
        "level": "confirm",
        "reason": "User wants a one-click check before anything goes to LinkedIn / X / blog."
      },
      {
        "id": "claim-public-figure",
        "action_class": "factual_claim_about_person",
        "level": "block",
        "reason": "Hallucinations about named people happened twice — see error_journal."
      },
      {
        "id": "financial-transfer",
        "action_class": "financial_action",
        "level": "require-owner",
        "reason": "No agent should move money without a human second-party check."
      },
      {
        "id": "casual-media",
        "action_class": "casual_media_generation",
        "level": "silent",
        "reason": "Image/video drafts are creative play. Do not interrupt."
      }
    ]
  }
}
```

### 5.2 Action class enum (closed at v1)

`casual_media_generation` · `factual_claim_about_person` · `factual_claim_with_date` · `public_post` · `external_message_send` · `financial_action` · `legal_action` · `medical_advice` · `code_execution_destructive` · `identity_assertion` · `consent_change`

Custom classes live under `x_<reverse-dns>` (e.g. `x_com_klickd_robot_actuation`).

### 5.3 `claim_sources`

```json
{
  "claim_sources": {
    "prefer": ["user_supplied", "tool:web_search", "tool:internal_kb"],
    "forbid": ["tool:unverified_scrape"],
    "require_citation_for": ["factual_claim_about_person", "factual_claim_with_date"]
  }
}
```

### 5.4 `human_veto_policy`

```json
{
  "human_veto_policy": {
    "applies_to": ["public_post", "financial_action", "legal_action"],
    "second_party": null,
    "min_level": "require-owner",
    "rationale": "These categories may not act without me explicitly approving."
  }
}
```

### 5.5 `error_journal[]`

```json
{
  "error_journal": [
    {
      "id": "ej-2026-04-12-01",
      "occurred_at": "2026-04-12T10:32:00Z",
      "action_class": "factual_claim_with_date",
      "summary": "Agent posted a release year of 2024 for a product released in 2023.",
      "lesson": "Always re-check public dates against at least one source before public_post.",
      "raised_gate": "claim-public-figure"
    }
  ]
}
```

### 5.6 `risk_thresholds`

```json
{
  "risk_thresholds": {
    "public_reach": "medium",
    "financial_amount_eur_max_silent": 0,
    "financial_amount_eur_max_confirm": 50,
    "irreversibility": "high_triggers_confirm"
  }
}
```

### 5.7 `preflight_checks`

```json
{
  "preflight_checks": [
    { "id": "date_freshness", "applies_to": ["factual_claim_with_date", "public_post"] },
    { "id": "recipient_identity", "applies_to": ["external_message_send"] },
    { "id": "media_consent", "applies_to": ["public_post"] }
  ]
}
```

## 6. Levels — normative intent

| Level | Agent behaviour | UX surface |
|---|---|---|
| `silent` | Act. No user-facing surface. Journal in the agent's own logs only. | None. |
| `warn` | Act, but surface a brief, dismissible note alongside the result ("FYI: I assumed the date 2024-Q3 — change?"). | Inline, one line, dismissible. |
| `confirm` | Stop before acting. Surface a one-sentence *why* + one-line *what* + a single primary action. | One-click yes/no. No form. |
| `block` | Stop. Do not act. Surface the reason and the lowest gate level the user could choose to proceed. | Modal-style stop; user decides whether to lower the gate for this session. |
| `require-owner` | Stop. The acting user is not the file owner OR a second-party check is required. Agent MUST NOT proceed without an out-of-band confirmation from the designated party. | Explicit handoff to the human owner / second party. |

Conflict resolution: when more than one gate matches an action, the **stricter** level wins (`silent < warn < confirm < block < require-owner`).

## 7. Media examples

The same gate framework works for the multimodal cases RFC-001 anticipates. Two illustrations:

### 7.1 Casual image generation — should NOT be a form

```json
{
  "id": "casual-media",
  "action_class": "casual_media_generation",
  "level": "silent"
}
```

User: *"make me three album-cover ideas for my band rehearsal photo"*. Agent generates. No consent dialog, no compliance form. This is the default that protects the experience.

### 7.2 Generated likeness of a named person — gate fires

```json
{
  "id": "likeness-named-person",
  "action_class": "factual_claim_about_person",
  "level": "block",
  "reason": "Any image, video or voice that *names or is recognisable as* a real person stops here."
}
```

Combined with RFC-001's `media_profile.consent.purposes`, the agent has two independent reasons to stop: the gate, and the per-entry consent.

### 7.3 Voice cloning for the user themselves — confirm, not block

```json
{
  "id": "self-voice-clone",
  "action_class": "identity_assertion",
  "level": "confirm",
  "reason": "I'm okay with you cloning my voice from the sample in media_profile, but ask me each session."
}
```

## 8. BagHolderAI mapping

`.klickd v4-A` is partly motivated by the BagHolderAI persona — a satirical, opinionated agent that comments on markets — where the cost of a *confident wrong* claim is much higher than the cost of an extra check.

Suggested gate set for a BagHolderAI deployment (illustrative):

| Action | Gate | Level | Notes |
|---|---|---|---|
| Generate a meme / cover image | `casual-media` | `silent` | Don't break the comedy with forms. |
| Quote a real ticker price | `factual_claim_with_date` | `confirm` | One-click: "use last close 2026-05-21?" |
| Name a public CEO and attribute a quote | `factual_claim_about_person` | `block` | Refuse unless `claim_sources` has a citation. |
| Auto-post to social | `public_post` | `require-owner` | The human ships the bag, not the agent. |
| Suggest a trade | `financial_action` | `block` | Disclaim, do not act. |

This maps cleanly onto the existing `ethics.locked_actions` discipline: gates handle the *softer* "I want to choose" cases; `ethics.locked_actions` handles the *hard* "never under any circumstances" cases. `verification_gates` MUST NOT be used to weaken `ethics.locked_actions`.

## 8b. v2 additions — claim grounding & contract tests (targets v4-B, non-normative)

v2 sharpens *how* a gate decides without changing *what* the user sees. The v1 UX contract (silent by default, one-click confirm, no compliance-form UX) is preserved verbatim. v2 only adds:

1. **Claim grounding** — every factual emission carries a `claim_status` and (when applicable) provenance fields, so the agent can self-check *before* a gate fires rather than relying on the user to catch hallucinations after the fact.
2. **Contract tests** — small, named, machine-checkable assertions attached to an action class. A gate set to `confirm` MAY auto-resolve when all bound contracts pass, collapsing what would have been a user-facing prompt into a silent green light.
3. **Reversibility / blast radius** — two coarse axes that feed v1's stricter-wins resolver without expanding the level enum.

These together close the most common failure mode left open by v1: the agent thinks it "checked" something but in fact only *believed* something.

### 8b.1 `claim_status` (per factual emission)

Every factual statement an agent makes in a gated action class SHOULD be tagged:

| Value | Meaning | Typical use |
|---|---|---|
| `executed` | A tool actually ran and produced this value (e.g. `tool:web_search` returned a page, `tool:pypi` returned a version). | Live version numbers, balances, current prices. |
| `inspected` | The agent read a source and is repeating its claim verbatim (no transformation). | Quoting a known doc. |
| `assumed` | The agent inferred this without grounding (training data, plausible guess, interpolation). | Anything not backed by an active source. |

A gate MAY refuse to fire `silent` if the claim status is `assumed` for an action class listed in `claim_sources.require_citation_for`. This is the v2 way to say "do not let a guess slip through silently" without forcing the user to confirm every routine action.

### 8b.2 Extended `claim_sources.*` fields

v1 `claim_sources` declared *preferences* (which sources are OK). v2 adds *records* of what was actually used:

```json
{
  "claim_sources": {
    "prefer": ["tool:pypi", "tool:zenodo", "tool:web_search"],
    "forbid": ["tool:unverified_scrape"],
    "require_citation_for": ["factual_claim_about_person", "factual_claim_with_date"],
    "records": [
      {
        "id": "src-2026-05-22-01",
        "source": "tool:pypi",
        "source_query": "klickd",
        "source_url": "https://pypi.org/pypi/klickd/json",
        "checked_at": "2026-05-22T09:14:02Z",
        "claim_status": "executed",
        "summary": "Latest published version is 3.5.1."
      }
    ]
  }
}
```

`source_query`, `source_url`, `checked_at` are non-normative recommendations: producers MAY omit any of them when the source has no meaningful URL or query (e.g. a local file). What matters is that *something* lets a downstream auditor re-run the check.

### 8b.3 `contract_tests`

A contract test is a named, declarative assertion bound to an action class. Producers MUST NOT smuggle code through this field; v2 only carries names and parameters. Resolution of test names to actual checks is a reader concern (SDK plugins, project-specific test runners).

```json
{
  "contract_tests": [
    {
      "id": "pypi-version-fresh",
      "applies_to": ["public_post", "factual_claim_with_date"],
      "kind": "freshness",
      "params": { "max_age_hours": 24, "source": "tool:pypi", "package": "klickd" }
    },
    {
      "id": "zenodo-doi-resolves",
      "applies_to": ["factual_claim_with_date", "public_post"],
      "kind": "resolves",
      "params": { "source": "tool:zenodo", "doi": "10.5281/zenodo.0000000" }
    },
    {
      "id": "media-likeness-consent",
      "applies_to": ["public_post", "casual_media_generation"],
      "kind": "consent_present",
      "params": { "subject": "named_person", "media_profile_ref": "self" }
    }
  ]
}
```

**Gate interaction.** If every contract test bound to an action class passes, the resolved gate level MAY be *lowered by one step* (e.g. `confirm` → `silent`). It MUST NOT be lowered past a `human_veto_policy` floor. If any bound test fails, the resolved level is raised by one step (capped at `block` — never auto-escalate to `require-owner`). This is the only mechanism in v2 that changes a gate's effective level, and it is bounded.

### 8b.4 `success_criteria`

Declarative statements of what "succeeded" means for an action class. Used by the agent for self-check before surfacing a result, and by `whitehat[]` audits for post-hoc verification.

```json
{
  "success_criteria": [
    {
      "action_class": "public_post",
      "criteria": [
        "All factual_claim_with_date items have claim_status in ['executed', 'inspected']",
        "No named person appears without a matching media_profile.consent entry",
        "Every bound contract_test passes"
      ]
    }
  ]
}
```

### 8b.5 `reversibility` and `blast_radius`

Two coarse axes that feed gate resolution. They MUST NOT introduce new gate levels — they only inform the *match* between an action and a gate.

```json
{
  "reversibility": {
    "default": "reversible",
    "by_action_class": {
      "public_post": "costly_to_reverse",
      "financial_action": "irreversible",
      "consent_change": "costly_to_reverse"
    }
  },
  "blast_radius": {
    "default": "local",
    "by_action_class": {
      "public_post": "public",
      "external_message_send": "external_party",
      "financial_action": "external_party"
    }
  }
}
```

Reader hint: an action whose resolved `(reversibility, blast_radius)` is `(irreversible, public)` SHOULD never be `silent` even if the contract tests pass. This is the one place v2 sets a floor.

### 8b.6 `error_journal[].rule_created`

v1's journal carries human-readable lessons. v2 lets each entry point to the rule it actually caused to exist:

```json
{
  "error_journal": [
    {
      "id": "ej-2026-04-12-01",
      "occurred_at": "2026-04-12T10:32:00Z",
      "action_class": "factual_claim_with_date",
      "summary": "Agent posted release year 2024 for a product released in 2023.",
      "lesson": "Always re-check public dates against at least one source before public_post.",
      "raised_gate": "claim-public-figure",
      "rule_created": {
        "kind": "contract_test",
        "id": "pypi-version-fresh"
      }
    }
  ]
}
```

`rule_created.kind` is one of `gate`, `contract_test`, `preflight_check`, `success_criterion`. This makes the journal causally linked to the rule set: if a rule is removed, journal entries that point at it become orphaned and surface in audit.

### 8b.7 Worked examples — PyPI, Zenodo, media

These illustrate v2 end-to-end without changing any v1 UX.

- **PyPI version claim in a public post.** Agent wants to say "klickd 3.5.1 is the latest release." Action class: `factual_claim_with_date` + `public_post`. Bound contract test: `pypi-version-fresh`. Agent runs `tool:pypi`, gets `3.5.1`, records `claim_status: executed`, `source_url: https://pypi.org/pypi/klickd/json`, `checked_at: 2026-05-22T09:14:02Z`. Contract test passes. Per §8b.3, the `confirm` gate lowers to `silent`. The user is not interrupted.
- **Zenodo DOI in a citation.** Agent wants to cite a DOI. Bound contract test: `zenodo-doi-resolves`. If the DOI does not resolve, `claim_status` stays `assumed`, the test fails, and the gate auto-raises one step (`confirm` → `block`). The user sees a stop with a specific reason, not a generic "are you sure?".
- **Media likeness with consent.** RFC-001's `media_profile` carries consent. v2's `media-likeness-consent` contract test reads that profile. If consent is present, the `block` on `factual_claim_about_person` may lower for the named-self case but not for third parties (the `(irreversible-ish, public)` floor from §8b.5 prevents collapse to `silent`).

### 8b.8 What v2 explicitly does NOT add

- **No new gate levels.** The enum stays at five.
- **No new user-facing UX.** v2 either lowers a `confirm` to `silent` (good — user sees less) or raises it to `block` (which already exists in v1).
- **No mandatory tooling.** Every v2 field is OPTIONAL. A producer that emits only v1 fields is fully conforming.
- **No normative test runner.** `contract_tests[].kind` is a name; resolving it is a reader / SDK concern.

## 9. Implementation ticket outline

This RFC does not require any change to v3.x SDKs. Tickets that would land alongside a future v4-A normative section in `SPEC.md`:

1. **klickd-py:** add `verification_gates` / `claim_sources` / `human_veto_policy` / `error_journal` / `risk_thresholds` / `preflight_checks` as round-tripping payload fields (preserve `x_*` verbatim per V-010 of RFC-001).
2. **@klickd/core:** mirror the above; expose a `resolveGate(actionClass, context)` helper returning the resolved level + the gate that won.
3. **schemas/payload.schema.json:** add the six fields as `additionalProperties: true` placeholders in v3.x (no validation), full schema in v4.
4. **whitehat integration:** when a gate at `confirm` / `block` / `require-owner` fires, append a `whitehat[]` entry of kind `audit` with `subject: "gate:<id>"`.
5. **error_journal entry helper:** SDK helper that appends an `error_journal` entry and (optionally) raises a named gate.
6. **Conformance tests (v4-A):**
   - G-001 — Stricter-wins resolution.
   - G-002 — `human_veto_policy` overrides any lower gate.
   - G-003 — `confirm` surface MUST be answerable with a single affirmative action (UX contract test, SDK-level).
   - G-004 — `error_journal[]` is append-only; deletion requires a retraction entry.
   - G-005 — Unknown `x_*` action classes preserved round-trip.
   - G-006 — Absence of `verification_gates` MUST NOT block (default permissive — §3).
7. **v4-B additions (additive over v4-A):**
   - klickd-py and `@klickd/core`: round-trip `contract_tests`, `success_criteria`, `reversibility`, `blast_radius`, `claim_sources.records[]`, `error_journal[].rule_created` verbatim. No validation in v4-A.
   - SDK helper `resolveGateV2(actionClass, context, contractResults)` that applies the §8b.3 ±1 lowering / raising rule and the §8b.5 floor.
   - Conformance tests:
     - G-101 — v4-A reader silently ignores all v4-B fields and resolves gates per v1.
     - G-102 — When all bound contract tests pass, a `confirm` gate lowers to `silent`, never past a `human_veto_policy` floor.
     - G-103 — When any bound contract test fails, the gate raises by one step, capped at `block` (never auto-`require-owner`).
     - G-104 — `(irreversible, public)` actions never resolve to `silent` regardless of contract outcomes.
     - G-105 — `error_journal[].rule_created` referencing a removed rule surfaces in audit.

## 10. Open questions

Even with §4 decided, the following remain genuinely open:

1. **Action-class matching DSL.** Should v4-A ship a normative matcher (e.g. a small expression language), or stay declarative-only and let SDKs match? Current draft: declarative-only, revisit if SDK divergence emerges.
2. **Second-party identification.** `human_veto_policy.second_party` is `null` in the v1 example. Do we point at a `companion_identity` entry, a public key, or a free-form contact? Likely: a stable id pointing into the existing identity section, but open.
3. **Should `error_journal[]` be encrypted at a finer granularity than the envelope?** Probably no in v1 — it inherits envelope confidentiality — but worth revisiting if the journal grows or is shared selectively.
4. **Interaction with §29c Privacy Guards.** A gate firing on `factual_claim_about_person` and re-identification rules in §29c overlap. v1 says: gates fire first, §29c is the floor. Confirm with reviewers.
5. **Should `preflight_checks` be normative names or producer-defined?** Current draft: small closed enum in v1 (`date_freshness`, `recipient_identity`, `media_consent`), `x_*` for the rest. To revisit.
6. **Telemetry of "silent" gates.** A gate at `silent` still records *that the agent reasoned about it*. Should this be visible to the user on demand? Likely yes via a "show me what you almost interrupted me about" affordance — open for v2.

## 11. Examples

Non-normative example files:

- v1 core: [`examples/verification_gates-v1.example.json`](./examples/verification_gates-v1.example.json)
- v2 draft (claim grounding + contract tests, PyPI / Zenodo / media): [`examples/verification_gates-v2.example.json`](./examples/verification_gates-v2.example.json)
