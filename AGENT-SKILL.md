# Klickd Portable Memory — Agent Skill v2

> **License:** CC0 1.0 Universal — Free to use, adapt, and redistribute without restriction.
> **Repo:** https://github.com/Davincc77/klickdskill
> **Schema:** `/schema/klickd-v2.json`
> **Spec:** `/SPEC.md`

---

## What this skill does

This skill enables any AI agent to read, write, and update a `.klickd` file — a portable, AES-256-GCM encrypted, client-side memory file that belongs entirely to the user.

The AI agent learns who the user is, tracks their competency progression against official frameworks, and stores everything **locally on the user's device** — never on any server.

The `.klickd` format is domain-agnostic and framework-aligned:
- **Education:** EQF, MENJE (LU), Eduscol (FR), FWB (BE), KMK (DE), MEN (MA, SN, CA)
- **Professional:** ESCO v1.2, EQF Levels 1–8, DigComp 3.0
- **Languages:** CEFR / CECRL (A1→C2)
- **Wellness, Creative, Custom:** Extensible schema

---

## Core principles

1. **Privacy by design** — No data ever leaves the device. The AI forgets. The user keeps everything.
2. **Portability** — The `.klickd` file can be moved between apps, devices, and AI agents.
3. **Curriculum-aware** — Competencies are mapped to official national/European frameworks.
4. **Annual sync** — Curriculum data is refreshed once a year from public signed JSON feeds.
5. **Extensible** — Any domain with a competency referential can be added via the `custom` block.

---

## How to use this skill (for AI agents)

### 1. Load the user's `.klickd` file

```
READ .klickd file → decrypt with user's local key → parse JSON per klickd-v2.json schema
```

### 2. Identify context

```
meta.domain_type → determines which domain block to use
identity.country + identity.language → determines curriculum source and response language
```

### 3. Use the curriculum to guide the session

```
domain.education.subjects[].competencies[] → official competencies for this student's level
domain.education.curriculum_ref.authority → which official framework to reference
ai_profile.learning_style + preferred_explanation_style → how to explain things
```

### 4. Update mastery after each session

For each competency touched during the session, update mastery level:
```
not_started → emerging → developing → secure → mastered
```
Log the delta in `history.sessions[].mastery_deltas`.

### 5. Update ai_profile progressively

After each session, update:
- `ai_profile.strengths` — topics where user excelled
- `ai_profile.areas_to_improve` — gaps identified
- `ai_profile.session_count` + `last_session`
- `ai_profile.ai_notes` — concise observations (max 500 chars)

### 6. Save session to history (Premium)

If `history.enabled = true`:
- Write session summary, competencies_touched, mastery_deltas
- Optionally: full message log (messages[])
- Encrypt session independently with AES-256-GCM

### 7. Write back to `.klickd`

```
Update meta.updated_at + meta.file_hash → re-encrypt → save locally
```

---

## Curriculum sync protocol

Once per year (or when `curriculum_sync.pending_update = true`):

1. Fetch curriculum JSON from `curriculum_sync.sync_source` (public URL)
2. Verify Ed25519 signature (`curriculum_sync.sync_signature`)
3. Merge updated competencies into `domain.education.subjects[].competencies[]`
   - Preserve existing mastery levels
   - Add new competencies as `not_started`
   - Flag deprecated competencies
4. Update `curriculum_sync.last_sync` and `next_sync_due` (+ 1 year)

**No server contact required** — curriculum feeds are static signed JSON files hosted publicly.

---

## Supported curriculum sources

| Country | Authority | Subjects covered | Update frequency |
|---------|-----------|-----------------|-----------------|
| 🇱🇺 Luxembourg | MENJE | Maths, FR, DE, EN, Sciences, Histoire | Annual (Sept) |
| 🇫🇷 France | Eduscol / DGESCO | Socle commun, programmes lycée | Annual (Sept) |
| 🇧🇪 Belgium (FWB) | Fédération Wallonie-Bruxelles | Tronc commun, référentiels disciplinaires | Annual |
| 🇩🇪 Germany | KMK | Bildungsstandards by Bundesland | Biennial |
| 🇲🇦 Morocco | MEN Maroc | Programme officiel secondaire | Annual |
| 🇸🇳 Senegal | MENA | Programme officiel | Annual |
| 🇨🇦 Canada | Provincial ministries | By province (QC, ON, BC...) | Annual |

---

## European competency frameworks alignment

| Framework | Coverage in .klickd |
|-----------|-------------------|
| **EQF** (European Qualifications Framework, 8 levels) | `competencies[].eqf_level` — all domains |
| **ESCO v1.2** (European Skills, Competences, Qualifications, Occupations) | `domain.professional.competencies[].esco_skill_uri` |
| **DigComp 3.0** (Digital Competence Framework) | `competencies[].digcomp_area` — 5 areas, 21 competences |
| **CEFR / CECRL** (Common European Framework of Reference for Languages) | `domain.language_learning.cefr_level` + skill breakdown |
| **LifeComp** (European Framework for Personal, Social, Learning competences) | Mappable via `custom` domain block |
| **EntreComp** (Entrepreneurship Competence Framework) | Mappable via `custom` domain block |

---

## Domain examples

### Education — Luxembourg student, 5e, Maths
```json
{
  "domain_type": "education",
  "country": "LU",
  "language": "fr",
  "domain": {
    "education": {
      "level": "5e",
      "curriculum_ref": { "authority": "MENJE", "year": 2025 },
      "subjects": [{
        "subject_id": "MATH",
        "label": "Mathématiques",
        "competencies": [
          { "id": "MENJE-MATH-5E-01", "label": "Résoudre des équations du 1er degré", "mastery": "secure", "eqf_level": 2 },
          { "id": "MENJE-MATH-5E-02", "label": "Travailler avec les fonctions linéaires", "mastery": "developing", "eqf_level": 2 }
        ]
      }]
    }
  }
}
```

### Professional — Junior developer, ESCO aligned
```json
{
  "domain_type": "professional",
  "domain": {
    "professional": {
      "occupation": { "label": "Software Developer", "eqf_target_level": 6 },
      "competencies": [
        { "esco_skill_uri": "http://data.europa.eu/esco/skill/...", "label": "JavaScript programming", "mastery": "secure" },
        { "esco_skill_uri": "...", "label": "CI/CD pipeline management", "mastery": "emerging" }
      ],
      "certifications": [{ "label": "AWS Solutions Architect", "status": "in_progress", "eqf_level": 6 }]
    }
  }
}
```

### Language — CEFR B1 French learner
```json
{
  "domain_type": "language_learning",
  "domain": {
    "language_learning": {
      "target_language": "fr",
      "cefr_level": "B1",
      "skills": { "reading": "B2", "writing": "B1", "listening": "B1", "speaking": "A2" },
      "target_certification": "DELF B2"
    }
  }
}
```

---

## Extending to new domains

Any domain with a published competency referential can be added via the `custom` block:

```json
{
  "domain_type": "custom",
  "domain": {
    "custom": {
      "domain_label": "Medical — Emergency Care",
      "referential_source": "https://www.erc.edu/courses/european-resuscitation-guidelines",
      "competencies": [
        { "id": "BLS-01", "label": "Basic Life Support", "mastery": "secure" },
        { "id": "ALS-03", "label": "Airway management", "mastery": "developing" }
      ]
    }
  }
}
```

Other domains already tested:
- **Legal:** Bar competency frameworks, specific legal domains
- **Sports coaching:** UEFA/FIFA coaching licenses, technical gesture taxonomy
- **Nursing:** NMC competency standards
- **Finance:** CFA, ACCA, AMF competency maps
- **Trades:** ECVET vocational units of learning outcomes

---

## Security & privacy

- All data is encrypted with **AES-256-GCM** using Web Crypto API
- The encryption key **never leaves the user's device**
- Each session in history is encrypted independently
- Curriculum sync uses **Ed25519 signatures** — no trust required
- Zero telemetry. Zero server calls. Zero data retention.

See `/SPEC.md` for full cryptographic specification.

---

## Versioning & extensibility

The schema is versioned (`meta.schema_version`). Breaking changes will increment the major version. Agents should check `schema_version` before reading and migrate if needed.

To propose new curriculum sources or domain extensions, open a PR on [github.com/Davincc77/klickdskill](https://github.com/Davincc77/klickdskill).

---

*Made in Luxembourg. CC0 — take it, use it, build on it.*
