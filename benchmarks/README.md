# .klickd Format — Empirical Benchmark

**DOI:** [10.5281/zenodo.20297686](https://doi.org/10.5281/zenodo.20297686)  
**Format version:** .klickd v3.1.2  
**Date:** May 19, 2026  
**Total simulations:** 46  
**Total tokens consumed:** 328,860

---

> **Related — work in progress:** [RFC-003 — Context Cost Benchmark](./context_cost/RFC.md) (Draft) defines a complementary, *cost*-oriented benchmark that measures the token / latency / friction cost of re-supplying context, with and without `.klickd`. This README documents the existing *quality* benchmark.

## What This Benchmark Is

This benchmark empirically measures the value of the `.klickd` format as a portable, encrypted AI memory layer. The core question:

> When a student resumes a learning session — possibly on a different AI model — does injecting a `.klickd` context file produce better continuity than starting without context?

Each simulation runs as follows:
1. **Session 1** — 4 pedagogical exchanges on a specific topic
2. **Interruption** — simulating the student closing the app
3. **Session 2** — 2 resume exchanges, with or without `.klickd` context injection

The `.klickd` payload is injected into the model's system prompt via `build_system_prompt()` from `load_klickd.py`, which wraps context in a `<UserContext>` block prepended to the base system prompt (§12 of the spec — highest authority).

---

## Models Tested

| Model | Provider | Role in benchmark |
|---|---|---|
| `llama-3.3-70b-versatile` | Groq | Primary model (Phase 1 + switch tests) |
| `llama-3.1-8b-instant` | Groq | Lightweight / downgrade target |
| `gemma2-9b-it` | Groq | **Decommissioned** during testing — results invalid |
| `gemini-2.5-flash` | Google (Gemini API) | Cross-provider switch target |

---

## Student Profiles Tested

11 distinct academic profiles across a wide range of domains and levels:

| Profile | Level | Domain |
|---|---|---|
| Sofia | L2 Droit | Contract law — vices du consentement |
| Thomas | BTS Informatique | Python debugging + sorting algorithms |
| Camille | Terminale | Philosophy dissertation — freedom vs. illusion |
| Léo | L3 Économie | Macroeconomics — ECB inflation policy |
| Amira | L1 Anglais | Essay writing — 1984 vs. Brave New World |
| Noah | Prépa MPSI | Newtonian mechanics — inclined plane + friction |
| Jade | Master 1 Biologie | Scientific writing — abstract for HSP70/Arabidopsis |
| Rayan | BEP Électrotechnique | RC circuit — charge and discharge |
| Théo | Master 2 Physique | **Advanced astrophysics** — black holes, Hawking radiation, Schwarzschild metric |
| Clara | L3 Philosophie | **Complex philosophy** — Kant ethics, Husserl phenomenology, Wittgenstein language |
| Emma | CM2 (primary) | **Simple subjects** — multiplication tables, verb conjugation |
| Alex | Mixed | **Escalation stress test** — tables → thermodynamics → Kant (same session) |
| Maxime | L2 Physique + philosophy | **4-subject stress test** — tables, black holes, Kant, entropy (mid-session cut) |

---

## Key Test Types

### 1. Standard Benchmark (Phase 1)
All 11 profiles run on `llama-3.3-70b-versatile` for both Session 1 and Session 2, with and without `.klickd`. Establishes the baseline improvement from context injection.

### 2. Cross-Model Switch Tests (Phase 2)
The same `.klickd` payload is used across Sessions 1 and 2 on different models. This tests whether context **survives a model change** — the primary use case for portable AI memory.

Switches tested:
- `llama-3.3-70b` → `gemini-2.5-flash`
- `gemini-2.5-flash` → `llama-3.3-70b`
- `llama-3.3-70b` → `llama-3.1-8b` (downgrade)
- `llama-3.1-8b` → `llama-3.3-70b` (upgrade)
- `gemini-2.5-flash` → `gemma2-9b-it` (decommissioned)
- Extended: astrophysics, complex philosophy, and multi-subject profiles across switches

### 3. Stress Test (Phase 3)
A single session covers 4 unrelated subjects in escalating complexity (primary maths → black holes → Kantian ethics → thermodynamics), interrupted mid-way through subject 4. The session is then resumed on a different model. Tests whether `.klickd` can reconstruct a multi-domain context across a model switch.

---

## Results Summary

| Metric | WITH .klickd | WITHOUT .klickd | Delta |
|---|---|---|---|
| Context restoration rate | **73%** | **39%** | **+34 pp** |
| "Perfect" resume quality | **70%** (16/23) | **26%** (6/23) | **+44 pp** |
| "Partial" quality | 9% (2/23) | 30% (7/23) | — |
| "None" quality | 22% (5/23) | 43% (10/23) | — |
| Avg. prompt tokens S2 | ~699 | ~130 | +569 tokens overhead |

### Cross-model switch — key finding

| Switch direction | Context restored WITH .klickd | Context restored WITHOUT |
|---|---|---|
| Same model (llama-3.3-70b → llama-3.3-70b) | 92% | 50% |
| gemini → llama (any size) | **100%** | 67% |
| llama-3.3-70b → llama-3.1-8b (downgrade) | **100%** | **0%** |
| llama-3.1-8b → llama-3.3-70b (upgrade) | **100%** | **0%** |
| llama → gemini | 0% | 0% |

> **Note on llama → gemini (0%):** Gemini Flash assimilates the `<UserContext>` block but does not cite specific prior session elements explicitly in its response. The context is present (prompt token count is ~5× higher with `.klickd`), but the evaluation method (keyword detection) scores it as 0. A semantic similarity evaluation would likely show better results.

### Token overhead
~570 additional prompt tokens per session — approximately $0.0004 at Groq pricing (negligible).

---

## Repository Structure

```
benchmarks/
├── README.md                  — this file
├── RAPPORT_FINAL.md           — full French-language analysis report
├── checkpoints/
│   ├── CHECKPOINT_18_37.md
│   ├── CHECKPOINT_18_40.md
│   ├── CHECKPOINT_18_42.md
│   ├── CHECKPOINT_18_48.md
│   ├── CHECKPOINT_18_50.md
│   └── CHECKPOINT_FINAL.md
└── raw/
    ├── summary.json           — all 46 results as JSON array
    ├── sofia_droit_with_klickd.json
    ├── sofia_droit_no_klickd.json
    └── ... (one file per simulation)
```

---

## Technical Notes

- **Library used:** `klickdskill_push/load_klickd.py` — `build_system_prompt(payload, base_system)` injects `<UserContext>` before the base system prompt
- **Encryption:** Not applied in simulation (payload used directly as dict); in production, `.klickd` files are AES-256-GCM encrypted with Argon2id key derivation
- **Rate limiting:** 1.8s sleep between API calls, 10–20s backoff on HTTP 429
- **`gemma2-9b-it`:** Decommissioned on Groq during the test window — all 2 simulations targeting this model returned HTTP 400 errors and are excluded from statistics
- **Evaluation method:** Keyword-based context detection (conservative, especially for Gemini)

---

*Benchmark conducted by the Klickd/Luxlearn team — Made in Luxembourg 🇱🇺*  
*App: [klickd.app](https://klickd.app) | DOI: [10.5281/zenodo.20297686](https://doi.org/10.5281/zenodo.20297686)*
