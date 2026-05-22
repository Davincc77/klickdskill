# RFC-003 Fixtures — Context Cost Benchmark

> **Non-normative, benchmark-only fixtures.** These files are inputs for the
> Context Cost Benchmark defined in [`../RFC.md`](../RFC.md). They are NOT part
> of the `.klickd` normative specification, and they do not validate against any
> schema in [`schema/`](../../../schema/) or [`schemas/`](../../../schemas/).

## What this is

A minimal, reproducible fixture set for **one** project-management agent task,
exercised over **10 user messages** across the three RFC-003 conditions
(`cold`, `paste`, `klickd`). The fixtures are intentionally small so that
external contributors can run the benchmark cheaply.

This PR ships **fixtures only**. The runner script and any actual model calls
land in a separate follow-up PR (see [`../RFC.md` §10](../RFC.md#10-next-steps)).

## Layout

```
fixtures/
├── README.md                              # this file
├── task.md                                # human-readable task spec
├── prompts/
│   └── flow.json                          # 10 user messages, in order
├── klickd/
│   ├── sample_context.json                # cleartext .klickd-style context
│   └── README.md                          # note on encrypted .klickd payload
├── baseline/
│   └── system_prompt.txt                  # long-form prose, cold-start mode
├── validation/
│   └── ground_truth.json                  # constraints, forbiddens, scoring hooks
└── verification_artifacts/
    └── sample_test.log                    # artifact-tee demo (pass+fail)
```

## Conditions covered

| Condition | Input to the model |
|---|---|
| `cold`   | `baseline/system_prompt.txt` short header only (no project context) + `flow.json` messages |
| `paste`  | `baseline/system_prompt.txt` short header + the full long-form prose pasted as a leading user message + `flow.json` messages |
| `klickd` | `baseline/system_prompt.txt` short header + `<UserContext>` block synthesised from `klickd/sample_context.json` + `flow.json` messages |

The three conditions share the same `flow.json` — that is the point of the
benchmark.

## On the encrypted `.klickd` payload

This PR ships **only the cleartext** `klickd/sample_context.json`. The
corresponding encrypted `.klickd` file (`sample_context.klickd`) is **not**
included yet. See [`klickd/README.md`](./klickd/README.md) for the rationale
and the deterministic-generation note.

If/when an encrypted fixture is added, it MUST be marked `encrypted: true` in
its envelope, MUST use the public test passphrase
`benchmark-public-test-passphrase`, and MUST be clearly labelled
**test-only / not secret** in every place it appears.

## Reproducibility

- All JSON files are 2-space indented, UTF-8, no trailing commas (per
  [`CONTRIBUTING.md`](../../../CONTRIBUTING.md)).
- `flow.json` is fixed: the 10 messages are the same across all three conditions.
- `ground_truth.json` is the only file the future runner uses to decide
  pass/fail per RFC-003 §8.
- No provider API keys, no live calls, no paid resources are required to read
  or validate these fixtures.

## What this is NOT

- Not a runner. No Python / JS scripts here.
- Not a result. No `results/YYYY-MM-DD/` directory is produced.
- Not a spec change. RFC-003 remains `Draft`; nothing here is normative.
- Not a leaderboard. No models, vendors, or scores are recorded.
