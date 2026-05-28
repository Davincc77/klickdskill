# RFC-010 — `pack_memory_compression` (extracted-facts / entity-linking / retrieval-compression pattern, pack-scoped)

| | |
|---|---|
| **RFC** | 010 |
| **Title** | `pack_memory_compression` — pack-scoped extracted-facts, entity-linking, and retrieval-compression pattern for Chimera carrier packs |
| **Target** | `.klickd v4.2` (post-v4.1 Chimera; NOT in scope for `v4.0.0` GA and NOT in scope for `v4.1` candidate pack artefacts) |
| **Status** | **Draft** |
| **Author** | Vince C. (Klickd / Luxlearn, Luxembourg) |
| **Created** | 2026-05-28 |
| **Supersedes** | — |
| **Relates to** | RFC-002 (`verification_gates`, `human_veto_policy`), RFC-004 (Migration & Backward Compatibility), RFC-006 (`agent_core`), RFC-007 (`usage_profile` & in-session skill routing), RFC-008 (`core_update_watch`), RFC-009 (`.klickd v4.1 — Chimera`), SPEC §33 (v4 round-trip), [`docs/rfcs/chimera/schema-fragments/README.md`](./chimera/schema-fragments/README.md) §10 (`structured_memory`) |

> **This RFC is non-normative and non-release.** It is a **Draft**, **docs-only**, and **v4.2-targeted**. It does **not** modify `SPEC.md`, the v4.0 GA schemas (`schemas/klickd-payload-v4.schema.json`, `schemas/klickd-payload-v4-preview.schema.json`, `schema/klickd-v4.schema.json`, `schema/klickd-v4-preview.schema.json`), any SDK, any vector, any lock file, or the status of any other RFC. It introduces **no** new normative field. It does **not** trigger a release: **no** tag, **no** `latest` on npm or PyPI, **no** DOI on Zenodo, **no** IANA action, **no** GitHub Release, **no** site exposure, **no** SDK bump. It does **not** modify any of the frozen 42 v4.1 x.klickd skill artefacts.
>
> The production-recommended `.klickd` remains **v3.5.1**. The GA track is **v4.0.0**. The next minor is **v4.1 Chimera** (RFC-009). This RFC describes a **v4.2** capability so reviewers can compare it against the v4.1 surface *before* any normative wording, schema, or pack field lands.

---

## 0. TL;DR

- v4.1 Chimera packs (`x.klickd/<pack>`) carry **carrier state** — what a carrier knows about itself in a domain. The append-only `structured_memory` slice (RFC-009 §5.6, schema fragments §10) grows monotonically with chapter/exercise/feedback events.
- For long-lived carriers, that slice grows. RFC-009 §3 already lists a planned "claim-memory growth & deterministic compaction" RFC (placeholder RFC-005).
- **RFC-010 (this RFC) is a different and complementary lever, scoped explicitly to v4.2 and to Chimera packs**: a `compressed_memory` block under each pack's `structured_memory`, carrying **pointers** to extracted facts, entity links, graph references, and an external vector index URI — never inline secrets, never inline embeddings, never extraction code or prompts.
- The user-validated concept name `knowledge.skills_compressed` is **reserved** as a user-facing alias / possible future payload alias. It is **not** implemented in v4.1 and is **not** added to v4.0 GA. See §10.
- **Anti-copy statement.** The pattern is inspired by published extraction/retrieval memory systems (Mem0, GraphRAG, Letta/MemGPT, A-MEM, Zep, and the wider RAG literature). **No code is copied; no compatibility with any of those systems is claimed; field names, the gate action class, the erasure-cascade rule, and host-side extraction are all `.klickd`-native and differ from those projects' shapes.** See §2 and §9.

---

## 1. Motivation

Three observations from the v4.1 Chimera audit drive this RFC:

1. **`structured_memory` is append-only and grows.** Chimera's `memory.x_klickd.<pack>` slice (RFC-009 §5.6, schema-fragments §10) records `chapter_completed`, `exercise_completed`, `feedback_received`, `competency_acquired`, etc. Over months of use this becomes a long, low-signal log even with the §10 "old entries roll up into `mastery[]`" guidance.

2. **Extraction is behaviour, not state.** Recent memory systems show good results extracting *facts* from raw conversation and storing only the facts (Mem0), linking facts into a graph (GraphRAG / Zep / A-MEM), and recalling via vector + graph hops. But that extraction is **runtime behaviour** that belongs **host-side** (in `agent_core` / `host_skill` per RFC-009 §0.1), **not** in a carrier file. The audit therefore recommends **against** mounting a fact-extraction block in v4.0 GA *or* in v4.1 candidate skill artefacts: those are state, not behaviour.

3. **Pack memory needs compression that survives portability and round-trip.** A pack must remain portable across hosts (RFC-009 §5.6) and round-trip cleanly through a v4.0 reader (SPEC §33.7). Any compression block therefore MUST be **declarative state** (pointers, hashes, URIs, policies) — never executable extraction logic, never inline embeddings.

RFC-010 is the corrected direction: a pack-scoped, **state-only**, **pointer-only** compression block, with extraction explicitly delegated host-side, mounted under a path the audit recommends — `x_klickd_pack.structured_memory.compressed_memory` — so that v4.0 GA and the frozen v4.1 skill artefacts are untouched.

## 2. Prior art and explicit anti-copy statement

The extracted-facts / entity-linking / retrieval-compression pattern is well-trodden in open and published memory systems. RFC-010 acknowledges that prior art and explicitly states what it is **not**.

| System | What it does | What RFC-010 borrows | What RFC-010 does NOT borrow |
|---|---|---|---|
| Mem0 | Runtime extraction of facts from chat turns, storage in a vector + key-value store, recall via similarity. | The high-level *idea* that compressed extracted facts can replace verbatim transcripts for memory recall. | Any code. Any field name. Any storage format. Any extraction prompt. No compatibility with Mem0 storage, API, or schema is claimed or implied. |
| GraphRAG / Microsoft GraphRAG | LLM-extracted entities + relations + community summaries over a corpus, queried with hybrid retrieval. | The high-level *idea* of pointing carrier memory at an entity/relation graph. | Code, prompts, schema, community-summary algorithm, indexer. No GraphRAG-compatible artefact is produced. |
| Letta / MemGPT | OS-style paged memory with summary + archival tiers managed by the agent. | The high-level *idea* of demoting raw turns to compressed summaries. | The OS / paging metaphor. The agent-managed tiering. No MemGPT-shaped block is introduced. |
| Zep | Temporal knowledge graph extraction with explicit time edges. | The high-level *idea* of temporal validity on extracted facts. | The graph schema, the temporal-edge algorithm, the API. |
| A-MEM / Agentic Memory | Atomic notes + dynamic linking inspired by Zettelkasten. | The high-level *idea* that linkable atomic units beat large summaries. | The note format, the linking algorithm. |
| Generic RAG | Chunk + embed + retrieve. | Nothing structural; baseline reference only. | The chunker, embedder, retriever, prompt. |

**Anti-copy statement (normative intent for this RFC):**

> RFC-010 is *inspired by* the family of extracted-facts / entity-linking / retrieval-compression systems above. **It copies no code, no schema, no field name, and no extraction prompt from any of them.** It claims **no** compatibility with Mem0, GraphRAG, Letta/MemGPT, Zep, A-MEM, or any other named memory system. Its field names (`compressed_memory`, `fact_pointers`, `entity_links`, `graph_refs`, `vector_index`, `retrieval_policy`, `derived_from`, `evidence_hashes`, `erasure_cascade`, `gate_refs`) are `.klickd`-native. Its host-side-only extraction rule (§5), pack-scoped mounting (§4), pointer-only fact bodies (§5.2), GDPR Art.17 erasure-cascade rule (§6.2), and `memory_recall_injection` gate action class (§6.3) are `.klickd`-native too. Any subsequent PR or implementation that imports or vendors code from a third-party memory system MUST disclose that fact and MUST NOT be merged under this RFC's banner.

## 3. Scope, non-scope, and target version

### 3.1 Scope

- A new optional block `compressed_memory` mounted at the pinned path `x_klickd_pack.structured_memory.compressed_memory` inside each Chimera carrier pack (§4.1).
- A `retrieval_policy` declaring how the host MAY recall the compressed block (top-k, recency weighting, gate references).
- A `vector_index` URI pointing at an **external** index (never inline embeddings).
- A `graph_refs[]` list of pointers to entity-graph nodes/edges, always external.
- A `fact_pointers[]` list of pointers — to evidence artefacts (`evidence_policy.pointer_only = true`, RFC-009 §11 / RFC-002 §8b) — with hash, derivation, confidence, and erasure metadata.
- An `erasure_cascade` block making GDPR Art.17 deletion deterministic across the compressed view and the indices it points at.
- A new verification gate action class `memory_recall_injection` (§6.3), defined here for v4.2 only.

### 3.2 Non-scope (explicit)

This RFC does **not** add:

- Any field to `schemas/klickd-payload-v4.schema.json`, `schemas/klickd-payload-v4-preview.schema.json`, `schema/klickd-v4.schema.json`, or `schema/klickd-v4-preview.schema.json`.
- Any field to any of the frozen 42 v4.1 x.klickd skill artefacts.
- Any code, prompt, scoring function, or runtime that extracts facts from conversation. Extraction is host-side (`agent_core` / `host_skill`, per RFC-009 §0.1).
- Any inline embedding, raw transcript, or fact body. Bodies are pointers (§5.2).
- Any `latest` on npm / PyPI / Zenodo / IANA / GitHub Release.
- Any change to RFC-005 (the planned claim-memory compaction RFC); RFC-005 remains the right home for deterministic compaction of `structured_memory`'s append-only slice. RFC-010 is **complementary**, not a replacement.

### 3.3 Target version

**v4.2**, after v4.1 Chimera GA and after RFC-005 (claim-memory growth & deterministic compaction) is at least Proposed. RFC-010 is **not** a v4.1 candidate skill artefact and **not** in scope for the v4.0 GA P0 backlog defined in [`docs/roadmap/ROAD-TO-V4-GA.md`](../roadmap/ROAD-TO-V4-GA.md).

## 4. Mounting

### 4.1 Path (pinned)

The canonical mount path for RFC-010 is:

```
x_klickd_pack.structured_memory.compressed_memory
```

This path is **pinned** by this Draft. There is no alternative. The schema fragment (§5), the example fixture (`docs/rfcs/examples/pack_memory_compression-v1.example.json`), and the validator test (`tests/test_rfc010_pack_memory_compression.py`) all use this exact path. The promotion PR MUST NOT introduce a second path.

The path nests the new block under the existing pack-scoped `structured_memory` field (RFC-009 §5.6, schema-fragments §10) rather than at the top of a pack manifest. The rationale is:

1. `structured_memory` is already the field that carries the carrier's pack-local memory slice.
2. The compressed view is a **derived** view of the same slice — co-locating them keeps the derivation visible.
3. Mounting under `x_klickd_pack.*` keeps the new block clearly in the `x.klickd/<pack>` namespace (RFC-009 §0.1 `carrier_pack`) and prevents any drift toward the top-level v4.0 `memory[]` (which RFC-009 §5.6 forbids aliasing).

### 4.2 Reserved user-facing concept name

The concept name `knowledge.skills_compressed` was validated by the user as the *user-facing* name for the idea. **It is not implemented in v4.0 GA or v4.1.** It is reserved as a possible **future payload alias** (e.g. a top-level read-only convenience view in v4.2 or later that reflects the per-pack `compressed_memory` blocks). It MUST NOT be added to v4.0 GA, MUST NOT be added to v4.1 candidate skill artefacts, and MUST NOT be relied on by any reader until a future RFC promotes it. See §10 for the full reservation note.

## 5. Schema fragment (NON-NORMATIVE)

This fragment defines the shape of `compressed_memory`. It is **not** added to any current schema file. A v4.0 / v4.1 reader that encounters `compressed_memory` MUST preserve it verbatim on round-trip (SPEC §33.7).

```jsonc
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://klickd.app/schemas/rfc-010/compressed_memory.schema.json",
  "title": "compressed_memory — RFC-010 v4.2 Draft (NON-NORMATIVE)",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "version",
    "derived_from",
    "fact_pointers",
    "entity_links",
    "graph_refs",
    "vector_index",
    "retrieval_policy",
    "erasure_cascade",
    "gate_refs"
  ],
  "properties": {
    "version": {
      "type": "string",
      "const": "rfc-010-draft",
      "description": "Pins this block to RFC-010 Draft. Bumped only when the RFC is promoted."
    },

    "derived_from": {
      "type": "object",
      "additionalProperties": false,
      "required": ["pack", "slice_path", "extractor"],
      "properties": {
        "pack":       { "type": "string", "pattern": "^x\\.klickd/[a-z][a-z0-9_-]*$" },
        "slice_path": { "type": "string", "const": "structured_memory" },
        "extractor": {
          "type": "object",
          "additionalProperties": false,
          "required": ["kind", "host", "agent_ref", "version", "deterministic_seed"],
          "properties": {
            "kind": {
              "type": "string",
              "enum": ["host_skill", "local_runtime", "verified_bridge"],
              "description": "Class of extractor that produced this compressed view. `host_skill` = a Klickd-side host_skill (RFC-009 §0.1). `local_runtime` = a manual / interactive run on the user's device, no automated pipeline. `verified_bridge` = a third-party bridge that publishes an attestation. No other value is allowed."
            },
            "host":              { "type": "string", "minLength": 1, "description": "Host that ran the extraction (e.g. 'kai-edu-2026'). Carrier never runs extraction itself; see §5.1." },
            "agent_ref": {
              "type": "string",
              "pattern": "^x\\.klickd/host/[a-z][a-z0-9._/-]*$",
              "description": "Discriminated reference to the extractor `host_skill` (RFC-009 §0.1). MUST start with `x.klickd/host/`. Arbitrary external URLs are forbidden — discrimination is enforced by the schema pattern, not only by the host gate."
            },
            "version": {
              "type": "string",
              "pattern": "^[0-9]+\\.[0-9]+\\.[0-9]+(?:-[A-Za-z0-9.+-]+)?$",
              "description": "Semver-shaped extractor host_skill version (`MAJOR.MINOR.PATCH` with optional pre-release suffix). Required so a re-extraction is reproducible."
            },
            "deterministic_seed":{ "type": ["string", "null"], "description": "Optional canonical seed for deterministic re-extraction. May be null if the extractor is intrinsically deterministic." },
            "attestation_hash": {
              "type": ["string", "null"],
              "pattern": "^(?:sha256|blake3):[A-Fa-f0-9]{32,}$",
              "description": "Required when `kind` ∈ {`host_skill`, `verified_bridge`} (automated or verified extraction). MAY be null when `kind = local_runtime` (manual on-device extraction with no automated pipeline to attest). Format: `<algo>:<hex>` where `<algo>` ∈ {`sha256`, `blake3`}."
            }
          },
          "allOf": [
            {
              "if":   { "properties": { "kind": { "enum": ["host_skill", "verified_bridge"] } }, "required": ["kind"] },
              "then": { "required": ["kind", "host", "agent_ref", "version", "deterministic_seed", "attestation_hash"], "properties": { "attestation_hash": { "type": "string" } } }
            }
          ]
        }
      }
    },

    "fact_pointers": {
      "type": "array",
      "description": "Pointer-only fact list (§5.2). Inline fact bodies are FORBIDDEN.",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["id", "evidence_uri", "evidence_hash", "derived_from", "confidence", "issued_at"],
        "properties": {
          "id":            { "type": "string", "pattern": "^fp_[A-Za-z0-9_-]{8,}$" },
          "evidence_uri":  { "type": "string", "format": "uri", "description": "Pointer to the canonical evidence artefact. MUST resolve to content addressed by `evidence_hash`. MUST NOT be a data: URL containing inline content." },
          "evidence_hash": {
            "type": "object",
            "additionalProperties": false,
            "required": ["algo", "value"],
            "properties": {
              "algo":  { "type": "string", "enum": ["blake3", "sha256"] },
              "value": { "type": "string", "minLength": 32 }
            }
          },
          "derived_from": {
            "type": "array",
            "minItems": 1,
            "items": { "type": "string", "description": "Reference into the pack's `structured_memory[]` slice (the `ref` field of an entry, per RFC-009 schema-fragments §10) or another fact pointer id (`fp_*`). RFC-010 does NOT require any new value in RFC-009's `kind` enum." }
          },
          "confidence": { "type": "number", "minimum": 0, "maximum": 1 },
          "issued_at":  { "type": "string", "format": "date-time" },
          "valid_until":{ "type": ["string", "null"], "format": "date-time", "description": "Optional temporal validity bound (e.g. 'student is in classe terminale 2026' expires 2027-09-01)." },
          "erasure_status": {
            "type": "string",
            "enum": ["active", "cascade_purged"],
            "default": "active",
            "description": "Local-to-RFC-010 erasure marker for the pointer itself. `active` = pointer is live. `cascade_purged` = the underlying evidence was erased and this pointer entry was cascade-purged per §6.2 (the entry MAY be removed entirely; if retained for auditability, it MUST carry this status). This field replaces any reliance on a new value in RFC-009 §10's `kind` enum."
          },
          "erasure_at": {
            "type": ["string", "null"],
            "format": "date-time",
            "description": "UTC timestamp of cascade purge. MUST be set when `erasure_status = cascade_purged`; MUST be null otherwise."
          },
          "redaction":  {
            "type": "string",
            "enum": ["none", "salted_hash_only", "encrypted_blob_pointer"],
            "default": "none",
            "description": "Privacy posture of the evidence the pointer references. `none` is acceptable only for non-sensitive facts."
          },
          "tags": { "type": "array", "items": { "type": "string" } }
        }
      }
    },

    "entity_links": {
      "type": "array",
      "description": "Entity-link records, each tying a fact pointer to an external entity. The entity itself is not stored inline.",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["fact_id", "entity_uri", "scheme"],
        "properties": {
          "fact_id":   { "type": "string", "pattern": "^fp_[A-Za-z0-9_-]{8,}$" },
          "entity_uri":{ "type": "string", "format": "uri", "description": "External entity URI (e.g. an ESCO competency, a Wikidata Q-id, a curriculum ref)." },
          "scheme":    { "type": "string", "description": "Identifier of the entity scheme — e.g. 'esco', 'wikidata', 'curriculum_ref'. No PII schemes allowed." },
          "role":      { "type": "string", "enum": ["subject", "object", "qualifier", "context"], "default": "subject" }
        }
      }
    },

    "graph_refs": {
      "type": "array",
      "description": "Pointers into an EXTERNAL entity/relation graph. The graph itself is never inlined.",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["graph_uri", "node_or_edge_id"],
        "properties": {
          "graph_uri":       { "type": "string", "format": "uri" },
          "node_or_edge_id": { "type": "string", "minLength": 1 },
          "kind":            { "type": "string", "enum": ["node", "edge"], "default": "node" },
          "labels":          { "type": "array", "items": { "type": "string" } }
        }
      }
    },

    "vector_index": {
      "type": "object",
      "additionalProperties": false,
      "required": ["uri", "embedding_model_ref", "dim", "inline_embeddings_forbidden"],
      "properties": {
        "uri":                 { "type": "string", "format": "uri", "description": "URI of the external vector index. MUST NOT be a data: URL." },
        "embedding_model_ref": { "type": "string", "minLength": 1, "description": "Discriminated reference to the embedding model (vendor, name, version). Free-text disallowed." },
        "dim":                 { "type": "integer", "minimum": 1 },
        "inline_embeddings_forbidden": { "type": "boolean", "const": true, "description": "MUST be true. The pack file MUST NOT contain any embedding vector inline (§5.4)." }
      }
    },

    "retrieval_policy": {
      "type": "object",
      "additionalProperties": false,
      "required": ["top_k", "max_facts_per_turn", "freshness_weighting", "host_side_only"],
      "properties": {
        "top_k":               { "type": "integer", "minimum": 1, "maximum": 50 },
        "max_facts_per_turn":  { "type": "integer", "minimum": 1, "maximum": 50 },
        "freshness_weighting": { "type": "string", "enum": ["none", "linear_recency", "exponential_recency"] },
        "host_side_only":      { "type": "boolean", "const": true, "description": "MUST be true. Retrieval is host behaviour; the carrier file never executes retrieval." },
        "require_gate":        { "type": "string", "enum": ["memory_recall_injection"], "default": "memory_recall_injection" }
      }
    },

    "erasure_cascade": {
      "type": "object",
      "additionalProperties": false,
      "description": "GDPR Art.17 deterministic deletion plan. See §6.2.",
      "required": ["targets", "on_evidence_deletion", "on_user_request"],
      "properties": {
        "targets": {
          "type": "array",
          "minItems": 1,
          "items": { "type": "string", "enum": ["fact_pointers", "entity_links", "graph_refs", "vector_index"] }
        },
        "on_evidence_deletion": {
          "type": "string",
          "enum": ["cascade_purge", "tombstone_only"],
          "description": "cascade_purge = remove pointer + entity links + vector entries + graph refs derived from the same evidence. tombstone_only = mark deleted, do not purge external index (only acceptable if the host can prove external purge by another channel)."
        },
        "on_user_request": {
          "type": "string",
          "enum": ["cascade_purge"],
          "description": "User-initiated Art.17 erasure MUST cascade_purge. No exceptions."
        },
        "verification_artifact_ref": { "type": ["string", "null"], "format": "uri" }
      }
    },

    "gate_refs": {
      "type": "array",
      "minItems": 1,
      "description": "References into verification_gates (RFC-002 §5.1). MUST include the memory_recall_injection gate (§6.3).",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["gate_name", "action_class"],
        "properties": {
          "gate_name":    { "type": "string", "minLength": 1 },
          "action_class": { "type": "string", "enum": ["memory_recall_injection"] }
        }
      }
    }
  }
}
```

### 5.1 Pointer-only facts (normative intent)

> A `fact_pointers[]` item MUST point at an evidence artefact via `evidence_uri` + `evidence_hash`. **Inline fact bodies are FORBIDDEN.** This mirrors RFC-009 §11 `evidence_policy.pointer_only = true`. The body of the fact lives outside the pack file, at the URI, addressed by the hash. The pack is therefore a **map of memory**, never a copy of it.

### 5.2 No raw sensitive content inline (normative intent)

> If an extracted fact is sensitive (anything that could re-identify the carrier, anything classified `redaction != "none"`), the `evidence_uri` MUST point at an **encrypted** artefact or a **salted-hash** opaque token. The pack file itself MUST NOT contain the raw text. v4.0 readers that do not decrypt or resolve pointers see only opaque references — this is the round-trip guarantee.

### 5.3 No inline embeddings (normative intent)

> `vector_index.inline_embeddings_forbidden = true` is a hard invariant. A pack file MUST NOT contain raw embedding vectors. The reasons are (a) embeddings leak information about source text; (b) embeddings are large and would bloat round-trip; (c) embeddings tie a portable carrier to a specific model version, which violates RFC-009 §5.6 portability.

### 5.4 No extraction logic inside the pack

> A pack file MUST NOT contain extraction prompts, scoring functions, regex patterns for fact mining, or any code/template used to *produce* the compressed view. Extraction is host-side: it lives in `agent_core` (RFC-006) or in a `host_skill` (RFC-009 §0.1). The pack records only the *output* state — pointers, hashes, links, policy.

## 6. Security and privacy rules

### 6.1 Host-side extractor only

The `derived_from.extractor` field is a **declaration** of which host ran the extraction. The carrier file does not contain extraction code. A host that produces or updates a `compressed_memory` block MUST:

1. Run extraction inside its `host_skill` (e.g. `x.klickd/host/memory-extractor`), never inside a carrier-side template.
2. Stamp `derived_from.extractor.kind` ∈ {`host_skill`, `local_runtime`, `verified_bridge`}, `host`, `agent_ref` (which MUST start with `x.klickd/host/` — no arbitrary external URLs), `version` (semver), and (if available) `deterministic_seed`.
3. Stamp `attestation_hash` (sha256 / blake3) whenever `kind ∈ {host_skill, verified_bridge}`. `attestation_hash` MAY be null only when `kind = local_runtime` (manual on-device extraction).
4. Submit each write to the `memory_recall_injection` gate (§6.3) and to the `human_authority_layer` (RFC-009 §0.1, §5.1).

A reader that cannot trust `derived_from.extractor` (missing `attestation_hash` when required, unknown `kind`, non-`x.klickd/host/` `agent_ref`, etc.) MUST treat the `compressed_memory` as opaque and recall from the underlying `structured_memory[]` slice instead.

### 6.2 GDPR Art.17 erasure cascade (normative intent)

When a carrier exercises a right-to-erasure (GDPR Art.17) against any evidence artefact referenced by a `fact_pointers[].evidence_uri`, the host MUST:

1. For every `fact_pointers[]` entry whose `evidence_uri` or `derived_from` chain resolves to the deleted artefact, EITHER remove the entry entirely OR set `erasure_status = "cascade_purged"` with `erasure_at = <UTC timestamp>` (auditable retention).
2. Remove every `entity_links[]` entry whose `fact_id` was purged or removed in (1).
3. Remove every `graph_refs[]` entry derived solely from facts purged or removed in (1).
4. Purge the corresponding vectors from `vector_index.uri` (or store a verifiable attestation that the external index has done so, per `erasure_cascade.verification_artifact_ref`).

This mechanism is **RFC-010-local**. RFC-010 does **not** require any change to RFC-009 §10's `structured_memory[].kind` enum: the erasure record lives on the `fact_pointers[]` item via `erasure_status` + `erasure_at`, not on the underlying `structured_memory[]` slice.

`erasure_cascade.on_user_request` MUST be `"cascade_purge"`. `"tombstone_only"` is **not** a valid response to a user request; it is allowed only as a transitional state for evidence deletions initiated outside the carrier (e.g. a third-party source-of-truth deletion) and only when an external purge attestation exists.

### 6.3 Verification gate action class `memory_recall_injection`

RFC-010 introduces (for v4.2 only, **non-normative until promoted**) a new `verification_gates` action class:

```jsonc
{
  "name": "compressed_memory_recall",
  "action_class": "memory_recall_injection",
  "level": "warn"
}
```

Semantics:

- An agent that retrieves from a pack's `compressed_memory` and *injects* the retrieved facts into a model prompt MUST consult this gate.
- The gate level (RFC-002 §5.1: `silent` / `warn` / `ask` / `refuse`) is **carrier-configurable**, but the gate itself MUST be present. A pack MAY raise the gate level; a host MUST NOT lower it.
- The gate is a **soft guard**, not a kill switch — it sits next to `ethics.locked_actions` (RFC-002 §6.4), not on top of it.

### 6.4 Human veto unchanged

Nothing in this RFC weakens or replaces the v4.0 `human_veto_policy` (RFC-002 §5.2) or the `human_authority_layer` (RFC-009 §0.1). The user always wins on every recall conflict.

### 6.5 No extraction prompts / scoring functions in the pack

A `compressed_memory` block MUST NOT contain:

- Extraction prompts or templates.
- Scoring functions, regular expressions used for mining, or any code intended to be executed.
- Inline model weights, distillations, or compressed knowledge derived from any third-party memory system's runtime.

A PR that violates this rule MUST be rejected as an RFC-010 validation failure.

## 7. Migration and compatibility

- **v4.0 GA.** No change. A v4.0 reader that encounters a `compressed_memory` block inside an unknown `x_klickd_pack.structured_memory.*` slice preserves it verbatim under SPEC §33.7.
- **v4.1 Chimera.** No change. The frozen 42 v4.1 x.klickd skill artefacts are not modified. v4.1 packs MAY ignore `compressed_memory` entirely; they MAY also recognise it but they MUST NOT mutate it without `memory_recall_injection` gate consultation.
- **v4.2.** Promotion of this RFC follows the same checklist as the v4 acceptance flow ([`ACCEPTANCE_CHECKLIST_V4.md`](./ACCEPTANCE_CHECKLIST_V4.md), adapted to v4.2). Schema files are touched **only at promotion time**.
- **RFC-005 relationship.** RFC-005 (claim-memory growth & deterministic compaction) compresses `structured_memory[]` *itself* by rolling up old entries into `mastery[]`. RFC-010 produces a **different view** — extracted facts pointing back at the same slice — for fast recall. They are independent and may ship together at v4.2 without conflict.

## 8. Validation criteria (RFC-010-specific)

A PR claiming to advance RFC-010 (including this PR) MUST satisfy:

1. The RFC document exists at `docs/rfcs/RFC-010-pack-memory-compression.md`.
2. **No** modification to `schemas/klickd-payload-v4.schema.json`.
3. **No** modification to `schemas/klickd-payload-v4-preview.schema.json`.
4. **No** modification to `schema/klickd-v4.schema.json` or `schema/klickd-v4-preview.schema.json`.
5. **No** modification to any of the 42 frozen v4.1 x.klickd skill artefacts.
6. **No** "Mem0 compatible", "GraphRAG compatible", "Letta compatible", "MemGPT compatible", "Zep compatible", or "A-MEM compatible" claim anywhere in the document or example fixture.
7. Key terms present in the RFC: `compressed_memory`, `fact_pointers`, `entity_links`, `graph_refs`, `vector_index`, `retrieval_policy`, `erasure_cascade`, `erasure_status`, `cascade_purged`, `gate_refs`, `memory_recall_injection`, `host-side`, `pointer-only`, `GDPR Art.17`, `knowledge.skills_compressed`, `host_skill`, `local_runtime`, `verified_bridge`, `attestation_hash`.
8. The example fixture under `docs/rfcs/examples/` is clearly marked non-GA / non-release.
9. No npm / PyPI / Zenodo / IANA / GitHub Release / tag artefact is added by the PR.

## 9. Anti-copy compliance checklist

For RFC-010 to remain merge-eligible, every PR under its banner MUST be able to answer **NO** to each of the following:

1. Does the PR import, vendor, or copy code from Mem0, GraphRAG, Letta/MemGPT, Zep, A-MEM, or any other memory system?
2. Does the PR claim compatibility (wire-level, schema-level, or API-level) with any of the above systems?
3. Does the PR re-use a field name from any of those systems' published schemas without the `.klickd`-native renaming applied in §5?
4. Does the PR ship extraction prompts, scoring code, or runtime logic copied from those systems?

If any answer is YES, the PR is out of scope for this RFC and MUST be re-routed to a separate, clearly-labelled integration RFC with its own license and provenance review.

## 10. Reserved user-facing concept name — `knowledge.skills_compressed`

The user validated `knowledge.skills_compressed` as the **user-facing** name for the idea ("my skills, in compressed form"). The audit recommends **not** mounting it in v4.0 GA or in v4.1 candidate skill artefacts because:

- v4.0 GA is identity / memory / governance — not skills.
- v4.1 packs (`x.klickd/<pack>`) are **carrier state**; the compression view is *derived* state — a separate level of indirection.
- Extraction / retrieval is **behaviour**, which lives host-side (RFC-009 §0.1 `host_skill`).

`knowledge.skills_compressed` is therefore **reserved**:

- It MUST NOT be added as a field to `schemas/klickd-payload-v4.schema.json` or `schemas/klickd-payload-v4-preview.schema.json`.
- It MUST NOT be added to any of the frozen 42 v4.1 x.klickd skill artefacts.
- It MAY be promoted in a **future** RFC (v4.2 or later) as a read-only top-level **alias** reflecting the union of pack-scoped `compressed_memory` blocks — but **only** after RFC-010 itself is promoted, and only as an alias, never as a writable surface.
- Documentation and user-facing UI MAY refer to the concept as "skills compressed" or `knowledge.skills_compressed` for human-readable purposes, but readers and writers MUST resolve such references to the pack-scoped `compressed_memory` blocks until and unless a promotion RFC says otherwise.

## 11. Open questions

> **Resolved in this Draft (no longer open):**
>
> - **Mount path** is pinned to `x_klickd_pack.structured_memory.compressed_memory` (§4.1). No alternative path remains in the RFC.
> - **`evidence_removed` enum dependency on RFC-009 §10** is removed. Erasure is now recorded on the `fact_pointers[]` items themselves via a local `erasure_status` field (§5, §6.2). RFC-010 no longer requires any change to RFC-009's `structured_memory[].kind` enum.

1. Should `derived_from.slice_path` be widened beyond the literal `"structured_memory"` (e.g. to allow a future `history[]` source)? — Default answer: no, until v4.2 ships at least one alternative slice.
2. Should `retrieval_policy.require_gate` accept additional gates (e.g. a future `memory_recall_redaction` action class)? — Default answer: not in v4.2; one gate, one action class.
3. Should `erasure_cascade.verification_artifact_ref` follow RFC-002 §8b attestation shape directly, or a thinner Art.17-specific shape? — Default answer: follow §8b; reduces surface and reuses contract tests.
4. Should the alias `knowledge.skills_compressed` (§10) be top-level on the envelope or top-level on the v4 payload? — Default answer: payload-level, mirroring `memory[]`.
5. Should `extractor.kind` enum gain additional values beyond `host_skill` / `local_runtime` / `verified_bridge` in v4.2 (e.g. `air_gapped_runtime`)? — Default answer: no, additions deferred to a future RFC.

## 12. Non-release confirmation

This RFC's promotion to **Proposed** or **Accepted** is **docs-only**, follows the v4 acceptance checklist, and triggers:

- **No** tag.
- **No** `latest` on npm or PyPI.
- **No** Zenodo DOI.
- **No** IANA action.
- **No** GitHub Release.
- **No** site exposure.
- **No** SDK bump.
- **No** vector update.
- **No** modification of the frozen 42 v4.1 x.klickd skill artefacts.
- **No** modification of v4.0 GA schemas.

Implementation work (schema, SDK, vectors) starts **only** when this RFC reaches `Accepted` *and* a separate v4.2 ROAD-TO file is opened. Until then, RFC-010 is shape-only.
