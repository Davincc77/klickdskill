# `examples/v4/personas/` — 5 profils d'exemple `.klickd v4-preview` (R4-P0-3)

> **Statut :** NON-NORMATIF, docs-only, exemples publics.
> **Track :** [R4-P0-3 « Profils d'exemple téléchargeables (5 personas) »](../../../docs/roadmap/ROAD-TO-V4-GA.md#r4-p0-3--profils-dexemple-téléchargeables-5-personas).
> **Schéma applicable :** [`schemas/klickd-payload-v4-preview.schema.json`](../../../schemas/klickd-payload-v4-preview.schema.json) (PERMISSIF, `additionalProperties: true`, voir [`SPEC.md` §33](../../../SPEC.md)).
> **Ne déclenche aucune release :** pas de tag, pas de `latest` npm/PyPI, pas de DOI Zenodo, pas de bump de version SDK.

---

## 1. Pourquoi ce dossier existe

[Letta `.af`](https://docs.letta.com/) a montré qu'un standard *spec-first sans
exemples téléchargeables* diverge dès la deuxième implémentation tierce. Le
backlog v4 (cf. [`ROAD-TO-V4-GA.md` §A5](../../../docs/roadmap/ROAD-TO-V4-GA.md)) en
fait un garde-fou explicite.

Ce dossier fournit **5 personas de référence** couvrant la matrice d'usages que
le wizard `user.klickd` ([R4-P0-1](../../../docs/spec/R4-P0-1-onboarding-wizard.md))
doit savoir produire ou réimporter sans warning :

| # | Fichier | Persona | Langue | Domaine | Facette preview |
|---|---------|---------|--------|---------|------------------|
| 1 | [`01-eleve-terminale-fr.klickd`](./01-eleve-terminale-fr.klickd) | Élève de Terminale (FR / Luxembourg) | `fr` | `education` | — |
| 2 | [`02-chef-projet-pme-fr.klickd`](./02-chef-projet-pme-fr.klickd) | Chef de projet PME | `fr` | `work` | — |
| 3 | [`03-fullstack-developer-en.klickd`](./03-fullstack-developer-en.klickd) | Full-stack developer | `en` | `work` | `reversibility` / `blast_radius` (RFC-002 v2-additive) |
| 4 | [`04-createur-media-fr.klickd`](./04-createur-media-fr.klickd) | Créateur·rice média | `fr` | `creator` | `media.klickd` (RFC-001 v1) |
| 5 | [`05-rpg-gamer-en.klickd`](./05-rpg-gamer-en.klickd) | RPG gamer | `en` | `gaming` | `gaming.klickd` baseline (R4-P1-4, registry-based) |

Chaque fichier porte un bloc `_example_metadata` qui rappelle explicitement :

- `non_normative: true`
- `contains_real_pii: false`
- `contains_secrets: false`
- `test_passphrase_if_encrypted: "klickd-example-only"`

---

## 2. Forme livrée : JSON lisible (`encrypted: false`)

Tous les fichiers de ce dossier sont des **payloads JSON lisibles** avec
`encrypted: false`. Cette forme suit la convention déjà utilisée par les
exemples historiques du dépôt (`examples/student_fr.klickd`,
`examples/professional_en.klickd`, `examples/family_plan.klickd`,
`examples/v4-preview/minimal.klickd`).

**Raisons :**

1. Le but est pédagogique : un développeur tiers doit pouvoir lire le profil
   et voir sa structure sans détour par une passphrase.
2. La governance V4 actuelle est **docs-only** ; ce PR n'introduit aucun nouvel
   artefact binaire signé ni vecteur normatif.
3. La forme encryptée (`encrypted: true`) est entièrement spécifiée et testée
   par les vectors `tests/vectors_v40_preview.json` et l'outillage SDK ; elle
   n'a pas besoin d'être dupliquée ici.

> **Aucun de ces fichiers ne contient de données personnelles réelles, de
> token, de clé, ni de secret.** Les noms (« Élève Exemple », « Dev Example »,
> « Veyra Stoneash », …) et les contextes sont fictifs.

---

## 3. Passphrase publique de test (si vous re-chiffrez localement)

Pour les tiers qui souhaitent **générer une variante chiffrée** de l'un de ces
profils — par exemple pour tester un workflow de déchiffrement — la passphrase
**publique** à utiliser est :

```
klickd-example-only
```

Cette passphrase est :

- **publique** : elle figure dans cette README et dans chaque
  `_example_metadata.test_passphrase_if_encrypted`.
- **non-secrète** : elle ne protège rien de réel.
- **non-réutilisable en production** : un writer v4 conforme
  ([R4-P0-1 §3.4](../../../docs/spec/R4-P0-1-onboarding-wizard.md)) doit
  rejeter une passphrase < 8 caractères et avertir sur les passphrases
  triviales ; `klickd-example-only` est volontairement reconnaissable comme
  « example only ».

### Re-chiffrer localement (optionnel)

Le dépôt fournit déjà [`save_klickd.py`](../../../save_klickd.py) (v3.0
envelope, AES-256-GCM + Argon2id). Exemple non-normatif :

```bash
python3 - <<'PY'
import json, pathlib, save_klickd
src = pathlib.Path("examples/v4/personas/01-eleve-terminale-fr.klickd")
payload = json.loads(src.read_text())
out = src.with_suffix(".encrypted.klickd")
save_klickd.save_klickd(
    payload=payload,
    passphrase="klickd-example-only",
    out_path=str(out),
    domain=payload.get("domain", "general"),
)
print("wrote", out)
PY
```

Les variantes chiffrées **ne sont pas commitées** ici (rien à gagner — elles
sont reproductibles à partir du JSON lisible + de la passphrase publique).

---

## 4. Validation contre le schéma v4-preview

Les 5 fichiers sont écrits pour être **valides** sous le schéma permissif
[`schemas/klickd-payload-v4-preview.schema.json`](../../../schemas/klickd-payload-v4-preview.schema.json)
(`additionalProperties: true` à tous les niveaux, aucune contrainte de type
forte sur les sections preview).

### Checklist DoD (R4-P0-3)

- [x] 5 fichiers correspondant à la matrice de personas de
      [`ROAD-TO-V4-GA.md` §R4-P0-3](../../../docs/roadmap/ROAD-TO-V4-GA.md#r4-p0-3--profils-dexemple-téléchargeables-5-personas).
- [x] Chaque fichier porte `preview: "v4.0.0-preview.1"` et
      `payload_schema_version: "4.0.0-preview.1"`.
- [x] Aucune donnée personnelle réelle, aucun secret, aucun token.
- [x] Passphrase de test publique documentée (`klickd-example-only`), sans
      jamais figurer comme contenu chiffré.
- [x] Validation contre le schéma preview permissif (cf. §5 ci-dessous).
- [ ] Validation stricte v4 ([P0-2 / P0-6](../../../docs/roadmap/ROAD-TO-V4-GA.md)) :
      **différée**. Le schéma strict v4 et les vectors stricts v4 n'existent
      pas encore — la DoD complète sera atteignable une fois P0-2/P0-6 mergés,
      conformément à l'ordre des dépendances inscrit dans ROAD-TO-V4-GA.

### Reproduire la validation locale

```bash
# Python — jsonschema
python3 - <<'PY'
import json, pathlib, jsonschema
schema = json.loads(pathlib.Path("schemas/klickd-payload-v4-preview.schema.json").read_text())
for p in sorted(pathlib.Path("examples/v4/personas").glob("*.klickd")):
    payload = json.loads(p.read_text())
    jsonschema.validate(payload, schema)
    print("OK", p.name)
PY
```

```bash
# Node — Ajv 2020-12
node - <<'JS'
const fs = require("fs");
const path = require("path");
const Ajv = require("ajv/dist/2020").default;
const ajv = new Ajv({strict: false, allErrors: true});
const schema = JSON.parse(fs.readFileSync("schemas/klickd-payload-v4-preview.schema.json", "utf8"));
const validate = ajv.compile(schema);
for (const f of fs.readdirSync("examples/v4/personas").filter(f => f.endsWith(".klickd")).sort()) {
  const payload = JSON.parse(fs.readFileSync(path.join("examples/v4/personas", f), "utf8"));
  if (!validate(payload)) { console.error(f, validate.errors); process.exit(1); }
  console.log("OK", f);
}
JS
```

---

## 5. Champs preview utilisés et leur RFC

| Section | RFC | Personas qui l'utilisent |
|---------|-----|---------------------------|
| `verification_gates` | [RFC-002 v1](../../../docs/rfcs/RFC-002-verification-gates.md) | 1, 2, 3, 4, 5 |
| `human_veto_policy` | RFC-002 v1 | 1, 2, 3, 4, 5 |
| `claim_sources` | RFC-002 v1 | 1, 2, 3, 4, 5 |
| `media_profile` | [RFC-001 v1](../../../docs/rfcs/RFC-001-media-profile-v1.md) | 4 |
| `reversibility` / `blast_radius` | RFC-002 v2-additive | 3 |
| `risk_thresholds` | RFC-002 v1 | 2 |
| `gaming_profile` | R4-P1-4 baseline (preview, registry-based) | 5 |

> Les readers v3.x **doivent ignorer** ces champs ;
> les readers v4-preview **doivent les préserver** verbatim au round-trip
> (cf. [`SPEC.md` §33](../../../SPEC.md)).

---

## 6. Hors-scope explicite

Ce dossier **ne** :

- ne définit pas de schéma strict v4 (track [P0-2](../../../docs/roadmap/ROAD-TO-V4-GA.md)) ;
- ne publie aucune release (`latest` / tag / Zenodo / DOI / npm / PyPI) ;
- ne modifie ni les SDK Python ni `@klickd/core` (l'alignement SDK est suivi
  séparément, cf. R4-P0-3/4 SDK dans `ROAD-TO-V4-GA.md`) ;
- ne définit pas la politique de dépréciation V4 — c'est la prochaine track
  [R4-P0-4](../../../docs/roadmap/ROAD-TO-V4-GA.md#r4-p0-4--politique-de-dépréciation-v4-formelle).
