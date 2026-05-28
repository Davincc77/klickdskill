# x.klickd matrix — visual brief (draft for designers)

| | |
|---|---|
| **Status** | **Draft · NON-NORMATIVE · design brief for the public site** |
| **Audience** | Designers and front-end engineers producing the public `x.klickd` matrix visual for `klickd.app/klickdskill` and supporting press / Zenodo materials |
| **Public wording** | `x.klickd` (canonical public name). The internal codename used in the planning track is intentionally not used here and must not appear in any rendered visual. |
| **Created** | 2026-05-28 |
| **Companion** | [`X_KLICKD_SITE_COPY.md`](./X_KLICKD_SITE_COPY.md) — paste-ready copy that sits next to this visual on the public site. |
| **Not for publication** | This file is a design brief. It is not the live visual. The visual itself does not yet exist in this PR; Vince will add screenshots and final artwork later. |

> **Hard constraints.** (1) Public wording must use `x.klickd`. The internal codename is forbidden in the visual, the alt text, the file name, the export metadata, and the captions. (2) No copyrighted third-party visuals (no embedded DigComp, SFIA, NICE, ENISA, CIS, O\*NET, ESCO, LifeComp, or WEF graphics) unless the licence terms of the source clearly permit reuse. Use original diagrams and reference the source by name and canonical URL in a caption. (3) Do not overclaim coverage. The visual shows that `x.klickd` *places a competency overlay across multiple recognised frameworks* — it does not show that `x.klickd` *replaces*, *extends*, or *certifies against* any of those frameworks.

---

## 1. Purpose of the visual

The visual exists to communicate **one** idea, in one glance:

> An `x.klickd` skill can carry competencies from multiple recognised public frameworks at once. A single recognised framework — DigComp, SFIA, NICE, ESCO — gives a clean grid within its own domain. `x.klickd` places a competency overlay above and across those grids so that a real AI-assisted role is visible from every relevant angle simultaneously.

If a reader takes away anything other than that idea after one second, the visual has failed.

The visual is **not** a marketing illustration with abstract icons. It is a labelled diagram that a reviewer can audit: every framework name appears with a citation, every example anchor is real and resolvable, every legend item is defined.

---

## 2. Layout

The composition is a **stacked triptych**, top to bottom:

1. **Top tile — the `x.klickd` matrix.** A wide horizontal grid. Rows are skills (sample of 6–10 representative skills, mix of Lite and Pro). Columns are competency anchors, grouped by framework. Each cell that an anchor occupies is filled. Cells that are empty are left empty (no decorative noise). The top tile is roughly 60 % of the visual's vertical height.
2. **Connector strip.** A short connector band — typographic, not iconic — that says, in plain language: *"The same skills, viewed through each recognised framework's own matrix:"*. This sets up the comparison.
3. **Bottom strip — the recognised-framework matrices.** A row of 3–5 small original-diagram thumbnails, each labelled with the framework name and a canonical URL caption. Each thumbnail shows the **shape** of that framework's native matrix (rows / columns labelled in plain text), **not** a reproduction of the framework's own published graphic. The bottom strip is roughly 30 % of the visual's vertical height.

The top tile sits **above and visually larger** than the bottom strip. The reading order — eye drops from top to bottom — encodes the claim: the `x.klickd` overlay is broader, the recognised frameworks are foundational references underneath.

> *[Screenshot: a sketch of the stacked triptych — top tile filling roughly 60 % of the height, connector band in the middle, bottom strip of thumbnails. Vince to add later.]*

### 2.1 Top tile — `x.klickd` matrix, in detail

- **Rows (left axis):** representative `x.klickd` skill names. For the public visual, pick 8 names, balanced across Lite and Pro, and representative of different domains:
  - `language-tutor` (Lite, education)
  - `research-assistant` (Lite, knowledge work)
  - `content-drafter` (Lite, content)
  - `accessibility-reviewer` (Lite, accessibility)
  - `data-analyst` (Pro, analytics)
  - `security-incident-response` (Pro, security)
  - `ux-researcher` (Pro, product)
  - `healthcare-ai-safety-reviewer` (Pro, regulated industry)
- **Column groups (top axis), left to right:**
  - **Transversal base** — 2 columns: `LifeComp` + `WEF transversal`.
  - **General** — 1–2 columns: `ESCO`.
  - **Digital** — 1 column: `DigComp 2.2`.
  - **IT professional** — 1 column: `SFIA`.
  - **Cybersecurity** — 2 columns: `NICE` + `ENISA / CIS`.
  - **Occupational** — 1 column: `O\*NET`.
- **Cells:** filled = "this skill anchors at least one competency in this framework". Empty = "this skill does not draw on this framework". Keep cell content minimal — a small dot or filled square is enough. Detailed anchor codes can be hover/tooltip content in the live site; in the static visual, omit them to keep the eye on the pattern.
- **Caption beneath the top tile:**
  > `x.klickd` competency overlay — each skill carries competencies from a shared transversal base plus a small set of role-specific anchors. Anchors point to public canonical URLs (ESCO, DigComp, LifeComp, NICE, ENISA, CIS, SFIA, O\*NET, WEF).

### 2.2 Bottom strip — recognised-framework matrices, in detail

Render **3 to 5** small original thumbnails. Recommended baseline:

1. **DigComp 2.2** thumbnail. Rows = 5 competence areas (Information & Data Literacy, Communication & Collaboration, Digital Content Creation, Safety, Problem Solving). Columns = 4 proficiency levels (Foundation, Intermediate, Advanced, Highly Specialised). Caption: *DigComp 2.2 — EU Joint Research Centre — `https://joint-research-centre.ec.europa.eu/scientific-tools-databases/digcomp_en`*.
2. **SFIA** thumbnail. Rows = sample of skill categories (e.g. `STRATEGY & ARCHITECTURE`, `CHANGE & TRANSFORMATION`, `DEVELOPMENT & IMPLEMENTATION`, `DELIVERY & OPERATION`, `PEOPLE & SKILLS`, `RELATIONSHIPS & ENGAGEMENT`). Columns = 7 responsibility levels (1 to 7). Caption: *SFIA — Skills Framework for the Information Age — `https://sfia-online.org/`*.
3. **NICE Workforce Framework** thumbnail. Rows = sample of work-role categories (e.g. `SECURELY PROVISION`, `OPERATE & MAINTAIN`, `PROTECT & DEFEND`, `ANALYZE`, `INVESTIGATE`). Columns = work roles (abbreviated). Caption: *NICE Workforce Framework for Cybersecurity — US NIST — `https://www.nist.gov/itl/applied-cybersecurity/nice/nice-framework-resource-center`*.
4. *(Optional)* **ESCO** thumbnail. A simple "occupations × skill groups" grid. Caption: *ESCO — European Commission — `https://esco.ec.europa.eu/`*.
5. *(Optional)* **WEF Future-of-Jobs transversal** thumbnail. A simple ranked list of transversal skills. Caption: *WEF Future of Jobs — World Economic Forum — most recent edition.*

Each thumbnail must be an **original** rendering, with grid lines, plain-text row and column labels, and the caption underneath. No screenshots of the framework owners' own published graphics. No copy-paste of their colour palettes if that palette is part of their visual identity.

---

## 3. Categories

The categories that group the columns of the top tile are:

| Category | Frameworks in the category | Why it is a category |
|---|---|---|
| **Transversal base** | LifeComp, WEF transversal | Shared by every skill in the catalog — the floor of judgment, communication, learning. |
| **General** | ESCO | Broad occupational and skill anchors that cut across domains. |
| **Digital** | DigComp 2.2 | The EU's reference for digital and AI-literacy competence. |
| **IT professional** | SFIA | The standard for IT and digital professional skills at seven responsibility levels. |
| **Cybersecurity** | NICE, ENISA, CIS | Cyber work roles, EU agency guidance, and operational control references. |
| **Occupational** | O\*NET | US occupational descriptions, useful for cross-Atlantic role mapping. |

Order is fixed left-to-right. The categories are not exhaustive — additional frameworks may be added in v4.2 — but the public visual published with v4.1 must use exactly this order so that the visual matches the copy in `X_KLICKD_SITE_COPY.md`.

---

## 4. Colours

The palette is restrained on purpose. A matrix with eight competing colours becomes a colour-coding puzzle, not a competency map.

- **Base.** Neutral page background (white or near-white in light mode; near-black in dark mode).
- **Grid lines.** Subtle low-contrast grey. Never black-on-white at full contrast — that pulls the eye away from filled cells.
- **Filled cells.** A single brand-aligned accent colour. The repository's existing badge palette (`#0066CC`) is a safe default. One accent — not one per framework. The category grouping is communicated by **column groupings and category labels at the top**, not by per-cell colour.
- **Category labels.** Subdued. A small uppercase typographic label above each column group, in muted grey.
- **Caption text.** Same colour as body text, slightly smaller. Citation URLs in the caption are not styled as bright links in the static visual (they are only links in the live HTML version of the page).

**Accessibility.** The filled-cell accent must pass WCAG AA contrast against the page background. Do not rely on colour alone to communicate "filled vs empty" — the filled cells are also visually larger / shaped (e.g. solid square inside the cell, while empty cells are blank). A colour-blind reader must be able to read the matrix.

---

## 5. Source citations — placement and rules

Every recognised-framework reference in the visual must carry a citation that names the framework and links to a public canonical URL.

**Placement rules:**

1. **Top tile.** Under the caption (§2.1), list the frameworks referenced and their canonical URLs as a single line in muted small text. Example:
   > *Anchors: ESCO `esco.ec.europa.eu` · DigComp 2.2 `joint-research-centre.ec.europa.eu/scientific-tools-databases/digcomp_en` · LifeComp `joint-research-centre.ec.europa.eu/scientific-tools-databases/lifecomp_en` · NICE `nist.gov/itl/applied-cybersecurity/nice/nice-framework-resource-center` · ENISA `enisa.europa.eu` · CIS `cisecurity.org/controls` · SFIA `sfia-online.org` · O\*NET `onetonline.org` · WEF Future of Jobs (most recent edition).*
2. **Bottom strip.** Each thumbnail caption names exactly one framework and its canonical URL. No bundling.
3. **Alt text.** Every image asset must include alt text that names the visual ("x.klickd competency matrix overlaid above DigComp, SFIA, and NICE reference matrices") and explicitly notes that the thumbnails are original diagrams referencing the source frameworks by name and URL.
4. **Image file metadata (EXIF / SVG `<title>` and `<desc>`).** Include the same citation list inside the file metadata so the citation travels with the asset if it is reused elsewhere.

**What the citation must include:**

- The framework name as the owner uses it (`DigComp 2.2`, not `DIGCOMP` or `digcomp`).
- The canonical owner URL — top-level domain page is enough; a deep link is better when stable.
- A version or edition tag where the framework owner provides one (`DigComp 2.2`, `SFIA 9` *if applicable at time of publication*, `NICE Workforce Framework` etc.).
- The year of the cited edition where the framework owner publishes dated editions (e.g. WEF Future of Jobs editions).

**What the citation must NOT include:**

- Vendor or partner logos that are not part of the published framework.
- Claims of certification or endorsement.
- Re-coloured or re-styled versions of the framework owner's own logo without an explicit licence to reuse.

---

## 6. What to avoid

The visual must not:

- Embed a **screenshot of the framework owner's own published matrix** (e.g. a screenshot of the DigComp wheel, the SFIA grid, or the NICE category table). Use original diagrams that reference the framework by name and URL.
- Use a framework owner's **logo** as a tile or column header unless the owner's licence terms clearly permit reuse for this purpose. Treat the framework name as text, not as a logo lockup.
- Suggest **certification or endorsement** by any framework owner. Captions must say "anchored to" / "references", never "certified by" / "endorsed by".
- Suggest **completeness**. The matrix shows that `x.klickd` carries anchors across multiple frameworks for the **representative** skill set in the visual. It is not a claim that every `x.klickd` skill anchors in every framework.
- Use the internal codename used in the planning track. The visual must read `x.klickd` everywhere — top tile heading, file name, alt text, EXIF metadata, social-share metadata.
- Display **dated promises** about v4.2. v4.2 is "in preparation"; the visual does not put a date on it.
- Use stock-photo people or hand-shaking imagery. The visual is a labelled diagram, not a brochure.

---

## 7. How to show broader / more flexible coverage without overclaiming

The phrasing trick is: **"broader overlay" and "flexible composition"**, never "more accurate" or "replaces".

Concretely, the visual should communicate:

1. **One skill, multiple anchors.** Each row in the top tile lights up cells in more than one framework column. This is the core visual claim: a single `x.klickd` skill maps into multiple recognised frameworks simultaneously.
2. **Different skills, different anchor profiles.** Two rows in the top tile have visibly different patterns of filled cells. This makes the point that the catalog is not a one-size-fits-all template — each role anchors where it actually belongs.
3. **Native framework matrices remain valid.** The bottom strip shows each recognised framework's native shape *as-is* (in original-diagram form). The visual does not redraw their structure. The implicit message: "We did not invent a replacement; we built an overlay."

**Captions that are safe.**

- "x.klickd places a competency overlay across multiple recognised frameworks."
- "Each `x.klickd` skill anchors to public frameworks; the overlay shows multiple anchors per skill."
- "Recognised frameworks shown for reference; `x.klickd` cites them, does not replace them."

**Captions that are NOT safe.**

- "x.klickd covers more competencies than DigComp."
- "x.klickd is broader than SFIA."
- "x.klickd certifies AI assistants against ESCO."
- "x.klickd extends NICE."

The difference is the verb. "Overlay across" is safe. "More than", "broader than", "extends", "certifies" are not.

---

## 8. Export targets

The same visual is needed in three sizes:

- **Hero — wide.** ~1600 × 900 px (16:9). For the site hero in §1 of `X_KLICKD_SITE_COPY.md`.
- **Inline — medium.** ~1200 × 800 px (3:2). For the section in §4 of `X_KLICKD_SITE_COPY.md`.
- **Social / thumbnail — square.** ~1200 × 1200 px (1:1). For social previews, Zenodo upload preview, and press kits.

All three exports must include the same captions and the same source-citation strip. The square version can drop the bottom strip if space is too tight, but in that case the top tile's caption must add: *"Recognised frameworks referenced: ESCO · DigComp · LifeComp · NICE · ENISA · CIS · SFIA · O\*NET · WEF."*.

Preferred formats:

- **SVG** as source-of-truth (text remains text, citations remain searchable).
- **PNG** export for the website at 2× pixel density.
- **PDF** export for the Zenodo deposit pack.

---

## 9. Acceptance checklist (for review before Vince signs off the visual)

A reviewer (or the validator, manually) must be able to tick every box below before the visual ships on the public site.

- [ ] The visual uses `x.klickd` everywhere — heading, alt text, file name, SVG `<title>`, EXIF metadata, social-share metadata.
- [ ] The internal codename used in the planning track appears **nowhere** in the visual or its metadata.
- [ ] The top tile uses the exact column-category order in §3.
- [ ] The bottom strip contains 3 to 5 original-diagram thumbnails, each with a name + canonical URL caption.
- [ ] No copyrighted third-party visual is embedded (no framework owner's own published matrix or wheel).
- [ ] No framework owner's logo is used as a tile or column header.
- [ ] Filled cells use a single accent colour; categories are communicated by column grouping and labels, not by colour.
- [ ] The visual meets WCAG AA contrast and works for a colour-blind reader (filled cells are also shape-distinguishable from empty cells).
- [ ] Captions use the safe verbs (`overlay across`, `references`, `anchors to`) and avoid the unsafe verbs (`more than`, `broader than`, `extends`, `certifies`).
- [ ] No v4.2 date is shown. v4.2 is labelled "in preparation" or omitted from the visual.
- [ ] The disclaimer that v4.1 is not GA is either present in the same page block as the visual or linked from the caption.

> *[Screenshot: the final visual with the acceptance checklist annotations laid over it. Vince to add later.]*

---

*End of visual brief. Designers: please flag any constraint in this brief that conflicts with the live site's existing visual system, before producing artwork.*
