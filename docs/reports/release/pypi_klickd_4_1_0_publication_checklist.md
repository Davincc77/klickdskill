# Checklist de publication PyPI — `klickd` 4.1.0

> **Statut : `READY_TO_PUBLISH_PENDING_APPROVAL`**
> Tous les contrôles locaux non publiants ont été exécutés avec succès le
> **2026-06-07** (UTC). La publication elle-même reste **en attente
> d'approbation explicite de l'humain**. Aucune commande de publication,
> aucun tag, aucune release, aucun `workflow_dispatch` n'a été lancé.

- **Paquet :** `klickd`
- **Version cible :** `4.1.0`
- **Branche de référence (audit antérieur) :** PR #127, commit `775eb23`
- **Branche de ce document :** `docs/pypi-klickd-4-1-0-publication-checklist`
- **Commit de base au moment des contrôles :** `80aada4`
- **Source canonique du paquet :** `packages/pypi/klickd/`
- **Workflow de publication :** `.github/workflows/publish-pypi.yml`

---

## 0. Comment la publication se déclenche réellement (analyse du workflow)

Fichier : `.github/workflows/publish-pypi.yml`

| Élément | Valeur |
| --- | --- |
| **Déclencheurs (`on:`)** | `release: types: [published]` **et** `workflow_dispatch` (input optionnel `ref`) |
| **Méthode de publication** | **PyPI Trusted Publishing (OIDC)** via `pypa/gh-action-pypi-publish@release/v1` |
| **Environnement GitHub requis** | `environment: pypi` (peut imposer une *protection rule* / approbation de reviewer) |
| **Permissions** | `id-token: write`, `contents: read` |
| **Répertoire de build** | `packages/pypi/klickd` → `python -m build --sdist --wheel --outdir dist/` |
| **Garde de cohérence de version** | Étape « Verify version matches tag » : **uniquement** si `release` ou `refs/tags/*`. Compare `pyproject.toml.version` au tag (en mappant les préfixes SemVer `-preview/-alpha/-beta/-rc` vers PEP 440). Échoue si divergence. |
| **Source d'authentification** | Aucun token PyPI stocké : l'OIDC GitHub→PyPI signe le jeton court. Aucun secret `PYPI_API_TOKEN` n'est utilisé. |

### Conséquences opérationnelles (CE QUI PUBLIE RÉELLEMENT)

Deux et seulement deux actions déclenchent une publication sur **PyPI de production** :

1. **Publier une GitHub Release** (`release: published`) — typiquement créée à
   partir d'un tag `v4.1.0`.
2. **Lancer manuellement `workflow_dispatch`** sur le workflow
   « Publish klickd to PyPI ».

> ⚠️ **Important :** créer un **tag** seul (`git tag` / `git push --tags`) **ne
> publie PAS** par lui-même — le déclencheur est `release: published`, pas
> `push: tags`. Cependant, créer un tag est la première étape qui mène à la
> release ; c'est pourquoi toutes les commandes de tag sont marquées
> **DO NOT RUN UNTIL APPROVED** par prudence.
>
> ⚠️ Il n'existe **aucun** workflow ciblant **TestPyPI** dans ce dépôt. Ne pas
> improviser une publication TestPyPI sans décision explicite.

---

## 1. Préconditions (à vérifier AVANT toute publication)

- [x] Version cohérente dans les 3 emplacements : `4.1.0`
  - `pyproject.toml` (racine, shim dev) → `4.1.0`
  - `packages/pypi/klickd/pyproject.toml` (canonique) → `4.1.0`
  - `packages/pypi/klickd/src/klickd/__init__.py` `__version__` → `4.1.0`
- [x] Build local sdist + wheel réussi (voir §5).
- [x] Tests du paquet : **109 passés / 1 ignoré**.
- [x] Smoke d'import depuis le wheel construit : OK (`klickd.__version__ == 4.1.0`).
- [x] Contenu wheel/sdist inspecté : 4 schémas, 5 starter skills, 42 packs
      x.klickd, métadonnées PEP 440 correctes.
- [x] Scan de secrets sur la source ET les artefacts : **aucun secret détecté**.
- [ ] **(MANUEL, réseau requis — NON exécuté ici)** Confirmer que `klickd==4.1.0`
      n'existe **pas déjà** sur PyPI (PyPI refuse le ré-upload d'une version
      existante) : `pip index versions klickd` ou consulter
      `https://pypi.org/project/klickd/#history`.
- [ ] **(MANUEL)** Confirmer que l'environnement GitHub `pypi` est bien
      configuré comme *Trusted Publisher* côté PyPI (projet `klickd`,
      propriétaire `Davincc77/klickdskill`, workflow `publish-pypi.yml`,
      environnement `pypi`).
- [ ] **(MANUEL)** Confirmer que le contenu à publier correspond bien au commit
      validé par l'audit (PR #127 / `775eb23`) — ou rebaser/merger d'abord.
- [ ] **(MANUEL)** `CHANGELOG.md` à jour pour 4.1.0 (déjà présent : section
      « packaging 4.1.0 — 2026-05-30 »).

---

## 2. Commandes locales EXACTES — build / check / test (SÛRES, ne publient pas)

Toutes ces commandes sont **locales et non publiantes**. Elles écrivent les
artefacts hors du dépôt (`/tmp`) pour ne jamais committer de binaires.

```bash
# Depuis la racine du dépôt
cd packages/pypi/klickd

# 1) Build propre dans /tmp (jamais dans le dépôt)
rm -rf /tmp/klickd_build && mkdir -p /tmp/klickd_build
python -m build --sdist --wheel --outdir /tmp/klickd_build/

# 2) Tests
cd /home/user/workspace/klickdskill-7d53bdf0
python -m pytest packages/pypi/klickd/tests -q

# 3) Smoke d'import depuis le wheel construit (venv isolé)
python -m venv --system-site-packages /tmp/klickd_smoke
/tmp/klickd_smoke/bin/pip install --no-index --no-deps \
  /tmp/klickd_build/klickd-4.1.0-py3-none-any.whl
/tmp/klickd_smoke/bin/python -c "import klickd, importlib.metadata as m; \
  print(klickd.__version__, m.version('klickd'))"

# 4) Inspection du contenu
python -m zipfile -l /tmp/klickd_build/klickd-4.1.0-py3-none-any.whl
tar -tzf /tmp/klickd_build/klickd-4.1.0.tar.gz | sort

# 5) Validation métadonnées (UNIQUEMENT si twine est déjà installé)
#    Ne PAS installer twine s'il faut le réseau ; sinon :
python -m twine check /tmp/klickd_build/*
```

> Le build CI utilise exactement `python -m build --sdist --wheel --outdir
> dist/` dans `packages/pypi/klickd`. La commande locale ci-dessus est
> identique sauf `--outdir /tmp/klickd_build/` pour ne rien committer.

---

## 3. Commandes git / tag / release qui PUBLIERAIENT — ⛔ DO NOT RUN UNTIL APPROVED ⛔

> **NE PAS EXÉCUTER ces commandes sans approbation humaine explicite.**
> Chacune mène, directement ou par la release qui suit, à un upload
> **irréversible** sur PyPI (PyPI interdit la suppression/réutilisation d'une
> version publiée).

### Option A — Tag + GitHub Release (chemin nominal)

```bash
# ⛔ DO NOT RUN UNTIL APPROVED ⛔
# 1) Se placer sur le commit exact validé par l'audit (PR #127 / 775eb23),
#    typiquement après merge sur main.
git checkout main
git pull --ff-only

# 2) Créer le tag annoté v4.1.0 (PUBLIANT en aval — déclenche la release)
#    ⛔ DO NOT RUN UNTIL APPROVED ⛔
git tag -a v4.1.0 -m "klickd 4.1.0"

# 3) Pousser le tag  ⛔ DO NOT RUN UNTIL APPROVED ⛔
git push origin v4.1.0

# 4) Créer ET publier la GitHub Release → DÉCLENCHE publish-pypi.yml
#    ⛔ DO NOT RUN UNTIL APPROVED ⛔  (c'est CETTE étape qui publie)
gh release create v4.1.0 \
  --title "klickd 4.1.0" \
  --notes "klickd 4.1.0 — voir CHANGELOG.md"
```

### Option B — Déclenchement manuel du workflow (workflow_dispatch)

```bash
# ⛔ DO NOT RUN UNTIL APPROVED ⛔  — publie directement sur PyPI prod
gh workflow run "Publish klickd to PyPI" --ref v4.1.0 -f ref=v4.1.0
```

> Rappel : l'environnement GitHub `pypi` peut exiger une **approbation de
> reviewer** avant que le job de publication ne s'exécute — c'est une
> protection supplémentaire à conserver.

---

## 4. Plan de rollback / vérification

PyPI **n'autorise pas** la republication d'une version. Le « rollback » réel
consiste donc à publier un **correctif** et, au besoin, à *yanker* la version
fautive (elle reste téléchargeable par épinglage mais n'est plus sélectionnée
par défaut).

```bash
# Vérifier ce qui est en ligne (réseau requis)
pip index versions klickd

# Yank d'une version problématique (NE PAS exécuter sans décision) :
#   → via l'UI PyPI : projet klickd → Releases → 4.1.0 → "Yank".
#   (Le yank ne supprime pas, il déclasse.)

# Correctif : bump vers 4.1.1 dans les 3 emplacements de version, rebuild,
# re-tag v4.1.1, nouvelle release. Même procédure que §3.
```

Garde-fous existants qui limitent le risque de mauvaise publication :
- Garde de cohérence version↔tag dans le workflow (échoue si divergence).
- Trusted Publishing OIDC : pas de token long-vivant à fuiter.
- Environnement `pypi` (protection rule possible).

---

## 5. Vérification post-publication (réseau requis — APRÈS approbation)

```bash
# 1) La version apparaît sur PyPI
pip index versions klickd          # doit lister 4.1.0
# ou : https://pypi.org/project/klickd/4.1.0/

# 2) Installation propre dans un venv neuf (avec dépendances, depuis PyPI)
python -m venv /tmp/klickd_verify
/tmp/klickd_verify/bin/pip install "klickd==4.1.0"
/tmp/klickd_verify/bin/python -c "import klickd, importlib.metadata as m; \
  assert klickd.__version__ == '4.1.0'; \
  assert m.version('klickd') == '4.1.0'; print('PyPI install OK')"

# 3) Extra optionnel
/tmp/klickd_verify/bin/pip install "klickd[validate]==4.1.0"
/tmp/klickd_verify/bin/python -c "import jsonschema; print('validate extra OK')"

# 4) Vérifier le run GitHub Actions
gh run list --workflow "Publish klickd to PyPI" --limit 3
```

---

## 6. Règle de mise à jour du « Sentinel » après publication

> **Définition.** Le *Sentinel* est le marqueur d'état de release qui indique
> « 4.1.0 effectivement publié sur PyPI ». Aucun fichier sentinel formel
> n'existe encore dans ce dépôt ; la règle ci-dessous fixe la convention.

**Ne mettre à jour le Sentinel qu'APRÈS confirmation que `klickd==4.1.0` est
visible et installable depuis PyPI (§5).** Tant que les vérifications post-
publication ne sont pas vertes, le statut reste
`READY_TO_PUBLISH_PENDING_APPROVAL`.

Après publication confirmée :

1. Mettre à jour l'en-tête de ce document : statut →
   `PUBLISHED` avec la date UTC réelle et l'URL
   `https://pypi.org/project/klickd/4.1.0/`.
2. Cocher la précondition « confirmer que 4.1.0 n'existe pas déjà » comme
   désormais **satisfaite par cette publication**.
3. Si une PR de release reste ouverte (p. ex. #127), la fermer/merger selon la
   décision humaine — **pas automatiquement**.
4. Consigner l'URL du run GitHub Actions de publication dans le journal §7.

---

## 7. Journal d'exécution des contrôles locaux (2026-06-07, UTC)

Environnement : Python 3.12.8, pip 24.3.1, `build` 1.5.0 présent, `pytest`
9.0.3 présent. `twine` **absent** et **non installable hors-ligne** → contrôle
`twine check` **non exécuté** (conforme à la consigne « ne pas installer de
dépendances réseau »). Validation des métadonnées effectuée par inspection
directe du `METADATA` du wheel.

| # | Contrôle | Commande (résumé) | Résultat |
| --- | --- | --- | --- |
| 1 | Cohérence de version | grep `4.1.0` sur les 3 fichiers | ✅ `4.1.0` partout |
| 2 | Build sdist+wheel | `python -m build … --outdir /tmp/klickd_build/` | ✅ `klickd-4.1.0.tar.gz` + `klickd-4.1.0-py3-none-any.whl` |
| 3 | Tests | `pytest packages/pypi/klickd/tests -q` | ✅ **109 passés, 1 ignoré** (10.4 s) |
| 4 | Smoke import (wheel) | venv `--no-deps` + `import klickd` | ✅ `__version__=4.1.0`, `metadata.version=4.1.0` |
| 5 | Métadonnées wheel | inspection `METADATA` | ✅ Metadata-Version 2.4 ; 4 `Requires-Dist` ; extra `validate` ; classifiers Py 3.9–3.12 |
| 6 | Tag wheel | lecture `WHEEL` | ✅ `py3-none-any`, purelib, hatchling 1.30.1 |
| 7 | Contenu sdist | `tar -tzf` | ✅ src complet + tests + 4 schémas + 5 starter + 42 packs x.klickd |
| 8 | Contenu wheel | `zipfile -l` | ✅ mêmes ressources, `dist-info` cohérent |
| 9 | `twine check` | indisponible hors-ligne | ⏭️ ignoré (consigne) — remplacé par inspection métadonnées |
| 10 | Scan secrets (source) | regex clés AWS/GH/Slack/OpenAI/PyPI/npm + mots-clés | ✅ aucun secret |
| 11 | Scan secrets (artefacts) | idem sur sdist + wheel extraits | ✅ aucun secret ; aucun `.env/.pem/.key` embarqué |

### Artefacts produits (hors dépôt, non committés)

```
/tmp/klickd_build/klickd-4.1.0.tar.gz            (~83 KB)
/tmp/klickd_build/klickd-4.1.0-py3-none-any.whl  (~196 KB)
```

### Métadonnées clés du wheel (extrait)

```
Metadata-Version: 2.4
Name: klickd
Version: 4.1.0
Requires-Python: >=3.9
Requires-Dist: argon2-cffi>=23.1
Requires-Dist: cryptography>=41.0
Requires-Dist: jcs>=0.2
Requires-Dist: typing-extensions>=4.8
Provides-Extra: validate
Requires-Dist: jsonschema>=4.18; extra == 'validate'
License: CC0-1.0
```

---

## 8. Verdict

**`READY_TO_PUBLISH_PENDING_APPROVAL`**

Tous les contrôles locaux non publiants sont verts. Le paquet `klickd==4.1.0`
se construit, s'importe, passe ses tests (109/1), embarque les bonnes
ressources et métadonnées, et ne contient aucun secret.

### Requiert une approbation humaine explicite avant exécution

1. **Vérification réseau préalable** : confirmer que `klickd==4.1.0` n'existe
   pas déjà sur PyPI (§1).
2. **Création du tag `v4.1.0`** (`git tag` / `git push origin v4.1.0`) — §3.
3. **Publication de la GitHub Release `v4.1.0`** (`gh release create`) — c'est
   l'action qui **déclenche la publication PyPI** — §3 Option A.
4. **OU** déclenchement manuel `workflow_dispatch` du workflow
   « Publish klickd to PyPI » — §3 Option B.
5. **Approbation éventuelle de l'environnement GitHub `pypi`** (reviewer) si la
   protection rule est active.
6. **Vérifications post-publication** (§5) et **mise à jour du Sentinel** (§6).

> Aucune de ces actions n'a été exécutée. Aucun tag, aucune release, aucun
> dispatch, aucune publication PyPI/TestPyPI n'a été effectué par ce travail.
