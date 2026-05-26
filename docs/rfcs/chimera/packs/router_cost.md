# `router_cost` rows — `x.klickd/user` and `x.klickd/student`

> **Status:** Draft · NON-NORMATIVE · companion to [RFC-009 §8.7](../../RFC-009-chimera-v4.1.md) and to [`benchmarks/context_cost/`](../../../../benchmarks/context_cost/) (RFC-003).
> **Track:** `.klickd v4.1` Chimera.
> **Triggers no release.** No tag, no benchmark output published, no schema change.

This file pins **deterministic, heuristic token-cost estimates** for the first two `competency_pack`s under RFC-009, in a shape compatible with RFC-003's `chimera_v41_extrapolation()` function ([`benchmarks/context_cost/runner.py`](../../../../benchmarks/context_cost/runner.py)).

It satisfies validation criterion **§8.7 (Router-priceable)** at spec level: every estimate below is reproducible offline from the canonicalised pack manifest using the same heuristic the RFC-003 runner already uses (`len(text)//4`). No provider API calls, no live tokenizer. When a real bundle ships, the same column is recomputed against the actual manifest bytes and the runner picks it up via the `pack_token_costs` argument.

## 1. Heuristic method (deterministic, offline)

For each pack:

1. Take the canonical JSON of the **manifest** (the top-level pack object — the shape sketched in [`student.md` §5](./student.md#5-illustrative-shape-sketch-not-a-json-schema)), with stable key order and no extraneous whitespace, encoded as UTF-8.
2. Compute `tokens_estimate = len(json_bytes_as_str) // 4` — same proxy as `input_token_estimate_heuristic` in [`benchmarks/context_cost/runner.py`](../../../../benchmarks/context_cost/runner.py) (RFC-003 §6).
3. Treat this estimate as the pack's `tokens_estimate` for `chimera_v41_extrapolation(pack_token_costs={...})`. It is illustrative; a future bundle update recomputes it against the bundled bytes.

This estimate excludes the offline SKOS bundle (`bundle/`), which lives alongside the manifest but is **not** loaded into the prompt by default — RFC-009 §5.7. A reader that loads the bundle pays additional cost, modelled separately under `bundle_token_cost` below.

## 2. Estimates

| Pack | `pack` id | Manifest scope | Manifest size (bytes, canonical JSON, illustrative) | `tokens_estimate` (heuristic) | `bundle_token_cost` (if loaded) | `baseline` | `source_row` |
|---|---|---|---|---|---|---|---|
| `x.klickd/user`    | `x.klickd/user`    | Base transversal core + `language_proficiency[]` only — no domain `competencies[]` beyond the base. | ~2,400 | **600** | ~1,800 (ESCO transversal + DigComp + LifeComp + EQF SKOS subset) | `base_plus_one` | [`router_cost.md#3-1`](#31-xklickduser-derivation) |
| `x.klickd/student` | `x.klickd/student` | Base transversal core + 6–10 ESCO/DigComp competencies + `mastery[]` carrier state + `curriculum_refs[]` + `exam_targets[]` + `history[]` (bounded, ~10 entries). | ~3,400 | **850** | ~2,400 (base bundle + ESCO education subset + EQF + CEFR) | `base_plus_one` | [`router_cost.md#3-2`](#32-xklickdstudent-derivation) |

The numeric estimates are **deliberately conservative**:

- `x.klickd/user` is smaller than the default 850 in `DEFAULT_CHIMERA_PACKS` because the base layer is leaner than a domain pack.
- `x.klickd/student` matches the default 850 — the heuristic confirms the runner default is the right order of magnitude.
- `bundle_token_cost` is reported separately so the router can decide whether to pay for offline resolution (e.g. a reader on an air-gapped machine) or rely on cached IRI resolution (default for connected runs).

## 3. Per-pack derivations

### 3.1 `x.klickd/user` derivation

Manifest scope (approximate, per [`../schema-fragments/README.md`](../schema-fragments/README.md) §1):

```text
pack                     ~30 B   (string "x.klickd/user")
pack_version             ~20 B
spec_ref                 ~70 B
publisher                ~80 B
frameworks[]             ~700 B  (4 entries: esco, digcomp, lifecomp, eqf)
base_transversal_core    ~900 B  (4 frameworks + 17 transversal_refs)
competencies[]           ~0 B    (empty for the base pack; all anchors live in base_transversal_core)
gates                    ~120 B
human_authority          ~120 B
memory_scope             ~40 B
evidence_policy          ~110 B
source_policy            ~110 B
router_cost              ~120 B
forbidden_fields         ~180 B
total                    ~2,400 B
tokens_estimate          ~600    (2400 // 4)
```

`bundle_token_cost` (when the SKOS bundle is loaded into the prompt rather than resolved from disk):

```text
esco/concepts.jsonld     ~700 B  (transversal subset, ~10 concepts × ~70 B)
digcomp/concepts.jsonld  ~500 B  (5 areas × ~100 B)
lifecomp/concepts.jsonld ~300 B  (9 competences × ~33 B)
eqf/concepts.jsonld      ~400 B  (8 level descriptors × ~50 B)
manifest.json + crosswalk ~300 B
total                    ~2,200 B  -> ~550 tokens
```

Conservative round-up: `bundle_token_cost = 1800` (covers multilingual `prefLabel` for `en` + `fr`).

### 3.2 `x.klickd/student` derivation

Manifest scope (approximate, mirrors `student.md` §5):

```text
pack                       ~30 B
pack_version               ~20 B
spec_ref                   ~70 B
publisher                  ~80 B
frameworks[]               ~700 B  (4 entries: esco, digcomp, lifecomp, eqf; optionally cefr at +200 B)
base_transversal_core      ~900 B
identity                   ~150 B
level                      ~180 B
curriculum_refs[]          ~200 B  (1 entry; +200 B per additional entry)
subjects[]                 ~300 B  (~3 subjects × ~100 B)
competencies[]             ~600 B  (6–10 anchored IRIs)
mastery[]                  ~400 B  (~3 entries × ~130 B)
preferences                ~200 B
accessibility              ~100 B
exam_targets[]             ~200 B  (1 entry)
history[]                  ~400 B  (~10 entries × ~40 B, bounded)
gates                      ~150 B
human_authority            ~120 B
memory_scope               ~50 B
evidence_policy            ~110 B
source_policy              ~110 B
router_cost                ~120 B
forbidden_fields           ~180 B
total                      ~3,400 B
tokens_estimate            ~850    (3400 // 4)
```

`bundle_token_cost` (when the SKOS bundle is loaded):

```text
base subset (as above)     ~2,200 B
esco/education subset      ~600 B  (extra ESCO education concepts)
eqf/concepts.jsonld        already in base
cefr/concepts.jsonld       ~700 B  (6 levels × ~100 B; conditional on language_proficiency[] being declared)
total                      ~3,500 B  -> ~875 tokens
```

Conservative round-up: `bundle_token_cost = 2400`.

## 4. Worked example — RFC-003 substitution

A reviewer can substitute these into `chimera_v41_extrapolation()` (see `benchmarks/context_cost/runner.py`) to bracket cost:

```python
from benchmarks.context_cost.runner import chimera_v41_extrapolation

# Baseline .klickd token estimate from RFC-003 dry-run (illustrative).
KLICKD_BASE = 4200  # heuristic-token total for the v4.0 base context.

# Substitute pack-specific estimates from this file. The remaining default
# packs keep their 850 placeholder until they ship their own router_cost rows.
custom_costs = {
    "core.Kai":      850,
    "core.KaiLegal": 850,
    "core.MediaKai": 850,
    "core.Code":     850,
    "core.Edu":      850,         # x.klickd/student equivalent in current runner naming
    "core.Health":   850,
    "core.Ops":      850,
}
# Override the entries we have published rows for:
# - x.klickd/user maps to a (yet unnamed) "core.User" base; placeholder name
#   reserved until the runner is updated to use the v4.1-native pack ids.
# - x.klickd/student maps to "core.Edu" in the current runner.
custom_costs["core.Edu"] = 850   # heuristic estimate above for x.klickd/student

extr = chimera_v41_extrapolation(KLICKD_BASE, pack_token_costs=custom_costs)
# extr["base_plus_seven"]["total_tokens"]   -> baseline + sum(all 7 pack costs)
# extr["router_selected"]["total_tokens"]   -> baseline + only routed packs
```

The substitution does NOT change the runner; it only feeds the published estimates into the existing `pack_token_costs` argument. **No release, no rerun, no committed CSV.**

### 4.1 Runner pack-id naming (open, narrow)

`benchmarks/context_cost/runner.py` currently uses `DEFAULT_CHIMERA_PACKS` with `core.<X>` names that pre-date RFC-009's `x.klickd/<name>` taxonomy. A future PR may rename `DEFAULT_CHIMERA_PACKS` to mirror RFC-009 P0/P1 ids (`x.klickd/user`, `x.klickd/student`, …) for naming consistency. That rename is **not** in scope here:

- It would touch a code path (`runner.py`), not just docs.
- The functional shape of `chimera_v41_extrapolation()` is unchanged either way (substitute via `pack_token_costs={...}` works under both naming schemes).

This file uses `core.Edu` as the substitution key for `x.klickd/student` only as a temporary bridge. When the runner is renamed, this row updates with it.

## 5. What this satisfies (RFC-009 §8.7)

This file makes the **Router-priceable** criterion satisfiable **at spec level** for `x.klickd/user` and `x.klickd/student`:

- ✅ Deterministic estimate (heuristic, reproducible offline).
- ✅ `baseline` named (`base_plus_one`).
- ✅ `source_row` named (this file, anchor `#3-1` / `#3-2`).
- ✅ Compatible with `chimera_v41_extrapolation(pack_token_costs=...)`.
- ✅ Audit-friendly: the derivation table is byte-budgeted by section.

What is **still TODO** (substance, not spec):

- Real bundle bytes (currently the bundle is shape-only — see [`../frameworks/README.md`](../frameworks/README.md)).
- Recomputation once a real `chimera_v41_extrapolation.json` row is published under `benchmarks/context_cost/results/`.
- Per-pack rows for the other four P0 packs (`coding`, `research`, `security`, `legal`) — those are explicit scaffolds for follow-up PRs.

## 6. See also

- [RFC-009 §5.3, §8.7, §8.1](../../RFC-009-chimera-v4.1.md) — seven-pack ceiling, router-priceable criterion, `router_cost` field in the v4.1-native shape table.
- [`../schema-fragments/README.md`](../schema-fragments/README.md) §13 — `router_cost` schema-intent fragment.
- [`../frameworks/README.md`](../frameworks/README.md) — framework registry + offline bundle shape (drives `bundle_token_cost`).
- [`../../../../benchmarks/context_cost/README.md`](../../../../benchmarks/context_cost/README.md) §"Chimera.klickd v4.1 — forward-looking extrapolation".
- [`../../../../benchmarks/context_cost/runner.py`](../../../../benchmarks/context_cost/runner.py) — canonical `chimera_v41_extrapolation()` function.
- [`./student.md`](./student.md) §6 — validation table for `x.klickd/student`.
