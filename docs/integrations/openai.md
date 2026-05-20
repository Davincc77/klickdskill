# OpenAI API — .klickd v3.4 Integration

**SDK:** [openai-python](https://github.com/openai/openai-python) · `pip install openai`

Inject `user_preferences` as the system message. The rest of the `.klickd` payload can be appended as additional structured context.

```python
import json
from openai import OpenAI

client = OpenAI()  # uses OPENAI_API_KEY env var

with open("profile.klickd") as f:
    klickd = json.load(f)

# Build system message from .klickd context
system_prompt = klickd.get("user_preferences", "")

# Optional: append structured context for richer handoff
if klickd.get("context"):
    ctx = klickd["context"]
    system_prompt += f"\n\nCurrent project: {ctx.get('current_project', '')}"
    system_prompt += f"\nState: {ctx.get('current_state', '')}"
    if ctx.get("resume_trigger"):
        system_prompt += f"\n{ctx['resume_trigger']}"

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "Let's continue."}
    ]
)

print(response.choices[0].message.content)
```

> **Note:** Inject `.klickd` context in the `system` role, not the `user` role.  
> If `injection_target` is `"user_message"` or `"both"`, also add the JSON Injection Guard (SPEC §25.3) as the first line of the system message.  
> Strip all `_`-prefixed fields (e.g. `_benchmark`) before injection.
