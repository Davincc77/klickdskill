# RFC-001 — `media_profile` v1

| | |
|---|---|
| **RFC** | 001 |
| **Title** | `media_profile` v1 — portable, encrypted, model-agnostic media context |
| **Target** | `.klickd v4` (envelope-v4 / payload extension) |
| **Status** | **Accepted** |
| **Author** | Vince C. (Klickd / Luxlearn, Luxembourg) |
| **Created** | 2026-05-22 |
| **Promoted to Proposed** | 2026-05-23 |
| **Promoted to Accepted** | 2026-05-24 |
| **Supersedes** | — |

> **This RFC is non-normative.** It targets a future `.klickd v4` release. No part of this document is binding on any current v3.x reader or writer. v3.x readers MUST ignore any `media_profile` field they encounter — see [Forward compatibility](#forward-compatibility).
>
> **Status note (Accepted).** The conceptual surface frozen at `Proposed` (the §4 decisions, the §5 illustrative schema, the §6 V-001…V-012 validation checklist, and the §9 error codes) is approved for inclusion in the next normative `SPEC.md` revision — see [`ACCEPTANCE_CHECKLIST_V4.md`](./ACCEPTANCE_CHECKLIST_V4.md) §3. Acceptance is **docs-only**: no SDK, schema, vector, or release is triggered. The formal JSON Schema, error wiring, and SDK API land only at `Implemented`. Open questions (§11) remain genuinely open and do not block acceptance.

---

## 1. Motivation

`.klickd v3.x` carries text-shaped user context (identity, knowledge, sessions, memory, ethics, personality). It has no first-class way to carry **media context** — the user's voice samples, reference images, signature documents, accessibility-relevant audio profiles, or model-side artefacts such as generated voice embeddings.

Today users wanting any of the following hit a wall:

1. **Cross-model voice continuity.** "My TTS agent on provider A should sound the same when I switch to provider B." Today this requires re-recording samples per provider.
2. **Reference images for visual style.** "Generate diagrams in the style of this hand-drawn sketch I made." Today this lives in provider-specific Gallery/Library features.
3. **Accessibility profiles.** A user with a speech impairment has a custom acoustic model. Today it is locked to one provider.
4. **Signature / handwriting style** for downstream document generators.
5. **Family / team avatars** for multi-agent setups (`companion_identity` in §28 has no visual counterpart).

The text-only design also makes it impossible to express "this context is partly multimodal" in a verifiable way — which matters as audit and consent requirements (EU AI Act Art. 50, GDPR Art. 22) tighten.

`media_profile` v1 fills this gap **without** turning `.klickd` into a media container. The principle is **references with verifiable hashes**, not embedded blobs.

## 2. Scope

**In scope (v1):**

- A payload-level `media_profile` object with typed entries for `voice`, `image`, `document`, `embedding`.
- A normative rule that media bytes are stored **outside** the `.klickd` file by default; the `.klickd` file holds metadata, hashes, and (optionally) inline base64 only below a size threshold.
- Hash-based deduplication and integrity verification.
- Modality-specific consent flags surfaced through the existing `data_integrity` block (§28).
- A reader-side adapter contract: an agent MAY refuse a `media_profile` entry it cannot consume, but MUST NOT silently drop it from the audit trail.

**Out of scope (v1, deferred to v2+):**

- Encrypted media sidecars (`.klickd.media/`) — sketched in §10 but not normative.
- Multi-passphrase wrapping for shared media.
- On-device fine-tuning artefact format (LoRA / adapter weights).
- Robotics actuator profiles (already partially covered by `robot_profile`).

## 3. Forward compatibility

This RFC bumps the wire envelope to `klickd_version: "4.0"`. Until v4 is normatively published in `SPEC.md`:

- v3.x **readers MUST IGNORE** `media_profile` if it appears in a v3.x payload (best-effort backward compatibility for early adopters).
- v3.x **writers MUST NOT emit** `media_profile`.
- v4 **readers MUST be able to read v3.x files** by applying the v2→v3 migration rules already in `SPEC.md` plus a no-op for the absent `media_profile`.

## 4. Decisions already resolved

The following decisions are taken and form the baseline of v1. They are listed here so reviewers can attack the **right** target.

1. **References, not embeds, by default.** A `media_profile` entry is metadata + hash + URI. Inline base64 is **permitted only** for entries ≤ 16 KiB total, and SHOULD be reserved for tiny artefacts (e.g. a 32×32 emblem, a short speech embedding).
2. **One hash, one algorithm.** Each entry carries exactly one content hash, BLAKE3, base64-encoded, with explicit `hash.algo: "blake3"` for future-proofing. No SHA-1, no MD5, no implicit algorithm.
3. **Modality is a closed enum at v1.** `voice` · `image` · `document` · `embedding`. Custom modalities live under `x_*` namespaces.
4. **No transcoding in the spec.** If a producer writes WAV, readers see WAV; no normative requirement to convert to OPUS/MP3. (Producers MAY advise a preferred fallback via `alt`.)
5. **Consent is per-entry, not per-file.** Each entry has a `consent` block. Agents MUST NOT use an entry whose `consent.purposes` does not include the action they are about to take.
6. **CC0 friendliness.** Nothing in `media_profile` requires non-free codecs or proprietary embeddings. Voice/image embeddings are vendor-tagged (`embedding.producer`), and consumers MAY refuse unknown producers.
7. **Storage location is opaque.** A `uri` MAY be `file://`, `https://`, `ipfs://`, `cas://<hash>`, or a relative path `./media/voice/sample-001.wav`. The reader chooses how to resolve.
8. **Encryption posture.** Inline `bytes_b64` entries inherit the file's envelope encryption (Argon2id + AES-256-GCM AAD-bound). External references are **out of scope of the file's confidentiality guarantees** — this is stated explicitly in §10 and the schema description.
9. **Soul Handoff interaction.** §28.8 guaranteed-fields list is **not extended** in v1; an Agent B receiving a v4 file MAY surface `media_profile` summaries but is not required to.

## 5. Schema (illustrative — non-normative)

```json
{
  "media_profile": {
    "version": 1,
    "entries": [
      {
        "id": "voice-primary",
        "modality": "voice",
        "label": "Primary voice sample (calm, neutral, fr-LU)",
        "language": "fr",
        "uri": "./media/voice/primary.wav",
        "media_type": "audio/wav",
        "byte_size": 384210,
        "duration_ms": 12000,
        "hash": { "algo": "blake3", "value": "<base64>" },
        "producer": { "kind": "human", "device": "iPhone 15, Voice Memos" },
        "consent": {
          "purposes": ["tts_synthesis", "voice_clone_personal"],
          "expires_at": "2027-05-22T00:00:00Z",
          "revocable": true
        },
        "x_notes": "Recorded 2026-05-20, ambient < 25 dB"
      },
      {
        "id": "style-sketch",
        "modality": "image",
        "label": "Hand-drawn diagram style",
        "uri": "cas://blake3:<base64>",
        "media_type": "image/png",
        "byte_size": 8120,
        "hash": { "algo": "blake3", "value": "<base64>" },
        "consent": { "purposes": ["style_reference"], "revocable": true }
      },
      {
        "id": "voice-embedding-vendorX-v2",
        "modality": "embedding",
        "label": "Vendor X voice embedding",
        "bytes_b64": "<≤16 KiB base64>",
        "media_type": "application/x-klickd-embedding+vendorX-v2",
        "hash": { "algo": "blake3", "value": "<base64>" },
        "producer": { "kind": "model", "name": "vendorX-voice-v2" },
        "consent": { "purposes": ["tts_synthesis"], "revocable": true }
      }
    ]
  }
}
```

### Field rules (intent — formal schema follows in v4 normative spec)

- `entries[].id` — unique per file; stable across edits; MUST match `^[a-z0-9][a-z0-9_-]{0,63}$`.
- `entries[].modality` — one of `voice` · `image` · `document` · `embedding`.
- Exactly one of `uri` **or** `bytes_b64` MUST be present. `bytes_b64` MUST decode to ≤ 16 KiB.
- `hash` is REQUIRED for both URI and inline entries. Readers MUST verify it before use (URI: after fetch; inline: after decode).
- `consent.purposes` is a closed enum at v1: `tts_synthesis` · `voice_clone_personal` · `style_reference` · `identity_verification` · `document_template` · `accessibility_profile`. Implementations MUST reject entries that declare a purpose outside this list **unless** the agent has a documented `x_purpose_*` extension.
- `media_type` — IANA media type. For embeddings, use `application/x-klickd-embedding+<producer>-<version>`.

## 6. Validation checklist (for the v4 conformance test suite)

Implementations claiming v4 conformance MUST pass:

- [ ] **V-001** — Reject `media_profile` whose `version` ≠ 1 with `KLICKD_E_VERSION`.
- [ ] **V-002** — Reject entries missing `id`, `modality`, or `hash`.
- [ ] **V-003** — Reject entries that contain both `uri` and `bytes_b64`.
- [ ] **V-004** — Reject `bytes_b64` entries whose decoded size > 16 KiB with `KLICKD_E_FORMAT`.
- [ ] **V-005** — Reject duplicate `id` within `entries[]`.
- [ ] **V-006** — Reject unknown `hash.algo` (v1: only `"blake3"`).
- [ ] **V-007** — On `uri` fetch: refuse to expose the entry to the agent if computed `blake3(content) ≠ hash.value`.
- [ ] **V-008** — Refuse to use an entry for an action whose purpose is not in `consent.purposes`.
- [ ] **V-009** — Refuse to use an entry whose `consent.expires_at` is in the past (compared to envelope `created_at` for offline use, or wall-clock for online use; producer SHOULD set both).
- [ ] **V-010** — Preserve unknown `x_*` fields verbatim on round-trip (no drop).
- [ ] **V-011** — A v3.x reader presented with a v4 file MUST surface a clear `KLICKD_E_VERSION` instead of attempting partial parsing.
- [ ] **V-012** — A v4 reader presented with a v3.x file MUST succeed and present `media_profile` as absent (not `null`, not `{}`).

## 7. Soul Handoff interaction (§28.8)

`media_profile` summaries MAY appear in a Soul Handoff after the §28.8 guaranteed fields, formatted as `media:<id>:<modality>`. Agent B MUST treat them as **hints**, not authoritative state — Agent B SHOULD re-verify hashes from the source file before using any media.

## 8. Privacy & threat model

- Inline `bytes_b64` content sits inside the envelope ciphertext and inherits the file's AAD-bound integrity. **This is the only confidentiality guarantee.**
- External `uri` content is **outside** the cryptographic boundary. The `.klickd` file authenticates *the hash*, not *the storage*. A reader that fetches `https://…` and gets the wrong bytes will detect it via V-007.
- A malicious holder of the `.klickd` file (without the passphrase) sees the inline ciphertext only — but for *external* references, sees the plaintext URI in the envelope. Producers SHOULD use opaque `cas://` references when URL leakage matters.
- Consent purposes are advisory in the spec but normative at the **reader** boundary: an agent that uses a sample outside `consent.purposes` is non-conformant.

## 9. Error codes (additions)

| Code | HTTP | Meaning |
|---|---|---|
| `KLICKD_E_MEDIA_HASH` | 422 | A `media_profile` entry's content hash did not match `hash.value`. |
| `KLICKD_E_MEDIA_CONSENT` | 403 | An agent attempted to use a `media_profile` entry outside its declared `consent.purposes`. |
| `KLICKD_E_MEDIA_SIZE` | 413 | An inline `bytes_b64` entry exceeded 16 KiB. |

## 10. Future work (v2+, NOT normative in v1)

- **Encrypted sidecar `.klickd.media/`** — a tarball or CAR file accompanying the `.klickd` file, with per-entry keys wrapped by the file's contentKey. Sketch:
  ```
  profile.klickd            # envelope, references entries by cas://blake3:<h>
  profile.klickd.media/     # tar of <h>.bin files, each XChaCha20-Poly1305 with
                            # per-entry key wrapped to contentKey
  ```
- Multi-passphrase / team wrapping for shared media (links to v4 schema-level multi-recipient envelope).
- A `media_profile` budget rule (max total external size to fetch before agent must ask).
- LoRA / adapter weights as a fifth modality (`adapter`) with stricter consent semantics.

## 11. Open questions

Even with §4 decided, the following remain genuinely open:

1. **Should `embedding` be a separate modality or a sub-type of `voice`/`image`?** Current choice: separate, because consent and verifiability rules differ.
2. **MUST readers verify hashes synchronously before exposing the entry to the agent, or MAY they pass through with a deferred-verification flag?** Current choice: synchronous (V-007) — simpler audit story. To revisit if it hurts streaming/mobile UX.
3. **CAS resolution (`cas://blake3:<h>`).** Is the reader required to ship a CAS resolver, or only if it advertises CAS support? Likely: optional, but advertised via reader capability handshake.
4. **Soul Handoff verbosity budget** — does the §28.8 300-char cap include media hints? Current draft says yes.
5. **Auditability of refusals.** When an agent refuses an entry (consent / size / hash), should it record the refusal back into the file's `whitehat[]` log? Probably yes — open for v2.

## 12. Examples

A non-normative example file lives at [`examples/media_profile-v1.example.json`](./examples/media_profile-v1.example.json).
