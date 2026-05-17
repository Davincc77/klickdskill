# Klickd Portable Memory Protocol

> **The AI memory that belongs to you. Not to us.**
> 
> An open standard for portable, encrypted, client-side AI memory — aligned with official competency frameworks from 7 countries and 4 European reference frameworks.
>
> **Made in Luxembourg. CC0 — free for everyone.**

---

## The idea

Every AI assistant forgets you when the session ends.

Some apps remember you — but they keep your data on their servers. You have no control.

Klickd flips this: the AI learns who you are, tracks your progress against official curricula, then **forgets everything**. You keep a portable encrypted file (`.klickd`) on your own device. You own it. You move it. You delete it.

This is **privacy-first AI memory** — and it works for any domain with a competency framework.

---

## What's in this repo

```
klickdskill/
├── README.md              ← you are here
├── SPEC.md                ← cryptographic specification (AES-256-GCM, Web Crypto API)
├── AGENT-SKILL.md         ← installable skill for any AI agent
├── LICENSE                ← CC0 1.0 Universal
├── schema/
│   ├── klickd-v1.json     ← original schema
│   └── klickd-v2.json     ← universal schema — EQF, ESCO, DigComp 3.0, CEFR
└── curriculum/
    ├── README.md          ← curriculum feed protocol
    ├── LU/                ← Luxembourg (MENJE)
    ├── FR/                ← France (Eduscol)
    ├── BE/                ← Belgium (FWB)
    ├── DE/                ← Germany (KMK)
    ├── MA/                ← Morocco (MEN)
    ├── SN/                ← Senegal (MENA)
    └── CA/                ← Canada/Quebec (MEQ)
```

---

## How it works — in 4 steps

```
1. SESSION STARTS
   AI reads .klickd → knows your level, country, curriculum, learning style

2. AI TEACHES
   Kai uses your country's official curriculum
   Tracks which competencies you work on

3. SESSION ENDS
   AI updates mastery levels → saves to .klickd
   Kai forgets the conversation
   You keep everything

4. NEXT SESSION
   Kai picks up exactly where you left off
   No server. No account. No tracking.
```

---

## European frameworks alignment

| Framework | What it covers | In .klickd |
|-----------|---------------|------------|
| **EQF** — European Qualifications Framework | 8 proficiency levels, all domains | `competencies[].eqf_level` |
| **ESCO v1.2** — European Skills, Competences, Occupations | 13,890 occupations + skills taxonomy | `professional.competencies[].esco_skill_uri` |
| **DigComp 3.0** — Digital Competence Framework | 5 areas, 21 competences, 4 proficiency levels | `competencies[].digcomp_area` |
| **CEFR / CECRL** — Common European Framework for Languages | A1 → C2, 5 skill areas | `language_learning.cefr_level` + skills breakdown |

---

## Supported domains

| Domain | Framework | Typical use |
|--------|-----------|-------------|
| **Education** | MENJE, Eduscol, FWB, KMK, MEN, MENA, MEQ | K-12 students, exam prep |
| **Professional** | ESCO v1.2 + EQF | Upskilling, career transitions |
| **Languages** | CEFR / CECRL | Language learning A1→C2 |
| **Digital skills** | DigComp 3.0 | Digital literacy |
| **Wellness** | WHO frameworks | Health coaching |
| **Creative** | Custom | Music, art, writing |
| **Any domain** | Custom block | Any competency referential |

---

## Curriculum feeds — 7 countries, annual sync

Each country has official competency feeds in `/curriculum/`. Once per year the `.klickd` file syncs locally — no server, verified by Ed25519 signature.

| Country | Authority | Subjects |
|---------|-----------|---------|
| 🇱🇺 Luxembourg | MENJE | Maths, FR, DE, EN, Sciences |
| 🇫🇷 France | Eduscol | Maths, Français, Sciences, Histoire |
| 🇧🇪 Belgium | FWB — Tronc commun | Maths, Français, Sciences |
| 🇩🇪 Germany | KMK — Bildungsstandards | Mathematik, Deutsch, Sciences |
| 🇲🇦 Morocco | MEN Maroc | Maths, Français, Sciences |
| 🇸🇳 Senegal | MENA | Maths, Français |
| 🇨🇦 Canada (QC) | MEQ | Maths, Français |

---

## Security

- **AES-256-GCM** encryption — Web Crypto API, runs in the browser
- **Key never leaves the device** — not stored anywhere
- Each session in history is encrypted independently
- Curriculum sync verified with **Ed25519 signatures**
- Zero telemetry. Zero server calls. Zero retention.

Full spec: [`SPEC.md`](./SPEC.md)

---

## Use this in your app

1. Read `AGENT-SKILL.md` — full instructions for any AI agent
2. Validate against `schema/klickd-v2.json`
3. Load curriculum from `curriculum/{COUNTRY}/`
4. Encrypt/decrypt with Web Crypto API per `SPEC.md`

---

## Invention disclosure

A formal invention disclosure was filed on 2026-05-16.

SHA-256: `d7045ce2b998a50fa0d42ee481c7ffc59900e7a9aeb4ccea8c039f2312d86db3`

File: [`disclosure/invention-disclosure-2026-05-16.pdf`](./disclosure/invention-disclosure-2026-05-16.pdf)

---

## Contributing

Open a PR to:
- Add curriculum feeds for new countries/levels
- Extend the schema for new domains
- Add professional frameworks (medical, legal, engineering...)
- Improve the cryptographic spec

---

## License

**CC0 1.0 Universal** — No rights reserved. Take it. Use it. Build on it. Make it better.

---

*Built in Luxembourg. For students everywhere.*  
*[klickd.app](https://klickd.app)*
