# x.klickd supply chain — skill-pack build process spec

> **Status:** Draft · **NON-NORMATIVE** · companion to [`RFC-009-chimera-v4.1.md`](../RFC-009-chimera-v4.1.md).
> **Triggers no release.** No tag, no `latest` on npm/PyPI, no Zenodo DOI, no IANA action, no schema change, no automation claim beyond the per-stage `tool` / `manual` / `planned` labels in §3.
> **Internal naming.** This document uses the public name **`x.klickd`** throughout. The internal track codename used in sibling directory/file paths is an internal identifier only and MUST NOT be propagated to public surfaces (README, `docs/public/*`, package metadata).

This document describes the **process** by which an `x.klickd` candidate `carrier_pack` is built, audited, and (if it passes) promoted. RFC-009 specifies the *artefact* (architecture, the ten validation criteria in §8/§8.1, the v4.1-native shape). This spec describes the *pipeline that produces and gates that artefact*. The two are companions: RFC-009 says what a pack must be; this says how a pack is made and checked.

---

## 0. Scope and claim boundary

This is a process specification, not a runnable end-to-end system today. Read the per-stage labels in §3 literally.

What this document does **not** claim:

- **No universal standard.** `x.klickd` is a format and a process, not an industry standard. No "universal standard" claim is made or implied.
- **No automatic compliance.** Nothing here delivers automatic GDPR / EU AI Act / sectoral compliance. License and boundary checks (§3 stages 11, 14) are *engineering checks*, not legal compliance attestations.
- **No proven benchmark superiority.** §9 describes benchmark *intent*. No "benchmark superiority proven" claim is made without external, reproducible evidence.
- **No loaded-skill claim without proof.** A pack is "loaded" / "used" only when `artifact_loaded = true` **and** `sha256_matches_manifest = true` per [`skill-loader-protocol.md`](../../integrations/skill-loader-protocol.md). A catalog entry, a stub, a routing placeholder, or a marketing page is never a loaded skill.

The **70–80% automation** figure in the brief is a **design target**, not a guarantee and not a measured result. As of this draft, only a subset of the pipeline is backed by shipped tooling (see §3). The honest current state is: the build *process* is specified end-to-end; the build *runner* is partial.

---

## 1. Build request (input)

The pipeline input is a normalised **build request**: configuration only.

- **Config-only.** Names the target pack id (`x.klickd/<name>`), the framework backbone to anchor against (RFC-009 §5.7), the track (P0 / P1), and the requested tier (Lite / Pro).
- **No PII, no secrets.** Build requests and every artefact they produce are publisher-owned. No user memory, sessions, consent, or PII enters the pipeline (RFC-009 §8 criterion 4).
- **Deterministic identity.** The build request is hashed to an `input_hash`. The same `input_hash` is expected to produce the same `output_hash` (§7).

**Outputs of a build are audit artefacts**, not just a pack file: the candidate pack, a diff report (§5), a determinism record (§7), and an audit-trail entry (§10).

---

## 2. Human / agent configuration and the gated premium pass

The pipeline is configurable by a **human or an agent** through the build request. The configuration surface is the *only* place an operator shapes the output before audit.

The **premium pass** — human or agent intervention to lift a candidate to reference quality — is restricted to the **last layer only** and is **gated**:

- It runs **only after** the candidate has been built and audited (§8).
- It runs **only if explicitly requested**.
- It edits the candidate's final layer; it does not silently re-run earlier stages or compensate for a failed build.

This gating is what keeps the benchmark (§9) honest: a premium pass that ran before the audit would mask how much the pipeline actually produced.

---

## 3. The 18-stage pipeline

Each stage is labelled with its current backing:

- **`tool`** — backed by shipped, runnable tooling in this repo.
- **`manual`** — performed by a human/agent reviewer; no automation claimed.
- **`planned`** — specified here but not yet backed by a shipped artefact. **Not automated today.**

| # | Stage | Backing | Notes |
|---|---|---|---|
| 1 | Build request normalisation | `manual` | Config-only; produces `input_hash` (§1). |
| 2 | Source intake | `manual` | Pull framework backbone refs (ESCO / WEF / O\*NET / DigComp / EQF / CEFR …) from the registry. |
| 3 | Domain mapping | `tool` (partial) | Candidate↔framework mapping validated by [`scripts/validate_v4_1_candidate_mapping.py`](../../../scripts/validate_v4_1_candidate_mapping.py). |
| 4 | Foundation / transversal grafting | `manual` | Graft the foundation + transversal competency floor (RFC-009 architecture). |
| 5 | Context-graph generation | `planned` | Required graph shape in §3.1; generator not yet shipped. |
| 6 | Governance & security injection | `manual` | Inject gate defaults + veto posture (RFC-009 §8 criteria 2, 8). |
| 7 | Evidence binding | `manual` | Every claim declares a grounding rule (RFC-009 §8 criterion 3). |
| 8 | Candidate skill generation | `planned` | Assemble the candidate pack artefact; assembler not yet shipped. |
| 9 | Diff report | `planned` | Logical diff vs prior version (§5); generator not yet shipped. |
| 10 | Threat model | `manual` | Per-pack; sized to risk (high-risk packs get a fuller model — §6). |
| 11 | License check | `manual` | Reject framework/source content with an incompatible licence. Engineering check, not legal attestation. |
| 12 | Source freshness check | `manual` | Flag references that have expired or changed upstream. |
| 13 | PII / secrets scan | `planned` | Scan candidate outputs **and** build logs; scanner not yet shipped. |
| 14 | Private / public boundary check | `manual` | No internal codename / confidential structure in any public-facing field. |
| 15 | Determinism & reproducibility checks | `tool` (partial) | Pack-level hash verification shipped: [`scripts/verify_xklickd_skill_packs.py`](../../../scripts/verify_xklickd_skill_packs.py). Build-level reproducibility record is `planned` (§7). |
| 16 | Human / agent premium pass | `manual`, gated | Last layer only, post-audit, if requested (§2). |
| 17 | Release candidate | `manual` | Promote `reviewed → release_candidate` (§4). Triggers no public release. |
| 18 | Stable promotion or rejection | `manual` | Promote `release_candidate → stable` or reject. Gated by RFC-009 §8 (all ten criteria) + the acceptance checklist. |

> No stage above is claimed as automated unless its row says `tool`. Stages marked `planned` are specification only and must not be presented as working automation.

### 3.1 Required context-graph shape

Every premium candidate must carry a context graph with at least:

- **Nodes:** `memory`, `competency`, `skill`, `evidence`, `policy`, `action`, `agent`, `risk`.
- **Edges:** `supports`, `contradicts`, `supersedes`, `requires_veto`, `activates_skill`, `depends_on`, `derived_from`, `decays_to`, `promotes_to`, `handoff_to`, `blocks_unless`, `enforces`.
- **Traversal flow:** `task → intent → competencies → skills → memory → evidence → policy/veto → minimal context → response → audit`.

The graph is the artefact's reasoning spine; §5's diff operates over it.

---

## 4. Version lineage

A candidate moves through an explicit lineage:

```text
candidate → reviewed → release_candidate → stable
```

Off-path states:

- **`deprecated`** — a previously-stable pack marked obsolete (§6). Stays resolvable for lineage, not offered as current.
- **`rolled_back`** — a promoted candidate later judged bad and withdrawn (§6).

Every transition is recorded in the audit-trail index (§10). No transition implies a public release, tag, DOI, or catalog exposure — those remain separately gated (RFC-009 §7).

---

## 5. Logical diff report

The diff report compares the previous version to the new candidate **over the context graph and the validation surface**, not just text:

- Added / removed / changed competencies, gates, evidence rules, and graph edges.
- Any change to gate defaults or human-authority posture is highlighted.

> **Gate-lowering is a hard fail.** If a candidate lowers a user's effective gate or weakens the human-authority layer relative to the prior version, the diff report fails the candidate. This mirrors RFC-009 §8 criterion 8.

---

## 6. Rollback, deprecation, approval revocation, threat-model sizing

- **Rollback protocol.** Withdraw a promoted candidate later judged bad: set state `rolled_back`, record reason + prior `output_hash` in the audit index, and restore the last-known-good `stable` as current. No silent overwrite.
- **Deprecation protocol.** Mark a pack obsolete: state `deprecated`, with a successor pointer when one exists. Deprecated packs remain hash-resolvable for lineage.
- **Approval revocation.** A prior "go" can be revoked: record the revocation against the approval id in the audit index; the candidate drops back to `reviewed`.
- **Threat-model sizing.** Every pack gets a threat model (stage 10). High-risk packs (e.g. `security`, `legal`) get a fuller model and, optionally, a stricter reviewer rule (per RFC-009 §11 open-decision 5). Sizing is documented, not assumed.

---

## 7. Determinism and reproducibility

- **Determinism.** The same inputs MUST produce the same output hash on two runs. Pack-level hashing is shipped today via [`scripts/verify_xklickd_skill_packs.py`](../../../scripts/verify_xklickd_skill_packs.py) (SHA-256 over `.klickd` bytes vs the manifest).
- **Reproducible build.** The same build request (`input_hash`) should produce the same candidate (`output_hash`). Each candidate records an `input_hash → output_hash` pair in the audit index (§10).
- **Honest bound.** The build-level reproducibility *record* is `planned` (stage 15) — the hash *primitive* exists and is shipped; the end-to-end build runner that emits the record does not yet exist. Do not claim full reproducible builds today.

---

## 8. Anti-mirage protocol

This is the load-bearing integrity rule of the supply chain.

When the supply chain is being tested or run, **no agent may silently compensate for the chain's work.** The agent's permitted actions are exactly:

1. **Configure** the build request.
2. **Launch** the chain.
3. **Audit** the output.
4. **Document** the gap between what the chain produced and the reference.
5. **Premium-pass** the candidate — **only after the audit, and only if explicitly requested** (§2).

A run that produces little, produces a thin pack, or fails is a **valid result** and must be reported as such. A failing or thin run must never be quietly hand-finished and reported as a success of the chain. The point of the chain is to reveal how much it actually automates; masking that defeats the measurement and repeats the trust incident the brief was written to prevent.

---

## 9. Benchmark intent

Validation compares three things:

1. A reference pack built manually by an agent.
2. A candidate generated by the supply chain (the design target is 70–80% of the work, *not* a guarantee).
3. The candidate after a gated premium pass (§2).

Measured against: foundation/transversal coverage, graph coherence, governance/security accuracy, evidence binding, absence of internal-name/confidential leakage, determinism, reproducibility, editorial quality, and ability to pass the hell tests.

> **Benchmarks must hunt for faults, not confirm success.** A benchmark designed to pass is not evidence. See [`benchmarks/v4.1/`](../../../benchmarks/v4.1/) — the CI workflows there are explicitly no-publish / no-tag.

---

## 10. Audit-trail index

An **append-only** index records every build, approval, rejection, promotion, rollback, deprecation, and revocation, keyed by candidate id and approval id, each carrying its `input_hash`, `output_hash`, state transition, timestamp, and reason. The index is consultable and is the single source of truth for lineage (§4) and revocation (§6).

> The audit index as a shipped, queryable artefact is `planned`. The hash primitives it would record exist today (§7); the index writer does not.

### 10.1 Internal serial fingerprint

A subtle, private serial fingerprint supports internal traceability / anti-cloning. It is **security-internal only**: documented solely in internal security material, never exposed on any public surface, and intentionally not described here. Its existence is noted so reviewers know the boundary; its construction is out of scope for this public document.

---

## 11. Pointers

- Artefact contract: [`RFC-009-chimera-v4.1.md`](../RFC-009-chimera-v4.1.md) (§5 architecture, §8/§8.1 validation).
- Truth boundary (load + hash-verify): [`skill-loader-protocol.md`](../../integrations/skill-loader-protocol.md).
- Operator quickstart (human or agent): [`packs/QUICKSTART.md`](./packs/QUICKSTART.md).
- Pack scope + validation summary: [`README.md`](./README.md).
- Concrete pack scaffolds: [`packs/README.md`](./packs/README.md).
- Shipped tooling: [`scripts/verify_xklickd_skill_packs.py`](../../../scripts/verify_xklickd_skill_packs.py), [`scripts/validate_v4_1_candidate_mapping.py`](../../../scripts/validate_v4_1_candidate_mapping.py).
- Benchmark harness (no-publish / no-tag): [`benchmarks/v4.1/`](../../../benchmarks/v4.1/).
