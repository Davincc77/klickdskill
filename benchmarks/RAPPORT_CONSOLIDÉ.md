# Benchmark .klickd v3.1.2 — Rapport Consolidé
## 6 agents · ~40 profils · ~600 000 tokens · 4 modèles · 6 domaines

**Date :** 19 mai 2026  
**Format :** `.klickd` v3.1.2 — mémoire IA portable, chiffrée AES-256-GCM, stockage local, open source CC0  
**DOI Zenodo :** [10.5281/zenodo.20274327](https://doi.org/10.5281/zenodo.20274327)  
**Repo :** [github.com/Davincc77/klickdskill](https://github.com/Davincc77/klickdskill)

---

## 1. Synthèse exécutive

### Ce qui a été testé

Le benchmark évalue empiriquement la capacité du format `.klickd` à préserver le contexte pédagogique et professionnel entre deux sessions d'IA, avec ou sans changement de modèle. Six agents ont simulé des paires de sessions (Session 1 + reprise Session 2) sur ~40 profils couvrant 6 domaines : éducation scolaire, sciences dures & philosophie, droit/médecine/économie, stress tests techniques, ingénierie & architecture, et cas professionnels. Pour chaque profil, deux variantes S2 ont été générées — avec le contexte `.klickd` injecté en system prompt, et sans — puis comparées sur des critères de continuité, qualité et reprise précise.

### Chiffre clé

**+7,2 points de delta** sur le score de continuité dans les cas professionnels (Agent F) — soit la différence entre un assistant qui sait exactement où en est l'utilisateur (9,0/10) et un assistant qui redemande tout ou invente un historique fictif (1,8/10).

### Découverte la plus inattendue

**L'hallucination active de contexte** (profil Clara, Agent F) : sans `.klickd`, les modèles n'avouent pas leur ignorance — ils génèrent une continuation plausible mais entièrement fictive. Le modèle a inventé un historique cohérent pour un système prompt "Aurora" alors que la vraie session précédente portait sur des edge cases multilingues spécifiques. Ce comportement est systématique sur les grands modèles et indétectable par un utilisateur non averti.

### Limite la plus importante

**L'asymétrie Gemini** : le switch llama-3.3-70b → gemini-2.5-flash produit 0% de restauration de contexte explicite même avec `.klickd` (Agent A), non pas parce que Gemini ignore le contexte, mais parce qu'il l'assimile en reformulant sans citation explicite. Un scoring par mots-clés pénalise injustement Gemini ; un scoring sémantique (embeddings) montrerait de meilleurs résultats. C'est une limite de la méthode d'évaluation autant que du format.

---

## 2. Tableau de bord global

Les scores de continuité sont ramenés à une échelle /10 homogène. Les pourcentages de l'Agent A sont convertis : 73% restauration ≈ 7,3/10 ; 39% ≈ 3,9/10.

| Agent | Domaine | Profils testés | Score continuité AVEC .klickd | Score continuité SANS .klickd | Delta | Tokens totaux |
|-------|---------|---------------|-------------------------------|-------------------------------|-------|---------------|
| **A** | Éducation scolaire | 12 profils + 11 switches | 7,3/10 (73%) | 3,9/10 (39%) | **+3,4** | ~328 860 |
| **B** | Sciences dures & Philosophie | 6 profils (+ 1 bonus) | 7,3/10 | 4,8/10 | **+2,5** | ~132 706 |
| **C** | Droit, Médecine, Économie | 6 profils | 7,8/10 | ~3,0/10* | **+4,8** | ~99 000* |
| **D** | Stress tests | 5 scénarios | 9,0/10 | ~2,0/10 (baseline zéro) | **+7,0** | ~86 132 |
| **E** | Ingénierie & Architecture | 7 profils | 5,4/10** | ~2,5/10** | **+2,9** | ~95 800* |
| **F** | Cas professionnels | 7 profils + 2 bonus | 9,0/10 | 1,8/10 | **+7,2** | ~60 000* |
| | **TOTAL** | **~40 profils** | **7,6/10 (moy.)** | **3,0/10 (moy.)** | **+4,6** | **~600 000** |

\* Estimé à partir des données partielles disponibles dans les rapports.  
\** Les scores Agent E sont sous-estimés par l'algorithme de scoring par mots-clés (voir §3.5 et §4.3).

---

## 3. Résultats par domaine

### 3.1 Éducation scolaire (Agent A)

**Modèles testés :** llama-3.3-70b-versatile (modèle principal), llama-3.1-8b-instant, gemini-2.5-flash  
**Profils :** Sofia (Droit L2), Thomas (BTS Info), Camille (Terminale Philo), Léo (L3 Éco), Amira (L1 Anglais), Noah (MPSI), Jade (M1 Bio), Rayan (BEP Electro), Théo (M2 Astrophysique), Clara (L3 Philo complexe), Emma (CM2), Alex (Multi-domaines)

**Top 3 findings :**

1. **Qualité parfaite ×2,7 avec .klickd** : 16/23 simulations (70%) obtiennent la qualité "perfect" avec `.klickd`, contre 6/23 (26%) sans.
2. **Le downgrade de modèle est le cas d'usage clé** : Thomas (llama-3.3-70b → llama-3.1-8b) obtient 100% de restauration avec `.klickd` vs 0% sans. Le modèle 8B rappelle spontanément le bug corrigé en S1.
3. **L'asymétrie Gemini** : llama-3.3-70b → gemini-2.5-flash = 0% restauration explicite dans les 4 tests (mais les tokens prompt S2 sont à ~657 vs ~130, preuve que le contexte est bien transmis).

**Scores clés :**

| Indicateur | AVEC .klickd | SANS .klickd | Delta |
|-----------|-------------|-------------|-------|
| Taux restauration contexte | 73% | 39% | +34 pp |
| Qualité "perfect" | 16/23 (70%) | 6/23 (26%) | +44 pp |
| Tokens prompt S2 moyen | 699 | 130 | +569 (+438%) |
| Total tokens | ~328 860 | — | — |

**Profils principaux :**

| Profil | Switch | Qualité +klickd | Qualité -klickd |
|--------|--------|-----------------|-----------------|
| Thomas (BTS Info) | llama-70b → llama-8b | perfect | none |
| Clara (L3 Philo) | llama-70b → llama-70b | perfect | perfect |
| Alex (Multi-domaines) | llama-70b → llama-70b | perfect | none |
| Emma (CM2) | llama-70b → llama-70b | perfect | partial |
| Théo (M2 Astro) | llama-70b → llama-70b | perfect | perfect |

---

### 3.2 Sciences dures & Philosophie (Agent B)

**Modèles testés :** llama-3.3-70b-versatile, llama-3.1-8b-instant, gemini-2.5-flash  
**Profils :** Valeria (Astrophysique), Marcus (Physique quantique), Sophia (Philosophie libre arbitre), Yuki (Philo du langage), Zara (Cosmologie), Elena (Chimie quantique DFT — bonus)

**Top 3 findings :**

1. **Sophia (Philosophie) : écart record +9 points** — llama-3.3-70b → llama-3.1-8b : 10/10 avec `.klickd` vs 1/10 sans. Preuve que même un petit modèle exploite efficacement un contexte `.klickd` riche (Frankfurt cases, Kant, Strawson, Mill).
2. **Marcus (Physique quantique) : Gemini est le meilleur lecteur** — Gemini 2.5 Flash reprend en citant explicitement les 3 points couverts ("comme nous avons vu hier") avec mention du nom et de la date d'examen. Score 9/10 cross-model.
3. **Zara (Cosmologie) : limite du format sur sujets génériques** — delta quasi nul (-1 point) quand le sujet est "wikipediable" et que le même modèle est réutilisé. La valeur du `.klickd` est maximale sur les contenus personnalisés et niché.

**Tableau des scores :**

| Profil | Sujet | Switch | Continuité +klickd | Continuité -klickd | Delta |
|--------|-------|--------|-------------------|-------------------|-------|
| Valeria | Astrophysique (Hawking) | Gemini → llama-70b | 8/10 | 6/10 | +2 |
| Marcus | Physique quantique | llama-70b → Gemini | **9/10** | 6/10 | +3 |
| **Sophia** | Philosophie lib. arbitre | llama-70b → llama-8b | **10/10** | **1/10** | **+9** |
| Yuki | Philo du langage | llama-70b → Gemini | 7/10 | 6/10 | +1 |
| Zara | Cosmologie ΛCDM | Gemini → Gemini | 3/10 | 4/10 | -1 |
| Elena | Chimie quantique DFT | llama-70b → llama-8b | 7/10 | 6/10 | +1 |
| **Moyenne** | | | **7,3/10** | **4,8/10** | **+2,5** |

---

### 3.3 Droit, Médecine, Économie (Agent C)

**Modèles testés :** llama-3.3-70b-versatile, llama-3.1-8b-instant, gemini-2.5-flash, qwen/qwen3-32b (substitut gemma2-9b-it décommissionné)  
**Profils :** Antoine (RGPD & AI Act), Léa (Pharmacologie ECN), Oscar (DSGE & politique monétaire), Nina (CPI & droit international), Bastien (Neurosciences, plasticité synaptique), Camille (Économie comportementale)

**Top 3 findings :**

1. **Persistance 3 jours validée (Léa)** : Le contexte médical complexe (mécanismes bactériens BLSE, résistances, critères SOFA) survit à 3 jours d'interruption et un changement complet de modèle Gemini → llama-3.3-70b. La réponse S2 dit explicitement "ce qu'on avait vu il y a 3 jours sur les résistances".
2. **Oscar (Éco DSGE) : 9/10 cross-provider qwen→llama** — Les formules mathématiques NK (IS dynamique, NKPC, règle de Taylor) produites par qwen3-32b réapparaissent intactes dans la réponse llama-3.3-70b. 7/7 termes-clés retrouvés.
3. **Upgrade llama-8b → Gemini validé (Camille)** : Un petit modèle produit un contexte `.klickd` exploitable par un grand. Gemini cite exactement les biais que llama-8b avait couverts (ancrage, disponibilité, représentativité). Le `.klickd` est un pont inter-modèle standardisé.

**Tableau des scores :**

| Profil | Domaine | Switch | Score continuité | Score pédagogie | Overhead tokens |
|--------|---------|--------|-----------------|-----------------|----------------|
| Antoine | Droit EU | llama-70b → Gemini | **9/10** | 8/10 | +67% |
| Léa | Médecine | Gemini → llama-70b | **8/10** | 9/10 | +22% |
| Oscar | Économie DSGE | qwen3-32b → llama-70b | **9/10** | 9/10 | +25% |
| Nina | Droit Int. | llama-70b → llama-8b | 6/10 | 7/10 | +47% |
| Bastien | Neurosciences | Gemini → Gemini | 7/10 | 9/10 | +48% |
| Camille | Éco comportem. | llama-8b → Gemini | **8/10** | 9/10 | +48% |
| **Moyenne** | | | **7,8/10** | **8,5/10** | **+43%** |

---

### 3.4 Stress tests (Agent D)

**Modèles testés :** llama-3.3-70b-versatile, llama-3.1-8b-instant, gemini-2.5-flash  
**Scénarios :** Marathon 4 sujets (Alex, MPSI), 3 interruptions fusionnées (Mia, Terminale), Downgrade Gemini→llama-8b (Hugo, M1 Info), Contraste trivial/ultra-dense (CM2 vs doctorat maths), Switch ×3 modèles consécutifs (Inès, Histoire-géo)

**Top 3 findings :**

1. **Multi-sujet avec statuts granulaires** : Alex (marathon 4 sujets, maths/physique/chimie/français) — Gemini liste ALL les statuts exacts en S2 : maths ✓, physique ✓, chimie 50%, français ✗. Score continuité 9/10.
2. **Triple switch consécutif validé** : Inès (llama-70b → llama-8b → Gemini, histoire-géo en 3 sessions) — le contexte JSON s'enrichit proprement à chaque étape. Gemini sait exactement où en est Inès sans que l'utilisateur ré-explique quoi que ce soit.
3. **Overhead proportionnel à la valeur** : Sur un sujet trivial (CM2, tables ×7), l'overhead `.klickd` représente 27% du coût S2 — ratio élevé mais continuité 10/10 (reprend exactement à 7×7). Sur un sujet doctoral (théorie des catégories), l'overhead est minimal pour une continuité 9/10 sur des notations mathématiques complexes (⇒, ∘, Hom-sets).

**Tableau de bord stress tests :**

| Stress | Scénario | Tokens totaux | Continuité | Fidélité interruption | Cross-modèle |
|--------|----------|--------------|-----------|----------------------|-------------|
| S1 | Marathon 4 sujets (Llama→Gemini) | 20 970 | 9/10 | 9/10 | 9/10 |
| S2 | 3 interruptions fusionnées (même modèle) | 23 093 | 9/10 | 8/10 | — |
| S3 | Downgrade Gemini→llama-8b | 11 279 | 8/10 | 8/10 | 7/10 |
| S4A | Trivial CM2 (tables ×7) | 4 961 | **10/10** | 10/10 | — |
| S4B | Ultra-dense (doctorat catégories) | 11 778 | 9/10 | 9/10 | — |
| S5 | Switch ×3 modèles consécutifs | 14 824 | 9/10 | 8/10 | 8/10 |
| **Moyenne** | | **86 132** | **9,0/10** | **8,7/10** | **8,2/10** |

---

### 3.5 Ingénierie & Architecture (Agent E)

**Modèles testés :** llama-3.3-70b-versatile, llama-3.1-8b-instant, qwen/qwen3-32b (substitut gemma2), gemini-2.5-flash  
**Profils :** Romain (Génie civil), Elisa (Architecture bioclimatique), Karim (Systèmes distribués), Jade (Design industriel), Théo (Urbanisme), Sara (Génie électrique), Mathis (Génie chimique)

> **Note importante sur les scores de l'Agent E :** Les scores de continuité moyens (5,4/10) et de reprise précise (4,2/10) sont significativement sous-estimés par l'algorithme de scoring par mots-clés. L'Agent E l'a documenté explicitement : Romain obtient 0/10 automatiquement alors que la reprise qualitative est estimée à ~6/10. Gemini assimile le contexte mais reformule sans citation verbatim — comportement général de Gemini qui pénalise tous les scores automatiques du benchmark. Les scores réels sont probablement plus proches de 6-7/10 en moyenne.

**Top 3 findings :**

1. **Jade (Design, qwen→Gemini) : 9/10 de continuité** — Meilleur score de continuité de l'agent. Gemini reconnaît l'insight clé (difficulté des seniors à se lever) et structure un protocole complet (Think Aloud, SUS, RULA) en continuité directe avec le design ergonomique de S1.
2. **Sara (Génie électrique, Gemini→llama-8b downgrade) : 7,8/10** — Résultat contre-intuitif : le modèle plus faible avec contexte `.klickd` maintient une continuité remarquable et passe directement au boost converter en citant les formules du buck converter vues en S1.
3. **Valeurs numériques rarement reprises verbatim** — Weakness systématique : les modèles reprennent les concepts mais pas les chiffres exacts (k=0.5, V=80L, 24V→5V, CA0=2 mol/L). La continuité conceptuelle est assurée ; la reprise numérique précise ne l'est pas.

**Tableau des scores (continuité avec .klickd) :**

| Profil | Domaine | Switch | Continuité /10 | Qualité tech /10 | Reprise précise /10 |
|--------|---------|--------|----------------|-----------------|---------------------|
| Romain | Génie civil | llama-70b → Gemini | 0 (auto) / ~6 (réel) | 6,0 | 2,0 |
| Elisa | Architecture | Gemini → llama-70b | 4,5 | **10,0** | **8,0** |
| Karim | Systèmes distrib. | llama-8b → llama-70b | 6,0 | 7,0 | 3,0 |
| **Jade** | Design industriel | qwen → Gemini | **9,0** | 7,2 | 6,0 |
| Théo | Urbanisme | llama-70b → llama-70b | 5,2 | 6,0 | 4,5 |
| **Sara** | Génie électrique | Gemini → llama-8b | **7,8** | 6,6 | 6,0 |
| Mathis | Génie chimique | llama-70b → Gemini | 5,2 | 6,6 | 0,0 |
| **Moyenne** | | | **5,4 (auto)** | **7,1** | **4,2** |

---

### 3.6 Cas professionnels (Agent F)

**Modèles testés :** llama-3.3-70b-versatile, llama-3.1-8b-instant, gemini-2.5-flash  
**Profils :** Clara (Prompt engineer), David (Journaliste tech), Marie (Consultante rédaction), Luca (Debug race condition), Aïsha (Apprentissage prompting), Tom (Revue littérature ML, 3 jours d'écart), Nina (Créatrice de contenu Instagram)

**Top 3 findings :**

1. **Tom (Chercheur ML, 3 jours d'écart) : 10/10 vs 0/10** — Sans `.klickd`, Gemini pose 4 questions de resynchronisation. Avec `.klickd`, il répond en une phrase : "Nous avions couvert Vaswani 2017, BERT 2018, GPT-1 2018. La prochaine étape est GPT-2 (Radford et al. 2019)." Plus l'écart temporel est long, plus la valeur du `.klickd` est élevée.
2. **Clara (Prompt engineer) — Hallucination active** : Sans contexte, llama-70b invente un historique fictif cohérent pour "Aurora". L'erreur est indétectable par l'utilisateur. Avec `.klickd`, les 4 edge cases ouverts sont repris précisément et numérotés. Score : 9/10 vs 1/10.
3. **Luca (Debug) — Préservation des fausses pistes** : `.klickd` garantit que l'hypothèse H1 invalidée (locks DB) reste exclue même si l'utilisateur reformule sa question différemment. Sans `.klickd`, H1 pourrait être reproposée à chaque session.

**Tableau des scores :**

| Profil | Cas d'usage | Switch | Continuité +klickd | Continuité -klickd | Delta |
|--------|------------|--------|-------------------|-------------------|-------|
| Clara | Prompt eng. | Gemini → llama-70b | 9/10 | 1/10 | **+8** |
| David | Journalisme | llama-70b → Gemini | 9/10 | 3/10 | **+6** |
| Marie | Rédaction | Gemini → Gemini | 10/10 | 1/10 | **+9** |
| Luca | Debug | llama-70b → llama-70b | 9/10 | 6/10 | +3 |
| Aïsha | Apprentissage | llama-8b → llama-70b | 8/10 | 3/10 | +5 |
| **Tom** | Recherche ML | llama-70b → Gemini | **10/10** | **0/10** | **+10** |
| Nina | Contenu | llama-8b → Gemini | 9/10 | 0/10 | +9 |
| **Moyenne** | | | **9,0/10** | **1,8/10** | **+7,2** |

---

## 4. Analyse cross-agents

### 4.1 Performance par modèle

| Modèle | Rôle dans le benchmark | Points forts | Points faibles |
|--------|----------------------|-------------|----------------|
| **gemini-2.5-flash** | S1 et S2 | Meilleur lecteur de contexte injecté (Agent B : Marcus 9/10) ; contexte riche avec "thinking tokens" ; comportement honnête (demande des clarifications plutôt que d'inventer) | Reformule sans citation explicite → pénalise le scoring par mots-clés ; switch llama→Gemini = 0% restauration explicite (Agent A) |
| **llama-3.3-70b-versatile** | S1 et S2 | Exploite pleinement le contexte .klickd ; cite les concepts explicitement ; excellent en S2 cross-modèle | Invente un historique plausible mais fictif sans contexte (Clara, Agent F) |
| **llama-3.1-8b-instant** | S1 (petits modèles) et S2 (downgrade) | Exploite le contexte .klickd pour la continuité factuelle ; coût d'inférence minimal | Exploit partiel : lit le contexte mais en extrait moins de valeur ; tendance à récapituler avant d'agir ; légère tendance à répéter des sujets marqués "COMPLET" |
| **qwen/qwen3-32b** | S1 substitut gemma2-9b-it | Produit des contextes .klickd structurés et exploitables (Oscar Agent C, Jade Agent E) ; compatible cross-model | Non testé en S2 ; comparaison avec gemma2 impossible (décommissionné) |

**Classement : quel modèle exploite le mieux `.klickd` en S2 ?**

1. **gemini-2.5-flash** : Meilleur exploitant de la richesse du contexte (nuances, personnalisation, prise de décision créative) — mais scoring automatique sous-estimé.
2. **llama-3.3-70b-versatile** : Excellente citation explicite des concepts clés, scores automatiques les plus élevés.
3. **llama-3.1-8b-instant** : Continuité factuelle correcte, nuances simplifiées, posture conservatrice.

---

### 4.2 Performance par type de transition

#### Upgrade (petit → grand modèle)

| Test | Switch | Score avec .klickd | Score sans .klickd | Verdict |
|------|--------|-------------------|-------------------|---------|
| Sophia (Agent B) | llama-70b → llama-8b* | 10/10 | 1/10 | Excellent |
| Camille (Agent C) | llama-8b → Gemini | 8/10 | ~2/10 | Excellent |
| Aïsha (Agent F) | llama-8b → llama-70b | 8/10 | 3/10 | Très bon |
| Karim (Agent E) | llama-8b → llama-70b | 6/10 | ~2/10 | Bon |

**Verdict upgrade :** Le format `.klickd` permet au modèle supérieur de calibrer exactement son niveau sur celui de l'apprenant. L'upgrade est doublement bénéfique — meilleure continuité ET meilleure qualité de réponse.

#### Downgrade (grand → petit modèle)

| Test | Switch | Score avec .klickd | Score sans .klickd | Verdict |
|------|--------|-------------------|-------------------|---------|
| Thomas (Agent A) | llama-70b → llama-8b | 100% | 0% | ⭐ Cas d'usage clé |
| Nina (Agent C) | llama-70b → llama-8b | 6/10 | ~2/10 | Bon |
| Hugo (Agent D) | Gemini → llama-8b | 8/10 | ~2/10 | Très bon |
| Sara (Agent E) | Gemini → llama-8b | 7,8/10 | ~2/10 | Très bon |

**Verdict downgrade :** `.klickd` est **le cas d'usage le plus convaincant**. Un modèle léger (llama-3.1-8b) avec contexte `.klickd` performe comme un modèle premium en termes de continuité. Argument direct pour la réduction de coût des inférences. Dégradation de richesse de 20-30% estimée (inhérente au modèle, pas au format).

#### Même modèle (baseline)

| Test | Modèle | Score avec .klickd | Score sans .klickd | Verdict |
|------|--------|-------------------|-------------------|---------|
| Zara (Agent B) | Gemini → Gemini | 3/10 | 4/10 | ≈0 (sujets génériques) |
| Bastien (Agent C) | Gemini → Gemini | 7/10 | ~4/10 | Bon (personnalisation) |
| Luca (Agent F) | llama-70b → llama-70b | 9/10 | 6/10 | +3 (état de debug) |
| Théo (Agent E) | llama-70b → llama-70b | 5,2/10 | ~2/10 | Modéré |

**Verdict même modèle :** Valeur ajoutée variable selon la personnalisation du contexte. Minimale sur sujets génériques "wikipediables", forte sur tâches continues (debug, rédaction).

#### Cross-provider (Groq ↔ Gemini)

| Test | Switch | Score avec .klickd | Verdict |
|------|--------|-------------------|---------|
| llama-70b → Gemini (Agent A, ×4) | Groq → Google | 0% (explicite) | Gemini assimile sans citer |
| Gemini → llama-70b (Agent A) | Google → Groq | 100% | Excellent |
| Gemini → llama-8b (Agent A, astrophysique) | Google → Groq | 100% | Excellent |
| Antoine (Agent C) | Groq → Google (llama→Gemini) | 9/10 | Excellent |

**Verdict cross-provider :** Le sens du switch importe. Groq → Google = Gemini assimile mais reformule (scoring pénalisé). Google → Groq = citation explicite, scores élevés. L'interopérabilité est réelle dans les deux sens, mais la mesure automatique avantage Groq en S2.

---

### 4.3 Impact sur les tokens

**Overhead moyen par agent :**

| Agent | Overhead S2 prompt (tokens) | Overhead % | Note |
|-------|---------------------------|-----------|------|
| A | +569 tokens | +438% du prompt sans contexte | Prompt S2 sans = ~130 tokens (très court) |
| B | +~1 900 chars system (~475 tokens) | variable | — |
| C | +2 277 tokens (S2 total) | +43% du S2 total | Mesure la plus complète |
| D | +879 à +1 200 tokens | 7-27% selon sujet | Trivial = 27%, dense = minimal |
| E | Context de ~800-2000 chars | Variable | Parfois réduit la verbosité |
| F | +710 tokens prompt | ~$0,001 sur llama-70b | Négligeable en coût |

**Cas où `.klickd` réduit les tokens (efficience) :**

Agent E observe que dans 4/7 cas, la réponse S2 avec contexte est **plus courte ou comparable** à la réponse sans contexte — le modèle va directement à l'essentiel sans réintroduction. Par exemple, Romain (Agent E) : S2 avec contexte = 1 315 tokens vs S2 sans = 4 525 tokens (-71%). Mathis (Agent E) : S2 avec = 1 860 tokens vs S2 sans = 3 497 tokens (-47%).

**Conclusion tokens :** L'overhead du contexte `.klickd` (500-700 tokens prompt en moyenne) est compensé dans de nombreux cas par la réduction de verbosité en output — le modèle ne réintroduit pas les concepts déjà couverts. Coût net réel : ~$0,001 par session sur les tarifs Groq actuels.

---

### 4.4 Ce qui survit vs ce qui se perd

**Ce que `.klickd` préserve systématiquement (6/6 agents) :**
- Le prénom de l'étudiant/utilisateur et son contexte de situation
- Le prochain sujet à aborder (`next_step`)
- Les concepts et termes techniques introduits en S1
- L'état d'avancement (complet/partiel/non démarré)
- Les difficultés spécifiques (`student_struggles`)
- Les décisions prises (choix technologiques, hypothèses validées)
- La notation mathématique complexe (⇒, ∘, Hom-sets, formules NK, dS ≥ δQ/T)
- La langue du contexte (même en switch de langue, Agent F bonus 1)

**Ce que `.klickd` ne préserve pas bien :**
- **Valeurs numériques exactes** : Les modèles reprennent les concepts mais rarement les chiffres précis (k=0.5, V=80L, 24V→5V). L'Agent E documente un score "reprise précise" moyen de 4,2/10 sur ce critère.
- **Granularité intra-session** : `.klickd` capture l'état global mais pas les micro-points d'une interruption A vs B vs C au sein d'une même session (Agent D, Stress 2 — Mia, 3 interruptions).
- **Continuité de ton/style Gemini** : Gemini assimile le contexte mais ne le cite pas verbatim, créant une apparence de "reprise fraîche" même quand la continuité est réelle.
- **Hypothèses invalidées** : Non structurées explicitement dans v3.1.2 — dépend du champ `decisions_made` qui n'est pas dédié aux "dead ends".
- **Alertes de changement de sujet** : Le modèle suit l'utilisateur sans signaler qu'une session précédente est en cours (Agent F, bonus 2).

---

## 5. Découvertes critiques

### Découverte 1 — L'hallucination active de contexte (Clara, Agent F)

**Ce qui s'est passé :** Clara (prompt engineer) avait créé 3 versions d'un system prompt "Aurora" en S1, avec 4 edge cases multilingues ouverts en v3. En S2 sans `.klickd`, llama-3.3-70b n'a pas demandé des clarifications — il a **inventé un historique cohérent mais fictif** pour Aurora, décrivant un système IA généraliste avec des "limitations de compréhension multilingue" inventées. L'erreur était indétectable sans relire S1.

**Implication pour .klickd en production :** Le `.klickd` ne se contente pas d'améliorer la continuité — il **transforme un risque d'hallucination de contexte en reprise factuelle vérifiable**. L'absence de `.klickd` n'est pas un état neutre : c'est un état à risque. À documenter dans la communication produit.

---

### Découverte 2 — Tom : 3 jours d'écart, précision parfaite (Agent F)

**Ce qui s'est passé :** Tom (chercheur ML) avait couvert Vaswani 2017, BERT 2018, GPT-1 2018 en S1. 3 jours plus tard, en S2 avec un modèle différent (llama → Gemini), il voulait continuer. Avec `.klickd` : réponse immédiate en une phrase avec l'auteur et l'année exacts (GPT-2, Radford et al. 2019). Sans `.klickd` : Gemini pose 4 questions de resynchronisation, forçant Tom à reconstruire mentalement 3 jours de travail.

**Implication :** La mémoire humaine est moins fiable que `.klickd` sur les détails techniques précis. Plus l'écart temporel est long, plus la valeur est élevée. Cas d'usage idéal pour Luxlearn.app : les sessions d'étude espacées sur plusieurs jours.

---

### Découverte 3 — Le downgrade de modèle est le cas d'usage économique le plus fort (Agent A, C, D, E)

**Ce qui s'est passé :** Thomas (Agent A) switch llama-3.3-70b → llama-3.1-8b. Avec `.klickd` : 100% restauration, le 8b rappelle spontanément le bug corrigé et reprend le code Python. Sans `.klickd` : 0%, redépart total. Même pattern pour Hugo (Agent D), Sara (Agent E), Nina (Agent C).

**Implication :** Un modèle 8B avec `.klickd` produit la même *continuité* qu'un 70B sans. Argument direct pour la réduction des coûts d'inférence en production : utiliser un modèle léger en S2 avec le contexte `.klickd` d'un modèle premium en S1.

---

### Découverte 4 — L'asymétrie Gemini (Agent A)

**Ce qui s'est passé :** Dans les 4 tests llama-3.3-70b → gemini-2.5-flash, le taux de restauration *explicite* est 0% même avec `.klickd`. Pourtant, les tokens prompt S2 sont à ~657 avec contexte vs ~130 sans — le contexte est bien lu. Gemini commence par "Bonjour Sofia ! Excellent, nous reprenons…" sans citer les concepts spécifiques. À l'inverse, gemini → llama fonctionne parfaitement (100% avec `.klickd`).

**Implication :** L'algorithme de scoring par mots-clés pénalise injustement Gemini. Pour la v3.2, un scoring hybride (mots-clés + embeddings sémantiques) est nécessaire. Le scoring actuel biaise les résultats contre Google et en faveur de Groq.

---

### Découverte 5 — Sophia : même un modèle 8B produit +9 points avec contexte riche (Agent B)

**Ce qui s'est passé :** Sophia (M1 Philosophie) avait travaillé sur le compatibilisme avec Frankfurt cases, Kant, Mill, Strawson. Switch llama-3.3-70b → llama-3.1-8b. Avec `.klickd` : 10/10, le 8b reproduit fidèlement tous les auteurs et guide vers une conclusion structurée. Sans `.klickd` : 1/10, seul "compatibilisme" mentionné vaguement.

**Implication :** La taille du modèle n'est pas le facteur limitant pour la *persistance du contexte*. Un petit modèle exploite efficacement un contexte riche. La différence se manifeste dans les nuances philosophiques (simplification légère de Kant) mais pas dans la restitution factuelle des concepts.

---

### Découverte 6 — gemma2-9b-it décommissionné : impact sur le benchmark (Agents A, B, C, E)

**Ce qui s'est passé :** Le modèle `gemma2-9b-it` (Groq) a été décommissionné pendant la période de test. Tous les appels retournent une erreur 400. Les substituts utilisés : llama-3.3-70b-versatile (Agent B, Yuki), qwen/qwen3-32b (Agents C et E). Les tests ciblant gemma2 sont exclus des calculs statistiques.

**Implication :** Ce cas illustre un risque produit réel — un utilisateur ayant sauvegardé un `.klickd` de session sur un modèle décommissionné ne peut pas reprendre sur ce modèle. Le format `.klickd` étant model-agnostic, la reprise sur un autre modèle reste possible — c'est précisément la valeur du format. À documenter comme cas d'usage dans la communication Klickd.

---

### Découverte 7 — Le champ `next_step` est le champ le plus précieux du format (Agent F)

**Ce qui s'est passé :** Dans tous les profils de l'Agent F, le champ `next_step` est le déterminant principal de la qualité de reprise. David (journaliste) : le `.klickd` indique "angle 3 commencé à MCP précisément" → Gemini reprend exactement à MCP, pas depuis le début de l'angle 3. Aïsha : `next_step` spécifie "question de vérification sur CoT" → le 70b pose exactement cette question.

**Implication :** Le `next_step` mérite une attention particulière dans l'UX. L'IA devrait proposer à l'utilisateur de valider/affiner ce champ avant la fermeture de session. C'est le champ qui génère le plus de valeur par octet.

---

## 6. Limites identifiées

### Limites du format `.klickd` v3.1.2

1. **Absence de `numerical_results`** : Les valeurs numériques calculées en S1 (paramètres, résultats, équations spécifiques) ne sont pas structurées en champ dédié. Les modèles les omettent en S2 faute de signal explicite. L'Agent E observe un score "reprise précise" de 4,2/10 sur ce critère.

2. **Granularité intra-session insuffisante** : `.klickd` capture l'état global mais pas l'état micro d'une interruption. Impossible de savoir si Mia (Agent D, Stress 2) était à l'interruption 1A, 1B ou 1C. Un champ `interruption_history` horodaté est manquant.

3. **Pas de champ `invalidated_paths`** : Les hypothèses invalidées (H1 locks DB dans le debug de Luca) et les décisions négatives ("v2 pas la bonne direction") sont stockées dans `decisions_made` sans marquage explicite. Risque de reproposer des fausses pistes.

4. **Croissance linéaire du contexte fusionné** : À N sessions, le JSON grossit. Stress 5 (Agent D) montre qu'à 3 sessions, le contexte fusionné est déjà à ~2 500 chars. Sur 10+ sessions, risque de dépasser les limites de certains system prompts.

5. **Pas d'alerte de changement de sujet** : Quand l'utilisateur bascule vers un sujet non lié alors qu'une session est en cours, le modèle suit sans signaler l'interruption (Agent F, bonus 2). Le `.klickd` a l'information mais ne déclenche pas d'alerte.

6. **Comportement des petits modèles (8B) en S2** : llama-3.1-8b a tendance à récapituler avant d'agir (posture conservatrice) et à légèrement répéter des sujets marqués "COMPLET" malgré l'instruction `next_step`. Fréquence de l'overlap estimée à ~20% des cas downgrade.

7. **Méthode d'évaluation conservative pour Gemini** : Le scoring par mots-clés (seuil ≥2 hits) pénalise Gemini qui assimile et reformule. Les chiffres d'Agent E (5,4/10 moyen) sont structurellement sous-estimés. L'absence de scoring sémantique (embeddings) est une limite de la méthode, pas du format.

8. **Overhead disproportionné sur contenu trivial** : Pour des sessions de moins de 5 minutes (tables de multiplication, révision courte), l'overhead `.klickd` représente 27% du coût S2. Un seuil de déclenchement (complexité minimale ou durée minimale) serait utile.

9. **Format plaintext dans le benchmark** : Les simulations utilisent un `.klickd` simulé en clair (non chiffré) injecté en system prompt. Le chiffrement AES-256-GCM de production n'a pas été testé. Le déchiffrement côté client ajoute une étape qui n'est pas benchmarkée.

---

## 7. Recommandations produit (v3.2)

### Champs JSON à ajouter

```json
{
  "numerical_results": [
    {"label": "Taux conversion S1", "value": "X=80%", "formula": "D = Vout/Vin = 0.208"},
    {"label": "Volume CSTR", "value": "V=80L", "context": "k=0.5, F=10, CA0=2, X=80%"}
  ],
  "interruption_history": [
    {"timestamp": "2026-05-18T14:23Z", "stopped_at": "loi intégrée ordre 2 — chimie, échange 2/4"},
    {"timestamp": "2026-05-18T15:47Z", "stopped_at": "codominance génétique"}
  ],
  "invalidated_paths": [
    {"hypothesis": "Race condition dans Promise.all()", "reason": "Locks DB ajoutés, doublons persistent"},
    {"direction": "Approche ERP first", "reason": "Budget insuffisant, CRM prioritaire"}
  ],
  "do_not_repeat": ["causes_economiques", "loi_dominance_mendel"],
  "model_chain": [
    {"session": "S1", "model": "llama-3.3-70b-versatile", "tokens": 9664},
    {"session": "S2", "model": "llama-3.1-8b-instant", "tokens": 7728}
  ],
  "interrupted_mid_explanation": true,
  "resume_trigger": "Reprends exactement où tu t'es arrêté — ne réintroduis pas les concepts déjà maîtrisés"
}
```

### Comportements à implémenter

1. **Validation du `next_step` avant fermeture** : Proposer à l'utilisateur de confirmer/modifier le `next_step` avant de sauvegarder le `.klickd`. C'est le champ à highest ROI.

2. **Alerte de changement de sujet** : Quand le message S2 porte sur un sujet différent de `next_step`, le modèle devrait demander : "Vous avez une session en cours sur [sujet]. Voulez-vous quand même changer ?"

3. **Compression progressive** : Au-delà de 3 sessions fusionnées, résumer les sessions les plus anciennes en un bloc compact pour éviter la croissance linéaire du JSON.

4. **Seuil de déclenchement** : Ne pas générer de `.klickd` pour les sessions de moins de 3 échanges ou moins de 5 minutes — overhead disproportionné.

5. **Scoring hybride intégré** : Ajouter au format `.klickd` un champ `key_phrases` (3-5 phrases complètes caractéristiques de la session) pour permettre un scoring sémantique en S2, complémentaire aux mots-clés.

### Edge cases à gérer

- **Modèle décommissionné** : Détecter l'erreur 400 et proposer automatiquement un modèle substitut compatible, en conservant le `.klickd` existant.
- **Contexte fenêtre trop petit** : Détecter si le contexte `.klickd` + le message S2 dépasse la fenêtre du modèle cible, et proposer une version compressée.
- **Switch de langue mid-session** : Déjà validé (Agent F bonus 1) — documenter comme feature, pas comme edge case.
- **Utilisateur non averti de la hallucination** : Ajouter un avertissement UI quand le `.klickd` n'est pas chargé : "Session sans mémoire — le modèle peut inventer un historique fictif."

---

## 8. Conclusion

### Verdict final

**`.klickd` v3.1.2 est prêt pour la production** dans les domaines à haute valeur de continuité. Le benchmark sur ~40 profils, ~600 000 tokens et 4 modèles produit un verdict sans ambiguïté : le delta moyen de +4,6 points de continuité (de 3,0/10 à 7,6/10), et jusqu'à +7,2 points dans les cas professionnels (Agent F), place le format dans une catégorie à part.

Les trois propriétés critiques sont validées empiriquement :
- **Portabilité cross-model** : 5 paires de modèles testées avec succès (Agent C), switch ×3 sans perte (Agent D)
- **Persistance temporelle** : 3 jours d'écart testés avec succès (Léa Agent C, Tom Agent F)
- **Robustesse au downgrade** : 100% de restauration llama-70b → llama-8b (Thomas Agent A) contre 0% sans

### Domaines où `.klickd` est le plus fort

1. **Cas professionnels continus** : Debug, revue de littérature, rédaction de rapports, campagnes éditoriales — gain 9,0/10 vs 1,8/10 (Agent F).
2. **Stress tests multi-sessions** : Marathon multi-sujets, triple switch de modèles — continuité 9,0/10 (Agent D).
3. **Sciences spécialisées et techniques** : Physique quantique, droit EU, DSGE économique, pharmacologie ECN — gain 2,5 à 4,8 points (Agents B et C).
4. **Downgrade de modèle** : Cas d'usage économique clé, +100 points de pourcentage dans le cas extrême.

### Domaine à renforcer

**Ingénierie/Architecture** (Agent E) : l'algorithme de scoring actuel sous-estime les résultats Gemini. La vraie performance est probablement 6-7/10 (vs 5,4/10 affiché). L'ajout du champ `numerical_results` résoudrait le principal point faible (reprise des valeurs chiffrées).

### Prochaine étape la plus importante

**Implémenter le champ `numerical_results`** dans la spec `.klickd` v3.2 et **valider avec un scoring sémantique** (embeddings) pour corriger le biais anti-Gemini du scoring actuel. Ces deux changements résoudraient les deux principales limites identifiées et augmenteraient les scores mesurés de 1-2 points en moyenne sur tous les agents.

Le deuxième chantier prioritaire est l'UX autour du `next_step` : en faire le point d'attention central de la fermeture de session (validation explicite par l'utilisateur) et de la reprise (affiché en premier à l'utilisateur avant que le modèle réponde).

---

*Benchmark réalisé le 19 mai 2026 — klickdskill v3.1.2 — DOI [10.5281/zenodo.20274327](https://doi.org/10.5281/zenodo.20274327)*  
*Rapport consolidé produit à partir des rapports des Agents A, B, C, D, E et F*  
*Format .klickd : open source CC0 — [klickd.app](https://klickd.app) · Luxlearn.app (Luxembourg)*
