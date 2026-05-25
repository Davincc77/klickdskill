<!--
Thanks for contributing to .klickd!

Please fill in this template. PRs with empty descriptions will be asked for more detail.
-->

## Summary

<!-- One or two sentences: what does this PR change, and why? -->

## Scope

- [ ] Documentation / community files only
- [ ] Reference implementation (Python SDK)
- [ ] Reference implementation (TypeScript SDK)
- [ ] Migrator
- [ ] Registry
- [ ] CI / workflows
- [ ] Specification (`SPEC*.md`)
- [ ] JSON schemas (`schema/`)
- [ ] Test vectors (`vectors/`)

## Linked issue

<!-- e.g. Closes #123, Refs #456. Spec / schema / vector changes should reference an RFC issue. -->

## Schema / SDK / vector impact

- [ ] No change to the `.klickd` wire format
- [ ] No change to JSON schemas
- [ ] No change to test vectors
- [ ] No package version bump
- [ ] If any of the above are checked **off**, this PR links an approved RFC issue and includes a migration / coexistence note below.

<!-- If applicable, describe the impact: -->

## Testing

<!-- How was this verified? Include commands run, vectors validated, or manual checks. -->

- [ ] Existing CI passes locally / will pass in CI
- [ ] New tests / vectors added where appropriate
- [ ] N/A — docs-only change

## Security and secret scan

- [ ] No secrets, passphrases, private keys, or personal data are included in this diff
- [ ] No cryptographic defaults are weakened (KDF floors, GCM tag, AAD coverage)
- [ ] If this PR touches the threat model or crypto, `SECURITY.md` was reviewed and updated as needed

## Governance reminders

- [ ] This PR does **not** publish to npm, PyPI, Zenodo, or any package registry
- [ ] This PR does **not** create a release, tag, or version bump
- [ ] This PR does **not** modify locked governance files outside its declared scope
- [ ] I have read [`CONTRIBUTING.md`](../CONTRIBUTING.md) and agree to the [Code of Conduct](../CODE_OF_CONDUCT.md)

## Additional notes

<!-- Anything reviewers should know: trade-offs, follow-ups, screenshots, etc. -->
