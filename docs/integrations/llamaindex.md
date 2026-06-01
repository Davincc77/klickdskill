# LlamaIndex — .klickd v4.0.0 Integration

**Framework:** [LlamaIndex](https://docs.llamaindex.ai) · `pip install llama-index`
**SDK:** `pip install klickd==4.0.0`

LlamaIndex offers two natural integration points for `.klickd`:

1. **System-prompt injection** — same pattern as LangChain / OpenAI; the
   payload becomes the system message of a chat engine or agent.
2. **Document ingestion** — the structured fields of a `.klickd` payload
   are turned into `Document` objects and embedded into a vector index
   alongside the rest of the user's corpus.

The reusable helpers live at
[`examples/v4/integrations/llamaindex/klickd_llamaindex.py`](../../examples/v4/integrations/llamaindex/klickd_llamaindex.py).

## 1. System-prompt injection

```python
from klickd import load_klickd
from llama_index.llms.openai import OpenAI
from llama_index.core.llms import ChatMessage

from examples.v4.integrations.llamaindex.klickd_llamaindex import klickd_to_system_prompt

with open("examples/v4/personas/01-eleve-terminale-fr.klickd", "rb") as f:
    payload = load_klickd(f.read())

system_prompt = klickd_to_system_prompt(payload)

llm = OpenAI(model="gpt-4o")
response = llm.chat([
    ChatMessage(role="system", content=system_prompt),
    ChatMessage(role="user", content="Let's continue."),
])
print(response.message.content)
```

## 2. Document ingestion (vector index)

```python
from klickd import load_klickd
from llama_index.core import VectorStoreIndex

from examples.v4.integrations.llamaindex.klickd_llamaindex import klickd_to_documents

with open("examples/v4/personas/03-fullstack-developer-en.klickd", "rb") as f:
    payload = load_klickd(f.read())

docs = klickd_to_documents(payload)
index = VectorStoreIndex.from_documents(docs)

query_engine = index.as_query_engine()
print(query_engine.query("What is the user currently blocked on?"))
```

`klickd_to_documents()` emits one `Document` per structurally distinct
section (`user_preferences`, `context`, `knowledge`, plus one per
`memory[]` entry), with metadata carrying the section name, version, and
the original `domain` / `profile_kind` so you can filter on retrieval.

## 3. Resume a session (chat workflow)

The portable file is what lets a LlamaIndex chat engine pick up *exactly
where the last session left off*, across models and machines. The system
prompt built from `context` (`current_project` / `current_state` /
`resume_trigger`) seeds the chat memory; the engine then continues the
conversation.

```python
from klickd_llamaindex import klickd_to_chat_messages, load_klickd_path
from llama_index.core.chat_engine import SimpleChatEngine
from llama_index.llms.openai import OpenAI

payload = load_klickd_path("examples/v4/personas/03-fullstack-developer-en.klickd")
seed = klickd_to_chat_messages(payload)          # [system] resume message

engine = SimpleChatEngine.from_defaults(llm=OpenAI(model="gpt-4o"), prefix_messages=seed)
print(engine.chat("Let's pick up where we left off — what's the next step?").response)
```

A self-contained, runnable version lives at
[`examples/v4/integrations/llamaindex/resume_chat_example.py`](../../examples/v4/integrations/llamaindex/resume_chat_example.py).
It has a hermetic `--check` dry-run (no LlamaIndex install, no network)
that the test suite exercises, and a `--live` mode for a real turn:

```bash
python examples/v4/integrations/llamaindex/resume_chat_example.py --check
python examples/v4/integrations/llamaindex/resume_chat_example.py --check --starter coding.klickd
```

## Loading bundled starter skill packs

You don't need a file on disk to try the bridge. The SDK ships four plain
starter packs; load one with the public accessor and the helper surfaces
its declared gates, human-authority owner, and memory scope:

```python
from klickd_llamaindex import klickd_to_system_prompt, load_starter_skill

payload = load_starter_skill("coding.klickd")   # uses klickd.get_starter_skill_bytes
print(klickd_to_system_prompt(payload))
```

Starter packs are capability *packs* — they carry `verification_gates`
and a `memory_scope`, not a persona `context`. Use a persona profile (or
the user's own `.klickd` file) when you want cross-session *resume*.

## Limitations & guardrails

- **No compliance claim.** This adapter does **not** confer automatic
  GDPR or EU AI Act compliance — compliance is the operator's
  responsibility. It is **not** a universal standard and implies no
  native `.klickd` support inside LlamaIndex; it is a reference adapter
  you run. See the [claim boundary](../../README.md) in the main README.
- **Compressed memory is optional.** The compressed-memory track
  (RFC-010) is a non-GA preview; nothing here depends on it. Plain
  `memory[]` entries are sufficient.
- **Trust boundary / prompt injection.** A decoded `.klickd` payload is
  **untrusted user content**, not privileged instructions. If a payload
  sets `injection_target` to `user_message` / `both`, the prompt builder
  applies the JSON Injection Guard (SPEC §25.3); still treat any text that
  reaches an index or chat turn as data, never as a command.
- **Encrypted files.** Pass `passphrase=...` to `load_klickd_path()` for
  encrypted envelopes; the bundled starter packs are plain.
- **Field stripping.** `_`-prefixed debug / benchmark fields are stripped
  before injection and ingest (SPEC §29) — the helpers do this for you.
- **Gate enforcement.** `verification_gates` are surfaced to the model as
  instructions only. Enforce the real gate semantics in your host
  application — the LLM is the *agent*, not the *referee* (SPEC §29).
- **Tenant isolation.** Treat each index as user-scoped; never co-mingle
  multiple users' `.klickd` payloads in one vector store without a tenant
  filter.

## References

- Concept DOI: [10.5281/zenodo.20262530](https://doi.org/10.5281/zenodo.20262530) ·
  v4.0.0: [10.5281/zenodo.20383133](https://doi.org/10.5281/zenodo.20383133)
- x.klickd v4.1 evidence pack: [10.5281/zenodo.20459934](https://doi.org/10.5281/zenodo.20459934)
  (candidate track; not GA — no universal-support / compliance / superiority claim)
- SPEC boundaries: [`SPEC.md`](../../SPEC.md) §25.3 (injection guard), §29 (field stripping & gate semantics)
