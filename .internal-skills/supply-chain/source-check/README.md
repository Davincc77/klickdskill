# Supply-chain stage: source freshness + license check

Internal operator note for `scripts/check_supply_chain_sources.py`. This stage
covers pipeline steps **11 (license check)** and **12 (source freshness)** for
the inputs that feed a skill / candidate build. It is an internal triage tool.

**It is not legal advice and makes no compliance claim.** It classifies sources
into review buckets so a human/agent can decide; it never asserts that a source
*is* legally compatible.

## Usage

```bash
python scripts/check_supply_chain_sources.py \
  --manifest path/to/source_manifest.json \
  --out .internal-skills/supply-chain/source-check/report.json
```

Flags:

- `--manifest` (required) — source manifest JSON (`xklickd.source_manifest.v0.1`).
- `--out` — write the deterministic JSON report to this path.
- `--quiet` — suppress stdout (report still written to `--out`).
- `--eval-date YYYY-MM-DD` — date used for age math. Set this in tests/CI for
  reproducible freshness classification; defaults to today (UTC).
- `--min-metadata-fields N` — minimum descriptive fields per source (default 3).

Stdlib-only, offline, no network I/O.

## Manifest shape (`xklickd.source_manifest.v0.1`)

```json
{
  "schema_version": "xklickd.source_manifest.v0.1",
  "sources": [
    {
      "id": "source-001",
      "title": "Example",
      "url": "https://example.org/spec",
      "retrieved_at": "2026-06-02",
      "published_at": "2026-01-01",
      "license": "CC-BY-4.0",
      "usage": "reference",
      "category": "default",
      "local_path": "data/file.txt",
      "hash": "sha256:...",
      "superseded": false,
      "url_exempt": false
    }
  ]
}
```

Required per source: `id`, `title`, `license`, `usage`. Optional: `url`,
`published_at`, `retrieved_at`, `category`, `local_path` + `hash`, `superseded`,
`url_exempt`.

## Classification

License buckets (normalized, alias-tolerant):

- **allowed**: MIT, Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC0-1.0, CC-BY-4.0
- **review**: CC-BY-SA-4.0, MPL-2.0, GPL-2.0, GPL-3.0, AGPL-3.0, custom, unknown
- **blocked**: proprietary-no-permission, no-redistribution, all-rights-reserved,
  non-commercial-only (for commercial/premium reuse)
- **unknown**: anything unrecognized → review

Freshness buckets (age budget by `category`, parameterizable in the script):

- default review budget: 365 days
- security / regulatory: 90 days
- academic / theory: 1095 days (drops to 365 when `superseded: true`)

Within budget → `fresh`; over budget but ≤ 2× → `review`; beyond → `stale`;
no `published_at` → `missing_date`.

## Blocking conditions (exit 1)

- a blocked license;
- a non-commercial license used for a commercial/premium `usage`;
- missing `url` (without `url_exempt`) or non-https `http://` url (without `url_exempt`);
- `missing_date` or `stale` for a `security`/`regulatory` source (critical);
- a referenced `local_path` that is missing or whose `hash` does not match;
- insufficient metadata (fewer than `--min-metadata-fields` descriptive fields);
- duplicate source `id`.

Non-blocking → `review` for review/unknown licenses, future-dated or
past-budget non-critical sources, or a declared hash with no `local_path`.

Exit codes: `0` clean, `1` one or more blocking findings, `2` usage / I/O / bad
schema.

## Report fields

`schema_version`, `manifest_path`, `manifest_hash`, `deterministic_report_id`,
`summary` (counts), `source_findings`, `blocked_findings`, `review_findings`,
`recommendations`, `non_deterministic_zone`.

## Determinism

`deterministic_report_id = sha256` over the manifest hash plus the sorted,
normalized per-source verdicts and findings. Identical `--manifest` and
`--eval-date` always produce the same id, independent of clock, host, or run
order. The wall-clock `evaluated_at` value and raw `age_days` are reported but
recorded under `non_deterministic_zone` / per-source and are excluded from the
id. A different `--eval-date` that flips a freshness class is a genuinely
different result and yields a different id by design.

## Anti-mirage scope

- The check reports only what it computes from the manifest. It does not
  synthesize a "pass" for sources it cannot verify.
- A source with no clear origin (no url, no date, thin metadata) is flagged or
  blocked, never silently accepted.
- No web crawling: freshness uses declared dates, not live fetches, so the
  result is deterministic and testable.

## Known limits

- Triage only; **no legal advice, no compliance determination.**
- License matching is identifier/alias based, not full SPDX-expression parsing
  (`MIT OR Apache-2.0` is treated as unknown → review).
- Freshness uses declared `published_at`; it does not detect that a live source
  silently changed. The `hash` + `local_path` check covers only local files.
- Age budgets are heuristics for internal review, not a policy guarantee.

## Tests

`tests/test_supply_chain_sources.py` with fixtures under
`tests/fixtures/supply_chain_sources/`. Run:

```bash
python -m pytest tests/test_supply_chain_sources.py -q
```
