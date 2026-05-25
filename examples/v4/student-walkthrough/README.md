# Student profile — works out-of-the-box across 4 providers

A ready-to-run `.klickd` v4.0.0 profile plus copy-pasteable snippets for
OpenAI, Anthropic, Groq, and xAI Grok. The same file drives all four —
that is the whole point.

> **Status:** non-normative, docs-only.
> **Profile:** [`student-multi-provider.klickd`](./student-multi-provider.klickd) — fictional persona, no real PII.

---

## The profile

A Socratic-tutoring profile for a calculus student stuck mid-session on
the chain rule. The interesting bits:

- `user_preferences` → tutor stays in Socratic mode, no direct answers.
- `context.resume_trigger` → the model picks up mid-worked-example.
- `verification_gates` → exam-related factual claims must be confirmed;
  nothing public.
- `agent_instructions` → load-time onboarding question.

## Install once

```bash
pip install klickd==4.0.0 openai anthropic groq
```

xAI uses the OpenAI client (`pip install openai>=1.0`).

## 4 providers, same `.klickd`

```python
from klickd import load_klickd

with open("examples/v4/student-walkthrough/student-multi-provider.klickd", "rb") as f:
    payload = load_klickd(f.read())

# Re-use the shared helper from the LangChain integration (no LangChain dep):
from examples.v4.integrations.langchain.klickd_langchain import klickd_to_system_prompt
system_prompt = klickd_to_system_prompt(payload)

user_msg = "I'm stuck — sin(x²). What do I do with the inside?"
```

### 1. OpenAI

```python
from openai import OpenAI
client = OpenAI()  # uses OPENAI_API_KEY
print(client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role":"system","content":system_prompt},
              {"role":"user","content":user_msg}],
).choices[0].message.content)
```

### 2. Anthropic Claude

```python
import anthropic
client = anthropic.Anthropic()  # uses ANTHROPIC_API_KEY
print(client.messages.create(
    model="claude-opus-4-5",
    max_tokens=1024,
    system=system_prompt,
    messages=[{"role":"user","content":user_msg}],
).content[0].text)
```

### 3. Groq

```python
from groq import Groq
client = Groq()  # uses GROQ_API_KEY
print(client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[{"role":"system","content":system_prompt},
              {"role":"user","content":user_msg}],
).choices[0].message.content)
```

### 4. xAI Grok

```python
import os
from openai import OpenAI
client = OpenAI(api_key=os.environ["XAI_API_KEY"],
                base_url="https://api.x.ai/v1")
print(client.chat.completions.create(
    model="grok-2-latest",
    messages=[{"role":"system","content":system_prompt},
              {"role":"user","content":user_msg}],
).choices[0].message.content)
```

## What this demonstrates

- **One soul, any model:** four providers, four model families, one file.
- **No vendor lock-in:** the profile sits on the user's disk; the system
  prompt is built deterministically from it.
- **No secrets in the profile:** API keys stay in the environment, never
  in `.klickd`. Do not "helpfully" embed them — `.klickd` is portable
  state, not a credential store.

## Honest non-promises

- This file does not include benchmark numbers — those live under
  [`benchmarks/`](../../../benchmarks/). Performance varies per model.
- The profile is fictional. Do not use it as a template for storing real
  student data without consulting [`SPEC.md` §29c (privacy guards)](../../../SPEC.md)
  and your local data-protection regime.
- "Works out-of-the-box" means *the prompt loads cleanly and the system
  message is well-formed* — not that any specific model will pass a
  particular pedagogical evaluation.
