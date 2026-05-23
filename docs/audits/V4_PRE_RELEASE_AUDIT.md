# `.klickd` — Pre-V4 Release Audit (deuxpeccable)

> **Scope:** end-to-end repository audit conducted on 2026-05-23, *before* any V4 GA release work.
> **Constraint:** read-only audit. No npm/PyPI/Zenodo publication, no tagging, no release. Docs-only safe fixes may be proposed as a separate PR.
> **Audience:** maintainer (Vince C.), release manager, future contributors.

---

## Executive summary

| Dimension | Score | Notes |
|---|---|---|
| GitHub hygiene | **A** | Zero open PRs/issues, 24/24 PRs merged, all CI green, releases properly marked. |
| Docs coherence | **B+** | Strong narrative + RFC structure; minor SPEC §33 / CHANGELOG / example drift on wire `klickd_version`. |
| Package metadata | **B−** | npm dist-tags impeccable (`latest=3.5.1`, `preview=4.0.0-preview.1`). **PyPI gap**: latest is `3.0.0`, not `3.5.1`. |
| Security hygiene | **A** | No secrets, no `.env`, no keys, no leaked credentials. All "secret-like" hits are documentation patterns or self-referential greps. |
| Tests / vectors | **A** | Python 59/59, JS 42/42 (incl. v4 preview round-trip). RFC-003 benchmark fixtures validate locally. |
| UX / adoption | **A−** | UX spec is well-articulated. v3.5.1 install path works for npm; PyPI install resolves to an older version (see P1). |
| OSS professionalism | **B+** | License, citation, security, contributing, acknowledgements all in place. Missing: issue templates, PR template, CODE_OF_CONDUCT. |
| Link hygiene | **A** | All sampled external links (`klickd.app`, Zenodo DOIs, GitHub) return 200. |

**Overall release readiness for V4 GA: B+ (good, not "deuxpeccable" yet).** The v4 preview track is in excellent shape. The single highest-leverage fix before GA is the **PyPI / v3.5.1 publication gap** (P0). Everything else is incremental polish.

---

## 1. GitHub hygiene — A

- **Open PRs / issues:** 0 open PRs, 0 open issues. All 24 merged PRs since #1 (P0 conformance) are present and accounted for.
- **Releases:** `v3.5.1` correctly marked **Latest**, `v4.0.0-preview.1` correctly marked **Pre-release**. Older `v3.0.0`, `v3.1.0` present.
- **Tags:** `v3.0.0`, `v3.1.0`, `v3.5.1`, `v4.0.0-preview.1` — coherent with releases.
- **Actions:** Last 15 runs green except 3 historical PyPI Trusted-Publisher failures (see §3 below).
- **Branches:** clean — only `main` after each merge.

No action required.

---

## 2. Docs coherence — B+

### 2.1 Strengths

- README narrative ("Your AI forgets you. Every. Single. Session.") is tight, benchmark-led, with a credible comparison table and prior-art statement.
- CHANGELOG explicitly versions the v4-preview registry mapping (git tag / npm `preview` / PyPI `a1` / Zenodo deferred).
- SPEC.md §33 documents the preview track and the dual-reader contract (v3.x readers ignore; v4 preview readers preserve unknown fields).
- `docs/ux/V4-UX-SPEC.md` is a real product/UX spec, not just an internal note. UX principles (P1–P8) are crisp.
- `docs/rfcs/` is well-organised. RFC-001/002/003/004 all present, statuses ("Draft") are consistent with non-GA stance.
- `ACKNOWLEDGEMENTS.md` attributes community insights (`VoltageGPU`, `cart0ne`, `TxDesk`) with discoverable links back to source threads.

### 2.2 Drift: wire `klickd_version` for v4 preview

The repository has **two coherent answers** for the v4-preview wire envelope, both stated normatively in different places:

| Source | Says |
|---|---|
| `CHANGELOG.md` lines 14–17, 66–67 | Wire envelope stays at `klickd_version="3.0"`; payload carries `payload_schema_version="4.0.0-preview.1"`. |
| `tests/vectors_v40_preview.json` | All fixtures use `klickd_version: "3.0"` + `payload_schema_version: "4.0.0-preview.1"`. |
| `SPEC.md` §33 line 1855 (table) | "Files claiming `klickd_version: "4.0"` are PREVIEW." |
| `SPEC.md` §33 line 1900 (example) | Example uses `"klickd_version": "4.0"`. |
| `examples/v4-preview/minimal.klickd` | Uses `"klickd_version": "4.0"`. |

The **vectors** and **CHANGELOG** are aligned and reflect the actual implementation. The **SPEC §33 example** and **`examples/v4-preview/minimal.klickd`** drifted to `"4.0"`. A v4-preview reader implemented strictly to the SPEC §33 example would diverge from the published vectors.

**Severity: P1 (docs/example/spec coherence).** Not a publication blocker, but exactly the kind of inconsistency that produces an issue 48 hours after GA.

**Recommended fix:** pick the canonical answer (the CHANGELOG/vectors line — wire stays `"3.0"`, payload opts in via `payload_schema_version`), then update SPEC §33 example and `examples/v4-preview/minimal.klickd` accordingly. Document the rationale in the SPEC.

### 2.3 Minor

- `examples/minimal.klickd` declares `"klickd_version": "3.4"` but README's example column says "valid v3.5". This is acceptable per SPEC (3.4 is a valid v3 envelope), but a casual reader will hesitate. Either bump examples to `"3.5"` or soften the README cell to "valid v3.x".
- Three historical files at root (`SKILL_v25.md`, `SKILL_v30.md`, `SPEC_v30.md`) live alongside the current `SKILL.md` / `SPEC.md`. They take up ~67 KB and are visible from the GitHub front page. Consider moving them under `archive/` or `docs/history/` for V4 GA.

---

## 3. Package metadata — B−

### 3.1 npm — A

- `@klickd/core` versions on registry: `3.0.1`, `3.5.1`, `4.0.0-preview.1`.
- dist-tags: `latest: 3.5.1`, `preview: 4.0.0-preview.1`. **Exactly as the checklist mandates.**
- `npm install @klickd/core` → 3.5.1. `npm install @klickd/core@preview` → 4.0.0-preview.1.
- `packages/@klickd/core/package.json` matches checked-in version (`4.0.0-preview.1` on the preview branch).

No action required.

### 3.2 PyPI — D (PRIMARY P0)

- `klickd` on PyPI has **two** releases: `3.0.0` (latest) and `4.0.0a1` (pre-release).
- `pip install klickd` currently installs **`3.0.0`**, *not* `3.5.1`.
- `CHANGELOG.md` (line 30) and `docs/releases/CHECKLIST_v4_preview.md` (line 140) **both promise** that `pip install klickd` resolves to `3.5.1`. This promise is currently false on the public registry.
- The README install snippet (`pip install klickd`) installs a 1+ generation old `klickd`, which does not match the schemas described in the README.

**Root cause** (from `gh run view 26327324373 --log-failed`): the PyPI Trusted-Publisher exchange fails on `release`-triggered runs with `invalid-publisher: Publisher with matching claims was not found`. The `workflow_dispatch` path succeeded once (which is how `4.0.0a1` got there). v3.5.1 was never published.

**Severity: P0.** This is the single biggest gap between stated and observed reality. It directly breaks the README's first install instruction.

**Recommended fix sequence (do this BEFORE any V4 GA work):**

1. On pypi.org, audit the Trusted Publisher configuration for `klickd`. The current GitHub claim is `repo:Davincc77/klickdskill:environment:pypi` with `workflow_ref` constrained to `refs/tags/v4.0.0-preview.1`. The trusted-publisher claims registered on PyPI are almost certainly tag-constrained, environment-mismatched, or both.
2. Either:
   - Register a tag-agnostic trusted publisher for the `pypi` environment, OR
   - Drop `environment: pypi` and rely on workflow-only matching (see how the npm workflow was simplified in #20).
3. Re-tag / re-release `v3.5.1` (or run a manual `workflow_dispatch` against the existing tag) to publish `klickd==3.5.1` on PyPI under the stable channel.
4. Verify `pip install klickd` resolves to `3.5.1` and `pip install --pre klickd` resolves to `4.0.0a1`.

Until step 4 verifies green, the README and CHANGELOG both contain a false statement about user-facing install behaviour.

---

## 4. Security hygiene — A

- **Secret scan** (`AKIA…`, `sk_live_/sk_test_`, `ghp_/gho_/github_pat_`, `xoxb-`, `AIza…`, `BEGIN PRIVATE KEY`, JWT tri-grams, hard-coded `api_key=`, `secret=`, `password=`, `token=`): **0 real hits**. The one match in `docs/rfcs/v4-media-test-pack.md` is the documented scanning regex itself, not a secret.
- **No `.env*` files.** No `*.pem`, `*.key`, `id_rsa*` anywhere outside `.git/`.
- **No build artefacts.** No `node_modules/`, `__pycache__/`, `dist/`, `build/` in the working tree.
- **`Luxlearn@pm.me`** appears in `SECURITY.md`, `CONTRIBUTING.md`, `PITCH.md`, `packages/pypi/klickd/pyproject.toml`, `packages/@klickd/core/package.json`. This is a public maintainer contact, **intentional**, not a leak.
- **Log files** under `benchmarks/context_cost/fixtures/` are non-normative RFC-003 sample artefacts (clearly labelled "non-normative benchmark fixture" / illustrative data only). No real PII.
- **DOI references** are public — no concern.

No action required.

---

## 5. Tests & vectors — A

- `python verify_vectors.py`: **59/59 PASS** (v2.5, v3.0, advanced, adversarial, v4 preview round-trip).
- `node verify_vectors.mjs` (with `hash-wasm` installed): **42/42 PASS**.
- `python benchmarks/context_cost/runner.py --check`: validates 10 flow messages + 6 continuity facts + artifact-tee fixture.
- RFC-003 edge-case fixtures (migration / tool-failure / multi-session) load cleanly.
- Adversarial pack covers: JSON injection, ethics-block tampering, Argon2id downgrade, cipher mixed-case, agent_instructions size bomb, growth-level overflow, etc.

No action required.

---

## 6. UX & adoption — A−

- README "Try it now" → working playground at `https://klickd.app/playground` (200).
- "Install" → `npm install @klickd/core` resolves 3.5.1 correctly. **`pip install klickd` resolves 3.0.0 (see §3.2).**
- 5 worked examples in `examples/` cover student (FR), professional (EN), family plan, minimal, full.
- `docs/ux/V4-UX-SPEC.md` defines the user-visible promise ("Load context → inspect what matters → resume work") and translates it to UI flows (open & decrypt, inspect, resume, migrate, handoff).
- Schema-validate snippet in README is copy-paste runnable.

**One adoption-path snag:** the README's example column says `minimal.klickd` is "valid v3.5", but the file declares `klickd_version: "3.4"`. Cosmetic but visible.

---

## 7. OSS professionalism — B+

| Item | Status |
|---|---|
| LICENSE (CC0-1.0) | ✅ |
| CITATION.cff | ✅ (v3.5, DOI `10.5281/zenodo.20320480`) |
| `.zenodo.json` | ✅ (v3.5.1 metadata) |
| SECURITY.md | ✅ (responsible-disclosure, threat model, response targets) |
| CONTRIBUTING.md | ✅ (what we welcome, what we don't accept, workflow) |
| ACKNOWLEDGEMENTS.md | ✅ (community insights with attribution) |
| CHANGELOG.md | ✅ (granular, version-mapped) |
| ROADMAP.md | ✅ (shipped / near-term / preview tracks) |
| Issue templates | ❌ Not present |
| PR template | ❌ Not present |
| CODE_OF_CONDUCT.md | ❌ Not present |
| `.github/FUNDING.yml` | ❌ Not present (optional) |

**Severity: P2.** Missing community boilerplate. None of these are GA-blocking; all three together would raise the perceived OSS maturity by one notch.

---

## 8. Link hygiene — A

Sampled `https://klickd.app`, `https://klickd.app/klickdskill`, `https://klickd.app/playground`, `https://doi.org/10.5281/zenodo.20320480`, `https://doi.org/10.5281/zenodo.20262530`, `https://github.com/Davincc77/klickdskill`. All return 200.

DOI references are version-specific:
- Root / concept DOI: `10.5281/zenodo.20262530`.
- v3.5: `10.5281/zenodo.20320480` (CITATION.cff, README badge).
- v3.4.x: `10.5281/zenodo.20302252` (SPEC.md).
- v3.1: `10.5281/zenodo.20297686` (benchmarks/).

These are not contradictions — each version has its own DOI, which is correct Zenodo practice. The concept DOI links all of them.

`Luxlearn` mentions in benchmarks/v32/* are historical (entity name at the time of those benchmark runs) and don't need rewriting unless the project decides to fully retire the `Luxlearn` brand reference. **Recommend**: keep historical reports unchanged; ensure new docs use `Klickd` (already true).

---

## 9. Release-readiness gap to "deuxpeccable" for V4 GA

### P0 — must fix before V4 GA

1. **Publish `klickd==3.5.1` to PyPI.** Currently `pip install klickd` installs `3.0.0`. Root cause is a PyPI Trusted-Publisher config mismatch on `release`-triggered runs (see §3.2 for the exact log evidence). Until fixed, the README contains a false install instruction.

### P1 — strongly recommended before V4 GA

2. **Resolve the v4-preview wire-version drift.** SPEC §33 example and `examples/v4-preview/minimal.klickd` use `klickd_version: "4.0"`. CHANGELOG and `tests/vectors_v40_preview.json` use `klickd_version: "3.0"` + `payload_schema_version: "4.0.0-preview.1"`. Pick one. The vectors-aligned answer is the safer one to canonicalize (it's what the SDKs already round-trip).
3. **Fix the PyPI Trusted-Publisher claim for release-triggered runs.** Even after step 1, the workflow will fail again at the next tag. Either drop the `environment: pypi` constraint or register a tag-agnostic publisher claim on pypi.org.
4. **Update the v4-preview Publication Checklist.** `docs/releases/CHECKLIST_v4_preview.md` sections 1 ("Tagging") and 2 ("GitHub Release") are already done — they should be marked as such, or the checklist should call out that those steps have been executed for the preview and only the publication-action steps (Zenodo, post-pub) remain optional.

### P2 — polish

5. **Reconcile `examples/minimal.klickd`'s `klickd_version: "3.4"`** with the README label "valid v3.5". Either bump the file to `"3.5"` or change the README cell.
6. **Add issue templates, PR template, CODE_OF_CONDUCT.md.** GitHub auto-detects these; perceived OSS maturity goes up.
7. **Archive historical SKILL_v25/SKILL_v30/SPEC_v30 under `archive/` or `docs/history/`** to declutter the repo front page.
8. **Mint the V4 GA Zenodo deposit** when ready, then update `.zenodo.json`, `CITATION.cff`, and the README DOI badge in a single follow-up PR. Do not mint before V4 GA is decided.

---

## 10. Checks actually run by this audit

| Check | Result |
|---|---|
| `git status` / `git log` | clean, recent history coherent |
| `gh pr list --state all`, `gh issue list --state all` | 24 PRs (all merged), 0 issues |
| `gh run list` | last 15 runs green except 3 historical PyPI failures |
| `gh release list`, `git tag -l` | releases ↔ tags ↔ CHANGELOG cross-checked |
| Secret scan (regex sweep) | 0 real hits |
| `find . -name ".env*" / *.pem / *.key / id_rsa*` | 0 hits |
| `find . -name "node_modules / __pycache__ / dist / build"` | 0 hits |
| `python verify_vectors.py` | 59/59 PASS |
| `node verify_vectors.mjs` (with hash-wasm) | 42/42 PASS |
| `python benchmarks/context_cost/runner.py --check` | OK |
| `npm view @klickd/core versions / dist-tags` | confirmed: latest=3.5.1, preview=4.0.0-preview.1 |
| `curl https://pypi.org/pypi/klickd/json` | confirmed: latest=3.0.0 (P0 gap) |
| External link probes (klickd.app, DOI, GitHub) | all 200 |
| `gh run view <failed run> --log-failed` | identified Trusted-Publisher claim mismatch |

---

## 11. Closing assessment

The repository is in genuinely good shape. The v4 preview track has been engineered with admirable restraint — preview is preview, GA is GA, dist-tags reflect that on npm exactly as the checklist promised, and the SPEC explicitly tells v3 readers to ignore preview fields. The benchmarks are reproducible. The tests are honest. The CC0 / open posture is consistent across LICENSE, package metadata, paper, and Zenodo.

The one place where stated and observed reality diverge is **PyPI**. Fix that, fix the wire-version doc drift, and this becomes "deuxpeccable" in the way the maintainer asked for.

— Audit produced 2026-05-23. No npm/PyPI/Zenodo writes were performed. No tag was moved. No release state was altered.
