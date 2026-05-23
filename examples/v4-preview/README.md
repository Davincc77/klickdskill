# `examples/v4-preview/` — `.klickd v4` preview examples (NON-NORMATIVE)

These files illustrate the top-level shape of a `.klickd v4.0.0-preview.1` document — the next **preview track** inside the `.klickd` standard family. They are **non-normative** and **NOT GA**.

| File | What it shows |
|------|---------------|
| `minimal.klickd` | A v4-preview file with the `preview` marker, `profile_kind`, and a few preview hooks (`verification_gates`, `human_veto_policy`, `claim_sources`). |

For per-field fixtures (`media_profile`, full `verification_gates`, etc.), see [`docs/rfcs/examples/`](../../docs/rfcs/examples/).

- Spec: [`SPEC.md` §33](../../SPEC.md)
- Permissive schemas: [`schemas/klickd-payload-v4-preview.schema.json`](../../schemas/klickd-payload-v4-preview.schema.json), [`schema/klickd-v4-preview.schema.json`](../../schema/klickd-v4-preview.schema.json)

> v3.x readers MUST ignore preview fields. v4-preview readers MUST preserve unknown fields verbatim.
