# `docs/rfcs/chimera/tests/` — local checks for the RFC-009 Draft scaffold

> **Status:** Draft · NON-NORMATIVE · companion to [RFC-009](../../RFC-009-chimera-v4.1.md).
> **Triggers no release.** No tag, no `latest` on npm/PyPI, no Zenodo DOI, no IANA action.

This directory ships the **offline checker** that exercises the Draft scaffold under [`../`](../) (the SKOS bundles, the schema fragment, the round-trip fixture). It is deliberately scoped to the RFC-009 Draft and lives alongside the RFC docs rather than under `tests/` (the latter is the runtime SDK test suite; this is a docs-side validator).

## 1. What it checks

The script [`check_chimera.py`](./check_chimera.py) runs eight deterministic checks:

| # | Check | Maps to |
|---|---|---|
| 1 | JSON validity of the schema fragment, fixture, and SKOS bundles. | RFC-009 §8.6 (offline-resolvable basics). |
| 2 | Strict Draft 2020-12 schema validation of [`../packs/fixtures/x.klickd.student.example.json`](../packs/fixtures/x.klickd.student.example.json). | RFC-009 §8.1 (v4.1-native shape). |
| 3 | Negative fixtures (carrier-vs-skill violation, legacy persona key, homegrown competency, authority weakening, PII, missing `forbidden_fields` literal) MUST fail validation. | RFC-009 §5.0, §5.1, §5.1.1, §8.4, §8.8, §8.9, §8.10. |
| 4 | Every `competency_ref` / `framework_ref` / `subject_ref` in the fixture resolves against [`../frameworks/base_transversal_core.bundle.json`](../frameworks/base_transversal_core.bundle.json) and [`../frameworks/x.klickd.student.bundle.json`](../frameworks/x.klickd.student.bundle.json). | RFC-009 §5.7, §8.6. |
| 5 | SHA-256 hashes in [`../frameworks/bundle-manifest.json`](../frameworks/bundle-manifest.json) match disk bytes. | Bundle integrity. |
| 6 | No PII keys (`email`, `phone`, `national_id`, `address`, …) anywhere in the fixture. | RFC-009 §8.4. |
| 7 | No persona-as-pack banned wording in the docs touched by this PR (with per-file ceilings for legitimate refutations). | RFC-009 §0.1.2. |
| 8 | Every relative markdown link in the touched docs resolves to an existing file. | Docs hygiene. |

## 2. How to run

```bash
# Direct invocation (verbose, one line per check):
python3 docs/rfcs/chimera/tests/check_chimera.py

# Via pytest (exposes one test per check, integrates with CI):
pytest tests/test_rfc009_chimera_scaffold.py -v
```

Both forms are offline (no network calls, no provider tokens, no paid resources). Both exit non-zero on any failure.

## 3. When to re-run

- After editing any file under [`../frameworks/`](../frameworks/), [`../schema-fragments/`](../schema-fragments/), [`../packs/`](../packs/), or [`../README.md`](../README.md).
- Before requesting review on RFC-009-related PRs.
- After bumping the bundle byte-content: re-run, then update [`../frameworks/bundle-manifest.json`](../frameworks/bundle-manifest.json) with the new hashes printed in the failure message (or use the regenerate command documented inside the manifest file).

## 4. Non-actions

- This checker does NOT modify any file under `schemas/`, `packages/`, `examples/`, or `tests/vectors_*.json`.
- It does NOT run the SDK test suite (`tests/test_post_v4_demos.py` already covers that).
- It does NOT trigger a release, tag, npm/PyPI publish, Zenodo DOI, or IANA action.
- It does NOT call any external API; everything is read from disk.

## 5. See also

- [`../../RFC-009-chimera-v4.1.md`](../../RFC-009-chimera-v4.1.md) — the RFC itself.
- [`../packs/fixtures/README.md`](../packs/fixtures/README.md) — the round-trip fixture, validation instructions, and negative-fixture catalogue.
- [`../schema-fragments/x.klickd.student.schema.json`](../schema-fragments/x.klickd.student.schema.json) — strict Draft 2020-12 schema fragment.
- [`../frameworks/bundle-manifest.json`](../frameworks/bundle-manifest.json) — bundle integrity manifest.
