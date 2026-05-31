# Repository structure

This document describes the canonical layout of the `klickdskill` repository, the
paths that are **load-bearing** (referenced by tests, CI, release tooling, schema
`$id` URLs, or public documentation), and the paths that are **intentionally
preserved** even though they might look redundant. It is descriptive of the
current state on the v4.1 line and is intended to make future cleanup safe rather
than to prescribe a reorganisation.

> **Stability note.** The v4.1 line is published: `@klickd/core@4.1.0` (npm),
> `klickd==4.1.0` (PyPI), and the x.klickd v4.1 evidence pack
> ([DOI 10.5281/zenodo.20459934](https://doi.org/10.5281/zenodo.20459934)).
> Reproducibility of that evidence pack depends on stable paths and identifiers,
> so structural changes are deliberately conservative. Anything that would change
> a path referenced by a test vector, a CI workflow, a release script, or a schema
> `$id` is treated as a breaking change and is **not** performed as cleanup.

## Top-level layout

| Path | Purpose |
|------|---------|
| `SPEC.md` | Normative specification (current, v4.0.0 GA surface). |
| `SKILL.md` | Current skill document. |
| `CHANGELOG.md`, `ROADMAP.md`, `SECURITY.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `LICENSE` | Standard project governance/docs. |
| `SCHEMA_INDEX.md` | Index of every JSON Schema and which validator consumes it. Start here for schema questions. |
| `CITATION.cff`, `.zenodo.json`, `paper.md`, `paper.bib` | Citation / archival / JOSS-paper metadata. |
| `schema/` | **Unified** single-file JSON Schemas (see below). |
| `schemas/` | **Split** envelope + payload JSON Schemas (see below). |
| `scripts/` | Generators, validators, and release/bundle tooling. |
| `tests/` | Cross-implementation test vectors (`vectors_*.json`, `negative_vectors_*.json`) and `pytest` suites. |
| `packages/` | Reference SDKs (see [Preserved package paths](#preserved-package-paths)). |
| `examples/` | Sample `.klickd` files and integration snippets per spec version. |
| `registry/` | Competency / domain / personality registries. |
| `benchmarks/` | Benchmark inputs, raw runs, and consolidated reports. |
| `curriculum/` | Per-jurisdiction curriculum material. |
| `integrations/` | Third-party integration adapters. |
| `docs/` | All long-form documentation, RFCs, release notes, audits, specs (see below). |

### Root scripts (public entry points — intentionally at root)

The following live at the repository root **on purpose** because they are public,
documented entry points and are invoked by name:

| File | Why it stays at root |
|------|----------------------|
| `verify_vectors.py`, `verify_vectors.mjs` | Invoked directly by `.github/workflows/test-vectors.yml` and documented in `CONTRIBUTING.md` as `python verify_vectors.py` / `node verify_vectors.mjs`. |
| `load_klickd.py`, `save_klickd.py` | Reference encoder/decoder referenced from `SKILL.md`. |

Moving these would require root compatibility wrappers and would break CI and the
documented contributor workflow, so they are left in place.

### Root historical snapshots (intentionally retained)

`SPEC_v30.md`, `SKILL_v25.md`, `SKILL_v30.md`, and `klickd_v330_spec.pdf` are
historical snapshots superseded by `SPEC.md` / `SKILL.md`. They are linked from
`README.md`, `CONTRIBUTING.md`, the issue templates, the test-vectors workflow,
and several RFCs (e.g. RFC-004). They are kept at root to preserve those links.
See [Deferred / future migration](#deferred--future-migration).

## The two schema directories are deliberately distinct

`schema/` and `schemas/` are **not** duplicates and are **not** to be consolidated:

- **`schema/` — unified schemas.** Each file validates a complete `.klickd`
  document (envelope + inline-or-encrypted payload) for one spec version
  (`klickd-v1.json`, `klickd-v2.json`, `klickd-v3.4.schema.json`,
  `klickd-v4-preview.schema.json`, `klickd-v4.schema.json`). Use these when a
  single-schema validation is sufficient (CI tooling, third-party integrations,
  registries).
- **`schemas/` — split schemas.** Envelope and payload validated as two
  independent steps (`klickd-envelope-v3.schema.json`,
  `klickd-payload-v3.schema.json`, `klickd-payload-v4-preview.schema.json`,
  `klickd-payload-v4.schema.json`). Use these for secure decoders that validate
  the envelope *before* decryption and the payload *after*.

Both directories carry a `README.md` that cross-references the other, and the
distinction is documented normatively in `SCHEMA_INDEX.md`. The split is
load-bearing:

- Test vectors reference unified paths, e.g. `tests/vectors_v40_ga.json` and
  `tests/negative_vectors_v40_ga.json` point at `schema/klickd-v4.schema.json`.
- Release tooling enumerates both, e.g.
  `scripts/generate_x_klickd_sha256sums.sh` and
  `scripts/generate_v4_1_zenodo_bundle.sh`.
- Schema `$id` URLs and ~40 documentation links resolve against these exact
  paths.

Consolidating `schema/` into `schemas/` (or vice versa) would break all of the
above, so it is **not** done.

## Preserved package paths

The reference SDKs keep their published locations exactly:

| Path | Package |
|------|---------|
| `packages/@klickd/core` | npm `@klickd/core` (`4.1.0`). |
| `packages/pypi/klickd` | PyPI `klickd` (`4.1.0`). |

These directory names are **never** renamed or moved. They mirror the published
package identifiers, and the v4.1 evidence-pack tooling and SHA256 manifests
reference them by path.

## `docs/` organisation

| Path | Contents |
|------|----------|
| `docs/spec/` | Migration guide, deprecation policy, and supplementary spec docs (e.g. `MIGRATION_V3_TO_V4.md`, `DEPRECATION_POLICY_V4.md`). |
| `docs/rfcs/` | RFCs. `docs/rfcs/chimera/` holds the internal candidate-track RFC scaffolding. |
| `docs/releases/` | Per-release notes and Zenodo prep checklists. |
| `docs/audits/` | Pre-release and security audits. |
| `docs/roadmap/` | Roadmap detail (e.g. `ROAD-TO-V4-GA.md`). |
| `docs/ux/`, `docs/use-cases/`, `docs/demos/`, `docs/checklists/`, `docs/community/`, `docs/integrations/`, `docs/public/` | Supporting material grouped by concern. |
| `docs/chimera/` | Internal v4.1 candidate-track working documents. |

### Codename boundary

`Chimera` is the **internal** codename for the v4.1 candidate track. It is
confined to `docs/chimera/`, `docs/rfcs/chimera/`, and internal scripts/tests.
Public surfaces — `README.md`, `SPEC.md`, `SKILL.md`, and everything under
`packages/` — use **`x.klickd`** only. New public-facing content must not
introduce the codename.

### Paper / specs note

The JOSS paper sources (`paper.md`, `paper.bib`) live at the repository root,
which is the location JOSS tooling expects; they are intentionally not moved
under `docs/`. Long-form specification material lives under `docs/spec/`, with the
normative specification itself at the root as `SPEC.md`.

## Deferred / future migration

The following are recognised as candidates for a future, coordinated change but
are **deliberately not performed** on the v4.1 line because they would touch
load-bearing paths or public links:

- Relocating root historical snapshots (`SPEC_v30.md`, `SKILL_v25.md`,
  `SKILL_v30.md`, `klickd_v330_spec.pdf`) under an `archive/` or `docs/history/`
  tree. This was raised in `docs/audits/V4_PRE_RELEASE_AUDIT.md` and remains
  deferred until the dependent links (README, CONTRIBUTING, issue templates, CI,
  RFCs) can be updated in the same change.
- Moving root reference scripts under `scripts/` with root compatibility
  wrappers. Deferred because it would change the documented CI and contributor
  entry points.
- Any consolidation of `schema/` and `schemas/`. Out of scope by design — the two
  directories serve different validation models (see above).

Each of these should be done as its own reviewed change that updates every
reference atomically, not as opportunistic cleanup.
