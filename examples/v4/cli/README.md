# `examples/v4/cli/` — Python CLI demo (R4-PV-1, non-normative)

A 100-line, path-based loader showing the smallest useful program built on
the official Python package.

> **Status:** non-normative, docs-only, no release artefact.
> **Package contract used:** `from klickd import load_klickd` — public API
> frozen at v4.0.0, see [`packages/pypi/klickd/`](../../../packages/pypi/klickd/).

---

## 1. Install

```bash
pip install klickd==4.0.0
```

(`load_klickd` itself has no network or filesystem side-effects; it parses
bytes and returns a `dict`.)

## 2. Run

Plain (unencrypted) payload:

```bash
python examples/v4/cli/klickd_cli.py examples/v4/personas/01-eleve-terminale-fr.klickd
```

JSON output:

```bash
python examples/v4/cli/klickd_cli.py \
  examples/v4/personas/03-fullstack-developer-en.klickd --json
```

Encrypted envelope (provide passphrase via flag — the script never reads
secrets from disk or environment by default):

```bash
python examples/v4/cli/klickd_cli.py my-profile.klickd --passphrase '...'
```

Strip `_`-prefixed debug/benchmark keys before printing (SPEC §29):

```bash
python examples/v4/cli/klickd_cli.py profile.klickd --strip-underscore
```

## 3. What it prints

The default human-readable summary surfaces only the fields an integrator
typically needs to confirm a successful load:

```
# klickd-cli — package klickd==4.0.0
# source: examples/v4/personas/01-eleve-terminale-fr.klickd

klickd_version        : 4.0
payload_schema_version: 4.0.0-preview.1
domain                : education
profile_kind          : learner
display_name          : Élève Exemple
language              : fr
current_project       : Intégrales — Terminale S
current_state         : Maîtrise ∫x²dx. Bloquée sur l'intégration par parties.
expertise_level       : intermediate
verification_gates    : 2 declared
user_preferences      : Tu reprends avec une élève de Terminale S, …
```

## 4. Exit codes

| Code | Meaning |
|------|---------|
| `0`  | Loaded successfully |
| `1`  | `load_klickd` raised (bad passphrase, malformed envelope, schema fail) |
| `2`  | File not found, or `klickd` package not installed |

## 5. Constraints respected

- No secrets, API keys, or real personal data in this directory.
- No overclaims: the script does **not** perform integration with any model.
  It is strictly a loader demo; the integration recipes live under
  [`examples/v4/integrations/`](../integrations/) and
  [`docs/integrations/`](../../../docs/integrations/).
