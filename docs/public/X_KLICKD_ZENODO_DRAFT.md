# x.klickd — Zenodo deposit draft (public DOI copy)

| | |
|---|---|
| **Status** | **Draft · NON-NORMATIVE · public deposit copy preparation** |
| **Audience** | Maintainer (Vince) preparing the next Zenodo deposit when v4.1 ships GA and the `x.klickd` catalog is published. |
| **Public wording** | `x.klickd` (canonical public name). The internal codename used in the planning track must not appear in any public Zenodo metadata. |
| **Created** | 2026-05-28 |
| **Companion** | [`X_KLICKD_SITE_COPY.md`](./X_KLICKD_SITE_COPY.md) · [`X_KLICKD_MATRIX_VISUAL_BRIEF.md`](./X_KLICKD_MATRIX_VISUAL_BRIEF.md) · [`/.zenodo.json`](../../.zenodo.json) — current GA Zenodo metadata for v4.0.0. |
| **Not for publication** | This file is a deposit draft. It is **not** a Zenodo deposit. No DOI is minted by this PR. No file in this PR triggers a release. The deposit only happens when Vince explicitly creates it from a tagged release. |

> **Hard locks.** (1) Public wording must use `x.klickd`. The internal codename used in the planning track is forbidden in every Zenodo field — title, description, keywords, notes, related-identifier titles. (2) v4.1 is **in preparation**; until it is tagged, this draft is *staged* metadata, not the metadata of an actual deposit. (3) No GA claim until v4.1 is released. The "non-GA" preview language in §6 below must be retained until the GA release is cut. (4) No copyrighted third-party material is uploaded. Diagrams in the deposit are original; sources are cited by name and canonical URL (mirror of `X_KLICKD_MATRIX_VISUAL_BRIEF.md` §5).

---

## 0. How to use this file

This draft is structured to map **one-for-one** onto the fields of a Zenodo software deposit. When the time comes to prepare the actual deposit:

1. Cut the GA release tag in this repository (`v4.1.0` once accepted).
2. Update `/.zenodo.json` from this draft (or paste fields into the Zenodo web UI, depending on Vince's preference).
3. Verify the related-identifier DOIs (`isVersionOf` for the concept DOI; `isNewVersionOf` for the previous version DOI).
4. Upload the deposit-bundle file list (§7).
5. Re-verify the disclaimer block (§6) before publishing — drop the non-GA language if v4.1 has been tagged GA at this point.

No field in this draft is final until Vince signs off and the release tag exists.

---

## 1. Title

> **`.klickd` v4.1 — `x.klickd` competency-anchored skill catalog**

Notes:

- Use the dotted name `.klickd` and `x.klickd` exactly as shown — that is the public lock.
- Do **not** include the internal codename anywhere in the title. The literal codename string is intentionally not reproduced in this draft; the rule is: only public wording (`.klickd`, `x.klickd`) appears in the deposit title.
- The minor track is v4.1; the format wire envelope remains `klickd_version 3.0` and is signalled inside the payload via `payload_schema_version 4.1`. The title says `v4.1` to match the release tag; the wire detail belongs in the description.

---

## 2. Version

> **4.1.0** *(to be confirmed at release time; if the release tag becomes `v4.1.0-rc.N` instead of `v4.1.0`, use that string verbatim).*

---

## 3. Upload type

> **software**

The deposit includes a normative specification document, two reference SDKs, JSON Schemas, strict cross-implementation test vectors, the migrator, the v4.1 candidate skill catalog (`x.klickd` artefacts), and original diagrams. The upload type remains `software`, consistent with `v4.0.0` precedent in `/.zenodo.json`.

---

## 4. Description (plain text, no HTML — Zenodo portability)

> `.klickd` is an open-source security and continuity layer for AI: a portable, encrypted file format for user context that travels across AI models, agents and sessions. The `x.klickd` namespace, introduced in v4.1, is the open, competency-anchored skill catalog built on top of the `.klickd` portable file format. Every `x.klickd` skill combines a shared transversal competency base with a small set of role-specific competencies, each anchored to a recognised public framework: ESCO (European Commission), DigComp 2.2 (EU Joint Research Centre), LifeComp (EU Joint Research Centre), NICE Workforce Framework for Cybersecurity (US NIST), ENISA (European Union Agency for Cybersecurity), CIS Controls (Center for Internet Security), SFIA (Skills Framework for the Information Age), O*NET (US Department of Labor), and WEF Future of Jobs (World Economic Forum). The mapping rule is strict: no homegrown taxonomy, every anchor links to a public canonical URL, and a candidate that does not resolve to one of those frameworks is held back, not invented. The catalog ships in two tiers — Lite (compact, broad coverage) and Pro (deeper, role-specialised, compact-index + lazy-body loading) — with size budgets and token-cost protections enforced by a validator script in the repository. The `.klickd` wire envelope remains klickd_version 3.0 with unchanged AES-256-GCM and Argon2id key derivation; v4.1 is signalled inside the payload via payload_schema_version 4.1. This deposit contains the reference specification (SPEC.md and the v4.1 RFC track), the reference Python and TypeScript SDKs, the JSON Schemas (Draft 2020-12), the cross-implementation strict test vectors, the non-destructive payload migrator, the v4.1 candidate `x.klickd` skill artefacts under examples/v4.1/, the validator script, and original diagrams illustrating the `x.klickd` competency overlay. This deposit does not claim certification by any framework owner; anchors to ESCO, DigComp, LifeComp, NICE, ENISA, CIS, SFIA, O*NET and WEF are references with canonical URLs, not endorsements. This deposit does not claim universal compatibility across all AI products. Until v4.1 is tagged as the general-availability release, the artefacts here are explicitly candidates and are not recommended for unmodified production use. A true open standard, not a prompt gallery.

Notes on the description copy:

- Plain text only. No HTML, no Markdown bullets, no asterisks for bold — Zenodo renders the description as plain text and these characters degrade portability.
- The tagline `A true open standard, not a prompt gallery.` is included at the end. This is a positioning lock from the public copy.
- The internal codename used in the planning track is **not** mentioned.
- The disclaimer that v4.1 is not GA is in the description and **must be retained** until the GA release is cut.

---

## 5. Creators

> Cirilli, Vincenzo (.klickd) — .klickd / klickd.app, Luxembourg

Mirrors the creator entry in `/.zenodo.json` for `v4.0.0`. If the contributor list grows by v4.1, Vince to update before the deposit is created.

---

## 6. Notes (non-GA disclaimer + sourcing)

> v4.1 of `.klickd` is the minor release that introduces the `x.klickd` competency-anchored skill catalog. Until v4.1 is tagged as the general-availability release, all `x.klickd` skill artefacts in this deposit are explicitly candidates and are not recommended for unmodified production use. v4.2 is in preparation and is expected to bring more generic Lite skills and more specialised Pro skills; no release date is promised. Framework anchors in the catalog reference public canonical URLs of the source frameworks (ESCO, DigComp, LifeComp, NICE, ENISA, CIS, SFIA, O*NET, WEF); no certification or endorsement by any framework owner is claimed. Diagrams included in this deposit are original works; no copyrighted third-party graphics are reproduced unless their licence terms clearly permit reuse. Description is plain text (no HTML) for portability.

---

## 7. File list (deposit bundle)

The deposit-bundle ZIP should contain (paths relative to the repository root):

- `SPEC.md` — normative v4.1 specification (post-merge of the relevant RFCs into `SPEC.md`).
- The v4.1 planning RFC under `docs/rfcs/` — see §7.1 below; this RFC carries the internal codename in its filename and is a candidate for **exclusion or rename** before the deposit bundle is sealed.
- `docs/public/X_KLICKD_SITE_COPY.md` — public site copy (this directory).
- `docs/public/X_KLICKD_MATRIX_VISUAL_BRIEF.md` — visual brief (this directory).
- `docs/public/X_KLICKD_ZENODO_DRAFT.md` — this file (the deposit draft itself, included for archival).
- `schemas/` — strict JSON Schemas (Draft 2020-12) for v4.1.
- `schema/` — legacy / aliased schema directory if still required by readers.
- `packages/` — Python (`klickd`) and TypeScript (`@klickd/core`) reference SDKs.
- `tests/` — strict cross-implementation test vectors.
- `verify_vectors.py`, `verify_vectors.mjs` — cross-implementation verifiers.
- `save_klickd.py`, `load_klickd.py` — reference CLI scripts.
- The v4.1 candidate `x.klickd` artefact tree under `examples/v4.1/` — see §7.1 below; the in-repo subdirectory carries the internal codename and **must be renamed inside the deposit bundle** to `x-klickd-skills/` (or excluded if covered by `SPEC.md` + the validator output) before the deposit ZIP is sealed. Lite tier (8 packs at the time of this draft) and Pro tier (34 packs at the time of this draft).
- `scripts/validate_v4_1_candidate_mapping.py` — validator enforcing the mapping rule.
- `CHANGELOG.md`, `CITATION.cff`, `LICENSE`, `README.md`, `ACKNOWLEDGEMENTS.md` — repository metadata.
- `assets/x-klickd-matrix-hero.svg`, `assets/x-klickd-matrix-hero.png` — original matrix visual (added by Vince when the visual is produced).

### 7.1 TODO before sealing the deposit bundle — codename-bearing paths

Zenodo's web record displays the uploaded ZIP's filenames and lets visitors browse the directory tree. Even though every metadata field (title, description, keywords, notes) in this draft is clean, **any file or directory inside the deposit ZIP that carries the internal codename will be visible to the public** through Zenodo's file browser. This is a hard lock: the public deposit surface must not show the codename.

Before the v4.1 Zenodo deposit ZIP is created, Vince MUST resolve the codename-bearing paths via one of the three options below. Pick exactly one per affected path:

1. **Rename in repo first (cleanest).** Open a separate PR that renames the codename-bearing in-repo paths to `x.klickd`-named equivalents (e.g. internal `examples/v4.1/<codename>-skills/` → `examples/v4.1/x-klickd-skills/`; the v4.1 planning RFC → an `x-klickd`-named filename). Merge before tagging v4.1 GA. The deposit bundle then naturally contains only clean paths. *Out of scope for the present site-copy PR — flagged here so Vince can plan the rename ahead of GA.*
2. **Repackage at archive time.** Keep the in-repo directory under its historical name, but **rename the path inside the deposit ZIP** before uploading to Zenodo. The bundle becomes `x-klickd-skills/lite/`, `x-klickd-skills/pro/`, and an `x-klickd`-named RFC filename — regardless of what the live repo calls them. Use `git archive` + a scripted rename step.
3. **Exclude from the deposit bundle.** If the codename-bearing v4.1 planning RFC is fully superseded by `SPEC.md` post-merge, omit it from the deposit ZIP entirely. The same applies to any subdirectory whose content is already redundantly captured by other public artefacts.

The deposit MUST NOT be created until exactly one of options 1/2/3 has been applied to every codename-bearing path that would otherwise appear in the bundle. The §14 acceptance checklist gates the deposit on this.

---

## 8. Keywords

The deposit's keyword list should mirror and extend the v4.0.0 keyword list (`/.zenodo.json`). Final keyword list:

- portable AI memory
- AI context
- AI competency
- competency-anchored skills
- x.klickd
- .klickd
- klickd
- open standard
- skill catalog
- Lite skill
- Pro skill
- LLM
- privacy
- GDPR
- client-side encryption
- AES-256-GCM
- Argon2id
- JSON Schema
- interoperability
- agent memory
- ESCO
- DigComp
- LifeComp
- NICE
- ENISA
- CIS Controls
- SFIA
- O*NET
- WEF
- educational technology
- v4
- v4.1

The internal codename used in the planning track is **not** a keyword. Do not add it under any spelling or capitalisation variant.

---

## 9. Access right and licence

- **Access right:** `open`
- **Licence:** `CC0-1.0`

Unchanged from `v4.0.0`. The CC0 licence is the open-standard lock — anyone may use the format, the schema, the skill artefacts, and the original diagrams without permission.

---

## 10. Related identifiers

To be confirmed at deposit time. The expected shape (mirroring `/.zenodo.json` for v4.0.0):

- `isSupplementTo` — `https://github.com/Davincc77/klickdskill` (this repository, `url`).
- `isIdenticalTo` — `https://www.npmjs.com/package/@klickd/core` (TypeScript SDK on npm, `url`) — once the v4.1 SDK is published.
- `isIdenticalTo` — `https://pypi.org/project/klickd/` (Python SDK on PyPI, `url`) — once the v4.1 SDK is published.
- `isVersionOf` — `10.5281/zenodo.20262530` (the concept DOI for the `.klickd` series, `doi`).
- `isNewVersionOf` — `10.5281/zenodo.20383133` (the v4.0.0 version DOI, `doi`).
- `isPreviousVersionOf` — *staged for the deposit AFTER v4.1; do not include in the v4.1 deposit itself; add at the v4.2 deposit time.*

If any of the npm / PyPI v4.1 packages is not yet published when the Zenodo deposit is created, omit that `isIdenticalTo` entry until the package is live. Do not point a related-identifier at a non-existent artifact.

---

## 11. Language

> `eng`

---

## 12. Communities

> *(empty for now; if Vince wants the deposit reviewed by a specific Zenodo community by v4.1 ship time, add the community slug here.)*

---

## 13. Source list (for the deposit's README / About block, mirror of public site §10)

For the deposit's bundle README (if Vince ships a top-level deposit README distinct from `README.md`), include the following source list:

- **ESCO** — European Commission. `https://esco.ec.europa.eu/`
- **DigComp 2.2** — EU Joint Research Centre. `https://joint-research-centre.ec.europa.eu/scientific-tools-databases/digcomp_en`
- **LifeComp** — EU Joint Research Centre. `https://joint-research-centre.ec.europa.eu/scientific-tools-databases/lifecomp_en`
- **NICE Workforce Framework for Cybersecurity** — US NIST. `https://www.nist.gov/itl/applied-cybersecurity/nice/nice-framework-resource-center`
- **ENISA** — European Union Agency for Cybersecurity. `https://www.enisa.europa.eu/`
- **CIS Controls** — Center for Internet Security. `https://www.cisecurity.org/controls`
- **SFIA** — Skills Framework for the Information Age. `https://sfia-online.org/`
- **O*NET** — US Department of Labor. `https://www.onetonline.org/`
- **WEF Future of Jobs** — World Economic Forum. `https://www.weforum.org/reports/the-future-of-jobs-report-2023/` *(or the most recent edition at deposit time).*

Each anchor in the catalog points to one of these owners' canonical URLs. The deposit does **not** redistribute the framework owners' content; it links to it.

---

## 14. Acceptance checklist before minting the v4.1 DOI

A reviewer (Vince, or a delegate) must be able to tick every box below before the v4.1 Zenodo deposit is created.

- [ ] v4.1 has been **tagged** in the repository as the GA release.
- [ ] `SPEC.md` and the v4.1 RFC track have been promoted to `Accepted` per RFC-009 §8.
- [ ] The validator script (`scripts/validate_v4_1_candidate_mapping.py`) passes on the catalog tree at the GA tag.
- [ ] The deposit metadata uses `x.klickd` everywhere — title, description, keywords, notes, related-identifier titles.
- [ ] The internal codename used in the planning track does **not** appear in any public-facing Zenodo field (title, description, keywords, notes).
- [ ] §7.1 has been applied: **no file or directory inside the deposit bundle ZIP carries the internal codename** in its name. One of the three options in §7.1 (rename in repo, repackage at archive time, or exclude) has been applied to every affected path. Spot-check by listing the bundle ZIP and grepping for the codename string before uploading.
- [ ] The disclaimer block (§6) has been re-evaluated against the GA state — if v4.1 is now GA at deposit time, the "candidates / not for unmodified production use" sentence has been removed; if v4.1 is being deposited as a release candidate, the non-GA sentence is retained.
- [ ] No copyrighted third-party visual is included in the deposit bundle. All diagrams included are original works.
- [ ] The related-identifier list points only at existing, published artefacts (npm, PyPI, prior Zenodo DOIs). No staged links to artefacts that do not yet exist.
- [ ] CC0-1.0 licence is unchanged.

---

*End of Zenodo deposit draft. Vince: please flag any field that should be set differently before the v4.1 deposit is prepared.*
