# `.klickd` × OpenAI — context bridge

A small, dependency-light bridge that loads a `.klickd` v4 profile or starter
skill **through the public `klickd` SDK only** and converts the validated
context into OpenAI-compatible chat messages (the list you pass as `messages=`
to `client.chat.completions.create`).

## What this is

- **A converter, not native support.** This is *bridge-mediated
  compatibility*: the `.klickd` payload is the portable state layer; your call
  stays an ordinary OpenAI Chat Completions request. No OpenAI service
  decrypts or auto-loads a `.klickd` file. We do **not** claim native OpenAI
  `.klickd` support beyond what these files implement.
- **Import-safe.** `klickd_openai.py` imports only the `klickd` SDK at module
  load time. The `openai` package is lazy-imported (only inside `create()`),
  so the bridge lints, imports, and unit-tests with no `openai` install.

## Files

| File | Purpose |
|---|---|
| [`klickd_openai.py`](./klickd_openai.py) | The `KlickdOpenAI` bridge + `load_profile` / `load_starter_skill`. |
| [`example_resume_session.py`](./example_resume_session.py) | Runnable cross-session resume demo (`--check` dry-run default, `--live` optional). |
| [`fixtures/resume_session.klickd`](./fixtures/resume_session.klickd) | Plain v4.0 profile used by the example/tests. |
| [`tests/`](./tests/) | Hermetic load / bridge / error-path tests. |

## Quickstart

```python
from klickd_openai import KlickdOpenAI

# Load a bundled starter skill (plain, no passphrase) via the SDK …
bridge = KlickdOpenAI.from_starter_skill("coding.klickd")
# … or a profile from disk (encrypted profiles need a passphrase):
# bridge = KlickdOpenAI.from_path("profile.klickd", passphrase="…")

# OpenAI-compatible message dicts — instruction message + prior turns:
messages = bridge.to_messages()                 # [{"role": "system", "content": ...}, ...]

# Full create(...) kwargs, with an appended user turn:
request = bridge.to_request(model="gpt-4o", user_input="continue", temperature=0)
# resp = client.chat.completions.create(**request)

# Or make the call directly (requires `openai` + OPENAI_API_KEY):
# resp = bridge.create(model="gpt-4o", user_input="continue")
```

Compressed memory is **opt-in**: `bridge.to_messages(compressed=True)` collapses
prior turns into a single instruction-role summary line instead of replaying
them.

## Run the example

From a clean checkout — no network, no `openai` required:

```bash
PYTHONPATH=packages/pypi/klickd/src \
    python examples/v4/integrations/openai/example_resume_session.py            # dry-run
```

Add `--live` to make one real `chat.completions.create` call. That mode needs
`pip install openai` and `OPENAI_API_KEY`; it is skipped (with a message) if
either is missing.

## Run the tests

```bash
PYTHONPATH=packages/pypi/klickd/src \
    pytest examples/v4/integrations/openai/tests -q
```

## Message-role boundaries (read these)

- **System / developer is trusted; user is not.** `.klickd` context is injected
  in the instruction role only. OpenAI's o-series / GPT-4.1+ models rename
  `system` to `developer` — same trust level. Pick with
  `to_messages(instruction_role="developer")`. The bridge **never** injects
  `.klickd` context into the `user` role; the only `user` message it adds is
  the `user_input=` you pass to `to_request` / `create`.
- **Prompt-injection guard.** If a payload sets `injection_target` to
  `user_message` / `both`, the instruction message prepends a JSON Injection
  Guard (SPEC §25.3) so structured data arriving in user turns is treated as
  content, not instructions.
- **`_`-prefixed fields are stripped** before injection (SPEC §29) — they are
  debug/benchmark only and never reach the model.

## Trust boundaries & limitations

- **The model does not decrypt the file. The trusted local runtime does.**
  Encrypted envelopes decrypt in-process via `klickd.load_klickd` with a
  passphrase you supply. The example's passphrase is demo-only — never commit a
  real one. Once you call the API, the decrypted context leaves your process
  for OpenAI; that is your decision to make.
- **Gates are advisory in the prompt; the host is the referee.**
  `verification_gates` are surfaced to the model as text. Actual enforcement
  (`block` / `confirm` / `silent`) belongs in your application code, not the
  LLM. `human_authority` / `human_veto_policy` are carried through unchanged —
  the final decision owner stays the human carrier (SPEC §29).
- **Validation is best-effort.** `from_payload` hard-requires a JSON object
  with `payload_schema_version`; if `jsonschema` is installed it also runs a
  *non-fatal* pass against the permissive v4 *preview* schema (findings on
  `bridge.schema_warnings`). It does not hard-fail on the strict GA schema,
  because starter skills nest state under `x_klickd_pack` and personas predate
  the GA surface.
- **No compliance claims.** This bridge makes no GDPR, EU AI Act, or
  universal-standard claim. It is a format converter.

## References

- Issue: <https://github.com/Davincc77/klickdskill/issues/107>
- DOI / evidence: <https://doi.org/10.5281/zenodo.20262530>
- Spec boundaries: [`SPEC.md`](../../../../SPEC.md) (§25.3 injection, §29 redaction)
- Integration guide: [`docs/integrations/openai.md`](../../../../docs/integrations/openai.md)

SPDX-License-Identifier: CC0-1.0
