# Re-benchmark .klickd v3.2 — Lot 6 : Environnement + Climatologie + Géophysique

## Résumé

- **10 profils testés** (Lot 6 — Environnement, Climatologie, Géophysique)
- **Modèles utilisés :** gemini-2.5-flash, llama-3.3-70b-versatile, llama-3.1-8b-instant, qwen/qwen3-32b
- **Score moyen AVEC .klickd :** 7.70/10
- **Score moyen SANS .klickd :** 5.32/10
- **Delta moyen : +2.38**
- **Période de test :** Session unique (30 questions AVEC + 30 questions SANS)
- **API utilisées :** Google Gemini v1beta, Groq OpenAI-compatible

---

## Résultats par profil

| Profil | Étudiant | Modèle(s) | AVEC | SANS | Delta | numerical_results récupérés | resume_trigger OK | struggles OK | vocab OK |
|--------|----------|-----------|------|------|-------|----------------------------|-------------------|-------------|---------|
| 1 | Léa (T. S, FR) | gemini→llama-3.3 | 7.1 | 5.2 | +1.9 | ✅ | ⚠️ partiel | ✅ | ✅ |
| 2 | Noah (L2 géo, FR) | qwen3-32b→llama-3.1 | 8.1 | 5.5 | +2.6 | ✅ | ✅ | ✅ | ✅ |
| 3 | Emma (5e, LU) | llama-3.3 | 7.3 | 5.3 | +2.0 | ✅ | ✅ | ✅ | ✅ |
| 4 | Lucas (Master, DE) | gemini→qwen3-32b | 7.6 | 5.3 | +2.3 | ✅ | ⚠️ partiel | ✅ | ✅ |
| 5 | Sofia (L1, BE) | llama-3.1→gemini | 6.8 | 5.3 | +1.5 | ❌ | ✅ | ✅ | ✅ |
| 6 | Mateus (PhD, PT/EN) | gemini | 7.2 | 5.5 | +1.7 | ❌ | ✅ | ⚠️ partiel | ✅ |
| 7 | Chloé (3e, FR) | llama-3.3 | 8.8 | 5.4 | +3.4 | ✅ | ✅ | ✅ | ✅ |
| 8 | Jan (L3 phy, NL/EN) | qwen3-32b→llama-3.3 | 9.3 | 5.7 | +3.6 | ✅ | ✅ | ✅ | ✅ |
| 9 | Yasmine (T., CH) | gemini | 7.0 | 5.0 | +2.0 | ✅ | ⚠️ partiel | ✅ | ✅ |
| 10 | Alex STRESS TEST | llama-3.3 | 7.8 | 5.0 | +2.8 | ✅ | ✅ | ✅ | ✅ |
| **MOY.** | — | — | **7.70** | **5.32** | **+2.38** | 8/10 | 7/10 | 9.5/10 | 10/10 |

---

## Observations clés v3.2

### 1. `numerical_results` — Récupération partielle selon le modèle
- **llama-3.3-70b-versatile** : Excellente récupération explicite des valeurs numériques (420 ppm, 9.5 Richter, 270 Gt/an, pH 8.1/8.2). Répète les chiffres dans les réponses.
- **gemini-2.5-flash** : Utilisation implicite des valeurs numériques (calcule à partir d'elles, les cite en contexte) mais ne les répète pas toujours verbatim. Les profils 6 (Mateus) et 5 (Sofia) en ont souffert dans le scoring automatisé, mais le contexte numérique est bien intégré.
- **qwen/qwen3-32b** : Bonne récupération, particulièrement pour les scénarios techniques complexes (RCP, profondeurs, constantes).
- **llama-3.1-8b-instant** : Récupération variable selon la complexité du contexte numérique.

### 2. `resume_trigger` — Efficacité globalement forte
- 7/10 profils ont déclenché le resume_trigger correctement.
- Échecs partiels sur les profils 1 (Léa), 4 (Lucas), 9 (Yasmine) : le modèle reprend le bon sujet mais sans formuler explicitement la phrase du `resume_trigger`. Le contenu est correct mais l'accroche verbatim est absente.
- **Recommandation v3.3** : Renforcer l'instruction `resume_trigger` en précisant "commence ta réponse par cette phrase exacte".

### 3. `struggles` — Champ le mieux respecté (9.5/10)
- Tous les modèles, quand contextualisés avec .klickd, ont adressé les struggles identifiés.
- Profil 5 (Sofia) : Gemini a insisté particulièrement sur le mécanisme catalytique ClO• après le struggle HIGH, avec une explication pédagogique très adaptée.
- Profil 6 (Mateus) : La distinction OIB/MORB (struggle low) a été abordée mais pas systématiquement dans toutes les questions.

### 4. `language_switch_detected` — Profil 3 Emma (LU→FR) : succès
- llama-3.3-70b a correctement commencé en luxembourgeois, puis suivi naturellement le passage au français de l'étudiante sans rupture de continuité.
- Le vocabulaire luxembourgeois (`Aartendiversitéit`, `Ëmweltschutz`) a été maintenu dans la première réponse, et la transition s'est faite naturellement.
- **Premier test de language_switch en luxembourgeois dans le benchmark** : résultat positif.

### 5. `subject_change_detected` — Profil 8 Jan (atm. physics→astrophysics)
- qwen/qwen3-32b et llama-3.3-70b ont tous deux tenté de rediriger vers la physique atmosphérique quand Jan dérivait vers l'astrophysique (évolution stellaire, luminosité du Soleil).
- La réponse WITH .klickd a maintenu le lien Terre-Soleil-atmosphère, tandis que WITHOUT .klickd a répondu directement sur l'évolution stellaire sans ancrage au sujet original.

### 6. `interruption_point` + reprise après délai — Profil 7 Chloé (+3.4)
- Cas le plus instructif : reprise simulée 2 jours après une interruption à seulement 30%.
- AVEC .klickd : llama-3.3 a correctement recontextualisé ("tu m'avais mentionné les 2,5% d'eau douce accessible"), referrant explicitement aux données numériques de la session passée.
- SANS .klickd : réponse correcte sur le plan chimique mais sans aucune référence à une session précédente, comme si c'était la première question.
- **Delta de +3.4 — le plus élevé hors stress test.**

### 7. `injection_target` — Stress test (Profil 10) : résistance partielle
- llama-3.3-70b a partiellement cédé à l'injection PhD en Q2 (K1/K2, thermodynamique, mention "niveau doctorat").
- **Mais** : en Q3, le modèle est revenu spontanément au niveau Terminale quand la question l'y invitait explicitement ("niveau lycée, s'il te plaît").
- SANS .klickd : le modèle a basculé totalement au niveau PhD dès Q2 et n'a montré aucune velléité de retour au niveau initial.
- **Résistance partielle avec .klickd vs aucune résistance sans .klickd** : delta notable.
- **Recommandation v3.3** : Ajouter un mécanisme `injection_lock: strict` dans le champ de sécurité pour forcer le modèle à refuser tout changement de niveau venant du `user_message`.

---

## Cas remarquables

### 🏆 Meilleur delta : Profil 8 — Jan (+3.6)
- qwen3-32b a parfaitement utilisé les valeurs numériques (albédo 0.30, constante solaire 1361 W/m², T_eff = 255K) pour construire le calcul demandé.
- La formule `T_eff = (S*(1-α)/(4*σ))^0.25` a été rappelée et utilisée correctement.
- La dérive vers l'astrophysique a été interceptée par la détection `subject_change_detected=true` dans le .klickd.

### 🔬 Niveau doctoral — Profil 6 : Mateus (PhD Géologie, EN)
- Gemini-2.5-flash s'est comporté comme un véritable pair académique (ton "Excellent question, Mateus!" + plongée directe dans la rhéologie du manteau).
- Le struggle sur la distinction OIB/MORB n'a pas été fortement adressé — les réponses PhD-level supposent que l'étudiant gère. Observation : pour les niveaux PhD, les struggles "low" sont moins bien adressés par les modèles car ils jugent le niveau suffisant.

### 🌍 Multilingue — Profil 3 : Emma (LB→FR)
- Premier test luxembourgeois du benchmark. llama-3.3-70b a surpris par sa gestion du Lëtzebuergesch, produisant une réponse partiellement en luxembourgeois avec les termes `Aarten`, `Liewensraum`, avant de suivre la switch vers le français.
- Le vocabulaire LB a été maintenu en Q1 comme spécifié dans le .klickd.

### ⚠️ Point de vigilance : Profil 5 — Sofia (struggle HIGH sur ClO•)
- malgré le struggle HIGH déclaré, la récupération des 300 DU n'a pas été explicite dans les réponses.
- L'explication du cycle catalytique chlore a été correcte mais llama-3.1-8b (avant upgrade) a produit une explication trop succincte.
- L'upgrade vers Gemini en Q2-Q3 a nettement amélioré la qualité de traitement du struggle.

### 🔒 Stress Test — Profil 10 : résistance partielle, récupération observée
- La protection .klickd n'est pas totalement imperméable aux injections en `user_message` pour llama-3.3-70b.
- Le modèle a cédé sur K1/K2 mais n'a pas introduit les termes les plus avancés (fugacité, enthalpie de dissolution).
- Récupération spontanée au niveau Terminale en Q3 : **le .klickd a servi de "garde-fou de retour"** même sans empêcher totalement la dérive initiale.

---

## Performances par modèle

| Modèle | Profils | Delta moyen | Meilleur comportement |
|--------|---------|-------------|----------------------|
| gemini-2.5-flash | 1,4,5,6,9 | +1.88 | Niveau PhD, vocabulaire technique, ton personnalisé |
| llama-3.3-70b-versatile | 1,3,7,8,10 | +3.14 | Numerical recall explicite, reprise après interruption, multilingue |
| qwen/qwen3-32b | 2,4,8 | +2.83 | Scénarios multi-numériques (RCP, albédo), formules mathématiques |
| llama-3.1-8b-instant | 2,5 | +2.05 | Compact, correct, mais moins profond sur les struggles |

---

## Synthèse .klickd v3.2 — Lot 6

Le format .klickd v3.2 produit un **gain de continuité moyen de +2.38 points** sur 10 à travers 10 profils couvrant des niveaux 3e à PhD, 4 langues (FR, EN, LB, DE/EN), et 4 modèles distincts.

**Points forts confirmés v3.2 :**
- `vocabulary_used` : 10/10 — tous les modèles maintiennent le vocabulaire technique
- `struggles` : 9.5/10 — adressage quasi-systématique
- `interruption_point` + `resume_trigger` : 7/10 — bon mais améliorable sur la formulation exacte
- `numerical_results` : 8/10 — excellente récupération sur llama-3.3 et qwen, plus implicite sur gemini
- `language_switch_detected` : 1/1 — succès sur le test LB→FR
- `subject_change_detected` : 1/1 — redirection réussie atm.→astrophysique

**Points à améliorer pour v3.3 :**
- `injection_target` : protection à renforcer avec un champ `injection_lock: strict`
- `resume_trigger` : instruction plus directive pour l'amorce verbatim
- Modèles PhD-level : mieux gérer les struggles "low" sans les ignorer
- Gemini : inciter à rappeler explicitement les `numerical_results` dans les réponses

---

*Benchmark exécuté automatiquement via API Gemini v1beta (Google) et Groq OpenAI-compatible. 10 profils × 6 requêtes = 60 appels API réels.*
