# Preview Publication Checklist — `v4.0.0-preview.1`

> This checklist documents the steps that **would** be performed to publish
> the `v4.0.0-preview.1` preview build. **None of these steps have been
> executed yet.** The preview track currently exists only in source form on
> `main`.
>
> Do **not** run any of the publish steps below unless a project maintainer
> has explicitly decided to cut a preview release and the corresponding PR
> has been reviewed and merged.

---

> **`x.klickd` v4.1 candidate catalog note (2026-05-28):** Any `x.klickd` candidate skill that will be exposed in a `/klickdskill` surface as part of a release MUST first clear the mandatory QA protocol in [`docs/chimera/V4_1_SKILL_QA_PROTOCOL.md`](../chimera/V4_1_SKILL_QA_PROTOCOL.md): all 14 PASS gates, no open BLOCKER, every WARN acknowledged, Architecture / Security / Legal-Claims / UX / QA sign-offs recorded. This is independent of the preview track gating below; it gates `ship_ready` and catalog exposure, not preview tagging.

## 0. Pre-flight (must all be green before tagging)

- [ ] `main` is clean and all preview PRs (SPEC §33, schemas, SDK round-trip,
      vectors, benchmarks, Hermes POC, RFCs) are merged.
- [ ] CHANGELOG entry for `v4.0.0-preview.1` is present, accurate, and
      explicitly marked `(preview, NOT GA)`.
- [ ] `docs/releases/v4.0.0-preview.1.md` is up-to-date and reflects the
      actual scope being shipped.
- [ ] Cross-impl verifiers pass locally and in CI:
      - `python verify_vectors.py`
      - `node verify_vectors.mjs` (with `hash-wasm` installed)
- [ ] Round-trip preservation tests pass for both SDKs.
- [ ] Secret scan run on the diff (`git diff main...`) — no keys, no tokens,
      no `.env`, no private fixtures.
- [ ] License headers / `CC0-1.0` declarations unchanged.
- [ ] Stable production format `v3.5.1` is still the default everywhere it
      should be (README badges, install instructions, schema index).

---

## 1. Tagging

- [ ] Decide on the tag name. The version is `4.0.0-preview.1` (SemVer
      prerelease). The git tag uses the conventional `v` prefix:
      **`v4.0.0-preview.1`**.
- [ ] Tag from the merged release-prep commit on `main`:

      ```bash
      git checkout main
      git pull --ff-only
      git tag -s v4.0.0-preview.1 -m "v4.0.0-preview.1 (preview, NOT GA)"
      git push origin v4.0.0-preview.1
      ```

- [ ] Confirm the tag points at the intended commit:

      ```bash
      git rev-parse v4.0.0-preview.1
      git show --stat v4.0.0-preview.1
      ```

---

## 2. GitHub Release

- [ ] Create the GitHub release from the tag.
- [ ] Mark it as **"Pre-release"** (not "Latest release").
- [ ] Body: use `docs/releases/v4.0.0-preview.1.md` verbatim (or link to it).
- [ ] Do **not** overwrite the "Latest release" badge for v3.5.1.

      ```bash
      gh release create v4.0.0-preview.1 \
        --prerelease \
        --title "v4.0.0-preview.1 (preview, NOT GA)" \
        --notes-file docs/releases/v4.0.0-preview.1.md
      ```

---

## 3. npm — `@klickd/core` under `preview` dist-tag

- [ ] Bump `packages/@klickd/core/package.json` `version` to
      `4.0.0-preview.1` **on a dedicated release commit** (do not mix with
      other changes).
- [ ] Verify the package builds and tests pass:

      ```bash
      cd packages/@klickd/core
      npm ci
      npm test
      npm run build
      ```

- [ ] Publish under the `preview` dist-tag (so `latest` keeps resolving to
      v3.5.1):

      ```bash
      npm publish --tag preview --access public
      ```

- [ ] Verify the dist-tags:

      ```bash
      npm dist-tag ls @klickd/core
      # expected:
      #   latest:  3.5.1
      #   preview: 4.0.0-preview.1
      ```

- [ ] Smoke-test from a clean directory:

      ```bash
      npm install @klickd/core@preview
      node -e "console.log(require('@klickd/core/package.json').version)"
      # expected: 4.0.0-preview.1

      npm install @klickd/core           # without @preview
      node -e "console.log(require('@klickd/core/package.json').version)"
      # expected: 3.5.1 (UNCHANGED)
      ```

- [ ] **Do not** move the `latest` dist-tag.

---

## 4. PyPI — `klickd` as a PEP 440 pre-release

- [ ] Bump `packages/pypi/klickd/pyproject.toml` (and `__version__` if
      present) to `4.0.0a1` — PEP 440 pre-release form.
      (Rationale: `pip install klickd` excludes pre-releases by default, so
      v3.5.1 keeps being the installed version unless users opt in with
      `--pre` or pin `klickd==4.0.0a1`.)
- [ ] Build sdist + wheel:

      ```bash
      cd packages/pypi/klickd
      python -m build
      twine check dist/*
      ```

- [ ] Publish via the existing **PyPI Trusted Publisher** GitHub Actions
      workflow (no long-lived tokens).
      - [ ] Confirm the workflow's `environment: pypi` is configured and
            still authorised on PyPI for this project.
      - [ ] Trigger the workflow on the `v4.0.0-preview.1` tag.
- [ ] Verify visibility on PyPI:
      - [ ] `pip install klickd` resolves to **3.5.1** (unchanged).
      - [ ] `pip install --pre klickd` or `pip install klickd==4.0.0a1`
            resolves to the new pre-release.

---

## 5. Zenodo — preview deposit (optional, field-by-field validation)

> Zenodo is the slowest-to-undo of the publish steps. **Treat it as the last
> action**, after npm + PyPI smoke tests pass.

- [ ] Decide whether a Zenodo deposit is wanted at all for the preview.
      A preview deposit will mint a **new version-specific DOI** under the
      same concept DOI as v3.5.1 (`10.5281/zenodo.20262530`).
- [ ] If yes, create a **draft** deposit (do not publish immediately) and
      validate every field against `.zenodo.json`:
      - [ ] `title` — includes the words "preview" / "non-GA".
      - [ ] `version` — `4.0.0-preview.1`.
      - [ ] `upload_type` — `software`.
      - [ ] `creators` — unchanged from v3.5.1 unless authorship has changed.
      - [ ] `license` — `CC0-1.0`.
      - [ ] `description` — clearly states "preview / non-GA" and that
            v3.5.1 remains the stable production release.
      - [ ] `related_identifiers` — link to GitHub release, npm preview tag,
            PyPI pre-release, and the v3.5.1 DOI as `IsPreviousVersionOf`.
      - [ ] `keywords` — add `preview`.
      - [ ] `notes` — explicit "PREVIEW / NOT GA" banner.
- [ ] Have a second reviewer eyeball the draft.
- [ ] Publish the Zenodo deposit only after maintainer sign-off.
- [ ] Update `CITATION.cff` and `.zenodo.json` **in a follow-up PR** with the
      newly minted DOI. Do **not** invent a DOI before Zenodo issues one.

---

## 6. Post-publication

- [ ] Update README to reference the preview release URL (GitHub release page)
      and dist channels. Keep the v3.5.1 badge as the primary, current
      release.
- [ ] Open a follow-up issue listing known limitations and the deprecation /
      sunset policy for `4.0.0-preview.1`.
- [ ] Announce in the usual channels with explicit "preview / not GA"
      language.

---

## Rollback plan

- npm: `npm dist-tag rm @klickd/core preview` removes the dist-tag without
  unpublishing the version. A truly broken upload can be `npm unpublish`'d
  within 72h; after that the version is permanent.
- PyPI: pre-releases can be yanked (`yank` flag on the release) — they
  remain visible but are excluded from resolution. Files cannot be replaced.
- GitHub release: can be deleted or converted to a draft.
- Zenodo: deposits cannot be deleted once published. They can be marked as
  withdrawn with a public note. **Hence the "Zenodo last" rule above.**
- Git tag: `git push --delete origin v4.0.0-preview.1` removes the remote
  tag; coordinate with anyone who may have already fetched it.
