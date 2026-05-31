# .klickd — One file. Any model. No server.

> *When it all .klickd*

[![.klickd format](https://img.shields.io/badge/.klickd%20format-v4.0.0%20GA-0066CC?style=flat-square&logo=json)](https://github.com/Davincc77/klickdskill)
[![SDKs](https://img.shields.io/badge/SDKs-v4.1.0%20stable-0066CC?style=flat-square&logo=json)](https://github.com/Davincc77/klickdskill)
[![License: CC0](https://img.shields.io/badge/License-CC0%201.0-lightgrey?style=flat-square)](https://creativecommons.org/publicdomain/zero/1.0/)
[![DOI (v4.0.0)](https://zenodo.org/badge/DOI/10.5281/zenodo.20383133.svg)](https://doi.org/10.5281/zenodo.20383133)
[![Concept DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20262530.svg)](https://doi.org/10.5281/zenodo.20262530)
[![DOI (x.klickd v4.1 evidence pack)](https://zenodo.org/badge/DOI/10.5281/zenodo.20459934.svg)](https://doi.org/10.5281/zenodo.20459934)
[![npm @klickd/core](https://img.shields.io/npm/v/@klickd/core?style=flat-square&logo=npm&label=%40klickd%2Fcore)](https://www.npmjs.com/package/@klickd/core)
[![PyPI klickd](https://img.shields.io/pypi/v/klickd?style=flat-square&logo=pypi&label=klickd)](https://pypi.org/project/klickd/)

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

> `.klickd` does not remove integration work — it makes it reusable. One integration. Infinite reuse. Across games, engines, platforms, apps, agents, robots, devices, and models.
>
> Reuse requires that the client, agent, or tool on the other side actually supports `.klickd` (or follows the [generic integration pattern](docs/integrations/generic.md)). The format is portable; compatibility still depends on the reader.

`.klickd` does not replace provider security, model alignment, or application-level access control; it complements them by giving the user-state layer a portable, verifiable shape.

> **Claim boundary.** `.klickd` gives you portable, client-side-encrypted user state and the technical primitives that *help* a privacy and safety program. It does **not** provide universal native support across AI clients — compatibility depends on the reader. It does **not** confer automatic GDPR or EU AI Act compliance — compliance is the operator's responsibility. It makes **no claim of superiority over external benchmarks or competing systems**. The v4.1 candidate / benchmark track (e.g. the `x.klickd` candidate skills) is **not GA** and carries no stability or compatibility guarantees. See the [DOI deposit](https://doi.org/10.5281/zenodo.20383133) for the full disclaimer. The v4.1 benchmark evidence pack is archived as a separate Zenodo record — [DOI 10.5281/zenodo.20459934](https://doi.org/10.5281/zenodo.20459934) — and documents the candidate-track benchmark evidence only; it asserts no universal native support, no automatic GDPR / EU AI Act compliance, and no superiority over external benchmarks.

---

## x.klickd v4.1 evidence pack

The current published benchmark evidence is the **x.klickd v4.1 evidence pack**, archived on Zenodo at **[DOI 10.5281/zenodo.20459934](https://doi.org/10.5281/zenodo.20459934)**. Reference SDKs are published as [`@klickd/core@4.1.0`](https://www.npmjs.com/package/@klickd/core) (npm) and [`klickd==4.1.0`](https://pypi.org/project/klickd/) (PyPI).

Headline figures from the evidence pack:

| Metric | Result |
|---|---|
| Valid outputs collected | **7,189** valid / 7,200 expected |
| Completion across four completed bundles | **99.85%** |
| Lower repeated input-token overhead (static `x.klickd`) | **76.49%** |
| Lower repeated input-token overhead (with optional `compressed_memory`) | **93.34%** |
| Automatic quality score — `x.klickd` conditions | **86.24 / 100** |
| Automatic quality score — standard AI usage without `x.klickd` | **58.51 / 100** |

> **Scope of these figures.** These are the candidate-track benchmark results documented in the [v4.1 evidence pack DOI](https://doi.org/10.5281/zenodo.20459934). They describe this benchmark only. They do **not** establish universal native support across AI clients, automatic GDPR / EU AI Act compliance, or superiority over external benchmarks or competing systems, and they are not an industry-standard or adoption claim. The v4.1 candidate track carries no stability or compatibility guarantees; the current production format remains v4.0.0 GA.

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

## The numbers (historical v3.5 / v4.0 benchmark)

> **Historical, not the current v4.1 evidence pack.** This section reports the earlier **v3.5 / v4.0** pedagogy benchmark. For the current published figures, see the [x.klickd v4.1 evidence pack](#xklickd-v41-evidence-pack) above ([DOI 10.5281/zenodo.20459934](https://doi.org/10.5281/zenodo.20459934)). The two benchmarks use different methodologies and are not directly comparable.

Benchmarked across 23 subjects, 115 profiles. Scorer: `qwen/qwen3-32b` via Groq.  
Full methodology (v3.5.1 deposit, still applicable to v4.0.0 payload semantics): [DOI 10.5281/zenodo.20320480](https://doi.org/10.5281/zenodo.20320480)

| Sequence | What was tested | Δ WITH vs WITHOUT |
|---|---|---|
| Seq 1 — 115 profiles | Core pedagogy | **+13.9 pts avg** (min +12.8, max +19.2) |
| Seq 2 — §31 recovery | Migration continuity | +9.5 pts (with recovery phrase) |
| Seq 3 — Soul Handoff | Cross-model identity | **+14.0 pts** (IC ±7.2) |

---

## Try it now

- [**5-minute developer path**](docs/community/TRY_IT.md) — install the SDK, load a starter `.klickd`, verify hashes, then plug into your provider of choice.
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
| xAI Grok (OpenAI-compatible) | [`docs/integrations/xai_grok.md`](docs/integrations/xai_grok.md) |
| LangChain (provider-agnostic chains) | [`docs/integrations/langchain.md`](docs/integrations/langchain.md) |
| LlamaIndex (system prompt + vector index) | [`docs/integrations/llamaindex.md`](docs/integrations/llamaindex.md) |
| GitHub Copilot / M365 Copilot (hybrid pattern) | [`docs/integrations/copilot.md`](docs/integrations/copilot.md) |
| Any provider (generic pattern) | [`docs/integrations/generic.md`](docs/integrations/generic.md) |

> **Experimental POC:** [`integrations/hermes/`](integrations/hermes/README.md) — Hermes Agent as workflow runner, `.klickd` as portable state layer. Local dry-run only; not a production integration.

---

## Demos (v4)

| Demo | What it shows |
|---|---|
| [`examples/v4/cli/`](examples/v4/cli/) | Python CLI: `pip install klickd==4.0.0` + a path-based `load_klickd` walkthrough |
| [`examples/v4/web-dropzone/`](examples/v4/web-dropzone/) | Browser drag-and-drop, zero install, local-only parse |
| [`examples/v4/student-walkthrough/`](examples/v4/student-walkthrough/) | One student profile, four providers (OpenAI · Anthropic · Groq · xAI Grok) |
| [`examples/v4/starter-skills/`](examples/v4/starter-skills/) | Four downloadable starter `.klickd` skills on the v4.0 envelope ([`user.klickd`](https://github.com/Davincc77/klickdskill/blob/main/examples/v4/starter-skills/user.klickd), [`student.klickd`](https://github.com/Davincc77/klickdskill/blob/main/examples/v4/starter-skills/student.klickd), [`research.klickd`](https://github.com/Davincc77/klickdskill/blob/main/examples/v4/starter-skills/research.klickd), [`coding.klickd`](https://github.com/Davincc77/klickdskill/blob/main/examples/v4/starter-skills/coding.klickd)) — non-normative, not v4.1 GA, with sha256 manifest and offline verifier (`scripts/verify_starter_skills.py`, `tests/test_starter_skills.py`). |
| [`docs/demos/storyboards/`](docs/demos/storyboards/) | 30–60s recording scripts for each integration (text only, no video) |

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

### Why there are two schema directories

The repo ships **two** schema directories on purpose — they are not duplicates and are not merged:

| Directory | Model | Use when |
|---|---|---|
| [`schema/`](schema/) | **Unified** — one file validates a complete document (envelope + inline-or-encrypted payload) per version. | Single-pass validation is enough: CI tooling, third-party integrations, registries. |
| [`schemas/`](schemas/) | **Split** — envelope and payload validated as two independent steps. | Secure decoders that validate the envelope *before* decryption and the payload *after*. |

Both carry a `README.md` that cross-references the other. The full mapping of every schema to the validator that consumes it is in [`SCHEMA_INDEX.md`](SCHEMA_INDEX.md); the load-bearing rationale (test vectors, release tooling, and schema `$id` URLs resolve against these exact paths) is in [`docs/STRUCTURE.md`](docs/STRUCTURE.md#the-two-schema-directories-are-deliberately-distinct).

---

## Repository structure

A compact map of the canonical layout. The authoritative, load-bearing version — including which paths are referenced by CI, test vectors, release tooling, and schema `$id` URLs — is in **[`docs/STRUCTURE.md`](docs/STRUCTURE.md)**.

```
.
├── SPEC.md                     # Normative specification (v4.0.0 GA surface)
├── SKILL.md                    # Current skill document
├── SCHEMA_INDEX.md             # Index: every schema → its validator (start here)
├── schema/                     # Unified single-file JSON Schemas (v1, v2, v3.4, v4)
├── schemas/                    # Split envelope + payload JSON Schemas (v3, v4)
├── verify_vectors.py           # Root wrapper → scripts/verify_vectors.py (CI entry point)
├── verify_vectors.mjs          # Root wrapper → scripts/verify_vectors.mjs (CI entry point)
├── load_klickd.py              # Root shim → scripts/load_klickd.py (import compatibility)
├── save_klickd.py              # Root shim → scripts/save_klickd.py (import compatibility)
├── scripts/                    # Reference encoder/decoder, verifiers, generators, release tooling
│   ├── load_klickd.py          #   Reference decoder (canonical)
│   ├── save_klickd.py          #   Reference encoder (canonical)
│   ├── verify_vectors.py       #   Python cross-impl vector verifier (canonical)
│   └── verify_vectors.mjs      #   Node cross-impl vector verifier (canonical)
├── tests/                      # Cross-implementation test vectors + pytest suites
├── packages/                   # Reference SDKs — @klickd/core (npm), klickd (PyPI)
├── examples/                   # Sample .klickd files and integration snippets
├── registry/                   # Competency / domain / personality registries
├── benchmarks/                 # Benchmark inputs, raw runs, reports
├── curriculum/                 # Per-jurisdiction curriculum material
├── integrations/               # Third-party integration adapters
├── tools/                      # Reserved for developer tooling (see tools/README.md)
└── docs/                       # Long-form docs, RFCs, release notes, audits, specs
    ├── paper/                  #   JOSS paper sources (paper.md, paper.bib)
    └── specs/                  #   Historical spec PDF snapshot
```

**Canonical scripts live under `scripts/`.** The reference encoder/decoder (`scripts/load_klickd.py`, `scripts/save_klickd.py`) and the cross-implementation verifiers (`scripts/verify_vectors.py`, `scripts/verify_vectors.mjs`) are the canonical implementations. Thin **root compatibility wrappers** of the same name are kept so the documented public entry points keep working unchanged — `python verify_vectors.py` / `node verify_vectors.mjs` (invoked by [`.github/workflows/test-vectors.yml`](.github/workflows/test-vectors.yml), [`package.json`](package.json), and the v4.1 evidence-pack bundle tooling) and `import load_klickd` / `import save_klickd` from the repo root. This preserves published v4.1 reproducibility while cleaning the root. The JOSS paper sources moved to [`docs/paper/`](docs/paper/) and the historical PDF to [`docs/specs/`](docs/specs/). Historical Markdown snapshots ([`SPEC_v30.md`](SPEC_v30.md), [`SKILL_v25.md`](SKILL_v25.md), [`SKILL_v30.md`](SKILL_v30.md)) remain at root to preserve existing links. See [`docs/STRUCTURE.md`](docs/STRUCTURE.md) for the full rationale.

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

To cite the **x.klickd v4.1 benchmark evidence pack** specifically (the candidate-track benchmark evidence, not the v4.0.0 GA release):

```bibtex
@misc{xklickd_v41_evidence_pack_2026,
  title   = {x.klickd v4.1.0: Portable, Encrypted and Governed Memory for Long-Running AI Workflows},
  author  = {Cirilli, Vincenzo},
  year    = {2026},
  version = {4.1.0},
  doi     = {10.5281/zenodo.20459934},
  url     = {https://doi.org/10.5281/zenodo.20459934},
  note    = {Benchmark evidence pack for the v4.1 candidate track; concept DOI (all versions): 10.5281/zenodo.20262530}
}
```

---

## Badge

```markdown
[![.klickd compatible](https://img.shields.io/badge/.klickd-v4.0.0%20compatible-0066CC?style=flat-square&logo=json)](https://github.com/Davincc77/klickdskill)
```

---

## Feedback & discussion

If you tried `.klickd` and something worked — or did not work — I'd like to hear about it. The repo is early, the format is small, and direct developer feedback is the most useful signal at this stage.

- [**5-minute path**](docs/community/TRY_IT.md) — the shortest honest route from clone to "I loaded a `.klickd` file in code".
- [**Feedback questions**](docs/community/FEEDBACK.md) — five short questions: what model, what integration, what broke, what would make adoption easier.
- [**GitHub Discussions**](https://github.com/Davincc77/klickdskill/discussions) — open-ended threads (seed prompts are being prepared in [`docs/community/DISCUSSION_PROMPTS.md`](docs/community/DISCUSSION_PROMPTS.md); not all categories are live yet).
- **Security findings** — please use the private disclosure process in [`SECURITY.md`](SECURITY.md), not Discussions.

No newsletter, no signup, no community claims we cannot back up — just a place to leave a short reply.

---

## Full Specification

[`SPEC.md`](SPEC.md) — encryption (AES-256-GCM), all field references, teaching modes, Soul Handoff, JSON Injection Guard, benchmark namespace, memory decay, shared context, versioning policy.

### Current GA format — `.klickd v4.0.0` · current stable SDKs — `v4.1.0`

The current and recommended production **format** is **v4.0.0 GA**. The wire envelope stays at `klickd_version: "3.0"` (unchanged crypto and AAD); v4 is signalled inside the payload via `payload_schema_version: "4.0"` (the canonical v4 GA value; the release label is `v4.0.0`). v3.x readers MUST ignore unknown fields; v4 readers MUST preserve them verbatim.

The current stable **reference SDKs** are **v4.1.0** ([`@klickd/core@4.1.0`](https://www.npmjs.com/package/@klickd/core) on npm and [`klickd==4.1.0`](https://pypi.org/project/klickd/) on PyPI); **v4.0.0** was the prior stable SDK release. The 4.1.0 SDKs read and write the same v4.0.0 GA wire envelope — the bump is a packaging/SDK minor release and changes no payload semantics, schema, or crypto. The separately archived [x.klickd v4.1 evidence pack](#xklickd-v41-evidence-pack) ([DOI 10.5281/zenodo.20459934](https://doi.org/10.5281/zenodo.20459934)) documents candidate-track benchmark evidence only and carries no stability or compatibility guarantees.

- Spec: [`SPEC.md`](SPEC.md) — normative v4 surface (additive over v3.5.1).
- Strict JSON Schemas (Draft 2020-12): [`schemas/klickd-payload-v4.schema.json`](schemas/klickd-payload-v4.schema.json), [`schema/klickd-v4.schema.json`](schema/klickd-v4.schema.json)
- Reference SDKs (v4.1.0 stable; wire envelope remains v4.0.0 GA): [`packages/pypi/klickd/`](packages/pypi/klickd/) (Python), [`packages/@klickd/core/`](packages/@klickd/core/) (TypeScript / JavaScript)
- Migrator (v3.x → v4, non-destructive): see `migrate` API in both SDKs.
- Migration guide: [`docs/spec/MIGRATION_V3_TO_V4.md`](docs/spec/MIGRATION_V3_TO_V4.md)
- Cross-implementation strict vectors: [`tests/`](tests/) and the two `verify_vectors.*` runners.
- Final release notes: [`docs/releases/v4.0.0.md`](docs/releases/v4.0.0.md)

The previous v3.5.1 release remains valid and interoperable; v4.0.0 readers accept v3.x payloads via the migrator.

---

## Historical files

A few root-level files are retained for provenance and are **not** the current specification. They are kept in place (not moved) because CI and historical audit notes still reference them:

| File | Status |
|---|---|
| [`SKILL_v25.md`](SKILL_v25.md), [`SKILL_v30.md`](SKILL_v30.md) | Historical skill revisions — superseded by [`SKILL.md`](SKILL.md). |
| [`SPEC_v30.md`](SPEC_v30.md) | Historical specification snapshot — superseded by [`SPEC.md`](SPEC.md) (v4.0.0 GA). |
| [`docs/specs/klickd_v330_spec.pdf`](docs/specs/klickd_v330_spec.pdf) | Historical PDF snapshot of an earlier spec revision. |

For the current normative surface, use [`SPEC.md`](SPEC.md) and [`SKILL.md`](SKILL.md).

---

## License

[CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/) — Public Domain. No permission required. No vendor lock-in.

---

*Made in Luxembourg · GDPR-native · [klickd.app/klickdskill](https://klickd.app/klickdskill)*
