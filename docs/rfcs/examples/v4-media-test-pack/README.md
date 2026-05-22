# v4 Media Test Pack — Fixtures (NON-NORMATIVE / DRAFT)

These files are **non-normative** example fixtures for [RFC-001 `media_profile` v1](../../RFC-001-media-profile-v1.md) and [RFC-002 `verification_gates` v1/v2](../../RFC-002-verification-gates.md). They support the design document at [`docs/rfcs/v4-media-test-pack.md`](../../v4-media-test-pack.md).

Nothing in this directory:

- validates against any current schema in `schema/` or `schemas/`
- depicts a real person
- references a private or production URI (the only outbound URLs are public CTAs: GitHub / Zenodo / PyPI / npm for Project A, `https://klickd.app` for Project B)
- carries a real licence, real hash, real DOI, real version number, or any secret

All hashes, DOIs, and licence strings are `PLACEHOLDER_*`. Synthetic narrators are tagged in `producer.*` accordingly.

## Files

| File | Project | RFC |
|---|---|---|
| `project-a-klickdskill.media_profile.json` | A — `.klickd / klickdskill` developer film | RFC-001 |
| `project-a-klickdskill.verification_gates.json` | A | RFC-002 (v1 core + v2 draft) |
| `project-b-klickd-app.media_profile.json` | B — `klickd.app` learning app film | RFC-001 |
| `project-b-klickd-app.verification_gates.json` | B | RFC-002 (v1 core + v2 draft) |

Real video generation requires a separate explicit approval from Vince and a documented model/credit decision. See §6 of the test pack document.
