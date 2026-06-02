# `xklickd_internal_skill_v4_2` — internal target mapping (DRAFT, NOT a public release)

| | |
|---|---|
| **Status** | **Internal · DRAFT · TARGET · NON-NORMATIVE** |
| **Track** | `xklickd_internal_skill_v4_2` — internal target mapping, ahead of internal production |
| **Created** | 2026-06-02 |
| **Scope** | Internal documentation only. This is the **target** internal mapping for v4.2; it is **not** a public release artefact. |
| **Relates to** | [`docs/chimera/README_V4_1.md`](../chimera/README_V4_1.md) · [`docs/chimera/V4_1_SKILL_CANDIDATE_MAPPING.md`](../chimera/V4_1_SKILL_CANDIDATE_MAPPING.md) · [`docs/chimera/V4_1_COMPETENCY_IDENTIFICATION_PROTOCOL.md`](../chimera/V4_1_COMPETENCY_IDENTIFICATION_PROTOCOL.md) · [`docs/rfcs/RFC-010-pack-memory-compression.md`](../rfcs/RFC-010-pack-memory-compression.md) |

> **This document is non-normative and triggers no release.** It is **internal documentation only**. It does **not** modify `SPEC.md`, any v4.0 GA schema, any SDK, any vector, any lock file, or the status of any RFC. It introduces **no new normative field**. It does **not** publish anything: no tag, no `latest` on npm/PyPI, no DOI on Zenodo, no IANA action, no GitHub Release, no SDK bump, no `/klickdskill` catalog change.
>
> **The public `.klickd` track remains v4.0.0 GA, with the 42 `x.klickd` artefacts under `examples/v4.1/x-klickd-skills/{lite,pro}/` framed as v4.1 candidates.** Nothing here promotes any public artefact to v4.2 and nothing here claims a public v4.2 release. v4.2 is **in preparation**; see [`docs/public/X_KLICKD_SITE_COPY.md`](../public/X_KLICKD_SITE_COPY.md) §7 ("v4.2 in preparation", no date promised).
>
> **The internal track name (`xklickd_internal_skill_v4_2`) MUST NOT leak into any public-facing surface.** Public wording remains `x.klickd`. This is a continuation of the v4.1 QA gate that forbids internal-name / host-side leakage (QA-G13 in [`docs/chimera/V4_1_SKILL_QA_PROTOCOL.md`](../chimera/V4_1_SKILL_QA_PROTOCOL.md)).
>
> **Supply-chain completeness is NOT claimed.** The `skill_lifecycle` section below describes the *target* lifecycle layout; it is not an assertion that every lifecycle stage is implemented, populated, or verified.

---

## 0. What this document is and is not

`docs/internal/` holds **internal** target mappings that precede internal production. This document records the v4.2 *target* internal skill mapping so reviewers can argue with **structure, naming, governance symmetry, and layer interactions** before any internal build lands.

This document **is**:

- an internal **target** for the v4.2 skill mapping shape;
- a record of the validated corrections that motivated v4.2 (governance symmetry, lifecycle rename, graph bindings, naming harmonisation, explicit interactions);
- a planning surface, comparable to `docs/chimera/` for v4.1 but scoped to the internal track.

This document **is not**:

- a public release or release announcement;
- a normative spec, schema, or SDK contract;
- a claim that any public `x.klickd` artefact is v4.2;
- a claim that the skill supply chain / lifecycle is complete.

---

## 1. Target top-level structure

The v4.2 internal skill mapping targets the following top-level layout. Each node is a documentation layer in the internal mapping, not a shipped artefact.

```text
xklickd_internal_skill_v4_2
├── metadata
├── competency_architecture
├── memory_system
├── governance_system
├── memory_governance
├── runtime
├── context_graph
├── interactions
├── evidence
├── security
├── audit
├── skill_lifecycle
└── output_contract
```

Two changes from earlier internal drafts are deliberate and validated:

1. **`supply_chain` is renamed conceptually to `skill_lifecycle`.** The earlier `supply_chain` label over-claimed a complete, audited provenance chain. `skill_lifecycle` names what the layer actually documents: the build → validate → promote → deprecate → release lifecycle of a skill, without asserting end-to-end supply-chain completeness. See §6.
2. **`interactions` is added as a first-class top-level layer** so the way layers communicate is documented explicitly rather than implied. See §5.

---

## 2. `governance_system` — detailed and symmetric with `memory_system`

`governance_system` is brought up to the same level of internal detail as `memory_system`, so the two control planes (what the agent remembers vs. what the agent is allowed to do) are documented symmetrically.

```text
governance_system
├── authority_hierarchy
├── human_veto
├── consent_rules
├── risk_levels
├── action_gates
├── non_lowerable_rules
├── escalation_rules
├── approval_lifecycle
├── revocation_rules
├── policy_conflict_resolution
└── governance_audit
```

| Sub-layer | Internal purpose |
|---|---|
| `authority_hierarchy` | Who/what can authorise an action class, and the precedence order between authorities. |
| `human_veto` | The point where a human can block an action before it executes; never lowerable by an agent. |
| `consent_rules` | What the user must have consented to for a given action class to be permitted. |
| `risk_levels` | The risk taxonomy that gates actions; higher risk requires stronger gates. |
| `action_gates` | The concrete preconditions an action must clear before execution. |
| `non_lowerable_rules` | Rules an agent can never relax, even under instruction or memory pressure. |
| `escalation_rules` | When and how a decision is escalated (e.g. to human veto). |
| `approval_lifecycle` | The states an approval moves through (requested → granted/denied → expired). |
| `revocation_rules` | How a previously granted approval is revoked and what that invalidates. |
| `policy_conflict_resolution` | Deterministic resolution when two policies disagree. |
| `governance_audit` | The audit surface specific to governance decisions, feeding the shared `audit` layer. |

### 2.1 Symmetry with `memory_system` and `memory_governance`

`memory_governance` remains the bridge layer: it is where `memory_system` (retrieval, write candidates, retention) meets `governance_system` (consent, risk, veto). The symmetry intent is: every memory write that could influence an action is subject to governance, and every governance decision that consults memory is auditable. `memory_governance` is intentionally kept separate from both parents so the bridge contract is reviewable on its own.

---

## 3. Naming harmonisation (competency / domain)

The following names are harmonised in the v4.2 internal mapping for consistency with the v4.1 competency vocabulary in [`docs/chimera/V4_1_COMPETENCY_IDENTIFICATION_PROTOCOL.md`](../chimera/V4_1_COMPETENCY_IDENTIFICATION_PROTOCOL.md):

| Section | Was | Now (v4.2 internal target) |
|---|---|---|
| top-level | `competency_architecture` | `competency_architecture` (unchanged — the umbrella section) |
| foundation | — | `competency_core` (the shared foundation competency) |
| primary domain | `domain_primary` | `primary_domain_competencies` |
| secondary domain | `domain_secondary` | `secondary_domain_competencies` |
| risk | `domain_risk_model` | `domain_risk_profile` |
| output | `domain_output_contract` | `domain_output_requirements` |

`competency_architecture` targets the following internal shape:

```text
competency_architecture
├── competency_core
├── primary_domain_competencies
├── secondary_domain_competencies
├── domain_risk_profile
└── domain_output_requirements
```

Rationale: the previous `domain_*` names mixed scope (which domain) with kind (what the field is). The harmonised names lead with kind (`*_domain_competencies`, `domain_risk_profile`, `domain_output_requirements`) so they read consistently and so `domain_output_requirements` is clearly distinct from the top-level `output_contract` (§7).

---

## 4. `context_graph`

`context_graph` is the layer the runtime traverses to resolve what is in scope for a task: competencies, memory entries, evidence, policy nodes, and action nodes, plus the edges between them. v4.2 makes the graph the explicit binding target for `output_contract` (§7) so that an output is tied to the graph nodes that justify it.

---

## 5. `interactions` — how the layers communicate

`interactions` is a new top-level layer that documents the directed flows between layers. It exists so the communication contract is explicit and reviewable, instead of being implied by prose scattered across other sections.

```text
interactions
├── task_to_competency_flow
├── competency_to_memory_flow
├── memory_to_context_graph_flow
├── context_graph_to_policy_flow
├── policy_to_output_contract_flow
├── output_to_audit_flow
└── lifecycle_to_runtime_flow
```

| Flow | From → To | What moves |
|---|---|---|
| `task_to_competency_flow` | task intake → `competency_architecture` | Detected intent activates the relevant competencies. |
| `competency_to_memory_flow` | `competency_architecture` → `memory_system` | Active competencies scope which memory is retrieved. |
| `memory_to_context_graph_flow` | `memory_system` → `context_graph` | Retrieved memory is placed as nodes/edges for traversal. |
| `context_graph_to_policy_flow` | `context_graph` → `governance_system` | Graph traversal surfaces the policy nodes that gate the task. |
| `policy_to_output_contract_flow` | `governance_system` → `output_contract` | Policy evaluation constrains what outputs are allowed/forbidden. |
| `output_to_audit_flow` | `output_contract` → `audit` | Every checked output emits an audit event. |
| `lifecycle_to_runtime_flow` | `skill_lifecycle` → `runtime` | Only promoted skills are loadable by the runtime; lifecycle state gates availability. |

### 5.1 Canonical flow

The canonical end-to-end flow for a single task is:

```text
user_task
→ intent_detection
→ competency_activation
→ memory_retrieval
→ context_graph_traversal
→ evidence_resolution
→ policy_evaluation
→ output_contract_check
→ human_veto_if_required
→ response_or_action
→ audit_event
→ memory_update_candidate
```

Notes:

- `human_veto_if_required` is gated by `governance_system.human_veto` and `governance_system.risk_levels`; it is **not** lowerable by an agent.
- `memory_update_candidate` is a *candidate*, not a committed write — it is subject to `memory_governance` before it can influence future tasks.
- `evidence_resolution` reads from the `evidence` layer; an output that requires citations (see `output_contract.required_citations`) cannot pass `output_contract_check` without resolved evidence.

---

## 6. `skill_lifecycle` (formerly `supply_chain`)

Renamed conceptually from `supply_chain` to `skill_lifecycle`. The layer documents the lifecycle of a skill from build request to release/deprecation. **It does not claim that the supply chain is complete or that every stage is implemented or verified.**

```text
skill_lifecycle
├── build_request
├── source_manifest
├── generated_candidate
├── validation_pipeline
├── audit_trail_index
├── determinism_record
├── logical_diff_report
├── source_license_report
├── threat_model_report
├── benchmark_report
├── premium_pass_report
├── promotion_gate
├── rollback_protocol
├── deprecation_protocol
└── release_record
```

| Stage | Internal purpose |
|---|---|
| `build_request` | The request that initiates a skill build. |
| `source_manifest` | The declared sources/competency anchors the build draws on. |
| `generated_candidate` | The produced candidate skill, pre-validation. |
| `validation_pipeline` | The ordered checks a candidate must pass. |
| `audit_trail_index` | Index into audit events produced during the build. |
| `determinism_record` | Evidence that the build is reproducible. |
| `logical_diff_report` | What changed logically versus the prior version. |
| `source_license_report` | Licence status of the declared sources. |
| `threat_model_report` | Threat-model review for the candidate. |
| `benchmark_report` | Benchmark results for the candidate. |
| `premium_pass_report` | Premium/extended review pass results. |
| `promotion_gate` | The gate a candidate must clear to be promoted. |
| `rollback_protocol` | How a promoted skill is rolled back. |
| `deprecation_protocol` | How a skill is retired. |
| `release_record` | Internal record of an internal promotion. **Not** a public release; no tag/DOI/package action. |

> `release_record` here is an **internal** lifecycle record only. It does not correspond to any public tag, npm/PyPI `latest`, Zenodo DOI, or GitHub Release, and must never be presented as one.

---

## 7. `output_contract` with `graph_bindings`

`output_contract` is extended with a `graph_bindings` sub-layer so that the contract is wired to `context_graph` (§4): every contracted output declares which graph nodes/edges it creates or requires.

```text
output_contract
├── allowed_outputs
├── forbidden_outputs
├── required_citations
├── required_uncertainty_markers
├── required_handoff_summary
├── required_audit_event
└── graph_bindings
    ├── creates_action_node
    ├── requires_policy_node
    ├── requires_evidence_node
    ├── may_trigger_veto_edge
    └── writes_audit_edge
```

| `graph_bindings` field | Meaning |
|---|---|
| `creates_action_node` | The output produces an action node in `context_graph`. |
| `requires_policy_node` | A policy node must exist and be satisfied (links to `governance_system`). |
| `requires_evidence_node` | An evidence node must be resolved (links to `evidence`). |
| `may_trigger_veto_edge` | The output may create an edge to `governance_system.human_veto`. |
| `writes_audit_edge` | The output writes an edge into the `audit` layer. |

This closes the loop with the canonical flow (§5.1): `output_contract_check` is the step that verifies these bindings before `human_veto_if_required` and `response_or_action`.

---

## 8. Out of scope / explicit non-claims

- **No public release.** Public `.klickd` is v4.0.0 GA; the 42 `x.klickd` artefacts are v4.1 candidates. This document does not change that and does not announce a public v4.2.
- **No artefact changes.** No file under `examples/v4.1/x-klickd-skills/` is modified by this document. No version, DOI, release note, or public README is touched.
- **No supply-chain completeness claim.** `skill_lifecycle` is a target layout, not an assertion that the lifecycle is fully built or verified.
- **No internal-name leakage.** `xklickd_internal_skill_v4_2` is an internal track name and must not appear on public surfaces.
- **Repository boundary.** This document is scoped to `Davincc77/klickdskill` only. It does not reference or modify any other repository.
