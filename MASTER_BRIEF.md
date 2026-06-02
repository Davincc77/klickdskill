# MASTER_BRIEF — x.klickd internal supply-chain protocol

| | |
|---|---|
| **Status** | **Internal · NON-NORMATIVE · binding on agents working in this repo** |
| **Created** | 2026-06-02 |
| **Scope** | The internal x.klickd skill supply chain (`.internal-skills/`, `scripts/generate_supply_chain_*`, `scripts/check_supply_chain_*`, `docs/internal/`, `docs/supply-chain/`, `docs/rfcs/chimera/`) |

> This file exists so that **future agents do not depend on any external or workspace-local brief that may be missing.** It restates the non-negotiable rules in-repo. If a delegated task references a brief you cannot find, this document is the authoritative fallback. Read it fully before acting.

---

## 0. Why this document exists

Work on the internal supply chain is delegated across many agents. Each delegation must carry complete context; an agent must never guess at intent or rely on a workspace path that may not be present. The companion process spec is [`docs/rfcs/chimera/SUPPLY_CHAIN.md`](docs/rfcs/chimera/SUPPLY_CHAIN.md) (non-normative, describes the pipeline). This brief captures the **rules of engagement** that sit above any individual task.

---

## 1. Anti-mirage rules (non-negotiable)

These rules exist to prevent the appearance of capability that does not exist ("mirage"). Apply them literally.

1. **No loaded-skill claim without proof.** A pack/skill is "loaded" or "used" **only** when `artifact_loaded = true` **and** `sha256_matches_manifest = true`, per [`docs/integrations/skill-loader-protocol.md`](docs/integrations/skill-loader-protocol.md). A catalog entry, a stub, a routing placeholder, a manifest row, or a marketing page is **never** a loaded executable skill. Do not describe one as such.
2. **Read the per-stage label literally.** Each pipeline stage is labelled `tool` (shipped, runnable, tested), `manual` (a human/agent procedure), or `planned` (specified, not built). Never describe a `planned` or `manual` stage as automated or shipped.
3. **No claims beyond evidence.** No "universal standard", no "automatic GDPR / EU AI Act / sectoral compliance", no "benchmark superiority proven", no automation percentage stated as a measured result. The 70–80% automation figure is a **design target**, not a guarantee.
4. **Determinism is claimed only where recorded.** A stage is deterministic only if a determinism record (same `input_hash` → same `output_hash`) backs it. Otherwise say so.
5. **No external action.** No release, no publish (npm / PyPI), no `latest` tag, no git tag, no Zenodo DOI, no IANA action, no external communication (email, Slack, social), no merge to `main`, no PR approval. Integration work opens **draft** PRs only.
6. **Repo isolation.** Do **not** touch `Davincc77/klickd-ai`. This work lives only in `Davincc77/klickdskill`.

---

## 2. Public v4.1 vs internal v4.2 boundary

- The public `.klickd` track is **v4.0.0 GA**; the 42 `x.klickd` artefacts are framed as **v4.1 candidates**. These are the only public version claims.
- v4.2 exists **only as an internal target** (see [`docs/internal/INTERNAL_SKILL_V4_2_MAPPING.md`](docs/internal/INTERNAL_SKILL_V4_2_MAPPING.md)). **Do not claim a public v4.2 release.** "v4.2 in preparation" is the maximum public-facing statement, and it lives only where already written.
- Internal track codenames (e.g. `xklickd_internal_skill_v4_2`, sibling-path codenames) are **internal identifiers only** and MUST NOT propagate to public surfaces: `README.md`, `docs/public/*`, package metadata, or any published artefact.

---

## 3. Current real (tool-backed) stages vs planned stages

See [`.internal-skills/supply-chain/README.md`](.internal-skills/supply-chain/README.md) for the authoritative per-stage table. Summary:

**Real, tool-backed today (shipped + tested):**

- **Audit / determinism** — `scripts/generate_supply_chain_audit.py` (audit-trail index + determinism record).
- **Logical diff** — `scripts/generate_supply_chain_diff.py` (before/after candidate diff with violation classes).
- **Source freshness + license compatibility** — `scripts/check_supply_chain_sources.py`.
- **Threat model** — `scripts/generate_supply_chain_threat_model.py` (deterministic threat-model generator v0.1).

**Planned (specified, not built):**

- Candidate generation (the build *runner*).
- Promotion gate (pass/fail enforcement that blocks promotion).
- Full PII / secrets scanner (beyond the engineering source/license checks).
- Runtime enforcement (in-loop guardrail enforcement at execution time).

---

## 4. Required validations before any integration PR

Run and report exactly (including pre-existing baseline failures):

- New supply-chain tests: `pytest tests/test_supply_chain_audit.py tests/test_supply_chain_diff.py tests/test_supply_chain_sources.py tests/test_supply_chain_threat_model.py`
- Pack verifier: `python scripts/verify_xklickd_skill_packs.py`
- Candidate mapping validator: `python scripts/validate_v4_1_candidate_mapping.py`
- v4 schema validator: `python scripts/validate_v4_schemas.py`
- Public codename / forbidden-claim greps over changed files (see §1, §2).

Report baseline failures **as-is**; do not mask them. Known pre-existing baseline: nested `packages/`, `benchmarks/`, `examples/`, `integrations/` test modules fail collection under root `pytest` due to import-path issues unrelated to the supply chain. Scope to `tests/` for a clean signal.

---

## 5. Next step after integration

The next step is **not** public release. It is: build the **runner candidate generator + promotion gate** (the two highest-leverage `planned` stages), so that candidate packs can be generated and gated end-to-end before any promotion decision.
