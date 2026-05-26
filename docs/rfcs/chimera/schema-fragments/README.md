# `docs/rfcs/chimera/schema-fragments/` — schema-intent fragments

> **Status:** Draft · NON-NORMATIVE · schema **intent** only, not a JSON Schema.
> **Track:** `.klickd v4.1` Chimera (see [RFC-009](../../RFC-009-chimera-v4.1.md)).
> **Triggers no release.** No tag, no `latest` on npm/PyPI, no DOI on Zenodo, no IANA action, no schema change.

This directory pins the **shape** of the top-level blocks of a v4.1 `competency_pack` so reviewers can argue against concrete field-level intent before any normative JSON Schema lands. The fragments are companion to [RFC-009 §8.1](../../RFC-009-chimera-v4.1.md) (the v4.1-native validation table) and to [`../packs/student.md`](../packs/student.md) (the first concrete pack scaffold).

> **These fragments are NOT a JSON Schema.**
>
> They use JSON-Schema-flavoured prose for clarity (`type`, `required`, `enum`) but deliberately omit `$schema`, `$id`, `additionalProperties`, and tooling-level keywords. A strict JSON Schema is out of scope for v4.1 Draft and arrives only if and when the RFC promotes past `Proposed` (see RFC-009 §10, §12).

## 0. Conventions

- Each fragment is **self-contained** and addressable by its `name:` slug.
- `type` values are JSON Schema primitives (`string`, `object`, `array`, `boolean`, `integer`, `null`).
- `required` lists the keys that MUST be present in a v4.1-native pack.
- `forbidden` lists keys that, if present, fail validation (carrier-vs-skill / no-legacy-adapter checks).
- `notes` carry the rationale and the cross-reference into RFC-009 / the framework registry.
- All `*_ref` fields are stable IRIs or registered prefix-shortened references (e.g. `esco:S1.2.3`). Free-text alternatives are explicitly rejected (RFC-009 §5.0).

## 1. `pack_manifest` (top-level fragment)

The pack manifest is the outermost object. Every other fragment below is a nested block under it.

```jsonc
{
  "name": "pack_manifest",
  "type": "object",
  "required": [
    "pack",
    "pack_version",
    "spec_ref",
    "publisher",
    "frameworks",
    "base_transversal_core",
    "competencies",
    "gates",
    "human_authority",
    "memory_scope",
    "evidence_policy",
    "source_policy",
    "router_cost",
    "forbidden_fields"
  ],
  "properties": {
    "pack": {
      "type": "string",
      "pattern": "^x\\.klickd/(user|student|coding|research|security|legal|work|creator|gaming|bridge|mission)$",
      "notes": "MUST equal a P0/P1 id (RFC-009 §3, §4). Free-form names rejected."
    },
    "pack_version": {
      "type": "string",
      "pattern": "^\\d+\\.\\d+\\.\\d+(?:-[0-9A-Za-z\\.-]+)?$",
      "notes": "SemVer; pre-release `-draft` allowed before validation passes. No release artefact implied (RFC-009 §7)."
    },
    "spec_ref": {
      "type": "string",
      "notes": "Path/URL to the canonical scaffold under `docs/rfcs/chimera/packs/<name>.md`."
    },
    "publisher": {
      "type": "object",
      "required": ["name", "ref"],
      "properties": {
        "name": { "type": "string", "notes": "Publisher org/community name. NOT the carrier (RFC-009 §8.4 — no PII)." },
        "ref":  { "type": "string", "notes": "Publisher's canonical URL/IRI." }
      }
    },
    "frameworks":           { "$fragment": "frameworks_array" },
    "base_transversal_core":{ "$fragment": "base_transversal_core" },
    "competencies":         { "$fragment": "competencies_array" },
    "mastery":              { "$fragment": "mastery_array", "notes": "Carrier-state, optional at publisher time, populated at carrier-instantiation time." },
    "levels":               { "$fragment": "levels_array",  "notes": "Required for student/work/coding/research/security/legal per RFC-009 §8.1." },
    "language_proficiency": { "$fragment": "language_proficiency_array", "notes": "Optional; CEFR-anchored." },
    "gates":                { "$fragment": "gates" },
    "human_authority":      { "$fragment": "human_authority" },
    "memory_scope":         { "$fragment": "structured_memory" },
    "evidence_policy":      { "$fragment": "evidence_policy" },
    "source_policy":        { "$fragment": "source_policy" },
    "router_cost":          { "$fragment": "router_cost" },
    "forbidden_fields":     { "$fragment": "forbidden_fields" }
  },
  "forbidden_top_level_keys": [
    "pedagogy", "teaching_method", "socratic_steps",
    "prompt_strategy", "scoring_rubric", "intervention_policy",
    "tone_rules", "system_prompt_overrides",
    "knowledge.mastered", "mastered_topics",
    "knowledge", "skill_application"
  ],
  "notes": [
    "The `forbidden_top_level_keys` list mirrors `forbidden_fields` and enforces RFC-009 §5.0 (no legacy adapter) + §5.1.1 (carrier-vs-skill).",
    "A pack file containing any key in `forbidden_top_level_keys` fails validation immediately."
  ]
}
```

## 2. `frameworks_array`

```jsonc
{
  "name": "frameworks_array",
  "type": "array",
  "minItems": 1,
  "items": {
    "type": "object",
    "required": ["scheme", "version", "iri_prefix", "canonical_url"],
    "properties": {
      "scheme": {
        "type": "string",
        "enum": ["esco", "digcomp", "lifecomp", "eqf", "cefr", "wef", "onet", "nice", "enisa", "cis", "sfia"],
        "notes": "Registered framework id (see `../frameworks/README.md` §1)."
      },
      "version": { "type": "string", "notes": "Publisher-pinned version string (e.g. `v1.1.1`, `2.2`, `2017`)." },
      "iri_prefix": { "type": "string", "notes": "Stable URL/IRI prefix concatenated with concept ids." },
      "canonical_url": { "type": "string", "notes": "Publisher landing page for the version." },
      "distribution_url": { "type": "string", "notes": "URL of the machine-readable artefact actually consumed." },
      "distribution_sha256": { "type": ["string", "null"], "pattern": "^[a-f0-9]{64}$|^TBD-at-bundle-generation$", "notes": "SHA-256 of the artefact at bundle generation. May be the literal `TBD-at-bundle-generation` placeholder pre-bundle." }
    }
  },
  "notes": "See `../frameworks/README.md` for canonical schemes and the per-pack default anchor set."
}
```

## 3. `base_transversal_core`

```jsonc
{
  "name": "base_transversal_core",
  "type": "object",
  "required": ["frameworks", "transversal_refs"],
  "properties": {
    "frameworks": {
      "$fragment": "frameworks_array",
      "notes": "The base layer's own framework anchors (typically ESCO transversal + DigComp + LifeComp + EQF). May be the same array as the top-level `frameworks[]` or a subset."
    },
    "transversal_refs": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "required": ["competency_ref", "scheme", "prefLabel"],
        "properties": {
          "competency_ref": { "type": "string", "notes": "Prefix-shortened IRI, e.g. `esco:S1.0.0`. Prefix MUST match a declared `frameworks[].scheme`." },
          "scheme":         { "type": "string", "notes": "Echoes the prefix for static checks." },
          "prefLabel":      { "type": "string", "notes": "Human-readable label; multilingual variants allowed under SKOS." }
        }
      }
    }
  },
  "forbidden_fields": ["pedagogy", "teaching_method", "tone_rules"],
  "notes": [
    "Mandatory in every `competency_pack` (RFC-009 §5.2).",
    "An empty `transversal_refs` array fails validation criterion §8.1 (frameworks[] non-empty).",
    "Not harvested from a persona's narrative description; declared against frameworks (RFC-009 §5.0)."
  ]
}
```

## 4. `competencies_array`

```jsonc
{
  "name": "competencies_array",
  "type": "array",
  "minItems": 0,
  "items": {
    "type": "object",
    "required": ["competency_ref", "prefLabel", "scheme"],
    "properties": {
      "competency_ref": {
        "type": "string",
        "notes": "Prefix-shortened IRI resolvable against a declared `frameworks[]` entry. Free-text strings rejected (RFC-009 §5.0)."
      },
      "prefLabel": {
        "type": ["string", "array"],
        "notes": "Human-readable label. Either a string (single language) or an array of `{value, language}` objects."
      },
      "scheme": { "type": "string", "notes": "Echoes the prefix for static checks." },
      "acquired_at": { "type": ["string", "null"], "notes": "ISO-8601 date; carrier state, optional at publisher time." }
    }
  },
  "notes": "Pack-side competence anchors. Carrier mastery against these anchors lives in `mastery[]`."
}
```

## 5. `mastery_array`

```jsonc
{
  "name": "mastery_array",
  "type": "array",
  "minItems": 0,
  "items": {
    "type": "object",
    "required": ["competency_ref", "mastery_level", "scale_ref", "evidence_refs", "assessed_at", "assessed_by_ref"],
    "properties": {
      "competency_ref": { "type": "string", "notes": "MUST match a `competencies[].competency_ref`." },
      "mastery_level":  { "type": "integer", "minimum": 0, "maximum": 6, "notes": "Small ordinal scale. Exact range is rubric-defined; the cap of 6 covers DigComp foundation..highly specialised + 1 reserved." },
      "scale_ref": {
        "type": "string",
        "notes": "Stable rubric reference, e.g. `digcomp:2.2/scale`, `eqf:2017/scale`, `bloom:1956/scale`. Free-form rubrics rejected."
      },
      "evidence_refs": {
        "type": "array",
        "items": { "type": "string" },
        "notes": "Pointers (URIs / artefact ids), NEVER inline copies (`evidence_policy.pointer_only`). May be empty when `assessed_by_ref` is `self`."
      },
      "assessed_at": { "type": "string", "notes": "ISO-8601 date." },
      "assessed_by_ref": {
        "type": "string",
        "pattern": "^(teacher|self|peer|agent|external):.*$",
        "notes": "Discriminated reference. Free-text rejected."
      }
    }
  },
  "forbidden_legacy_aliases": ["mastered", "mastered_topics", "knowledge.mastered"],
  "notes": [
    "Persona-shaped `mastered_topics: [...]` rejected at validation (RFC-009 §5.0 + §8.9).",
    "Pointer-only by default; see `evidence_policy.pointer_only`."
  ]
}
```

## 6. `levels_array`

```jsonc
{
  "name": "levels_array",
  "type": "array",
  "minItems": 1,
  "items": {
    "type": "object",
    "required": ["framework_ref", "level_label", "effective_at"],
    "properties": {
      "framework_ref": { "type": "string", "notes": "IRI into a declared `frameworks[]` scheme (typically `eqf` for qualification level)." },
      "level_label":   { "type": "string", "notes": "Value from the cited framework (e.g. `EQF level 4`). Narrative `\"advanced\"` / `\"expert\"` rejected." },
      "effective_at":  { "type": "string", "notes": "ISO-8601 date the level was last assessed/declared." }
    }
  },
  "notes": "Required for student/work/coding/research/security/legal per RFC-009 §8.1."
}
```

## 7. `language_proficiency_array` (CEFR-anchored)

```jsonc
{
  "name": "language_proficiency_array",
  "type": "array",
  "minItems": 0,
  "items": {
    "type": "object",
    "required": ["language_tag", "cefr_level", "scheme_ref"],
    "properties": {
      "language_tag": { "type": "string", "notes": "IETF BCP-47 language tag (e.g. `fr`, `en-GB`)." },
      "cefr_level":   { "type": "string", "enum": ["A1", "A2", "B1", "B2", "C1", "C2"], "notes": "Council of Europe CEFR descriptor." },
      "scheme_ref":   { "type": "string", "notes": "Stable URL to CEFR Companion Volume 2020 (see `../frameworks/README.md` §1)." },
      "skills":       { "type": "object", "notes": "Optional per-skill CEFR sub-levels: `{ \"listening\": \"B2\", \"reading\": \"C1\", ... }`." }
    }
  },
  "notes": "Separate from `levels[]` (which is qualification-level, typically EQF). A learner may be EQF-4 with French C2 and English B2 simultaneously."
}
```

## 8. `gates` (RFC-002 shape)

```jsonc
{
  "name": "gates",
  "type": "object",
  "required": ["verification_gates_default", "human_veto_policy"],
  "properties": {
    "verification_gates_default": {
      "type": "object",
      "required": ["raise_only", "claim_grounding_required"],
      "properties": {
        "raise_only":               { "type": "boolean", "enum": [true], "notes": "MUST be `true` (RFC-009 §5.1, §8.8). A pack default MUST NOT lower a user's v4.0 gate." },
        "claim_grounding_required": { "type": "boolean", "notes": "Per RFC-002 §8b: every claim the pack lets the agent emit MUST be grounded." },
        "reversibility_threshold":  { "type": ["string", "null"], "enum": ["low", "medium", "high", null], "notes": "Optional default reversibility posture for pack-enabled actions." }
      }
    },
    "human_veto_policy": {
      "type": "object",
      "required": ["owner", "scope"],
      "properties": {
        "owner": { "type": "string", "enum": ["human_carrier", "human_carrier_with_guardian"], "notes": "RFC-002 §6 invariant." },
        "scope": { "type": "array", "items": { "type": "string" }, "notes": "Pack-specific scope of veto, e.g. `[\"mastery_writes\", \"exam_target_changes\", \"accommodations_changes\"]`." }
      }
    }
  },
  "notes": "Static check verifies `raise_only: true`; failure is criterion §8.8 fail."
}
```

## 9. `human_authority`

```jsonc
{
  "name": "human_authority",
  "type": "object",
  "required": ["final_decision_owner", "agent_role", "escalation"],
  "properties": {
    "final_decision_owner": {
      "type": "string",
      "enum": ["human_carrier", "human_carrier_with_guardian"],
      "notes": "Per RFC-009 §0.1 `human_authority_layer`. No other value is acceptable."
    },
    "agent_role": {
      "type": "string",
      "enum": ["advisory"],
      "notes": "Fixed value. An agent NEVER decides on a carrier's behalf."
    },
    "escalation": {
      "type": "string",
      "enum": ["self", "guardian_then_school", "school_only", "professional_then_self", "operator_then_self"],
      "notes": "Closed enum (resolved from `packs/student.md` §8.3 open decision). New values require an RFC bump."
    }
  }
}
```

## 10. `structured_memory` (the `memory_scope` field + pack-scoped slice shape)

```jsonc
{
  "name": "structured_memory",
  "type": "string",
  "pattern": "^memory\\.x_klickd\\.(user|student|coding|research|security|legal|work|creator|gaming|bridge|mission)$",
  "notes": [
    "MUST equal `memory.x_klickd.<name>` where `<name>` matches the `pack` name.",
    "MUST NOT alias `memory[]` (the v4.0 main memory). RFC-009 §5.6.",
    "A v4.0 reader that does not understand pack slices MUST preserve them verbatim on round-trip (SPEC §33.7)."
  ],
  "slice_shape": {
    "type": "array",
    "items": {
      "type": "object",
      "required": ["at", "kind", "ref"],
      "properties": {
        "at":   { "type": "string", "notes": "ISO-8601 UTC timestamp." },
        "kind": {
          "type": "string",
          "enum": [
            "chapter_completed",
            "exercise_completed",
            "mock_taken",
            "feedback_received",
            "self_reflection",
            "competency_acquired",
            "level_change",
            "evidence_added"
          ]
        },
        "ref":            { "type": "string", "notes": "Stable reference to the artefact/event." },
        "mastery_delta":  { "type": ["object", "null"], "notes": "Optional `{ competency_ref, before, after }` triple." },
        "agent_ref":      { "type": ["string", "null"], "notes": "Optional discriminated agent reference." }
      }
    },
    "notes": "Bounded by a per-pack compaction policy; old entries roll up into `mastery[]`, NOT memory creep."
  }
}
```

## 11. `evidence_policy`

```jsonc
{
  "name": "evidence_policy",
  "type": "object",
  "required": ["required_for_claims", "pointer_only", "attestation_shape_ref"],
  "properties": {
    "required_for_claims": { "type": "boolean", "enum": [true], "notes": "MUST be `true` for v4.1-native packs (RFC-002 §8b; RFC-009 §8.3)." },
    "pointer_only":        { "type": "boolean", "enum": [true], "notes": "MUST be `true`. Inline copies of carrier work in the pack are forbidden (size + privacy)." },
    "attestation_shape_ref": { "type": "string", "enum": ["rfc-002#8b"], "notes": "Single canonical attestation shape today; future shapes require RFC update." }
  }
}
```

## 12. `source_policy`

```jsonc
{
  "name": "source_policy",
  "type": "object",
  "required": ["frameworks_offline_bundle", "allow_inline_definitions", "language_tags"],
  "properties": {
    "frameworks_offline_bundle": {
      "type": "string",
      "notes": "Relative path to the pack's offline SKOS/JSON-LD bundle directory (see `../frameworks/README.md` §3). Pre-bundle, the value MAY be the literal `\"docs/rfcs/chimera/frameworks/README.md#3\"` pointing at the shape spec."
    },
    "allow_inline_definitions": {
      "type": "boolean",
      "notes": "Per-scheme licensing decides whether inline framework text is shipped (see `../frameworks/README.md` §3.4). Default `false`."
    },
    "language_tags": {
      "type": "array",
      "minItems": 1,
      "items": { "type": "string", "pattern": "^[a-z]{2}(?:-[A-Z]{2})?$" },
      "notes": "IETF BCP-47 tags. Mandatory non-empty so a reader knows which `prefLabel` languages to expect."
    }
  }
}
```

## 13. `router_cost` (RFC-003-compatible)

```jsonc
{
  "name": "router_cost",
  "type": "object",
  "required": ["tokens_estimate", "baseline", "source_row"],
  "properties": {
    "tokens_estimate": {
      "type": "integer",
      "minimum": 0,
      "notes": "Deterministic heuristic-token estimate for the pack manifest. Heuristic = `len(text)//4` over the canonicalised JSON, matching `benchmarks/context_cost/runner.py` (RFC-003 §6). See `../packs/router_cost.md` for per-pack estimates."
    },
    "baseline": {
      "type": "string",
      "enum": ["base", "base_plus_one", "base_plus_seven"],
      "notes": "Which RFC-003 baseline this estimate is taken against. `base_plus_one` = base + this pack alone; `base_plus_seven` = upper-bound seven-pack ceiling. See RFC-009 §5.3."
    },
    "source_row": {
      "type": "string",
      "notes": "Reference to the row in `benchmarks/context_cost/` (or `../packs/router_cost.md`) where this estimate was computed. Allows audit."
    },
    "pack_token_costs_entry": {
      "type": ["string", "null"],
      "notes": "Optional key into `chimera_v41_extrapolation(pack_token_costs=...)` so the runner can substitute the pack's published estimate for the default 850."
    }
  },
  "notes": [
    "RFC-009 §8.7 criterion fails if `tokens_estimate` is `null` at validation time.",
    "The estimate is a heuristic, NOT a provider token count. RFC-003 §6 documents the proxy."
  ]
}
```

## 14. `forbidden_fields` (frozen literal)

```jsonc
{
  "name": "forbidden_fields",
  "type": "array",
  "minItems": 10,
  "items": { "type": "string" },
  "must_literally_include": [
    "pedagogy",
    "teaching_method",
    "socratic_steps",
    "prompt_strategy",
    "scoring_rubric",
    "intervention_policy",
    "tone_rules",
    "system_prompt_overrides",
    "knowledge.mastered",
    "mastered_topics"
  ],
  "notes": [
    "Frozen literal list. Reviewers and static checkers use this to enforce RFC-009 §5.1.1 (carrier-vs-skill) and §5.0 (no legacy adapter).",
    "Adding or removing entries requires an RFC update.",
    "If any key in this list appears anywhere in the pack file (top-level or nested), validation fails immediately."
  ]
}
```

## 15. How these fragments combine

The pack-author workflow is:

1. Start from §1 (`pack_manifest`) and fill the required top-level keys.
2. For `frameworks[]`, pick from `../frameworks/README.md` §1.
3. For `base_transversal_core`, copy the default anchor set from `../frameworks/README.md` §2.1 (then refine if the pack genuinely extends the floor).
4. Populate `competencies[]` with framework-anchored IRIs (`esco:...`, `digcomp:...`, …). `mastery[]` is carrier-state and may be empty at publisher time.
5. Fill `gates`, `human_authority`, `memory_scope`, `evidence_policy`, `source_policy`, `router_cost`, `forbidden_fields` from the fragments above — these are publisher state, not carrier state.
6. Validate against [RFC-009 §8](../../RFC-009-chimera-v4.1.md) ten criteria + the v4.1-native shape table of [RFC-009 §8.1](../../RFC-009-chimera-v4.1.md).

If any of steps 1–5 yields a free-text value where a framework IRI is required, or yields a value listed in `forbidden_fields`, the pack fails validation. There is no migration tool and no compatibility shim (RFC-009 §5.0).

## 16. See also

- [`../../RFC-009-chimera-v4.1.md`](../../RFC-009-chimera-v4.1.md) — full RFC (carrier-vs-skill in §5.1.1, validation in §8, shape table in §8.1).
- [`../frameworks/README.md`](../frameworks/README.md) — canonical framework registry + offline bundle shape.
- [`../packs/student.md`](../packs/student.md) — first concrete pack scaffold (`x.klickd/student`).
- [`../packs/router_cost.md`](../packs/router_cost.md) — pack-level `router_cost` estimates and RFC-003 cross-walk.
