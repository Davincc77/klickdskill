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
  echo "WARNING: expected 42 candidate skills; found ${TOTAL}." >&2
  echo "         Continuing, but verify before depositing." >&2
fi

echo "==> Hashing x.klickd skills + manifests + normative docs"

cd "${ROOT}"

{
  # Skills (lite + pro) and their manifests.
  find "examples/v4.1/x-klickd-skills" -type f \
       \( -name '*.klickd' -o -name 'manifest.json' -o -name 'README.md' \) -print0 \
    | LC_ALL=C sort -z \
    | xargs -0 sha256sum

  # Normative docs and metadata pinned to the deposit.
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
      scripts/validate_v4_1_candidate_mapping.py \
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
      ( cd "${ROOT}" && sha256sum "${f}" )
    fi
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
