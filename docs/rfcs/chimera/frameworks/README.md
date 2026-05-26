# `docs/rfcs/chimera/frameworks/` — framework references and offline bundle shape

> **Status:** Draft · NON-NORMATIVE · companion to [RFC-009 §5.7, §8.6](../../RFC-009-chimera-v4.1.md).
> **Track:** `.klickd v4.1` Chimera.
> **Triggers no release.** No tag, no `latest` on npm/PyPI, no DOI on Zenodo, no IANA action, no schema change.

This directory documents the **authoritative skill-framework references** that Chimera `competency_pack`s anchor against, and the **shape** of the offline SKOS/JSON-LD bundle each pack is expected to ship with (per [RFC-009 §8.6](../../RFC-009-chimera-v4.1.md)).

It does **not** ship the bundles themselves (those are substance, not spec). It pins **which** frameworks count as authoritative, **where** their canonical artefacts live, and **how** a pack-side bundle is laid out so a reader can resolve `competency_ref` → `prefLabel` offline.

## 1. Canonical framework registry

The frameworks below are the ones a v4.1-native `competency_pack` MAY declare in its top-level `frameworks[]` block (see [RFC-009 §8.1](../../RFC-009-chimera-v4.1.md)). The list is intentionally short. Adding a framework requires a new RFC entry.

| `scheme` (id used in packs) | Name | Version pinned for v4.1 P0 | Canonical landing page | Canonical machine-readable distribution | Notes |
|---|---|---|---|---|---|
| `esco` | ESCO — European Skills, Competences, Qualifications and Occupations | `v1.1.1` (2022-09 stable) | `https://esco.ec.europa.eu/en` | `https://esco.ec.europa.eu/en/use-esco/download` (SKOS/RDF turtle bundle) | EU primary occupational / skill backbone. Multilingual (27 languages). Public licence. ESCO uses "skill" as the framework term; in Chimera vocabulary that maps to **competency anchor**, never `host_skill`. |
| `digcomp` | DigComp 2.2 — European Digital Competence Framework | `2.2` (2022) | `https://joint-research-centre.ec.europa.eu/digcomp_en` | `https://publications.jrc.ec.europa.eu/repository/handle/JRC128415` (PDF + structured CSV annexes) | 5 areas × 21 competences. Stable IDs `digcomp:<area>.<competence>` (e.g. `digcomp:1.1` "Browsing, searching, filtering data, information and digital content"). |
| `lifecomp` | LifeComp — European Framework for the Personal, Social and Learning to Learn Key Competence | `2020` | `https://joint-research-centre.ec.europa.eu/lifecomp_en` | `https://publications.jrc.ec.europa.eu/repository/handle/JRC120911` | 3 areas (Personal, Social, Learning to Learn) × 9 competences. Used for `base_transversal_core` self-regulation / learning-to-learn anchors. |
| `eqf` | EQF — European Qualifications Framework | `2017 Council Recommendation` (current consolidated) | `https://europa.eu/europass/en/europass-tools/european-qualifications-framework` | `https://europa.eu/europass/en/description-eight-eqf-levels` (level descriptors) | 8 levels (EQF-1 .. EQF-8). Used for `level.level_label` (e.g. `"EQF level 4"`). NOT a competency catalogue — only a level scale. |
| `cefr` | CEFR — Common European Framework of Reference for Languages | `2020 Companion Volume` | `https://www.coe.int/en/web/common-european-framework-reference-languages` | `https://rm.coe.int/common-european-framework-of-reference-for-languages-learning-teaching/16809ea0d4` (Companion Volume PDF, with structured can-do descriptors) | 6 levels A1..C2. Used by `x.klickd/student` for the `language_proficiency[]` field (separate from the EQF qualification level). |
| `wef` | WEF Future of Jobs taxonomy | `2023 report` (current; superseded by 2025 once stable) | `https://www.weforum.org/publications/the-future-of-jobs-report-2023/` | `https://www.weforum.org/reports/the-future-of-jobs-report-2023/digest/` (structured skill list in annex) | Transversal / "future skills" layer. WEF does not publish IRIs; pack-side bundle gives stable surrogate IDs `wef:<slug>` and includes the upstream URL + report year as `dcterms:source`. |
| `onet` | O\*NET — US Occupational Information Network | `28.0` (2024-02; current at time of writing) | `https://www.onetonline.org/` | `https://www.onetcenter.org/database.html` (relational dump + SOC mapping) | Cross-check for occupational depth where ESCO is sparse. Used for `x.klickd/coding`, `x.klickd/work` cross-walk. |
| `nice` | NICE Framework — NIST SP 800-181r1 | `r1 (2020)` (with the 2024 work-role refresh) | `https://niccs.cisa.gov/workforce-development/nice-framework` | `https://csrc.nist.gov/publications/detail/sp/800-181/rev-1/final` (NIST SP 800-181 Rev. 1 PDF + companion CSV) | Cybersecurity workforce framework. Used by `x.klickd/security`. |
| `enisa` | ENISA European Cybersecurity Skills Framework (ECSF) | `1.0` (2022-09) | `https://www.enisa.europa.eu/topics/skills-and-competences/skills-development/european-cybersecurity-skills-framework` | `https://www.enisa.europa.eu/publications/european-cybersecurity-skills-framework-ecsf` (PDF + role profile annex) | EU cyber skills cross-check; pairs with `nice` for `x.klickd/security`. |
| `cis` | CIS Critical Security Controls | `v8` (2021) | `https://www.cisecurity.org/controls/cis-controls-list` | `https://www.cisecurity.org/controls/v8` (control catalogue) | Operational security controls; used by `x.klickd/security` for blast-radius / hygiene anchors. |
| `sfia` | SFIA — Skills Framework for the Information Age | `8` (2021) | `https://sfia-online.org/en/sfia-8` | `https://sfia-online.org/en/sfia-8/all-skills-a-z` (per-skill HTML; licensable XML/CSV under SFIA Foundation T&Cs) | Software-engineering cross-check for ESCO ICT under `x.klickd/coding`. **Licensing caveat:** SFIA content is under SFIA Foundation licence; a pack MAY reference SFIA codes (`sfia:PROG`) and link out, but MUST NOT ship SFIA text inline unless the pack publisher holds the appropriate licence. The offline bundle for SFIA carries `id` + canonical URL only when no licence is held — see §3.4. |

### 1.1 What "stable URL / hash" means here

Several frameworks (ESCO, DigComp, EQF, CEFR, NICE) publish a stable, dated artefact (RDF dump, PDF Companion Volume, CSV annex). A pack's `frameworks[]` entry SHOULD record both:

- **`canonical_url`** — the publisher's permanent URL for the version pinned;
- **`distribution_url`** — the URL of the machine-readable artefact actually consumed by the pack-side bundle;
- **`distribution_sha256`** — the SHA-256 of that artefact at the time the pack-side bundle was generated.

If a distribution URL is unstable (WEF, ENISA, SFIA at the time of writing), the bundle uses `distribution_sha256` of the **mirror copy** the pack ships under `bundle/<scheme>/source.<ext>` and records that the upstream artefact is mirrored, not fetched at resolve-time. This is what RFC-009 §8.6 calls "offline-resolvable".

### 1.2 What is NOT in the registry

- **Homegrown Klickd taxonomies.** Forbidden by [RFC-009 §5.7](../../RFC-009-chimera-v4.1.md). If a needed concept is missing in all of the above, it is an issue for the framework, not a reason to invent a new scheme.
- **Persona-shaped scales.** Free-text "advanced", "expert", "intermediate" are not framework levels (see [RFC-009 §5.0](../../RFC-009-chimera-v4.1.md)). Use EQF for qualification level and CEFR for languages.
- **Proprietary employer competency models** (e.g. internal grading rubrics). A pack MAY *cite* one via `scale_ref` but MUST NOT register it as a `frameworks[]` scheme.

## 2. Recommended framework anchors per pack

This table is the **default anchor set** each P0/P1 pack SHOULD declare. A pack MAY add frameworks; it MUST NOT drop frameworks marked as **required** here without explicit RFC-level discussion.

| Pack | Required frameworks | Recommended additional frameworks | Notes |
|---|---|---|---|
| `x.klickd/user` (base) | `esco` (transversal subset), `digcomp`, `lifecomp` | `eqf` (level), `cefr` (language) | `base_transversal_core` source. See §2.1 below. |
| `x.klickd/student` | `esco` (education + transversal subset), `digcomp`, `eqf` | `cefr` (for language-of-study), `lifecomp` (learning-to-learn) | See `../packs/student.md` §2.0. |
| `x.klickd/coding` | `esco` (ICT occupations + skills), `digcomp` (problem solving, content creation) | `onet` (cross-walk), `sfia` (by id-link only unless licence held) | Pack publisher licensing affects whether SFIA text can ship inline. |
| `x.klickd/research` | `esco` (research occupations + analytical-thinking skills), `digcomp` (information & data literacy) | `wef` (analytical thinking) | RFC-002 §8b grounding rules are pack-internal, not a framework anchor. |
| `x.klickd/security` | `nice`, `enisa`, `cis` | `esco` (security occupations) | All three required because they cover different decompositions (role vs framework vs control). |
| `x.klickd/legal` | `esco` (legal occupations) | EU AI Act / GDPR references (citation-only, not a `frameworks[]` scheme) | Jurisdictional citations live in `curriculum_refs[]`-style fields, NOT in `frameworks[]`. |
| `x.klickd/work` (P1) | `esco` (management), `wef` | `lifecomp` (social competence) | — |
| `x.klickd/creator` (P1) | `esco` (creative occupations) | RFC-001 `media_profile` references (not a `frameworks[]` scheme) | — |
| `x.klickd/gaming` (P1) | `esco` (leisure / sport), `wef` (complex problem solving) | — | — |
| `x.klickd/bridge` (P1) | `wef` (technology literacy) | `esco` (ICT) | — |
| `x.klickd/mission` (P1) | `wef` (active learning), `esco` (transversal) | — | — |

### 2.1 `base_transversal_core` — concrete framework anchors

The `base_transversal_core` (RFC-009 §5.2, §0.1) is the always-on cross-pack competency floor. It is **mandatory** in every `competency_pack`, with the same concrete anchor set:

```jsonc
{
  "base_transversal_core": {
    "frameworks": [
      {
        "scheme": "esco",
        "version": "v1.1.1",
        "iri_prefix": "http://data.europa.eu/esco/skill/",
        "canonical_url": "https://esco.ec.europa.eu/en/classification/skill_main",
        "distribution_url": "https://esco.ec.europa.eu/en/use-esco/download",
        "distribution_sha256": "TBD-at-bundle-generation"
      },
      {
        "scheme": "digcomp",
        "version": "2.2",
        "iri_prefix": "https://joint-research-centre.ec.europa.eu/digcomp/2.2/",
        "canonical_url": "https://joint-research-centre.ec.europa.eu/digcomp_en",
        "distribution_url": "https://publications.jrc.ec.europa.eu/repository/handle/JRC128415",
        "distribution_sha256": "TBD-at-bundle-generation"
      },
      {
        "scheme": "lifecomp",
        "version": "2020",
        "iri_prefix": "https://joint-research-centre.ec.europa.eu/lifecomp/2020/",
        "canonical_url": "https://joint-research-centre.ec.europa.eu/lifecomp_en",
        "distribution_url": "https://publications.jrc.ec.europa.eu/repository/handle/JRC120911",
        "distribution_sha256": "TBD-at-bundle-generation"
      },
      {
        "scheme": "eqf",
        "version": "2017",
        "iri_prefix": "https://europa.eu/europass/eqf/",
        "canonical_url": "https://europa.eu/europass/en/europass-tools/european-qualifications-framework",
        "distribution_url": "https://europa.eu/europass/en/description-eight-eqf-levels",
        "distribution_sha256": "TBD-at-bundle-generation"
      }
    ],
    "transversal_refs": [
      { "competency_ref": "esco:S1.0.0",  "scheme": "esco",    "prefLabel": "Communication, collaboration and creativity" },
      { "competency_ref": "esco:S1.1.0",  "scheme": "esco",    "prefLabel": "Communicating" },
      { "competency_ref": "esco:S1.4.0",  "scheme": "esco",    "prefLabel": "Working with others" },
      { "competency_ref": "esco:S2.0.0",  "scheme": "esco",    "prefLabel": "Information skills" },
      { "competency_ref": "esco:S3.0.0",  "scheme": "esco",    "prefLabel": "Assisting and caring" },
      { "competency_ref": "esco:S4.0.0",  "scheme": "esco",    "prefLabel": "Management skills" },
      { "competency_ref": "esco:S5.0.0",  "scheme": "esco",    "prefLabel": "Working with computers" },
      { "competency_ref": "digcomp:1.1",  "scheme": "digcomp", "prefLabel": "Browsing, searching, filtering data, information and digital content" },
      { "competency_ref": "digcomp:1.2",  "scheme": "digcomp", "prefLabel": "Evaluating data, information and digital content" },
      { "competency_ref": "digcomp:2.1",  "scheme": "digcomp", "prefLabel": "Interacting through digital technologies" },
      { "competency_ref": "digcomp:4.1",  "scheme": "digcomp", "prefLabel": "Protecting devices" },
      { "competency_ref": "digcomp:5.1",  "scheme": "digcomp", "prefLabel": "Solving technical problems" },
      { "competency_ref": "lifecomp:P1",  "scheme": "lifecomp", "prefLabel": "Self-regulation" },
      { "competency_ref": "lifecomp:P2",  "scheme": "lifecomp", "prefLabel": "Flexibility" },
      { "competency_ref": "lifecomp:L1",  "scheme": "lifecomp", "prefLabel": "Growth mindset" },
      { "competency_ref": "lifecomp:L2",  "scheme": "lifecomp", "prefLabel": "Critical thinking" },
      { "competency_ref": "lifecomp:L3",  "scheme": "lifecomp", "prefLabel": "Managing learning" }
    ]
  }
}
```

The IRIs above are **stable framework IDs**, not invented surrogates. ESCO `S1.0.0` is the actual top-level skill-pillar code; DigComp `1.1` is the actual competence code in the 2.2 framework; LifeComp `P1`/`P2`/`L1`/`L2`/`L3` are the published codes in the 2020 framework; EQF level labels (`"EQF level 4"`) match `https://europa.eu/europass/en/description-eight-eqf-levels`.

The `iri_prefix` values are documented as **stable URL prefixes** under each publisher; `distribution_sha256` is filled at bundle-generation time (it is "TBD-at-bundle-generation" in the spec because no bundle is shipped under this RFC — only the shape).

## 3. Offline bundle shape (per pack)

A pack-side bundle is a directory laid out as:

```text
bundle/
├── manifest.json              # top-level index (see §3.1)
├── <scheme>/                  # one directory per declared framework
│   ├── concepts.jsonld        # SKOS/JSON-LD list of the framework concepts the pack references
│   ├── source.<ext>           # mirror copy of the upstream distribution (only when distribution_url is unstable)
│   └── LICENSE.txt            # framework licence text, verbatim
└── crosswalk.jsonld           # optional: cross-framework `skos:exactMatch` / `skos:closeMatch` links
```

The bundle is **scoped to the pack**: it includes only the framework concepts the pack `competencies[]` / `mastery[]` / `base_transversal_core.transversal_refs[]` actually reference, plus their `skos:broader` ancestors up to the framework root.

### 3.1 `manifest.json`

```jsonc
{
  "$schema_intent": "non-normative; see RFC-009 §8.6",
  "pack_ref": "x.klickd/student",
  "pack_version": "0.1.0-draft",
  "generated_at": "2026-05-26T00:00:00Z",
  "generator_ref": "docs/rfcs/chimera/frameworks/README.md#3",
  "frameworks": [
    {
      "scheme": "esco",
      "version": "v1.1.1",
      "iri_prefix": "http://data.europa.eu/esco/skill/",
      "concepts_file": "esco/concepts.jsonld",
      "concepts_count": 0,
      "source_mirror": null,
      "source_distribution_url": "https://esco.ec.europa.eu/en/use-esco/download",
      "source_distribution_sha256": "TBD-at-bundle-generation",
      "licence_file": "esco/LICENSE.txt",
      "licence_ref": "Creative Commons Attribution 4.0 International (CC BY 4.0)"
    }
  ],
  "crosswalk_file": "crosswalk.jsonld",
  "languages": ["en", "fr"]
}
```

### 3.2 `<scheme>/concepts.jsonld` (SKOS/JSON-LD subset)

Each `concepts.jsonld` is a JSON-LD document with a `skos:ConceptScheme` and the `skos:Concept`s the pack references.

```jsonc
{
  "@context": {
    "skos": "http://www.w3.org/2004/02/skos/core#",
    "dct": "http://purl.org/dc/terms/",
    "xsd": "http://www.w3.org/2001/XMLSchema#"
  },
  "@graph": [
    {
      "@id": "http://data.europa.eu/esco/concept-scheme/skills",
      "@type": "skos:ConceptScheme",
      "skos:prefLabel": "ESCO Skills Pillar",
      "dct:hasVersion": "v1.1.1",
      "dct:source": "https://esco.ec.europa.eu/en/use-esco/download"
    },
    {
      "@id": "http://data.europa.eu/esco/skill/S1.0.0",
      "@type": "skos:Concept",
      "skos:inScheme": "http://data.europa.eu/esco/concept-scheme/skills",
      "skos:prefLabel": [
        { "@value": "Communication, collaboration and creativity", "@language": "en" },
        { "@value": "Communication, collaboration et créativité",  "@language": "fr" }
      ],
      "skos:notation": "S1.0.0",
      "skos:broader": null
    }
  ]
}
```

A reader resolving `competency_ref: "esco:S1.0.0"` looks up `@id` `http://data.europa.eu/esco/skill/S1.0.0` in `esco/concepts.jsonld` and gets the multilingual `prefLabel` without any network call.

### 3.3 `crosswalk.jsonld` (optional)

Cross-framework links use `skos:exactMatch` / `skos:closeMatch`. This is how a `digcomp:5.1` "Solving technical problems" gets connected to `esco:S1.2.0` "Solving problems" without inventing a new scheme.

```jsonc
{
  "@context": { "skos": "http://www.w3.org/2004/02/skos/core#" },
  "@graph": [
    {
      "@id": "https://joint-research-centre.ec.europa.eu/digcomp/2.2/5.1",
      "skos:closeMatch": [
        { "@id": "http://data.europa.eu/esco/skill/S1.2.0" }
      ]
    }
  ]
}
```

### 3.4 Licensing per framework (offline bundle)

| Scheme | Licence | Inline-text shipping in bundle | Notes |
|---|---|---|---|
| `esco` | CC BY 4.0 | ✅ allowed | Attribution required (`dct:source` in `concepts.jsonld`). |
| `digcomp` | CC BY 4.0 | ✅ allowed | Same. |
| `lifecomp` | CC BY 4.0 | ✅ allowed | Same. |
| `eqf` | EU public-sector reuse (Decision 2011/833/EU) | ✅ allowed (level descriptors only) | EQF is a small fixed set of 8 descriptors. |
| `cefr` | Council of Europe terms | ⚠️ id + URL only by default | Inline only with publisher's permission. |
| `wef` | WEF report copyright | ⚠️ id + URL only | Pack uses surrogate `wef:<slug>` ids; inline only with permission. |
| `onet` | Public domain (US Government work) | ✅ allowed | — |
| `nice` | Public domain (NIST publication) | ✅ allowed | — |
| `enisa` | EU public-sector reuse | ✅ allowed (id + descriptor) | — |
| `cis` | CIS terms of use | ⚠️ id + URL only by default | Inline only with CIS licence. |
| `sfia` | SFIA Foundation licence | ⚠️ id + URL only by default | Inline only with SFIA licence. |

A bundle that ships inline text for a `⚠️` scheme without a publisher permission line in `<scheme>/LICENSE.txt` fails validation criterion §8.6 (offline-resolvable) *and* publisher-side licensing — it MUST NOT be published.

## 4. Round-trip safety

A v4.0-only reader that does not understand `bundle/` is **not expected to read it**. The bundle lives alongside the pack manifest, never inside the v4.0 `.klickd` payload. A v4.0 reader that ignores the bundle preserves the pack manifest verbatim (RFC-009 §5.6, SPEC §33.7); the bundle is auxiliary, never user-state.

## 5. What is in scope and out of scope here

In scope (this directory):

- The canonical framework registry (§1).
- The default per-pack anchor set (§2).
- The `base_transversal_core` anchor IDs and stable URL prefixes (§2.1).
- The offline bundle directory shape and `manifest.json` schema-intent (§3).
- Licensing rules per framework for inline text (§3.4).

Out of scope (deferred to a future RFC or to substance PRs, never to a release):

- Actually shipping the bundles (i.e. populating `esco/concepts.jsonld` with the real subset).
- A CLI generator that walks ESCO RDF and emits the SKOS subset. **No tool is implied by this RFC.**
- Crosswalk completeness (`crosswalk.jsonld` is optional; populating it is a substance task per pack).
- Versioning policy for upstream framework releases (when does v4.1 follow ESCO v1.1.2?).
- Any catalog or download surface for bundles. The no-catalog rule of [RFC-009 §7](../../RFC-009-chimera-v4.1.md) applies to bundles too.

## 6. See also

- [`../../RFC-009-chimera-v4.1.md`](../../RFC-009-chimera-v4.1.md) §5.7 (framework backbone), §8.1 (`frameworks[]` field), §8.6 (offline-resolvable criterion).
- [`../packs/student.md`](../packs/student.md) §2.0 (base transversal core in the student pack).
- [`../packs/README.md`](../packs/README.md) §4 (no-fake-catalog rule).
- [`../schema-fragments/`](../schema-fragments/) — schema-intent fragments for the pack manifest, `base_transversal_core`, `competencies`, `mastery`, `evidence_policy`, `source_policy`, `gates`, `human_authority`, structured memory.
