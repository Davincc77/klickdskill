# .klickd RFCs

This directory hosts **Requests for Comments** (RFCs) for the `.klickd` format.

RFCs are the place where significant changes — new payload sections, new envelope fields, behavioural rules with cross-implementation impact — are proposed, discussed, and refined **before** they enter the normative specification in `SPEC.md`.

> An RFC is **not** part of the normative specification while its status is `Draft` or `Proposed`. Implementors MUST NOT rely on RFC content unless and until it is promoted into `SPEC.md` and the relevant schema files in `schema/` / `schemas/`.

## Lifecycle

| Status | Meaning |
|---|---|
| `Draft` | Author is iterating. Not ready for implementation. |
| `Proposed` | Open for community review. Stable enough to prototype against. |
| `Accepted` | Approved for inclusion in the next normative `SPEC.md` revision. |
| `Implemented` | Has been merged into `SPEC.md` and the reference SDKs. Kept here as historical record. |
| `Withdrawn` | Closed without promotion. Kept for the record. |
| `Superseded by RFC-NNN` | Replaced by a later RFC. |

## Naming

Files follow `RFC-NNN-short-slug.md` with zero-padded sequential numbers (`RFC-001-…`). Example payloads, if any, live in `docs/rfcs/examples/` and are clearly marked **non-normative**.

## Current RFCs

| # | Title | Target | Status |
|---|---|---|---|
| 001 | [`media_profile` v1](./RFC-001-media-profile-v1.md) | `.klickd v4` | **Proposed** (2026-05-23) |
| 002 | [`verification_gates` + `human_veto`](./RFC-002-verification-gates.md) | `.klickd v4-A` (v1) · `v4-B` (v2 draft) | **Proposed** (v1 core, 2026-05-23) · Draft (v2 §8b additions) |
| 003 | [Context Cost Benchmark](../../benchmarks/context_cost/RFC.md) | `.klickd v4` (research / benchmark track) | Draft |
| 004 | [Migration & Backward Compatibility](./RFC-004-migration-backward-compatibility.md) | `.klickd v4` (migration policy for `v2.5 → v3.x → v3.5.1 → v4`) | **Proposed** (2026-05-23) |
| 005 | *Claim-memory growth & deterministic compaction (planned — not yet drafted)* | `.klickd v4+` (post-preview) | Planned — placeholder in [`ROADMAP.md`](../../ROADMAP.md) |
| 006 | [`agent_core` / Agent Operating Context](./RFC-006-agent-core.md) | `.klickd v4+` (post-GA; first-party showcase `core.Kai.klickd`) | Draft |

> RFC-001, RFC-002 (v1 core), and RFC-004 were promoted from `Draft` to `Proposed` on 2026-05-23 (docs-only). This freezes the conceptual surface for community review and for the v4 GA schema / SDK work tracked in [`docs/roadmap/ROAD-TO-V4-GA.md`](../roadmap/ROAD-TO-V4-GA.md). No SDK, schema, or vector changes are part of this promotion. RFC-003 stays `Draft` pending the benchmark execution (P1-3). RFC-002 §8b additions (v2 — claim grounding, contract tests, verification artifacts) stay `Draft` and may still iterate without affecting the v1 Proposed surface.

## Companion docs (non-normative)

| Doc | Purpose | Status |
|---|---|---|
| [v4 UX / Product Spec](../ux/V4-UX-SPEC.md) | UX intent for future v4 clients (viewer / decryptor / validator / migrator / agent handoff). Docs-only, no spec/schema/SDK change. | Draft |
| [`core.klickd` B2B use-case](../use-cases/CORE_KLICKD_B2B.md) | Concept doc — organisations / agents carry a portable `core.klickd` (rules, gates, tone, evidence, approvals) distinct from a user's `user.klickd`. Non-normative, future RFC candidate. | Draft (concept) |

## Test packs

Non-normative test packs exercise RFC fields against concrete (synthetic) scenarios before any normative wording or schema lands. They are draft-only and clearly marked.

| Pack | Targets | Status |
|---|---|---|
| [v4 Media Test Pack](./v4-media-test-pack.md) (Projects A `.klickd/klickdskill` + B `klickd.app`) | RFC-001, RFC-002 | Draft — fixtures only, no render |

## How to write one

1. Copy the structure of an existing RFC.
2. Use `Status: Draft` while iterating.
3. Be explicit about what is **normative** (RFC 2119 MUST / SHOULD / MAY) and what is illustrative.
4. List **open decisions** at the bottom — even ones you have answered locally — so reviewers can spot accidental assumptions.
5. Open a PR. Do not edit `SPEC.md` in the same PR unless adding a small roadmap pointer.
