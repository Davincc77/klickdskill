#!/usr/bin/env bash
# release_bundle_inventory.sh — v4.0.0 release-prep helper.
#
# Generates a local, deterministic inventory and SHA256SUMS for the v4.0.0
# bundle artefacts. Output goes to <repo>/release-artifacts/v4.0.0/, which
# is .gitignored and never committed.
#
# This script does NOT publish anything. It only produces local artefacts
# for the maintainer to inspect before any gated publish (npm / PyPI /
# Zenodo / git tag / GitHub Release).

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VERSION="4.0.0"
OUT_DIR="${ROOT}/release-artifacts/v${VERSION}"

mkdir -p "${OUT_DIR}"

cd "${ROOT}"

echo "==> Building npm package @klickd/core@${VERSION}"
if [ -d "packages/@klickd/core" ]; then
  (
    cd packages/@klickd/core
    if [ -f package.json ]; then
      npm pack --pack-destination "${OUT_DIR}" >/dev/null
    fi
  )
fi

echo "==> Building Python sdist + wheel for klickd==${VERSION}"
if [ -d "packages/pypi/klickd" ]; then
  (
    cd packages/pypi/klickd
    if [ -f pyproject.toml ]; then
      python -m build --outdir "${OUT_DIR}" >/dev/null 2>&1 || \
        echo "  (skip: python -m build not available; install with 'pip install build')"
    fi
  )
fi

echo "==> Snapshotting key normative artefacts"
# Copy referenceable files for the Zenodo deposit bundle.
mkdir -p "${OUT_DIR}/spec"
for f in SPEC.md SCHEMA_INDEX.md CHANGELOG.md README.md CITATION.cff .zenodo.json LICENSE; do
  [ -f "${ROOT}/${f}" ] && cp "${ROOT}/${f}" "${OUT_DIR}/spec/"
done

mkdir -p "${OUT_DIR}/schemas"
cp -f schema/klickd-v4.schema.json "${OUT_DIR}/schemas/" 2>/dev/null || true
cp -f schemas/klickd-payload-v4.schema.json "${OUT_DIR}/schemas/" 2>/dev/null || true

mkdir -p "${OUT_DIR}/release-notes"
cp -f docs/releases/v4.0.0.md "${OUT_DIR}/release-notes/" 2>/dev/null || true

echo "==> Generating SHA256SUMS"
(
  cd "${OUT_DIR}"
  find . -type f ! -name SHA256SUMS -print0 \
    | LC_ALL=C sort -z \
    | xargs -0 sha256sum > SHA256SUMS
)

echo
echo "Inventory written to: ${OUT_DIR}"
echo "Contents:"
ls -la "${OUT_DIR}"
echo
echo "SHA256SUMS (head):"
head -20 "${OUT_DIR}/SHA256SUMS" || true
echo
echo "Done. These artefacts are local-only; they are not committed to the repo."
