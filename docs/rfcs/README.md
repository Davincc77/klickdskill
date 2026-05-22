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
| 001 | [`media_profile` v1](./RFC-001-media-profile-v1.md) | `.klickd v4` | Draft |

## How to write one

1. Copy the structure of an existing RFC.
2. Use `Status: Draft` while iterating.
3. Be explicit about what is **normative** (RFC 2119 MUST / SHOULD / MAY) and what is illustrative.
4. List **open decisions** at the bottom — even ones you have answered locally — so reviewers can spot accidental assumptions.
5. Open a PR. Do not edit `SPEC.md` in the same PR unless adding a small roadmap pointer.
