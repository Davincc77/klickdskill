# Repository structure

This document describes the canonical layout of the `klickdskill` repository, the
paths that are **load-bearing** (referenced by tests, CI, release tooling, schema
`$id` URLs, or public documentation), and the paths that are **intentionally
preserved** even though they might look redundant. A compact, reader-facing summary
of this layout is surfaced in the
[Repository structure](../README.md#repository-structure) section of `README.md`.

The root was cleaned in the restructuring PR: the reference scripts now live under
`scripts/` and the paper/PDF sources moved under `docs/`. Backward compatibility is
preserved by **thin root wrappers** (for the scripts) so that published v4.1
reproducibility — the documented CLI entry points and `import` paths — is not
broken. See [Root compatibility wrappers](#root-compatibility-wrappers).

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
| `CITATION.cff`, `.zenodo.json` | Citation / archival metadata. The JOSS paper sources moved to `docs/paper/` (see below). |
| `schema/` | **Unified** single-file JSON Schemas (see below). |
| `schemas/` | **Split** envelope + payload JSON Schemas (see below). |
| `scripts/` | Reference encoder/decoder (`load_klickd.py`, `save_klickd.py`), cross-impl verifiers (`verify_vectors.py`, `verify_vectors.mjs`), generators, validators, and release/bundle tooling. **Canonical home for the reference scripts.** |
| `tests/` | Cross-implementation test vectors (`vectors_*.json`, `negative_vectors_*.json`) and `pytest` suites. |
| `packages/` | Reference SDKs (see [Preserved package paths](#preserved-package-paths)). |
| `examples/` | Sample `.klickd` files and integration snippets per spec version. |
| `registry/` | Competency / domain / personality registries. |
| `benchmarks/` | Benchmark inputs, raw runs, and consolidated reports. |
| `curriculum/` | Per-jurisdiction curriculum material. |
| `integrations/` | Third-party integration adapters. |
| `tools/` | **Reserved** for optional developer/maintainer utilities not part of the release pipeline. Currently a documented placeholder (`tools/README.md` only); load-bearing tooling stays in `scripts/`. |
| `docs/` | All long-form documentation, RFCs, release notes, audits, specs (see below). |

### Root compatibility wrappers

The reference scripts were moved into `scripts/` (their canonical home). To keep
the documented public entry points working unchanged, **thin wrappers of the same
name remain at the repository root**:

| Root file | Delegates to | Why the wrapper exists |
|-----------|--------------|------------------------|
| `verify_vectors.py` | `scripts/verify_vectors.py` (via `runpy`) | `python verify_vectors.py` is invoked by `.github/workflows/test-vectors.yml`, `package.json` (`test:py`, `test:all`), `CONTRIBUTING.md`, and the v4.1 evidence-pack bundle tooling. |
| `verify_vectors.mjs` | `scripts/verify_vectors.mjs` (via `import`) | `node verify_vectors.mjs` is invoked by `package.json` (`test`, `test:all`), the test-vectors workflow, and `CONTRIBUTING.md`. |
| `load_klickd.py` | `scripts/load_klickd.py` (re-exports all public names) | Keeps `import load_klickd` working for code that puts the repo root on `PYTHONPATH` (e.g. `demo/demo_soul_handoff.py`). |
| `save_klickd.py` | `scripts/save_klickd.py` (re-exports all public names) | Keeps `import save_klickd` working from the repo root. |

The wrappers contain **no logic** beyond delegation, so there is a single source of
truth (the `scripts/` copy). The canonical implementations resolve repository-root
paths (`tests/`, `schema/`, `schemas/`) as `Path(__file__).parent.parent`, so they
run correctly both directly (`python scripts/verify_vectors.py`) and through the
wrapper. New code should import/invoke the `scripts/` paths directly; the root
wrappers exist for backward compatibility with published references.

### Root historical snapshots (intentionally retained)

`SPEC_v30.md`, `SKILL_v25.md`, and `SKILL_v30.md` are historical Markdown snapshots
superseded by `SPEC.md` / `SKILL.md`. They are linked from `README.md`,
`CONTRIBUTING.md`, the issue templates, the test-vectors workflow, and several RFCs
(e.g. RFC-004). They are kept at root to preserve those links.

The historical PDF snapshot moved to `docs/specs/klickd_v330_spec.pdf` (see
[Paper / specs note](#paper--specs-note)); its `README.md` link was updated in the
same change.

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

The JOSS paper sources moved to `docs/paper/` (`docs/paper/paper.md`,
`docs/paper/paper.bib`). There is no live JOSS submission yet (it is an open item
on `ROADMAP.md`), so no JOSS tooling is broken by the move. **When the paper is
submitted to JOSS,** note that JOSS resolves the paper at the repository root or in
a top-level `paper/` directory — if its tooling cannot be pointed at
`docs/paper/paper.md` (e.g. via the `paper-path` input on the JOSS GitHub Action),
move or symlink the sources to a top-level `paper/` at submission time.

The historical spec PDF lives at `docs/specs/klickd_v330_spec.pdf`. Long-form
specification material lives under `docs/spec/`, with the normative specification
itself at the root as `SPEC.md`.

## Completed in the restructuring PR

- **Reference scripts moved under `scripts/`** with root compatibility wrappers
  (see [Root compatibility wrappers](#root-compatibility-wrappers)). All CI,
  `package.json`, and `import` entry points were preserved.
- **Paper sources moved to `docs/paper/`** and the **historical PDF moved to
  `docs/specs/`**, with dependent links (`README.md`, `ROADMAP.md`) updated.

## Deferred / future migration

The following remain **deliberately not performed** because they would touch
load-bearing paths or public links:

- Relocating the root historical Markdown snapshots (`SPEC_v30.md`,
  `SKILL_v25.md`, `SKILL_v30.md`) under an `archive/` or `docs/history/` tree.
  Raised in `docs/audits/V4_PRE_RELEASE_AUDIT.md`; deferred until the dependent
  links (README, CONTRIBUTING, issue templates, CI, RFCs) can be updated in the
  same change.
- Any consolidation of `schema/` and `schemas/`. Out of scope by design — the two
  directories serve different validation models, and their `$id` URLs plus test
  vectors (`tests/vectors_v40_ga.json` → `schema/klickd-v4.schema.json`) resolve
  against these exact paths (see
  [the two schema directories](#the-two-schema-directories-are-deliberately-distinct)).

Each of these should be done as its own reviewed change that updates every
reference atomically, not as opportunistic cleanup.
