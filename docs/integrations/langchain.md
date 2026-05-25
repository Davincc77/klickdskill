# LangChain — .klickd v4.0.0 Integration

**Framework:** [LangChain](https://python.langchain.com) · `pip install langchain langchain-openai`
**SDK:** `pip install klickd==4.0.0`

LangChain's prompt + chain primitives map cleanly to `.klickd`: the
payload becomes the system message, the chain stays provider-agnostic.

## Reference adapter

The reusable helpers live at
[`examples/v4/integrations/langchain/klickd_langchain.py`](../../examples/v4/integrations/langchain/klickd_langchain.py).
They have **no LangChain dependency at import time** — `langchain_*`
imports are deferred to `build_chain()`, so the prompt builder is safe to
use in any environment.

## Minimal example

```python
from klickd import load_klickd
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

# 1. Decode the .klickd file
with open("examples/v4/personas/03-fullstack-developer-en.klickd", "rb") as f:
    payload = load_klickd(f.read())

# 2. Build the system prompt (use the helper for full SPEC §29 compliance)
from examples.v4.integrations.langchain.klickd_langchain import klickd_to_system_prompt
system_prompt = klickd_to_system_prompt(payload)

# 3. Standard LangChain chain
prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{input}"),
])
chain = prompt | ChatOpenAI(model="gpt-4o")

print(chain.invoke({"input": "Let's pick up where we left off."}).content)
```

## Notes

- Always inject `.klickd` content in the `system` role unless the payload
  explicitly sets `injection_target` to `user_message` / `both` — in
  which case `klickd_to_system_prompt()` prepends the JSON Injection
  Guard automatically (SPEC §25.3).
- Strip `_`-prefixed debug / benchmark keys before injection
  (SPEC §29) — the helper does this for you.
- `verification_gates` are surfaced to the model as a single short
  instruction. Enforce the actual gate semantics in the host application,
  not in the LLM — the LLM is the *agent*, not the *referee*.
- The helper supports both plain (`encrypted: false`) and encrypted
  envelopes: pass `passphrase=...` to `load_klickd_path()`.

## Provider-agnostic by design

Swap `ChatOpenAI` for `ChatAnthropic`, `ChatGroq`, or any
LangChain-supported chat model. The `.klickd` payload is the portable
state layer; the chain stays untouched.
