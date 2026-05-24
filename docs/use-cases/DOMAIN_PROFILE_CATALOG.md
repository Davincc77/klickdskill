# Domain Profile Catalog — `.klickd` scope taxonomy & domain seed list

| | |
|---|---|
| **Status** | **Draft · NON-NORMATIVE · concept doc / exploratory** |
| **Track** | `.klickd v4+` — future RFC / extension (NOT P0 GA) |
| **Author** | Vince C. (Klickd / Luxlearn, Luxembourg) |
| **Created** | 2026-05-24 |
| **Audience** | Reviewers of `.klickd` taxonomy, future RFC drafters, integrators evaluating per-domain shapes |
| **Relates to** | [`docs/rfcs/RFC-006-agent-core.md`](../rfcs/RFC-006-agent-core.md) · [`docs/use-cases/CORE_KLICKD_B2B.md`](./CORE_KLICKD_B2B.md) · [`docs/use-cases/CREATOR-CORE-KLICKD.md`](./CREATOR-CORE-KLICKD.md) · [`docs/roadmap/ROAD-TO-V4-GA.md`](../roadmap/ROAD-TO-V4-GA.md) §P2-6 |

> **This document is non-normative and exploratory.** It does **not** modify any
> SPEC section, schema, SDK behaviour, vector, lock file, or RFC status. It
> introduces **no new normative field**. It does **not** publish anything
> (npm / PyPI / Zenodo / IANA / DOI). The only artefact it ships is *this
> markdown file*.
>
> The production-recommended `.klickd` remains **v3.5.1**. The preview track
> remains **v4.0.0-preview.1**. Anything sketched here would become normative
> only via a future RFC, after V4 GA gates listed in
> [`ROAD-TO-V4-GA.md`](../roadmap/ROAD-TO-V4-GA.md) are met.

---

## 0. Why this document

Three previous concept notes
([`CORE_KLICKD_B2B.md`](./CORE_KLICKD_B2B.md),
[`CREATOR-CORE-KLICKD.md`](./CREATOR-CORE-KLICKD.md),
[`RFC-006-agent-core.md`](../rfcs/RFC-006-agent-core.md))
each gestured at the same open question without naming it:

> *Once `.klickd` carries more than "a user's private memory", what is the
> shape of the **other** things it carries? Where do `med.klickd`,
> `nature.klickd`, `engineer.klickd`, `legal.klickd` fit — as profiles, as
> agents, as projects, as competency packs?*

The risk of answering this badly is real. Two failure modes loom:

1. **Surface creep.** Inventing a new top-level extension (`med.klickd`,
   `nature.klickd`, …) every time a vertical appears. The format ends up
   with dozens of incompatible normative subsections.
2. **Homegrown taxonomy.** Inventing Klickd-specific lists of "competencies"
   per domain when the world already maintains them (ESCO, O\*NET, SFIA,
   DigComp, CanMEDS, NICE, …). Klickd then drifts from authoritative skill
   frameworks and becomes harder to audit, harder to localise, harder to
   trust in regulated contexts.

This catalog is the **conservative answer** to both: clarify the four scopes
that already exist conceptually, list the domains worth seeding, and — for
each domain — point at the **official / recognised competency framework**
the future shape SHOULD borrow from, with a `TO_VERIFY` marker wherever the
licensing / openness of that framework is not yet confirmed by a maintainer
of this repo.

---

## 1. Four scopes of a `.klickd` file (clarification)

`.klickd` is **one envelope, one schema**. The "scope" is *what kind of
artefact* the payload describes. The four scopes below are conceptual; they
are signalled today by the **combination of sections present**, not by a
distinct file extension. They are summarised here so the rest of this
document can refer to them unambiguously.

| Scope | Suggested filename hint | What it carries | Who owns it | Travels with | Today |
|---|---|---|---|---|---|
| **`user.klickd`** | `<person>.klickd` | Private memory of a human: identity, preferences, memory[], growth, accessibility, ethics, gates. | The person. | The person, across agents and devices. | Normative core of v3.5.1 / v4-preview. |
| **`core.<agent>.klickd`** | `core.Kai.klickd`, `core.<Agent>.klickd` | Operating context of an **agent** or **organisation**: pedagogy, tone, tool policy, safety policy, default gates, escalation, evidence rules. **No user PII.** | The publisher (org / agent owner). | The deployment, across users and sessions. | Sketched by [RFC-006](../rfcs/RFC-006-agent-core.md) and [CORE_KLICKD_B2B](./CORE_KLICKD_B2B.md). |
| **`<domain>_profile`** (e.g. `med`, `legal`, `engineer`) | embedded payload inside a `core.*.klickd` OR standalone reference file | **Domain-level** rules, expected competencies, source standards, risks, compliance gates, evidence requirements, allowed/forbidden tools, human-veto defaults. **No org-specific workflow, no client data.** | The community / publisher of the domain pack. | Any `core.*.klickd` that imports / references it. | Conceptually anticipated by [`ROAD-TO-V4-GA.md`](../roadmap/ROAD-TO-V4-GA.md) §P2-6. |
| **`project.<domain>.klickd`** | `project.<case-id>.klickd` | State of a **specific** project / dossier / campaign / case: brief, status, deliverables, named participants (with consent), per-project gates. | The project owner. | The collaborators, for the duration of the project. | Sketched by [CREATOR-CORE-KLICKD](./CREATOR-CORE-KLICKD.md) §2. |

### 1.1 Composition rule (informative, mirrors RFC-006 §7 and CORE_KLICKD_B2B §5)

At runtime a host MAY load several files into the effective context:

```
core.<agent>.klickd      ── constrains  (operating context, gates, tools, tone)
    └── references <domain>_profile  ── declares  (domain competencies, risks, sources)
user.klickd              ── personalises  (soul, memory, preferences, user veto)
project.<domain>.klickd  ── scopes  (this specific case / campaign / dossier)
```

Invariants carried from RFC-006 / CORE_KLICKD_B2B:

- **One file, one scope.** A file is exactly one of the four. Never mixed.
- **User wins on personal veto / consent / human-veto.** Agent/core/domain
  defaults can be *raised* by the user, never *lowered*.
- **`core` wins on safety-relevant gates.** A `core.<agent>.klickd` can
  *raise* a `<domain>_profile` default (e.g. force `block` where the domain
  baseline says `confirm`).
- **No write-back.** Runtimes never modify `core.*` or `<domain>_profile`
  files implicitly; they are versioned artefacts changed by an explicit,
  reviewed action.
- **No client / patient / case data in `core.*` or `<domain>_profile`.**
  Project data lives in `project.*.klickd`. User data lives in
  `user.klickd`. Crossing the boundary is the single biggest foot-gun.

### 1.2 What `<domain>_profile` is **not**

- **Not a runtime.** It is data describing what a competent practitioner /
  agent / publisher in that domain is expected to honour. The runtime
  enforces; the profile expresses.
- **Not a substitute for licensing / professional registration.** A
  `med_profile` does not turn an agent into a clinician. It encodes
  competency references, scope limits, evidence rules, and red-flag
  triggers.
- **Not a translation of an official framework.** It *references* official
  frameworks (ESCO, CanMEDS, SFIA, …) by ID + version + URL; it does not
  copy their content.
- **Not a marketplace category.** Klickd does not run a directory of
  approved domain profiles. Anyone can publish one; auditability comes
  from signed provenance + framework references, not from a registry.

---

## 2. Principle — do not multiply normative extensions too fast

A core tension throughout RFC-006, CORE_KLICKD_B2B, and CREATOR-CORE-KLICKD
is the temptation to invent a new top-level extension every time a vertical
appears. This catalog states the principle explicitly:

> **Prefer composing existing fields over minting new ones.** Before
> proposing `med.klickd`, `engineer.klickd`, `nature.klickd` as distinct
> normative extensions of the format, exhaust composition of the existing
> surface.

The existing surface that SHOULD carry domain specialisation is:

| Existing primitive | Carries (in a domain context) |
|---|---|
| `usage_profile` *(field referenced in CREATOR-CORE §3.1 / RFC-007 future track)* | High-level "what is this file used for" hint, machine-readable. |
| `extensions[]` *(generic open-extension mechanism)* | Optional, host-pluggable, MUST round-trip verbatim. |
| `domain_profile` *(future field, sketched in this catalog)* | The structured **per-domain** payload described in §3 below. |
| `competency_map` *(future field, this catalog)* | The mapping from **official framework references** (ESCO ID, SFIA skill code, CanMEDS role, …) to the agent's / file's declared coverage. |
| `tool_policy` *(RFC-006)* | Allowed / blocked / confirmation-required tool capabilities, expressed as capabilities not vendor names. |
| `compliance_gates` *(generalisation of RFC-002 `verification_gates`)* | Domain-level mandatory gates (e.g. clinician sign-off, jurisdiction scope, AI disclosure, citation requirement). |
| `claim_sources` *(v4-preview)* | Where a factual claim came from (statute, study, dataset, guideline). |

This catalog therefore proposes **a single new structural concept**
(`<domain>_profile` as a payload section inside a `core.*` file) rather than
a family of new file types. The competency surface inside it is a *reference
graph* into official frameworks, not a re-invented taxonomy.

---

## 3. Per-domain seed table

The list below is the **initial taxonomy**. It is deliberately conservative:
domains that have a recognised, internationally-cited competency framework
get a row; domains without one get a `TO_VERIFY` row or are deferred.

For each domain row:

- **Base competencies** — minimal set the profile SHOULD reference, by
  framework ID (not by name copy-paste).
- **Risks** — top failure modes in this domain, used by future linters.
- **Compliance gates** — gates the profile SHOULD set as default (e.g.
  human review before publication, disclaimer required, jurisdiction
  scoping).
- **Evidence requirements** — what kinds of sources a factual claim in this
  domain MUST cite.
- **Human veto** — default position on human-in-the-loop for sensitive
  outputs (`always` / `on_threshold` / `optional`).
- **Tool policy hint** — capability-level allow/block (no vendor names).
- **Source standards** — official frameworks the future `competency_map`
  SHOULD reference, with URL and a license / openness column.
- **Example fields** — illustrative-only field names; **non-normative**.
- **Framework references** — table at the end of the row mapping framework
  → URL → status (`stable` / `evolving`) → license (`open` / `restricted` /
  `TO_VERIFY`).

> **Convention.** `TO_VERIFY` means *the maintainer of this repo has not
> yet confirmed the licensing or openness of that framework for embedding
> by ID*. It does **not** mean the framework is closed; it means the claim
> is unverified at the date of this document.

---

### 3.1 Education

- **Base competencies** — referenced via:
  - **UNESCO ICT Competency Framework for Teachers (ICT-CFT v3)** — teacher
    digital competencies.
  - **OECD Future of Education and Skills 2030 / Learning Compass** —
    learner competencies framework.
  - **DigComp 2.2** (European Digital Competence Framework for citizens).
  - **CEFR** (Common European Framework of Reference for Languages) — when
    the profile concerns language pedagogy.
- **Risks** — pedagogical malpractice, age-inappropriate content,
  scoring of minors leaked publicly, fabricated curriculum references.
- **Compliance gates** — `age_appropriate_check`, `no_public_scoring`,
  `caregiver_consent_if_minor`, `claim_sources_required` for factual
  assertions.
- **Evidence requirements** — curriculum reference IDs (hashed per RFC-001
  V-007), peer-reviewed pedagogy where applicable.
- **Human veto** — `always` for content reaching minors.
- **Tool policy hint** — allow: KB read, curriculum lookup, exercise
  generator (sandbox); block: any tool that auto-publishes to a student
  audience without review.
- **Source standards** — see references below.
- **Example fields (illustrative)** — `education_profile.cefr_level`,
  `education_profile.age_band`, `education_profile.curriculum_refs[]`.

| Framework | URL | Status | License |
|---|---|---|---|
| UNESCO ICT-CFT v3 | https://unesdoc.unesco.org/ark:/48223/pf0000265721 | stable | `TO_VERIFY` (UNESCO publication terms) |
| OECD Learning Compass 2030 | https://www.oecd.org/education/2030-project/ | evolving | `TO_VERIFY` |
| DigComp 2.2 (EU JRC) | https://publications.jrc.ec.europa.eu/repository/handle/JRC128415 | stable | open (EU Commission reuse policy — `TO_VERIFY` per-asset) |
| CEFR (Council of Europe) | https://www.coe.int/en/web/common-european-framework-reference-languages | stable | `TO_VERIFY` |
| UNESCO AI Competency Framework for Teachers (2024) | https://unesdoc.unesco.org/ark:/48223/pf0000391105 | new | `TO_VERIFY` |

---

### 3.2 Legal

- **Base competencies** — referenced via:
  - **ESCO** occupation `Lawyers` (occupation code 2611) + associated skill
    pillars.
  - **ISCO-08** occupation code 2611 (Lawyers) as cross-walk.
  - Where applicable, **CCBE (Council of Bars and Law Societies of Europe)**
    Code of Conduct for European Lawyers (professional duties).
- **Risks** — unauthorised practice of law, jurisdiction mismatch, conflict
  of interest undetected, citation fabrication, advice given without
  retainer / engagement letter.
- **Compliance gates** — `jurisdiction_declared`, `conflict_check_before_draft`,
  `licensed_human_sign_off_required`, `disclaimer_required`,
  `citation_required_per_assertion`.
- **Evidence requirements** — statute / case / regulation ID with date,
  internal memo ID, jurisdiction scope.
- **Human veto** — `always` for outgoing legal advice; `optional` for
  internal-only drafting (the org sets the threshold).
- **Tool policy hint** — allow: case-law search, internal clause library
  read, redline diff; block: any tool that auto-sends to a client or signs
  on behalf of a lawyer.
- **Example fields (illustrative)** — `legal_profile.jurisdictions[]`,
  `legal_profile.practice_areas[]`, `legal_profile.clause_library_ref`.

| Framework | URL | Status | License |
|---|---|---|---|
| ESCO (EU) — Lawyers (2611) | https://esco.ec.europa.eu/en/classification/occupation_main?uri=http://data.europa.eu/esco/occupation/9a7d4257-c0d0-4ce5-8f47-b1aaf45f1d4f | stable | open data (CC BY 4.0 — `TO_VERIFY` per-row) |
| ISCO-08 (ILO/OIT) | https://www.ilo.org/public/english/bureau/stat/isco/isco08/ | stable | open with attribution — `TO_VERIFY` |
| CCBE Code of Conduct | https://www.ccbe.eu/ | stable | `TO_VERIFY` (professional rules text) |

---

### 3.3 Medical / Health

- **Base competencies** — referenced via:
  - **CanMEDS 2015 Framework** (Royal College of Physicians and Surgeons of
    Canada) — physician competency roles (Medical Expert, Communicator,
    Collaborator, Leader, Health Advocate, Scholar, Professional).
  - **WHO Global Competency Framework for Universal Health Coverage** —
    when relevant to public-health-oriented profiles.
  - **ESCO** for non-physician health occupations (nursing, pharmacy, AHP).
- **Risks** — diagnosis without licence, prescription without licence,
  missed red-flag symptoms, patient data leakage, hallucinated guideline
  citations, scope creep into mental-health crisis territory.
- **Compliance gates** — `no_diagnosis`, `no_prescription`,
  `clinician_review_required_for_clinical_output`,
  `red_flag_triggers_escalation`, `disclaimer_required`,
  `pediatric_safeguards_if_minor`, `mental_health_crisis_redirect`.
- **Evidence requirements** — guideline ID (e.g. NICE, HAS, WHO, NCCN),
  publication date, jurisdiction; never naked clinical claim.
- **Human veto** — `always` on any output the host classifies as
  clinical-adjacent reaching a patient.
- **Tool policy hint** — allow: guideline KB read, symptom triage workflow
  (informational); block: prescription tools, EHR writes, lab-order
  execution.
- **Example fields (illustrative)** — `med_profile.scope_of_practice`,
  `med_profile.guideline_refs[]`, `med_profile.red_flag_triggers[]`,
  `med_profile.jurisdictions[]`.

| Framework | URL | Status | License |
|---|---|---|---|
| CanMEDS 2015 | https://www.royalcollege.ca/rcsite/canmeds/canmeds-framework-e | stable | `TO_VERIFY` (Royal College terms) |
| WHO UHC Competency Framework | https://www.who.int/publications/i/item/9789240034303 | stable | `TO_VERIFY` (WHO IGO licence) |
| ESCO — Health occupations | https://esco.ec.europa.eu/ | stable | open data CC BY 4.0 — `TO_VERIFY` |

---

### 3.4 Engineering (non-software)

- **Base competencies** — referenced via:
  - **International Engineering Alliance** — Graduate Attributes &
    Professional Competencies (Washington/Sydney/Dublin Accords).
  - **EQF (European Qualifications Framework)** levels 6–8 for engineering
    qualifications.
  - **ESCO** for occupation-level mapping.
- **Risks** — safety calculations outside licensed scope, code/standard
  citation fabrication, jurisdiction-of-standard mismatch, "stamped"
  engineering deliverables without a PE / chartered sign-off.
- **Compliance gates** — `chartered_engineer_sign_off_required_for_stamped_output`,
  `standard_citation_required`, `jurisdiction_of_standard_declared`,
  `safety_critical_review_gate`.
- **Evidence requirements** — standard ID (ISO, IEC, EN, ASME, IEEE, …) +
  edition + date; calculation reference.
- **Human veto** — `always` for safety-critical or regulated deliverables.
- **Tool policy hint** — allow: standards KB read, calculation sandbox;
  block: any tool that emits a stamped / sealed deliverable autonomously.
- **Example fields (illustrative)** — `engineer_profile.discipline`,
  `engineer_profile.standards_refs[]`, `engineer_profile.jurisdictions[]`.

| Framework | URL | Status | License |
|---|---|---|---|
| Int'l Engineering Alliance — Graduate Attributes & Professional Competencies | https://www.ieagreements.org/ | stable | `TO_VERIFY` |
| EQF (European Qualifications Framework) | https://europa.eu/europass/en/europass-tools/european-qualifications-framework | stable | open — `TO_VERIFY` per-asset |
| ESCO — Engineering occupations | https://esco.ec.europa.eu/ | stable | CC BY 4.0 — `TO_VERIFY` |

---

### 3.5 Software / Dev

- **Base competencies** — referenced via:
  - **SFIA (Skills Framework for the Information Age) v9** — global skill
    definitions for IT professions.
  - **ESCO** for occupation/skill cross-walk where SFIA is unsuitable.
  - **e-CF (European e-Competence Framework, EN 16234-1)** as an EU-aligned
    alternative / complement.
- **Risks** — license-incompatible dependency added, secret leak in
  generated code, untested security-critical change merged, fabricated
  benchmark/perf claim, force-push to protected branch.
- **Compliance gates** — `ci_green_required_before_merge`,
  `license_allowlist_enforced`, `secret_scan_required`,
  `security_review_gate_on_auth_paths`, `benchmark_artefact_required_for_perf_claim`.
- **Evidence requirements** — test artefact, benchmark output, SBOM entry,
  CVE reference for security claim.
- **Human veto** — `on_threshold` (e.g. production deploys, schema
  migrations, security-sensitive paths).
- **Tool policy hint** — allow: repo read/write within scope, CI status,
  package registry read; block: direct prod deploys, force-push to
  protected branches, package publish without release ticket.
- **Example fields (illustrative)** — `dev_profile.sfia_skills[]`,
  `dev_profile.languages[]`, `dev_profile.repo_conventions_ref`.

| Framework | URL | Status | License |
|---|---|---|---|
| SFIA v9 | https://sfia-online.org/en/sfia-9 | stable | restricted (free for individuals; commercial use licensed) — `TO_VERIFY` / `USER_ORG_RESPONSIBILITY` |
| e-CF (EN 16234-1) | https://itprofessionalism.org/about-it-professionalism/competences/the-e-competence-framework/ | stable | `TO_VERIFY` |
| ESCO — ICT occupations | https://esco.ec.europa.eu/ | stable | CC BY 4.0 — `TO_VERIFY` |

> **SFIA governance rule (explicit).** SFIA MAY be **referenced** from a
> `dev_profile` as an external framework — by skill code, version, and
> URL — that a user, agent, or org can choose to consult, map against, or
> formally adopt **at their own discretion and under their own SFIA
> licence**. Klickd / `.klickd` artefacts **MUST NOT embed, copy,
> redistribute, derive, or sell SFIA content as-is** (skill definitions,
> level descriptors, framework tables, …) unless a proper SFIA licence
> has been obtained by the publisher of that artefact. Until such a
> licence is confirmed, the SFIA row stays `TO_VERIFY /
> USER_ORG_RESPONSIBILITY`: the responsibility of holding a valid SFIA
> licence sits with the **user / org** that integrates SFIA-derived
> content into their `dev_profile`, not with Klickd. For
> Klickd-published default `dev_profile` seeds, prefer **open / public**
> frameworks (e.g. ESCO ICT, EU e-CF references via their public
> publications) over SFIA-derived content. See §4 default-seed rule.

---

### 3.6 Finance / Accounting

- **Base competencies** — referenced via:
  - **IFAC International Education Standards (IES 1–8)** — professional
    accountant competencies.
  - **CFA Institute Body of Knowledge** (for investment professionals,
    `TO_VERIFY` on referenceability terms).
  - **ESCO** for finance/accounting occupations.
- **Risks** — unlicensed investment advice, regulator-misaligned wording,
  unsourced figures, forward-looking statement without disclaimer,
  recommendation produced by non-licensed actor.
- **Compliance gates** — `licensed_human_required_for_recommendation`,
  `figure_source_required`, `risk_disclaimer_on_forward_looking`,
  `jurisdiction_of_regulator_declared`.
- **Evidence requirements** — data provider + timestamp + identifier
  (e.g. ISIN, ticker, dataset), regulator reference for compliance claim.
- **Human veto** — `always` for any allocation suggestion or forward-looking
  projection.
- **Tool policy hint** — allow: market-data read, research KB read; block:
  trade execution, account writes, payment initiation.
- **Example fields (illustrative)** — `finance_profile.regulator_scope`,
  `finance_profile.instrument_universe`, `finance_profile.licence_state`.

| Framework | URL | Status | License |
|---|---|---|---|
| IFAC IES 1–8 | https://www.ifac.org/_flysystem/azure-private/publications/files/Handbook-of-IES-2019.pdf | stable | `TO_VERIFY` |
| CFA Institute CBOK | https://www.cfainstitute.org/programs/cfa/curriculum/cbok | stable | restricted — `TO_VERIFY` |
| ESCO — Finance occupations | https://esco.ec.europa.eu/ | stable | CC BY 4.0 — `TO_VERIFY` |

---

### 3.7 Research

- **Base competencies** — referenced via:
  - **VITAE Researcher Development Framework (RDF)** — researcher
    competencies across career stages.
  - **OECD Frascati Manual** definitions for R&D activity types.
  - **EQF** levels 7–8 for doctoral-equivalent qualifications.
- **Risks** — fabricated citation, p-hacking framing, undisclosed conflict
  of interest, dual-use risk in sensitive domains, data-handling
  non-compliance.
- **Compliance gates** — `citation_required_per_claim`,
  `coi_disclosure_if_funded`, `ethics_review_ref_required_if_human_subjects`,
  `dual_use_screen_for_sensitive_domains`.
- **Evidence requirements** — DOI, preprint ID, dataset DOI, ethics
  committee reference.
- **Human veto** — `on_threshold` (publication, press release).
- **Tool policy hint** — allow: literature search, dataset read, sandboxed
  analysis; block: direct submission to journals/preprint servers without
  review.

| Framework | URL | Status | License |
|---|---|---|---|
| VITAE RDF | https://www.vitae.ac.uk/researchers-professional-development/about-the-vitae-researcher-development-framework | stable | restricted — `TO_VERIFY` |
| OECD Frascati Manual | https://www.oecd.org/sti/inno/frascati-manual.htm | stable | `TO_VERIFY` |

---

### 3.8 Media / Creator

- **Base competencies** — referenced via:
  - **UNESCO Media and Information Literacy (MIL) Curriculum** for
    educators and producers.
  - **EntreComp** (entrepreneurial competence) for indie creator business
    skills.
  - Platform community-guideline references (TikTok / Meta / YouTube /
    LinkedIn — **versioned by date**, see [CREATOR-CORE-KLICKD §4](./CREATOR-CORE-KLICKD.md)).
- **Risks** — copyright infringement (music, fonts, archive imagery),
  impersonation / non-consented voice/face cloning, AI disclosure absent,
  platform community-guideline mismatch, minor likeness without parental
  consent.
- **Compliance gates** — `ai_disclosure_present`, `subtitles_present`,
  `music_license_documented`, `consent_for_likeness_documented`,
  `platform_rules_passed`.
- **Evidence requirements** — license ID for assets, consent record per
  `media_profile` entry, platform-rule version pinned.
- **Human veto** — `always` for sponsored, regulated-domain, or minor-likeness
  content; `on_threshold` for organic content with factual claims.
- **Tool policy hint** — allow: render sandbox, asset library read,
  storyboard generator; block: auto-publish to platforms without gate
  check.
- **Cross-reference** — [`CREATOR-CORE-KLICKD.md`](./CREATOR-CORE-KLICKD.md)
  is the authoritative concept note for this row.

| Framework | URL | Status | License |
|---|---|---|---|
| UNESCO MIL Curriculum | https://www.unesco.org/en/media-information-literacy | stable | `TO_VERIFY` |
| EntreComp (EU JRC) | https://joint-research-centre.ec.europa.eu/scientific-activities/entrecomp-entrepreneurship-competence-framework_en | stable | open — `TO_VERIFY` per-asset |
| C2PA Content Credentials | https://c2pa.org/specifications/ | evolving | open spec — `TO_VERIFY` |

---

### 3.9 Agriculture / Nature / Environment

- **Base competencies** — referenced via:
  - **GreenComp** (European Sustainability Competence Framework, JRC).
  - **FAO Competency Framework** for food and agriculture professionals
    (`TO_VERIFY` on external referenceability).
  - **ESCO** for green / agriculture occupations (ESCO has a "green skills"
    overlay).
- **Risks** — greenwashing claims, unsourced biodiversity / climate
  assertions, region-mismatched agronomic advice, regulated-pesticide /
  livestock-handling recommendations without licence.
- **Compliance gates** — `green_claim_source_required`,
  `region_declared_for_agronomic_advice`,
  `regulated_substance_block_without_licence`, `disclaimer_required`.
- **Evidence requirements** — peer-reviewed study, FAO / IPCC / IPBES
  reference, national agricultural advisory reference.
- **Human veto** — `on_threshold` (public claims, official-looking advisory).
- **Tool policy hint** — allow: dataset read (climate, biodiversity),
  literature search; block: any tool that prescribes regulated substances
  autonomously.

| Framework | URL | Status | License |
|---|---|---|---|
| GreenComp (EU JRC) | https://publications.jrc.ec.europa.eu/repository/handle/JRC128040 | stable | open — `TO_VERIFY` per-asset |
| FAO Competency Framework | https://www.fao.org/employment/competency-framework/en/ | stable | `TO_VERIFY` |
| ESCO — Green skills overlay | https://esco.ec.europa.eu/en/about-esco/escopedia/escopedia/green-skills | stable | CC BY 4.0 — `TO_VERIFY` |

---

### 3.10 Architecture / Construction

- **Base competencies** — referenced via:
  - **UIA (International Union of Architects)** Accord on Recommended
    International Standards of Professionalism.
  - **EQF** for qualifications mapping.
  - **ESCO** for occupation-level mapping.
- **Risks** — building-code mismatch with jurisdiction, fire-safety
  hallucination, unstamped technical drawings, accessibility-standard
  oversight.
- **Compliance gates** — `licensed_architect_sign_off_required_for_stamped_output`,
  `building_code_jurisdiction_declared`,
  `accessibility_standard_referenced`,
  `fire_safety_review_gate`.
- **Evidence requirements** — building-code clause ID + jurisdiction +
  edition; accessibility standard (e.g. EN 17210, ADA) ID + date.
- **Human veto** — `always` for stamped deliverables.
- **Tool policy hint** — allow: code search, BIM read, sandbox calc; block:
  stamped-deliverable export.

| Framework | URL | Status | License |
|---|---|---|---|
| UIA Accord | https://www.uia-architectes.org/en/resource/uia-accord/ | stable | `TO_VERIFY` |
| EQF | https://europa.eu/europass/en/europass-tools/european-qualifications-framework | stable | open — `TO_VERIFY` |
| EN 17210 (Accessibility) | https://www.cencenelec.eu/ | stable | restricted (CEN-CENELEC standards) — `TO_VERIFY` |

---

### 3.11 Customer support

- **Base competencies** — referenced via:
  - **ESCO** for customer-service occupations.
  - **HDI / SDI** support competency models (`TO_VERIFY` on
    referenceability terms).
- **Risks** — refund / compensation outside policy, escalation matrix
  mishandled, SLA mis-promise, tone-of-voice drift, sensitive-topic
  routing failure.
- **Compliance gates** — `policy_id_required_per_promise`,
  `refund_threshold_check`, `supervisor_sign_off_above_threshold`,
  `escalation_for_sensitive_topics`.
- **Evidence requirements** — policy ID + version + date.
- **Human veto** — `on_threshold` (above refund/compensation threshold).
- **Tool policy hint** — allow: ticket read/write within scope, KB read;
  block: direct billing-system writes, account closure.

| Framework | URL | Status | License |
|---|---|---|---|
| ESCO — Customer service | https://esco.ec.europa.eu/ | stable | CC BY 4.0 — `TO_VERIFY` |
| HDI / SDI support competencies | https://www.thinkhdi.com/ | stable | restricted — `TO_VERIFY` |

---

### 3.12 Sales

- **Base competencies** — referenced via:
  - **ESCO** for sales-related occupations.
  - National sales certifications where applicable (`TO_VERIFY`).
- **Risks** — unsourced product / competitor claim, regulated-claim risk
  (health / finance / legal), GDPR-style consent issues in outreach,
  pricing or contract misrepresentation.
- **Compliance gates** — `competitor_comparison_sourced`,
  `outreach_consent_basis_declared`, `disclaimer_required_for_regulated_claim`,
  `contract_term_sign_off_above_threshold`.
- **Evidence requirements** — product-spec doc ID + date, competitor source
  ID + date.
- **Human veto** — `on_threshold` (contract terms, public-facing comparisons).
- **Tool policy hint** — allow: CRM read, product catalog read; block:
  contract execution, pricing override without sign-off.

| Framework | URL | Status | License |
|---|---|---|---|
| ESCO — Sales occupations | https://esco.ec.europa.eu/ | stable | CC BY 4.0 — `TO_VERIFY` |

---

### 3.13 HR

- **Base competencies** — referenced via:
  - **ESCO** for HR occupations.
  - **CIPD Professional Map** (UK / EU practice) — `TO_VERIFY` on
    referenceability terms.
  - **SHRM Competency Model** (US practice) — `TO_VERIFY`.
- **Risks** — discrimination / bias in recommendations, breach of employment
  law per jurisdiction, candidate-data leakage, automated-decision-making
  exposure under EU AI Act / GDPR Art. 22.
- **Compliance gates** — `jurisdiction_of_employment_law_declared`,
  `automated_decision_disclosure`, `bias_audit_ref_for_screening_outputs`,
  `human_review_required_for_hiring_recommendation`.
- **Evidence requirements** — policy ID, statute reference per jurisdiction.
- **Human veto** — `always` for any output influencing hiring / promotion /
  termination.
- **Tool policy hint** — allow: HRIS read within scope, KB read; block:
  scoring-based shortlisting without human review.

| Framework | URL | Status | License |
|---|---|---|---|
| ESCO — HR occupations | https://esco.ec.europa.eu/ | stable | CC BY 4.0 — `TO_VERIFY` |
| CIPD Profession Map | https://www.cipd.org/en/the-people-profession/the-profession-map/ | stable | restricted — `TO_VERIFY` |
| SHRM Competency Model | https://www.shrm.org/credentials/certification/educators/competency-model | stable | restricted — `TO_VERIFY` |

---

### 3.14 Compliance

- **Base competencies** — referenced via:
  - **ESCO** for compliance occupations.
  - **GRC Capability Model (OCEG Red Book)** — `TO_VERIFY`.
- **Risks** — regulator-misaligned wording, jurisdiction confusion,
  missed-deadline regulatory filing, hallucinated regulation citation.
- **Compliance gates** — `regulator_declared`, `jurisdiction_declared`,
  `regulation_citation_required_per_claim`, `human_sign_off_for_filing`.
- **Evidence requirements** — regulation ID + article + jurisdiction + date.
- **Human veto** — `always` for any regulatory filing or public
  representation of compliance posture.
- **Tool policy hint** — allow: regulation KB read; block: direct filing
  submission.

| Framework | URL | Status | License |
|---|---|---|---|
| ESCO — Compliance occupations | https://esco.ec.europa.eu/ | stable | CC BY 4.0 — `TO_VERIFY` |
| OCEG GRC Capability Model | https://www.oceg.org/resources/red-book-3/ | stable | restricted — `TO_VERIFY` |

---

### 3.15 Cybersecurity

- **Base competencies** — referenced via:
  - **NICE Cybersecurity Workforce Framework (NIST SP 800-181 rev1)** —
    work roles, tasks, knowledge, skills, abilities.
  - **ENISA European Cybersecurity Skills Framework (ECSF)** for EU
    cross-walk.
  - **ESCO** for occupation-level mapping.
- **Risks** — disclosure of unpatched vulnerabilities to wrong audience,
  dual-use of offensive tooling, social-engineering pretext generation
  outside engagement scope, customer-data exposure in IR.
- **Compliance gates** — `engagement_scope_declared`,
  `disclosure_policy_followed`, `dual_use_tool_block_outside_scope`,
  `customer_data_redaction_required`.
- **Evidence requirements** — CVE / advisory ID, engagement letter
  reference, MITRE ATT&CK technique ID for TTP claims.
- **Human veto** — `always` for offensive-action authorisation, public
  disclosure.
- **Tool policy hint** — allow: read-only recon within scope, defensive
  KB read; block: exploit execution outside scope, public disclosure
  without sign-off.

| Framework | URL | Status | License |
|---|---|---|---|
| NICE Framework (NIST SP 800-181 rev1) | https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-181r1.pdf | stable | public domain (US gov) — `TO_VERIFY` |
| ENISA ECSF | https://www.enisa.europa.eu/topics/education/european-cybersecurity-skills-framework | stable | open — `TO_VERIFY` per-asset |
| MITRE ATT&CK | https://attack.mitre.org/ | stable | open (Apache 2.0 terms — `TO_VERIFY`) |

---

### 3.16 Robotics

- **Base competencies** — referenced via:
  - **ESCO** for robotics-adjacent occupations.
  - **ISO 10218** (industrial robots, safety) and **ISO/TS 15066**
    (collaborative robots) referenced for safety competencies.
  - **EQF** levels for engineering qualifications.
- **Risks** — unsafe trajectory, missing human-detection safeguard,
  certification mismatch, dual-use export-controlled capability.
- **Compliance gates** — `safety_standard_declared`,
  `human_proximity_safeguard_required`, `export_control_screen`,
  `licensed_engineer_sign_off_for_deployment`.
- **Evidence requirements** — standard ID + edition + date, safety case
  document reference.
- **Human veto** — `always` for deployment to a non-controlled environment.
- **Tool policy hint** — allow: simulation sandbox, KB read; block:
  real-hardware actuation without explicit human authorisation per session.

| Framework | URL | Status | License |
|---|---|---|---|
| ISO 10218 | https://www.iso.org/standard/73933.html | stable | restricted (ISO licensing) — `TO_VERIFY` |
| ISO/TS 15066 | https://www.iso.org/standard/62996.html | stable | restricted — `TO_VERIFY` |
| ESCO — Robotics occupations | https://esco.ec.europa.eu/ | stable | CC BY 4.0 — `TO_VERIFY` |

---

### 3.17 Public sector

- **Base competencies** — referenced via:
  - **OECD Public Service Leadership and Capability framework**.
  - **EU Common Training Framework / EUPAN** references where applicable
    (`TO_VERIFY`).
  - **ESCO** for public-administration occupations.
- **Risks** — administrative-law mismatch, discriminatory automated
  decision exposure (EU AI Act high-risk for public services),
  citizen-data handling under GDPR, transparency-of-decision obligations.
- **Compliance gates** — `automated_decision_disclosure_required`,
  `administrative_law_jurisdiction_declared`,
  `citizen_appeal_pathway_declared`,
  `human_review_required_for_decision_affecting_citizen`.
- **Evidence requirements** — statute / regulation ID + jurisdiction +
  date, internal procedure ID.
- **Human veto** — `always` for any decision affecting an individual citizen.
- **Tool policy hint** — allow: KB read, case-management read within scope;
  block: any tool emitting a binding decision autonomously.

| Framework | URL | Status | License |
|---|---|---|---|
| OECD Public Service Leadership & Capability | https://www.oecd.org/governance/pem/ | stable | `TO_VERIFY` |
| EU AI Act (high-risk public-sector annex) | https://eur-lex.europa.eu/eli/reg/2024/1689/oj | stable | open (EU law) |
| ESCO — Public administration | https://esco.ec.europa.eu/ | stable | CC BY 4.0 — `TO_VERIFY` |

---

### 3.18 Personal productivity

- **Base competencies** — referenced via:
  - **LifeComp** (European Personal, Social and Learning to Learn
    competence framework, JRC).
  - **DigComp 2.2** for the digital-skills overlay.
- **Risks** — over-collection of user habits / health data, profiling drift,
  scope creep into therapy / coaching territory without licence.
- **Compliance gates** — `data_minimisation_default`,
  `no_health_advice_without_disclaimer`,
  `local_first_storage_default`, `consent_per_purpose`.
- **Evidence requirements** — none for personal logs; for any factual
  claim, `claim_sources` applies as in other domains.
- **Human veto** — `optional` (this is the *user's own* assistant).
- **Tool policy hint** — allow: local-store read/write, calendar/task
  capability; block: third-party telemetry, broadcast / publish without
  explicit consent.

| Framework | URL | Status | License |
|---|---|---|---|
| LifeComp (EU JRC) | https://publications.jrc.ec.europa.eu/repository/handle/JRC123624 | stable | open — `TO_VERIFY` per-asset |
| DigComp 2.2 (EU JRC) | https://publications.jrc.ec.europa.eu/repository/handle/JRC128415 | stable | open — `TO_VERIFY` per-asset |

---

## 4. Cross-cutting framework references

The recurring frameworks above are summarised here for a single
authoritative table. **License columns are conservative**: anything not
explicitly verified by a maintainer is marked `TO_VERIFY` — that is *not*
a claim of restriction, only an absence of confirmation.

| Framework | Steward | URL | Scope | Status | License |
|---|---|---|---|---|---|
| **ESCO** | European Commission (DG EMPL) | https://esco.ec.europa.eu/ | EU multilingual occupations + skills + qualifications | stable, versioned | open data CC BY 4.0 — `TO_VERIFY` per asset |
| **EQF** | European Commission | https://europa.eu/europass/en/european-qualifications-framework-eqf | EU qualification levels 1–8 | stable | open — `TO_VERIFY` per asset |
| **ISCO-08** | ILO / OIT | https://www.ilo.org/public/english/bureau/stat/isco/isco08/ | International occupation classification | stable | open with attribution — `TO_VERIFY` |
| **O\*NET** | US DoL / National Center for O\*NET Development | https://www.onetonline.org/ | US occupations + skills database | stable, frequently updated | public domain (US gov source) — `TO_VERIFY` |
| **SFIA** | SFIA Foundation | https://sfia-online.org/ | IT skills (global) | stable | restricted (free for individuals; commercial licensing required) — `TO_VERIFY` / `USER_ORG_RESPONSIBILITY` (see §3.5 SFIA governance rule) |
| **DigComp 2.2** | EU JRC | https://publications.jrc.ec.europa.eu/repository/handle/JRC128415 | Digital competence for citizens | stable | open EU reuse — `TO_VERIFY` |
| **EntreComp** | EU JRC | https://joint-research-centre.ec.europa.eu/scientific-activities/entrecomp-entrepreneurship-competence-framework_en | Entrepreneurial competence | stable | open EU reuse — `TO_VERIFY` |
| **GreenComp** | EU JRC | https://publications.jrc.ec.europa.eu/repository/handle/JRC128040 | Sustainability competence | stable | open EU reuse — `TO_VERIFY` |
| **LifeComp** | EU JRC | https://publications.jrc.ec.europa.eu/repository/handle/JRC123624 | Personal, social, learning-to-learn | stable | open EU reuse — `TO_VERIFY` |
| **NICE Framework** | NIST (US) | https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-181r1.pdf | Cybersecurity workforce | stable | US gov publication, public domain — `TO_VERIFY` |
| **ENISA ECSF** | ENISA (EU) | https://www.enisa.europa.eu/topics/education/european-cybersecurity-skills-framework | EU cybersecurity workforce | stable | open — `TO_VERIFY` |
| **CanMEDS 2015** | Royal College of Physicians & Surgeons of Canada | https://www.royalcollege.ca/rcsite/canmeds/canmeds-framework-e | Physician competencies | stable | `TO_VERIFY` |
| **CEFR** | Council of Europe | https://www.coe.int/en/web/common-european-framework-reference-languages | Languages | stable | `TO_VERIFY` |
| **UNESCO ICT-CFT v3** | UNESCO | https://unesdoc.unesco.org/ark:/48223/pf0000265721 | Teacher ICT competencies | stable | `TO_VERIFY` |
| **UNESCO AI Competency Framework for Teachers (2024)** | UNESCO | https://unesdoc.unesco.org/ark:/48223/pf0000391105 | Teacher AI competencies | new | `TO_VERIFY` |
| **OECD Learning Compass 2030** | OECD | https://www.oecd.org/education/2030-project/ | Learner competencies | evolving | `TO_VERIFY` |
| **Int'l Engineering Alliance** | IEA | https://www.ieagreements.org/ | Engineering graduate attributes & professional competencies | stable | `TO_VERIFY` |
| **VITAE RDF** | VITAE (UK) | https://www.vitae.ac.uk/researchers-professional-development/about-the-vitae-researcher-development-framework | Researcher development | stable | restricted — `TO_VERIFY` |
| **IFAC IES** | IFAC | https://www.ifac.org/ | Accountant education standards | stable | `TO_VERIFY` |
| **MITRE ATT&CK** | MITRE | https://attack.mitre.org/ | Adversary TTPs | stable | open — `TO_VERIFY` |
| **C2PA Content Credentials** | C2PA Coalition | https://c2pa.org/specifications/ | Content provenance | evolving | open spec — `TO_VERIFY` |

> **Recommendation.** Before a future RFC promotes any field that
> *embeds* content from any of these frameworks, a maintainer MUST
> independently confirm the embedding terms (URL, version, license, per-row
> attribution requirement, and any commercial-use limitation). Until then,
> the safe pattern is **reference-by-ID-and-URL only**, never embed.

> **Default-seed rule (open-first).** For any `domain_profile` that
> Klickd itself **ships as a default seed** (i.e. published from this
> repo, not authored by a third-party publisher), maintainers SHOULD
> prefer frameworks whose row above is **open / public** (CC BY, EU
> reuse, US gov public domain, open spec) over frameworks marked
> `restricted` or `TO_VERIFY / USER_ORG_RESPONSIBILITY`. Restricted
> frameworks (e.g. SFIA, CFA CBOK, ISO standards, CIPD, SHRM, HDI,
> CanMEDS depending on terms) MAY be **listed as referenceable
> alternatives** that a user, agent, or org can opt into under their own
> licence — but they MUST NOT be the only path a seeded profile
> provides, and their content MUST NOT be embedded into the seed.

> **`USER_ORG_RESPONSIBILITY` marker (clarification).** A row tagged
> `USER_ORG_RESPONSIBILITY` (in addition to `TO_VERIFY`) signals that
> the framework has a known licence regime requiring an active
> agreement for non-individual / commercial use, and that the burden
> of holding that agreement falls on the **user / org** that chooses
> to integrate the framework into their own `domain_profile` — not on
> Klickd. Klickd's role is limited to providing the **reference
> pointer** (ID, version, URL, status) so users can find the source of
> truth. SFIA is the canonical example of this pattern today; the same
> marker applies to any other framework whose terms forbid embedding
> or commercial redistribution without a licence.

---

## 5. Roadmap (P0 / P1 / P2)

This document is explicitly **non-blocking** for V4 GA. The roadmap below
mirrors the prioritisation pattern used in
[`CREATOR-CORE-KLICKD §8`](./CREATOR-CORE-KLICKD.md).

### P0 (catalog docs — this PR)

- **P0-D-1 — This file.** `docs/use-cases/DOMAIN_PROFILE_CATALOG.md`
  captures the four scopes, the composition rule, the principle of
  composing existing primitives before minting new ones, and the seed
  list of 18 domains with framework references.
- **P0-D-2 — Reference cross-links.** Link in / from
  [`CORE_KLICKD_B2B.md §8`](./CORE_KLICKD_B2B.md),
  [`CREATOR-CORE-KLICKD.md §3.3`](./CREATOR-CORE-KLICKD.md),
  [`RFC-006 §14`](../rfcs/RFC-006-agent-core.md) — *deferred to a
  follow-up PR to keep this one strictly additive.*

### P1 (examples — docs-only, post-merge)

- **P1-D-1 — Worked example file.** A single illustrative
  `examples/v4-preview/domain-profile.example.md` that shows how three
  domains (e.g. `med`, `dev`, `legal`) would look as `<domain>_profile`
  payloads referenced by a single `core.<Agent>.klickd`. Markdown only;
  not a JSON vector.
- **P1-D-2 — Framework licence verification log.** A docs-only
  `docs/use-cases/DOMAIN_FRAMEWORK_LICENSES.md` that, for each framework
  marked `TO_VERIFY` above, captures the actual terms with date checked
  and the maintainer who verified. Promotes `TO_VERIFY` rows to
  `verified` or `restricted-confirmed`.
- **P1-D-3 — Audit cross-link in CORE_KLICKD_B2B / CREATOR-CORE.** Tiny
  edits adding "see DOMAIN_PROFILE_CATALOG" pointers in both companion
  notes (kept out of this PR to avoid widening scope).

### P2 (schema / future RFC — post-V4 GA)

- **P2-D-1 — RFC-008 (tentative) — `domain_profile` v1.** Promote the
  catalog into a normative RFC. Defines the `<domain>_profile` section,
  `competency_map[]`, `compliance_gates`, `tool_policy` (capability-level),
  and the composition rule with `core.*` and `user.*`. **Depends on:**
  V4 GA closed; RFC-006 promoted past `Proposed`; framework licence log
  (P1-D-2) complete for at least the EU JRC frameworks.
- **P2-D-2 — Per-domain RFCs (as needed).** Only spawn a dedicated RFC
  for a domain that *cannot* express itself through the generic
  `<domain>_profile` shape. The default expectation is **zero per-domain
  RFCs**; the catalog should be sufficient.
- **P2-D-3 — Lint surface.** Linter rules referencing the catalog (no
  client data, no embedded framework content, framework reference must
  resolve, jurisdiction declared where required). Stay docs-only until a
  schema lands.
- **P2-D-4 — Composition vectors.** Once schemas are strict, add a
  conformance vector per domain that exercises the
  `core` × `domain_profile` × `user` × `project` composition.

---

## 6. Risks (specific to this catalog)

| Risk | Type | Mitigation |
|---|---|---|
| **Premature normativity.** Readers treat the seed list as a closed enumeration of allowed domains. | Adoption / governance | This document opens with a non-normative banner; the per-domain rows are explicitly seed material; the principle in §2 favours composition over enumeration. |
| **Licence overclaim.** Marking a restricted framework as "open" creates legal risk for downstream integrators. | Legal | Every framework cell is marked `TO_VERIFY` unless a maintainer has independently confirmed; the P1-D-2 verification log is the path to promotion. |
| **Framework drift.** ESCO / O\*NET / DigComp / NICE all version their content. A profile referencing "ESCO 2611" without version is brittle. | Adoption | Future RFC SHOULD require `framework_version` + `framework_revision_date` per `competency_map[]` entry, and treat missing version as a lint warning. |
| **Domain coverage bias.** The seed list over-indexes on EU + Anglophone frameworks. | Equity | Document explicitly acknowledges this; future P1 work should add cross-walks to non-EU frameworks (e.g. ILO ISCO is global, but national equivalents matter for compliance). |
| **Embedded content via copy-paste.** A future contributor copies a framework's competency list into the catalog or into an example file, inheriting third-party licensing. | Legal | The catalog states the rule explicitly in §4 and §1.2: **reference by ID + URL only**, never embed. P2-D-3 lint should encode this. |
| **Restricted-framework redistribution (e.g. SFIA).** A future contributor embeds SFIA (or any framework tagged `USER_ORG_RESPONSIBILITY`) skill definitions / level descriptors into a seed `dev_profile`, or ships them as part of a Klickd-published artefact without a SFIA licence. | Legal | §3.5 SFIA governance rule + §4 default-seed rule: Klickd / `.klickd` MUST NOT embed, copy, redistribute, derive, or sell SFIA content as-is unless a proper SFIA licence is obtained by the publisher. SFIA stays **reference-only** (ID + version + URL); the licence burden falls on the user / org that integrates SFIA-derived content. Default Klickd-shipped seeds prefer open frameworks (ESCO ICT, EU e-CF refs). |
| **Surface creep into Klickd-branded taxonomy.** "Klickd Skills v1" gets minted as a rival to ESCO/SFIA. | Adoption | The catalog is a *router* to authoritative frameworks, not a competing one. Any future Klickd-internal vocabulary SHOULD be limited to *gluing* official references together, never replacing them. |
| **Domain pack as backdoor for org rules.** A `<domain>_profile` ships with org-specific workflow / vendor names. | Portability | §1.2 prohibits this; org workflow lives in `core.<agent>.klickd`. P2-D-3 lint should reject vendor names in `<domain>_profile` `tool_policy`. |
| **User-PII leakage.** A worked example accidentally embeds a real user or patient case. | Privacy | All examples in this document are framework references only; no fabricated nor real case data. RFC-006 §6 + CORE_KLICKD_B2B §2.1 invariants apply transitively. |

---

## 7. Open questions

- **Naming.** `<domain>_profile` vs `domain_pack` vs `competency_profile`?
  The catalog uses `<domain>_profile` for symmetry with `media_profile`,
  `creator_profile`, `agent_core`; a future RFC SHOULD lock the name once.
- **Per-domain vs generic schema.** Should `med_profile`, `legal_profile`,
  `dev_profile` share a single generic shape with domain-specific
  competency maps, or each get a dedicated subschema? The catalog defaults
  to **single generic shape**; deviation only if a domain proves it cannot
  fit (e.g. robotics safety-case shape).
- **Composition with `extensions[]`.** Where exactly does
  `<domain>_profile` live — top-level next to `agent_core`, inside
  `agent_core.domain_profile`, or as an entry in `extensions[]`? The
  catalog stays agnostic; RFC-006 §7 injection slices give the host the
  composition contract regardless.
- **Multi-domain agents.** A `core.<Agent>.klickd` covering both
  `legal` and `compliance` — list of profiles or composed profile? The
  catalog suggests a list; ordering matters for conflict resolution
  (most-restrictive wins).
- **Versioning the catalog itself.** Should this file carry its own
  version line, or live as a moving document until promoted to an RFC?
  Current choice: moving doc, frozen at RFC promotion time.
- **Non-Western frameworks.** A future P1 task SHOULD survey
  competency frameworks outside EU / US / Anglophone Commonwealth (e.g.
  ASEAN Qualifications Reference Framework, African Continental
  Qualifications Framework, national frameworks in Japan, Korea, Brazil).
- **Conflict between `<domain>_profile` and a regulator update.** A
  framework reference can go stale faster than this catalog. The
  composition rule should require `last_reviewed` per `competency_map[]`
  entry and treat staleness as a lint warning.

---

## 8. What this document does **not** do

- It **does not** add any normative field to `.klickd` v3.5.1 or v4.
- It **does not** publish a Klickd-branded competency taxonomy.
- It **does not** trigger any release (no tag, no npm, no PyPI, no
  Zenodo, no DOI).
- It **does not** modify any `locked_*` field, schema, SDK, vector, or
  RFC status.
- It **does not** claim that any referenced framework is openly licensed
  for embedding unless the row says so explicitly *and* a maintainer has
  signed the framework licence verification log (P1-D-2 — not yet
  created).
- It **does not** supersede [RFC-006](../rfcs/RFC-006-agent-core.md),
  [CORE_KLICKD_B2B](./CORE_KLICKD_B2B.md), or
  [CREATOR-CORE-KLICKD](./CREATOR-CORE-KLICKD.md). It complements them
  by giving the per-domain seed list those three documents gesture at
  without enumerating.

---

*Document vivant. Toute modification passe par une PR. This is a concept
catalog, not a specification.*
