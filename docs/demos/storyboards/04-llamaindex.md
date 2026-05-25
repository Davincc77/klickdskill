# Storyboard 04 — LlamaIndex (~55 s)

**Goal:** show the two `.klickd` × LlamaIndex shapes — system-prompt
injection and document ingestion into a vector index.

**Surfaces shown:** IDE + terminal.

| t (s) | Scene | On-screen text | Voice-over (≤ 12 words) | What the viewer learns |
|-------|-------|----------------|--------------------------|-------------------------|
| 0–4 | Title card | `.klickd × LlamaIndex — two integrations` | "Two ways to use .klickd with LlamaIndex." | Framing |
| 4–14 | IDE: `klickd_llamaindex.py`, scroll past `klickd_to_system_prompt` and `klickd_to_documents` | callouts on both function names | "System prompt — or vector index." | Two shapes |
| 14–28 | Terminal: `python` REPL — load payload, build system prompt, send chat message via `llama_index.llms.openai` | REPL output | "Direct injection: profile becomes the system message." | Shape 1 demoed |
| 28–48 | REPL: call `klickd_to_documents(payload)`, build `VectorStoreIndex`, run `query_engine.query("What is the user blocked on?")` | answer cites `knowledge.struggles[0]` | "Or index the structured fields. Retrieval picks the right chunk." | Shape 2 demoed |
| 48–53 | Code overlay: highlight `metadata={"section":"knowledge"}` | yellow box on metadata | "Each section keeps its label." | Metadata filtering possible |
| 53–55 | End card | `docs/integrations/llamaindex.md` | "Doc + code linked." | CTA |

## Recording notes

- Use any persona, e.g.
  [`02-chef-projet-pme-fr.klickd`](../../../examples/v4/personas/02-chef-projet-pme-fr.klickd)
  for the document-ingestion shape (richer `context` + `knowledge`).
- The vector index build uses a real embedding model — pick the smallest
  available to keep the clip short. State the model name on screen.
- Do not claim retrieval accuracy numbers in voice-over.
