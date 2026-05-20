# .klickd — Open Learner Context Format

[![.klickd version](https://img.shields.io/badge/.klickd-v3.4-0066CC?style=flat-square&logo=json)](https://github.com/Davincc77/klickdskill)
[![License: CC0](https://img.shields.io/badge/License-CC0%201.0-lightgrey?style=flat-square)](https://creativecommons.org/publicdomain/zero/1.0/)
[![DOI](https://img.shields.io/badge/DOI-10.5281%2Fzenodo.20302252-blue?style=flat-square)](https://doi.org/10.5281/zenodo.20302252)

A portable, AI-provider-agnostic context file format that carries a user's conversation history, expertise state, and session continuity across AI models — with zero server involvement. Drop a `.klickd` file into any compatible AI client to resume exactly where you left off, regardless of whether the previous session was on GPT-4o, Claude, Gemini, or Llama.

---

## Quick Start

```json
{
  "klickd_version": "3.4",
  "created_at": "2026-05-19T21:00:00Z",
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
pip install klickd-sdk
```

**Node.js / TypeScript**
```bash
npm install @klickd/sdk
```

---

## Examples

Five canonical example files covering the full range of use cases:

| File | Description |
|---|---|
| [`examples/student_fr.klickd`](examples/student_fr.klickd) | French high-school student, maths, socratic mode |
| [`examples/professional_en.klickd`](examples/professional_en.klickd) | Mid-level developer upskilling into ML, certification goal |
| [`examples/family_plan.klickd`](examples/family_plan.klickd) | Child profile with ADHD support and shared family context |
| [`examples/minimal.klickd`](examples/minimal.klickd) | Cold start — 5 fields only, valid v3.4 |
| [`examples/full_v34.klickd`](examples/full_v34.klickd) | Full reference file — all v3.4 fields populated |

---

## Integrations

Provider-specific guides for injecting `.klickd` context:

| Provider | Guide |
|---|---|
| OpenAI (GPT-4o, o1, …) | [`docs/integrations/openai.md`](docs/integrations/openai.md) |
| Anthropic (Claude Opus, Sonnet, …) | [`docs/integrations/anthropic.md`](docs/integrations/anthropic.md) |
| Groq (Llama, Qwen, …) | [`docs/integrations/groq.md`](docs/integrations/groq.md) |
| OpenRouter (multi-provider Soul Handoff) | [`docs/integrations/openrouter.md`](docs/integrations/openrouter.md) |
| Any provider (generic pattern) | [`docs/integrations/generic.md`](docs/integrations/generic.md) |

---

## JSON Schema

Validate `.klickd` files against the official Draft 7 schema:

```bash
# Python
pip install jsonschema
python -c "
import json, jsonschema
schema = json.load(open('schema/klickd-v3.4.schema.json'))
doc    = json.load(open('examples/student_fr.klickd'))
jsonschema.validate(doc, schema)
print('Valid.')
"
```

Schema file: [`schema/klickd-v3.4.schema.json`](schema/klickd-v3.4.schema.json)  
`$id`: `https://klickd.app/schema/v3.4.json`

---

## Benchmark Results

v3.4 benchmark — 200 profiles across 6 AI models:

| Metric | Result |
|---|---|
| Mean delta vs baseline | **+4.68** |
| Soul Handoff score | **+16** |
| Profiles evaluated | 200 |
| Models tested | GPT-4o, Claude Opus 4, Gemini 2.5 Flash, Llama 3.3 70B, Qwen3-32B, Mistral Large |

The Soul Handoff scenario measures how well a new AI model resumes a session originally started on a different model, using only the `.klickd` file as context bridge.

---

## Cite This Work

If you use `.klickd` in academic or research work, please cite:

```bibtex
@misc{klickd2026,
  title  = {.klickd — Open Learner Context Format, v3.4.1},
  author = {Cirilli, Vincenzo},
  year   = {2026},
  doi    = {10.5281/zenodo.20302252},
  url    = {https://github.com/Davincc77/klickdskill}
}
```

DOI: [10.5281/zenodo.20302252](https://doi.org/10.5281/zenodo.20302252)

---

## Badge

Add to your README if your project supports `.klickd v3.4`:

```markdown
[![.klickd compatible](https://img.shields.io/badge/.klickd-v3.4%20compatible-0066CC?style=flat-square&logo=json)](https://github.com/Davincc77/klickdskill)
```

See [`docs/badge.md`](docs/badge.md) for all badge variants (certified, experimental).

---

## Full Specification

[`SPEC.md`](SPEC.md) — 1,235 lines, version 3.4 (production)

Covers: encryption (AES-256-GCM), all field references, teaching modes, Soul Handoff, JSON Injection Guard, benchmark namespace, memory decay, shared context, and versioning policy.

---

## License

[CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/) — Public Domain.  
No permission required. No vendor lock-in.
