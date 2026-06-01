# `.klickd` × LangChain / LangGraph — memory bridge

A small, dependency-light bridge that loads a `.klickd` v4 profile or starter
skill **through the public `klickd` SDK only** and converts the validated
context into LangChain messages and LangGraph state.

## What this is

- **A converter, not native support.** This is *bridge-mediated
  compatibility*: the `.klickd` payload is the portable state layer; your
  chain / graph stays ordinary LangChain / LangGraph code. We do **not** claim
  native framework integration beyond what these files implement.
- **Import-safe.** `klickd_memory.py` imports only the `klickd` SDK at module
  load time. `langchain_core` / `langgraph` are lazy-imported, so the bridge
  lints, imports, and unit-tests with no LangChain install.

## Files

| File | Purpose |
|---|---|
| [`klickd_memory.py`](./klickd_memory.py) | The `KlickdMemory` bridge + `load_profile` / `load_starter_skill`. |
| [`klickd_langchain.py`](./klickd_langchain.py) | System-prompt builder (reused by the bridge). |
| [`example_resume_session.py`](./example_resume_session.py) | Runnable cross-session resume demo. |
| [`fixtures/resume_session.klickd`](./fixtures/resume_session.klickd) | Plain v4.0 profile used by the example/tests. |
| [`tests/`](./tests/) | Hermetic load / bridge / error-path tests. |

## Quickstart

```python
from klickd_memory import KlickdMemory

# Load a bundled starter skill (plain, no passphrase) via the SDK …
mem = KlickdMemory.from_starter_skill("coding.klickd")
# … or a profile from disk (encrypted profiles need a passphrase):
# mem = KlickdMemory.from_path("profile.klickd", passphrase="…")

# LangChain-compatible (role, content) tuples — system prompt + prior turns:
for role, content in mem.to_messages():
    ...

# LangGraph state: {"messages": [...], "klickd": {resume, gates, authority}}:
state = mem.to_langgraph_state()

# Ready-made langchain-core message objects (requires langchain-core):
# msgs = mem.to_lc_messages()
```

Compressed memory is **opt-in**: `mem.to_messages(compressed=True)` collapses
prior turns into a single system summary line instead of replaying them.

## Run the example

From a clean checkout — no network, no LangChain required:

```bash
PYTHONPATH=packages/pypi/klickd/src \
    python examples/v4/integrations/langchain/example_resume_session.py
```

If `langchain-core` / `langgraph` are installed, the example also builds real
LangChain message objects and runs a tiny LangGraph; otherwise it prints the
dependency-free tuples and state dict.

## Run the tests

```bash
PYTHONPATH=packages/pypi/klickd/src \
    pytest examples/v4/integrations/langchain/tests -q
```

## Trust boundaries & limitations

- **The model does not decrypt the file. The trusted local runtime does.**
  Encrypted envelopes are decrypted in-process via `klickd.load_klickd` with a
  passphrase you supply. The example's passphrase is demo-only — never commit a
  real one.
- **System vs. user injection.** `.klickd` content is injected in the *system*
  role. If a payload sets `injection_target` to `user_message` / `both`, the
  system prompt prepends a JSON Injection Guard (SPEC §25.3) so structured data
  in user messages is treated as content, not instructions.
- **Gates are advisory here; the host is the referee.** `verification_gates`
  are surfaced to the model as text and preserved in `state["klickd"]`. Actual
  enforcement (`block` / `confirm` / `silent`) belongs in your application
  code, not the LLM. `human_authority` / `human_veto_policy` are carried
  through unchanged — the final decision owner stays the human carrier.
- **Validation is best-effort.** `from_payload` hard-requires a JSON object
  with `payload_schema_version`; if `jsonschema` is installed it also runs a
  *non-fatal* pass against the permissive v4 *preview* schema (findings on
  `mem.schema_warnings`). We do not hard-fail on the strict GA schema, because
  starter skills nest state under `x_klickd_pack` and personas predate the GA
  surface.
- **No compliance claims.** This bridge makes no GDPR, EU AI Act, or
  universal-standard claim. It is a format converter.

## References

- DOI / evidence: <https://doi.org/10.5281/zenodo.20262530>
- Spec boundaries: [`SPEC.md`](../../../../SPEC.md) (§25.3 injection, §29 redaction)
- Integration guide: [`docs/integrations/langchain.md`](../../../../docs/integrations/langchain.md)

SPDX-License-Identifier: CC0-1.0
