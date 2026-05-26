# v4.0 Improved Starter Packs — Acceptance Checklist

> **Status:** Standalone acceptance criteria document. **Non-normative.**
> Docs-only — independent of the actual pack files and any pack generation
> work. Adding or editing this checklist does **not** modify, generate, or
> publish any starter pack.
>
> **Scope:** the four v4.0 improved starter packs:
>
> - `user.klickd` (private personal memory carrier — normative core,
>   see [`docs/spec/R4-P0-1-onboarding-wizard.md`](../spec/R4-P0-1-onboarding-wizard.md))
> - `student.klickd` (learner starter; v4.0 surface only — distinct from the
>   future v4.1 Chimera `x.klickd/student` `competency_pack` scaffold in
>   [`docs/rfcs/chimera/packs/student.md`](../rfcs/chimera/packs/student.md))
> - `research.klickd` (researcher starter)
> - `coding.klickd` (developer / coding-agent starter)
>
> **Where the packs live (informational, non-binding):** the four starter
> `.klickd` files currently ship under
> [`examples/v4/starter-skills/`](../../examples/v4/starter-skills/) (neutral
> public path). This pointer is informational — acceptance below is defined
> against the pack files wherever they live in the repo, not against this
> path.
>
> **Out of scope (hard exclusions):**
>
> - Triggering a release, tag, npm/PyPI publication, dist-tag move, or
>   Zenodo deposit. See [`docs/releases/CHECKLIST_v4_preview.md`](../releases/CHECKLIST_v4_preview.md)
>   for the publication track; this checklist explicitly does **not** invoke
>   it.
> - Any v4.1 / Chimera surface (frameworks, `base_transversal_core`,
>   `competency_pack` carrier-vs-skill rule). v4.1 acceptance lives under
>   [`docs/rfcs/RFC-009-chimera-v4.1.md`](../rfcs/RFC-009-chimera-v4.1.md).
> - Site / `klickd.app` UX shipping. The site handoff item below describes
>   the gate, not the work.

---

## 0. Ground rules

These rules apply across all four packs. A pack that fails any single rule
in this section is **not acceptable**, regardless of how complete the rest
of the work is.

- [ ] **No fake catalog.** Every reference to an external taxonomy,
      framework, registry, or "domain catalog" inside any pack file or the
      pack's documentation MUST resolve to an actually existing public
      source. No invented IRIs, no placeholder taxonomies presented as
      authoritative, no "TBD" entries shipped as real. If a framework
      anchor is not ready, the field is **omitted**, not stubbed with a
      plausible-looking fake.
- [ ] **No v4.1 GA claim.** Pack files, their READMEs, and any
      surrounding docs MUST NOT describe themselves as "v4.1", "Chimera
      GA", "v4.1-ready", "v4.1-native", or imply that v4.1 has shipped.
      The v4.0 improved packs target the v4.0 surface (see SPEC §33 and
      the v4 onboarding wizard); v4.1 remains a draft RFC.
- [ ] **No DOI.** The packs and their READMEs MUST NOT carry a Zenodo or
      other DOI, MUST NOT cite a future or "reserved" DOI, and MUST NOT
      claim citation under the v3.5.1 concept DOI. DOI minting is a
      release-time action handled by
      [`docs/releases/CHECKLIST_v4_preview.md`](../releases/CHECKLIST_v4_preview.md)
      §5 and is **out of scope** here.
- [ ] **No release actions.** Acceptance of this checklist MUST NOT
      involve tagging, publishing to npm or PyPI, moving the `latest`
      dist-tag, opening a Zenodo deposit, updating `CITATION.cff` /
      `.zenodo.json`, or filing an IANA request. Those belong to the
      release checklist and require a separate explicit decision.
- [ ] **Docs-only independence.** This checklist is reviewable and
      mergeable on its own. It MUST NOT block on pack generation, schema
      changes, SDK updates, or vectors. Conversely, the pack work MUST
      NOT depend on edits to this file to proceed.

---

## 1. Per-pack acceptance criteria

Apply the same shape to each of the four packs. A pack is acceptable when
every box in its section is ticked.

### 1.1 `user.klickd`

- [ ] Pack file is a valid v4 `user.klickd` envelope per SPEC §33 and the
      current v4 schema. Validation MUST be performed against the
      published v4 schema, not a local copy with edits.
- [ ] Produced via the seven-step onboarding wizard surface defined in
      [`docs/spec/R4-P0-1-onboarding-wizard.md`](../spec/R4-P0-1-onboarding-wizard.md);
      no field appears in the pack that the wizard cannot produce
      client-side.
- [ ] No `<x>.klickd` domain payload leaks into the `user.klickd` main
      path (no `gaming.*`, `coding.*`, `research.*`, `student.*` fields).
- [ ] No teacher / agent method fields (`pedagogy`, `socratic_steps`,
      `prompt_strategy`, `tone_rules`, …). `user.klickd` carries user
      state, not agent behaviour.
- [ ] Round-trips through both the JS and Python reference SDKs with
      byte-stable canonical form.
- [ ] Locale fields (UI language, content language) are explicit; no
      implicit en-US fallback in the file itself.

### 1.2 `student.klickd`

- [ ] Pack file is a valid v4 envelope. `student.klickd` is treated as a
      **v4.0 domain starter**, not as the v4.1 Chimera
      `x.klickd/student` `competency_pack` (those are different
      artefacts; see scope note above).
- [ ] Contains only learner-state fields appropriate to v4.0 (identity
      anchor, learning context, current goals, accessibility, gates).
      No `base_transversal_core`, no framework-anchored IRIs presented
      as normative, no carrier-vs-skill claims — those belong to v4.1.
- [ ] Personas under `examples/v4/personas/` are referenced as
      **inspiration only**, never imported wholesale, and never
      relabelled as the pack itself.
- [ ] Round-trips through both reference SDKs.
- [ ] Free-text mastery / level fields are explicitly marked
      non-normative in the pack's own comments / README — they are not
      claimed as a competency taxonomy.

### 1.3 `research.klickd`

- [ ] Pack file is a valid v4 envelope.
- [ ] Carries researcher state only: domain, current questions, working
      datasets / sources (by reference, not content), preferred output
      conventions, ethics / IRB gates. **MUST NOT** embed proprietary or
      third-party dataset contents.
- [ ] Citation conventions are described as "the researcher's preferred
      style", not as a claim about how `.klickd` itself should be cited.
      No DOI for the pack.
- [ ] No "fake catalog" of fields, journals, or institutions — every
      enumerated value is either user-supplied or sourced from an
      existing public registry that is cited in the pack README.
- [ ] Round-trips through both reference SDKs.

### 1.4 `coding.klickd`

- [ ] Pack file is a valid v4 envelope.
- [ ] Carries developer state: stack(s), conventions, repository scope,
      review expectations, tone, allowed / forbidden actions, evidence
      requirements. **MUST NOT** embed secrets, tokens, `.env` content,
      or private fixtures.
- [ ] No invented "skill catalog" of languages / frameworks presented as
      authoritative. Free-text stacks are allowed; normative
      taxonomies are not claimed.
- [ ] No agent-behaviour fields (`agent_persona`, `system_prompt`,
      `tool_policy_rewrite`, …) — those belong to a host-side skill or
      to the agent runtime, not to the carrier pack.
- [ ] Round-trips through both reference SDKs.

---

## 2. Package README update requirement

Each pack's README (the file that ships with the pack, wherever the pack
lives in the repo) MUST be updated as part of the acceptance work and
MUST cover, at a minimum:

- [ ] **What the pack is** and what it carries (one paragraph, plain
      language).
- [ ] **What it is not** — explicit "no agent behaviour", "no fake
      catalog", "no v4.1 GA claim", "no DOI" lines mirroring §0 above.
- [ ] **Version surface** — names the v4.0 surface and links to the
      authoritative SPEC section. Does not claim v4.1 / Chimera.
- [ ] **How to validate** — exact command for the JS and Python
      validators, including the schema path. Commands MUST be
      copy-pasteable and MUST work from a clean clone.
- [ ] **How to round-trip** — exact commands for JS and Python SDK
      round-trip preservation. Same copy-paste rule.
- [ ] **Where to file issues** — link to the repo's issue tracker; no
      private channel as the only option.
- [ ] **License** — restates `CC0-1.0` (or whatever the pack's actual
      license is); does not invent a license.
- [ ] **No DOI / no citation block.** README MUST NOT contain a
      `CITATION.cff` snippet for the pack, MUST NOT print a DOI, and
      MUST NOT instruct the reader to "cite this pack as …".

If the pack does not yet have a README, creating one that satisfies the
points above is part of acceptance. README work is **not** optional.

---

## 3. Tests to run

These tests MUST pass locally **and** in CI on the same commit being
proposed for merge. A pack is not acceptable on the strength of a CI
green-tick alone if local runs differ.

- [ ] **JS validator** against the v4 schema for each of the four pack
      files:

      ```bash
      node verify_vectors.mjs       # cross-impl verifier
      # plus per-pack validation, e.g.
      node packages/@klickd/core/bin/validate.mjs path/to/user.klickd
      ```

- [ ] **Python validator** against the v4 schema for each of the four
      pack files:

      ```bash
      python verify_vectors.py
      # plus per-pack validation, e.g.
      python -m klickd.validate path/to/user.klickd
      ```

- [ ] **Round-trip preservation** in both SDKs (parse → serialise →
      compare canonical form) for each pack. Failure of round-trip on
      any single pack blocks acceptance of all four.
- [ ] **Schema-version sanity:** every pack declares the v4 envelope
      version it targets, and that version exists in the published
      schema index. No `"version": "4.1.0"`, no `"v4.1-preview"`, no
      bare `"4"` — exact strings only, drawn from the schema index.
- [ ] **Secret scan** on the diff that introduces or updates the packs
      (`git diff main…HEAD`): no API keys, no tokens, no `.env`, no
      private fixtures. Use the project's existing secret-scan tooling;
      do not skip with `--no-verify`.
- [ ] **Link check** on every pack README: no dead links, no links to
      unreleased pages, no links to a future DOI.
- [ ] **No new vectors required.** Acceptance MUST NOT depend on adding
      cross-impl vector fixtures for these packs in the same PR. If
      vectors are wanted, they ship in a follow-up PR governed by the
      vectors process — not by this checklist.

---

## 4. Site handoff after repo delivery

The `klickd.app` site work begins **only after** the pack PR(s) are
merged into `main`. This section defines the handoff gate; it does not
schedule the site work itself.

- [ ] All four pack PRs are merged into `main` and the `main` build is
      green.
- [ ] Each pack's README on `main` satisfies §2 above.
- [ ] The tests in §3 pass on `main` (not just on the PR branch).
- [ ] A short **site-handoff note** is added to the relevant roadmap or
      release-notes file (e.g. `docs/roadmap/ROAD-TO-V4-GA.md`) stating:
      - which commit on `main` the four packs are at,
      - which schema version they target,
      - which validator + SDK versions were used for §3,
      - that no DOI, no release, and no v4.1 claim is associated with
        the handoff.
- [ ] The site team is given **read-only references** (commit SHA, file
      paths, schema version) — no inline copies of pack contents in
      tickets or chat that can drift from `main`.
- [ ] The handoff explicitly states that any wording on the site
      describing these packs MUST match §0 (no fake catalog, no v4.1 GA
      claim, no DOI, no release action). Marketing copy that contradicts
      §0 blocks site go-live, regardless of design readiness.

Site shipping is then governed by its own process, outside this
checklist.

---

## 5. Acceptance sign-off

A pack (or the set of four) is **accepted** when:

- [ ] Every box in §0 is ticked.
- [ ] Every box in the relevant subsection of §1 is ticked.
- [ ] §2 (README) is ticked for the pack(s) in scope.
- [ ] §3 (tests) is ticked, with the test run linked from the PR.
- [ ] §4 (site handoff) is set up — even if site work has not started,
      the handoff gate is documented.

Acceptance is recorded **in the PR description** that merges the pack
work, by linking back to this checklist and noting any deviations. This
document itself is not rewritten per pack — it is the stable target the
PR is measured against.
