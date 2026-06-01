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

## Runnable example (check / live)

A self-contained, two-mode example lives at
[`examples/v4/integrations/xai_grok/resume_chat_example.py`](../../examples/v4/integrations/xai_grok/resume_chat_example.py):

```bash
# Hermetic dry-run: no `openai` import, no network, no API key.
# Decodes a .klickd source, builds the OpenAI-compatible messages, prints them.
python examples/v4/integrations/xai_grok/resume_chat_example.py --check
python examples/v4/integrations/xai_grok/resume_chat_example.py --check --starter coding.klickd

# Live: requires `pip install openai>=1.0` and XAI_API_KEY; runs a real Grok turn.
python examples/v4/integrations/xai_grok/resume_chat_example.py --live
```

`klickd_to_messages(payload, user_message)` is the pure bridge both modes
share — it returns the `[{"role": "system", ...}, {"role": "user", ...}]`
list `chat.completions` expects, and is the function the test suite
exercises. `load_starter_skill("coding.klickd")` loads a bundled
capability pack via the public SDK accessor; starter packs carry
`verification_gates` and a `memory_scope`, not a persona `context`, so use
a persona profile when you want cross-session *resume*.

## Limitations & guardrails

- **Compatible bridge, not native support.** This is a workflow bridge
  over xAI's OpenAI-compatible Chat Completions API. It is **not** native
  `.klickd` support inside xAI/Grok beyond the adapter you run here.
- **No compliance claim.** This adapter does **not** confer automatic GDPR
  or EU AI Act compliance — that is the operator's responsibility. It is
  **not** a universal standard. See the [claim boundary](../../README.md).
- **Compressed memory is optional.** Nothing here depends on the
  compressed-memory track (RFC-010); plain `memory[]` entries suffice.
- **Trust boundary / prompt injection.** A decoded `.klickd` payload is
  **untrusted user content**, not privileged instructions. When a payload
  sets `injection_target` to `user_message` / `both`, the prompt builder
  prepends the JSON Injection Guard (SPEC §25.3); still treat any text that
  reaches a chat turn as data, never as a command.
- **Encrypted files.** Pass `passphrase=...` to `load_klickd_path()` for
  encrypted envelopes; the bundled starter packs are plain. Never embed the
  `XAI_API_KEY` (or any secret) in a `.klickd` profile.
- **Field stripping.** `_`-prefixed debug / benchmark fields are stripped
  before injection (SPEC §29) — the helpers do this for you.
- **Gate enforcement.** `verification_gates` are surfaced to Grok as
  instructions only. Enforce real gate semantics in your host application —
  the LLM is the *agent*, not the *referee* (SPEC §29).
- **Provider-specific limits.** Grok is reached through the OpenAI client
  with `base_url = https://api.x.ai/v1`; the model catalog, rate limits,
  context window, and any silent truncation are xAI's, not `.klickd`'s.
  Set an explicit `max_tokens` for large payloads and pin a model with
  `model=` when you need a specific Grok version.

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
