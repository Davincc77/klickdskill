# `tools/` — reserved for developer tooling

This directory is **reserved** for ad-hoc developer and maintainer tooling that is
not part of the release/validation pipeline.

It is intentionally a placeholder right now:

- **Release, bundle, and SHA256-manifest tooling** lives in [`../scripts/`](../scripts/)
  and is referenced by CI and the v4.1 evidence-pack generators. Do not move those
  here — their paths are load-bearing (see
  [`../docs/STRUCTURE.md`](../docs/STRUCTURE.md)).
- **Schema and vector generators/validators** also live in [`../scripts/`](../scripts/).

New, optional helper utilities that are *not* invoked by CI, release tooling, or
published manifests may be added here so that `scripts/` stays limited to the
load-bearing pipeline. Until such a utility exists, this directory holds only this
README to document the convention rather than introduce an empty folder.
