# v4 Media Test Pack — Marketing Video Fixtures (DRAFT, NON-NORMATIVE)

| | |
|---|---|
| **Document** | v4 Media Test Pack |
| **Status** | **Draft — NON-NORMATIVE** |
| **Targets** | [RFC-001 `media_profile` v1](./RFC-001-media-profile-v1.md) · [RFC-002 `verification_gates` v1/v2](./RFC-002-verification-gates.md) |
| **Author** | Vince C. (Klickd / Luxlearn, Luxembourg) |
| **Created** | 2026-05-22 |
| **Scope** | Fixture prep + design only. **No paid media generated. No publication. No production URIs beyond the public `klickd.app` CTA.** |

> **This document is non-normative.** It exists to exercise the v4-A / v4-B RFC fields against two concrete, *hypothetical* marketing video projects, so reviewers can attack the **right** target. Nothing here is a brief for an actual paid render. Real video generation requires a separate explicit approval from Vince and a documented model/credit decision (see [§6 Approval gate](#6-approval-gate)).

---

## 1. Why two projects?

The v4 RFCs (`media_profile`, `verification_gates`) are the first parts of the format to touch **outbound, public-facing artefacts**. To stress-test them, we need fixtures for the two distinct surfaces Klickd would plausibly market:

- **Project A — `.klickd / klickdskill`.** The portable, encrypted, AI-memory **format and SDK**. Audience: developers, researchers, AI builders. CTA: GitHub / Zenodo / npm / PyPI.
- **Project B — `klickd.app`.** The privacy-first **AI learning product** (Kai, Proof Mode, multilingual Europe / Luxembourg). Audience: parents, students, schools. CTA: `https://klickd.app`.

The two projects share zero copy and differ in audience, voice, gate profile, and licensing posture. If a single fixture pair can express both, the RFC fields are doing their job.

## 2. What this test pack contains

For each project, under [`examples/v4-media-test-pack/`](./examples/v4-media-test-pack/):

1. A **`media_profile` fixture** (JSON) — synthetic entries only, placeholder hashes, no real bytes, no third-party URIs except the project's own public CTA.
2. A **`verification_gates` fixture** (JSON) — v1 core + v2 draft fields (claim grounding, contract tests, reversibility, blast radius). Gates set to match the project's audience and risk.
3. A **storyboard outline** (in this doc, §4) — shot list, runtime, intent. No image/video bytes.
4. A **generation prompt draft** (in this doc, §5) — the prose a producer would feed a model *if* approval to render were granted.
5. **Rights / provenance placeholders** — declared in the `media_profile.consent` and `producer` fields; concrete licences left as `PLACEHOLDER_*`.
6. **Pass/fail criteria** — what a reviewer should look at to decide whether the RFC fields are expressive enough.

What this test pack does **not** contain:
- No generated images, audio, or video.
- No real-person likeness, voice sample, name, or biometric.
- No private URIs (S3, internal CDNs, drafts).
- No API tokens, credentials, signing keys.
- No `klickd.app` content beyond the public CTA URL.
- No schema changes. No SDK changes. No SPEC.md changes.

## 3. Synthesis principles (apply to both projects)

The fixtures follow these rules so any future render is automatically a *safer* render:

1. **Synthetic-only subjects.** No identifiable real person. Faces/voices, if depicted, are explicitly typed as `synthetic` in `producer.kind` and gated by `factual_claim_about_person`.
2. **No likeness drift.** Even when a synthetic narrator is used, gates treat them as a `factual_claim_about_person` candidate so the agent must not silently graft them onto a real identity.
3. **Provenance placeholders, not real licences.** Every `consent.purposes` is set; every `producer` is declared; every licence string is `PLACEHOLDER_LICENCE_*`. A real render fills these in *before* publishing.
4. **CTA is the only outbound URL.** Project A points at GitHub / Zenodo / npm / PyPI (all public registries). Project B points at `https://klickd.app` (public landing). Nothing else is referenced.
5. **Multilingual where it matters.** Project B carries `fr-LU`, `en-LU`, `de-LU`, `lb-LU` voice slots as placeholders to exercise per-language consent. Project A keeps a single `en` slot — its audience is global English-speaking devs.
6. **Gates favour the user, not the marketer.** `public_post` is never `silent`. `factual_claim_about_person` is at least `block` for any named human. Claims about version numbers / DOI / release dates pass through `claim_sources.records[]` and `contract_tests` before any post.

## 4. Storyboards (outline only — no rendered bytes)

### 4.1 Project A — `.klickd / klickdskill` marketing video

**Working title:** *"One soul. Any model. Any body."*
**Target runtime:** 45–60 s.
**Aspect ratio:** 16:9 master, 9:16 vertical recut.
**Tone:** Quiet, technical, confident. No hype voiceover.

| # | Shot | Visual | Audio | Notes |
|---|---|---|---|---|
| 1 | 0:00–0:06 | Black. A single `.klickd` filename fades in, then the BLAKE3 hash crawls underneath. | Soft synth tone. | Establishes: "this is a file, and it's verifiable." |
| 2 | 0:06–0:16 | Abstract animation: a portrait silhouette walks out of one model logo (synthetic block) and into another, carrying a small encrypted "box" with them. | Narrator (synthetic en voice): *"Your memory. Your context. Your soul. Encrypted, portable, model-agnostic."* | Silhouette MUST be unmistakably synthetic — geometric, not photoreal. |
| 3 | 0:16–0:28 | Diagram morph: text identity → knowledge → ethics → media. RFC-001 / RFC-002 references shown subtly. | Narrator: *"v4 adds media context — voice, image, document — without becoming a media container."* | The diagram is the product. No people. |
| 4 | 0:28–0:40 | Three side-by-side panels: a GitHub repo, a Zenodo DOI badge, a `pip install klickd` / `npm i @klickd/core` shell. | Narrator: *"Open. Audited. CC0-compatible."* | Real registry icons are public marks; treat them as `claim_status: inspected` with a `tool:pypi` / `tool:zenodo` source record. |
| 5 | 0:40–0:55 | Closing card: the `.klickd` logo, the four CTAs, the licence line. | Narrator: *"klickdskill on GitHub. klickd on PyPI and npm. DOI on Zenodo."* | No `klickd.app` here — Project A's CTA set is registry-only. |
| 6 | 0:55–1:00 | Hold on the licence line. | Silence. | The licence is the closing image. |

**Hard rules for Project A:**
- No human face, real or implied photoreal.
- No screen recording of a private repo, branch, or unmerged PR.
- Version numbers / DOIs MUST come from `claim_sources.records[]` with `claim_status: executed`.

### 4.2 Project B — `klickd.app` marketing video

**Working title:** *"Kai helps you learn — not cheat."*
**Target runtime:** 30–45 s.
**Aspect ratio:** 9:16 master (mobile-first), 16:9 recut.
**Tone:** Warm, calm, parent-trustworthy. Multilingual (EU / Luxembourg).

| # | Shot | Visual | Audio | Notes |
|---|---|---|---|---|
| 1 | 0:00–0:05 | A synthetic, abstract "student" silhouette and a glowing "Kai" companion side by side. No faces. | Soft ambient. A child's *synthetic* humming. | The humming MUST be tagged `producer.kind: synthetic`. No real child voice. |
| 2 | 0:05–0:15 | Split screen: the student writes a homework question; Kai responds with *guiding* questions, not answers. A small "Proof Mode" badge ticks "verified". | Narrator (synthetic en-LU / fr-LU / de-LU / lb-LU, language by version): *"Kai helps you learn — not cheat."* | Per-language voice slot is what `media_profile` exercises. |
| 3 | 0:15–0:25 | A parent (synthetic silhouette) sees a transparent log of the session on their phone. | Narrator: *"Parents see what's checked, what's guessed, what's wrong — with proof."* | The phone UI shown MUST be a stylised mock, not a screen recording of the real app. |
| 4 | 0:25–0:35 | Map of Europe with Luxembourg highlighted; four language captions flash. | Narrator: *"Privacy-first, EU-hosted, made in Luxembourg."* | Geography claims pass through `factual_claim_with_date`-style grounding for current hosting facts. |
| 5 | 0:35–0:45 | Closing card: `klickd.app`, the four language flags, parent-consent line. | Narrator: *"klickd.app."* | The **only** outbound URL in this video. |

**Hard rules for Project B:**
- No real child face, voice, name, or school logo.
- "Made in Luxembourg" / "EU-hosted" claims MUST have a matching `claim_sources.records[]` entry with `claim_status: inspected` (e.g. company registry) before any public render.
- The "Proof Mode" badge MUST resolve to a real product feature; if it doesn't yet, the claim moves to `claim_status: assumed` and a `block` gate fires.

## 5. Generation prompt drafts (text only)

These are the prose briefs a producer would feed a video model *if* §6 approval is granted. They are intentionally short and synthesis-friendly. **Do not feed these to a production model without §6 approval.**

### 5.1 Project A prompt draft

```
60-second technical brand film for a developer-facing format called .klickd
(GitHub: Davincc77/klickdskill). Mood: quiet, confident, slightly cryptographic.
No human faces. No photoreal subjects. Visuals are abstract geometry,
filename animations, and clean register icons. Voiceover is a single
synthetic English narrator, calm cadence, no hype.

Beats:
1. A filename and BLAKE3 hash appear on black.
2. An abstract silhouette walks between two model logos carrying an encrypted
   box (symbolising portable AI memory).
3. A diagram morphs across identity → knowledge → ethics → media context.
4. Three panels: GitHub repo card, Zenodo DOI badge, pip/npm install commands.
5. Closing card with CTAs: GitHub, PyPI, npm, Zenodo. Licence line under it.

Avoid: any human likeness, any real-person voice, any screen recording of
private repositories, any mention of klickd.app (this film is registry-only).
```

### 5.2 Project B prompt draft

```
40-second consumer brand film for an EU AI learning app called Kai, at
klickd.app. Mood: warm, calm, parent-trustworthy. Audience: parents and
students in Luxembourg and the EU. No human faces — characters are
stylised, geometric silhouettes only. Voiceover is a synthetic narrator
in one of: en-LU, fr-LU, de-LU, lb-LU (four language variants of the
same film). A short synthetic humming bed under voiceover.

Beats:
1. A student silhouette and a glowing companion "Kai" appear side by side.
2. The student writes a homework question; Kai responds with guiding
   questions, never the final answer. A "Proof Mode" badge ticks "verified".
3. A parent silhouette views a transparent session log on a stylised phone.
4. A map of Europe with Luxembourg highlighted; four language captions.
5. Closing card: klickd.app, four language flags, parent-consent line.

Avoid: any real child voice, any real face or school logo, any screen
capture of the real app UI (use stylised mockups only), any claim that
isn't backed by a claim_sources.records entry — including
"EU-hosted" and "made in Luxembourg".
```

## 6. Approval gate

This document is the *only* artefact the test pack produces autonomously. Any of the following require **explicit Vince approval** and a documented decision in `error_journal[]` (or its successor):

- Running either prompt against a paid video model.
- Generating any audio (voice or music) for either project.
- Swapping the synthetic silhouettes for any face — synthetic *or* real.
- Replacing any `PLACEHOLDER_*` licence or consent value with a real one.
- Publishing the fixtures or the rendered video anywhere outside this repo.
- Touching `klickd.app` production in any way.

Approval is per-project: approving Project A does not approve Project B.

## 7. Pass / fail criteria for the test pack

A reviewer can ship the test pack (without rendering anything) if all of the following hold. The criteria mirror RFC-002 §8b.4 `success_criteria` style.

| # | Criterion | Pass when |
|---|---|---|
| TP-001 | Fixtures parse as JSON. | `python -c "import json,sys;[json.load(open(p)) for p in sys.argv[1:]]"` exits 0 for both fixture files. |
| TP-002 | No real-person identifiers. | No names, emails, biometrics, school logos, or screen-capture URIs appear. Synthetic narrators are typed `producer.kind: synthetic`. |
| TP-003 | No secrets / tokens. | `grep -REn '(AKIA|ASIA|ghp_|gho_|sk-|xoxb-|BEGIN [A-Z]+ PRIVATE KEY)' docs/rfcs/examples/v4-media-test-pack/` returns nothing. |
| TP-004 | Only declared outbound URLs. | Project A references GitHub / Zenodo / npm / PyPI public hosts only. Project B references `https://klickd.app` only. |
| TP-005 | Every `media_profile` entry has `hash`, `consent.purposes`, and a typed `producer`. | RFC-001 V-002, V-003, V-008 are satisfied by the fixture as written. |
| TP-006 | Every `verification_gates.gates[]` entry has `id`, `action_class`, `level`, `reason`. | RFC-002 §5.1 shape is honoured. |
| TP-007 | `public_post` is never `silent` in either project. | Audit `gates[]` for `public_post`; level is one of `confirm`, `block`, `require-owner`. |
| TP-008 | `factual_claim_about_person` is `block` for any named human. | Both projects use synthetic narrators, so this gate is `block` and there is no opt-down. |
| TP-009 | All factual claims in the storyboard map to a `claim_sources.records[]` slot. | Version numbers, DOIs, hosting facts, "made in Luxembourg" each have a `records[]` slot with `claim_status` set. |
| TP-010 | Contract tests bound to high-risk classes are listed. | At minimum `pypi-version-fresh`, `zenodo-doi-resolves`, `media-likeness-consent` exist where the storyboard would need them. |
| TP-011 | Reversibility / blast radius declared. | Both fixtures set `reversibility.by_action_class.public_post = costly_to_reverse` and `blast_radius.by_action_class.public_post = public`. |
| TP-012 | No production URIs beyond the public CTA. | No S3, internal CDN, draft branch, or unmerged PR URL appears anywhere in the test pack. |

A failure on any criterion blocks the PR; it does not block the render — there is no render planned.

## 8. Layout

```
docs/rfcs/
  v4-media-test-pack.md                          (this document)
  examples/
    v4-media-test-pack/
      README.md                                  (short pointer, NON-NORMATIVE banner)
      project-a-klickdskill.media_profile.json   (synthetic fixture)
      project-a-klickdskill.verification_gates.json
      project-b-klickd-app.media_profile.json
      project-b-klickd-app.verification_gates.json
```

All five JSON files are NON-NORMATIVE and do not validate against any schema in `schema/` or `schemas/`. Hashes, DOIs, and licence strings are placeholders.

## 9. Open questions

1. **Should Project B carry one `media_profile` entry per language, or one entry with a `language` discriminator?** The fixture takes the first approach (four `voice-narrator-<lang>` entries) because RFC-001 V-005 forbids duplicate `id` and per-language consent is cleaner. Reviewer call.
2. **Where does the synthetic-narrator declaration belong** — `producer.kind: "synthetic"` (a new value alongside `human` / `model`)? RFC-001 §5 lists only `human` and `model`. The fixture uses `producer.kind: "model"` with `producer.name: "synthetic-narrator-<lang>"` as a pragmatic placeholder; this is exactly the kind of small gap a test pack is supposed to surface.
3. **Should `contract_tests` reference real test runners now**, or stay declarative names? The fixtures stay declarative (RFC-002 §8b.3); v4-B SDK resolution is future work.
4. **Project A and Project B share no copy.** Is there a shared "Klickd brand" gate file we should extract? Probably not yet — premature abstraction for two fixtures.
