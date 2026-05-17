# Klickd Curriculum Feeds

Public, signed curriculum JSON feeds for the `.klickd` annual sync protocol.

Each file covers one subject × one level × one country × one year.

## Structure

```
curriculum/
├── LU/          Luxembourg — MENJE
├── FR/          France — Eduscol / DGESCO
├── BE/          Belgium — Fédération Wallonie-Bruxelles
├── DE/          Germany — KMK (Kultusministerkonferenz)
├── MA/          Morocco — MEN Maroc
├── SN/          Senegal — MENA
└── CA/          Canada — Provincial ministries (QC, ON, BC)
```

## File naming convention

```
{subject_id}-{level}-{year}.json
```

Examples:
- `LU/maths-5e-2025.json`
- `FR/maths-terminale-2025.json`
- `BE/francais-s3-2025.json`

## Schema per file

```json
{
  "meta": {
    "country": "LU",
    "authority": "MENJE",
    "subject": "Mathématiques",
    "subject_id": "MATH",
    "level": "5e",
    "year": 2025,
    "language": "fr",
    "source": "https://official-source-url"
  },
  "competencies": [
    {
      "id": "MENJE-MATH-5E-01",
      "domain": "Algèbre",
      "label": "Résoudre des équations du premier degré",
      "eqf_level": 2,
      "keywords": ["équation", "inconnue"]
    }
  ]
}
```

## Contributing

To add a curriculum feed:
1. Create a file following the naming convention
2. Reference the official source in `meta.source`
3. Map competency IDs to official identifiers where available
4. Open a PR

## Authorities & sources

| Country | Authority | Official URL |
|---------|-----------|-------------|
| 🇱🇺 LU | MENJE | https://portal.education.lu |
| 🇫🇷 FR | Eduscol | https://eduscol.education.fr |
| 🇧🇪 BE | FWB | https://www.enseignement.be/referentiels |
| 🇩🇪 DE | KMK | https://www.kmk.org/themen/schule/bildungsstandards.html |
| 🇲🇦 MA | MEN | https://www.men.gov.ma |
| 🇸🇳 SN | MENA | https://www.education.gouv.sn |
| 🇨🇦 CA | Provincial | https://www.education.gouv.qc.ca (QC) |

*All curriculum data is sourced from public official documents. CC0.*
