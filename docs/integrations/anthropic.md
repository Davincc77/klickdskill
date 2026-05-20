# Anthropic Claude API — .klickd v3.4 Integration

**SDK:** [anthropic-sdk-python](https://github.com/anthropic/anthropic-sdk-python) · `pip install anthropic`

Claude's Messages API accepts a top-level `system` parameter — ideal for `.klickd` injection.

```python
import json
import anthropic

client = anthropic.Anthropic()  # uses ANTHROPIC_API_KEY env var

with open("profile.klickd") as f:
    klickd = json.load(f)

system_prompt = klickd.get("user_preferences", "")

# Append key context fields for richer handoff
ctx = klickd.get("context", {})
if ctx.get("current_state"):
    system_prompt += f"\n\nCurrent state: {ctx['current_state']}"
if ctx.get("resume_trigger"):
    system_prompt += f"\n{ctx['resume_trigger']}"

message = client.messages.create(
    model="claude-opus-4-5",
    max_tokens=4096,
    system=system_prompt,
    messages=[
        {"role": "user", "content": "Let's continue where we left off."}
    ]
)

print(message.content[0].text)
```

> **Context window:** Claude Opus and Sonnet support 200 K tokens. For large `.klickd` payloads (full session history + archived sessions), Claude's context window is strongly recommended.  
> **Injection:** Always use the `system` parameter, not a user-role message, unless `injection_target` is `"user_message"` or `"both"`.  
> Strip all `_`-prefixed fields (e.g. `_benchmark`) before injection.
