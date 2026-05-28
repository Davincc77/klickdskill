#!/usr/bin/env bash
# generate_x_klickd_sha256sums.sh — v4.1 Zenodo prep helper.
#
# Generates a deterministic SHA256SUMS file for the 42 x.klickd skills and
# relevant normative docs, ahead of the v4.1 Zenodo deposit.
#
# Output:
#   release-artifacts/v4.1.0/SHA256SUMS.x-klickd-skills.txt
#
# This script does NOT publish, tag, release, or deposit anything. It only
# produces a local, deterministic hash file for the maintainer to attach
# to the Zenodo deposit bundle.
#
# Expected public path (post-rename):
#   examples/v4.1/x-klickd-skills/
#
# If the rename PR has not yet merged, the script exits with a clear
# message instructing the maintainer to wait. The script does not fall
# back to the internal codename path; doing so would risk leaking the
# codename into the deposit surface.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VERSION="4.1.0"
OUT_DIR="${ROOT}/release-artifacts/v${VERSION}"
OUT_FILE="${OUT_DIR}/SHA256SUMS.x-klickd-skills.txt"

SKILLS_DIR="${ROOT}/examples/v4.1/x-klickd-skills"

if [ ! -d "${SKILLS_DIR}" ]; then
  cat >&2 <<EOF
ERROR: expected public catalog path not found:
  ${SKILLS_DIR}

This script is intentionally gated on the post-rename public path. It
will not hash the internal codename path, because the SHA256SUMS file
is part of the Zenodo deposit surface and any codename leak there is a
hard block.

If the rename PR has not yet merged to main, wait for it. Otherwise,
re-check the path after merging.
EOF
  exit 2
fi

mkdir -p "${OUT_DIR}"

# Counts (sanity)
LITE_COUNT="$(find "${SKILLS_DIR}/lite" -maxdepth 1 -name '*.klickd' 2>/dev/null | wc -l | tr -d ' ')"
PRO_COUNT="$(find "${SKILLS_DIR}/pro" -maxdepth 1 -name '*.klickd' 2>/dev/null | wc -l | tr -d ' ')"
TOTAL="$((LITE_COUNT + PRO_COUNT))"

echo "==> x.klickd v4.1 catalog counts"
echo "    lite: ${LITE_COUNT}"
echo "    pro:  ${PRO_COUNT}"
echo "    total: ${TOTAL}"

if [ "${TOTAL}" -ne 42 ]; then
  echo "ERROR: expected 42 candidate skills; found ${TOTAL}." >&2
  echo "       The v4.1 candidate catalog is frozen at 42 (8 Lite + 34 Pro)." >&2
  echo "       Any drift is a release-blocker and must be reconciled before" >&2
  echo "       generating SHA256SUMS for the deposit." >&2
  exit 1
fi

cd "${ROOT}"

# Build the list of files to hash. The validator
# (scripts/validate_v4_1_candidate_mapping.py) is intentionally NOT
# hashed: its source contains the literal internal-codename byte
# (FORBIDDEN_PUBLIC_TERMS) by design — it exists to scan the tree for
# that literal — and listing its name in the SHA256SUMS file that ships
# in the deposit would surface that string on Zenodo's public file
# browser. The validator stays in the repo and CI; it is documented in
# the deposit's Zenodo notes but neither shipped nor hashed.
HASH_LIST="$(mktemp)"
trap 'rm -f "${HASH_LIST}"' EXIT

find "examples/v4.1/x-klickd-skills" -type f \
     \( -name '*.klickd' -o -name 'manifest.json' -o -name 'README.md' \) \
     >> "${HASH_LIST}"

for f in \
    SPEC.md \
    SCHEMA_INDEX.md \
    CHANGELOG.md \
    README.md \
    CITATION.cff \
    LICENSE \
    ACKNOWLEDGEMENTS.md \
    .zenodo.json \
    schema/klickd-v4.schema.json \
    schemas/klickd-payload-v4.schema.json \
    docs/public/X_KLICKD_SITE_COPY.md \
    docs/public/X_KLICKD_MATRIX_VISUAL_BRIEF.md \
    docs/public/X_KLICKD_ZENODO_DRAFT.md \
    ; do
    # NOTE: docs/releases/V4_1_ZENODO_PREP_CHECKLIST.md is intentionally
    # not hashed here. It is an in-repo prep checklist whose audit
    # section embeds the codename string. Hashing it inside the
    # SHA256SUMS file that ships in the deposit would surface that
    # string in the deposit. The checklist lives in the repo only.
  if [ -f "${ROOT}/${f}" ]; then
    echo "${f}" >> "${HASH_LIST}"
  fi
done

echo
echo "==> Hard-fail audits on files about to be hashed (mirrors bundle script)"
fail=0

echo "    [audit 1/3] codename in file content"
content_hits="$(LC_ALL=C sort -u "${HASH_LIST}" | while IFS= read -r f; do
  if grep -Il 'chimera' "${ROOT}/${f}" >/dev/null 2>&1; then
    echo "${f}"
  fi
done)"
if [ -n "${content_hits}" ]; then
  echo "      FAIL: internal-codename string found in files to be hashed:"
  echo "${content_hits}" | sed 's/^/        /'
  fail=1
else
  echo "      OK"
fi

echo "    [audit 2/3] codename in any filename"
name_hits="$(LC_ALL=C sort -u "${HASH_LIST}" | grep -i 'chimera' || true)"
if [ -n "${name_hits}" ]; then
  echo "      FAIL: internal-codename in filenames to be hashed:"
  echo "${name_hits}" | sed 's/^/        /'
  fail=1
else
  echo "      OK"
fi

echo "    [audit 3/3] obvious secret patterns"
secret_hits="$(LC_ALL=C sort -u "${HASH_LIST}" | while IFS= read -r f; do
  if grep -IlE '(BEGIN (RSA |EC |DSA |OPENSSH |PRIVATE) KEY|AKIA[0-9A-Z]{16}|aws_secret|ghp_[0-9A-Za-z]{36})' "${ROOT}/${f}" >/dev/null 2>&1; then
    echo "${f}"
  fi
done)"
if [ -n "${secret_hits}" ]; then
  echo "      FAIL: secret-like content found in files to be hashed:"
  echo "${secret_hits}" | sed 's/^/        /'
  fail=1
else
  echo "      OK"
fi

if [ "${fail}" -ne 0 ]; then
  echo
  echo "SHA256SUMS generation FAILED. Fix the failures above and re-run." >&2
  exit 1
fi

echo
echo "==> Hashing x.klickd skills + manifests + normative docs"
{
  LC_ALL=C sort -u "${HASH_LIST}" | while IFS= read -r f; do
    sha256sum "${f}"
  done
} > "${OUT_FILE}"

echo
echo "Wrote: ${OUT_FILE}"
echo
echo "Line count: $(wc -l < "${OUT_FILE}")"
echo
echo "Head:"
head -10 "${OUT_FILE}"
echo
echo "Done. This file is local-only and intended for inclusion in the"
echo "Zenodo deposit bundle. No upload happens here."
