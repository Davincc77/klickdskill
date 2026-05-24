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
- RFC-001 / 002 (v1 core) / 004 en **Accepted** (promues `Proposed` 2026-05-23, puis `Accepted` 2026-05-24, docs-only, via le [V4 Acceptance Checklist](../rfcs/ACCEPTANCE_CHECKLIST_V4.md) §3 C1–C16). RFC-003 et RFC-002 §8b (v2 additions) restent **Draft**.
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

### Corrections de périmètre V4 (validation maintainer 2026-05-24)

Suite à la revue comparative UX/DX du 2026-05-24 (cf. intake détaillé dans
[`V4-UX-DX-RESEARCH-NOTES.md`](./V4-UX-DX-RESEARCH-NOTES.md) §3) et la
validation explicite du maintainer post-Acceptance Checklist V4 :

1. **Continuité générique (media / project) = V4.** Les benchmarks et
   évidence de continuité d'état génériques (références hash, `continuity_state`,
   `next_action`) sont **dans le périmètre V4** via [RFC-001 `media_profile` v1](../rfcs/RFC-001-media-profile-v1.md)
   — déjà `Accepted` — et l'extension `project.klickd` minimale (cf. §2.4
   R4-P1-2).
2. **Baseline NPC / gaming = V4 conditionnel.** Un profil `gaming.klickd`
   baseline est dans le périmètre V4 **uniquement si optionnel et
   registry-based** (cf. §2.4 R4-P1-4). Il ne doit pas alourdir
   l'onboarding `user.klickd` ni devenir un MUST de la SPEC v4.
3. **3D / spatial / CAD / printing = V5 track.** Tout rendu 3D, capture
   spatiale, CAO, ou flux d'impression 3D est **hors périmètre V4** et
   **ne bloque pas** le tag `v4.0.0`. Ces sujets restent en piste V5
   (forward-looking) sans champ normé en v4.

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
- **P2-13 — `usage_profile` & in-session skill routing (RFC-007).** Piste future
  décrite dans [`docs/rfcs/RFC-007-usage-profile-skill-routing.md`](../rfcs/RFC-007-usage-profile-skill-routing.md) :
  sélection de **purpose** au premier lancement (`learner` / `creator` /
  `developer` / `legal` / `finance` / `health` / `research` / …), principe de
  **progressive disclosure** (le `.klickd` de base ne contient que les sections
  utiles à la purpose retenue), et **routing de skill / facette** en session
  (rules + log append-only, sans jamais stocker le prompt brut). Invariants
  durs : user wins sur les `verification_gates` (RFC-002), mutuellement
  exclusif avec `agent_core` (RFC-006), `no-raw-prompts` dans le
  `profile_switch_log`. **Aucun changement schéma / SDK / vector**, **post-V4
  GA**, **ne bloque pas le tag `v4.0.0`**. Promotion `Draft → Proposed` envisagée
  uniquement si la pression empirique se confirme après GA (first-run bloat,
  routing inconsistency cross-provider).
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

### 2.4 Backlog UX/DX-driven (intake recherche comparative — 2026-05-24)

> **Source intake :** [`V4-UX-DX-RESEARCH-NOTES.md`](./V4-UX-DX-RESEARCH-NOTES.md)
> (revue Mem0, Letta `.af`, Zep, LangGraph, AGENTS.md, Cursor, Obsidian,
> Logseq, 1Password, Bitwarden, KeePassXC, ComfyUI workflow JSON,
> 2026-05-24). Décisions actionnables uniquement — le rapport source
> intégral n'est **pas** copié dans le repo.
>
> Les identifiants utilisent le préfixe `R4-` pour ne pas entrer en
> collision avec les items P0/P1/P2 numérotés en §2.1–2.3. La priorité
> P0/P1/P2 reste la dimension portante.

#### R4-P0-1 — Wizard `user.klickd` 7 étapes avec rechargement de vérification

- **Objet :** interface guidée (web component / page dédiée) qui génère un `user.klickd` valide **sans exposer le JSON brut**. Étape 6 = recharger le fichier dans le wizard avant de quitter — non-négociable.
- **Pourquoi :** 1Password, Obsidian, Bitwarden convergent ; sans wizard avec rechargement, `.klickd` reste réservé aux développeurs et l'onboarding crée des fichiers non-réouvrables.
- **Livrables :** contrat normatif RFC 2119 dans [`docs/spec/R4-P0-1-onboarding-wizard.md`](../spec/R4-P0-1-onboarding-wizard.md), spec UX dans [`docs/ux/V4-UX-SPEC.md`](../ux/V4-UX-SPEC.md), maquette des 7 écrans, contrat des erreurs aux étapes 4 (passphrase) et 6 (rechargement).
- **DoD :** chaque étape a un seul choix dominant ; étape 6 produit un succès ou un message d'erreur orienté utilisateur (cf. R4-P0-2) ; aucun écran n'expose un payload JSON brut. **Statut :** contrat normatif R4-P0-1 inscrit (docs/spec) — implémentation `klickd.app` séparée.
- **Garde-fou anti-pattern :** A1 (mur JSON), A5 (spec-first sans exemples), A6 (erreurs non actionnables).
- **Périmètre :** docs-only pour la spec UX et le contrat normatif. L'implémentation du wizard est tracée séparément côté `klickd.app` (hors-repo) et ne bloque pas le tag `v4.0.0` côté format — mais bloque l'adoption non-développeur.
- **Dépendances :** P0-1 (SPEC normative v4), R4-P0-2 (messages d'erreur), R4-P0-3 (profils d'exemple).

#### R4-P0-2 — Messages d'erreur `KLICKD_E_*` i18n orientés utilisateur

- **Objet :** table `error_messages` mappant **chaque** code `KLICKD_E_*` à un message utilisateur + action recommandée, en FR/EN/DE/LB (langues officielles du projet).
- **Pourquoi :** Bitwarden et KeePassXC : codes seuls inutilisables par non-développeurs. Couvre l'anti-pattern A6.
- **Livrables :** contrat normatif RFC 2119 dans [`docs/spec/R4-P0-2-error-i18n-table.md`](../spec/R4-P0-2-error-i18n-table.md) (table FR/EN/DE/LB + safe-disclosure + sévérité/recoverabilité + actions utilisateur), exemples par code, contrat de fallback (EN si la langue n'est pas couverte).
- **DoD :** chaque code `KLICKD_E_*` documenté dans la spec a une ligne `code → message FR/EN/DE/LB → action`. Au moins une action ne renvoie **jamais** « contactez le support » (autonomie utilisateur). **Statut :** contrat normatif R4-P0-2 inscrit (docs/spec) — alignement SDK différé à R4-P0-3 / R4-P0-4.
- **Garde-fou anti-pattern :** A6.
- **Périmètre :** docs-only. Les SDKs Python/JS ne sont pas modifiés tant que P0-3/4 n'attaquent pas l'API publique de validation. Les codes introduits par R4-P0-2 (`KLICKD_E_PASS_MISMATCH`, `KLICKD_E_SAVE_LOCAL`, `KLICKD_E_LEGACY_VERSION`, `KLICKD_E_CORRUPT`, `KLICKD_E_POLICY_LOCKED`, `KLICKD_E_UNSAFE_QR`) sont normatifs côté contrat utilisateur mais **non encore présents** dans les SDKs.
- **Dépendances :** P0-1, R4-P0-1 (le wizard §3.4 / §3.6 dépend de cette table pour ses messages d'erreur).

#### R4-P0-3 — Profils d'exemple téléchargeables (5 personas)

- **Objet :** 5 fichiers `.klickd` v4 valides + décryptables avec une **passphrase de test publique** (jamais un secret réel), couvrant : élève terminale (éducation, FR), chef de projet PME (work, FR), développeur full-stack (work, EN), créateur média (creator, preview `media.klickd`), joueur RPG (gaming, preview `gaming.klickd`).
- **Pourquoi :** Letta `.af` montre que des exemples téléchargeables accélèrent l'adoption développeur. Sans fichier de référence, les tiers implémentent depuis la spec et divergent.
- **Livrables :** dossier `examples/v4/personas/`, README expliquant la passphrase de test (réutiliser celle déjà utilisée par les fixtures non-secrets actuels — pas de nouveau secret), checklist de validation contre les vectors v4 stricts (P0-6).
- **DoD :** chaque fichier passe la validation stricte v4 (P0-2/P0-6) sans warning ; chaque fichier round-trip via les SDKs (P0-3/P0-4) ; aucune donnée personnelle ni secret réel.
- **Garde-fou anti-pattern :** A5 (spec-first sans exemples).
- **Dépendances :** P0-2, P0-3, P0-4, P0-6.
- **Statut :** 5 personas inscrits dans [`examples/v4/personas/`](../../examples/v4/personas/) (cf. README du dossier) — validés contre le schéma permissif v4-preview ([`schemas/klickd-payload-v4-preview.schema.json`](../../schemas/klickd-payload-v4-preview.schema.json) et [`schema/klickd-v4-preview.schema.json`](../../schema/klickd-v4-preview.schema.json)). La validation stricte v4 et le round-trip SDK restent **différés** à P0-2 / P0-6 / SDK alignment conformément à l'ordre des dépendances.

#### R4-P0-4 — Politique de dépréciation V4 formelle

- **Objet :** document `docs/spec/DEPRECATION_POLICY_V4.md` définissant explicitement le cycle de vie d'un champ (`active` → `deprecated` → `removed`), la règle de marquage (`deprecated` après Vx+2 si <10 % d'usage observé sur les vectors / exemples / fixtures de référence), et la garantie de lecture silencieuse des champs `deprecated` par les readers v4.
- **Pourquoi :** `.klickd` v3.2 → v3.4 a ajouté 26 champs sans politique de sortie. Sans politique de dépréciation, le schéma grossit indéfiniment et les agents hallucinent des champs.
- **Livrables :** `DEPRECATION_POLICY_V4.md` (normatif post-P0-1), section dédiée dans la SPEC v4, ajout d'un bloc `deprecated_fields[]` au schéma envelope (informationnel, non-bloquant).
- **DoD :** la politique distingue *deprecated dans la SPEC* (champ encore valide mais discouraged) et *removed* (champ supprimé du schéma) ; aucune suppression sans transition `deprecated` d'au moins une version mineure ; le `deprecated_fields[]` est purement documentaire, jamais utilisé pour rejeter.
- **Garde-fou anti-pattern :** A4 (inflation schéma).
- **Dépendances :** P0-1.
- **Statut :** contrat normatif R4-P0-4 inscrit ([`docs/spec/DEPRECATION_POLICY_V4.md`](../spec/DEPRECATION_POLICY_V4.md)) — cycle `active` → `deprecated` → `removed`, gate combiné **Vx+2 AND <10 % d'usage** sur le corpus de référence, préservation verbatim inconditionnelle sur round-trip, bloc envelope OPTIONNEL `deprecated_fields[]` purement documentaire, exception champs locked / safety (§9), garde-fous A4 opératoires (§14). Pointeur ajouté en SPEC §33.13. Alignement SDK (log développeur de la dépréciation) **différé** à une track SDK ultérieure.

#### R4-P1-1 — `media.klickd` minimal (alignement RFC-001)

- **Objet :** confirmer le **noyau minimal** déjà spécifié par [RFC-001 `media_profile` v1](../rfcs/RFC-001-media-profile-v1.md) (`Accepted`) — `project_name`, `assets[]` (label, path / `cas://blake3:<h>`, hash, software, last_modified), `continuity_state`, `next_action` — et confirmer que le **rendu 3D / spatial / CAD / printing reste V5**, hors périmètre V4.
- **Pourquoi :** ComfyUI workflow JSON valide qu'un format de continuité média peut tenir en 3 champs requis. La continuité générique (référence média + état) est V4 ; le rendu spatial est V5.
- **Livrables :** note de cadrage dans RFC-001 ou dans la SPEC §33 (post-P0-1) confirmant la frontière V4 ↔ V5.
- **DoD :** la SPEC v4 normative énonce que `media_profile` v1 (V4) ne couvre **pas** 3D/spatial/CAD/printing ; un test négatif vérifie que ces sections, si présentes, sont préservées verbatim mais non interprétées.
- **Garde-fou anti-pattern :** A4 (inflation schéma).
- **Dépendances :** P0-1, RFC-001 (`Accepted`).

#### R4-P1-2 — `project.klickd` minimal + export AGENTS.md

- **Objet :** profil `project.klickd` minimal (dev / repo) avec champ `agents_md_content` (string Markdown) **auto-généré** depuis `stack`, `repo_url`, `decisions_locked[]`, `next_milestone`, `tests_required[]`. Le wizard pose 5 questions et produit à la fois le `.klickd` chiffré ET un AGENTS.md prêt à committer.
- **Pourquoi :** AGENTS.md est le standard de facto 2025-2026 (20+ outils). Un `project.klickd` qui exporte un AGENTS.md valide multiplie l'interopérabilité de `.klickd` dans les workflows dev.
- **Livrables :** RFC dédiée (à ouvrir, statut `Draft`) ou extension de RFC-001 — décision dans la PR de spec.
- **DoD :** le mapping `project.klickd` → AGENTS.md est déterministe ; l'AGENTS.md produit passe les linters connus (markdownlint) ; aucun secret n'entre dans l'AGENTS.md (R4-P0-2 : warning si tentative).
- **Garde-fou anti-pattern :** A1 (mur JSON, l'AGENTS.md est l'interface humaine), A3 (couplage cloud — `project.klickd` reste local-first).
- **Dépendances :** P0-1, R4-P0-3.

#### R4-P1-3 — JSON Schema v4 publié à URL stable + validateur testable

- **Objet :** publier `klickd-v4.schema.json` (cf. P0-2) à une **URL stable** (`schema.klickd.app` ou GitHub raw versionné) et fournir un **validateur web minimal** *zero-server* (tout client-side, comme le viewer P1-5).
- **Pourquoi :** ComfyUI publie son schema et référence un repo RFC. Sans schema publié, les tiers divergent.
- **Livrables :** redirect ou fichier statique à URL stable, validateur web (`demo/validator/`), CI qui valide `examples/v4/**` contre le schéma à chaque PR.
- **DoD :** URL résolvable et stable post-tag v4.0.0 ; validateur fonctionne offline ; aucun upload / télémétrie.
- **Garde-fou anti-pattern :** A3 (couplage cloud — le validateur doit fonctionner hors-ligne).
- **Dépendances :** P0-2.

#### R4-P1-4 — `gaming.klickd` baseline optionnelle (registry-based)

- **Objet :** profil `gaming.klickd` baseline minimale — `character_name`, `game`, `continuity_state`, `next_session_trigger`, `npc_memory[]` — **uniquement** activable via le registre de domaines, jamais via l'onboarding `user.klickd` principal.
- **Pourquoi :** la portabilité de contexte narratif NPC a une valeur réelle (cross-save gaming est verrouillé par les plateformes, mais le contexte narratif est platform-agnostic). Néanmoins, alourdir le path d'onboarding principal serait une régression UX.
- **Livrables :** RFC dédiée (à ouvrir, statut `Draft`), exemple non-normatif dans `examples/v4/personas/` (cf. R4-P0-3), note dans la SPEC §33 (post-P0-1) clarifiant qu'un reader v4 **doit** ignorer en silence un payload `domain: gaming` s'il ne déclare pas la facette.
- **DoD :** zéro impact sur l'onboarding `user.klickd` ; le profil est optionnel et registry-based ; aucun champ `gaming.*` n'est requis dans le schéma envelope v4.
- **Garde-fou anti-pattern :** A1 (mur JSON), A4 (inflation schéma).
- **Périmètre V4 confirmé :** baseline gaming est **V4 si et seulement si** optionnel + registry-based.
- **Dépendances :** P0-1, R4-P0-4.

#### R4-P1-5 / R4-P2-1 — QR / deeplink onboarding trigger (conditionnel)

- **Objet :** mode d'onboarding trigger générant un **QR code** (ou deeplink local `klickd://load?...`) pour le provisioning d'un `.klickd` sur un nouvel agent / nouvel appareil. Inspiré du Secret Key 1Password.
- **Pourquoi UX :** geste « scanner pour transférer mon identité IA » est immédiatement compréhensible. Couvre le cross-device sans introduire de compte.
- **Risque architecture :** une URL temporaire de téléchargement réintroduit une dépendance serveur — *contradiction directe* avec la claim « zero-server pour les fichiers `.klickd` ».
- **Décision (2026-05-24, validation mainteneur — cf. [`docs/ux/V4-ONBOARDING-QR-DEEPLINK.md`](../ux/V4-ONBOARDING-QR-DEEPLINK.md)) :** **P1 conditionnel → P2 si revue architecture zero-server bloque.** Le QR / deeplink est **un déclencheur d'UI d'import/reprise**, jamais un transport. Il ne véhicule **ni** contenu `.klickd` brut, **ni** passphrase, **ni** token durable, **ni** lien public permanent. Flux zero-server préférés :
  - (a) **schéma URI custom** `klickd://import` qui ouvre l'UI d'import standard (R4-P0-1) ; l'utilisateur sélectionne ensuite son fichier local et saisit sa passphrase ;
  - (b) **page launcher HTTPS sans état** `https://klickd.app/import-klickd` qui détecte le client installé ou rend l'UI d'import en PWA / WASM (déchiffrement entièrement côté agent utilisateur) ;
  - (c) **URL serveur temporaire** — *future conditionnelle uniquement*, jamais V4 P0, soumise à RFC dédiée et aux contraintes C1–C7 listées dans [`docs/ux/V4-ONBOARDING-QR-DEEPLINK.md`](../ux/V4-ONBOARDING-QR-DEEPLINK.md) §3 (fichier chiffré uniquement, TTL court, usage unique, pas de passphrase ni payload brut, consentement explicite, pas d'identifiant durable).
- **Livrables :** [`docs/ux/V4-ONBOARDING-QR-DEEPLINK.md`](../ux/V4-ONBOARDING-QR-DEEPLINK.md) (présent dépôt) ; toute variante serveur-temporaire requiert une RFC `Accepted` avant implémentation.
- **DoD :** la décision ne casse pas la claim zero-server ; aucune URL temporaire serveur n'est introduite tacitement ; le QR / deeplink n'est jamais le transport du fichier ou de la passphrase ; P0 reste import local + reload verification (R4-P0-1).
- **Garde-fou anti-pattern :** A3 (couplage cloud masqué). Tout PR qui smuggle du contenu, une passphrase ou un credential durable dans une URL est refusé en revue.
- **Dépendances :** P0-1, revue architecture explicite par Vince (effectuée 2026-05-24).

#### R4-P2-2 — `compression_policy.mode: "progressive"` (preview avant application)

- **Objet :** nouveau mode de compression qui affiche à l'utilisateur « taille actuelle → taille après compression » et permet l'annulation avant écriture.
- **Pourquoi :** LangGraph documente que les checkpoints créent « une croissance de stockage significative ». La compression silencieuse érode la confiance.
- **Livrables :** extension non-bloquante de la `compression_policy` (post-P0-1), pas de champ requis ajouté.
- **DoD :** `mode: "progressive"` est *opt-in* ; les modes existants restent inchangés.
- **Garde-fou anti-pattern :** A2 (migration silencieuse).
- **Dépendances :** P0-1.

#### R4-P2-3 — `preferred_model` (réservé depuis v3.4) → routing hint normalisé V4

- **Objet :** finaliser la sémantique de `preferred_model` : **hint, pas obligation**, un reader peut l'ignorer mais **doit** logger l'override.
- **Pourquoi :** champ réservé depuis v3.4 sans contrat — les intégrateurs divergent.
- **Livrables :** ajout dans la SPEC §33 normative (post-P0-1) d'une règle 2119 (MAY pour le respect, SHOULD pour le log).
- **DoD :** zéro changement breaking ; la SPEC v4 normative cadre l'intent.
- **Dépendances :** P0-1.

#### R4-P2-4 — UI dédiée `shared_context` (Plan Famille)

- **Objet :** interface dédiée pour configurer `visible_to_members` et `private_fields` sans éditer le JSON brut.
- **Pourquoi :** champ avancé v3.4 avec implications RGPD ; sans UI, les parents exposent des données sensibles (mood, struggles) par accident.
- **Livrables :** spec UX dans [`docs/ux/V4-UX-SPEC.md`](../ux/V4-UX-SPEC.md). Implémentation tracée hors-repo côté `klickd.app`.
- **DoD :** zéro champ JSON n'est exposé directement ; le default est *private*.
- **Garde-fou anti-pattern :** A1 (mur JSON).
- **Dépendances :** P0-1, R4-P0-1 (wizard pattern).

#### R4-P2-5 — IANA MIME `application/vnd.klickd+json`

- **Objet :** doublon volontaire de P2-1 (déjà tracé). Reste P2, post-tag GA, processus administratif externe.
- **Statut :** noté pour cohérence de la table ; voir P2-1 pour le tracking canonique.

#### R4-Anti-Patterns — liste opposable

Tout PR v4+ (RFC, spec, schéma, SDK, exemple) **doit** justifier, si la
question se pose, en quoi elle n'introduit aucun des anti-patterns
suivants. Liste détaillée et exemples concrets dans
[`V4-UX-DX-RESEARCH-NOTES.md`](./V4-UX-DX-RESEARCH-NOTES.md) §2.

- **A1 — Mur JSON.** Pas de payload brut affiché à l'utilisateur final.
- **A2 — Migration silencieuse.** Toute migration émet un `migration_report` (RFC-004) ET un message utilisateur orienté action.
- **A3 — Couplage cloud masqué.** Pas de dépendance serveur tacite ; toute intégration sync requiert consentement explicite et changement de claim.
- **A4 — Inflation schéma.** Pas d'ajout de champ sans politique de dépréciation associée (R4-P0-4).
- **A5 — Spec-first sans exemples.** Toute RFC `Accepted` ou section SPEC normative est accompagnée d'au moins un exemple complet et valide.
- **A6 — Erreurs non actionnables.** Tout nouveau code `KLICKD_E_*` est accompagné d'un message utilisateur + action (R4-P0-2).

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

> **Statut 2026-05-24 :**
>
> - La PR #30 « rfc(v4): promote RFC-001 / RFC-002 / RFC-004 from Draft to Proposed » a été mergée le 2026-05-23 (docs-only).
> - La PR « docs(rfc): add V4 acceptance checklist » a introduit l'[**Acceptance Checklist V4**](../rfcs/ACCEPTANCE_CHECKLIST_V4.md) (critères C1–C16 pour `Proposed → Accepted`, I1–I9 pour `Accepted → Implemented`), docs-only.
> - La PR « rfc(v4): promote RFC-001 / RFC-002 (v1 core) / RFC-004 from Proposed to Accepted » (#35) a été mergée le 2026-05-24 (SHA `891e7581`). Acceptance = docs-only, aucun SDK / schéma / vector / publish / tag.
> - La PR courante (docs-only) inscrit le **backlog UX/DX-driven** §2.4 et l'intake [`V4-UX-DX-RESEARCH-NOTES.md`](./V4-UX-DX-RESEARCH-NOTES.md). Aucune modification SPEC / schéma / SDK / vector / publish.

Justification : promouvoir RFC-001 / RFC-002 (v1 core) / RFC-004 de `Proposed`
à `Accepted` est le préalable explicite de P0-1 (SPEC normative v4). Le
checklist C1–C16 garde l'autorité de décision côté mainteneur mais rend
l'évaluation auditable par n'importe quel contributeur.

La séquence après merge de la PR d'acceptance est :

1. ~~**PR « rfc(v4): promote RFC-001 from Proposed to Accepted »**~~ — incluse dans la PR groupée d'acceptance (2026-05-24).
2. ~~**PR « rfc(v4): promote RFC-002 (v1 core) from Proposed to Accepted »**~~ — idem.
3. ~~**PR « rfc(v4): promote RFC-004 from Proposed to Accepted »**~~ — idem.
4. ~~**PR « rfc(v4): promote RFC-001 / RFC-002 (v1 core) / RFC-004 from Proposed to Accepted »**~~ — mergée 2026-05-24 (PR #35, SHA `891e7581`).
5. **PR courante** (docs-only) — inscrit le backlog UX/DX-driven §2.4 et l'intake [`V4-UX-DX-RESEARCH-NOTES.md`](./V4-UX-DX-RESEARCH-NOTES.md). Confirme les corrections de périmètre V4 §0 (continuité générique V4, baseline gaming V4-conditionnel, 3D/spatial/CAD/printing V5).
6. **PR suivante recommandée — `spec(v4): begin promoting §33 preview wording toward normative (P0-1)`** — démarre la phase SPEC normative maintenant que les trois RFCs sont en `Accepted` et que le backlog UX/DX-driven est inscrit. Cette PR sera docs-only également (touche `SPEC.md` §33 — pas de schéma strict, pas de SDK, pas de vector), conformément à la règle §3.10.

Aucune de ces PR ne déclenche un publish (npm / PyPI / Zenodo), un tag, ni une
annonce externe. Elles restent docs-first conformément à la règle §3.10.

---

*Document vivant. Toute modification passe par une PR.*
