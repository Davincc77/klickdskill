# klickd-proof-protocol — Agent Skill

**Version:** 1.1  
**Protocol:** `klickd-proof-protocol`  
**License:** CC0 1.0 Universal (Public Domain)  
**Source:** https://github.com/Davincc77/klickd-proof-protocol  
**Maintained by:** Klickd (https://klickd.app) — Luxembourg

---

## What this skill is

This skill teaches any AI agent how to:
1. **Generate** a `.klickd` session file at the end of a learning session
2. **Ingest** a `.klickd` file at the start of a new session to restore context
3. **Adapt its behavior** based on the decoded profile
4. **Run Proof Mode** — zero-persistence knowledge verification
5. **Populate domain-specific fields** depending on the subject area

The `.klickd` format is open, client-side, privacy-first. No server ever sees the payload. The agent never stores data — the user owns the file.

---

## Core principle

> **Kai forgets. The user doesn't.**

At the end of every session, the agent helps the user export a `.klickd` file. At the start of the next session, the user uploads it. The agent re-reads the profile and continues as if no time passed — without any server-side memory.

---

## Architecture

```
[Session ends]
     │
     ▼
Agent generates profile JSON
     │
     ▼
Browser encrypts with AES-GCM 256 (key = PBKDF2 from user password)
     │
     ▼
.klickd file downloaded locally
     │
     ▼  (next session)
User uploads .klickd
     │
     ▼
Browser decrypts with user password
     │
     ▼
Agent receives plaintext profile JSON → adapts behavior
```

**Zero server calls. Zero telemetry. Fully offline-capable.**

---

## Step-by-step agent behavior

### On session START

1. Ask the user: *"Do you have a .klickd file to load?"*
2. If yes → receive decrypted profile JSON (the app handles decryption)
3. Parse the `domain` field to activate domain-specific logic (see below)
4. Read `profile.mastered`, `profile.weak_points`, `profile.preferred_style`
5. Personalize greeting and first question accordingly
6. **Do not ask questions the user already mastered** (check `mastered[]`)
7. Start with topics in `last_topics[]` or known `weak_points[]`

### During session (Proof Mode)

Proof Mode = zero persistence, active knowledge verification.

1. After explaining a concept, wait for the user to signal readiness
2. Ask a verification question (open question, exercise, or request for explanation)
3. Evaluate the answer:
   - Score ≥ 0.80 → add topic to `mastered[]` candidate
   - Score < 0.50 → add to `weak_points[]` candidate
   - Between → mark as `in_progress`
4. Track results in `proof_results[]` (in memory only — not sent anywhere)
5. Adjust teaching style in real time based on answers

### On session END

1. Compile the updated profile (see domain schemas below)
2. Output the profile JSON to the app layer
3. The app encrypts and offers the `.klickd` file for download
4. Tell the user: *"Your .klickd file is ready. Load it next time to continue where we left off."*
5. **Clear all session memory** — nothing persists on the agent side

---

## Domain schemas

The `profile` object contains a mandatory `domain` field. Each domain extends the base profile with relevant fields.

### Base profile (all domains)

```json
{
  "domain": "string (required)",
  "subjects": ["string"],
  "mastered": ["string"],
  "weak_points": ["string"],
  "in_progress": ["string"],
  "preferred_style": "socratic | direct | example-first | visual | auto",
  "language": "fr | en | de | lb | ...",
  "last_topics": ["string"],
  "session_count": 0,
  "notes": "free text, max 1000 chars",
  "custom": {}
}
```

The `custom` object is reserved for implementers to add non-standard fields without breaking the schema.

---

### Domain: `education`

For school subjects (math, physics, languages, history, etc.)

```json
{
  "domain": "education",
  "subjects": ["mathematics", "french", "physics"],
  "mastered": ["quadratic equations", "passé composé agreement"],
  "weak_points": ["logarithms", "subjunctive"],
  "curriculum": "Luxembourg | France | Belgium | Germany | IB | custom",
  "level": "primary | lower_secondary | upper_secondary | university | adult",
  "exam_targets": ["Bac S", "BTS", "DELF B2"],
  "proof_results": [
    {
      "topic": "quadratic equations",
      "score": 0.92,
      "date": "2026-05-16T16:45:00Z",
      "method": "open_question | exercise | explanation"
    }
  ]
}
```

**Agent behavior for education:**
- Map topics to curriculum level before testing
- For mathematics: use `·` for multiplication, superscript for powers (`x²`), `1/4` for fractions
- For languages: track grammar rules separately from vocabulary
- Respect `exam_targets` — prioritize topics likely to appear in the target exam
- Use `proof_results.score` to decide whether to re-test or move on

---

### Domain: `language_learning`

For standalone language acquisition (not part of a school curriculum)

```json
{
  "domain": "language_learning",
  "target_language": "de",
  "native_language": "fr",
  "cefr_level": "A1 | A2 | B1 | B2 | C1 | C2",
  "vocabulary_known": ["Haus", "gehen", "weil"],
  "grammar_mastered": ["present tense", "accusative case"],
  "grammar_weak": ["subjunctive II", "genitive"],
  "preferred_correction_style": "immediate | end_of_turn | never",
  "immersion_mode": false
}
```

**Agent behavior:**
- If `immersion_mode: true` → respond only in `target_language`
- Track vocabulary and grammar separately
- Use `cefr_level` to calibrate complexity of sentences and explanations

---

### Domain: `professional`

For corporate training, upskilling, certification prep

```json
{
  "domain": "professional",
  "field": "software_engineering | finance | law | medicine | marketing | hr | custom",
  "certifications_target": ["AWS SAA", "CFA Level 1"],
  "certifications_obtained": ["Google Cloud ACE"],
  "skills_mastered": ["REST API design", "DCF valuation"],
  "skills_weak": ["Kubernetes networking", "options pricing"],
  "seniority": "junior | mid | senior | lead | executive",
  "company_context": "optional — free text describing team/role for contextualization"
}
```

**Agent behavior:**
- Adapt terminology to `seniority` level
- For certification prep: cross-reference `skills_weak` with known exam domains
- Keep `company_context` private — never echo it back verbatim in responses

---

### Domain: `creative`

For writing, music, design, visual arts coaching

```json
{
  "domain": "creative",
  "discipline": "writing | music | visual_arts | game_design | filmmaking | custom",
  "projects": [
    {
      "id": "proj-001",
      "title": "Short story — Luxembourg 2080",
      "status": "in_progress",
      "last_feedback": "Structure is strong, dialogue needs work"
    }
  ],
  "style_references": ["Kafka", "Ursula K. Le Guin"],
  "recurring_weaknesses": ["show don't tell", "pacing in act 2"],
  "goals": ["finish first draft by June 2026", "submit to contest X"]
}
```

**Agent behavior:**
- Reference `projects[]` to maintain continuity across sessions
- Don't repeat feedback already given — check `last_feedback`
- Use `style_references` to calibrate tone of suggestions

---

### Domain: `wellness`

For mindfulness, mental fitness, habit coaching (non-medical)

```json
{
  "domain": "wellness",
  "focus_areas": ["stress management", "sleep hygiene", "focus"],
  "habits_tracked": ["10min meditation", "no phone before 8am"],
  "habit_streak": { "10min meditation": 7 },
  "blockers": ["evening anxiety", "inconsistent schedule"],
  "preferred_tone": "supportive | challenging | neutral"
}
```

**Agent behavior:**
- Never give medical advice — wellness only
- Use `preferred_tone` throughout session
- Celebrate streaks explicitly but briefly
- Check `blockers` before suggesting new habits

---

### Domain: `custom`

For any use case not covered above. Fully open schema.

```json
{
  "domain": "custom",
  "domain_label": "human-readable name for this domain",
  "version": "1.0",
  "fields": {
    "any_key": "any_value"
  }
}
```

Implementers using `custom` should document their schema extension and submit a PR to add it as a named domain.

---

## Extensibility guide

The klickd-proof-protocol is designed to evolve. Here's how to extend it properly:

### Adding a new domain

1. Fork the repo
2. Add a new `### Domain: your_domain` section to this file
3. Add the corresponding `$defs` entry in `schema/klickd-v1.json`
4. Add a `domain_extensions/your_domain-v1.json` schema file
5. Submit a PR with:
   - The new domain section in this skill file
   - The JSON schema
   - A short description of the use case

### Adding fields to an existing domain

1. Add new fields as **optional** (never break existing `.klickd` files)
2. Increment the `meta.version` in the spec (minor version bump: `1.0` → `1.1`)
3. Document the migration path in `SPEC.md`

### Protocol versioning

- `meta.version` in the `.klickd` file refers to the protocol version used to generate it
- Agents MUST handle files from any past version gracefully (ignore unknown fields)
- Breaking changes require a major version bump (`1.x` → `2.0`) and a migration tool

### Adding new proof methods

Current methods: `open_question`, `exercise`, `explanation`

To add a new method:
1. Define it in `SPEC.md` under `§ Proof Methods`
2. Add it to the `method` enum in `schema/klickd-v1.json`
3. Document expected agent behavior in this skill under the relevant domain

---

## Minimal implementation example

```javascript
// At session end — generate and download .klickd file (browser)
async function exportSession(profile, password) {
  const encoder = new TextEncoder();
  const salt = crypto.getRandomValues(new Uint8Array(16));
  const iv   = crypto.getRandomValues(new Uint8Array(12));

  const keyMaterial = await crypto.subtle.importKey(
    "raw", encoder.encode(password), "PBKDF2", false, ["deriveKey"]
  );
  const key = await crypto.subtle.deriveKey(
    { name: "PBKDF2", salt, iterations: 310000, hash: "SHA-256" },
    keyMaterial,
    { name: "AES-GCM", length: 256 },
    false, ["encrypt"]
  );

  const ciphertext = await crypto.subtle.encrypt(
    { name: "AES-GCM", iv },
    key,
    encoder.encode(JSON.stringify(profile))
  );

  const blob = new Uint8Array(salt.byteLength + iv.byteLength + ciphertext.byteLength);
  blob.set(salt, 0);
  blob.set(iv, 16);
  blob.set(new Uint8Array(ciphertext), 28);

  const b64 = btoa(String.fromCharCode(...blob))
    .replace(/\+/g, "-").replace(/\//g, "_").replace(/=/g, "");

  const file = {
    meta: {
      protocol: "klickd-proof-protocol",
      version: "1.0",
      created_at: new Date().toISOString(),
      session_count: (profile.session_count || 0) + 1
    },
    payload: b64
  };

  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([JSON.stringify(file)], { type: "application/json" }));
  a.download = "session.klickd";
  a.click();
}
```

For a full implementation reference, see the [Klickd app source](https://klickd.app).

---

## License

This skill, this protocol, and all associated files are released under **CC0 1.0 Universal (Public Domain)**.

You may use, copy, modify, and distribute this work for any purpose, without permission, without attribution.

See `LICENSE` in this repository.

---

*klickd-proof-protocol — made in Luxembourg, built for the world.*
