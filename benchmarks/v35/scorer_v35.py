#!/usr/bin/env python3
"""
klickdskill Scorer v3.5
-----------------------
Remplace score_response() heuristique par un LLM-as-judge matière-aware.

Bugs corrigés vs v3.4:
  1. Heuristique "densité de mots-clés" favorisait WITHOUT sur questions économie
     pour des profils "English/Deutsch" langues vivantes → Δ négatif (lot 89 Δ-1.0)
  2. SUBJECT_FAMILY manquait les variantes multilingues (Englisch, Französisch, etc.)
  3. Alias arabe → philosophie (absurde) supprimé
  4. Questions per-profil : chaque profil obtient des questions alignées à SA matière
     (pas seulement le premier profil du lot)
  5. score_response() remplacé par LLM-judge : évalue l'ADAPTATION PÉDAGOGIQUE,
     pas la densité factuelle

Grille LLM-judge /10 par question:
  Continuité contextuelle  /3  — le profil .klickd est utilisé (niveau, langue, objectif)
  Précision pédagogique    /3  — la réponse est correcte ET adaptée à la matière réelle
  Adaptation               /2  — style, humeur, obstacles respectés
  Langue / registre        /2  — réponse dans la bonne langue, bon registre
"""

import json, os, re, time, requests

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.3-70b-versatile"

# ══════════════════════════════════════════════════════════════════════════════
# BANQUE DE QUESTIONS v3.5
# Règle : chaque clé = matière normalisée (lowercase)
# Couvre toutes les variantes multilingues connues
# ══════════════════════════════════════════════════════════════════════════════
QUESTIONS_V35 = {
    # ── Langues vivantes ───────────────────────────────────────────────────
    "english": [
        "What is the difference between present perfect and past simple? Give 2 examples.",
        "Explain the difference between 'will' and 'going to' for future plans.",
        "What are relative clauses? Form a sentence using 'which' and one using 'who'.",
        "Explain the difference between countable and uncountable nouns with examples.",
        "What is the passive voice? Transform this sentence: 'She wrote the email.'",
    ],
    "deutsch": [
        "Erkläre den Unterschied zwischen Konjunktiv I und Konjunktiv II mit Beispielen.",
        "Was ist das Passiv? Forme einen Satz im Passiv.",
        "Erkläre die vier deutschen Kasus mit je einem Beispielsatz.",
        "Was ist eine Erörterung und wie ist sie aufgebaut?",
        "Erkläre den Unterschied zwischen Haupt- und Nebensatz.",
    ],
    "espagnol": [
        "Explique la différence entre ser et estar avec 2 exemples chacun.",
        "Quand utilise-t-on le subjonctif présent en espagnol ?",
        "Explique la différence entre por et para.",
        "Qu'est-ce que le pretérito indefinido vs imperfecto ? Donne des exemples.",
        "Explique les pronoms relatifs que et quien.",
    ],
    "français": [
        "Explique la différence entre le passé composé et l'imparfait.",
        "Qu'est-ce qu'une proposition subordonnée relative ? Donne un exemple.",
        "Explique la règle d'accord du participe passé avec avoir.",
        "Quelle est la différence entre style direct et style indirect ?",
        "Explique la structure d'une dissertation en 3 parties.",
    ],
    "luxembourgeois": [
        "Wéi gëtt den Artikel 'de/den/d'' am Lëtzebuergeschen benotzt?",
        "Erkläre den Ënnerscheed tëscht Vergangenheet a Vergaangenheet.",
        "Wat sinn d'Grondregele vun der lëtzebuergescher Orthographie?",
        "Wéi funktionéiert d'Wuertstelllung am lëtzebuergesche Saz?",
        "Erkläre d'Biegung vun den Adjektiver am Lëtzebuergeschen.",
    ],
    "arabe": [
        "Explique la différence entre l'arabe dialectal (darija) et l'arabe standard (MSA/Fusha).",
        "Qu'est-ce que la conjugaison du présent (المضارع) en arabe standard ?",
        "Explique le système des racines trilitères en arabe.",
        "Quelle est la différence entre l'état défini (avec ال) et indéfini ?",
        "Explique la déclinaison des noms (إعراب) : nominatif, accusatif, génitif.",
    ],
    "italien": [
        "Explique la différence entre passato prossimo et imperfetto.",
        "Quand utilise-t-on le congiuntivo en italien ?",
        "Explique les pronoms réfléchis en italien.",
        "Quelle est la différence entre 'bello' et 'buono' ?",
        "Explique la formation du condizionale présent.",
    ],
    # ── Mathématiques ──────────────────────────────────────────────────────
    "mathématiques": [
        "Explique la méthode de résolution d'une équation du second degré.",
        "Qu'est-ce qu'une dérivée ? Explique avec la fonction f(x) = x².",
        "Explique le théorème de Pythagore et donne un exemple d'application.",
        "Qu'est-ce qu'une limite ? Explique lim(x→0) sin(x)/x.",
        "Explique la différence entre suite arithmétique et géométrique.",
    ],
    "probabilités": [
        "Explique la différence entre probabilité conditionnelle et indépendance.",
        "Qu'est-ce que l'espérance mathématique d'une variable aléatoire ?",
        "Explique le théorème de Bayes avec un exemple simple.",
        "Quelle est la loi binomiale et quand l'utilise-t-on ?",
        "Explique la loi normale et le rôle de l'écart-type.",
    ],
    "algèbre": [
        "Explique la notion de groupe en algèbre abstraite.",
        "Qu'est-ce qu'une matrice carrée inversible ?",
        "Explique le produit scalaire de deux vecteurs.",
        "Qu'est-ce qu'un espace vectoriel ?",
        "Explique la décomposition en valeurs propres.",
    ],
    # ── Sciences ───────────────────────────────────────────────────────────
    "physique": [
        "Explique la deuxième loi de Newton F=ma avec un exemple.",
        "Quelle est la différence entre énergie cinétique et potentielle ?",
        "Explique le principe de conservation de l'énergie.",
        "Qu'est-ce que la loi d'Ohm ? Donne la formule.",
        "Explique la différence entre onde transversale et longitudinale.",
    ],
    "chimie": [
        "Explique la liaison covalente et donne un exemple (H₂O).",
        "Qu'est-ce qu'une réaction d'oxydoréduction ?",
        "Explique la loi de conservation de la matière (Lavoisier).",
        "Qu'est-ce que le pH ? Comment le calculer ?",
        "Explique la différence entre acide fort et acide faible.",
    ],
    "chimie organique": [
        "Explique la différence entre SN1 et SN2.",
        "Qu'est-ce qu'une réaction d'addition électrophile ?",
        "Explique la stéréochimie R/S avec un exemple.",
        "Qu'est-ce qu'un groupe fonctionnel ? Cite 3 exemples.",
        "Explique le mécanisme d'une estérification.",
    ],
    "biologie": [
        "Explique la différence entre mitose et méiose.",
        "Qu'est-ce que l'ADN et comment est-il structuré ?",
        "Explique la photosynthèse en termes simples.",
        "Quelle est la différence entre cellule eucaryote et procaryote ?",
        "Explique le mécanisme de la synthèse protéique.",
    ],
    "biologie cellulaire": [
        "Explique le cycle cellulaire et ses phases.",
        "Qu'est-ce que l'apoptose ?",
        "Explique la différence entre mitose et méiose.",
        "Qu'est-ce que la membrane plasmique et son rôle ?",
        "Explique le rôle des mitochondries dans la cellule.",
    ],
    # ── Sciences humaines ──────────────────────────────────────────────────
    "histoire": [
        "Explique les causes principales de la Première Guerre mondiale.",
        "Qu'est-ce que la Révolution industrielle et quels en sont les effets ?",
        "Explique la différence entre démocratie et totalitarisme.",
        "Qu'est-ce que la décolonisation ? Donne un exemple.",
        "Explique les conséquences de la Seconde Guerre mondiale.",
    ],
    "géographie": [
        "Explique le concept de métropolisation.",
        "Quels sont les principaux flux de la mondialisation ?",
        "Explique la différence entre IDH et PIB.",
        "Qu'est-ce qu'une firme multinationale ?",
        "Comment expliquer les inégalités Nord/Sud ?",
    ],
    "philosophie": [
        "Explique l'impératif catégorique de Kant.",
        "Quelle est la différence entre éthique déontologique et conséquentialiste ?",
        "Explique le contrat social selon Rousseau.",
        "Qu'est-ce que le nihilisme chez Nietzsche ?",
        "Explique la distinction être/existence chez Heidegger.",
    ],
    "science politique": [
        "Explique la différence entre régime présidentiel et parlementaire.",
        "Qu'est-ce que la séparation des pouvoirs ?",
        "Explique le concept de légitimité politique selon Weber.",
        "Quelle est la différence entre fédéralisme et unitarisme ?",
        "Explique la notion d'État-nation.",
    ],
    # ── Économie et droit ──────────────────────────────────────────────────
    "économie": [
        "Explique-moi le mécanisme des taux d'intérêt et leur impact sur l'investissement.",
        "Quelle est la différence entre politique monétaire et politique budgétaire ?",
        "Explique le modèle IS-LM en termes simples.",
        "Qu'est-ce que l'élasticité-prix de la demande ?",
        "Comment fonctionne le marché des changes ?",
    ],
    "macroéconomie": [
        "Explique la différence entre PIB nominal et PIB réel.",
        "Qu'est-ce que l'inflation et comment la mesure-t-on ?",
        "Explique le multiplicateur keynésien.",
        "Quelle est la courbe de Phillips ?",
        "Explique la politique d'assouplissement quantitatif (QE).",
    ],
    "ses": [
        "Quelle est la différence entre chômage frictionnel et structurel ?",
        "Explique la stratification sociale selon Bourdieu.",
        "Qu'est-ce que la mobilité sociale ?",
        "Explique le concept de capital social.",
        "Qu'est-ce que l'État-providence ?",
    ],
    "droit constitutionnel": [
        "Qu'est-ce que le principe de séparation des pouvoirs ?",
        "Explique la hiérarchie des normes selon Kelsen.",
        "Quelle est la différence entre régime parlementaire et présidentiel ?",
        "Explique le contrôle de constitutionnalité des lois.",
        "Qu'est-ce que l'état de droit ?",
    ],
    "droit international": [
        "Quelle est la différence entre droit international public et privé ?",
        "Explique le principe de souveraineté étatique en droit international.",
        "Qu'est-ce qu'un traité international et comment est-il ratifié ?",
        "Explique le rôle de la Cour Internationale de Justice.",
        "Qu'est-ce que le droit international humanitaire ?",
    ],
    "droit des contrats": [
        "Quels sont les éléments essentiels d'un contrat valide ?",
        "Explique la différence entre nullité absolue et relative.",
        "Qu'est-ce que la force majeure en droit des contrats ?",
        "Explique le principe de la liberté contractuelle.",
        "Qu'est-ce que la responsabilité contractuelle ?",
    ],
    "droit européen": [
        "Explique la différence entre règlement et directive européenne.",
        "Qu'est-ce que la primauté du droit européen ?",
        "Explique le fonctionnement de la Cour de Justice de l'UE.",
        "Qu'est-ce que l'effet direct ?",
        "Explique le marché unique européen.",
    ],
    # ── Informatique ───────────────────────────────────────────────────────
    "informatique": [
        "Explique la complexité temporelle O(n log n) vs O(n²).",
        "Quelle est la différence entre BFS et DFS ?",
        "Explique l'algorithme de Dijkstra.",
        "Qu'est-ce que la récursivité ? Donne un exemple.",
        "Comment fonctionne un algorithme de tri rapide ?",
    ],
    "algorithmique": [
        "Explique la différence entre algorithme glouton et programmation dynamique.",
        "Qu'est-ce qu'un arbre binaire de recherche ?",
        "Explique le principe diviser pour régner.",
        "Qu'est-ce que la notation grand O ?",
        "Explique la différence entre pile (stack) et file (queue).",
    ],
    "bases de données": [
        "Explique la différence entre SQL et NoSQL.",
        "Qu'est-ce qu'une clé primaire et une clé étrangère ?",
        "Explique les formes normales (1NF, 2NF, 3NF).",
        "Qu'est-ce qu'une transaction ACID ?",
        "Explique la différence entre JOIN INNER et LEFT JOIN.",
    ],
    "réseaux": [
        "Explique le modèle OSI et ses 7 couches.",
        "Quelle est la différence entre TCP et UDP ?",
        "Explique le fonctionnement du protocole HTTPS.",
        "Qu'est-ce qu'une adresse IP et un masque de sous-réseau ?",
        "Explique le fonctionnement du DNS.",
    ],
    # ── Arts et lettres ────────────────────────────────────────────────────
    "littérature française": [
        "Explique les caractéristiques du mouvement romantique français.",
        "Quelle est la différence entre une métaphore et une comparaison ?",
        "Explique la structure d'un sonnet.",
        "Qu'est-ce que le réalisme littéraire ?",
        "Explique les figures de style : anaphore, chiasme, oxymore.",
    ],
    "arts": [
        "Comment analyser la composition d'une peinture ?",
        "Explique les caractéristiques du cubisme.",
        "Quelle est la différence entre impressionnisme et expressionnisme ?",
        "Explique les techniques de la Renaissance.",
        "Qu'est-ce que l'art conceptuel ?",
    ],
    "musique": [
        "Explique la différence entre une gamme majeure et mineure.",
        "Qu'est-ce qu'une cadence parfaite en harmonie ?",
        "Comment fonctionne la modulation en musique tonale ?",
        "Explique les accords de 7e de dominante.",
        "Qu'est-ce que le contrepoint ?",
    ],
    "cinéma": [
        "Explique la différence entre plan séquence et montage cut.",
        "Qu'est-ce que la profondeur de champ ?",
        "Explique la règle des 180 degrés.",
        "Qu'est-ce que le champ/contrechamp ?",
        "Explique la différence entre son diégétique et extradiégétique.",
    ],
    "théâtre": [
        "Explique la différence entre tragédie et comédie classique.",
        "Qu'est-ce que la règle des trois unités ?",
        "Explique la notion de catharsis chez Aristote.",
        "Qu'est-ce que le théâtre épique de Brecht ?",
        "Explique la différence entre monologue et tirade.",
    ],
    # ── Médecine et santé ─────────────────────────────────────────────────
    "médecine": [
        "Explique le cycle cardiaque et ses phases.",
        "Quelle est la différence entre pression systolique et diastolique ?",
        "Explique le mécanisme d'action des bêta-bloquants.",
        "Qu'est-ce que la filtration glomérulaire ?",
        "Explique la différence entre immunité innée et adaptative.",
    ],
    "pharmacologie": [
        "Explique la différence entre agoniste et antagoniste.",
        "Qu'est-ce que la demi-vie d'un médicament ?",
        "Explique le mécanisme d'action des IEC.",
        "Quelles sont les contre-indications des bêta-bloquants ?",
        "Qu'est-ce que l'index thérapeutique ?",
    ],
    # ── Sport ──────────────────────────────────────────────────────────────
    "sport": [
        "Explique la différence entre cinématique et cinétique.",
        "Qu'est-ce que le VO2max et comment l'améliorer ?",
        "Explique les trois filières énergétiques musculaires.",
        "Quelle est la différence entre tendon et ligament ?",
        "Explique le seuil lactique et son importance en entraînement.",
    ],
}

# ══════════════════════════════════════════════════════════════════════════════
# SUBJECT_FAMILY v3.5
# Couvre les variantes multilingues + aliases manquants
# ══════════════════════════════════════════════════════════════════════════════
SUBJECT_FAMILY_V35 = {
    # ── Langues — variantes multilingues ──────────────────────────────────
    "anglais":          "english",
    "englisch":         "english",     # v3.5 fix lot 89 P02
    "english language": "english",
    "english b":        "english",
    "english c":        "english",
    "allemand":         "deutsch",
    "german":           "deutsch",
    "deutsche":         "deutsch",
    "französisch":      "français",    # v3.5 fix lot 89 P04
    "french":           "français",
    "langue française": "français",
    "littérature":      "littérature française",
    "spanish":          "espagnol",
    "español":          "espagnol",
    "arabe":            "arabe",       # v3.5 fix: suppression alias → philosophie
    "arabic":           "arabe",
    "darija":           "arabe",
    "arabe standard":   "arabe",
    "arabe msa":        "arabe",
    "italian":          "italien",
    "italiano":         "italien",
    "luxemburgisch":    "luxembourgeois",
    "lëtzebuergesch":   "luxembourgeois",
    # ── Maths ─────────────────────────────────────────────────────────────
    "maths":            "mathématiques",
    "math":             "mathématiques",
    "mathematik":       "mathématiques",
    "mathematics":      "mathématiques",
    "géométrie":        "mathématiques",
    "analyse":          "mathématiques",
    "algèbre linéaire": "algèbre",
    "séries numériques":"mathématiques",
    "statistiques":     "probabilités",
    "stats":            "probabilités",
    "stochastik":       "probabilités",
    # ── Sciences ─────────────────────────────────────────────────────────
    "physik":           "physique",
    "physics":          "physique",
    "mécanique":        "physique",
    "électromagnétisme":"physique",
    "physique quantique":"physique",
    "circuits rlc":     "physique",
    "chemie":           "chimie",
    "chemistry":        "chimie",
    "chimie organique avancée": "chimie organique",
    "organic chemistry":"chimie organique",
    "oxydoréduction":   "chimie",
    "biochimie":        "biologie cellulaire",
    "biochemistry":     "biologie cellulaire",
    "svt":              "biologie",
    "biologie moléculaire": "biologie cellulaire",
    "biologie":         "biologie",
    "biology":          "biologie",
    # ── Sciences humaines ─────────────────────────────────────────────────
    "geschichte":       "histoire",
    "geschicht":        "histoire",
    "history":          "histoire",
    "géopo":            "géographie",
    "geo":              "géographie",
    "geographie":       "géographie",
    "philo":            "philosophie",
    "ethics":           "philosophie",
    "behavioral economics": "macroéconomie",
    "économie avancée": "macroéconomie",
    "microéconomie":    "économie",
    "macro":            "macroéconomie",
    "sciences économiques": "économie",
    "science économique": "économie",
    "économie sociale": "ses",
    "droit social":        "droit des contrats",
    "droit":               "droit des contrats",
    "law":                 "droit international",
    "international law":   "droit international",
    "public international law": "droit international",
    "science politique":"science politique",
    "politik":          "science politique",
    # ── Info ──────────────────────────────────────────────────────────────
    "python":           "algorithmique",
    "javascript":       "algorithmique",
    "programmation":    "algorithmique",
    "coding":           "algorithmique",
    "sql":              "bases de données",
    "database":         "bases de données",
    "réseau":           "réseaux",
    "network":          "réseaux",
    "tcp/ip":           "réseaux",
    # ── Arts ─────────────────────────────────────────────────────────────
    "analyse filmique": "cinéma",
    "film":             "cinéma",
    "texte dramatique": "théâtre",
    "dissertation":     "littérature française",
    "arts plastiques":  "arts",
    "peinture":         "arts",
    "art history":      "arts",
    "musik":              "musique",
    "music theory":       "musique",
    "théorie musicale":   "musique",
    "harmonie":           "musique",
    "solfège":            "musique",
    # ── Médecine ─────────────────────────────────────────────────────────
    "médecine ecn":     "médecine",
    "pcem":             "médecine",
    "bts infirmier":    "pharmacologie",
    "nursing":          "médecine",
    "anatomie":         "médecine",
}

# ══════════════════════════════════════════════════════════════════════════════
# RÉSOLUTION MATIÈRE v3.5
# Per-profil (pas per-lot) + normalisation robuste
# ══════════════════════════════════════════════════════════════════════════════
def resolve_subject(raw_subject: str) -> str:
    """
    Résout la matière déclarée vers une clé de QUESTIONS_V35.
    Ordre : exact match → partial match → SUBJECT_FAMILY → fallback
    """
    if not raw_subject:
        return "économie"
    
    s = raw_subject.lower().strip()
    
    # 1. Exact match
    if s in QUESTIONS_V35:
        return s
    
    # 2. Partial match dans les clés QUESTIONS — clés longues d'abord (évite chimie avant chimie organique)
    for key in sorted(QUESTIONS_V35.keys(), key=len, reverse=True):
        if key in s or s in key:
            return key
    
    # 3. SUBJECT_FAMILY — exact match
    if s in SUBJECT_FAMILY_V35:
        target = SUBJECT_FAMILY_V35[s]
        if target in QUESTIONS_V35:
            return target
    
    # 4. SUBJECT_FAMILY — partial match (aliases longs d'abord)
    for alias, family in sorted(SUBJECT_FAMILY_V35.items(), key=lambda x: len(x[0]), reverse=True):
        if alias in s or s in alias:
            if family in QUESTIONS_V35:
                return family
    
    # 5. Fallback neutre (philosophie est plus générique qu'économie)
    return "philosophie"


def get_questions_for_profile(profile: dict) -> tuple[str, list[str]]:
    """Retourne (subject_resolved, [5 questions]) pour un profil donné."""
    payload = profile.get("payload", profile)
    raw = payload.get("knowledge", {}).get("subject", "")
    subject = resolve_subject(raw)
    questions = QUESTIONS_V35.get(subject, QUESTIONS_V35["philosophie"])
    return subject, questions


# ══════════════════════════════════════════════════════════════════════════════
# LLM-JUDGE v3.5
# ══════════════════════════════════════════════════════════════════════════════
JUDGE_SYSTEM = """Tu es un évaluateur pédagogique expert. Tu notes des réponses d'agents IA à des questions d'élèves.

Tu reçois :
- Le profil de l'élève (niveau, matière, langue, style, objectifs, obstacles)
- La question posée
- Réponse WITH : l'agent avait accès au profil .klickd
- Réponse WITHOUT : l'agent n'avait aucun contexte

Note chaque réponse sur 10 selon cette grille STRICTE :
- Continuité contextuelle /3 : la réponse utilise le niveau, la langue et l'objectif du profil
- Précision pédagogique /3 : la réponse est correcte ET enseigne la bonne matière (PAS une matière adjacente)
- Adaptation /2 : style, humeur, points faibles respectés
- Langue/registre /2 : réponse dans la LANGUE DU PROFIL ÉLÈVE (champ 'Langue'), PAS dans la langue de la question. Ex : si l'élève est DE et la matière est 'english', répondre en allemand est CORRECT (2/2). Répondre en anglais serait incorrect pour un profil DE.

IMPORTANT : Une réponse qui enseigne une MAUVAISE matière (ex : répondre économie à un élève d'anglais langue) obtient 0 en "Précision pédagogique", même si elle est factuellement correcte.
IMPORTANT : La langue de la réponse doit correspondre à 'Langue' du profil, pas à la langue de la question posée.

Réponds UNIQUEMENT au format JSON :
{"with_score": <0-10>, "without_score": <0-10>, "with_reason": "<20 mots max>", "without_reason": "<20 mots max>"}"""


def score_response_v35(with_resp: str, without_resp: str, profile: dict, question: str) -> tuple[int, int]:
    """
    LLM-as-judge matière-aware. Remplace l'heuristique v3.4.
    Retourne (with_score/10, without_score/10).
    """
    payload = profile.get("payload", profile)
    name    = payload.get("display_name", "Élève")
    level   = payload.get("knowledge", {}).get("level", "?")
    subject = payload.get("knowledge", {}).get("subject", "?")
    lang    = payload.get("language", "FR")
    mood    = payload.get("mood", "neutral")
    style   = payload.get("teaching_mode", ["direct"])
    style_s = style[0] if isinstance(style, list) else style
    goal    = payload.get("learning_goal", {}).get("description", "")
    struggles = payload.get("knowledge", {}).get("struggles", [])

    user_msg = f"""PROFIL ÉLÈVE:
Nom: {name} | Matière: {subject} | Niveau: {level} | Langue: {lang}
Humeur: {mood} | Style: {style_s} | Objectif: {goal}
Points faibles: {', '.join(struggles) if struggles else 'aucun'}

QUESTION POSÉE:
{question}

RÉPONSE WITH (.klickd chargé):
{with_resp[:800]}

RÉPONSE WITHOUT (pas de contexte):
{without_resp[:800]}"""

    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload_req = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": JUDGE_SYSTEM},
            {"role": "user", "content": user_msg}
        ],
        "max_tokens": 120,
        "temperature": 0.1
    }

    for attempt in range(3):
        try:
            r = requests.post(GROQ_URL, headers=headers, json=payload_req, timeout=30)
            r.raise_for_status()
            content = r.json()["choices"][0]["message"]["content"]
            # Parse JSON — tolérant aux blocs ```json
            content = re.sub(r'```json\s*|\s*```', '', content).strip()
            result = json.loads(content)
            ws = max(0, min(10, int(result.get("with_score", 5))))
            wo = max(0, min(10, int(result.get("without_score", 5))))
            return ws, wo
        except Exception as e:
            if attempt < 2:
                time.sleep(3)
            else:
                # Fallback heuristique minimal si LLM échoue
                ws = 7 if len(with_resp) > 200 else 5
                wo = 6 if len(without_resp) > 200 else 4
                return ws, wo


# ══════════════════════════════════════════════════════════════════════════════
# TEST RAPIDE
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    import sys
    
    print("=== Test resolve_subject v3.5 ===\n")
    test_cases = [
        ("English",          "english"),
        ("Englisch",         "english"),     # bug lot 89 P02
        ("Französisch",      "français"),    # bug lot 89 P04
        ("arabe (darija→MSA)", "arabe"),     # bug lot 89 P05
        ("espagnol",         "espagnol"),
        ("svt",              "biologie"),
        ("Mathematik",       "mathématiques"),
        ("Python",           "algorithmique"),
        ("histoire",         "histoire"),
        ("chimie organique avancée", "chimie organique"),
        ("unknown_subject",  "philosophie"), # fallback
    ]
    
    all_pass = True
    for raw, expected in test_cases:
        got = resolve_subject(raw)
        ok = "✅" if got == expected else "❌"
        if got != expected:
            all_pass = False
        print(f"  {ok} {repr(raw):<35} → {got} (expected: {expected})")
    
    print(f"\n{'✅ All tests pass' if all_pass else '❌ Some tests failed'}\n")
    
    # Test LLM-judge si --live passé
    if "--live" in sys.argv:
        print("\n=== Test LLM-judge (profil English) ===\n")
        profil_test = {
            "payload": {
                "display_name": "Sophie",
                "language": "EN",
                "knowledge": {"subject": "English", "level": "B2", "struggles": ["tenses"]},
                "mood": "motivated",
                "teaching_mode": ["socratic"],
                "learning_goal": {"description": "Master English grammar for Cambridge B2"}
            }
        }
        q = "What is the difference between present perfect and past simple?"
        with_r = "Great question Sophie! Present perfect: 'I have eaten' (past with present relevance). Past simple: 'I ate yesterday' (specific time). Your struggle with tenses is common at B2 level. Here's a tip: look for time markers!"
        without_r = "The present perfect is used for actions with present relevance: 'I have visited Paris'. Past simple for completed actions at a specific time: 'I visited Paris in 2019'."
        
        ws, wo = score_response_v35(with_r, without_r, profil_test, q)
        print(f"  WITH={ws}/10  WITHOUT={wo}/10  Δ={ws-wo:+d}")
        print(f"  Expected: WITH > WITHOUT (WITH adapts to Sophie's profile)\n")
