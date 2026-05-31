#!/usr/bin/env bash
# generate_v4_1_zenodo_bundle.sh — v4.1 Zenodo prep helper.
#
# Stages the v4.1 deposit bundle locally for the maintainer to inspect
# before uploading to Zenodo. This script:
#
#   - Does NOT publish, tag, release, push to npm/PyPI, or contact Zenodo.
#   - Does NOT include screenshots / matrix visuals unless they are
#     already present on disk and Vince has committed them.
#   - Does NOT include any path or file whose name contains the internal
#     planning-track codename.
#   - Does NOT include build outputs, .git, .github, node_modules,
#     __pycache__, dotfiles for IDEs, or any secret-looking file.
#
# Output (local only, .gitignored):
#   release-artifacts/v4.1.0/bundle/        — staged tree
#   release-artifacts/v4.1.0/bundle.zip     — sealed ZIP for upload
#
# Run after the rename PR has merged. If the public catalog path is
# absent, the script exits non-zero.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VERSION="4.1.0"
OUT_DIR="${ROOT}/release-artifacts/v${VERSION}"
STAGE="${OUT_DIR}/bundle"
ZIP_FILE="${OUT_DIR}/bundle.zip"

SKILLS_DIR_REL="examples/v4.1/x-klickd-skills"
SKILLS_DIR="${ROOT}/${SKILLS_DIR_REL}"

if [ ! -d "${SKILLS_DIR}" ]; then
  cat >&2 <<EOF
ERROR: expected public catalog path not found:
  ${SKILLS_DIR}

The v4.1 bundle build is gated on the post-rename public path. It will
not fall back to the internal codename path. Wait for the rename PR to
merge to main, then re-run.
EOF
  exit 2
fi

echo "==> Cleaning previous stage"
rm -rf "${STAGE}" "${ZIP_FILE}"
mkdir -p "${STAGE}"

cd "${ROOT}"

copy_if_exists() {
  local src="$1"
  local dst_parent
  if [ -f "${src}" ] || [ -d "${src}" ]; then
    dst_parent="${STAGE}/$(dirname "${src}")"
    mkdir -p "${dst_parent}"
    cp -R "${src}" "${dst_parent}/"
  fi
}

echo "==> Copying spec & metadata"
for f in SPEC.md SCHEMA_INDEX.md CHANGELOG.md README.md CITATION.cff LICENSE ACKNOWLEDGEMENTS.md .zenodo.json; do
  copy_if_exists "${f}"
done

echo "==> Copying schemas"
copy_if_exists "schema/klickd-v4.schema.json"
copy_if_exists "schemas/klickd-payload-v4.schema.json"

echo "==> Copying reference SDKs (source only)"
if [ -d "packages/@klickd/core" ]; then
  mkdir -p "${STAGE}/packages/@klickd"
  rsync -a \
    --exclude 'node_modules' \
    --exclude 'dist' \
    --exclude 'build' \
    --exclude '.cache' \
    --exclude 'coverage' \
    --exclude '*.tgz' \
    "packages/@klickd/core" "${STAGE}/packages/@klickd/"
fi
if [ -d "packages/pypi/klickd" ]; then
  mkdir -p "${STAGE}/packages/pypi"
  rsync -a \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    --exclude '*.egg-info' \
    --exclude 'build' \
    --exclude 'dist' \
    --exclude '.pytest_cache' \
    "packages/pypi/klickd" "${STAGE}/packages/pypi/"
fi

echo "==> Copying tests & verifiers"
# Codename-bearing test files and the candidate-mapping validator are
# intentionally EXCLUDED from the deposit bundle. Rationale:
#   - The validator's job is to scan the source tree for the literal
#     internal-codename byte. Its source therefore must contain that
#     literal (FORBIDDEN_PUBLIC_TERMS) and a string of
#     internal planning-tree paths used as scan targets. Shipping the
#     validator inside the deposit ZIP would surface those bytes on
#     Zenodo's public file browser, defeating the leak guard the
#     validator exists to enforce. The validator stays in the repo and
#     CI; it is documented in the deposit's Zenodo notes but not
#     shipped.
#   - The codename-bearing tests (test_rfc009_scaffold.py,
#     test_v4_1_candidate_mapping.py, test_klickdapp_student_carriers.py,
#     test_starter_pack_validator.py) reference the historical in-repo
#     planning tree and the validator itself; they would surface the
#     codename in the deposit. Cross-implementation verification of the
#     deposited artefacts is covered by verify_vectors.{py,mjs} and the
#     vector JSON files, which are codename-free and DO ship.
if [ -d "tests" ]; then
  mkdir -p "${STAGE}/tests"
  rsync -a \
    --exclude '__pycache__' \
    --exclude '.pytest_cache' \
    --exclude 'test_rfc009_scaffold.py' \
    --exclude 'test_rfc009_chimera_scaffold.py' \
    --exclude 'test_v4_1_candidate_mapping.py' \
    --exclude 'test_klickdapp_student_carriers.py' \
    --exclude 'test_starter_pack_validator.py' \
    "tests/" "${STAGE}/tests/"
fi
# Reference scripts now live under scripts/ (canonical), with thin root
# compatibility wrappers kept at the repo root. Bundle BOTH: the canonical
# implementations (so the deposit is self-contained) and the root wrappers
# (so `python verify_vectors.py` / `node verify_vectors.mjs` still work from
# the bundle root exactly as documented).
for f in scripts/verify_vectors.py scripts/verify_vectors.mjs \
         scripts/save_klickd.py scripts/load_klickd.py \
         verify_vectors.py verify_vectors.mjs save_klickd.py load_klickd.py; do
  copy_if_exists "${f}"
done

echo "==> Copying x.klickd v4.1 catalog (post-rename path)"
mkdir -p "${STAGE}/examples/v4.1"
rsync -a "${SKILLS_DIR_REL}/" "${STAGE}/${SKILLS_DIR_REL}/"

# Validator is intentionally NOT copied into the bundle. See comment
# above under "Copying tests & verifiers" for the rationale.

echo "==> Copying public copy and Zenodo draft"
mkdir -p "${STAGE}/docs/public"
for f in \
    docs/public/X_KLICKD_SITE_COPY.md \
    docs/public/X_KLICKD_MATRIX_VISUAL_BRIEF.md \
    docs/public/X_KLICKD_ZENODO_DRAFT.md \
    ; do
  copy_if_exists "${f}"
done
# NOTE: docs/releases/V4_1_ZENODO_PREP_CHECKLIST.md is intentionally NOT
# copied into the bundle. It is a pre-deposit prep checklist whose audit
# section embeds the literal codename string for grep purposes. Including
# it in the deposit surface would leak that string. The checklist lives
# in the repo only.

echo "==> Copying matrix visuals (only if present)"
for f in assets/x-klickd-matrix-hero.svg assets/x-klickd-matrix-hero.png; do
  if [ -f "${ROOT}/${f}" ]; then
    copy_if_exists "${f}"
    echo "    included: ${f}"
  else
    echo "    SKIP (not present): ${f}"
  fi
done

echo
echo "==> Hard-fail audits (exit non-zero on any leak)"
fail=0

echo "    [audit 1/5] codename in file content"
if grep -rIli 'chimera' "${STAGE}" >/dev/null 2>&1; then
  echo "      FAIL: 'chimera' string found in bundle content:"
  grep -rIli 'chimera' "${STAGE}" | sed 's/^/        /'
  fail=1
else
  echo "      OK"
fi

echo "    [audit 2/5] codename in any filename / dirname"
if find "${STAGE}" -iname '*chimera*' -print | grep -q .; then
  echo "      FAIL: 'chimera' in bundle paths:"
  find "${STAGE}" -iname '*chimera*' -print | sed 's/^/        /'
  fail=1
else
  echo "      OK"
fi

echo "    [audit 3/5] obvious secret patterns"
if grep -rIliE '(BEGIN (RSA |EC |DSA |OPENSSH |PRIVATE) KEY|AKIA[0-9A-Z]{16}|aws_secret|ghp_[0-9A-Za-z]{36})' "${STAGE}" >/dev/null 2>&1; then
  echo "      FAIL: secret-like content found"
  fail=1
else
  echo "      OK"
fi

echo "    [audit 4/5] no build/VCS/cache leaks"
leaked="$(find "${STAGE}" \( -name node_modules -o -name dist -o -name build -o -name __pycache__ -o -name '.git' -o -name '.github' -o -name '.claude' -o -name '.idea' -o -name '.vscode' -o -name '.pytest_cache' -o -name '*.egg-info' \) -print 2>/dev/null || true)"
if [ -n "${leaked}" ]; then
  echo "      FAIL: build/VCS/cache dirs in bundle:"
  echo "${leaked}" | sed 's/^/        /'
  fail=1
else
  echo "      OK"
fi

echo "    [audit 5/5] candidate skill count = 42"
COUNT="$(find "${STAGE}/${SKILLS_DIR_REL}" -maxdepth 2 -name '*.klickd' | wc -l | tr -d ' ')"
echo "      counted: ${COUNT}"
if [ "${COUNT}" -ne 42 ]; then
  echo "      FAIL: expected 42, found ${COUNT}. The v4.1 candidate catalog"
  echo "            is frozen at 42 (8 Lite + 34 Pro); any drift is a"
  echo "            release-blocker and must be reconciled before deposit."
  fail=1
else
  echo "      OK"
fi

if [ "${fail}" -ne 0 ]; then
  echo
  echo "Bundle staging FAILED. Fix the failures above and re-run." >&2
  echo "Stage left in place for inspection: ${STAGE}" >&2
  exit 1
fi

echo
echo "==> Generating SHA256SUMS inside bundle"
(
  cd "${STAGE}"
  find . -type f ! -name SHA256SUMS -print0 \
    | LC_ALL=C sort -z \
    | xargs -0 sha256sum > SHA256SUMS
)

echo "==> Sealing ZIP"
(
  cd "${OUT_DIR}"
  rm -f bundle.zip
  # -X: drop extra file attributes for reproducibility
  zip -rqX bundle.zip bundle
)

echo
echo "Bundle ZIP: ${ZIP_FILE}"
echo "Stage:      ${STAGE}"
echo "Size:       $(du -h "${ZIP_FILE}" | cut -f1)"
echo
echo "Next steps (performed by Vince, NOT by this script):"
echo "  1. Open the bundle ZIP and visually browse the file list."
echo "  2. Re-run the pre-Zenodo grep checklist in"
echo "     docs/releases/V4_1_ZENODO_PREP_CHECKLIST.md §6 against the stage."
echo "  3. If all green, upload bundle.zip to Zenodo manually."
echo
echo "This script does NOT upload anything."
