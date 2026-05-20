# Groq — .klickd v3.4 Integration

**SDK:** [groq-python](https://github.com/groq/groq-python) · `pip install groq`

Groq's API is OpenAI-compatible. Recommended models for `.klickd` payloads:

| Model | Use case |
|---|---|
| `llama-3.3-70b-versatile` | General purpose, strong context adherence |
| `qwen/qwen3-32b` | Preferred for `injection_resistance_level: strict` |

> ⚠️ Avoid `llama-3.1-8b-instant` when `injection_resistance_level` is `moderate` or `strict` (confirmed masked compliance vulnerability — SPEC §23.2).

```python
import json
from groq import Groq

client = Groq()  # uses GROQ_API_KEY env var

with open("profile.klickd") as f:
    klickd = json.load(f)

system_prompt = klickd.get("user_preferences", "")

ctx = klickd.get("context", {})
if ctx.get("current_state"):
    system_prompt += f"\n\nCurrent state: {ctx['current_state']}"
if ctx.get("resume_trigger"):
    system_prompt += f"\n{ctx['resume_trigger']}"

response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    max_tokens=2048,          # Set explicitly — payloads >1500 tokens risk truncation
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "Let's continue."}
    ]
)

print(response.choices[0].message.content)
```

> **Truncation:** Groq models may silently truncate responses on payloads exceeding ~1500 tokens.  
> Always set an explicit `max_tokens` value when injecting `.klickd` payloads.  
> Strip all `_`-prefixed fields (e.g. `_benchmark`) before injection.
