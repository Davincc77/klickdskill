# Mistral AI — .klickd v4.0.0 Integration

**SDK:** [mistralai](https://github.com/mistralai/client-python) · `pip install mistralai`
**.klickd:** `pip install klickd==4.0.0`

This is a **compatibility bridge, not native Mistral support.** Mistral's
chat endpoint accepts the same system/user message shape every other
adapter in this repo uses, so a `.klickd` profile maps onto a Mistral
`chat.complete(model=..., messages=[...])` request the same way it maps
onto OpenAI or xAI. The format is portable; compatibility still depends
on the reader supporting it (or following the
[generic pattern](generic.md)).

## Quick start (dry-run, no network)

The bridge ships a CLI that builds the request locally and prints it —
no API key, no SDK, no network:

```bash
PYTHONPATH=packages/pypi/klickd/src \
  python examples/v4/integrations/mistral/klickd_mistral_cli.py \
    examples/v4/integrations/mistral/fixtures/resume_session.klickd \
    --message "Let's continue."
```

Output is the exact `{"model", "messages"}` payload you would send.

## Live call

```python
import os
from mistralai import Mistral
from klickd import load_klickd

from examples.v4.integrations.mistral.klickd_mistral import klickd_to_messages

with open("profile.klickd", "rb") as f:
    payload = load_klickd(f.read())          # passphrase=... if encrypted

messages = klickd_to_messages(payload, "Let's continue.")

client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])  # never hard-code
response = client.chat.complete(model="mistral-large-latest", messages=messages)
print(response.choices[0].message.content)
```

The reusable helper lives at
[`examples/v4/integrations/mistral/klickd_mistral.py`](../../examples/v4/integrations/mistral/klickd_mistral.py)
and exposes a one-shot `chat(profile_path, user_message)` wrapper. The
wrapper reads the API key from `MISTRAL_API_KEY`; it never logs it.

## Models

Mistral publishes its current catalog at <https://docs.mistral.ai/>. The
helper defaults to `mistral-large-latest`; pass `model=` to pin a
specific version. `.klickd` makes no assumption about which model is
selected — it is purely the state layer.

## Compressed vs. verbatim memory

By default the bridge sends only the system prompt plus the live turn —
prior `memory[]` turns are summarized through `user_preferences` /
`context`, not replayed. **Compressed memory is the optional, cheaper
default.** Pass `--replay-memory` (CLI) or `replay_memory=True`
(`klickd_to_messages` / `chat`) to replay memory turns verbatim when
exact recall matters more than tokens.

## Security & trust boundaries

- **Encrypted files.** `.klickd` envelopes may be encrypted
  (Argon2id + AES-GCM). The Mistral model never decrypts anything: the
  trusted local `klickd` runtime decrypts the file *before* the prompt
  is built. Pass `passphrase=...` to `load_klickd` / `load_klickd_path`.
  Never put a passphrase or API key inside a `.klickd` profile.
- **Prompt injection.** If `injection_target` is `user_message` or
  `both`, `klickd_to_system_prompt()` prepends the JSON Injection Guard
  (SPEC §25.3) so structured content arriving in user messages is
  treated as data, not instructions. This is mitigation, not a
  guarantee — review profiles from untrusted sources before injecting.
- **Trust boundary.** The local runtime is trusted (it decrypts and
  builds the prompt); the remote model is not. Secrets stay on the local
  side of that line. Treat the API key like any production secret.
- **Redaction.** All `_`-prefixed debug/benchmark keys (e.g. `_bench`)
  are stripped before injection (SPEC §29); the helper does this.

## Provider-specific limitations

- **Not native support.** This is a workflow-level compatibility bridge.
  Mistral does not parse `.klickd` natively; the adapter translates the
  profile into ordinary chat messages.
- **No compliance claim.** Using this bridge does **not** make a
  deployment GDPR- or EU AI Act-compliant, and `.klickd` is not a
  universal or industry standard. Compliance depends on how *you* handle
  data, retention, and disclosure — out of scope for this adapter.
- **API surface drift.** This adapter targets the `mistralai`
  `client.chat.complete(...)` surface. If Mistral changes method names or
  message schema, pin the SDK version or update the wrapper.
- **Token budget.** Long `memory[]` replays can exceed the model's
  context window. Prefer the compressed default unless verbatim recall is
  required.

## Run the tests

```bash
PYTHONPATH=packages/pypi/klickd/src \
  pytest examples/v4/integrations/mistral/tests -q
```

Hermetic: no network, and `mistralai` need not be installed (the live
call test is skipped if it is absent).

---

Tracking: [issue #108](https://github.com/Davincc77/klickdskill/issues/108).
