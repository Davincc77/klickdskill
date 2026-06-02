# x.klickd dev-preview

A short, offline path for an external developer to see what x.klickd structured
memory/skill context does — in under 10 minutes, **no API key, no account, no
secrets**.

> Status: developer preview. The public release remains v4.1. This directory is
> a hands-on preview, **not** a new public release, benchmark, or product claim.

## Quick commands

From a fresh clone of the repository root:

```bash
git clone https://github.com/Davincc77/klickdskill
cd klickdskill
python -m venv .venv && source .venv/bin/activate
pip install -e .
python examples/dev-preview/hello_skill.py
python examples/dev-preview/run_demo.py
```

- `hello_skill.py` — smoke test. Loads a bundled x.klickd starter skill and one
  of the 42 v4.1 candidate skill packs, hash-verifying it against the published
  manifest. Exit 0 means the SDK is installed and skills load.
- `run_demo.py` — the comparative demo. Writes
  [`results/comparison_scorecard.md`](results/comparison_scorecard.md) and
  prints a summary.

`pip install -e .` from the repo root installs the same published `klickd`
package whose source lives at `packages/pypi/klickd/` (no code duplication).

## What this proves

The demo simulates an agent **resuming a complex coding task after an
interruption**, run two ways over the same static fixture
([`fixtures/interrupted_task.json`](fixtures/interrupted_task.json)):

- **Baseline** — only an ambiguous resume prompt (`"...ship it"`) is available.
  The resumer has no carried task state and no governance, so it assumes prior
  work is done, skips the failing test, and treats "ship it" as push-to-main.
- **With x.klickd** — the same prompt **plus** carried task state (memory) and
  the verification gates + human-veto policy read **live from the bundled
  `x.klickd/coding` skill** via the SDK. The resumer recovers the failing-test
  state, runs the suite first, follows the saved review channel, and refuses
  the human-veto-scoped actions.

The governance rules the x.klickd lane obeys (e.g. `force_push`,
`production_deploy`) are read at runtime from the skill, not hardcoded in the
demo — so the demo cannot drift from what the skill actually carries.

## What this does NOT prove

- **Not a model benchmark.** No LLM or API is called. Both lanes are
  deterministic rule-based simulations; this is labelled a *deterministic local
  demo*, not a quality or performance measurement of any assistant.
- **Not native client support.** Loading a `.klickd` artifact and hash-verifying
  it does not mean any AI client natively understands `.klickd`. Compatibility
  always depends on the reader.
- **No compliance claim.** `.klickd` is portable, client-side-encryptable user
  state; it does not by itself confer GDPR / EU AI Act compliance.

## How it relates to the internal supply chain

The skill packs loaded here are the **public** v4.1 candidate artifacts shipped
with the SDK and verified against the published manifest. The repository also
runs an internal, non-normative process that vets future candidate skills
before any of them could become public. That internal process is intentionally
**out of scope** for this preview: the quickstart reads only already-public,
hash-verifiable artifacts and needs no private inputs of any kind.

## Files

| File | Purpose |
|---|---|
| `hello_skill.py` | Smoke test: load + hash-verify a skill via the SDK. |
| `run_demo.py` | Deterministic with/without-x.klickd resume comparison. |
| `fixtures/interrupted_task.json` | Static input describing the interrupted task. |
| `results/comparison_scorecard.md` | Generated scorecard (committed sample included). |
