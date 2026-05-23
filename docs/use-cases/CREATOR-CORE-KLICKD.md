# Use case — `creator core.klickd` (B2C / media generation)

> **Status:** Draft · NON-NORMATIVE · forward-looking product direction.
> **Scope:** docs-only. Décrit comment un fichier `.klickd` peut servir
> de **contexte créatif réutilisable** pour la génération de contenus
> média (Reels, TikTok, YouTube Shorts, clips, micro-leçons, etc.).
>
> Ce document **n'est pas une promesse de livraison**, ne décrit aucune
> API publique, ne déclenche aucun publish (npm / PyPI / Zenodo), et
> ne modifie aucun champ `locked_*`.
>
> La version production recommandée reste **v3.5.1**. La piste « creator
> core.klickd » est rattachée au backlog [`docs/roadmap/ROAD-TO-V4-GA.md`](../roadmap/ROAD-TO-V4-GA.md)
> en **P2 — souhaitable / extension** (post-GA v4).

---

## 1. Pourquoi ce use case

Le cœur historique de `.klickd` est **B2B / professionnel** : un fichier
portable qui transporte un contexte de travail (avocat, développeur,
support client, recherche, médecine, robotique…) entre modèles et
sessions. Le format reste neutre vis-à-vis du domaine — c'est la
combinaison `domain` + `agent_instructions` + `memory[]` qui spécialise
l'usage.

Une **deuxième famille d'usages** émerge naturellement avec
[RFC-001 `media_profile` v1](../rfcs/RFC-001-media-profile-v1.md) :
le **créateur de contenu** (B2C, indépendant, micro-entreprise) qui veut
qu'un agent génère **à sa place** des Reels, Shorts, clips, micro-leçons,
posts produit, avec **sa** voix, **son** style visuel, **ses** hooks,
**ses** contraintes de plateforme — sans devoir tout redire à chaque
session, ni à chaque outil, ni à chaque modèle.

Un `creator core.klickd` répond à cette demande :

> *Un fichier portable, chiffré côté client, qui décrit **comment moi je
> fais des vidéos**, et qu'un agent (ou une chaîne d'agents) peut
> charger pour produire un brief, un storyboard, un script, et —
> quand un modèle vidéo le permet — un rendu, sans réinventer mon
> style ni violer les règles des plateformes.*

Le `.klickd` ne **remplace** pas le modèle de génération vidéo. Il
**conditionne** ce que ce modèle reçoit en entrée.

---

## 2. Distinction des trois portées

`.klickd` n'est pas un seul artefact. Le format peut décrire **trois
portées** distinctes, qui se composent :

| Portée | Nom suggéré | Contenu typique | Durée de vie | Partagé ? |
|---|---|---|---|---|
| **Privée personnelle** | `user.klickd` | identité, préférences, mémoire, accessibilité, ton, valeurs, croissance, anti-blackhat — **mémoire privée** | mois → années | non, jamais |
| **Opérationnelle créative** | `creator core.klickd` (ou `media creator core.klickd`) | **contexte créatif réutilisable** : style, hooks, formats, brand voice, règles de plateforme, contraintes de génération, prompt templates, `media_profile` (références voix/image/document) | mois → années | oui, sous consentement |
| **Projet / campagne** | `project.klickd` (ou `media_profile`-only) | **état d'un projet précis** : un Reel donné, une série de Shorts, un lancement produit, un cours de 10 micro-leçons, un EP de 6 clips, etc. | jours → semaines | oui, avec collaborateurs |

> ⚠️ **Cette typologie est conceptuelle, pas un champ normé.** Le
> format `.klickd` est **un** schéma. La portée est exprimée par les
> sections présentes (ex. : un `creator core.klickd` ne contient pas
> de mémoire privée, un `project.klickd` contient un `media_profile`
> riche mais pas d'identité).

### 2.1 Règles de composition

- Un agent peut **charger plusieurs fichiers** dans un même contexte
  (ex. : `user.klickd` + `creator core.klickd` + `project.klickd`).
- Le `user.klickd` est **toujours privé** : il ne quitte pas le
  périphérique du créateur. Il n'est **jamais partagé** avec une équipe,
  un client, un sous-traitant, ni une plateforme.
- Le `creator core.klickd` peut être **partagé avec un collaborateur de
  confiance** (monteur, motion designer, agent IA tiers), sous
  consentement explicite — c'est le contexte créatif, pas la vie privée.
- Le `project.klickd` est **le plus partageable** : c'est l'état d'un
  livrable précis, équivalent d'un brief client.

### 2.2 Ce qui n'appartient PAS au `creator core.klickd`

- Conversations privées (chats, DMs, e-mails, sessions thérapeutiques).
- Secrets : tokens d'API, mots de passe, clés de licence.
- Assets sous copyright **non licenciés** (musique, samples, fonts payantes, images d'archives).
- Données d'identité d'autrui (likeness sans consentement, voix d'une autre personne).
- Données d'enfants sans consentement parental documenté.
- Historique d'achat, données médicales, données fiscales — ces choses
  vivent dans `user.klickd` privé, jamais ici.

---

## 3. Composition d'un `creator core.klickd` (illustrative)

> Cette section décrit **comment on assemblerait** un creator core.klickd
> avec les sections **existantes** du format (v3.5.1) **enrichies** par
> v4 (`media_profile`, `verification_gates`, `human_veto_policy`,
> `claim_sources`). Aucun nouveau champ normé n'est introduit ici.

### 3.1 Sections utiles, telles qu'elles existent déjà

- **`domain`** : `"media_creation"` (valeur libre, non énumérée à ce
  jour — pas de breaking change).
- **`agent_instructions`** (≤ 32 KiB) : le « brief opérationnel » du
  créateur — ton, structure de hook, longueur cible, règles d'éthique,
  refus types.
- **`personality.voice`** : la voix éditoriale (registre, vocabulaire,
  rythme, tics rhétoriques assumés).
- **`personality.values`** : valeurs non négociables (ex. : pas de
  fat-shaming, pas de promesses santé non fondées, AI disclosure
  systématique).
- **`memory[]`** : exemples passés validés (hooks qui ont marché,
  formats qui ont converti) — sous forme **non identifiante** (pas de
  noms, pas de DMs, pas de stats détaillées d'audience si elles sont
  sensibles).
- **`growth`** : compétences créatives (montage, écriture de hook,
  scénarisation, etc.) — utile pour qu'un agent sache *où* le créateur
  veut progresser et *où* il préfère être assisté.
- **`ethics`** (authority SYSTEM, immutable, anti-blackhat) : barrières
  dures (pas d'impersonation, pas de deepfake de tiers, pas de
  désinformation, AI disclosure obligatoire, consentement likeness, etc.).

### 3.2 Sections v4 directement pertinentes

- **`media_profile`** (RFC-001) : références **hash-vérifiées** vers
  les samples voix, références visuelles, signatures, embeddings ;
  consentement **par entrée** (`tts_synthesis`, `voice_clone_personal`,
  `style_reference`, `document_template`, `accessibility_profile`).
  → C'est **la** brique qui rend le creator core.klickd opérationnel.

- **`verification_gates`** (RFC-002) : portes de vérification avant
  publication. Pour un créateur, ces gates sont les **règles
  de plateforme** + **règles éthiques** (cf. §4 ci-dessous).

- **`human_veto_policy`** (RFC-002) : « rien ne se poste sans mon OK »,
  ou « les éducatifs auto-publient, les sponsorisés exigent veto humain ».

- **`claim_sources`** + **`verification_artifacts`** : pour les
  contenus qui contiennent des **affirmations factuelles** (santé,
  finance, droit, science) — sourcer, plutôt qu'inventer.

- **`migration` / `context_cost`** : non spécifiques au use case mais
  utiles à long terme.

### 3.3 Champs *additionnels suggérés* (non normés, pour discussion)

Ces champs **n'existent pas** en v4-preview. Ils sont proposés ici comme
matière à futurs RFC. Aucune implémentation ne devrait s'appuyer dessus
avant qu'un RFC ne les promeuve.

- `creator_profile.brand_voice` — résumé compact du ton éditorial
  (déjà partiellement couvert par `personality.voice`).
- `creator_profile.hook_patterns[]` — bibliothèque de structures de
  hook validées (ex. : « problem → reframe → CTA », « curiosity gap
  30s »).
- `creator_profile.formats[]` — formats récurrents (`reel_30s_face_cam`,
  `short_lecture_60s`, `product_launch_clip_15s`…).
- `creator_profile.platform_rules{}` — règles **par plateforme** (TikTok,
  Reels, Shorts, X, LinkedIn) : durées max, hashtags max, musiques
  autorisées, exigences AI disclosure, etc.
- `creator_profile.generation_constraints` — contraintes réutilisables :
  ratio (9:16, 1:1, 16:9), fps, watermark obligatoire, langue par défaut,
  sous-titres obligatoires, etc.
- `creator_profile.prompt_templates[]` — modèles de prompt voix/image/vidéo
  paramétrables (alignés sur la voix de marque).
- `creator_profile.do_not_list[]` — interdits explicites (sujets, tons,
  mots, marques concurrentes, contenus mineurs, etc.).
- `creator_profile.licensing` — politique d'usage assets (CC0 only ?
  licence achetée ? watermark ?).

> Si la pression empirique se confirme, un **RFC-007 — `creator_profile`
> v1** pourrait être ouvert post-v4 GA (RFC-006 est déjà pris par
> [`agent_core`](../rfcs/RFC-006-agent-core.md)). Ce document **n'engage rien**.

---

## 4. Comment ça s'articule avec v4 `media_profile`

| v4 surface | Rôle dans un creator core.klickd |
|---|---|
| **storyboard** *(non normé en v4-preview, esquissé dans `examples/v4-preview/`)* | État d'un **projet** (rentre dans `project.klickd`, pas dans le core). |
| **prompt_visibility** | Indique si les prompts utilisés pour générer un asset sont **visibles** (transparence) ou **opaques** (secret de fabrication). Un creator core peut imposer `prompt_visibility: "visible"` par défaut sur les contenus éducatifs et `"opaque"` sur les sponsorisés. |
| **AI disclosure** | Doit être **on par défaut** dans tout `creator core.klickd` qui produit du contenu IA-assisté. Implémenté via `verification_gates` (« no_publish_without_ai_disclosure ») et `ethics` (authority SYSTEM). |
| **C2PA** | Quand le modèle/outil de rendu supporte C2PA (Content Credentials), le `creator core.klickd` **doit** demander la signature C2PA en sortie. Le hash `media_profile.entries[].hash` reste la source de vérité côté `.klickd` ; C2PA est la **signature publique** côté asset livré. |
| **Provenance** | `media_profile.entries[].producer` documente l'origine de chaque source (humain vs modèle, device, vendor). C'est l'épine dorsale de la provenance interne. |
| **Platform-specific rules** | `verification_gates` peut encoder des gates « platform_tiktok_compliant », « platform_reels_compliant » qui inspectent durée, sous-titres, AI disclosure, etc. |
| **Brand voice** | `personality.voice` + (futur) `creator_profile.brand_voice` + `agent_instructions` ciblé. |
| **Reusable generation constraints** | `creator_profile.generation_constraints` + `agent_instructions` + `verification_gates`. |

> Tant que `creator_profile` n'est pas normé, **tout passe par
> `agent_instructions` + `personality` + `media_profile` + `verification_gates`**.
> C'est verbeux mais déjà suffisant pour un POC.

---

## 5. Exemples (non normatifs)

Tous les exemples ci-dessous sont **illustratifs**. Ils ne sont pas
livrés comme vectors à ce stade.

### 5.1 Générateur TikTok / Reels (créateur lifestyle)

- `domain: "media_creation"`
- `agent_instructions` : structure de hook 0–3s, durée 15–45s, voix
  off optionnelle, sous-titres obligatoires en bas, AI disclosure
  toujours présente, pas de musique sous copyright non-licenciée.
- `personality.voice` : direct, chaleureux, FR-LU, tutoiement, peu
  d'anglicismes.
- `media_profile.entries[]` : `voice-primary` (sample 12s, hash blake3,
  consent `tts_synthesis` + `voice_clone_personal`, expires 2027) ;
  `style-sketch-overlay` (PNG 32 KiB, consent `style_reference`).
- `verification_gates` : gates `ai_disclosure_present`,
  `subtitles_present`, `duration_max_45s`, `music_license_documented`.
- `human_veto_policy` : auto-publish OK pour micro-leçons (≤ 90s, pas
  de claim factuel) ; veto humain obligatoire pour contenus sponsorisés.

### 5.2 YouTube Shorts éducatifs (vulgarisation)

- `domain: "media_creation"` + `personality.values` : exactitude > viralité.
- `verification_gates.claim_sources_required` : tout claim factuel
  (date, chiffre, citation) doit pointer vers `claim_sources[]` avec
  source vérifiable.
- `verification_artifacts` : capture de page source archivée.
- `verification_gates.no_publish_without_ai_disclosure: true`.
- `media_profile.entries[]` : `whiteboard-base.png` (style référence),
  `narrator-voice.wav` (voix off TTS), `intro-jingle.opus` (musique
  CC0 documentée dans `licensing`).

### 5.3 Clips de lancement produit (D2C / startup solo)

- `personality.voice` calé sur la voix de marque (déjà décrite ailleurs).
- `creator_profile.platform_rules` (suggéré) : 3 plateformes
  (TikTok 15s, Reels 30s, LinkedIn 60s) avec coupes adaptées.
- `verification_gates` : pas de claim santé/médical, pas de comparatif
  concurrent non sourcé, AI disclosure systématique.
- `media_profile.entries[]` : `product-shot.png` (photo produit, licence
  propriétaire, `consent.purposes: ["style_reference"]`), `logo.svg`
  (asset de marque, licence propre).

### 5.4 Micro-leçons éducatives (instituteur / formateur)

- `domain: "education"` (et non `media_creation`) — le contenu prime sur le format.
- `personality.values` : respect de l'âge cible, pas de stéréotypes,
  langue claire.
- `verification_gates.claim_sources_required: true`.
- `ethics` (authority SYSTEM) : pas de capture d'enfants (likeness),
  pas de scoring d'élèves visible publiquement.
- `human_veto_policy` : 100 % veto humain (un prof ne laisse pas un
  agent publier seul).

### 5.5 Artiste musical (contenu autour des sorties)

- `media_profile.entries[]` : `voice-singing-ref.wav` (consent
  `voice_clone_personal` **ou refus explicite** si l'artiste interdit
  le clonage de sa voix chantée — `consent.purposes` peut être vide,
  voire `consent.revocable: true` + `expires_at` court).
- `ethics` : interdiction explicite de générer la **voix d'un autre
  artiste** ; interdiction de reproduire un style protégé sans licence.
- `verification_gates.platform_rules` : règles TikTok/Reels musique
  (ne pas utiliser un track sans licence éditoriale).

### 5.6 Domaines régulés — disclaimers obligatoires

Pour des créateurs **juristes**, **médecins**, **financiers**, **psy**,
le `creator core.klickd` **doit** encoder des disclaimers obligatoires :

- `verification_gates.disclaimer_required: true` (ex. : « Ce contenu
  ne constitue pas un avis juridique / médical / financier
  personnalisé »).
- `ethics` (authority SYSTEM) : interdiction de fournir un diagnostic,
  un avis personnalisé, ou une recommandation d'investissement.
- `human_veto_policy` : veto humain **obligatoire** sur tout contenu
  régulé, sans exception.
- `claim_sources_required: true` (jurisprudence, étude, source
  réglementaire datée).

> ⚠️ Ces gates **n'exonèrent pas** le créateur de ses obligations
> professionnelles. `.klickd` est un outil de **discipline**, pas un
> outil de **conformité réglementaire**.

---

## 6. Sécurité / vie privée — règles dures

Ces règles sont **non négociables** pour tout outil qui se réclame de
ce use case.

1. **Pas de chats privés bruts.** Aucun `creator core.klickd` ne doit
   contenir d'extrait verbatim de conversation privée (DM, e-mail,
   session de coaching). Si une leçon doit en être tirée, elle est
   **résumée**, **anonymisée**, et **dépouillée d'identifiants**.
2. **Pas de secrets.** Pas de tokens, mots de passe, clés d'API, clés
   privées. Les outils qui produisent du contenu doivent référencer
   les secrets via le **système de secrets de l'hôte** (env, vault), pas
   via `.klickd`.
3. **Pas d'assets copyrightés non licenciés.** Toute entrée
   `media_profile` doit déclarer son `consent.purposes` **et** sa
   licence côté `creator_profile.licensing` (futur). En attendant, la
   documentation côté `agent_instructions` est obligatoire.
4. **Pas d'impersonation.** Interdiction d'utiliser la voix, le visage,
   le nom, ou le style **identifiable** d'une autre personne sans
   consentement signé documenté.
5. **Consentement likeness.** Si une voix ou un visage humain est
   utilisé pour clonage / synthèse, `consent.purposes` doit inclure
   explicitement `voice_clone_personal` ou un équivalent ; `revocable: true`
   est fortement recommandé ; `expires_at` doit être fini (pas d'éternité).
6. **AI disclosure systématique.** Tout contenu généré ou
   substantiellement assisté par IA est **étiqueté** côté plateforme
   (TikTok AI Content, Meta AI Info, YouTube Altered Content). Le
   `verification_gates.ai_disclosure_present` doit l'imposer
   **avant publication**, pas après.
7. **C2PA quand disponible.** Si le pipeline de rendu supporte C2PA,
   la signature est **obligatoire** côté `creator core.klickd` pour les
   contenus à enjeu (régulés, sponsorisés, publication large).
8. **Mineurs.** Aucun contenu mineur sans consentement parental
   documenté (et déclaré dans `data_integrity`). Pas de likeness d'enfant
   sans cadre légal explicite.
9. **Localisation des données.** Le `.klickd` reste **côté
   créateur**. Aucune télémétrie. Pas de upload silencieux vers un
   service tiers. Conforme au principe `local-first` du format.
10. **Effacement.** `consent.revocable: true` doit être pris au sérieux
    par les agents : une révocation efface l'entrée du `media_profile`
    et invalide les caches dérivés.

---

## 7. Risques

| Risque | Type | Mitigation |
|---|---|---|
| **Confusion privé / créatif.** Un créateur dépose des bribes de chats privés dans le `creator core`, qu'il partage ensuite avec un monteur. | Vie privée | Outils doivent **proposer 3 portées explicites** à la création (user / creator core / project) + un linter qui refuse les chats verbatim dans un creator core. |
| **Deepfake / impersonation accidentelle.** Un agent utilise un sample « voice-ref » pour cloner une voix sans `consent.purposes` adéquat. | Éthique / légal | `verification_gates` doit imposer un **check `consent.purposes` à chaque usage** (V-008 de RFC-001), pas seulement à l'ingestion. |
| **Surclaim créatif.** Un créateur « santé » génère un contenu qui ressemble à un avis médical. | Régulé | `verification_gates.disclaimer_required` + veto humain obligatoire sur domaines régulés. |
| **Fuite de provenance.** Un `media_profile` partagé expose des URLs internes (`https://my-internal-cdn/…`). | Privacy / sécurité | RFC-001 §8 — préférer `cas://blake3:<h>` aux URLs publiques pour les contenus sensibles. |
| **Inflation du fichier.** Un creator core accumule 200 entrées media, dont 80 obsolètes. | UX / coût contexte | RFC-005 (compaction de mémoire) + politique de purge documentée côté outil. |
| **AI disclosure « shadow off ».** Un outil tiers consomme le `.klickd` mais désactive le tag AI disclosure pour des raisons de portée algorithmique. | Éthique / légal | `ai_disclosure_present` doit être un gate **bloquant la publication** côté outil, pas un champ optionnel. |
| **Copyright musical.** Un agent inclut un sample sous licence éditoriale incompatible avec TikTok/Reels. | Légal | `media_profile.entries[].license` (futur) + linter de compatibilité plateforme côté outil. |
| **Mineurs.** Likeness d'enfant dans un `style_reference`. | Légal / éthique | Refus dur côté schéma (`consent.purposes` ne peut contenir `voice_clone_personal` ou équivalent pour mineurs). |
| **Lock-in vendor d'embedding.** `voice-embedding-vendorX-v2` devient inutilisable quand vendorX disparaît. | Adoption | RFC-001 §4 décision 6 — `embedding.producer` explicite ; outils doivent pouvoir **régénérer** depuis le `voice-primary` source. |
| **Confusion GA / preview.** Des créateurs adoptent un schéma `creator_profile` non normé puis ce champ change. | Adoption | **Tant que `creator_profile` n'est pas RFC-accepted, tout passe par `agent_instructions`.** Documenté ici en §3.3. |

---

## 8. Priorisation (par rapport au backlog V4 GA)

Cette piste est **explicitement non bloquante** pour V4 GA.

### P0 (bloquant GA) — *aucun ajout*

Le creator core.klickd **ne demande pas** de nouveau champ normé pour
exister. Tous les blocs P0 du backlog [`docs/roadmap/ROAD-TO-V4-GA.md`](../roadmap/ROAD-TO-V4-GA.md)
restent inchangés.

### P1 (bloquant adoption) — *suggestions docs-only*

- **P1-C-1 — Cookbook « creator core.klickd ».** Une page
  `docs/use-cases/CREATOR-CORE-COOKBOOK.md` qui montre, pas à pas,
  comment **composer** un creator core avec les champs v4 existants
  (sans introduire de nouveau champ). Cible : un créateur peut copier
  un template, l'adapter, et le tester en local en < 30 min.
- **P1-C-2 — Exemple `.klickd` non chiffré.** Un fichier
  `examples/v4-preview/creator-core-tiktok.example.klickd` illustratif,
  aligné sur §5.1.
- **P1-C-3 — Linter docs.** Une checklist (markdown) qui vérifie qu'un
  creator core respecte les règles §6 (privé, secrets, copyright,
  impersonation, AI disclosure, C2PA, mineurs).

### P2 (souhaitable / extension) — *RFC future*

- **P2-C-1 — RFC-007 `creator_profile` v1 (proposé).** Promouvoir les
  champs §3.3 en RFC dédiée, avec schéma strict, gates dédiés, et
  vectors (RFC-006 est déjà pris par [`agent_core`](../rfcs/RFC-006-agent-core.md)).
  **Dépendance :** V4 GA livré (sinon double migration).
- **P2-C-2 — Gates de plateforme (RFC-008 ?).** Encodage des règles
  TikTok / Reels / Shorts / X / LinkedIn dans un schéma versionné,
  avec dates de dernière vérification (les règles changent vite).
- **P2-C-3 — Intégration C2PA.** Profil d'interopérabilité formel
  entre `.klickd media_profile` et Content Credentials côté assets
  livrés (`prompt_visibility`, provenance, AI disclosure machine-readable).
- **P2-C-4 — Templates par vertical** (lifestyle, éducation, musique,
  produit, régulé) — pack d'exemples sous CC0.
- **P2-C-5 — Compaction des memory[]** spécifique aux créateurs
  (les exemples passés peuvent vite saturer).

---

## 9. Ce que ce document **ne fait pas**

- Il **n'ajoute aucun champ normé** au schéma `.klickd` (v3.5.1 ou v4).
- Il **n'engage aucun calendrier**.
- Il **ne déclenche aucun publish** (npm / PyPI / Zenodo / IANA / DOI).
- Il **ne modifie aucun `locked_*`** (ethics, locked_actions).
- Il **ne supersede** aucune RFC existante.
- Il **n'autorise pas** un outil tiers à se prévaloir d'une
  conformité « creator core.klickd » — il n'existe pas de label, et
  ce document est marqué non-normatif.

---

## 10. Prochaines étapes raisonnables (sans engagement)

1. **Cette PR docs-only** — pose le use case.
2. **Discussion communautaire** — récolter des cas concrets de
   créateurs (FR-LU et au-delà).
3. **POC interne** — assembler un creator core.klickd réel (sans
   RFC nouveau) à partir des champs v4 existants, et le tester sur
   3 plateformes.
4. **Décision** — si la pression empirique se confirme, ouvrir
   **RFC-007 `creator_profile` v1** post-V4 GA (RFC-006 = `agent_core`).

---

*Document vivant. Toute modification passe par une PR.
Cf. [`docs/roadmap/ROAD-TO-V4-GA.md`](../roadmap/ROAD-TO-V4-GA.md) §2.3 (P2)
et [`docs/rfcs/RFC-001-media-profile-v1.md`](../rfcs/RFC-001-media-profile-v1.md).*
