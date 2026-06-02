# x.klickd supply-chain quickstart — build & audit a candidate pack

> **Status:** Draft · **NON-NORMATIVE** · operator guide for [`../SUPPLY_CHAIN.md`](../SUPPLY_CHAIN.md).
> **Triggers no release.** Nothing here publishes, deploys, tags, or assigns a DOI.
> **Internal naming.** Use the public name **`x.klickd`** in everything you produce. Do not write the internal codename into any pack field or public surface.

This is the operator path — usable by a **human or an agent** — for running the supply chain on one candidate `carrier_pack`. It is a build-and-audit loop, not a publish flow. For the full process and the per-stage `tool` / `manual` / `planned` honesty labels, read [`../SUPPLY_CHAIN.md`](../SUPPLY_CHAIN.md) first.

---

## Truth boundary (read this before you say "it works")

A pack is **loaded / used** only when both are true:

```text
artifact_loaded == true   AND   sha256_matches_manifest == true
```

A catalog row, a stub, a routing placeholder, or a doc page is **not** a loaded skill. If you cannot show both flags true, do not claim the pack is in use. See [`../../../integrations/skill-loader-protocol.md`](../../../integrations/skill-loader-protocol.md).

---

## The 5-step loop

1. **Configure the build request** (config only — no PII, no secrets). Pick the pack id `x.klickd/<name>`, framework backbone, track (P0/P1), tier (Lite/Pro). This fixes the `input_hash`.
2. **Launch the chain.** Run the available pipeline stages (§3 of the spec). Stages marked `planned` are not runnable yet — note them, don't fake them.
3. **Audit the output.** Verify artefacts and hashes with the shipped tooling (below). Check graph coverage, gates, evidence binding, and that no internal name leaked.
4. **Document the gap.** Write down what the chain produced vs the reference, honestly. A thin or failing run is a valid result (anti-mirage rule, §8 of the spec).
5. **Premium pass — only if requested, only after the audit.** Lift the final layer to reference quality. Never run this before the audit; never use it to mask a failed build.

---

## Multi-agent role split

If you run this with more than one agent, keep the roles separate so the audit stays honest:

| Role | Does | Must NOT |
|---|---|---|
| **Builder** | Configures the build request, launches the chain. | Hand-finish output and call it the chain's work. |
| **Auditor** | Verifies artefacts + hashes, checks graph/gates/evidence/leaks, documents the gap. | Edit the candidate to make it pass. |
| **Premium** | Last-layer pass, only after audit + only if requested. | Re-run earlier stages silently; touch anything before the audit exists. |

The separation is the safeguard: the builder cannot grade itself, and the premium pass cannot pre-empt the measurement.

---

## Shipped verification commands (no install needed)

```bash
# 1. Verify all 42 published artifacts parse + hash-match the manifest.
python scripts/verify_xklickd_skill_packs.py verify
#    -> expect: 42 verified (8 Lite, 34 Pro), all SHA-256 match

# 2. List them.
python scripts/verify_xklickd_skill_packs.py list

# 3. Load + hash-verify one (the artifact_loaded + sha256 contract).
python scripts/verify_xklickd_skill_packs.py load work-assistant

# 4. Validate the candidate↔framework mapping.
python scripts/validate_v4_1_candidate_mapping.py
```

These are dependency-free and read the public artifacts directly. They are the concrete backing for stage 3 (mapping) and stage 15 (pack-level determinism) of the pipeline.

---

## Pre-done checklist

Before you call a candidate done, confirm:

- [ ] Build request was config-only (no PII / secrets).
- [ ] Verifier passes (`verify` exits 0; hashes match).
- [ ] Candidate mapping validates.
- [ ] Context-graph nodes/edges present (spec §3.1).
- [ ] Gate defaults + human-authority posture declared; no gate lowered.
- [ ] Evidence grounding rule on every claim.
- [ ] No internal codename / confidential structure in any public-facing field.
- [ ] Gap documented honestly; `planned` stages not presented as automated.
- [ ] Premium pass (if any) ran **after** the audit and was explicitly requested.
- [ ] No publish / tag / DOI / catalog action taken.

---

## Pointers

- Full process spec: [`../SUPPLY_CHAIN.md`](../SUPPLY_CHAIN.md)
- Artefact contract: [`../../RFC-009-chimera-v4.1.md`](../../RFC-009-chimera-v4.1.md) (§8 validation)
- Truth boundary: [`../../../integrations/skill-loader-protocol.md`](../../../integrations/skill-loader-protocol.md)
- Pack index: [`./README.md`](./README.md)
- Benchmark harness: [`../../../../benchmarks/v4.1/`](../../../../benchmarks/v4.1/)
