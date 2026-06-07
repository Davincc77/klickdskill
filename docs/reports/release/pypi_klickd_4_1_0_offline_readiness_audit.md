# Audit hors-ligne de préparation à la publication PyPI — `klickd` 4.1.0

- **Dépôt** : `Davincc77/klickdskill`
- **Branche auditée** : `main`
- **Commit (HEAD au moment de l'audit)** : `80aada4d971455a009e139db6f35bdd87c306b1a`
- **Date de l'audit** : 2026-06-07
- **Type d'audit** : inspection / build / tests strictement **hors-ligne**. Aucune publication PyPI ou TestPyPI. Aucun appel à un LLM ou une API externe.

---

## Verdict : **READY** (prêt à publier)

Le paquet Python `klickd==4.1.0` est **prêt à être publié sur PyPI**. La version,
les métadonnées, les artefacts construits, les tests et la parité avec le paquet
npm `@klickd/core@4.1.0` sont tous cohérents. Aucun bloquant n'a été identifié.
Un point mineur **non bloquant** (impossibilité d'exécuter `twine check` faute
de l'outil en local) est documenté plus bas, avec une vérification de
substitution équivalente qui réussit.

---

## 1. Localisation des fichiers du paquet Python

Le paquet **canonique et publié** se trouve dans :

```
packages/pypi/klickd/
├── pyproject.toml                 # métadonnées de packaging faisant autorité
├── README.md                      # long_description (text/markdown)
├── src/klickd/                    # arbre source du paquet
│   ├── __init__.py                # __version__ = "4.1.0"
│   ├── _types.py, decode.py, encode.py, errors.py, migrate.py, validate.py
│   ├── starter_skills_resources.py, x_klickd_skills_resources.py
│   ├── schemas/                   # 4 schémas JSON v4 (payload + envelope, GA + preview)
│   ├── starter_skills/            # 4 fichiers .klickd + manifest.json + README.md
│   └── x_klickd_skills/           # 42 packs .klickd v4.1 candidats + manifest.json
└── tests/                         # 7 modules de test + fixtures
```

- **`pyproject.toml` racine** (`/pyproject.toml`) : c'est un **shim d'installation
  de développement** uniquement (`pip install -e .` depuis la racine du clone). Il
  cible le **même** arbre source (`packages/pypi/klickd/src/klickd`) et n'est
  **jamais publié**. Sa version est également `4.1.0`, cohérente avec le paquet
  canonique.
- **Workflow de publication CI** : `.github/workflows/publish-pypi.yml`.
  - Déclencheurs : `release: [published]` et `workflow_dispatch`.
  - Build : `python -m build --sdist --wheel` dans `packages/pypi/klickd`.
  - Garde de cohérence version/tag (mapping SemVer prerelease → PEP 440).
  - Publication via **PyPI Trusted Publishing (OIDC)** — pas de jeton longue durée.
- `MANIFEST.in` : **absent**. Non requis ici : le backend `hatchling` inclut
  automatiquement les sous-répertoires `schemas/`, `starter_skills/` et
  `x_klickd_skills/` car ils font partie de l'arbre `src/klickd` sélectionné.

## 2. Version courante et existence de la configuration 4.1.0

| Emplacement | Version |
|-------------|---------|
| `packages/pypi/klickd/pyproject.toml` → `[project].version` | **4.1.0** |
| `packages/pypi/klickd/src/klickd/__init__.py` → `__version__` | **4.1.0** |
| `pyproject.toml` racine (shim dev) | **4.1.0** |
| Métadonnées du wheel construit (`METADATA`) | **4.1.0** |
| Métadonnées du sdist (`PKG-INFO`) | **4.1.0** |
| `importlib.metadata.version('klickd')` après installation du wheel | **4.1.0** |

La configuration 4.1.0 **existe et est cohérente partout**. La dernière version
publiée sur PyPI est `4.0.1` ; `4.1.0 > 4.0.1`, donc **aucune collision de
version** sur PyPI. Le npm `@klickd/core` est déjà à `4.1.0` (lock-step).

> Note : la racine `package.json` (`klickdskill`, v4.0.0, `private: true`) est le
> harnais de test/vecteurs du dépôt, **pas** le SDK npm. Le SDK npm publiable est
> `packages/@klickd/core` (v4.1.0).

## 3. Journal des changements / notes de version 4.1.0

`CHANGELOG.md` contient une entrée datée **4.1.0 — 2026-05-30** :
« `@klickd/core` and `klickd` SDK minor release; x.klickd v4.1 candidate track
documented ». Points saillants :

- Montée de version en lock-step npm + PyPI `4.0.3 → 4.1.0`.
- L'enveloppe filaire `.klickd` normative reste **v4.0.0 GA** ; les 4 schémas JSON
  et les 4 fichiers starter `.klickd` sont **inchangés** depuis 4.0.0 (octet pour
  octet, même manifeste SHA-256).
- Les 42 packs x.klickd v4.1 sont explicitement **candidats / non-GA**
  (`_pack_metadata.claims_v41_ga: false`).
- Cette version **ne crée pas** de tag git, de Release GitHub, de DOI Zenodo ni
  d'action IANA — c'est une **release de packaging/SDK uniquement**.

## 4. Construction locale du wheel et du sdist

Construction réalisée hors-ligne avec `python -m build` (backend `hatchling`,
environnement isolé). **Succès** :

```
Successfully built klickd-4.1.0.tar.gz and klickd-4.1.0-py3-none-any.whl
```

| Artefact (local uniquement, dans `/tmp/klickd_dist/`) | Taille | SHA-256 |
|--------------------------------------------------------|--------|---------|
| `klickd-4.1.0-py3-none-any.whl` | ~192 Ko (196 437 o) | `db8029f1d5ad273cdb3d1780e22f03c0e04a8e3225d2e137c7dd3c426a91d633` |
| `klickd-4.1.0.tar.gz` (sdist) | ~81 Ko (83 213 o) | `736a4c8257b722ca89a0ece31397ab27554735f500632171b4c091d3f7e59d37` |

> Les artefacts ne sont **pas** commités (le dépôt ignore `dist/` et
> `release-artifacts/` via `.gitignore`). Chemins locaux seulement.

## 5. Inspection des artefacts construits

- **Métadonnées (wheel `METADATA`)** : `Metadata-Version: 2.4`, `Name: klickd`,
  `Version: 4.1.0`, `Description-Content-Type: text/markdown`.
- **Dépendances** : `cryptography>=41.0`, `argon2-cffi>=23.1`, `jcs>=0.2`,
  `typing-extensions>=4.8` ; extra `validate` → `jsonschema>=4.18`.
- **Licence** : `License: CC0-1.0` + classifier
  `License :: CC0 1.0 Universal (CC0 1.0) Public Domain Dedication`.
- **Classifiers** : Production/Stable, Developers, Python 3 / 3.9–3.12,
  Cryptography, Libraries — cohérents avec `requires-python = ">=3.9"`.
- **Contenu inclus** (wheel **et** sdist) :
  - 9 modules Python (`__init__`, `_types`, `decode`, `encode`, `errors`,
    `migrate`, `validate`, `starter_skills_resources`, `x_klickd_skills_resources`).
  - **4 schémas JSON** (`klickd-payload-v4`, `klickd-payload-v4-preview`,
    `klickd-v4`, `klickd-v4-preview`).
  - **4 starter skills** `.klickd` + `manifest.json` + `README.md`.
  - **42 packs x_klickd** `.klickd` + `manifest.json`.
  - Le sdist inclut en plus les tests + fixtures (bon pour une distribution source).
- **Validation des métadonnées** : `twine` **n'est pas installé** en local. En
  substitution, validation stricte via `packaging.metadata.Metadata.from_email(...,
  validate=True)` → **succès** (nom/version/content-type conformes, pas d'erreur
  de champ). Le rendu Markdown du README est correct (`text/markdown`).
- **Installation hors-ligne** : `pip install --no-index --no-deps <wheel>` dans un
  venv neuf → installé, `importlib.metadata.version('klickd') == 4.1.0`.

## 6. Tests et tests de fumée d'import

- **Suite de tests du paquet** (`pytest` dans `packages/pypi/klickd`) :
  **109 réussis, 1 ignoré (skip), 0 échec** (~11 s). Toutes les dépendances
  d'exécution + l'extra `validate` étaient déjà présentes localement — **aucun
  téléchargement réseau requis**.
- **Test de fumée fonctionnel** de la surface publique :
  - `klickd.__version__ == "4.1.0"`.
  - Aller-retour chiffrement/déchiffrement (`save_klickd` / `load_klickd`) : OK.
  - `list_starter_skills()` → `['coding', 'research', 'student', 'user']`.
  - `list_xklickd_skill_packs()` → **42** ; `load_xklickd_skill_pack(...)` →
    `artifact_loaded = True`, `sha256_matches_manifest = True`.
  - `validate(..., strict=True)` sur un payload v4 GA : OK.

## 7. Recherche de secrets (fichiers source + artefacts)

Balayage des fichiers source (`src/`, `tests/`, `pyproject.toml`, `README.md`) et
des artefacts extraits (wheel + sdist) pour motifs : clés AWS (`AKIA…`), jetons
PyPI (`pypi-AgEI…`), jetons GitHub (`ghp_…`/`gho_…`), jetons npm, jetons Slack
(`xox…`), clés privées PEM, `password=`/`token=`, fichiers `.env`/`.pem`/`.npmrc`/`.pypirc`.

**Résultat : aucun secret.** Le seul « match » brut était un hash SHA-256 légitime
dans le fichier `RECORD` du wheel (faux positif du filtre de sous-chaîne `secret`),
sans rapport avec un identifiant. Aucun fichier d'identifiants parasite.

## 8. Parité avec npm `@klickd/core` 4.1.0

| Élément | npm `@klickd/core` 4.1.0 | PyPI `klickd` 4.1.0 | Parité |
|---------|--------------------------|---------------------|--------|
| Version | 4.1.0 | 4.1.0 | ✅ identique |
| Licence | CC0-1.0 | CC0-1.0 | ✅ |
| Starter skills (noms) | 4 | 4 | ✅ identiques |
| Starter skills (octets, SHA-256) | — | — | ✅ **4/4 identiques** |
| Packs x.klickd (noms) | 42 | 42 | ✅ identiques |
| Packs x.klickd (octets, SHA-256) | — | — | ✅ **42/42 identiques** |
| Schémas JSON v4 (octets, SHA-256) | 4 | 4 | ✅ **4/4 identiques** |
| Homepage / Repository | klickd.app/klickdskill / GitHub | idem | ✅ |

La surface (schémas, packs, starter skills) est **byte-identique** entre les deux
SDK 4.1.0 — parité totale confirmée par comparaison SHA-256.

---

## Bloquants

**Aucun bloquant.**

## Points mineurs non bloquants

1. **`twine check` non exécuté** : l'outil `twine` n'est pas installé dans
   l'environnement d'audit (mode hors-ligne, pas d'installation réseau). La
   validation de substitution stricte (`packaging.metadata`, `Metadata-Version 2.4`)
   réussit, ce qui couvre l'essentiel des contrôles de `twine check`. **Recommandé**
   d'exécuter un `twine check dist/*` réel dans la CI avant publication (à des fins
   de confirmation, pas un bloquant).
2. **Licence : double déclaration** : les métadonnées portent à la fois
   `License: CC0-1.0` (champ texte) et un classifier `License :: …`. Avec
   `Metadata-Version 2.4`, c'est une combinaison dépréciée mais **acceptée** par
   PyPI/twine (avertissement doux possible). Optionnel : migrer plus tard vers une
   expression SPDX `license = "CC0-1.0"` sans classifier de licence.

---

## Prochaines étapes recommandées

1. **Publier `klickd==4.1.0` sur PyPI** via le workflow `publish-pypi.yml` :
   créer le tag/Release approprié (la garde version↔tag du workflow validera la
   cohérence), publication via Trusted Publishing OIDC.
2. Avant publication, laisser la CI exécuter `twine check dist/*` (confirmation).
3. (Optionnel, ultérieur) Nettoyer la double déclaration de licence en passant à
   l'expression SPDX.

---

## Annexe — Reproductibilité (hors-ligne)

```bash
# Build (hors-ligne, backend hatchling)
cd packages/pypi/klickd
python -m build --sdist --wheel --outdir /tmp/klickd_dist

# Tests
python -m pytest -q          # 109 passed, 1 skipped

# Validation métadonnées (substitut twine)
python -c "import zipfile,packaging.metadata as m; \
  m.Metadata.from_email(zipfile.ZipFile('/tmp/klickd_dist/klickd-4.1.0-py3-none-any.whl').read('klickd-4.1.0.dist-info/METADATA'), validate=True)"

# Parité SHA-256 npm vs PyPI : 4/4 starter, 42/42 packs, 4/4 schémas → identiques
```
