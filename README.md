# .klickd — One file. Any model. No server.

> *When it all .klickd*

[![.klickd version](https://img.shields.io/badge/.klickd-v4.0.0-0066CC?style=flat-square&logo=json)](https://github.com/Davincc77/klickdskill)
[![License: CC0](https://img.shields.io/badge/License-CC0%201.0-lightgrey?style=flat-square)](https://creativecommons.org/publicdomain/zero/1.0/)
[![DOI (v4.0.0)](https://zenodo.org/badge/DOI/10.5281/zenodo.20383133.svg)](https://doi.org/10.5281/zenodo.20383133)
[![Concept DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20262530.svg)](https://doi.org/10.5281/zenodo.20262530)

**Official page for the open `.klickd` format → [klickd.app/klickdskill](https://klickd.app/klickdskill)**

---

Your AI forgets you. Every. Single. Session.

You explain your level. Your goals. Your context. Then the session ends — and tomorrow, you start from zero again. Every time. With every model.

`.klickd` fixes that. One encrypted file on your device. Drop it into any AI. It picks up exactly where you left off — whether that was GPT-4o yesterday, Claude this morning, or Llama tonight.

**No account. No server. No one else holds your memory.**

---

## Positioning (v4)

`.klickd` is an **open-source security and continuity layer for every actor in AI**.

- **For users** — privacy, ownership, and memory portability: your context is a file on your device, encrypted client-side, and follows you across models.
- **For agents** — structured context and verified constraints: a strict schema for identity, preferences, gates and human-veto signals that an agent can read without inventing them.
- **For developers** — schemas, SDKs and a non-destructive migrator: Python (`klickd`) and TypeScript (`@klickd/core`) reference implementations, strict v4 JSON Schemas (Draft 2020-12), and a v3.x → v4 payload migrator.
- **For industry** — controlled, opt-in interoperability: a CC0 format with cross-implementation strict test vectors, so independent readers and writers can interoperate without ceding control of state to any single vendor.

> **One soul. Any model. Any agent.**

`.klickd` does not replace provider security, model alignment, or application-level access control; it complements them by giving the user-state layer a portable, verifiable shape.

---

## What it looks like

```json
{
  "klickd_version": "3.0",
  "payload_schema_version": "4.0",
  "created_at": "2026-05-25T00:00:00Z",
  "encrypted": false,
  "domain": "education",
  "user_preferences": "You are continuing a session with a learner working on calculus. Resume as if you have been here from the start."
}
```

Save as `profile.klickd`. Load it in any compatible client. Your AI knows who you are.

That's it.

---

## Why not just use Mem0, Letta, or OpenMemory?

They all require a running server, a Docker container, or an API key. Your memory lives in their infrastructure — not in your hands.

`.klickd` is a file. It lives on your device. It travels with you. It works offline. And it's encrypted client-side with AES-256-GCM + Argon2id — the server never sees your context.

| | .klickd | Mem0 / OpenMemory | PAM | Letta | agentmemory |
|---|---|---|---|---|---|
| Zero server process | ✅ | ❌ Docker + Qdrant | ❌ SDK + transport | ❌ runtime | ❌ Node port 3113 |
| Client-side encryption | ✅ AES-256-GCM + Argon2id | ❌ server-side | ❌ | ❌ | ❌ |
| No API key required | ✅ | ❌ | ❌ | ❌ | ✅ |
| Portable file (drag-and-drop) | ✅ | ❌ | ❌ | ❌ | ❌ |
| Pedagogical schema | ✅ curriculum, mastery, CEFR | ❌ | ❌ | ❌ | ❌ |
| DOI-referenced benchmark | ✅ | ❌ | ❌ | ❌ | ❌ |
| GDPR / Luxembourg jurisdiction | ✅ | ❌ | ❌ | ❌ | ❌ |

---

## The numbers

Benchmarked across 23 subjects, 115 profiles. Scorer: `qwen/qwen3-32b` via Groq.  
Full methodology (v3.5.1 deposit, still applicable to v4.0.0 payload semantics): [DOI 10.5281/zenodo.20320480](https://doi.org/10.5281/zenodo.20320480)

| Sequence | What was tested | Δ WITH vs WITHOUT |
|---|---|---|
| Seq 1 — 115 profiles | Core pedagogy | **+13.9 pts avg** (min +12.8, max +19.2) |
| Seq 2 — §31 recovery | Migration continuity | +9.5 pts (with recovery phrase) |
| Seq 3 — Soul Handoff | Cross-model identity | **+14.0 pts** (IC ±7.2) |

---

## Try it now

- [**Playground**](https://klickd.app/klickdskill/playground) — load a `.klickd` file live, see what the AI receives
- [**klickdskill docs**](https://klickd.app/klickdskill) — full specification and integration guides

---

## Install

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

| File | Who it's for |
|---|---|
| [`examples/student_fr.klickd`](examples/student_fr.klickd) | French high-school student, maths, Socratic mode |
| [`examples/professional_en.klickd`](examples/professional_en.klickd) | Mid-level developer upskilling into ML |
| [`examples/family_plan.klickd`](examples/family_plan.klickd) | Child profile with ADHD support and shared family context |
| [`examples/minimal.klickd`](examples/minimal.klickd) | Cold start — minimal valid v3.x payload (forward-compatible with v4.0.0) |
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

> **Experimental POC:** [`integrations/hermes/`](integrations/hermes/README.md) — Hermes Agent as workflow runner, `.klickd` as portable state layer. Local dry-run only; not a production integration.

---

## Schema validation

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

Schemas:
- v4.0.0 GA (strict): [`schema/klickd-v4.schema.json`](schema/klickd-v4.schema.json), [`schemas/klickd-payload-v4.schema.json`](schemas/klickd-payload-v4.schema.json)
- v3.x (legacy, still valid): [`schema/klickd-v3.4.schema.json`](schema/klickd-v3.4.schema.json)

---

## Prior art

To our knowledge, no existing format combines zero-process portability, client-side AES-256-GCM + Argon2id encryption, a structured pedagogical schema, and a DOI-referenced reproducible benchmark.

Evaluated against: Mem0, PAM (arXiv:2605.11032), Letta/MemGPT, Cortex, Opal (arXiv:2604.02522), MeMo (arXiv:2605.15156), agentmemory (~15K stars).  
Full analysis: [Zenodo preprint](https://doi.org/10.5281/zenodo.20320480)

---

## Long context vs portable state

`.klickd` is **not** a replacement for long-context models or context-window extension — and it is not in competition with the GPU / runtime infrastructure that makes those windows possible. The two address different layers of the same problem:

- **Longer context helps the model fit more.** GPU and runtime infrastructure (extended windows, KV-cache offload, streaming attention) expand what a single inference call can process.
- **Portable state helps the system repeat less.** `.klickd` reduces what the model has to repeatedly process across sessions, vendors, and models, by carrying user-level state as a portable file.

They are complementary. A larger window does not, on its own, retain who the user is between yesterday's GPT-4o session and tomorrow's Claude session — that is a state-persistence concern, not a capacity concern. Equally, a `.klickd` payload does not stretch a single call's working memory.

For most real workloads the useful question is not "long context **or** portable state" but "long context **and** portable state": expand capacity at the runtime layer, and trim repetition at the state layer. RFC-003 (Context Cost Benchmark) is being designed to measure exactly this — see [§9.1 of the RFC](benchmarks/context_cost/RFC.md#91-relation-to-long-context-models-and-context-window-extension) for the non-normative framing.

*Insight prompted by a [DEV.to discussion](https://dev.to/davincc77/ai-agents-dont-have-a-memory-problem-they-have-an-architecture-problem-3pl6) with VoltageGPU — see [`ACKNOWLEDGEMENTS.md`](ACKNOWLEDGEMENTS.md).*

---

## Cite

```bibtex
@misc{klickd2026,
  title   = {.klickd — Open Encrypted Format for Portable AI User Context, v4.0.0},
  author  = {Cirilli, Vincenzo},
  year    = {2026},
  version = {4.0.0},
  doi     = {10.5281/zenodo.20383133},
  url     = {https://doi.org/10.5281/zenodo.20383133},
  note    = {Concept DOI (all versions): 10.5281/zenodo.20262530}
}
```

---

## Badge

```markdown
[![.klickd compatible](https://img.shields.io/badge/.klickd-v4.0.0%20compatible-0066CC?style=flat-square&logo=json)](https://github.com/Davincc77/klickdskill)
```

---

## Full Specification

[`SPEC.md`](SPEC.md) — encryption (AES-256-GCM), all field references, teaching modes, Soul Handoff, JSON Injection Guard, benchmark namespace, memory decay, shared context, versioning policy.

### Current GA — `.klickd v4.0.0`

The current and recommended production format is **v4.0.0**. The wire envelope stays at `klickd_version: "3.0"` (unchanged crypto and AAD); v4 is signalled inside the payload via `payload_schema_version: "4.0"` (the canonical v4 GA value; the release label is `v4.0.0`). v3.x readers MUST ignore unknown fields; v4 readers MUST preserve them verbatim.

- Spec: [`SPEC.md`](SPEC.md) — normative v4 surface (additive over v3.5.1).
- Strict JSON Schemas (Draft 2020-12): [`schemas/klickd-payload-v4.schema.json`](schemas/klickd-payload-v4.schema.json), [`schema/klickd-v4.schema.json`](schema/klickd-v4.schema.json)
- Reference SDKs (4.0.0): [`packages/pypi/klickd/`](packages/pypi/klickd/) (Python), [`packages/@klickd/core/`](packages/@klickd/core/) (TypeScript / JavaScript)
- Migrator (v3.x → v4, non-destructive): see `migrate` API in both SDKs.
- Migration guide: [`docs/spec/MIGRATION_V3_TO_V4.md`](docs/spec/MIGRATION_V3_TO_V4.md)
- Cross-implementation strict vectors: [`tests/`](tests/) and the two `verify_vectors.*` runners.
- Final release notes: [`docs/releases/v4.0.0.md`](docs/releases/v4.0.0.md)

The previous v3.5.1 release remains valid and interoperable; v4.0.0 readers accept v3.x payloads via the migrator.

---

## License

[CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/) — Public Domain. No permission required. No vendor lock-in.

---

*Made in Luxembourg · GDPR-native · [klickd.app/klickdskill](https://klickd.app/klickdskill)*
