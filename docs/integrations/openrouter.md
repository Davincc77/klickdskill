# OpenRouter — .klickd v3.4 Integration

**Docs:** [openrouter.ai/docs](https://openrouter.ai/docs)

OpenRouter provides a single OpenAI-compatible endpoint routing to 200+ models. Ideal for **Soul Handoff** workflows where the user switches AI providers mid-conversation — the `.klickd` file carries full context, and OpenRouter selects the target model.

```python
import json
import httpx

with open("profile.klickd") as f:
    klickd = json.load(f)

system_prompt = klickd.get("user_preferences", "")
ctx = klickd.get("context", {})
if ctx.get("current_state"):
    system_prompt += f"\n\nCurrent state: {ctx['current_state']}"
if ctx.get("resume_trigger"):
    system_prompt += f"\n{ctx['resume_trigger']}"

# Strip benchmark/debug namespaces before injection
payload_keys_to_strip = [k for k in klickd if k.startswith("_")]
for k in payload_keys_to_strip:
    klickd.pop(k)

response = httpx.post(
    "https://openrouter.ai/api/v1/chat/completions",
    headers={
        "Authorization": "Bearer YOUR_OPENROUTER_API_KEY",
        "HTTP-Referer": "https://yourapp.com",
        "X-Title": "Your App Name"
    },
    json={
        "model": "qwen/qwen3-32b",   # or any OpenRouter model slug
        "max_tokens": 2048,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Let's continue where we left off."}
        ]
    }
)

print(response.json()["choices"][0]["message"]["content"])
```

**Soul Handoff — cross-provider pattern:**

1. User exports `.klickd` from Provider A (e.g. GPT-4o).
2. `.klickd` file is loaded by the new client.
3. `user_preferences` is injected as `system` message into Provider B via OpenRouter.
4. Companion identity (`companion_identity.name`, `teaching_mode`) is preserved.
5. Session resumes from `context.resume_trigger`.

> **Model selection:** For `injection_resistance_level: strict`, prefer `qwen/qwen3-32b` or `meta-llama/llama-3.3-70b-instruct`.  
> Strip all `_`-prefixed fields before injection.
