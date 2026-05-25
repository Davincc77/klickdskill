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

## Notes

- Strip `_`-prefixed debug / benchmark fields before ingest — the helper
  does this for you.
- Encrypted envelopes: pass `passphrase=...` to `load_klickd_path()`.
- Treat the index as user-scoped: never co-mingle multiple users' `.klickd`
  payloads in the same vector store without a tenant filter.
