# RFC-002 — `verification_gates` + `human_veto` v1

| | |
|---|---|
| **RFC** | 002 |
| **Title** | `verification_gates` + `human_veto` v1 — UX-first guardrails for agent actions |
| **Target** | `.klickd v4-A` (payload extension, additive) |
| **Status** | **Draft** |
| **Author** | Vince C. (Klickd / Luxlearn, Luxembourg) |
| **Created** | 2026-05-22 |
| **Supersedes** | — |

> **This RFC is non-normative.** It targets a future `.klickd v4-A` release. No part of this document is binding on any current v3.x reader or writer. v3.x readers MUST ignore any `verification_gates`, `claim_sources`, `human_veto_policy`, `error_journal`, `risk_thresholds`, or `preflight_checks` field they encounter — see [Forward compatibility](#forward-compatibility).

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

## 3. Forward compatibility

This RFC targets `klickd_version: "4.0"` (shared envelope bump with RFC-001). Until v4 is normatively published in `SPEC.md`:

- v3.x **readers MUST IGNORE** `verification_gates`, `claim_sources`, `human_veto_policy`, `error_journal`, `risk_thresholds`, `preflight_checks` if they appear in a v3.x payload.
- v3.x **writers MUST NOT emit** these fields.
- v4 **readers MUST be able to read v3.x files** by treating all six fields as absent (not `null`, not `{}`).
- A v4-A reader that encounters a v4 file without `verification_gates` MUST behave as if a permissive default profile were present (see §5.1) — i.e. **absence MUST NOT trigger blocking behaviour**.

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

## 10. Open questions

Even with §4 decided, the following remain genuinely open:

1. **Action-class matching DSL.** Should v4-A ship a normative matcher (e.g. a small expression language), or stay declarative-only and let SDKs match? Current draft: declarative-only, revisit if SDK divergence emerges.
2. **Second-party identification.** `human_veto_policy.second_party` is `null` in the v1 example. Do we point at a `companion_identity` entry, a public key, or a free-form contact? Likely: a stable id pointing into the existing identity section, but open.
3. **Should `error_journal[]` be encrypted at a finer granularity than the envelope?** Probably no in v1 — it inherits envelope confidentiality — but worth revisiting if the journal grows or is shared selectively.
4. **Interaction with §29c Privacy Guards.** A gate firing on `factual_claim_about_person` and re-identification rules in §29c overlap. v1 says: gates fire first, §29c is the floor. Confirm with reviewers.
5. **Should `preflight_checks` be normative names or producer-defined?** Current draft: small closed enum in v1 (`date_freshness`, `recipient_identity`, `media_consent`), `x_*` for the rest. To revisit.
6. **Telemetry of "silent" gates.** A gate at `silent` still records *that the agent reasoned about it*. Should this be visible to the user on demand? Likely yes via a "show me what you almost interrupted me about" affordance — open for v2.

## 11. Examples

A non-normative example file lives at [`examples/verification_gates-v1.example.json`](./examples/verification_gates-v1.example.json).
