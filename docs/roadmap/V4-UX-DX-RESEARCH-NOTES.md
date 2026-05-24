# V4 UX/DX research notes (intake)

> **Status:** Draft · NON-NORMATIVE · backlog intake summary.
> **Scope:** synthétise les décisions actionnables tirées d'une revue
> comparative UX end-user / DX développeur (Mem0, Letta `.af`, Zep,
> LangGraph, AGENTS.md, Cursor rules, Obsidian, Logseq, 1Password,
> Bitwarden, KeePassXC, ComfyUI workflow JSON) menée le **2026-05-24**.
> Ce document **ne copie pas** le rapport source intégral — il en
> extrait les décisions backlog et les anti-patterns à inscrire dans
> [`ROAD-TO-V4-GA.md`](./ROAD-TO-V4-GA.md) §2.4.
>
> **Aucun changement** : SPEC, schéma, SDK, vector, tag, publish.

---

## 0. Pourquoi cette note

La V4 GA est gouvernée par la roadmap normative
[`ROAD-TO-V4-GA.md`](./ROAD-TO-V4-GA.md). Avant que la SPEC §33 ne soit
promue normative (P0-1), nous avons besoin que le backlog reflète aussi
la **réalité d'adoption** observée dans les écosystèmes voisins
(local-first PKM, gestionnaires de mots de passe, fichiers d'agent
portables, workflows IA générative).

Cette note est l'intake : une liste minimale d'items P0/P1/P2 issus de
la revue, et une liste d'anti-patterns que V4 doit éviter. Les items
eux-mêmes vivent dans §2.4 de la roadmap.

---

## 1. Décisions actionnables (synthèse)

### 1.1 P0 — bloquants GA (UX/DX-driven)

1. **`user.klickd` 7-step wizard avec rechargement de vérification
   obligatoire.** Inspiré de 1Password Emergency Kit, Obsidian vault
   setup, Bitwarden import. Étape 6 = recharger le fichier généré avant
   la fin du wizard. Sans cette étape, l'onboarding crée des fichiers
   que l'utilisateur ne sait pas réouvrir.
2. **Messages d'erreur i18n orientés utilisateur pour tous les codes
   `KLICKD_E_*`.** Une table `error_messages` (FR/EN/DE/LB) mappant chaque
   code à un message orienté utilisateur + une action recommandée.
   Bitwarden et KeePassXC sont la référence : `[ligne] [type] "nom" :
   champ X dépasse N caractères` est actionnable, `KLICKD_E_FORMAT`
   seul ne l'est pas.
3. **Profils d'exemple téléchargeables (5 personas).** Letta publie des
   `.af` d'exemple — c'est ce qui a accéléré l'adoption développeur.
   Cinq fichiers `.klickd` valides + décryptables (passphrase de test
   non-secret, déjà-publique) : élève terminale, chef de projet, dev,
   créateur média (preview `media.klickd`), joueur (preview
   `gaming.klickd`).
4. **Politique de dépréciation formelle.** `.klickd` a ajouté 26 champs
   en v3.4. Sans politique, le schéma devient ingérable et les agents
   hallucinent des champs. Règle proposée : tout champ ajouté en Vx
   passe à `deprecated` en Vx+2 s'il n'apparaît pas dans ≥10 % des
   fichiers d'exemple. Un `deprecated` est ignoré silencieusement par
   les readers v4 mais reste documenté pour migration.

### 1.2 P1 — bloquants adoption (UX/DX-driven)

1. **`media.klickd` minimal (RFC-001 v1, déjà `Accepted`).** Noyau :
   `project_name`, `assets[]` (label, path, hash, software,
   last_modified), `continuity_state`, `next_action`. Pattern repris de
   ComfyUI workflow JSON (références hash, pas de binaire dans le
   fichier). **Périmètre V4 confirmé** : la continuité générique
   (référence média + état de continuité) est V4. Le rendu 3D / CAD /
   spatial / printing reste **V5 track** et ne doit pas bloquer V4.
2. **`project.klickd` minimal avec export AGENTS.md.** Champ
   `agents_md_content` (string Markdown) auto-généré à partir des
   champs `stack`, `repo_url`, `decisions_locked`, `next_milestone`.
   AGENTS.md est le standard de facto 2025-2026 (20+ outils). Permettre
   l'export depuis un `project.klickd` chiffré multiplie
   l'interopérabilité.
3. **JSON Schema v4 publié et testable.** Au-delà de P0-2 (schéma
   strict côté repo), publier le schéma à une URL stable (cf. ComfyUI
   workflow_json) et fournir un validateur web minimal (zero-server,
   tout côté client). Ne pré-engage pas l'IANA MIME (P2-1).
4. **`gaming.klickd` baseline optionnelle (registry-based).** Profil
   **registré** (ne s'active que si `domain: gaming`), noyau minimal :
   `character_name`, `game`, `continuity_state`, `next_session_trigger`,
   `npc_memory[]`. **Périmètre V4 confirmé** par Vince : baseline NPC /
   gaming est V4 *uniquement si* optionnel et registry-based — il ne
   doit jamais alourdir l'onboarding `user.klickd` principal.
5. **QR / deeplink onboarding trigger** — classé **P1/P2 conditionnel,
   subject to zero-server architecture review.** Le pattern 1Password
   QR de provisioning est attractif UX, mais une URL temporaire de
   téléchargement réintroduit une dépendance serveur en contradiction
   avec la claim « zero-server pour les fichiers `.klickd` ». À
   trancher : (a) QR encode le fichier complet (taille ≤ 3 KB
   compressé), zéro-serveur ; (b) QR encode un *deeplink* local
   (`klickd://load?token=...`) sans réseau ; (c) abandon si aucune
   variante n'est zero-server.

### 1.3 P2 — souhaitable / extension (UX/DX-driven)

1. **`compression_policy.mode: "progressive"` avec preview** — montrer
   « taille actuelle → taille après compression » avant d'appliquer.
   Évite la méfiance LangGraph (« checkpoints créent une croissance de
   stockage significative »).
2. **`preferred_model` (réservé depuis v3.4) → routing hint normalisé
   V4** — clarifier sémantiquement : hint, pas obligation ; un reader
   peut l'ignorer mais doit logger l'override.
3. **`shared_context` (Plan Famille) UI dédiée** — RGPD : sans UI,
   `visible_to_members` / `private_fields` se configurent en JSON brut,
   ce qui expose des données sensibles (mood, struggles) par accident.
4. **IANA MIME `application/vnd.klickd+json`** — déjà tracé en P2-1
   roadmap actuelle. Confirmation : reste P2, post-tag GA.

---

## 2. Anti-patterns à éviter (V4)

| # | Anti-pattern | Observé chez | Garde-fou V4 |
|---|---|---|---|
| A1 | **Mur JSON.** Afficher le payload brut à l'utilisateur. | Premières versions LangGraph, exports Logseq, specs `.klickd` v2.x exposées directes. | Le wizard cache le JSON. L'utilisateur ne voit jamais qu'un résumé (`nom · domaine · dernière session`). |
| A2 | **Migration silencieuse.** Lire un fichier d'une version antérieure sans informer des champs manquants ou dépréciés. | ComfyUI v0.4 → v1.0 (champs ignorés), Cursor `.cursorrules` → `.cursor/rules/`. | RFC-004 `migration_report` obligatoire + UX message orienté utilisateur (« profil v2 mis à jour vers v4, données intactes »). |
| A3 | **Couplage cloud masqué.** Prétendre local-first tout en nécessitant un appel serveur. | OpenMemory MCP (clé API OpenAI obligatoire), Obsidian Sync payant. | Toute intégration `session_metadata` / sync future requiert consentement explicite + changement de claim. Pas de sync serveur par défaut. |
| A4 | **Inflation schéma.** Ajouter des champs à chaque version sans déprécier. | `.klickd` v3.2 → v3.4 (26 nouveaux champs). | Voir P0-4 (politique de dépréciation formelle). |
| A5 | **Spec-first sans exemples.** Documentation exhaustive mais exemples fragmentaires. | Spec `.klickd` actuelle (exemples par section, pas fichiers complets valides). | Voir P0-3 (5 profils d'exemple complets téléchargeables, passphrase test publique). |
| A6 | **Erreurs non actionnables.** Codes machine seuls (`KLICKD_E_FORMAT`) sans message + action. | LangGraph pré-v0.3 (stacktrace Python brut), premiers workflows ComfyUI (nœud « invalid » sans localisation). | Voir P0-2 (table `error_messages` i18n, code → message utilisateur + action). |

---

## 3. Corrections de périmètre V4 (validation Vince 2026-05-24)

Ces corrections explicites du périmètre V4 sont issues de la revue :

1. **Continuité générique (media / project) = V4.** Les benchmarks et
   évidence de continuité d'état génériques (références hash, état de
   continuité, prochain action) sont **dans le périmètre V4** via
   RFC-001 (`media_profile`) — déjà `Accepted`. La couche
   `project.klickd` minimale (P1.2 ci-dessus) suit le même cadrage.
2. **Baseline NPC / gaming = V4, conditionnel.** Un profil
   `gaming.klickd` baseline est **dans le périmètre V4** uniquement si
   *optionnel* et *registry-based*. Il ne doit pas alourdir
   l'onboarding `user.klickd`, ne pas devenir un MUST de la SPEC v4, et
   rester ignorable par tout reader v4 ne déclarant pas la facette
   `domain: gaming`.
3. **3D / spatial / CAD / printing = V5 track.** Tout ce qui touche au
   rendu 3D, à la capture spatiale, à la CAO, ou aux flux d'impression
   3D, est **hors périmètre V4** et n'entre pas dans la séquence GA.
   Ces sujets restent en piste V5 (forward-looking), n'introduisent
   aucun champ normé en v4, et **ne bloquent pas** le tag `v4.0.0`.

---

## 4. Notes de gouvernance pour cette intake

- Cette note **n'introduit aucun champ normé**, **ne modifie aucun
  schéma**, **ne touche aucun SDK ou vector**, et **ne déclenche aucun
  publish** (npm / PyPI / Zenodo / IANA).
- Les items concrets sont inscrits dans
  [`ROAD-TO-V4-GA.md`](./ROAD-TO-V4-GA.md) §2.4 sous un préfixe `R4-`
  (R pour *research-informed*) afin de ne pas collisionner avec les
  identifiants P0/P1/P2 existants.
- Les anti-patterns A1–A6 sont citables depuis n'importe quelle RFC ou
  PR de revue. Toute nouvelle RFC v4+ devra justifier en quoi elle
  *n'introduit pas* ces anti-patterns.
- La validation maintainer (Vince, 2026-05-24, `Go` post-audit
  Acceptance Checklist) confirme les corrections de périmètre §3.

---

*Document vivant — toute modification passe par une PR docs-only.*
