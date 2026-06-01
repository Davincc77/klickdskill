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

## Memory bridge & cross-session resume

For agent / chat workflows that **resume context across sessions**, use the
`KlickdMemory` bridge at
[`examples/v4/integrations/langchain/klickd_memory.py`](../../examples/v4/integrations/langchain/klickd_memory.py).
It loads a profile or starter skill **through the `klickd` SDK only**
(`load_klickd`, `get_starter_skill_bytes`, `validate_iter_errors`) and
converts the validated context into LangChain messages and LangGraph state.
This is *bridge-mediated compatibility, not native framework support*.

```python
from klickd_memory import KlickdMemory

mem = KlickdMemory.from_starter_skill("coding.klickd")   # SDK-loaded, plain
# or: KlickdMemory.from_path("profile.klickd", passphrase="…")  # encrypted

messages = mem.to_messages()              # [(role, content), ...] system + prior turns
state    = mem.to_langgraph_state()       # {"messages": [...], "klickd": {...}}
# lc_msgs = mem.to_lc_messages()          # langchain-core message objects (optional)
```

A runnable cross-session example (save in session 1, resume in session 2) lives
at
[`example_resume_session.py`](../../examples/v4/integrations/langchain/example_resume_session.py).
It runs from a clean checkout with no network and no LangChain install; if
`langchain-core` / `langgraph` are present it additionally builds real message
objects and a tiny graph.

### Boundaries (read these)

- **Compressed memory is opt-in.** `to_messages(compressed=True)` collapses
  prior turns into a single system summary line; the default replays them.
- **System vs. user injection.** Content is injected in the *system* role. If a
  payload sets `injection_target` to `user_message` / `both`, the system prompt
  prepends a JSON Injection Guard (SPEC §25.3).
- **Trust boundary.** The AI model does not decrypt the `.klickd` file — the
  trusted local runtime does. Encrypted profiles decrypt in-process via
  `load_klickd` with a passphrase you supply.
- **Gates are advisory in the prompt; enforce them in the host.**
  `verification_gates` are surfaced as text and preserved in
  `state["klickd"]`; `human_authority` / `human_veto_policy` pass through
  unchanged, keeping the human carrier as final decision owner.
- **No compliance claims.** This bridge makes no GDPR, EU AI Act, or
  universal-standard claim — it is a format converter. See the
  [adapter README](../../examples/v4/integrations/langchain/README.md), the
  evidence pack at <https://doi.org/10.5281/zenodo.20262530>, and
  [`SPEC.md`](../../SPEC.md) (§25.3, §29) for boundaries.
