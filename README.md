# .klickd — Open Learner Context Format

> *When it all .klickd*

[![.klickd version](https://img.shields.io/badge/.klickd-v3.5.1-0066CC?style=flat-square&logo=json)](https://github.com/Davincc77/klickdskill)
[![License: CC0](https://img.shields.io/badge/License-CC0%201.0-lightgrey?style=flat-square)](https://creativecommons.org/publicdomain/zero/1.0/)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20320480.svg)](https://doi.org/10.5281/zenodo.20320480)

A portable, AI-provider-agnostic context file format that carries a learner's conversation history, expertise state, and session continuity across AI models — with zero server involvement. Drop a `.klickd` file into any compatible AI client to resume exactly where you left off, regardless of whether the previous session was on GPT-4o, Claude, Gemini, or Llama.

**One file. Any model. No account. No server.**

---

## Why `.klickd`?

Every major AI memory system — Mem0, PAM, Letta, OpenMemory — requires a running server, an API key, or cloud infrastructure. Your memory lives in their database, not in your hands.

`.klickd` is different: it is a self-contained, encrypted file. The server never sees your context. No runtime. No Docker. No account. You own your memory.

| | .klickd | Mem0 / OpenMemory | PAM | Letta | MeMo | agentmemory |
|---|---|---|---|---|---|---|
| Zero server process | ✅ | ❌ (Docker + Qdrant) | ❌ (SDK + transport) | ❌ (runtime) | ❌ (model infra) | ❌ (Node port 3113) |
| Client-side encryption | ✅ AES-256-GCM + Argon2id | ❌ server-side | ❌ | ❌ | ❌ | ❌ |
| No API key required | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Portable file (drag-and-drop) | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Pedagogical schema | ✅ (curriculum, mastery, CEFR) | ❌ | ❌ | ❌ | ❌ | ❌ |
| DOI-referenced benchmark | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| GDPR / Luxembourg jurisdiction | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |

---

## Try it

- [Playground](https://klickd.app/playground) — live interactive test
- [klickdskill page](https://klickd.app/klickdskill) — full documentation

---

## Quick Start

```json
{
  "klickd_version": "3.5.1",
  "created_at": "2026-05-21T00:00:00Z",
  "encrypted": false,
  "domain": "education",
  "user_preferences": "You are continuing a session with a learner working on calculus. Resume as if you have been here from the start."
}
```

Save as `profile.klickd`, then load it with any compatible SDK or inject `user_preferences` directly as a system prompt.

---

## Install SDK

**Python**
```bash
pip install klickd
```

**Node.js / TypeScript**
```bash
npm install @klickd/core
```

---

## Examples

| File | Description |
|---|---|
| [`examples/student_fr.klickd`](examples/student_fr.klickd) | French high-school student, maths, Socratic mode |
| [`examples/professional_en.klickd`](examples/professional_en.klickd) | Mid-level developer upskilling into ML |
| [`examples/family_plan.klickd`](examples/family_plan.klickd) | Child profile with ADHD support and shared family context |
| [`examples/minimal.klickd`](examples/minimal.klickd) | Cold start — 5 fields only, valid v3.5 |
| [`examples/full_v34.klickd`](examples/full_v34.klickd) | Full reference file — all fields populated |

---

## Integrations

| Provider | Guide |
|---|---|
| OpenAI (GPT-4o, o1, …) | [`docs/integrations/openai.md`](docs/integrations/openai.md) |
| Anthropic (Claude Opus, Sonnet, …) | [`docs/integrations/anthropic.md`](docs/integrations/anthropic.md) |
| Groq (Llama, Qwen, …) | [`docs/integrations/groq.md`](docs/integrations/groq.md) |
| OpenRouter (multi-provider Soul Handoff) | [`docs/integrations/openrouter.md`](docs/integrations/openrouter.md) |
| Any provider (generic pattern) | [`docs/integrations/generic.md`](docs/integrations/generic.md) |

---

## JSON Schema

```bash
pip install jsonschema
python -c "
import json, jsonschema
schema = json.load(open('schema/klickd-v3.4.schema.json'))
doc    = json.load(open('examples/student_fr.klickd'))
jsonschema.validate(doc, schema)
print('Valid.')
"
```

Schema: [`schema/klickd-v3.4.schema.json`](schema/klickd-v3.4.schema.json) — `$id`: `https://klickd.app/schema/v3.5.json`

---

## Benchmark Results (v3.5 LLM-judge)

Scorer: `qwen/qwen3-32b` via Groq — grid /10: Continuity /3 + Pedagogical Precision /3 + Adaptation /2 + Language /2.  
Full methodology and raw data: [DOI 10.5281/zenodo.20320480](https://doi.org/10.5281/zenodo.20320480)

| Sequence | Scope | Δ (WITH vs WITHOUT .klickd) |
|---|---|---|
| Seq 1 — 23 subjects, 115 profiles | Core pedagogy | **+13.9 pts avg** (min +12.8, max +19.2) |
| Seq 2 — §31 recovery, 4 profiles | Migration continuity | +9.5 (with recovery phrase) |
| Seq 3 — Soul Handoff, 10 profiles | Cross-model identity | **+14.0 pts** (IC ±7.2) |

---

## Prior Art

`.klickd` is positioned relative to the following systems in the related work section of the [Zenodo preprint](https://doi.org/10.5281/zenodo.20320480): Mem0 (Singh & Yadav, 2026), PAM (Ravindran, arXiv:2605.11032), Letta/MemGPT, Cortex (Kindly Robotics, 2026), ate/.mv2, Opal (arXiv:2604.02522), MeMo (Zeng et al., arXiv:2605.15156), and agentmemory (rohitg00, ~15K stars). To our knowledge, no existing format combines zero-process portability, client-side AES-256-GCM + Argon2id encryption, a structured pedagogical schema, and a DOI-referenced reproducible benchmark.

---

## Cite This Work

```bibtex
@misc{klickd2026,
  title  = {.klickd — Open Learner Context Format, v3.5},
  author = {Cirilli, Vincenzo},
  year   = {2026},
  doi    = {10.5281/zenodo.20320480},
  url    = {https://doi.org/10.5281/zenodo.20320480}
}
```

---

## Badge

```markdown
[![.klickd compatible](https://img.shields.io/badge/.klickd-v3.5%20compatible-0066CC?style=flat-square&logo=json)](https://github.com/Davincc77/klickdskill)
```

See [`docs/badge.md`](docs/badge.md) for all variants.

---

## Full Specification

[`SPEC.md`](SPEC.md) — covers encryption (AES-256-GCM), all field references, teaching modes, Soul Handoff, JSON Injection Guard, benchmark namespace, memory decay, shared context, and versioning policy.

---

## License

[CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/) — Public Domain. No permission required. No vendor lock-in.

---

*Made in Luxembourg · GDPR-native · klickd.app*
