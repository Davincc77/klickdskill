# Acknowledgements

`.klickd` is developed in the open, and the framing of the format owes a lot to public conversation around it. This file records community insights that have visibly shaped the documentation or the design intent — without overstating endorsement. Inclusion here is not a co-author credit and does not imply that the named contributor reviewed or approved the final wording.

## Community insights

### Long context vs portable state

**Contributor:** [VoltageGPU](https://dev.to/voltagegpu) (DEV.to)
**Source:** Comment thread on [*AI agents don't have a memory problem — they have an architecture problem*](https://dev.to/davincc77/ai-agents-dont-have-a-memory-problem-they-have-an-architecture-problem-3pl6) (DEV.to, 2026)
**Where it landed in the repository:**

- [`README.md` §"Long context vs portable state"](README.md#long-context-vs-portable-state)
- [`benchmarks/context_cost/RFC.md` §9.1 — Relation to long-context models and context-window extension](benchmarks/context_cost/RFC.md#91-relation-to-long-context-models-and-context-window-extension)

**Summary of the insight:** GPU / runtime infrastructure (longer context windows, KV-cache offload, streaming attention) expands what a single inference call can process; it does not, on its own, retain user-level state between sessions, vendors, or models. The two layers are complementary: *longer context helps the model fit more; portable state helps the system repeat less.* This framing prompted the explicit non-competition language in the README and the non-normative `long_context` / `hybrid` comparison-condition note in RFC-003.

---

## How to contribute an insight

If a discussion you participated in materially shaped a section of the docs or the spec, open a PR adding an entry to this file in the same shape:

- **Contributor** — name or handle, with a link.
- **Source** — a public URL (post, comment, talk, issue) that future readers can verify.
- **Where it landed** — the specific file(s) and section(s) the insight informed.
- **Summary of the insight** — one short paragraph, in your own words, that someone reading only this file could understand without clicking the source.

Please do not add entries that are just thanks or general support — this file is for insights that visibly changed the documentation or the design intent. For private feedback, code contributions, or sponsorship, see [`CONTRIBUTING.md`](CONTRIBUTING.md) and the repository's commit history instead.
