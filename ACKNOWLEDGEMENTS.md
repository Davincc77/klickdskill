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

### Pre-action verification & scoped operating rules

**Contributor:** [cart0ne](https://dev.to/cart0ne) (DEV.to)
**Source:** Comment thread on *AI agents don't have a memory problem — they have an architecture problem* (DEV.to, 2026)
**Where it landed in the repository:**

- [`SPEC.md` §33.4 — Preview design principles](SPEC.md#334-preview-design-principles) (pre-action vs post-action clarification)
- [`SPEC.md` §33.10 — Privacy invariants & semantic stability (preview)](SPEC.md#3310-privacy-invariants--semantic-stability-preview)
- [`ROADMAP.md` — RFC-005 placeholder (scoped state / handoff scope)](ROADMAP.md)

**Summary of the insight:** A portable AI state format benefits from distinguishing *state* (who the user is, what they are working on) from *operating rules / constraints* (when the agent should slow down or refuse), and from carrying both alongside an explicit *verification-before-action* contract rather than only a post-hoc audit log. This framing reinforced the existing direction of RFC-002 (`verification_gates` are pre-action by design, `error_journal[]` is post-action) and motivated a future RFC slot for *scoped state* (project / role / handoff sub-profiles). Inclusion here does not imply endorsement of the eventual design.

### Claim-level memory, append-only journals, and syntactic vs behavioral round-trip

**Contributor:** [TxDesk](https://dev.to/txdesk) (DEV.to)
**Source:** Comment thread on *AI agents don't have a memory problem — they have an architecture problem* (DEV.to, 2026)
**Where it landed in the repository:**

- [`SPEC.md` §33.10 — Privacy invariants & semantic stability (preview)](SPEC.md#3310-privacy-invariants--semantic-stability-preview) (syntactic round-trip ≠ behavioral equivalence note)
- [`ROADMAP.md` — RFC-005 placeholder (claim-level memory growth, deterministic provenance-preserving compaction)](ROADMAP.md)

**Summary of the insight:** Sustainable portable state needs (a) memory at the level of *claims* with source, timestamp, and ideally model/confidence rather than free-form prose; (b) append-only event logs with explicit, provenance-preserving compaction rather than full-session rewrites; and (c) an explicit recognition that syntactic round-trip (the bytes survive) is necessary but not sufficient for behavioral equivalence across providers and model versions. The first two reinforced the existing append-only design of `verification_artifacts[]` / `error_journal[]` and motivated a future RFC for claim-memory compaction; the third was added as a non-normative reader/writer note in §33.10. Inclusion here does not imply endorsement of any specific implementation choice.

---

## How to contribute an insight

If a discussion you participated in materially shaped a section of the docs or the spec, open a PR adding an entry to this file in the same shape:

- **Contributor** — name or handle, with a link.
- **Source** — a public URL (post, comment, talk, issue) that future readers can verify.
- **Where it landed** — the specific file(s) and section(s) the insight informed.
- **Summary of the insight** — one short paragraph, in your own words, that someone reading only this file could understand without clicking the source.

Please do not add entries that are just thanks or general support — this file is for insights that visibly changed the documentation or the design intent. For private feedback, code contributions, or sponsorship, see [`CONTRIBUTING.md`](CONTRIBUTING.md) and the repository's commit history instead.
