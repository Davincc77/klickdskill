# `docs/rfcs/chimera/packs/fixtures/` — round-trip fixtures for Chimera packs

> **Status:** Draft · NON-NORMATIVE · companion to [RFC-009](../../../RFC-009-chimera-v4.1.md) and [`../student.md`](../student.md).
> **Triggers no release.** No tag, no `latest` on npm/PyPI, no Zenodo DOI, no IANA action, no schema change to `schemas/`.

This directory ships **deterministic JSON fixtures** for the v4.1 Chimera packs introduced in [RFC-009](../../../RFC-009-chimera-v4.1.md). The fixtures exist so that:

1. Reviewers can run a strict-schema check against the schema fragments under [`../../schema-fragments/`](../../schema-fragments/) without inventing data.
2. The carrier-vs-skill rule (RFC-009 §5.1.1) and the no-legacy-adapter rule (RFC-009 §5.0) are demonstrably enforceable on real bytes.
3. A future v4.1-vs-v4.0 round-trip test has a known good starting point.

The fixtures are **not** persona files. They MUST NOT be served under `examples/v4/personas/` or under any future `/klickdskill` catalog surface (see [RFC-009 §7](../../../RFC-009-chimera-v4.1.md) and [`../README.md`](../README.md)).

## 1. Fixtures shipped here

| File | Pack | Schema (strict Draft 2020-12) | Offline SKOS bundle | Notes |
|---|---|---|---|---|
| `x.klickd.student.example.json` | `x.klickd/student` | [`../../schema-fragments/x.klickd.student.schema.json`](../../schema-fragments/x.klickd.student.schema.json) | [`../../frameworks/base_transversal_core.bundle.json`](../../frameworks/base_transversal_core.bundle.json) + [`../../frameworks/x.klickd.student.bundle.json`](../../frameworks/x.klickd.student.bundle.json) | First concrete P0 pack instance. Carries learner state only; no host-side teacher method. |

Every `competency_ref`, `framework_ref`, `subject_ref`, and CEFR `scheme_ref` in `x.klickd.student.example.json` resolves to an `@id` declared in one of the two SKOS bundles above. No external network call is required to read the fixture; this is what RFC-009 §8.6 calls "offline-resolvable".

## 2. How to validate the fixture (offline, no provider calls)

### 2.1 Python (`jsonschema`)

```bash
python3 - <<'PY'
import json
from jsonschema import Draft202012Validator

schema = json.load(open("docs/rfcs/chimera/schema-fragments/x.klickd.student.schema.json"))
data   = json.load(open("docs/rfcs/chimera/packs/fixtures/x.klickd.student.example.json"))

# 1. schema is itself a valid Draft 2020-12 document
Draft202012Validator.check_schema(schema)

# 2. data validates strictly against the schema
errors = sorted(Draft202012Validator(schema).iter_errors(data), key=lambda e: e.absolute_path)
assert not errors, [(list(e.absolute_path), e.message) for e in errors]

print("OK — fixture validates against schema; no network calls were made.")
PY
```

### 2.2 Node.js (`ajv` 2020 build)

```bash
node - <<'JS'
const Ajv = require("ajv/dist/2020");
const fs  = require("fs");
const ajv = new Ajv({ allErrors: true, strict: false });
const schema = JSON.parse(fs.readFileSync("docs/rfcs/chimera/schema-fragments/x.klickd.student.schema.json","utf8"));
const data   = JSON.parse(fs.readFileSync("docs/rfcs/chimera/packs/fixtures/x.klickd.student.example.json","utf8"));
const validate = ajv.compile(schema);
const ok = validate(data);
if (!ok) { console.error(validate.errors); process.exit(1); }
console.log("OK — fixture validates against schema; no network calls were made.");
JS
```

### 2.3 Combined check (recommended for reviewers)

Run all four checks at once:

```bash
python3 docs/rfcs/chimera/tests/check_chimera.py
```

That script performs:

1. JSON validity of every fixture under this directory.
2. Strict Draft 2020-12 schema validation of `x.klickd.student.example.json`.
3. Negative checks: a corrupted copy with `pedagogy`, `mastered_topics`, etc. injected MUST fail; the legitimate fixture MUST pass.
4. SKOS bundle round-trip: every `competency_ref` / `framework_ref` / CEFR `scheme_ref` used in the fixture resolves against the bundle's `@graph` entries.
5. SHA-256 bundle integrity matches [`../../frameworks/bundle-manifest.json`](../../frameworks/bundle-manifest.json).
6. No PII keys present in the fixture (`email`, `phone`, `national_id`, `address`, `birthdate`, etc.).
7. No banned persona-as-pack wording in the docs touched by this PR.

## 3. Round-trip vector (manual cross-check)

Until [`tests/roundtrip_v30.json`](../../../../../tests/roundtrip_v30.json) is extended to cover v4.1 packs, the round-trip property a v4.0-only reader MUST satisfy is documented here, and verified manually:

| Step | Action | Expected outcome |
|---|---|---|
| R1 | Embed `x.klickd.student.example.json` as an additional top-level block on a v4.0 GA payload. | The combined payload still validates against [`schemas/klickd-payload-v4.schema.json`](../../../../../schemas/klickd-payload-v4.schema.json) because that schema's top-level `additionalProperties: true` preserves unknown blocks verbatim (SPEC §33.7). |
| R2 | Parse the combined payload with the existing v4.0 SDK (which has no knowledge of `x.klickd/*`). | Parse succeeds; the unknown `x.klickd/student` block round-trips byte-stable on re-serialisation. |
| R3 | Re-parse with a v4.1-aware reader. | The reader recognises the pack block and validates it against [`../../schema-fragments/x.klickd.student.schema.json`](../../schema-fragments/x.klickd.student.schema.json). |
| R4 | Compare R1's input bytes with R2's output bytes. | Byte-identical (deterministic round-trip; RFC-009 §8.5). |

The unit-test wiring for R1–R4 lands with the schema-promotion PR (see [RFC-009 §10, §12](../../../RFC-009-chimera-v4.1.md)) and is intentionally out of scope for the Draft. `check_chimera.py` exercises R3 today.

## 4. Negative fixtures — what MUST fail validation

Five categories of bad input that the schema rejects. Each is exercised by [`../../tests/check_chimera.py`](../../tests/check_chimera.py):

| Category | Concrete example | Why rejected | Schema mechanism |
|---|---|---|---|
| **Carrier-vs-skill violation (RFC-009 §5.1.1)** | Adding a top-level `pedagogy: { steps: [...] }` block. | Pedagogy is a `host_skill`, not a `competency_pack`. | `additionalProperties: false` at top-level (unknown key); also caught by `forbidden_fields` literal check. |
| **Legacy persona key (RFC-009 §5.0)** | Adding `knowledge.mastered: ["derivatives"]` or `mastered_topics: ["calculus"]`. | Persona-shaped legacy field; v4.1 packs do not accept these. | `additionalProperties: false`; also caught by `forbidden_fields` literal check. |
| **Homegrown competency** | A `competency_ref` like `klickd:custom:foo` or `mastered:derivatives`. | No declared framework, no resolvable IRI. | `competency_ref` $def `pattern` restricts the scheme prefix to the registered framework list. |
| **Human-authority weakening** | Setting `gates.verification_gates_default.raise_only: false` or `human_authority.agent_role: "executor"`. | A pack default MUST NOT lower v4.0 gates; an agent is ALWAYS advisory. | `const: true` on `raise_only`; `const: "advisory"` on `agent_role`. |
| **PII in the pack** | Adding `identity.email`, `identity.phone`, `identity.national_id`. | The pack is publisher-owned, not user-owned; PII lives in the v4.0 user file. | `additionalProperties: false` on the `identity` object. |

## 5. Non-actions (scope discipline)

- No `.klickd` file ships under `examples/v4/personas/` for this scaffold. The persona directory stays anchors-only per [RFC-009 §6](../../../RFC-009-chimera-v4.1.md).
- No SDK code is added under `packages/`. The fixture is text only.
- No vector under `tests/vectors_*.json` is changed. The schema fragment and the fixture live under `docs/rfcs/chimera/`.
- No change to `schemas/klickd-payload-v4*.schema.json`. Promotion to `schemas/` requires the RFC to reach `Accepted`.
- No DOI, no IANA action, no tag, no `latest` channel on npm/PyPI.

## 6. See also

- [`../../../RFC-009-chimera-v4.1.md`](../../../RFC-009-chimera-v4.1.md) — full RFC (carrier-vs-skill in §5.1.1, validation in §8, shape table in §8.1).
- [`../student.md`](../student.md) — concrete pack scaffold.
- [`../../schema-fragments/x.klickd.student.schema.json`](../../schema-fragments/x.klickd.student.schema.json) — strict Draft 2020-12 JSON Schema fragment.
- [`../../frameworks/base_transversal_core.bundle.json`](../../frameworks/base_transversal_core.bundle.json) and [`../../frameworks/x.klickd.student.bundle.json`](../../frameworks/x.klickd.student.bundle.json) — physical SKOS/JSON-LD subset bundles.
- [`../../frameworks/bundle-manifest.json`](../../frameworks/bundle-manifest.json) — bundle SHA-256 manifest.
- [`../../tests/check_chimera.py`](../../tests/check_chimera.py) — combined validator script.
