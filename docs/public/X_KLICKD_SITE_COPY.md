# x.klickd — public site copy (draft, paste-ready)

| | |
|---|---|
| **Status** | **Draft · NON-NORMATIVE · public-facing copy preparation** |
| **Audience** | Website team (`klickd.app/klickdskill`), press, partners, community contributors |
| **Public wording** | `x.klickd` (the canonical public name of the open competency-anchored skill namespace) |
| **Created** | 2026-05-28 |
| **Not for publication** | This file is a copy draft. It is not the live website. Nothing here triggers a release, a Zenodo deposit, an npm/PyPI publication, an IANA action, or a public announcement. |

> **Public wording lock.** All public-facing copy in this document uses `x.klickd`. The internal codename used in the planning track (see the internal planning directory; the literal codename string is intentionally not reproduced in this paste-ready draft) is intentionally **not used** here and must not appear in the published site, in PR copy aimed at the public, in slide decks for external audiences, or in Zenodo metadata.
>
> **v4.1 is not GA.** v4.1 of the open `.klickd` spec — under which `x.klickd` skills are framed — is in preparation. Until the v4.1 release is tagged, the artefacts referenced here are **candidate** material. No GA claim, no production guarantee, no recommendation to ship `x.klickd` skills into a live product unmodified.
>
> **Screenshots.** Every section that benefits from a screenshot or visual is marked `[Screenshot: …]`. Vince will add screenshots later. This task does not generate or fake any screenshots.

---

## 0. How to use this file

This document is **paste-ready copy** organised by website section. The website team can lift each section into the live site with at most light formatting changes (heading levels, link targets, image placements). The intent is:

- Section 1 (Hero) goes above the fold on `klickd.app/klickdskill` (or its successor).
- Sections 2–8 are body sections, in order.
- Section 9 (Disclaimer) is a footer block that must appear on any page that mentions v4.1 candidate skills.
- Section 10 (Source list) is a transparency block — also linked from the footer.

Every claim in this document is anchored either to a file in this repository or to a publicly available authoritative source. Reviewers should flag any sentence that is **not** so anchored.

---

## 1. Hero

### Headline

> **x.klickd — the open competency standard for AI skills.**

### Sub-headline

> A true open standard, not a prompt gallery.

### Lead paragraph

> `x.klickd` is the open, competency-anchored skill namespace built on top of the `.klickd` portable AI-identity format. Every `x.klickd` skill combines a **shared transversal competency base** with a small set of **role-specific competencies**, each mapped to a recognised framework — ESCO, DigComp, LifeComp, NICE, ENISA, CIS, SFIA, O\*NET, WEF — so that what an AI assistant is allowed to do, and what it is expected to know, is auditable against public references instead of vibes.

### Call-to-action buttons

- **Primary:** *Browse the v4.1 candidate catalog* → `/klickdskill/catalog` *(catalog page is in preparation; this CTA must be hidden until v4.1 ships).*
- **Secondary:** *Read the spec* → `/klickdskill/spec` (links to `SPEC.md` and the v4.1 RFC track once public).
- **Tertiary:** *Contribute a skill* → `/klickdskill/contribute` (links to `docs/community/`).

> *[Screenshot: hero composition with the `x.klickd` matrix tile (see `X_KLICKD_MATRIX_VISUAL_BRIEF.md`) on the right, the four-line copy on the left, and a subtle reference strip — ESCO • DigComp • SFIA • NICE • WEF — under the headline. Vince to add later.]*

---

## 2. Why `x.klickd` is different

### Section heading

> **A true open standard, not a prompt gallery.**

### Body

`x.klickd` is **not** a curated collection of prompts, a marketplace, or a wrapper around a single vendor's tool. It is an **open file format with competency anchors**:

- **Open.** CC0-licensed schema, public JSON Schemas (Draft 2020-12), strict cross-implementation test vectors, two reference SDKs (Python and TypeScript), a non-destructive payload migrator, and a public DOI on Zenodo.
- **Competency-anchored.** Every skill declares the competencies it draws on, and every competency is anchored to an authoritative public framework (ESCO, DigComp, LifeComp, NICE, ENISA, CIS, SFIA, O\*NET, WEF). No homegrown taxonomy. If a competency does not resolve to one of those frameworks, the skill is held back, not invented.
- **Auditable.** The mapping rule is published in the spec, validated by a script (`scripts/validate_v4_1_candidate_mapping.py`), and reviewable by anyone — no log-in, no NDA, no vendor account.
- **Portable.** An `x.klickd` skill is consumed via the `.klickd` portable file format. The user keeps state on their device. The skill plugs into any conformant reader. No server is required.

> A prompt gallery shows you *what to type*. `x.klickd` declares *what the assistant is competent to do, against which public standards, with which gates and human-veto rules*. The difference is the difference between a recipe blog and a food-safety code.

> *[Screenshot: a side-by-side compare — left tile: a generic "prompt gallery" listing card titles only; right tile: an `x.klickd` skill entry showing competency anchors (ESCO `b1c3…`, DigComp `1.2`, SFIA `DTAN`) and gate posture. Vince to add later.]*

---

## 3. How an `x.klickd` skill is built

### Section heading

> **Every skill = shared transversal base + role-specific competencies, mapped to public frameworks.**

### Body

Each `x.klickd` skill is composed in two layers.

**Layer 1 — shared transversal base.** Every skill carries the same transversal-competency base: meta-skills that any AI-assisted human role benefits from. These are anchored primarily to **LifeComp** (Personal, Social, Learning-to-Learn) and **WEF Future-of-Jobs** transversal categories (complex problem solving, critical thinking, active learning). The base is **shared** across the catalog so that role-specific skills inherit a common floor of judgment, communication, and learning ability rather than re-declaring it.

**Layer 2 — role-specific competencies.** On top of the transversal base, each skill adds a small set (typically 4–8 for Lite, 8–14 for Pro) of competencies that define the role. These are anchored to the **role-appropriate** public framework:

- **ESCO** (European Commission) — generic occupational and skill anchors.
- **DigComp 2.2** (EU JRC) — digital and AI-literacy competence.
- **NICE / ENISA / CIS** — cybersecurity work roles and controls.
- **SFIA** — IT and digital professional skills.
- **O\*NET** — US occupational descriptions.
- **WEF Future-of-Jobs** — transversal skills outlook.
- **LifeComp** — personal, social, learning-to-learn competence.

The mapping rule is strict: a competency that does not resolve to one of those frameworks does **not** ship. A skill that cannot find role-specific anchors stays a candidate; it does not get promoted by improvisation.

Each skill also declares its **gate posture** (raise-only, human-veto, who owns final decisions) and its **source / evidence policy** (where verification artefacts are expected to come from, pointer-only by default). These are inherited from `.klickd` v4 conventions (RFC-002, RFC-003).

> *[Screenshot: a diagram of a single skill — the shared transversal base as a foundation slab, the role-specific competencies stacked on top, and a strip showing the public-framework logos each anchor resolves to. Vince to add later. Use the layout described in `X_KLICKD_MATRIX_VISUAL_BRIEF.md` §2.]*

---

## 4. The `x.klickd` competency matrix

### Section heading

> **One matrix. Broader and more flexible than any single framework.**

### Body

A single recognised framework — say, DigComp 2.2 — gives you a clean grid of digital-competence areas (information, communication, content creation, safety, problem solving) and proficiency levels. NICE gives you a clean grid of cybersecurity work roles. SFIA gives you a clean grid of IT-professional skills at seven responsibility levels.

Each of those frameworks is excellent **inside its own domain** and limited **outside its domain**. A cybersecurity incident-response role is barely visible in DigComp; an AI-literacy competence is barely visible in NICE; a learning-to-learn competence is barely visible in SFIA.

The `x.klickd` matrix is a **competency overlay** that places each `x.klickd` skill against the relevant public frameworks at once, so that a single role is visible from every angle that matters:

- For a `data-analyst` skill, the matrix shows the relevant ESCO occupation anchor, the SFIA `DTAN` (Data Analysis) anchor, the DigComp 1.2 / 3.2 cells, and the LifeComp transversal cells.
- For a `security-incident-response` skill, the matrix shows the relevant NICE work-role anchor, the ENISA / CIS control references, the SFIA `SCAD` (Security Administration) and related anchors, and the LifeComp transversal cells.
- For an `accessibility-reviewer` skill, the matrix shows the relevant DigComp 3.1 / 2.6 cells, the WEF transversal cells, and the relevant ESCO anchors.

The intent is **not** to redraw or replace those frameworks. The intent is to show that one `x.klickd` skill can carry competencies across **multiple** frameworks at once, in a way no single framework's native matrix can. See `X_KLICKD_MATRIX_VISUAL_BRIEF.md` for the visual specification — including how to show recognised framework matrices alongside, and above/near, the `x.klickd` matrix to make the broader coverage visible without overclaiming.

> **What this does not mean.** `x.klickd` does not certify against ESCO, DigComp, NICE, ENISA, CIS, SFIA, O\*NET, or WEF. Those frameworks have their own owners and their own certification regimes. `x.klickd` cites them, anchors to them, and links back to the public canonical URLs. No endorsement is claimed.

> *[Screenshot: the `x.klickd` matrix tile (top) shown above a strip of recognised-framework matrix thumbnails — DigComp, SFIA, NICE — with a caption that reads "x.klickd places a competency overlay across all of these at once". Diagrams must be original (no copyrighted third-party visuals unless clearly allowed). Vince to add later. Sourcing rules in `X_KLICKD_MATRIX_VISUAL_BRIEF.md` §5.]*

---

## 5. Two tiers — `Lite` and `Pro`

### Section heading

> **Lite skills for breadth. Pro skills for depth.**

### Body

Every `x.klickd` skill ships in one of two tiers.

**Lite (≤ 12 KB, ≤ 900 tokens estimated).** Lite skills are compact, broad-coverage skills designed to load cheaply into any assistant. They carry the shared transversal base and a tight set of role-specific competencies. Lite skills cover the most common AI-assisted roles — research assistant, content drafter, language tutor, basic accessibility reviewer — and are the right starting point for users who want capability without a heavy footprint.

**Pro (≤ 24 KB, ≤ 1 350 tokens estimated, compact-index loading).** Pro skills are deeper, role-specialised skills with a larger and more selective competency set. They use a **compact-index + lazy-body** loading strategy so the assistant only pulls the full body when it needs it. Pro covers AI-assisted specialist roles — data analyst, security incident response, UX researcher, product manager, technical writer, learning designer, sustainability analyst, healthcare AI safety reviewer, edge AI operator, and more.

Both tiers obey the same competency-anchor rule: shared transversal base + role-specific competencies, every anchor in a recognised public framework.

> *[Screenshot: a two-column tile — left column "Lite" with a thumbnail list of Lite skill names; right column "Pro" with a thumbnail list of Pro skill names. Both columns show the size ceiling under the heading. Vince to add later.]*

---

## 6. Bundles

### Section heading

> **Pre-composed skill bundles for common contexts.**

### Body

A user rarely needs one skill in isolation. The `x.klickd` catalog ships **bundles** — small, curated groups of skills that work well together for a common context:

- **Learner bundle.** Language-tutor + research-assistant + content-drafter (Lite). For students starting from a clean device.
- **Maker bundle.** Content-drafter + accessibility-reviewer + UX-researcher (Lite + Pro). For solo makers shipping accessible work.
- **Ops bundle.** Devops-operator + security-incident-response + customer-support-operator (Pro). For small ops teams.
- **Analyst bundle.** Data-analyst + finance-analyst + sustainability-analyst (Pro). For analysts working across domains.
- **Safety bundle.** Healthcare-AI-safety-reviewer + edge-AI-operator + security-incident-response (Pro). For teams shipping AI in regulated or constrained environments.

Bundles are **composition shortcuts**, not new skills. Every skill in every bundle is the same skill that ships standalone — same competencies, same gates, same anchors. A bundle is a curated subset of the catalog, not a re-encoding.

> *[Screenshot: five bundle tiles laid out in a 3-2 grid, each tile showing the bundle name, the skills it contains as small chips, and a "compose this bundle" CTA. Vince to add later.]*

---

## 7. v4.2 in preparation

### Section heading

> **What is coming next.**

### Body

The next iteration of the open `.klickd` track — **v4.2** — is **in preparation**. It is expected to bring:

- **More generic Lite skills**, broadening the coverage of common AI-assisted roles that any user can pick up without a specialist background.
- **More specialised Pro skills**, deepening the coverage of specialist roles (e.g. additional regulated-industry safety reviewers, additional ops and platform roles, additional analyst roles).

No release date is promised. v4.2 will be tagged when its candidate catalog is mapped, validated, and reviewed — exactly the same gating ladder as v4.1. Until then, anything labelled `v4.2` in the repository is planning material, not a release.

> *[Screenshot: a small "roadmap" tile showing v4.0.0 (released), v4.1 (in preparation), v4.2 (in preparation), with no dates. Vince to add later.]*

---

## 8. Transparency and sources

### Section heading

> **Public sources, public anchors, public test vectors.**

### Body

`x.klickd` is built on public material. The site links out to:

- The **`.klickd` spec** — `SPEC.md` and the v4.1 RFC track (`docs/rfcs/RFC-009-*`) — for the file format, schema, and competency-mapping rules.
- The **canonical framework registry** — the in-repo list of admissible competency sources (ESCO, DigComp, LifeComp, NICE, ENISA, CIS, SFIA, O\*NET, WEF) with their canonical public URLs. *(Copy team: link the rendered version of the registry once it has a public URL; do not link the internal planning-track path.)*
- The **reference SDKs** — Python (`klickd` on PyPI) and TypeScript (`@klickd/core` on npm) — published once each release is GA.
- The **strict test vectors** — for cross-implementation conformance — in this repository under `tests/`.
- The **Zenodo deposit** — for the canonical, citable spec snapshot. See `X_KLICKD_ZENODO_DRAFT.md` for the public DOI copy.

Every framework anchor in every skill carries a canonical URL. A reader who wants to verify a competency anchor can click through to the source. No anchor is an opaque internal code.

> *[Screenshot: a "transparency" tile with three tiles inside — "Spec on GitHub", "DOI on Zenodo", "Test vectors" — each linking out. Vince to add later.]*

---

## 9. Disclaimer (footer block, MUST appear on any page that references v4.1)

> **Disclaimer.** `.klickd` v4.1 — the version under which the `x.klickd` candidate catalog is framed — is **not yet generally available**. Skill artefacts referenced on this site are **candidates**. They are published openly so that competency mappings and framework anchors can be reviewed in public, but they are not GA, are not recommended for unmodified production use, and do not carry compatibility or stability guarantees until v4.1 is tagged and a corresponding Zenodo deposit is minted. v4.2 is in preparation and will bring more generic Lite skills and more specialised Pro skills; no release date is promised.

> **No certification claim.** Anchors to ESCO, DigComp, LifeComp, NICE, ENISA, CIS, SFIA, O\*NET and WEF are **references**, not certifications. The frameworks have their own owners and their own certification regimes. `x.klickd` cites and links to them; no endorsement by those bodies is claimed.

> **No third-party visuals reproduced.** All diagrams and matrices shown on this site are original work referencing the source frameworks by name and URL. No copyrighted third-party visuals are embedded unless their licences clearly permit it.

---

## 10. Source list (for the footer / About page)

The site footer should link to the following public sources. The list mirrors the canonical framework registry, with the relevant top-level public URL for each entry. Reviewers should re-verify these URLs before publication.

- **ESCO** — European Commission. `https://esco.ec.europa.eu/`
- **DigComp 2.2** — EU Joint Research Centre. `https://joint-research-centre.ec.europa.eu/scientific-tools-databases/digcomp_en`
- **LifeComp** — EU Joint Research Centre. `https://joint-research-centre.ec.europa.eu/scientific-tools-databases/lifecomp_en`
- **NICE Workforce Framework for Cybersecurity** — US NIST. `https://www.nist.gov/itl/applied-cybersecurity/nice/nice-framework-resource-center`
- **ENISA** — European Union Agency for Cybersecurity. `https://www.enisa.europa.eu/`
- **CIS Controls** — Center for Internet Security. `https://www.cisecurity.org/controls`
- **SFIA** — Skills Framework for the Information Age. `https://sfia-online.org/`
- **O\*NET** — US Department of Labor. `https://www.onetonline.org/`
- **WEF Future of Jobs** — World Economic Forum. `https://www.weforum.org/reports/the-future-of-jobs-report-2023/` *(or the most recent edition at time of publication).*

---

## 11. Public wording rules (for the copy team)

When editing this copy or extending the site, the following wording rules apply:

1. **Use `x.klickd`** in every public-facing reference to the competency-anchored skill namespace. Do **not** use the internal codename used in the planning track (the literal codename string is intentionally not reproduced here; see the internal planning directory for the actual paths). The internal codename is for internal planning only.
2. **Use the tagline `A true open standard, not a prompt gallery.`** as the sub-headline. Do not paraphrase it for variety — it is a positioning lock.
3. **Always pair the catalog mention with the disclaimer in §9** until v4.1 is GA. Do not strip the disclaimer for layout reasons.
4. **Never claim a partnership, certification, endorsement, or accreditation** from any framework owner (EU Commission, NIST, ENISA, CIS, SFIA Foundation, US Department of Labor, World Economic Forum). The relationship is *references and anchors*, not partnership.
5. **Avoid screenshots that embed copyrighted third-party visuals** unless their licence clearly permits it. Use original diagrams referencing the source by name and URL. See `X_KLICKD_MATRIX_VISUAL_BRIEF.md` §5 for the sourcing rules.
6. **Do not promise dates for v4.2.** Say "in preparation". If a release date becomes firm, update this copy in PR review.

---

## 12. Open questions for the website team

The following items are not decided in this copy draft and should be resolved with the website team before publication.

- **URL slug.** `klickd.app/klickdskill` is the current page slug. If the public catalog gets its own sub-page (`/klickdskill/catalog`), the CTA in §1 should be wired to it.
- **Catalog rendering.** Whether the public catalog renders the candidate artefacts directly from the internal candidate-catalog location or from a curated public mirror. The site copy here is agnostic and works either way.
- **Bundle naming.** The bundle names in §6 are draft labels. Vince may want to revise them (e.g. "Learner pack", "Maker pack").
- **Roadmap depth.** §7 currently lists only v4.0.0, v4.1, v4.2. If the public roadmap should show more (e.g. v5 outlook), Vince to expand.

---

*End of paste-ready copy draft. Reviewers: please flag any sentence that is not anchored to a file in this repository or to a public framework URL.*
