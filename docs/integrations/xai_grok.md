# xAI Grok — .klickd v4.0.0 Integration

**API:** [xAI Chat Completions](https://docs.x.ai/) (OpenAI-compatible) ·
`base_url = https://api.x.ai/v1`
**SDK:** the official OpenAI Python client works directly. `pip install openai>=1.0`
**.klickd:** `pip install klickd==4.0.0`

Because xAI's chat endpoint is OpenAI-compatible, `.klickd` injection
follows the exact same pattern as the [OpenAI guide](openai.md): the
payload becomes the system message; the rest of the request is unchanged.

## Quick start

```python
import os
from openai import OpenAI
from klickd import load_klickd

from examples.v4.integrations.xai_grok.klickd_xai import klickd_to_system_prompt

with open("examples/v4/personas/05-rpg-gamer-en.klickd", "rb") as f:
    payload = load_klickd(f.read())

system_prompt = klickd_to_system_prompt(payload)

client = OpenAI(
    api_key=os.environ["XAI_API_KEY"],   # required; never hard-code
    base_url="https://api.x.ai/v1",
)

response = client.chat.completions.create(
    model="grok-2-latest",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "Let's continue."},
    ],
)
print(response.choices[0].message.content)
```

The reusable helper lives at
[`examples/v4/integrations/xai_grok/klickd_xai.py`](../../examples/v4/integrations/xai_grok/klickd_xai.py)
and exposes a one-shot `chat(profile_path, user_message)` convenience
wrapper. The wrapper reads the API key from the `XAI_API_KEY`
environment variable; it never logs it.

## Models

xAI publishes the current model catalog at <https://docs.x.ai/>. The
helper defaults to `grok-2-latest`; pass `model=` to pin a specific
version. `.klickd` makes no assumption about which Grok model is
selected — it is purely the state layer.

## Notes

- Always use the `system` role unless `injection_target` is
  `user_message` / `both` — in which case `klickd_to_system_prompt()`
  prepends the JSON Injection Guard automatically (SPEC §25.3).
- Strip `_`-prefixed debug / benchmark keys before injection (SPEC §29);
  the helper does this.
- Encrypted envelopes: pass `passphrase=...` to `load_klickd_path()`.
- xAI uses standard bearer auth; treat the key like any production
  secret. **Never** commit it, and never include it in a `.klickd`
  profile.
