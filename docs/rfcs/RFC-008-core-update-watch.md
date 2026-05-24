# RFC-008 — `core_update_watch` / Domain Core Skill Veille & Update Policy

| | |
|---|---|
| **RFC** | 008 |
| **Title** | `core_update_watch` — automatic veille and update policy for the **domain / agent core** skill layer, with a hard boundary against user memory |
| **Target** | `.klickd v4+` (post-GA extension track; NOT part of `v4.0.0` GA P0) |
| **Status** | **Draft** |
| **Author** | Vince C. (Klickd / Luxlearn, Luxembourg) |
| **Created** | 2026-05-24 |
| **Supersedes** | — |
| **Relates to** | RFC-001 (`media_profile`), RFC-002 (`verification_gates`, `human_veto_policy`), RFC-004 (Migration & Backward Compatibility — "Never break the soul"), RFC-006 (`agent_core`), [`CORE_KLICKD_B2B.md`](../use-cases/CORE_KLICKD_B2B.md), [`CREATOR-CORE-KLICKD.md`](../use-cases/CREATOR-CORE-KLICKD.md), [`ROAD-TO-V4-GA.md`](../roadmap/ROAD-TO-V4-GA.md) |

> **This RFC is non-normative.** It describes a *future* extension track on top of `.klickd v4`. It does **not** bind any current SDK, schema, reader or writer, and is **not** in scope for the `v4.0.0` GA P0 backlog defined in [`docs/roadmap/ROAD-TO-V4-GA.md`](../roadmap/ROAD-TO-V4-GA.md). v3.x and v4-preview readers MUST IGNORE every field listed below if they encounter it. v4 readers that do not understand `core_update_watch` MUST preserve it verbatim on round-trip (SPEC §33.7).
>
> No runtime code, no cron, no scheduler, no auto-publish, no signed key infrastructure is shipped or implied by this PR. The only artefact this PR adds is **this document**.

---

## 1. Motivation

`.klickd` v4 has, on paper, two cleanly separated payload classes (RFC-006, [`CORE_KLICKD_B2B.md`](../use-cases/CORE_KLICKD_B2B.md)):

| File class | What it carries | Who owns it |
|---|---|---|
| `user.klickd` | The user's portable memory: identity, preferences, history, growth, gates, consent — the *soul*. | The user. |
| `core.klickd` (incl. `core.<Agent>.klickd`, `core.<Org>.klickd`, `core.<Domain>.klickd`) | An agent's or organisation's operating context: domain rules, pedagogy, tone, workflow, evidence policy, tool policy, default gates. | The publisher (agent / org / domain authority). |

This separation enables a property that has no analogue in monolithic agent stacks: **the domain / agent core layer can be updated without touching user memory.** A new version of a legal core can ship when EU AI Act §50 transparency rules change; a new version of a medical core can ship when an HAS / NICE guideline is revised; a new version of a media core can ship when C2PA 2.x or platform watermarking policy changes — and *none* of these updates need to read, write, or mutate a single `user.klickd` byte.

Today, that capability is implicit. There is no defined surface for a core publisher to say:

- *what they watch* (which competency framework, which regulator, which standards body),
- *how often they check*,
- *what triggers a new version*,
- *how a host is expected to apply (or refuse) the update*,
- *and — most importantly — what they are forbidden from touching.*

`core_update_watch` is that surface. It is a payload-level block, scoped to **core** files only, that declares the **veille** (monitoring) sources, cadence, application channel, and review policy for the domain skill layer of a published core. Its single load-bearing invariant is **personal_data_boundary**: a `core_update_watch` operation MUST NOT, under any circumstance, mutate `user.klickd` content.

The principle, carrying forward RFC-004 ("Never break the soul") into the update domain:

> **Automatic veille updates ONLY the core / domain skill layer, never the user's personal memory. User data is immutable unless the user explicitly consents and migrates.**

This RFC does **not** introduce auto-update for `user.klickd`. RFC-004 already governs user-side migration and is the *only* path for user-side change.

## 2. Scope

**In scope (v1 of this RFC):**

- A payload-level `core_update_watch` object, valid only in a file with `profile_kind: "agent"` (RFC-006) or in a future `profile_kind: "core"` discriminator (open question §15 #1), declaring how the core publisher monitors upstream sources and ships updates.
- A normative invariant `personal_data_boundary` enforced at writer side, reader side, and update-applier side: a core update operation MUST NOT mutate any path inside a `user.klickd` file.
- A versioning rule for core skill packs (`skill_pack_manifest`), aligned with SemVer and the RFC-006 `agent_core.version` discipline.
- A `competency_framework_watch` block linking a skill to one or more upstream frameworks (legal text, clinical guideline, engineering standard, curriculum reference, platform policy).
- A `human_review_required` / `auto_apply_allowed` discipline that distinguishes update classes — wording fixes vs additive guidance vs MAJOR behavioural change — and forces human review for safety-critical domains (legal, medical, financial, platform-compliance).
- Provenance, signatures (sketch — full key infrastructure deferred to a future RFC, see RFC-006 §14), changelog, diff summary, and rollback model.
- Relation rules with RFC-002 (effective gates), RFC-004 (migration of user files is unaffected), and RFC-006 (agent_core stays the carrier).

**Out of scope (v1, deferred):**

- A normative wire format for the signed update channel (transparency log, key rotation, threshold signatures). v1 sketches a `signature` slot; normalisation is deferred to a future RFC (likely RFC-009).
- A discovery / marketplace surface for published cores. This is an ecosystem artefact, not a format artefact (consistent with RFC-006 §2).
- Auto-update of `user.klickd`. **Out of scope by design.** User-side change goes through RFC-004 migration only, with explicit user confirmation.
- Cross-core composition (a core that imports another core's update feed). Mirrors RFC-006's one-core-one-file stance; deferred.
- Runtime scheduler / cron / watcher implementation. This RFC describes the *contract*; whether a host polls, subscribes, or relies on a push channel is host-pluggable.
- A strict JSON Schema for `core_update_watch`. v1 of this RFC describes the shape; strict schema arrives only if and when the RFC is promoted past `Proposed`.

## 3. Forward compatibility

This RFC targets a `.klickd v4+` payload extension on **core files only**. It does **not** modify v3.x, and it does **not** modify the normative surface of `v4.0.0` GA.

- A `v4.0.0` GA writer MAY emit `core_update_watch` only if the RFC is at least `Proposed` and the writer documents the divergence; otherwise it lives strictly on the post-GA track.
- A `v4.0.0` GA reader that does not understand `core_update_watch` MUST preserve it verbatim on round-trip (SPEC §33.7, RFC-004 §3, RFC-006 §3).
- A v3.x reader presented with a file carrying `core_update_watch` MUST surface `KLICKD_E_VERSION` per the RFC-001 §3 V-011 pattern. It MUST NOT partial-parse.
- A reader that *does* understand `core_update_watch` MUST refuse to load it inside a file whose `profile_kind` is a user role (`learner`, `team`, `robot`, …). See §6.
- A user-side reader (any reader operating on `user.klickd`) MUST IGNORE `core_update_watch` if it somehow appears there, and SHOULD surface a warning. `core_update_watch` is meaningless and forbidden in user files.

## 4. Decisions already resolved

The following decisions form the baseline. Reviewers should attack the **right** target.

1. **Core layer is the only update target.** `core_update_watch` updates `core.klickd` content (rules, curriculum refs, framework versions, evidence policy, tool policy, safety policy). It does **not**, ever, update a `user.klickd` file.
2. **User data is immutable to the update path.** A core update operation MUST treat every `user.klickd` byte as read-only. The boundary is enforced at three layers: writer (refuse to emit), reader (refuse to apply), runtime (refuse to merge). The invariant has its own error code: `KLICKD_E_CORE_UPDATE_USER_DATA`.
3. **The user wins on conflict, always.** If a core update raises a default gate or changes a rule that conflicts with a user-set value in `user.klickd`, the **user wins** (RFC-002 invariant; RFC-006 §4 #5). A core update MUST NOT lower a user-set floor and MUST NOT replace a user-chosen value.
4. **Safety-critical domains require human review.** For declared safety-critical domains (legal, medical, financial, child-safety, platform-compliance), `human_review_required: true` is enforced regardless of the update class. `auto_apply_allowed` MUST be `false` for these classes in v1 of this RFC.
5. **Signed when possible, declared when not.** A core update SHOULD carry a `signature` block and provenance pointing to the publisher's public key. If unsigned, the host MUST surface that fact before applying.
6. **Rollback is mandatory.** Every applied core update MUST be reversible to the immediately previous core version, via a local backup analogous to RFC-004 §3 #3. There is no "best-effort" partial rollback.
7. **No silent legal / medical / financial rule changes.** A MAJOR update to a safety-critical core MUST surface a one-screen summary (changelog + diff_summary + affected_skills) and require an explicit human action to commit. (Mirrors RFC-004 §3 #4.)
8. **Veille is declarative, not behavioural.** This RFC describes *what a core publisher watches and how they ship*. It does **not** mandate a polling cadence or a transport. A host MAY honour the declaration with a cron, a push subscription, or manual operator action.
9. **No PII in update artefacts.** Changelogs, diff summaries, and `affected_skills` lists MUST NOT mention identified or identifiable natural persons (other than the publisher's own contact). This carries the RFC-006 §6 no-PII invariant into the update domain.
10. **CC0-compatible.** A user with `jq` and a text editor MUST be able to inspect a `core_update_watch` block, the `skill_pack_manifest`, and the `migration_report`-equivalent (`core_update_report`) without proprietary tooling. (Mirrors RFC-004 §4 #9.)

## 5. Shape (illustrative — non-normative)

A `core_update_watch` block sits inside an `agent_core` (RFC-006) — or, when a dedicated `profile_kind: "core"` arrives, at payload root of a core file. v1 of this RFC pins it inside `agent_core` to avoid surface creep.

```jsonc
{
  "klickd_version": "4.0",
  "profile_kind": "agent",
  "agent_core": {
    "version": "1.4.0",
    "identity": { "name": "KaiLegal", "vendor": "Klickd", "role": "domain_companion" },
    // ... pedagogy, rules, tool_policy, safety_policy as per RFC-006 ...

    "core_update_watch": {
      "core_update_policy": {
        "source_registry": "klickd-core-registry/v1",
        "watch_sources": [
          {
            "id": "eu-ai-act-art50",
            "kind": "regulation",
            "uri": "https://eur-lex.europa.eu/eli/reg/2024/1689/oj",
            "jurisdiction": "EU",
            "etag_or_hash": { "algo": "blake3", "value": "<base64>" },
            "last_checked": "2026-05-20T07:00:00Z",
            "change_detected": false
          },
          {
            "id": "c2pa-spec",
            "kind": "standard",
            "uri": "https://c2pa.org/specifications/specifications/2.1/specs/C2PA_Specification.html",
            "etag_or_hash": { "algo": "blake3", "value": "<base64>" },
            "last_checked": "2026-05-22T07:00:00Z",
            "change_detected": true,
            "affected_skills": ["media.provenance", "media.watermark"]
          }
        ],
        "cadence": "daily",
        "update_channel": "klickd://core-channel/stable",
        "semantic_versioning": true,
        "changelog_required": true,
        "diff_summary": true,
        "human_review_required": true,
        "auto_apply_allowed": false,
        "rollback": {
          "supported": true,
          "backup_strategy": "sibling_file",
          "min_versions_retained": 2
        },
        "deprecation_policy": {
          "min_notice_days": 90,
          "supersession_required": true
        }
      },

      "personal_data_boundary": {
        "protected_paths": [
          "user.klickd",
          "$.identity",
          "$.memory[*]",
          "$.archived_sessions[*]",
          "$.whitehat[*]",
          "$.companion_identity",
          "$.consent_*",
          "$.personality",
          "$.growth",
          "$.onboarding_trigger"
        ],
        "forbidden_writes": ["replace", "merge", "delete", "default-fill"],
        "merge_strategy": "core_overlay_only",
        "user_wins_conflicts": true
      },

      "competency_framework_watch": [
        {
          "framework_id": "eu-ai-act",
          "version": "1689/2024",
          "source_url": "https://eur-lex.europa.eu/eli/reg/2024/1689/oj",
          "last_checked": "2026-05-20T07:00:00Z",
          "change_detected": false,
          "affected_skills": ["legal.transparency", "legal.disclosure"]
        },
        {
          "framework_id": "c2pa",
          "version": "2.1",
          "source_url": "https://c2pa.org/specifications/specifications/2.1/",
          "last_checked": "2026-05-22T07:00:00Z",
          "change_detected": true,
          "affected_skills": ["media.provenance"]
        }
      ],

      "skill_pack_manifest": {
        "domain": "legal.eu",
        "version": "1.4.0",
        "compatible_klickd_versions": ["4.0", "4.1"],
        "hash": { "algo": "blake3", "value": "<base64>" },
        "signatures": [
          {
            "key_id": "klickd-legal-2026",
            "algo": "ed25519",
            "value": "<base64>",
            "signed_at": "2026-05-22T08:00:00Z"
          }
        ]
      }
    }
  }
}
```

### Field rules (intent — formal schema only if/when promoted past `Proposed`)

- `core_update_watch` MUST appear only inside `agent_core` (v1). A file with `profile_kind ∈ { "learner", "team", "robot", … }` carrying `core_update_watch` is non-conformant and MUST be rejected (`KLICKD_E_CORE_UPDATE_WRONG_KIND`).
- `core_update_policy.cadence` MUST be one of `manual`, `hourly`, `daily`, `weekly`, `on_publish`. A host is free to ignore the cadence in favour of a stricter one but MUST NOT relax it without surfacing the change.
- `core_update_policy.human_review_required` MUST be `true` for domains declared safety-critical (see §6.2). A writer that emits `human_review_required: false` for such a domain MUST be rejected with `KLICKD_E_CORE_UPDATE_REVIEW_REQUIRED`.
- `core_update_policy.auto_apply_allowed` MUST be `false` whenever `human_review_required` is `true`. The two flags are jointly constrained.
- `personal_data_boundary.protected_paths` MUST include, at minimum, the user-owned sections enumerated in RFC-006 §6. A writer that emits a `protected_paths` list **shorter** than the RFC-006 §6 enumeration MUST be rejected with `KLICKD_E_CORE_UPDATE_BOUNDARY`.
- `personal_data_boundary.user_wins_conflicts` MUST be `true`. The field exists for explicitness; setting it to `false` is non-conformant.
- `competency_framework_watch[].version` SHOULD be a stable identifier (regulatory citation, standards version, ISBN, DOI) — not a moving branch reference.
- `skill_pack_manifest.version` MUST match the SemVer regex `^\d+\.\d+\.\d+(-[A-Za-z0-9.-]+)?$` (mirrors RFC-006 `agent_core.version`).
- `skill_pack_manifest.hash` is REQUIRED. Unsigned manifests are permitted in v1 but MUST be surfaced to the host before apply.

## 6. The personal-data boundary (normative intent)

This is the load-bearing invariant of this RFC, equivalent in weight to RFC-001 §V-007 (hash verification) and RFC-006 §6 (no PII in agent core).

### 6.1 Three-layer enforcement

- **Producer rule.** A writer that emits a `core_update_*` artefact MUST reject any path that targets a user-owned section (see RFC-006 §6 enumeration plus `personal_data_boundary.protected_paths`). The writer MUST surface `KLICKD_E_CORE_UPDATE_USER_DATA` and abort. There is no override flag.
- **Reader rule.** A reader presented with a `core_update_report` whose `applied_changes[]` touches any protected path MUST refuse the apply, restore from backup if necessary, and surface `KLICKD_E_CORE_UPDATE_USER_DATA`. It MUST NOT attempt partial application.
- **Runtime rule.** A host that composes `user.klickd` + `core.klickd` at request time MUST treat the user file as a read-only overlay floor: core defaults can be raised by user values, never the reverse. (Mirrors RFC-006 §7 slice ordering.)

### 6.2 Safety-critical domains

The following `skill_pack_manifest.domain` prefixes are declared safety-critical for v1:

| Prefix | Examples |
|---|---|
| `legal.*` | `legal.eu`, `legal.lux`, `legal.contracts` |
| `medical.*` | `medical.guidelines`, `medical.triage`, `medical.pharma` |
| `financial.*` | `financial.kyc`, `financial.aml`, `financial.tax` |
| `child_safety.*` | `child_safety.minor_redaction`, `child_safety.caregiver_routing` |
| `platform_compliance.*` | `platform_compliance.tiktok`, `platform_compliance.meta`, `platform_compliance.c2pa` |

For any core whose `domain` matches one of these prefixes:

- `human_review_required` MUST be `true`.
- `auto_apply_allowed` MUST be `false`.
- A MAJOR update MUST surface a one-screen summary (changelog, diff_summary, affected_skills, source citations) and require an explicit human action to commit.
- Updates MUST be signed (`signatures[]` non-empty) or surfaced as unsigned to the operator before apply.

A host that relaxes any of the above is non-conformant.

### 6.3 No PII in update artefacts

A `changelog`, `diff_summary`, `affected_skills`, or `core_update_report` MUST NOT mention an identified or identifiable natural person (other than the publisher's own contact). Curriculum updates, clinical-guideline updates, regulatory updates concern *content*, not specific patients, clients, or learners. Mirrors RFC-006 §6.

## 7. Update lifecycle (host contract)

A core update is a five-step process. It is host-controlled; the RFC defines the contract, not the implementation.

| Step | Action | Who | Artefact |
|---|---|---|---|
| 1 | **Detect.** Compare `watch_sources[].etag_or_hash` against current upstream. | Host (poll) or publisher (push). | Updated `last_checked`, `change_detected` flags. |
| 2 | **Fetch.** Pull candidate new core version from `update_channel`, verify `skill_pack_manifest.hash`, verify `signatures[]` if present. | Host. | Candidate `core.klickd` file (not yet active). |
| 3 | **Review.** If `human_review_required`, surface changelog + diff_summary + affected_skills + provenance to the operator. Block on explicit confirmation. | Operator (human). | Recorded confirmation timestamp. |
| 4 | **Apply.** Replace active core; persist previous version to backup (analogous to RFC-004 §3 #3). Emit `core_update_report` sibling artefact. | Host. | Backup file, `core_update_report`. |
| 5 | **Verify.** Confirm `personal_data_boundary` was not breached (re-hash protected user paths; assert equality with pre-apply hashes). Roll back on mismatch. | Host. | Pass/fail recorded in `core_update_report`. |

Step 5 is the load-bearing verification: the host MUST hash protected user paths before apply, hash them after apply, and assert byte equality. Any mismatch MUST trigger automatic rollback and a loud error (`KLICKD_E_CORE_UPDATE_USER_DATA`).

### 7.1 `core_update_report` (sibling artefact — illustrative)

```jsonc
{
  "core_update_report": {
    "schema": "klickd.core_update_report/v1-draft",
    "generated_at": "2026-05-22T08:30:00Z",
    "domain": "legal.eu",
    "source_version": "1.3.2",
    "target_version": "1.4.0",
    "trigger": { "source_id": "eu-ai-act-art50", "change_detected_at": "2026-05-20T07:00:00Z" },
    "signed": true,
    "signature_verified": true,
    "human_review_required": true,
    "human_confirmed_at": "2026-05-22T08:29:51Z",
    "backup_path": "./core.KaiLegal.klickd.bak-1.3.2-2026-05-22T08-29-00Z",
    "applied_changes": [
      { "path": "$.agent_core.rules.always[3]", "kind": "add", "summary": "disclose AI status per Art. 50" },
      { "path": "$.agent_core.curriculum.refs[2].hash", "kind": "update", "summary": "C2PA 2.1 manifest refresh" }
    ],
    "user_data_boundary_check": {
      "protected_paths_hashed_before": "<base64>",
      "protected_paths_hashed_after":  "<base64>",
      "equal": true
    },
    "rollback_supported": true
  }
}
```

`core_update_report` is a **sibling artefact**, not a payload section embedded in the core file. Embedding it would itself be a soul-touching mutation, in the spirit of RFC-004 §4 #4.

## 8. Domain examples (illustrative)

These examples show how `core_update_watch` would be used in practice. They are non-normative; field placement may evolve.

### 8.1 Legal core — EU AI Act change

```jsonc
"competency_framework_watch": [{
  "framework_id": "eu-ai-act",
  "version": "1689/2024",
  "source_url": "https://eur-lex.europa.eu/eli/reg/2024/1689/oj",
  "last_checked": "2026-05-20T07:00:00Z",
  "change_detected": true,
  "affected_skills": ["legal.transparency", "legal.disclosure"]
}]
```

→ Triggers a MAJOR bump on `core.KaiLegal.klickd` from 1.3.x to 1.4.0. `human_review_required: true`. Signed by Klickd-legal key. Surfaces one-screen summary; operator confirms. User `verification_gates` untouched.

### 8.2 Medical core — guideline revision

```jsonc
{ "framework_id": "has-fr-triage", "version": "2026-Q2", "change_detected": true,
  "affected_skills": ["medical.triage.adult", "medical.triage.peds"] }
```

→ MAJOR bump on `core.MedKai.klickd`. `human_review_required: true`. Operator (clinical lead) reviews diff_summary. User memory (patient history kept on user side, if any) untouched.

### 8.3 Engineering core — ISO/IEC standard update

```jsonc
{ "framework_id": "iso-iec-25010", "version": "2023", "change_detected": true,
  "affected_skills": ["engineering.quality_model"] }
```

→ MINOR bump. `human_review_required` may be `false` for non-safety engineering domains. `auto_apply_allowed` host-pluggable; diff still surfaced post-apply.

### 8.4 Education core — curriculum revision

```jsonc
{ "framework_id": "lux-maths-cycle3", "version": "2026", "change_detected": true,
  "affected_skills": ["edu.maths.cycle3"] }
```

→ MINOR bump on `core.Kai.klickd`. Curriculum hash (RFC-006 `curriculum.refs[].hash`) refreshed. User `growth` and `memory[]` untouched — the *content* of the curriculum changed, not what *the learner* did under the previous version.

### 8.5 Media core — platform / C2PA change

```jsonc
{ "framework_id": "c2pa", "version": "2.1", "change_detected": true,
  "affected_skills": ["media.provenance", "media.watermark"] }
```

→ MAJOR bump on `core.MediaKai.klickd` because platform-compliance is safety-critical. `human_review_required: true`. User `media_profile` references (RFC-001) untouched.

## 9. Relation to other RFCs

- **RFC-001 (`media_profile`).** `core_update_watch` may refresh framework references (e.g. C2PA 2.x) on the *core* side. A user's `media_profile` references and hashes (RFC-001 V-007) are user-owned and remain untouched. Re-hashing user-referenced media is **never** a core-update concern.
- **RFC-002 (`verification_gates`, `human_veto_policy`).** A core update MAY raise a `default_verification_gates` value (`silent → confirm`), never lower a user-set value. `human_veto_policy` MUST NOT be set or modified by a core update (RFC-006 §4 #6 carried through).
- **RFC-004 (Migration).** RFC-004 governs the `v3.x → v4` migration of *user* files. RFC-008 governs *core* updates within the v4 line. They share the "Never break the soul" principle, the backup-before-write discipline (§3 #3 / §7 step 4), and the loud-failure discipline (§3 #7 / §7 step 5). They never interact: a core update never triggers a user migration, and a user migration never triggers a core update.
- **RFC-006 (`agent_core`).** `core_update_watch` lives **inside** `agent_core` in v1. The one-file-one-role invariant of RFC-006 §4 #1 is preserved: a user profile never carries `core_update_watch`. The no-PII invariant of RFC-006 §6 carries directly into update artefacts (§6.3).
- **RFC-007 (`creator_profile`, reserved).** A future `creator_profile` core MAY carry its own `core_update_watch` (e.g. platform-policy watch for TikTok, Reels, Shorts). Same boundary rules apply.

## 10. Relation to compliance frameworks

- **GDPR.** A `core_update_watch` operation processes **no personal data** (boundary §6.1; no-PII §6.3). Publishing core updates does not create a data subject. The boundary check at §7 step 5 is the load-bearing technical safeguard.
- **EU AI Act (Art. 50, Art. 53 GPAI obligations).** `competency_framework_watch[].framework_id: "eu-ai-act"` is the canonical declarative surface for AI Act transparency-rule changes. Provenance and changelog at the core update level satisfy the "documented and up-to-date" requirement at the agent-publisher level; they do not absolve an integrator's own DPIA.
- **EU AI Act Art. 5 (prohibited practices) / safety-critical.** §6.2's safety-critical domains include `medical.*`, `legal.*`, `financial.*`, `child_safety.*`, `platform_compliance.*` — these align with high-risk categories where silent updates would be inappropriate.
- **EU DSA / platform compliance.** `platform_compliance.*` core updates (TikTok / Meta / YouTube / C2PA) are explicitly safety-critical: a silent change to "what can be auto-posted" is forbidden by §6.2.
- **Children's data.** Carried from RFC-006 §10: a `safety_policy.topics_require_caregiver_when_minor` change in a core MUST go through human review.
- **Right to portability.** Unaffected. User portability is a property of `user.klickd`, which a core update is forbidden to touch.

These are *intent* statements. They are not legal advice and they do not override an integrator's own DPIA / SOC2 / ISO 27001 controls.

## 11. Safety properties (summary)

A conformance pack that targets `core_update_watch` SHOULD enforce, at minimum:

- [ ] **U-001** — Reject a `core_update_watch` block in a file whose `profile_kind` is not `agent` (or future `core`) (`KLICKD_E_CORE_UPDATE_WRONG_KIND`).
- [ ] **U-002** — Reject an update operation whose `applied_changes[].path` touches any protected user path (`KLICKD_E_CORE_UPDATE_USER_DATA`).
- [ ] **U-003** — Reject a safety-critical core update with `human_review_required: false` or `auto_apply_allowed: true` (`KLICKD_E_CORE_UPDATE_REVIEW_REQUIRED`).
- [ ] **U-004** — Reject a `personal_data_boundary.protected_paths` list that does not cover the RFC-006 §6 enumeration (`KLICKD_E_CORE_UPDATE_BOUNDARY`).
- [ ] **U-005** — Reject `personal_data_boundary.user_wins_conflicts: false`.
- [ ] **U-006** — On gate conflict between a core update and a user `verification_gates`, the user value MUST win and the host MUST log the override (carries RFC-002 / RFC-006 §4 #5).
- [ ] **U-007** — Reject any attempt to write `human_veto_policy` via a core update.
- [ ] **U-008** — Backup-before-write: a core apply without a successful backup MUST fail and leave the previous version in place (mirrors RFC-004 §3 #3).
- [ ] **U-009** — Post-apply hash check: protected user paths MUST hash byte-identical before and after apply (`KLICKD_E_CORE_UPDATE_USER_DATA` on mismatch). Automatic rollback on failure.
- [ ] **U-010** — A `core_update_report` MUST NOT contain PII (mirrors RFC-006 §6 via §6.3).
- [ ] **U-011** — Unsigned updates MUST be surfaced as unsigned before apply; the host MUST NOT silently treat unsigned as signed.
- [ ] **U-012** — Rollback path MUST restore byte-identical previous core (`KLICKD_E_CORE_UPDATE_ROLLBACK` on failure).

## 12. Error codes (additions)

| Code | HTTP | Meaning |
|---|---|---|
| `KLICKD_E_CORE_UPDATE_WRONG_KIND` | 422 | `core_update_watch` present in a file whose `profile_kind` is a user role. |
| `KLICKD_E_CORE_UPDATE_USER_DATA` | 422 | A core update operation attempted to read/write/mutate a protected user path. |
| `KLICKD_E_CORE_UPDATE_BOUNDARY` | 422 | `personal_data_boundary.protected_paths` is missing required entries or `user_wins_conflicts` is `false`. |
| `KLICKD_E_CORE_UPDATE_REVIEW_REQUIRED` | 422 | Safety-critical domain emitted with `human_review_required: false` or `auto_apply_allowed: true`. |
| `KLICKD_E_CORE_UPDATE_SIGNATURE` | 422 | `signatures[]` present but failed verification, or required by policy and absent. |
| `KLICKD_E_CORE_UPDATE_ROLLBACK` | 500 | Rollback was requested or auto-triggered, and the previous core version could not be restored. |
| `KLICKD_E_CORE_UPDATE_VERSION` | 422 | `skill_pack_manifest.version` is malformed or incompatible with `compatible_klickd_versions`. |

## 13. Roadmap and relation to v4 GA

`core_update_watch` is firmly **post-GA**. It does not block, gate, or modify `v4.0.0` GA. The intended phasing aligns with [`ROAD-TO-V4-GA.md`](../roadmap/ROAD-TO-V4-GA.md):

- **P0 (GA-blocking) — none.** Nothing in this RFC blocks `v4.0.0` GA. RFC-001 / RFC-002 / RFC-004 close out independently.
- **P1 (adoption) — prerequisites.** RFC-006 (`agent_core`) at `Proposed` or better; `core.Kai.klickd` showcase live; signed-channel sketch (RFC-006 §14) advanced enough that this RFC's `signatures[]` slot is not vapourware.
- **P2 (extension) — this RFC.** Promote to `Proposed` once first-party `core.KaiLegal.klickd` and `core.MediaKai.klickd` exist as docs-only showcases mirroring `core.Kai.klickd`. Promote to `Accepted` once two third-party publishers have shipped a `skill_pack_manifest` against the shape and the conformance pack of §11 is green.

This is consistent with `ROAD-TO-V4-GA.md` §2.3 (P2 — souhaitable / extension).

## 14. Future work (post-v1)

- **Signed-channel normalisation.** A real `signatures[]` discipline with key rotation, transparency log, and threshold signatures. Likely RFC-009 — paired with RFC-006 §14's deferred signature work.
- **Update channel discovery.** A `update_channel` URI scheme (`klickd://core-channel/<id>`) resolved by a registry or a CAS layer. Host-pluggable; not normalised here.
- **Cross-core composition.** A core whose `core_update_watch.watch_sources[]` *imports* another core's feed (e.g. `core.MedKai-Lux.klickd` imports `core.MedKai.klickd` plus a Lux-specific overlay). Deferred to a future RFC.
- **Telemetry of apply outcomes.** A privacy-preserving aggregate of "how many hosts applied v1.4.0 within N days" — entirely opt-in and PII-free. Out of v1 scope.
- **Co-evolution with RFC-004.** If a core update would *also* require a user-side schema bump (extremely rare; would mean a v4 → v4.1 envelope change), the two RFCs interact: the core update MUST NOT proceed until the user has been offered an RFC-004 migration. v1 of this RFC simply forbids the case at writer side.

## 15. Open questions

1. **`profile_kind: "agent"` vs `profile_kind: "core"`.** Carrying `core_update_watch` inside `agent_core` (RFC-006) keeps the surface tight but conflates "agent operating context" with "domain skill pack". A dedicated `profile_kind: "core"` discriminator would be cleaner long-term. Current draft: stay inside `agent_core` to avoid surface creep; revisit when a non-agent skill pack (e.g. pure curriculum) appears.
2. **Cadence floor.** Is `manual` a permissible value, or must every core declare at least `weekly`? Current draft: `manual` is allowed; some domains (e.g. tax codes) genuinely change only on declared dates and polling daily would be noise.
3. **MAJOR vs MINOR semantics for safety-critical domains.** Should *every* safety-critical update be treated as MAJOR for review purposes, regardless of SemVer? Current draft: yes for `legal.*` / `medical.*` / `financial.*`; revisit for `engineering.*` and `platform_compliance.*`.
4. **Hash discipline on watch sources.** `etag_or_hash` allows ETag for HTTP polling and hash for content-addressed sources. Is the looseness a problem? Current draft: no — different upstream sources have different freshness primitives.
5. **What happens when a watched source disappears.** A regulatory portal redirects; a standards URL 404s. Does the core auto-deprecate the corresponding skill? Current draft: no — surface a warning, leave the skill active, escalate to human review. Silent deprecation would itself be a "break the soul" event.
6. **Cross-jurisdiction conflicts.** A core watches both EU and US frameworks; they diverge. How does the core express "conflict, escalate to operator"? Likely a `conflict_policy` sub-block in v2 of this RFC; out of v1.
7. **Localised cores and language drift.** A French legal core derives from an EU regulation translated to FR. The translation changes upstream. Is that a MAJOR or PATCH? Currently host-pluggable; will pressure-test once `core.KaiLegal.klickd` ships.
8. **First-party privilege.** Does Klickd's own first-party cores get any privileged status at the format level? Carried from RFC-006 §15 #6: no, the format is publisher-agnostic; branding stays at the app level.

## 16. Examples and showcases (future)

Once promoted past `Draft`, this RFC SHOULD be accompanied by at least:

- `core.KaiLegal.klickd` — first-party legal core with `competency_framework_watch` against EU AI Act, GDPR, Lux national overlays.
- `core.MediaKai.klickd` — first-party media core with watch against C2PA, platform policies, watermarking standards.
- `core.MedKai.klickd` — first-party medical core (illustrative; not a clinical product).
- A non-normative `core_update_report` fixture at `docs/rfcs/examples/core_update_report-v1.example.json` (mirrors RFC-006's `examples/` discipline).

These would join `core.Kai.klickd` (RFC-006 §13) as first-party showcases of the format's separation-of-concerns story:

> *Configure your agent's operating context once. Watch upstream sources. Update the core. Never touch the user's soul.*
