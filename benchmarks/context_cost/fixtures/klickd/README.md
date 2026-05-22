# `fixtures/klickd/` — Sample context for the `klickd` condition

> **Non-normative benchmark fixture for RFC-003.**

## Files

- [`sample_context.json`](./sample_context.json) — cleartext, human-readable
  `.klickd`-style context. This is what the runner injects via the canonical
  `<UserContext>` block for the `klickd` condition.

## On the encrypted `sample_context.klickd` file

This PR **does not ship an encrypted `sample_context.klickd`** file.

We considered including a deterministically-encrypted payload using the public
test passphrase `benchmark-public-test-passphrase`, marked explicitly
**test-only / not secret**. We did not include it in this PR for two reasons:

1. The `.klickd` envelope uses random IV / salt per
   [`SPEC.md`](../../../../SPEC.md), so a "deterministically generated"
   encrypted file would require pinning IV / salt to fixed test vectors. That
   belongs in a follow-up runner PR that also exercises `load_klickd` /
   `save_klickd`, not in a fixtures-only PR.
2. Shipping an encrypted blob without the runner that decrypts and validates it
   would add a binary to the repo that no test exercises.

When the runner PR lands, it will (if it adds the encrypted fixture):

- mark the envelope `encrypted: true`,
- use exclusively the public passphrase
  `benchmark-public-test-passphrase` — never a real user secret,
- generate the file with a fixed IV / salt sourced from a documented seed, and
  pin that seed in this README,
- add an obvious `TEST_ONLY_DO_NOT_USE` marker inside the cleartext payload
  metadata (e.g. as a top-level `_test_only: true` field), and
- assert via a unit test that the round-trip succeeds and the resulting
  cleartext matches `sample_context.json` byte-for-byte after canonicalisation.

Until then, the `klickd` condition runs against
[`sample_context.json`](./sample_context.json) loaded as cleartext.

## Why a public passphrase is fine here

The benchmark fixture contains **synthetic** project-management data for a
fictional persona ("Léa", small Luxembourg EdTech team). It contains no real
PII, no real vendor names, no real contracts. The passphrase is published in
this repository and reproduced in every clone. It MUST NOT be reused for any
real `.klickd` file anywhere.
