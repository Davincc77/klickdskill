# RFC-006 — `agent_core` / Agent Operating Context

| | |
|---|---|
| **RFC** | 006 |
| **Title** | `agent_core` — versioned, portable, PII-free operating context for first-party agents (e.g. Kai) |
| **Target** | `.klickd v4+` (post-preview; future RFC track, NOT part of `v4.0.0` GA P0) |
| **Status** | **Draft** |
| **Author** | Vince C. (Klickd / Luxlearn, Luxembourg) |
| **Created** | 2026-05-23 |
| **Supersedes** | — |
| **Relates to** | RFC-001 (`media_profile`), RFC-002 (`verification_gates`, `human_veto_policy`), RFC-003 (Context Cost Benchmark), RFC-004 (Migration), SPEC §25.2 (`companion_identity`), SPEC §33.4 #9 (state vs operating rules) |

> **This RFC is non-normative.** It describes a *future* track on top of `.klickd v4`. It does **not** bind any current SDK, schema, reader or writer, and is **not** in scope for the `v4.0.0` GA P0 backlog defined in [`docs/roadmap/ROAD-TO-V4-GA.md`](../roadmap/ROAD-TO-V4-GA.md). v3.x and v4-preview readers MUST IGNORE every field listed below if they encounter it. v4 readers that do not understand `agent_core` MUST preserve it verbatim on round-trip (SPEC §33.7).

---

## 1. Motivation

`.klickd` today carries a single class of payload: a **user-owned profile** describing who the user is, what they know, what they want, what they consent to. This is the right primitive for a *learner* profile (the default `profile_kind` in SPEC §33.3). It is also the right primitive for any human end user reading the file with their own passphrase.

But two real use cases push against this single-class shape:

1. **A first-party agent has its *own* operating context.** Kai (Klickd's reference learning companion) is not "the user" — Kai is an agent with a curriculum, a pedagogical posture, a tool policy, a safety policy, and a language baseline. None of this is the user's memory; all of it shapes how Kai talks to *every* user. Today this context lives implicitly in system prompts, scattered configuration, or model-side fine-tuning. None of these are portable across providers, none are versioned in a way a third party can audit, and none separate cleanly from user PII.
2. **Showcase / first-party demonstration of the format.** `.klickd` already claims to be a portable, model-agnostic context format. The most credible demonstration of that claim is to publish a non-user `.klickd` file that an agent *itself* uses as its operating context — `core.Kai.klickd` — and show that swapping providers preserves the agent's behaviour the same way swapping providers preserves a user profile today.

`agent_core` is the field that turns this implicit operating context into a first-class, versioned, auditable, PII-free payload section. The companion file `core.Kai.klickd` is the first-party showcase: a real, shipped `.klickd` file that carries Kai's operating context and nothing else.

The principle, which carries forward from RFC-004 and SPEC §33.4 #9:

> **A `.klickd` file is either a user profile *or* an agent core. Never both. Never mixed.**

## 2. Scope

**In scope (v1 of this RFC):**

- A payload-level `agent_core` object carrying an agent's operating context: identity, language, pedagogy, curriculum references, rule set, tool policy, safety policy, and version metadata.
- A normative invariant: an `agent_core` file MUST NOT contain user PII, user memory, user sessions, user `whitehat[]`, user `consent_*` blocks, or any other user-owned section. (See §6.)
- A `profile_kind: "agent"` discriminator value (already reserved in SPEC §33.3 as an example) that signals the file is an agent core and not a learner profile.
- Versioning rules so an agent can ship `core.<AgentName>.klickd` v1, v2, … and a host reader can pin or migrate.
- An **injection slice** contract: how a host SHOULD assemble an effective context window from a user profile + an agent core, without conflating their provenance.
- A `provenance` block at the `agent_core` level: who published this core, when, what signature (if any), against which spec/RFC revision.
- Relation rules with RFC-002 (`verification_gates`, `human_veto_policy`): an agent core MAY carry **default** gates, but a user profile's gates MUST take precedence on conflict (user veto > agent default).
- A research-track relation to RFC-003: an agent core SHOULD be measurable on the same Context Cost Benchmark as a user profile, so the "this saves context" claim is testable on first-party material.

**Out of scope (v1, deferred):**

- Cryptographic identity of an agent publisher (signatures, key rotation, transparency log). v1 sketches a `signature` slot but does not normalise it.
- Multi-agent composition (an agent core that imports another agent core). Deferred to a future RFC; v1 is one core per file.
- LoRA / adapter weights as part of `agent_core`. RFC-001 §10 already lists `adapter` as a future modality; the boundary stays there.
- Marketplaces, discovery, ranking, or rating of agent cores. Out of `.klickd` scope entirely.
- Strict JSON Schema for `agent_core`. v1 of this RFC describes the shape; strict schema arrives only if and when the RFC is promoted past `Proposed`.

## 3. Forward compatibility

This RFC targets a `.klickd v4+` payload extension. It does **not** modify v3.x, and it does **not** modify the normative surface of `v4.0.0` GA. Specifically:

- A `v4.0.0` GA writer MAY emit `agent_core` only if the RFC is at least `Proposed` and the writer documents the divergence; otherwise `agent_core` lives strictly on the post-GA track.
- A `v4.0.0` GA reader that does not understand `agent_core` MUST preserve it verbatim on round-trip (SPEC §33.7, RFC-004).
- A v3.x reader presented with a file carrying `agent_core` and `profile_kind: "agent"` MUST treat it as it would any v4 file: surface `KLICKD_E_VERSION` and refuse partial parsing (RFC-001 §3 V-011 pattern).
- A v4 reader that *does* understand `agent_core` MUST refuse to load it as a user profile (i.e. MUST refuse to feed it into a code path that expects user memory or user PII). See §6.

## 4. Decisions already resolved

The following decisions form the baseline. Reviewers should attack the **right** target.

1. **One file, one role.** A `.klickd` file is either a user profile (`profile_kind` ∈ { `learner`, `team`, `robot`, … }) **or** an agent core (`profile_kind: "agent"`). Mixing is non-conformant. This is the strongest single invariant in this RFC.
2. **No PII, ever.** `agent_core` files carry zero personal data about any human user. Pedagogy and curriculum are about *content*, not about *who the student is*. This is enforced at the producer side (refuse to write) and at the reader side (refuse to load mixed shapes). See §6.
3. **Versioned by the publisher.** `agent_core.version` is a `MAJOR.MINOR.PATCH` string controlled by the publisher (e.g. Klickd for Kai). It is *not* the `.klickd` envelope version; it is the **agent core's own** version line.
4. **Provenance is explicit.** `agent_core.provenance` records `published_by`, `published_at`, `spec_revision`, optional `signature` block. A reader MAY surface this to a user before injection.
5. **Default gates, not overriding gates.** If both a user profile and an agent core specify `verification_gates`, the **user wins on conflict**. The agent core's gates are *defaults* the user MAY accept by silence, never floors the user cannot lower. (RFC-002 invariant carried through.)
6. **Human veto is not delegable to an agent.** An agent core MUST NOT set `human_veto_policy` on behalf of the user. It MAY *propose* a baseline; the user's profile is the only authoritative carrier.
7. **Injection is host-controlled.** This RFC defines the *shape*, not the *prompt template*. A host (Klickd.app, a third-party integrator, a CLI) assembles the effective system prompt; the RFC documents which slices SHOULD appear, in what order, with what provenance markers.
8. **Showcase first.** `core.Kai.klickd` is the first-party showcase. The RFC's shape is informed by what Kai actually needs in production, not by a hypothetical generic agent. Other producers MAY publish their own `core.<Agent>.klickd` against the same shape.

## 5. Shape (illustrative — non-normative)

```jsonc
{
  "klickd_version": "4.0",
  "profile_kind": "agent",
  "agent_core": {
    "version": "1.0.0",
    "identity": {
      "name": "Kai",
      "vendor": "Klickd",
      "role": "learning_companion",
      "languages": ["fr", "en"],
      "default_language": "fr"
    },
    "pedagogy": {
      "posture": "socratic_with_scaffolding",
      "anti_patterns": ["spoon_feeding", "moralising", "praise_inflation"],
      "session_shape": {
        "default_block_minutes": 25,
        "checkpoint_every_n_blocks": 2
      }
    },
    "curriculum": {
      "refs": [
        { "id": "lux-maths-cycle3", "uri": "klickd://curriculum/lux-maths-cycle3", "hash": { "algo": "blake3", "value": "<base64>" } },
        { "id": "fr-grammar-b2",    "uri": "klickd://curriculum/fr-grammar-b2",    "hash": { "algo": "blake3", "value": "<base64>" } }
      ]
    },
    "rules": {
      "tone": ["direct", "patient", "non-condescending"],
      "always": [
        "answer the user's actual question before suggesting alternatives",
        "name the concept being practised before drilling it"
      ],
      "never": [
        "fabricate a citation",
        "claim to remember a session that is not in the user's .klickd",
        "lower a user-set verification gate"
      ]
    },
    "language_policy": {
      "respect_user_language": true,
      "fallback_chain": ["user.default_language", "agent.default_language", "en"]
    },
    "tool_policy": {
      "allowed": ["web_search", "calculator", "code_runner_sandbox"],
      "blocked": ["arbitrary_shell", "outbound_email", "payment"],
      "require_confirmation": ["web_search"]
    },
    "safety_policy": {
      "topics_require_caregiver_when_minor": ["mental_health_crisis", "self_harm", "explicit_content"],
      "redirect_to_human_help": ["medical_emergency", "abuse_disclosure"]
    },
    "default_verification_gates": {
      "factual_claim_about_person": "block",
      "public_post": "confirm",
      "casual_media_generation": "silent"
    },
    "provenance": {
      "published_by": "Klickd / Luxlearn (Luxembourg)",
      "published_at": "2026-05-23T00:00:00Z",
      "spec_revision": "SPEC.md@<git-sha>",
      "rfc_revision": "RFC-006@Draft",
      "signature": null
    }
  }
}
```

### Field rules (intent — formal schema only if/when promoted past `Proposed`)

- `profile_kind` MUST equal `"agent"` for a file carrying `agent_core`. A file with `agent_core` and any other `profile_kind` is non-conformant.
- `agent_core.version` MUST match `^\d+\.\d+\.\d+(-[A-Za-z0-9.-]+)?$`. Producers SHOULD follow SemVer semantics for breaking vs additive changes.
- `agent_core.identity.name` SHOULD match `^[A-Za-z][A-Za-z0-9_-]{0,63}$`.
- `agent_core.curriculum.refs[].hash` is REQUIRED when `uri` resolves to fetchable content (same rule as RFC-001 V-007).
- `agent_core.default_verification_gates` MUST use the same level vocabulary as RFC-002 (`silent` / `warn` / `confirm` / `block` / `require-owner`). On conflict with a user profile's `verification_gates`, the **user wins** (§4 #5).
- `agent_core.provenance.spec_revision` SHOULD be a stable pointer (git sha, content hash, or DOI) — not a moving branch reference.

## 6. The no-PII invariant (normative intent)

The single hardest failure mode of `agent_core` is **leaking user PII into a file that is published as part of an agent's identity**. If `core.Kai.klickd` ever shipped with a user's session transcript embedded, every host of every Kai deployment would carry that user's memory forever. This RFC therefore commits to a producer-side and reader-side rule:

- **Producer rule.** A writer that emits `agent_core` MUST refuse to write any of the following sections into the same file: `identity` (user identity per SPEC §25.1), `memory[]`, `archived_sessions[]`, `whitehat[]`, `companion_identity`, `consent_*`, `personality`, `growth`, `onboarding_trigger`, `data_integrity` (when carrying user-specific signals), or any free-form section that names an identified or identifiable natural person other than the agent publisher's own contact. The writer MUST surface `KLICKD_E_AGENT_CORE_PII` and abort.
- **Reader rule.** A reader presented with a file carrying both `agent_core` and any of the user-owned sections listed above MUST refuse to load the file as either a user profile or an agent core, and MUST surface `KLICKD_E_AGENT_CORE_MIXED`. It MUST NOT attempt to partition the file silently.
- **Validator rule.** A `.klickd validate` invocation against an `agent_core` file MUST run the no-PII check independently of schema validity. Schema-valid does not imply PII-clean.

This is the moral equivalent of RFC-001's hash verification rule (V-007): one hard fail-closed boundary, surfaced loudly, never silently relaxed.

## 7. Injection slices (host contract)

When a host assembles the effective context window for a session, it combines:

1. The **agent core** (`core.Kai.klickd`) — operating rules, pedagogy, language policy, tool policy, safety policy, default gates.
2. The **user profile** (`<user>.klickd`) — identity, memory, gates, consents, companion preferences.
3. Optional **session ephemera** — what the user just typed; not a `.klickd` payload.

The host SHOULD assemble the system prompt as ordered slices, each carrying its provenance marker:

| Order | Slice | Provenance marker | Source |
|---|---|---|---|
| 1 | Identity & language | `[agent:identity]` | `agent_core.identity` |
| 2 | Pedagogy & rules | `[agent:rules]` | `agent_core.pedagogy`, `agent_core.rules` |
| 3 | Tool & safety policy | `[agent:policy]` | `agent_core.tool_policy`, `agent_core.safety_policy` |
| 4 | User identity & companion | `[user:identity]` | user `.klickd` §25.1 / §25.2 |
| 5 | User memory & growth | `[user:memory]` | user `.klickd` `memory[]`, `growth` |
| 6 | Effective verification gates | `[gates:effective]` | merge of user gates over `agent_core.default_verification_gates`, **user wins on conflict** |
| 7 | Human veto policy | `[user:veto]` | user `.klickd` only (agent MUST NOT set this) |

Slices 6 and 7 carry the conflict-resolution invariant of §4 #5–#6: agent defaults can be *raised* by the user, never the reverse.

The host MUST NOT collapse slices into an undifferentiated prompt that hides the provenance of each line: an auditor reading the prompt should be able to tell which line came from the agent publisher vs the user.

## 8. Provenance and versioning

`agent_core.provenance` exists so a host can answer four questions before injection:

1. **Who** published this core? (`published_by`)
2. **When**? (`published_at`)
3. **Against which spec / RFC revision**? (`spec_revision`, `rfc_revision`)
4. **Is it signed, and by whom**? (`signature`, optional in v1)

`agent_core.version` is independent of the `.klickd` envelope's `klickd_version`. A single `klickd_version: "4.0"` file MAY carry any `agent_core.version` ≥ `0.1.0`. Changes follow SemVer:

- **PATCH** — wording, examples, no behavioural change for a host.
- **MINOR** — additive fields, new allowed tools, new curriculum refs.
- **MAJOR** — change in pedagogy posture, rule set, default gates, or anything that would surprise a previously-pinned host.

A host SHOULD pin `agent_core.version` (e.g. `Kai ^1.x`) and surface a confirmation to the user before adopting a MAJOR bump.

## 9. Relation to RFC-003 (Context Cost Benchmark)

RFC-003 measures the user-visible cost of repeated re-explanation across sessions and providers, with and without a `.klickd` user profile. `agent_core` is the dual: it is *the agent's* portable context, and the analogous question is **"how much instruction drift across providers does an agent core absorb?"**

A research-track extension SHOULD measure:

- Cross-provider behavioural delta when the same `core.Kai.klickd` is injected into provider A vs provider B (e.g. consistency of pedagogy posture, of refusal patterns, of language choice).
- The marginal cost (tokens, latency) of injecting `agent_core` on top of a user profile, compared to injecting only the user profile.
- Whether `agent_core` reduces hallucination on first-party pedagogy claims (does Kai stop inventing curriculum it does not have?).

This is **research**, not normative. The benchmark itself stays in `benchmarks/context_cost/` and is reproducible without network calls beyond declared `tool:*` entries.

## 10. Relation to compliance frameworks

The no-PII invariant of §6 is the compliance load-bearing rule. Specifically:

- **GDPR.** An `agent_core` file is **not** personal data (no identified or identifiable natural person). Publishing `core.Kai.klickd` does not create a data subject. This is only true if §6 is enforced; a producer that violates §6 has effectively shipped a personal-data leak.
- **EU AI Act (Art. 50 transparency).** `agent_core.provenance` is the surface a deployer SHOULD use to disclose "you are interacting with an AI" with a concrete publisher and version. The slice provenance markers of §7 give an auditor the *exact* lines that were declared agent-side vs user-side.
- **Children's data (Lux / EU).** When a user profile signals minor status, `agent_core.safety_policy.topics_require_caregiver_when_minor` becomes active; the host MUST honour it as a *floor*, not a default.
- **Right to portability.** `agent_core` is published; portability is a non-issue for the agent core itself. The user profile remains the user's portable artefact, untouched.

These are *intent* statements. They are not legal advice and they do not override an integrator's own DPIA.

## 11. Validation checklist (informative, for future v4+ conformance pack)

A conformance pack that targets `agent_core` SHOULD include at least:

- [ ] **A-001** — Reject a file with `agent_core` and any user-owned section listed in §6 (`KLICKD_E_AGENT_CORE_MIXED`).
- [ ] **A-002** — Reject a writer call that tries to emit `agent_core` together with user PII (`KLICKD_E_AGENT_CORE_PII`).
- [ ] **A-003** — Reject `profile_kind ≠ "agent"` when `agent_core` is present.
- [ ] **A-004** — Reject `agent_core.version` that does not match the SemVer regex.
- [ ] **A-005** — On gate conflict between `agent_core.default_verification_gates` and user `verification_gates`, the user value MUST win and the host MUST log the override.
- [ ] **A-006** — Reject any attempt to set `human_veto_policy` from `agent_core`.
- [ ] **A-007** — Preserve unknown `agent_core.x_*` fields verbatim on round-trip.
- [ ] **A-008** — A v3.x reader presented with `agent_core` MUST surface `KLICKD_E_VERSION`, not partial-parse.
- [ ] **A-009** — A v4 reader without `agent_core` support MUST preserve the field verbatim.
- [ ] **A-010** — `core.<AgentName>.klickd` files MUST round-trip byte-stable across reference Python and JS SDKs (when those SDKs gain `agent_core` support).

## 12. Error codes (additions)

| Code | HTTP | Meaning |
|---|---|---|
| `KLICKD_E_AGENT_CORE_MIXED` | 422 | A file carries both `agent_core` and user-owned sections (memory, identity, sessions, …). |
| `KLICKD_E_AGENT_CORE_PII` | 422 | A writer was asked to emit `agent_core` together with user PII. |
| `KLICKD_E_AGENT_CORE_VERSION` | 422 | `agent_core.version` is malformed or unsupported by the reader pin. |
| `KLICKD_E_AGENT_CORE_GATE_OVERRIDE` | 409 | An `agent_core` attempted to set a gate **below** the user's floor (rejected; user wins). |

## 13. First-party showcase: `core.Kai.klickd`

`core.Kai.klickd` is the first first-party file that exercises this RFC end-to-end. It is the Klickd-published operating context for Kai, the reference learning companion in `klickd.app`. Its role is:

- **Showcase.** Demonstrate, on real first-party material, that `.klickd` carries an agent's operating context portably and auditably — not just a user's profile.
- **Reference.** Be the canonical example other producers (third-party agent publishers) can study before publishing their own `core.<Agent>.klickd`.
- **Test surface.** Be a fixture the Context Cost Benchmark (RFC-003) and the future conformance pack of §11 can target.

`core.Kai.klickd` is **not** a substitute for a user profile, **not** a vehicle for user data, and **not** a marketplace listing. It is one specific Kai operating context, versioned, published, and replaceable.

A non-normative example payload lives at [`docs/rfcs/examples/agent_core-v1.example.json`](./examples/agent_core-v1.example.json). It is illustrative only — hashes are placeholders, signatures are absent.

## 14. Future work (post-v1)

- **Signature & transparency log.** A real `provenance.signature` slot with key rotation and a public log so a host can verify which publisher actually shipped this core. Likely RFC-007.
- **Composition.** An agent core that *imports* another (e.g. `core.KaiPro.klickd` extends `core.Kai.klickd`). Out of v1 scope; deferred to keep one-file-one-role tractable.
- **Adapter weights.** RFC-001 §10 sketches `adapter` as a fifth modality. If adopted, `agent_core` MAY reference adapter weights for an open-weights deployment. The hash discipline of RFC-001 carries through.
- **Marketplace surface.** Out of scope of `.klickd`. A registry of published agent cores is an ecosystem artefact, not a format artefact.
- **Promotion to normative.** This RFC stays `Draft` while v4 GA is closed out (P0 of [`ROAD-TO-V4-GA.md`](../roadmap/ROAD-TO-V4-GA.md) is not blocked on this). Promotion to `Proposed` is realistic once RFC-001/002/004 are `Accepted` and the schemas are strict.

## 15. Open questions

1. **`profile_kind: "agent"` vs a dedicated top-level discriminator.** Reusing `profile_kind` keeps the surface small but conflates "user role" (learner/team/robot) with "file class" (user vs agent). Alternative: a separate `file_class: "user" | "agent"` axis. Current choice: keep `profile_kind` for v1 to avoid surface creep; revisit if the conflation bites in real fixtures.
2. **Default-gate merge semantics.** Today: user wins on conflict. Open: when the agent core *raises* a gate (`silent → confirm`), should the user be notified or is silent-raise acceptable? Current draft: silent-raise is fine, silent-lower is forbidden.
3. **Multi-language agent cores.** `core.Kai.klickd` declares `languages: ["fr","en"]`. Is the right shape one file with multilingual content, or one file per language with a manifest? Current choice: one file, multilingual; revisit when content volume justifies splitting.
4. **Curriculum reference resolution.** `klickd://curriculum/<id>` is a placeholder URI scheme. Is this resolved by the host, by a registry, or by a CAS layer? Likely host-pluggable, but the v1 RFC does not normalise it.
5. **Versioning a *family* of cores.** If `core.KaiKids.klickd` and `core.KaiPro.klickd` share 80% of `core.Kai.klickd`, do they fork or compose? Currently fork (one-file-one-role). Composition is the §14 deferred item.
6. **First-party privilege.** Does Klickd's own showcase get any privileged status in `klickd.app`? Likely no at the format level; the format is publisher-agnostic. Branding and trust signals are an app-level concern, not a `.klickd` concern.

## 16. Examples

- [`docs/rfcs/examples/agent_core-v1.example.json`](./examples/agent_core-v1.example.json) — illustrative `core.Kai.klickd` fragment. Non-normative; hashes are placeholders; not a target for current schema validation.
