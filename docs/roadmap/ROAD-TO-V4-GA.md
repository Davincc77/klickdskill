# Road to `.klickd` v4 GA

> **Status:** Draft · NON-NORMATIVE · structuration de travail.
> **Scope:** backlog priorisé décrivant ce qui sépare `v4.0.0-preview.1`
> (déjà mergé) d’un `v4.0.0` réellement livrable et adoptable.
> **Ce document n’est pas une promesse de calendrier**, ne déclenche aucun
> publish (npm / PyPI / Zenodo), aucun tag, aucune release.
>
> La version production recommandée reste **v3.5.1**.
> La version preview existante reste **v4.0.0-preview.1** (additive,
> non-normative, voir [`docs/releases/v4.0.0-preview.1.md`](../releases/v4.0.0-preview.1.md)).

---

## 0. Pourquoi cette doc

`v4.0.0-preview.1` a posé les bases de la track v4 :

- SPEC §33 (preview, non-normative)
- schémas permissifs (`additionalProperties: true`)
- SDKs round-trip-preserving (`klickd==4.0.0a1`, `@klickd/core@4.0.0-preview.1` — preview, jamais `latest`)
- RFC-001 / 002 (v1 core) / 004 en **Proposed** (promues 2026-05-23, docs-only). RFC-003 et RFC-002 §8b (v2 additions) restent **Draft**.
- RFC-006 (`agent_core` / Agent Operating Context, première itération, future-work) en **Draft** — voir [`docs/rfcs/RFC-006-agent-core.md`](../rfcs/RFC-006-agent-core.md). **Hors P0 GA** : post-GA / showcase first-party `core.Kai.klickd`.
- UX spec ([`docs/ux/V4-UX-SPEC.md`](../ux/V4-UX-SPEC.md))
- vectors `vectors_v40_preview.json`
- CI : `test-vectors`, `verify-npm-preview`

Une `v4.0.0` (GA) demande davantage : un **schéma strict**, des SDKs avec
surface publique pour les sections v4, un **migrateur** (RFC-004), des
**vectors de migration**, des benchmarks reproductibles (RFC-003), et un
matériel d’adoption (docs, exemples, viewer). Ce document liste, priorise et
définit les critères de sortie de chacun de ces chantiers.

Principe directeur, hérité de RFC-004 : **« Never break the soul. »** Aucune
étape ne doit dégrader, deviner, ou inventer un champ déjà écrit par un
utilisateur en v2.5 / v3.x / v3.5.1 / v4-preview.

---

## 1. Distinction preview vs GA

| Aspect | `v4.0.0-preview.1` (existant) | `v4.0.0` (GA cible) |
|---|---|---|
| SPEC | §33 marquée **Non-Normative** | §33 promue normative (ou refonte SPEC v4) |
| Schémas | permissifs (`additionalProperties: true`) | stricts, par section (media/gates/migration/context_cost) |
| SDK | round-trip opaque | API publique typée pour lire/écrire/valider les sections v4 |
| Migration | aucune (RFC-004 = Draft) | migrateur réel + `migration_report` + rollback |
| Vectors | `vectors_v40_preview.json` | vectors stricts + vectors de migration v2.5/v3.x/v3.5.1 → v4 |
| Benchmark | RFC-003 dry-run scaffold | RFC-003 mesures reproductibles + rapport publié |
| UI | UX spec docs-only | viewer / decryptor / validator / migrator de référence |
| Distribution | npm `preview` dist-tag, PyPI `a1`, **pas de Zenodo** | npm `latest`, PyPI stable, DOI Zenodo, IANA MIME |
| Annonce publique | aucune (preview interne) | post Hermes/dev.to + landing klickd.app |

> **Règle ferme :** tant que `v4.0.0` n’est pas livré, **rien ne publie en `latest`**, **aucun tag `v4.0.0`** n’est créé, **aucun DOI Zenodo v4** n’est minté.

---

## 2. Backlog priorisé

Trois niveaux de priorité :

- **P0 — bloquant GA.** Sans cet item, on ne peut pas appeler la version `v4.0.0`.
- **P1 — bloquant adoption.** Pas bloquant pour le tag, mais sans cet item l’adoption externe est irréaliste.
- **P2 — souhaitable / extension.** Améliore l’histoire produit ; reportable post-GA si besoin.

Chaque entrée précise : *Objet → Livrables → Critères de sortie (Definition of Done) → Dépendances*.

### 2.1 P0 — bloquant GA

#### P0-1 — SPEC normative v4

- **Objet :** transformer la §33 preview en surface normative (ou réécrire SPEC en version 4 dédiée), avec règles de compat ascendante explicites.
- **Livrables :** `SPEC.md` v4 (ou nouveau document `SPEC_v4.md` puis bascule), table de version, règle de préservation des champs inconnus durcie, sunset policy du preview.
- **DoD :**
  - aucun MUST/SHOULD ambigu dans les sections v4 ;
  - règles de coexistence v3.x ↔ v4 explicites (un reader v3.x **doit** ignorer en silence ; un reader v4 **doit** round-tripper) ;
  - mention IANA MIME `application/vnd.klickd+json` confirmée ou explicitement déférée.
- **Dépendances :** RFC-001/002/004 promues `Accepted`.

#### P0-2 — JSON Schema strict v4

- **Objet :** schéma `klickd-v4.schema.json` (envelope + payload) avec `additionalProperties: false` sur les sections normées, en gardant la règle « unknown fields toléré au niveau racine pour préservation ».
- **Livrables :** `schema/klickd-v4.schema.json`, `schemas/klickd-payload-v4.schema.json`, `SCHEMA_INDEX.md` mis à jour.
- **DoD :**
  - schéma valide en Draft 2020-12 ;
  - validation passe sur tous les vectors v4 stricts ;
  - les vectors preview restent acceptés via le schéma preview (deux schémas coexistent jusqu’au sunset).
- **Dépendances :** P0-1.

#### P0-3 — SDK Python `klickd` 4.0.0

- **Objet :** API publique typée pour les sections v4 (`media_profile`, `verification_gates`, `human_veto_policy`, `claim_sources`, `verification_artifacts`, `migration`, `context_cost`), validation stricte + permissive, round-trip garanti.
- **Livrables :** `packages/pypi/klickd/` mis à jour, tests unitaires + vectors, type hints complets, `4.0.0` final (preview = `a1` → `b*` → `rc*` → `4.0.0`).
- **DoD :**
  - 100 % des vectors v4 stricts passent en validation ;
  - tous les vectors v3.x continuent à passer (régression zéro) ;
  - aucun MUST de SPEC v4 non couvert par un test ;
  - aucun publish PyPI tant que P0-1/2/4 ne sont pas verts (publish manuel sur décision Vince).
- **Dépendances :** P0-1, P0-2.

#### P0-4 — SDK JS/TS `@klickd/core` 4.0.0

- **Objet :** parité fonctionnelle avec le SDK Python (mêmes sections, mêmes vectors), dual ESM/CJS, Argon2id parity (lever le skip CI noté en ROADMAP v4 GA).
- **Livrables :** `packages/@klickd/core/` mis à jour, tests Jest + vectors, types `.d.ts`, build dist.
- **DoD :**
  - 100 % des vectors v4 stricts passent ;
  - Argon2id natif fonctionnel en Node ≥ 20 (plus de fallback skip) ;
  - aucun publish npm tant que P0-1/2/3 ne sont pas verts ;
  - cross-impl test vectors (Python ↔ JS) à 100 %.
- **Dépendances :** P0-1, P0-2, P0-3.

#### P0-5 — Migrateur RFC-004

- **Objet :** outil réel et reproductible pour migrer `v2.5 → v3.x → v3.5.1 → v4`, avec **backup obligatoire**, **`migration_report`** émis, **confirmation utilisateur**, **rollback documenté**, **préservation verbatim** des champs inconnus.
- **Livrables :**
  - module `klickd.migrate` (Python) et `@klickd/core/migrate` (JS) ;
  - CLI `klickd migrate <fichier>` ;
  - vectors `vectors_v4_migration.json` (cas heureux + cas dégradés : champ inconnu, KDF v2 PBKDF2, AAD 4-fields, payload tronqué…) ;
  - doc utilisateur `docs/migration/V4-MIGRATION.md`.
- **DoD :**
  - aucun champ silencieusement perdu sur les vectors de référence ;
  - rollback testé et documenté ;
  - aucune migration n’écrit le fichier d’origine (toujours un nouveau fichier + report).
- **Dépendances :** P0-1, P0-2, P0-3, P0-4.

#### P0-6 — Vectors stricts + cross-impl

- **Objet :** suite de vectors v4 *normative*, séparée de la suite preview, partagée Python ↔ JS, qui couvre toutes les sections v4 normées.
- **Livrables :** `tests/vectors_v40.json`, `tests/roundtrip_v40.json`, `tests/negative_vectors_v40.json`, CI `test-vectors` étendu.
- **DoD :**
  - chaque MUST de SPEC v4 a au moins un vecteur positif et un vecteur négatif ;
  - exécutés par les deux SDKs sans divergence ;
  - les vectors preview ne disparaissent pas (preuve de continuité).
- **Dépendances :** P0-2, P0-3, P0-4.

### 2.2 P1 — bloquant adoption

#### P1-1 — README / landing / docs

- **Objet :** mettre à jour `README.md` racine, `SCHEMA_INDEX.md`, et le contenu de `klickd.app` (hors-repo) pour refléter v4 GA sans casser la lisibilité des sections v3.x.
- **Livrables :** `README.md`, `SCHEMA_INDEX.md`, `docs/v4/README.md` (index v4), bandeau preview → GA.
- **DoD :** un nouvel arrivant peut comprendre, en moins de 5 minutes, *quelle* version utiliser et *pourquoi*.

#### P1-2 — Exemples & integrations

- **Objet :** mettre à jour `examples/`, `integrations/hermes/`, snippets Python/JS pour utiliser l’API v4 (sans casser les exemples v3.x).
- **Livrables :** `examples/v4/`, doc d’intégration agent (system-prompt injection), exemples avec `verification_gates` et `claim_sources`.
- **DoD :** chaque exemple est exécutable localement et documente clairement *preview vs GA*.

#### P1-3 — Context Cost Benchmark (RFC-003) — exécution

- **Objet :** passer de fixtures dry-run à des mesures reproductibles, publiées dans `benchmarks/context_cost/`.
- **Livrables :** runner exécutable, jeux de scénarios, rapport `benchmarks/context_cost/REPORT.md`.
- **DoD :** un tiers peut reproduire les chiffres avec le runner local, sans clés provider.

#### P1-4 — Démo Hermes / dev.to

- **Objet :** finaliser le POC `integrations/hermes/` en démo publiable (article dev.to, vidéo courte, lien public), sans appel API payant.
- **Livrables :** scénario reproductible, README démo, lien article (à publier hors-repo).
- **DoD :** la démo tourne avec un `.klickd` test, montre la valeur portable, ne dépend d’aucun secret.

#### P1-5 — Viewer / decryptor / validator de référence

- **Objet :** implémenter le matériel UX décrit dans [`docs/ux/V4-UX-SPEC.md`](../ux/V4-UX-SPEC.md) (Open & decrypt, Validate, Summary, Rules & Gates, Evidence).
- **Livrables :** `demo/` enrichi (web local, zero-server), ou paquet séparé `viewer/`, conforme au principe local-first.
- **DoD :** un utilisateur peut ouvrir un `.klickd` v4, lire un Summary, voir les gates, sans aucun upload ni télémétrie.

#### P1-6 — Vectors de migration v2.5/v3.x/v3.5.1 → v4

- **Objet :** suite de vectors dédiée à la migration (entrée + sortie + report attendu).
- **Livrables :** `tests/migration_v40.json`, intégration au runner CI.
- **DoD :** aucun champ legacy perdu ; rollback testé sur chaque entrée.
- **Dépendances :** P0-5.

#### P1-7 — RFC-006 (`agent_core`) profile + invariant no-PII (docs-only)

- **Objet :** stabiliser la surface conceptuelle de `agent_core` ([RFC-006](../rfcs/RFC-006-agent-core.md)) **sans toucher** au schéma strict v4 ni aux SDKs : profil de champs, invariant *no-PII* (§6), invariant *one-file-one-role* (§4 #1), contrat d'injection slices (§7), provenance/versioning (§8), relations RFC-002 (gates : user wins on conflict) et RFC-003 (benchmark cross-provider).
- **Livrables :** RFC-006 promue `Draft → Proposed`, exemple non-normatif `docs/rfcs/examples/agent_core-v1.example.json` aligné, ajout dans `SCHEMA_INDEX.md` d'une ligne *RFC-006 (sketch, no schema yet)*, note dans `docs/rfcs/README.md`.
- **DoD :**
  - RFC-006 explicite `MUST` / `SHOULD` / `MAY` (RFC 2119) sur l'invariant no-PII et la résolution de conflit `default_verification_gates` ↔ `verification_gates` ;
  - aucun SDK, schéma, ou vector modifié ;
  - aucune mention de `core.Kai.klickd` comme livrable shippable (uniquement showcase concept, voir P2) ;
  - GA `v4.0.0` reste **non bloquée** par cet item — il n'entre pas dans la liste P0.
- **Dépendances :** P0-1 (SPEC normative v4) en cours, RFC-002 (gates) en `Proposed` ou plus.

### 2.3 P2 — souhaitable / extension

- **P2-1 — IANA MIME registration** (`application/vnd.klickd+json`) — déclenche un workflow externe, à découpler du tag GA.
- **P2-2 — Zenodo DOI v4 GA** — uniquement après confirmation Vince, post-tag.
- **P2-3 — RFC-005 (claim-memory growth & compaction)** — placeholder déjà dans `ROADMAP.md`, à promouvoir en Draft quand la pression empirique est documentée.
- **P2-4 — High-security Argon2id preset** (m=131072 / t=4) opt-in, déjà esquissé v3.1.
- **P2-5 — Multi-passphrase / key-wrapping** — fonctionnalité partage d’équipe (déjà listée v4.0 dans `ROADMAP.md`).
- **P2-6 — Domain schemas formels** (`education`, `work`, `finance`, `legal`, `robotics`). Voir aussi le pattern B2B [`core.klickd` for organisations](../use-cases/CORE_KLICKD_B2B.md) — concept doc qui formalise un cas d’usage `core.klickd` (rules / gates / tone / evidence / approval) distinct du `user.klickd` (mémoire utilisateur). Non-normatif, futur RFC.
- **P2-7 — Counter-based IV** pour hauts volumes (birthday bound).
- **P2-8 — Memory search index** local et chiffré (BM25 / embedding, optionnel).
- **P2-9 — `agent_core` schéma strict + SDK surface (post-GA).** Une fois [RFC-006](../rfcs/RFC-006-agent-core.md) en `Accepted`, ajouter un schéma strict `klickd-agent-core-v1.schema.json`, des hooks SDK (Python + JS) pour lire/écrire/valider `agent_core`, et le check fail-closed *no-PII* du §6 RFC-006 (`KLICKD_E_AGENT_CORE_MIXED` / `KLICKD_E_AGENT_CORE_PII`). Hors P0 GA — démarre uniquement après tag `v4.0.0`.
- **P2-10 — Showcase first-party `core.Kai.klickd`.** Publier un fichier `core.Kai.klickd` réel (versionné via `agent_core.version`, provenance Klickd), démonstration de portabilité cross-provider d'un *agent core* (vs profil utilisateur). Lié à `klickd.app` (intégration), mais le fichier vit dans le repo (`examples/v4/agent_core/`) pour reproductibilité. **Aucune publication npm/PyPI/Zenodo associée.** Dépend de P2-9.
- **P2-11 — Benchmark cross-provider `agent_core` (extension RFC-003).** Étendre le Context Cost Benchmark pour mesurer la dérive de comportement d'un même `core.Kai.klickd` entre providers (consistance posture pédagogique, refus, langue). Recherche, non normatif.
- **P2-12 — Use case « creator core.klickd » (B2C / créateur).** Piste produit
  forward-looking décrite dans [`docs/use-cases/CREATOR-CORE-KLICKD.md`](../use-cases/CREATOR-CORE-KLICKD.md) :
  utiliser `.klickd` comme **contexte créatif réutilisable** pour la
  génération média (Reels, TikTok, Shorts, micro-leçons, clips produit).
  Distingue trois portées (`user.klickd` privé, `creator core.klickd`
  réutilisable, `project.klickd`/`media_profile` campagne). S'appuie sur
  v4 (`media_profile`, `verification_gates`, AI disclosure, C2PA). **Aucun
  nouveau champ normé**, **aucun engagement de livraison**, **post-V4 GA**.
  Pourra déclencher une **RFC-007 `creator_profile` v1** si la pression
  empirique se confirme. Indépendant de P2-9/P2-10/P2-11 (`agent_core` /
  `core.Kai.klickd`) : un *agent core* (RFC-006) capture la posture d'un
  agent IA, tandis qu'un *creator core* capture l'identité créative d'un
  humain producteur de média.

---

## 3. Gouvernance & règles d’exécution

Ces règles s’appliquent à *toute* PR du chantier V4 GA :

1. **Petites PRs ciblées.** Une PR par item de backlog (ou par sous-livrable clairement délimité). Aucune PR « v4 GA » géante.
2. **Checks verts obligatoires.** `test-vectors` + `verify-npm-preview` + toute CI ajoutée pour v4 doivent être verts avant merge.
3. **Logs et traces explicites.** Tout changement de comportement utilisateur (migration, gate déclenché) émet un log explicite — pas de mutation silencieuse.
4. **Aucun publish sans Vince.** Aucune PR ne déclenche un publish npm `latest`, PyPI stable, Zenodo DOI, IANA MIME, ou un tag `v4.0.0`. Ces actions sont **manuelles** et requièrent une approbation explicite de Vince.
5. **Aucun secret commité.** Ni clés provider, ni passphrases de test au-delà de ce qui existe déjà dans les fixtures non-secrets actuels. Toute clé/credential doit transiter par GitHub Environments (cf. `verify-npm-preview` / `publish-npm`).
6. **Préservation des champs inconnus.** Toute modification de SDK / schéma / migrateur doit explicitement préserver les champs inconnus verbatim. Un test négatif est requis.
7. **Migration non destructive.** Le fichier source d’une migration n’est **jamais** réécrit en place. Un backup + un nouveau fichier + un `migration_report` sont obligatoires (RFC-004).
8. **Pas de surpromesse publique.** Tant que P0 n’est pas vert, communication externe = « preview ». Aucun visuel / texte landing ne doit suggérer GA prématurément.
9. **`locked` non modifiable.** Aucun item de backlog ne modifie de champ `locked_*` (ethics, locked_actions). Tout besoin perçu doit ouvrir une RFC dédiée *avant* code.
10. **Doc d’abord.** Pour tout chantier P0, la PR de doc / RFC promue précède la PR de code.

---

## 4. Séquence recommandée (sans engagement de date)

L’ordre suivant minimise le re-travail :

1. **PR docs-only** (cette PR) — pose le backlog, met à jour `ROADMAP.md`.
2. **RFC-001/002/004 → `Accepted`** — gel de la surface normative v4.
3. **SPEC normative v4 (P0-1)** — promotion §33 ou nouveau document.
4. **Schémas stricts (P0-2)** + **vectors stricts (P0-6)** — en parallèle, petit aller-retour entre les deux.
5. **SDK Python (P0-3)** puis **SDK JS (P0-4)** — Python d’abord (langage de référence des vectors), JS aligne ensuite.
6. **Migrateur (P0-5)** + **vectors migration (P1-6)** — uniquement quand SDKs lisent v4 strict.
7. **README / docs / exemples (P1-1, P1-2)** — refresh non bloquant, peut commencer en parallèle de P0-3/4.
8. **RFC-003 exécution (P1-3)** et **démo Hermes (P1-4)** — chantier adoption / preuve.
9. **Viewer de référence (P1-5)** — peut démarrer en parallèle dès que P0-2 est figé.
10. **GA decision gate** — Vince déclenche tag + publish + Zenodo manuellement.
11. **Post-GA (P2 future-work).** Promotion `RFC-006` → `Proposed` / `Accepted`, puis schéma strict `agent_core` (P2-9), showcase `core.Kai.klickd` (P2-10), extension benchmark cross-provider (P2-11). **Aucun de ces items ne bloque ni ne précède le tag `v4.0.0`.**

---

## 5. Prochaine PR recommandée

> **Statut 2026-05-23 :** la PR « rfc(v4): promote RFC-001 / RFC-002 / RFC-004 from Draft to Proposed » a été ouverte et est docs-only (aucun SDK, schéma, vector touché). Elle gèle la surface conceptuelle de RFC-001 (`media_profile`), RFC-002 v1 core (gates / `human_veto_policy`), et RFC-004 (migration / never-break-the-soul). RFC-002 §8b (v2 additions) et RFC-003 (benchmark) restent `Draft` et n'entrent **pas** dans cette promotion.

Justification : geler la surface conceptuelle avant d'écrire le schéma strict
évite un effet « schema-first, RFC-after » où la sémantique devient implicite
dans le code. Cette PR reste docs-only et low-risk : elle ne touche aucun SDK,
aucun schéma, aucun vector. Elle prépare P0-1.

La prochaine étape attendue, après merge de cette promotion, est :

> **PR « spec(v4): begin promoting §33 preview wording toward normative (P0-1) ».**

Cette PR suivante ne déclenche toujours aucun publish (npm / PyPI / Zenodo), aucun tag,
aucune annonce externe. Elle reste docs-first conformément à la règle §3.10.

---

*Document vivant. Toute modification passe par une PR.*
