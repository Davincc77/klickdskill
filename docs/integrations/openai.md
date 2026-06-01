# OpenAI — .klickd v4.0.0 Integration

**SDK:** [openai-python](https://github.com/openai/openai-python) · `pip install openai`
**`.klickd` SDK:** `pip install klickd`

`.klickd` content is injected in the **instruction role** (`system`, or
`developer` on the o-series / GPT-4.1+). The end user's input stays in the
`user` role. No OpenAI service decrypts or auto-loads a `.klickd` file — this
is *bridge-mediated compatibility*, not native support.

## Minimal example

```python
import json
from openai import OpenAI

client = OpenAI()  # uses OPENAI_API_KEY env var

with open("profile.klickd") as f:
    klickd = json.load(f)        # plain payload; use load_klickd(...) for encrypted

# Build the instruction message from .klickd context
system_prompt = klickd.get("user_preferences", "")
ctx = klickd.get("context") or {}
if ctx.get("current_project"):
    system_prompt += f"\n\nCurrent project: {ctx['current_project']}"
if ctx.get("current_state"):
    system_prompt += f"\nState: {ctx['current_state']}"
if ctx.get("resume_trigger"):
    system_prompt += f"\n{ctx['resume_trigger']}"

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "Let's continue."},
    ],
)

print(response.choices[0].message.content)
```

> Inject `.klickd` context in the `system` (or `developer`) role, never the
> `user` role. Strip all `_`-prefixed fields (e.g. `_bench`) before injection
> (SPEC §29). If `injection_target` is `user_message` / `both`, prepend the
> JSON Injection Guard (SPEC §25.3) as the first line of the instruction
> message.

## Reusable bridge & cross-session resume

For chat/agent workflows that **resume context across sessions**, use the
`KlickdOpenAI` bridge at
[`examples/v4/integrations/openai/klickd_openai.py`](../../examples/v4/integrations/openai/klickd_openai.py).
It loads a profile or starter skill **through the `klickd` SDK only**
(`load_klickd`, `get_starter_skill_bytes`, `validate_iter_errors`) and converts
the validated context into OpenAI message dicts and full `create(...)` kwargs.
The `openai` package is lazy-imported, so the bridge imports and unit-tests with
no `openai` install. This is *bridge-mediated compatibility, not native OpenAI
support*.

```python
from klickd_openai import KlickdOpenAI

bridge = KlickdOpenAI.from_starter_skill("coding.klickd")    # SDK-loaded, plain
# or: KlickdOpenAI.from_path("profile.klickd", passphrase="…")  # encrypted

messages = bridge.to_messages()                          # [{"role","content"}, ...]
request  = bridge.to_request(model="gpt-4o", user_input="continue", temperature=0)
# resp   = client.chat.completions.create(**request)
# resp   = bridge.create(model="gpt-4o", user_input="continue")   # optional live call
```

A runnable cross-session example (save in session 1, resume in session 2) lives
at
[`example_resume_session.py`](../../examples/v4/integrations/openai/example_resume_session.py).
It runs from a clean checkout with **no network and no `openai` install** in its
default `--check` dry-run mode; pass `--live` (with `openai` + `OPENAI_API_KEY`)
to make one real call.

```bash
PYTHONPATH=packages/pypi/klickd/src \
    python examples/v4/integrations/openai/example_resume_session.py          # dry-run
PYTHONPATH=packages/pypi/klickd/src \
    pytest examples/v4/integrations/openai/tests -q                           # tests
```

### Message-role boundaries (read these)

- **System / developer is trusted; user is not.** Context is injected in the
  instruction role only. OpenAI renamed `system` to `developer` on the o-series
  / GPT-4.1+ models — same trust level; pick it with
  `to_messages(instruction_role="developer")`. The bridge never injects
  `.klickd` context into the `user` role.
- **Prompt-injection guard.** If `injection_target` is `user_message` / `both`,
  the instruction message prepends a JSON Injection Guard (SPEC §25.3) so
  structured data in user turns is treated as content, not instructions.
- **Compressed memory is opt-in.** `to_messages(compressed=True)` collapses
  prior turns into a single instruction-role summary line; the default replays
  them.
- **Trust boundary.** The model does not decrypt the `.klickd` file — the
  trusted local runtime does. Encrypted profiles decrypt in-process via
  `load_klickd` with a passphrase you supply. Once you call the API the
  decrypted context leaves your process for OpenAI; that is your decision.
- **Gates are advisory in the prompt; enforce them in the host.**
  `verification_gates` are surfaced as text; `human_authority` /
  `human_veto_policy` pass through unchanged, keeping the human carrier as final
  decision owner.
- **No compliance claims.** This bridge makes no GDPR, EU AI Act, or
  universal-standard claim — it is a format converter. See the
  [adapter README](../../examples/v4/integrations/openai/README.md),
  [issue #107](https://github.com/Davincc77/klickdskill/issues/107), the
  evidence pack at <https://doi.org/10.5281/zenodo.20262530>, and
  [`SPEC.md`](../../SPEC.md) (§25.3, §29) for boundaries.
