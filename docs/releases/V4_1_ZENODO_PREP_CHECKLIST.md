# v4.1 Zenodo Preparation Checklist — x.klickd

| | |
|---|---|
| **Status** | **Draft · NON-NORMATIVE · pre-deposit preparation pack** |
| **Audience** | Maintainer (Vince) preparing the v4.1 Zenodo deposit. **No deposit is created by this file.** |
| **Public wording** | `x.klickd` (canonical public name). The internal planning-track codename MUST NOT appear in any public Zenodo metadata, file path, or bundle filename. |
| **Created** | 2026-05-28 |
| **Companion** | [`docs/public/X_KLICKD_ZENODO_DRAFT.md`](../public/X_KLICKD_ZENODO_DRAFT.md) (deposit field draft) · [`/.zenodo.json`](../../.zenodo.json) (current v4.0.0 metadata) · [`scripts/generate_v4_1_zenodo_bundle.sh`](../../scripts/generate_v4_1_zenodo_bundle.sh) (prep helper) · [`scripts/generate_x_klickd_sha256sums.sh`](../../scripts/generate_x_klickd_sha256sums.sh) (skills SHA256SUMS helper). |

> **Hard locks.**
> 1. **No publish actions in this PR or this checklist.** This file describes what would happen *when* Vince decides to mint the v4.1 DOI. Running through it must not by itself create a tag, a release, a npm/PyPI publish, or a Zenodo deposit.
> 2. **`x.klickd` only** in every public-facing field, filename, or directory entry. The internal codename is forbidden.
> 3. **Vince performs the Zenodo deposit.** The maintainer logs in to Zenodo, uploads the bundle, fills the form (or imports `.zenodo.json`), and clicks *Publish*. No automation in this repo performs that step.
> 4. **v4.1 is not GA until tagged.** All bundle artefacts and metadata carry the "candidate / not for unmodified production use" disclaimer until the GA tag exists.
> 5. **Screenshots and matrix visuals are added by Vince.** The bundle build excludes any expected screenshot path until the asset is present on disk and Vince ticks the asset-ready box below.

---

## 0. What this pack contains

- [`docs/public/X_KLICKD_ZENODO_DRAFT.md`](../public/X_KLICKD_ZENODO_DRAFT.md) — Zenodo-form field draft (title, description, creators, keywords, related identifiers, notes, file list).
- This file — pre-deposit acceptance checklist + dependency map.
- [`scripts/generate_v4_1_zenodo_bundle.sh`](../../scripts/generate_v4_1_zenodo_bundle.sh) — local-only bundle builder (ZIP staging, exclusions). Does NOT upload anywhere.
- [`scripts/generate_x_klickd_sha256sums.sh`](../../scripts/generate_x_klickd_sha256sums.sh) — SHA256SUMS generator for the 42 x.klickd skills + the v4.1 docs. Runs against `examples/v4.1/x-klickd-skills/` (the post-rename public path).

All output goes under `release-artifacts/v4.1.0/` which is `.gitignored` and never committed.

---

## 1. Dependency on the rename PR

This pack assumes the public catalog path is **`examples/v4.1/x-klickd-skills/`**. At the time of writing, the in-repo path still uses the internal codename. The Zenodo bundle MUST NOT be sealed until the rename PR has merged to `main` and the new path is live.

Acceptance gates for the rename dependency:

- [ ] Rename PR merged — `examples/v4.1/x-klickd-skills/` exists on `main`.
- [ ] `examples/v4.1/x-klickd-skills/lite/` contains 8 `*.klickd` skill files plus `manifest.json`.
- [ ] `examples/v4.1/x-klickd-skills/pro/` contains 34 `*.klickd` skill files plus `manifest.json`.
- [ ] Total candidate skill count: **42**.
- [ ] All references in `SPEC.md`, `README.md`, `docs/chimera/V4_1_*.md`, `docs/public/X_KLICKD_*.md`, `scripts/validate_v4_1_candidate_mapping.py`, and `.zenodo.json` point at the new path (verified by the grep checklist in §6).

Until those boxes tick, run the SHA256SUMS and bundle scripts in **dry mode** — they detect the absence of the expected path and exit non-zero with a clear message.

### 1.1 What the rename PR must change (findings from a dry-run audit, 2026-05-28)

A dry-run staging of the bundle (with the path temporarily renamed for testing) surfaced codename strings *inside* skill content, not just in paths. The rename PR therefore needs to rewrite both:

- **Paths** — `examples/v4.1/chimera-skills/` → `examples/v4.1/x-klickd-skills/`.
- **Embedded JSON keys/values inside every skill `.klickd`** — `kind`, `domain_schema_version`, `see_readme`, `see_planning_doc`, manifest `kind`, and any other field that currently carries the internal codename. The bundle audit (§6 / script audit 1) will fail until these strings are replaced.
- **Test files** — at least `tests/test_rfc009_chimera_scaffold.py` (filename) and several other tests reference the codename. The deposit may exclude tests, or the rename PR may rename them; either approach works.
- **CHANGELOG entries and planning docs under `docs/chimera/`** — these mention the codename for legitimate historical reasons. If they ship in the bundle, they leak. Two options: either exclude the planning-doc directory from the bundle, or rewrite the planning docs into `x.klickd`-named successors before tagging GA.

None of these changes are made by this prep PR. They belong in the rename PR (or a follow-up content-cleanup PR before tagging v4.1 GA).

---

## 2. Zenodo deposit fields (mirror)

Field-by-field values live in [`docs/public/X_KLICKD_ZENODO_DRAFT.md`](../public/X_KLICKD_ZENODO_DRAFT.md). At deposit time:

1. Copy the field values from §1–§13 of that file into either `/.zenodo.json` (preferred — Zenodo imports automatically from the GitHub release) or the Zenodo web form.
2. Verify the description is **plain text** (no Markdown, no HTML).
3. Verify the keyword list mirrors §8 of the draft (no codename, no spelling variants).
4. Verify related-identifier DOIs and URLs (`isVersionOf`, `isNewVersionOf`, `isSupplementTo`, `isIdenticalTo`).
5. Confirm `access_right: open`, `license: CC0-1.0`.

---

## 3. File list (bundle contents)

The bundle ZIP that will be uploaded to Zenodo should contain only:

- **Normative spec & schema**
  - `SPEC.md`
  - `SCHEMA_INDEX.md`
  - `schema/klickd-v4.schema.json`
  - `schemas/klickd-payload-v4.schema.json`
- **Reference implementations** (source only — no build artefacts, no `node_modules/`, no `dist/`)
  - `packages/@klickd/core/`
  - `packages/pypi/klickd/`
- **Cross-impl test vectors and verifiers**
  - `tests/`
  - `verify_vectors.py`
  - `verify_vectors.mjs`
  - `save_klickd.py`, `load_klickd.py`
- **v4.1 catalog (post-rename path)**
  - `examples/v4.1/x-klickd-skills/lite/` (8 skills + manifest)
  - `examples/v4.1/x-klickd-skills/pro/` (34 skills + manifest)
- **Validator**
  - `scripts/validate_v4_1_candidate_mapping.py`
- **Public copy**
  - `docs/public/X_KLICKD_SITE_COPY.md`
  - `docs/public/X_KLICKD_MATRIX_VISUAL_BRIEF.md`
  - `docs/public/X_KLICKD_ZENODO_DRAFT.md`
- *(Not bundled: this checklist itself — `docs/releases/V4_1_ZENODO_PREP_CHECKLIST.md`. It embeds literal codename strings inside its grep audit section, so it intentionally stays in the repo and out of the deposit surface.)*
- **Repository metadata**
  - `README.md`
  - `CHANGELOG.md`
  - `CITATION.cff`
  - `LICENSE`
  - `ACKNOWLEDGEMENTS.md`
  - `.zenodo.json`
- **SHA256SUMS** for the 42 skills + spec/schema/docs (generated by `scripts/generate_x_klickd_sha256sums.sh`).
- **Original diagrams (only if present at bundle-build time)**
  - `assets/x-klickd-matrix-hero.svg`
  - `assets/x-klickd-matrix-hero.png`
  - The build script skips these silently if they are absent. Vince adds them when ready.

### Explicit exclusions (must not appear in the bundle)

- Any path containing the internal codename in its name. (Hard lock — see §6.)
- `node_modules/`, `dist/`, `build/`, `__pycache__/`, `*.pyc`, `.pytest_cache/`.
- `.git/`, `.github/`, `.claude/`, IDE config (`.vscode/`, `.idea/`).
- `release-artifacts/` (this is where the bundle is *built*, not what gets shipped inside it).
- `.env`, `.env.*`, `*.pem`, `*.key`, `id_rsa*`, `*.p12`, `*.pfx`, any private fixture.
- Screenshots not yet added by Vince. The bundle script does not invent placeholders; if the file is absent, it is omitted.

---

## 4. Source list (for description / about block)

Same source list as in the Zenodo draft §13 — ESCO, DigComp 2.2, LifeComp, NICE, ENISA, CIS Controls, SFIA, O*NET, WEF Future of Jobs. Each anchor is a reference to a canonical public URL; no certification, endorsement, or content redistribution is claimed.

---

## 5. Non-overclaiming wording lock

The bundle README and the Zenodo description MUST retain every disclaimer in [`X_KLICKD_ZENODO_DRAFT.md`](../public/X_KLICKD_ZENODO_DRAFT.md) §6 verbatim until v4.1 is tagged GA. Specifically:

- "candidates / not recommended for unmodified production use" — until GA.
- "no certification or endorsement by any framework owner" — permanently.
- "no universal compatibility across all AI products" — permanently.
- "diagrams are original works; no copyrighted third-party graphics are reproduced unless their licence terms clearly permit reuse" — permanently.

If the GA tag exists at deposit time, the first bullet may be removed. The others remain.

---

## 6. Pre-Zenodo grep checklist (codename leak audit)

Before sealing the bundle ZIP, run every command below. Each must produce **zero matches** in the staged bundle. Run them from the repo root against the staged bundle directory (`release-artifacts/v4.1.0/bundle/`).

```bash
# Stage directory the bundle script writes to
STAGE="release-artifacts/v4.1.0/bundle"

# 1. No codename in any file content (case-insensitive)
grep -rIli 'chimera' "$STAGE" || echo "OK: no 'chimera' content"

# 2. No codename in any filename or directory name
find "$STAGE" -iname '*chimera*' -print | (grep . && echo FAIL || echo "OK: no 'chimera' paths")

# 3. No private fixture / secrets patterns
grep -rIliE '(BEGIN (RSA |EC |DSA |OPENSSH |PRIVATE) KEY|AKIA[0-9A-Z]{16}|aws_secret|ghp_[0-9A-Za-z]{36})' "$STAGE" \
  && echo FAIL: secret-like content || echo "OK: no obvious secret patterns"

# 4. No node_modules / dist / __pycache__ leaked
find "$STAGE" \( -name node_modules -o -name dist -o -name __pycache__ -o -name '.git' \) -print \
  | (grep . && echo FAIL || echo "OK: no build/VCS dirs")

# 5. Confirm 42 candidate skill files
find "$STAGE/examples/v4.1/x-klickd-skills" -name '*.klickd' | wc -l
# Expect: 42

# 6. Confirm public path uses the post-rename name
ls "$STAGE/examples/v4.1/" | grep -i 'x-klickd-skills' && echo "OK: x.klickd public path"

# 7. Description, keywords, notes — manual eyeball on the staged .zenodo.json
grep -i 'chimera' "$STAGE/.zenodo.json" && echo FAIL || echo "OK: .zenodo.json clean"
```

If any command produces a FAIL line, **do not upload the bundle**. Fix the source, re-run `scripts/generate_v4_1_zenodo_bundle.sh`, and re-run the grep checklist.

**Known false positives on audit 3 (secret patterns):**

- `tests/test_post_v4_demos.py` references the string `BEGIN PRIVATE KEY` as a needle the test itself looks for in fixtures.
- `tests/test_starter_pack_validator.py` includes the literal `AKIAABCDEFGHIJKLMNOP` as a fake AWS key fixture to verify the leak detector.

These are legitimate test code. If the deposit includes the `tests/` directory, manually verify each audit-3 hit is a fixture in test code (not real material) before clearing the gate.

---

## 7. SHA256SUMS generation

Run [`scripts/generate_x_klickd_sha256sums.sh`](../../scripts/generate_x_klickd_sha256sums.sh) after the rename PR has merged. Output goes to `release-artifacts/v4.1.0/SHA256SUMS.x-klickd-skills.txt`.

Verification:

```bash
# Sanity check the count of hashed files
wc -l release-artifacts/v4.1.0/SHA256SUMS.x-klickd-skills.txt
# Expect: 42 skill lines + 2 manifest.json lines + spec/schema/docs lines

# Spot-verify a hash
cd examples/v4.1/x-klickd-skills/lite
sha256sum artist.klickd
# Compare to release-artifacts/v4.1.0/SHA256SUMS.x-klickd-skills.txt
```

---

## 8. Acceptance gate before Vince deposits

Every box must be ticked. **None of these are ticked by Claude or by any automation in this PR.**

- [ ] Rename PR merged; `examples/v4.1/x-klickd-skills/` exists on `main`.
- [ ] v4.1 GA tag exists (`git tag --list v4.1.0`).
- [ ] `scripts/validate_v4_1_candidate_mapping.py` passes on the catalog at the GA tag.
- [ ] `scripts/generate_x_klickd_sha256sums.sh` ran cleanly; SHA256SUMS file exists.
- [ ] `scripts/generate_v4_1_zenodo_bundle.sh` ran cleanly; bundle staged under `release-artifacts/v4.1.0/bundle/`.
- [ ] All commands in §6 (grep checklist) returned OK.
- [ ] Original matrix visuals are either (a) present at `assets/x-klickd-matrix-hero.{svg,png}` and Vince has confirmed they are original, or (b) deliberately omitted from this deposit.
- [ ] Description in `/.zenodo.json` (or the web form) is plain text, contains the v4.1 non-GA disclaimer if not yet GA, ends with "A true open standard, not a prompt gallery."
- [ ] Keywords mirror §8 of the draft. No codename in any variant.
- [ ] Related identifiers: `isVersionOf` → concept DOI; `isNewVersionOf` → v4.0.0 version DOI; `isSupplementTo` → repo URL; `isIdenticalTo` → npm/PyPI **only if** v4.1 packages are published.
- [ ] Vince has read the bundle README and signed off on the wording.
- [ ] Vince uploads to Zenodo and clicks Publish. **This is the only deposit step. It is performed by Vince, not by Claude, not by CI.**

---

## 9. What this checklist does NOT do

- Does **not** publish.
- Does **not** tag.
- Does **not** create a GitHub Release.
- Does **not** push to npm or PyPI.
- Does **not** call any Zenodo API.
- Does **not** add screenshots or visuals — Vince adds them.
- Does **not** modify `/.zenodo.json` at deposit time — Vince either pastes into the web form or updates `.zenodo.json` himself.

If you (an agent, a CI job, or a contributor) find yourself about to do any of the above on behalf of the maintainer: stop. Open an issue instead.
