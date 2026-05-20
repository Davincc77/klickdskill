#!/usr/bin/env python3
"""
Runner générique Bloc A — lots 57-66
WITH .klickd vs WITHOUT — scoring 0-50 — llama-3.3-70b-versatile Groq
Usage: python3 run_bloc_a.py <lot_num> <p_start> <p_end>
"""
import json, os, sys, time, requests, re
sys.path.insert(0, os.path.dirname(__file__))
from scorer_v35 import score_response_v35, get_questions_for_profile, resolve_subject, QUESTIONS_V35, SUBJECT_FAMILY_V35

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.3-70b-versatile"
BASE = "/home/user/workspace/benchmark_results"

def call_groq(system_prompt, user_message, max_tokens=800):
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": MODEL, "messages": [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ], "max_tokens": max_tokens, "temperature": 0.3}
    for attempt in range(3):
        try:
            r = requests.post(GROQ_URL, headers=headers, json=payload, timeout=45)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
        except Exception as e:
            if attempt < 2:
                time.sleep(5)
            else:
                raise

def build_with_prompt(profile: dict) -> str:
    payload = profile.get("payload", profile)
    name = payload.get("display_name", "Étudiant")
    lang = payload.get("language", "FR")
    subject = payload.get("knowledge", {}).get("subject", "")
    level = payload.get("knowledge", {}).get("level", "")
    mastery = payload.get("knowledge", {}).get("mastery_score", 0.5)
    struggles = payload.get("knowledge", {}).get("struggles", [])
    goal = payload.get("learning_goal", {}).get("description", "")
    mood = payload.get("mood", "neutral")
    style = payload.get("teaching_mode", ["direct"])
    style_str = style[0] if isinstance(style, list) else style
    resume = payload.get("resume_trigger", "")
    errors = payload.get("error_patterns", struggles[:2])
    prefs = payload.get("user_preferences", "")
    
    prompt = f"""Tu es Kai, assistant pédagogique IA. Profil .klickd chargé :

Élève: {name} | Niveau: {level} | Matière: {subject}
Maîtrise: {mastery*100:.0f}% | Humeur: {mood} | Style: {style_str}
Objectif: {goal}
Points faibles: {', '.join(struggles) if struggles else 'aucun'}
Erreurs récurrentes: {', '.join(errors) if errors else 'aucune'}
Reprise: {resume}
{prefs}

Adapte chaque réponse au niveau, style et humeur de l'élève. Réponds en {lang}."""
    return prompt

def build_without_prompt(profile: dict) -> str:
    payload = profile.get("payload", profile)
    lang = payload.get("language", "FR")
    subject = payload.get("knowledge", {}).get("subject", "")
    return f"Tu es un assistant pédagogique. Réponds en {lang}. Matière : {subject}."

# Questions génériques par matière
# v3.5 scorer — bank étendu, alignment matière > fallback générique
# Règle: si la matière déclarée n'est pas dans ce dict, on cherche un fallback
# par famille (sciences, langues, arts, sciences humaines) avant d'utiliser économie
QUESTIONS = {
    # ── Sciences économiques et sociales ──────────────────────────────────
    "économie": [
        "Explique-moi le mécanisme des taux d'intérêt et leur impact sur l'investissement.",
        "Quelle est la différence entre politique monétaire et politique budgétaire ?",
        "Explique le modèle IS-LM en termes simples.",
        "Qu'est-ce que l'élasticité-prix de la demande ?",
        "Comment fonctionne le marché des changes ?",
    ],
    "ses": [
        "Quelle est la différence entre chômage frictionnel et chômage structurel ?",
        "Explique le mécanisme du multiplicateur keynésien.",
        "Qu'est-ce que la mobilité sociale selon Bourdieu ?",
        "Comment fonctionne la socialisation primaire et secondaire ?",
        "Explique la distinction entre capital économique et capital culturel.",
    ],
    "macroéconomie": [
        "Explique le modèle IS-LM en termes simples.",
        "Quelle est la différence entre politique monétaire et budgétaire ?",
        "Explique la trappe à liquidité de Keynes.",
        "Comment une banque centrale contrôle-t-elle l'inflation ?",
        "Qu'est-ce que la courbe de Phillips ?",
    ],
    "sociologie": [
        "Explique l'anomie selon Durkheim.",
        "Quelle est la différence entre stratification et mobilité sociale ?",
        "Explique le concept de capital social chez Bourdieu.",
        "Qu'est-ce que l'institution sociale ?",
        "Comment Goffman analyse-t-il l'interaction sociale ?",
    ],
    # ── Droit ─────────────────────────────────────────────────────────────
    "droit": [
        "Explique le principe de primauté du droit de l'UE.",
        "Quelle est la différence entre le Conseil de l'UE et le Conseil européen ?",
        "Comment fonctionne la procédure en manquement devant la CJUE ?",
        "Qu'est-ce que l'effet direct d'une directive ?",
        "Explique le mécanisme de codécision.",
    ],
    "droit constitutionnel": [
        "Explique la différence entre loi organique et loi ordinaire.",
        "Qu'est-ce que le bloc de constitutionnalité ?",
        "Comment fonctionne le contrôle de constitutionnalité en France ?",
        "Quelle est la différence entre régime présidentiel et parlementaire ?",
        "Explique le principe de séparation des pouvoirs.",
    ],
    "droit des contrats": [
        "Quelles sont les conditions de formation d'un contrat valide ?",
        "Explique la différence entre nullité absolue et relative.",
        "Qu'est-ce que la force majeure en droit des contrats ?",
        "Comment fonctionne la résolution d'un contrat pour inexécution ?",
        "Explique le principe de la liberté contractuelle et ses limites.",
    ],
    "droit européen": [
        "Explique le principe de primauté du droit de l'UE.",
        "Quelle est la différence entre règlement et directive UE ?",
        "Comment fonctionne la marge d'appréciation nationale en droit CEDH ?",
        "Qu'est-ce que le principe de proportionnalité en droit UE ?",
        "Explique le mécanisme du renvoi préjudiciel.",
    ],
    "science politique": [
        "Quelle est la différence entre régime présidentiel et parlementaire ?",
        "Explique le concept de bipartisme vs multipartisme.",
        "Qu'est-ce que la légitimité politique selon Weber ?",
        "Comment fonctionne le fédéralisme ?",
        "Explique le concept de démocratie délibérative.",
    ],
    # ── Musique et arts ───────────────────────────────────────────────────
    "musique": [
        "Explique la différence entre une gamme majeure et mineure.",
        "Qu'est-ce qu'une cadence parfaite ?",
        "Comment fonctionne la modulation en musique tonale ?",
        "Explique les accords de 7e de dominante.",
        "Qu'est-ce que le contrepoint ?",
    ],
    "théorie musicale": [
        "Explique la différence entre mode ionien et dorien.",
        "Qu'est-ce qu'une harmonisation à 4 voix en style choral ?",
        "Explique la règle de l'octave en harmonie tonale.",
        "Qu'est-ce qu'un accord de sensible ?",
        "Comment fonctionne la modulation au relatif mineur ?",
    ],
    "arts": [
        "Comment analyser la composition d'une peinture ?",
        "Explique les caractéristiques du cubisme.",
        "Quelle est la différence entre impressionnisme et expressionnisme ?",
        "Explique les techniques de la Renaissance.",
        "Qu'est-ce que l'art conceptuel ?",
    ],
    "histoire de l'art": [
        "Quelles sont les caractéristiques du baroque ?",
        "Explique la différence entre Renaissance italienne et nordique.",
        "Qu'est-ce que le romantisme en peinture ?",
        "Comment analyser une œuvre avec la méthode iconographique ?",
        "Explique le mouvement des Impressionnistes.",
    ],
    "cinéma": [
        "Explique la différence entre raccord dans l'axe et faux raccord.",
        "Qu'est-ce qu'un plan séquence ?",
        "Explique la notion de champ/contrechamp.",
        "Quels sont les éléments de la mise en scène ?",
        "Explique la différence entre montage alterné et montage parallèle.",
    ],
    "littérature française": [
        "Quelles sont les caractéristiques du roman réaliste du XIXe siècle ?",
        "Explique la différence entre discours direct et indirect libre.",
        "Qu'est-ce que le romantisme littéraire ?",
        "Comment rédiger un plan dialectique pour une dissertation littéraire ?",
        "Explique le concept d'ironie dramatique.",
    ],
    "théâtre": [
        "Quelle est la différence entre tragédie et comédie classique ?",
        "Explique la règle des trois unités.",
        "Qu'est-ce qu'une didascalie et son rôle ?",
        "Explique le concept de catharsis chez Aristote.",
        "Comment analyser le conflit dramatique dans une pièce ?",
    ],
    # ── Chimie et physique ────────────────────────────────────────────────
    "chemistry": [
        "Explain the SN1 vs SN2 reaction mechanism.",
        "What is an aldol condensation?",
        "Explain stereochemistry and R/S nomenclature.",
        "What are functional groups? Give 3 examples.",
        "Explain nucleophilic substitution with an example.",
    ],
    "chimie organique": [
        "Explique la différence entre substitution SN1 et SN2.",
        "Qu'est-ce qu'une réaction d'addition électrophile sur un alcène ?",
        "Explique la règle de Markovnikov.",
        "Quelle est la différence entre stéréoisomères R et S ?",
        "Explique le mécanisme d'une réaction d'estérification.",
    ],
    "chimie": [
        "Explique la différence entre acide fort et acide faible.",
        "Qu'est-ce qu'une réaction d'oxydoréduction ?",
        "Comment équilibrer une demi-équation rédox ?",
        "Explique la constante d'équilibre Kc.",
        "Qu'est-ce que l'enthalpie de réaction ?",
    ],
    "physique": [
        "Explique la différence entre cinématique et cinétique.",
        "Qu'est-ce que le VO2max et comment l'améliorer ?",
        "Explique les trois filières énergétiques musculaires.",
        "Quelle est la différence entre tendon et ligament ?",
        "Explique le seuil lactique et son importance en entraînement.",
    ],
    "thermodynamique": [
        "Explique le premier principe de la thermodynamique.",
        "Qu'est-ce que l'entropie et le deuxième principe ?",
        "Explique la différence entre processus réversible et irréversible.",
        "Qu'est-ce que l'enthalpie libre G et son signe ?",
        "Comment calculer le travail dans une transformation isochore ?",
    ],
    "mécanique des fluides": [
        "Explique l'équation de Bernoulli.",
        "Quelle est la différence entre pression statique et dynamique ?",
        "Explique le principe de conservation du débit volumique.",
        "Qu'est-ce qu'un fluide parfait vs réel ?",
        "Comment fonctionne un venturi ?",
    ],
    # ── Mathématiques ─────────────────────────────────────────────────────
    "mathématiques": [
        "Explique la différence entre convergence absolue et conditionnelle d'une série.",
        "Qu'est-ce qu'un espace vectoriel ?",
        "Explique le théorème de Lagrange en analyse.",
        "Comment calculer la dérivée d'une fonction composée ?",
        "Qu'est-ce qu'une intégrale impropre ?",
    ],
    "algèbre linéaire": [
        "Explique la différence entre noyau et image d'une application linéaire.",
        "Qu'est-ce qu'une base orthonormée ?",
        "Comment calculer le déterminant d'une matrice 3×3 ?",
        "Explique le théorème du rang.",
        "Qu'est-ce qu'une valeur propre ?",
    ],
    "probabilités": [
        "Explique la différence entre loi binomiale et loi de Poisson.",
        "Qu'est-ce qu'une variable aléatoire continue vs discrète ?",
        "Explique le théorème de Bayes.",
        "Qu'est-ce que l'espérance mathématique ?",
        "Comment calculer la variance d'une somme de variables indépendantes ?",
    ],
    # ── Informatique ──────────────────────────────────────────────────────
    "informatique": [
        "Explique la complexité temporelle O(n log n) vs O(n²).",
        "Quelle est la différence entre BFS et DFS ?",
        "Explique l'algorithme de Dijkstra.",
        "Qu'est-ce que la récursivité ? Donne un exemple.",
        "Comment fonctionne un algorithme de tri rapide ?",
    ],
    "algorithmique": [
        "Explique la différence entre complexité O(n) et O(n²).",
        "Qu'est-ce qu'un algorithme de tri par fusion ?",
        "Explique le principe de diviser pour régner.",
        "Qu'est-ce qu'un arbre binaire de recherche ?",
        "Comment fonctionne la mémoïsation en programmation dynamique ?",
    ],
    "bases de données": [
        "Explique la différence entre JOIN INNER et LEFT OUTER.",
        "Quelle est la différence entre WHERE et HAVING en SQL ?",
        "Explique la normalisation et les formes normales.",
        "Qu'est-ce qu'un index en base de données ?",
        "Explique la différence entre clé primaire et clé étrangère.",
    ],
    "machine learning": [
        "Explique la différence entre régularisation L1 et L2.",
        "Qu'est-ce que le surapprentissage (overfitting) ?",
        "Explique le principe de la rétropropagation.",
        "Quelle est la différence entre classification et régression ?",
        "Explique le principe du gradient descent.",
    ],
    "réseaux": [
        "Explique la différence entre TCP et UDP.",
        "Qu'est-ce que le modèle OSI et ses 7 couches ?",
        "Comment fonctionne le protocole HTTPS ?",
        "Explique la différence entre routage statique et dynamique.",
        "Qu'est-ce qu'une adresse IP et un masque sous-réseau ?",
    ],
    # ── Langues ───────────────────────────────────────────────────────────
    "philosophie": [
        "Explique l'impératif catégorique de Kant.",
        "Quelle est la différence entre éthique déontologique et conséquentialiste ?",
        "Explique le contrat social selon Rousseau.",
        "Qu'est-ce que le nihilisme chez Nietzsche ?",
        "Explique la distinction être/existence chez Heidegger.",
    ],
    "sport": [
        "Explique la différence entre cinématique et cinétique.",
        "Qu'est-ce que le VO2max et comment l'améliorer ?",
        "Explique les trois filières énergétiques musculaires.",
        "Quelle est la différence entre tendon et ligament ?",
        "Explique le seuil lactique et son importance en entraînement.",
    ],
    "deutsch": [
        "Erkläre den Unterschied zwischen Konjunktiv I und Konjunktiv II.",
        "Was ist das Passiv und wann benutzt man es?",
        "Erkläre die vier deutschen Kasus.",
        "Was ist eine Erörterung und wie schreibt man sie?",
        "Erkläre die Unterschiede zwischen Haupt- und Nebensatz.",
    ],
    "english": [
        "What is the difference between present perfect and past simple?",
        "Explain the difference between 'will' and 'going to'.",
        "What are relative clauses and how do you form them?",
        "Explain the difference between countable and uncountable nouns.",
        "What is the passive voice and when is it used?",
    ],
    "espagnol": [
        "Explique la différence entre ser et estar.",
        "Quand utilise-t-on le subjonctif en espagnol ?",
        "Explique la différence entre por et para.",
        "Qu'est-ce que le prétérit indéfini vs imparfait en espagnol ?",
        "Explique les pronoms relatifs que et quien.",
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
    "anatomie": [
        "Explique la différence entre artère et veine.",
        "Quelles sont les principales artères du thorax ?",
        "Explique la structure d'un neurone.",
        "Qu'est-ce que le péristaltisme ?",
        "Explique l'anatomie du cœur et ses 4 cavités.",
    ],
    "biologie cellulaire": [
        "Explique la différence entre mitose et méiose.",
        "Qu'est-ce que la respiration cellulaire ?",
        "Explique la synthèse des protéines (transcription/traduction).",
        "Qu'est-ce que le cycle cellulaire ?",
        "Explique la différence entre cellule procaryote et eucaryote.",
    ],
    "biologie": [
        "Explique la différence entre mitose et méiose.",
        "Qu'est-ce que la photosynthèse ?",
        "Explique le mécanisme de l'évolution darwinienne.",
        "Qu'est-ce qu'un enzyme et son mécanisme d'action ?",
        "Explique la régulation génique.",
    ],
    "genetics": [
        "Explain the difference between dominant and recessive traits.",
        "How does a dihybrid cross work?",
        "What is the 9:3:3:1 phenotype ratio?",
        "Explain incomplete dominance with an example.",
        "What is the difference between genotype and phenotype?",
    ],
    # ── Géographie et histoire ────────────────────────────────────────────
    "géographie": [
        "Explique le concept de métropolisation.",
        "Quels sont les principaux flux de la mondialisation ?",
        "Explique la différence entre IDH et PIB.",
        "Qu'est-ce qu'une firme multinationale ?",
        "Comment expliquer les inégalités Nord/Sud ?",
    ],
    "histoire": [
        "Quelles sont les causes de la Première Guerre mondiale ?",
        "Explique le concept de totalitarisme.",
        "Qu'est-ce que la décolonisation et ses enjeux ?",
        "Explique les causes de la Révolution française.",
        "Qu'est-ce que la Guerre Froide ?",
    ],
}

# Fallback par famille si matière non trouvée
SUBJECT_FAMILY = {
    # sciences
    "physique quantique": "physique",
    "circuits rlc": "physique",
    "mécanique": "physique",
    "électromagnétisme": "physique",
    "chimie organique avancée": "chimie organique",
    "oxydoréduction": "chimie",
    "biochimie": "biologie cellulaire",
    # maths
    "séries numériques": "mathématiques",
    "géométrie": "mathématiques",
    "géométrie analytique": "mathématiques",
    "analyse": "mathématiques",
    "statistiques": "probabilités",
    # info
    "python": "algorithmique",
    "sql": "bases de données",
    "réseau": "réseaux",
    "tcp/ip": "réseaux",
    # langues
    "français langue": "littérature française",
    "français": "littérature française",
    "anglais": "english",
    "allemand": "deutsch",
    "arabe": "philosophie",  # fallback neutre
    # santé
    "médecine ecn": "médecine",
    "pcem": "médecine",
    "bts infirmier": "pharmacologie",
    "svt": "biologie",
    # droit
    "droit international": "droit européen",
    "droit social": "droit des contrats",
    # arts
    "analyse filmique": "cinéma",
    "texte dramatique": "théâtre",
    "dissertation": "littérature française",
    # sciences humaines
    "économie avancée": "macroéconomie",
    "behavioral economics": "macroéconomie",
    "science politique": "science politique",
    "geschicht": "histoire",
    "mathematik": "mathématiques",
}
def run_lot(lot_num: int, p_start: int, p_end: int):
    lot_dir = f"{BASE}/v341_lot{lot_num}"
    results = []
    
    # v3.5 : sujet déterminé per-profil (plus per-lot)
    # On lit le premier profil juste pour l'affichage du log
    subject = None
    for i in range(p_start, p_end + 1):
        path = f"{lot_dir}/profil_{i:02d}.json"
        if os.path.exists(path):
            with open(path) as f:
                profile = json.load(f)
            subj = profile.get("payload", {}).get("knowledge", {}).get("subject", "")
            if subj: subject = subj; break

    print(f"\n{'='*60}")
    print(f"LOT {lot_num} — sujet (P{p_start:02d}): {subject} — scorer v3.5 LLM-judge")
    print(f"{'='*60}")
    
    for i in range(p_start, p_end + 1):
        path = f"{lot_dir}/profil_{i:02d}.json"
        if not os.path.exists(path): continue
        
        with open(path) as f:
            profile = json.load(f)
        
        name = profile.get("payload", {}).get("display_name", f"P{i:02d}")
        print(f"\n  P{i:02d} — {name}")
        
        with_total = 0
        without_total = 0
        probe_results = []
        
        with_prompt = build_with_prompt(profile)
        without_prompt = build_without_prompt(profile)

        # v3.5 : questions per-profil (pas per-lot)
        profile_subject, questions = get_questions_for_profile(profile)
        print(f"    matiere={profile_subject} ({len(questions)} questions)")
        
        for q_idx, question in enumerate(questions[:5]):
            try:
                with_resp = call_groq(with_prompt, question, max_tokens=600)
                time.sleep(1.5)
                without_resp = call_groq(without_prompt, question, max_tokens=600)
                time.sleep(1.5)
                
                ws, wos = score_response_v35(with_resp, without_resp, profile, question)
                with_total += ws
                without_total += wos
                probe_results.append({
                    "q": q_idx + 1,
                    "question": question[:60],
                    "with_score": ws,
                    "without_score": wos,
                    "with_excerpt": with_resp[:150],
                    "without_excerpt": without_resp[:150],
                })
                print(f"    Q{q_idx+1}: WITH={ws}/10 WITHOUT={wos}/10 Δ={ws-wos:+d}")
            except Exception as e:
                print(f"    Q{q_idx+1}: ERROR — {e}")
                probe_results.append({"q": q_idx+1, "error": str(e)})
                time.sleep(5)
        
        result = {
            "profil": f"P{i:02d}",
            "name": name,
            "with_score": with_total,
            "without_score": without_total,
            "delta": with_total - without_total,
            "probes": probe_results,
        }
        results.append(result)
        print(f"  → WITH={with_total}/50 WITHOUT={without_total}/50 Δ={with_total-without_total:+d}")
    
    # Sauvegarder
    out_path = f"{lot_dir}/results_p{p_start:02d}_p{p_end:02d}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"lot": lot_num, "subject": subject, "results": results}, f, ensure_ascii=False, indent=2)
    
    if results:
        avg_with = sum(r["with_score"] for r in results) / len(results)
        avg_without = sum(r["without_score"] for r in results) / len(results)
        print(f"\n  LOT {lot_num} P{p_start}-P{p_end}: WITH={avg_with:.1f} WITHOUT={avg_without:.1f} Δ={avg_with-avg_without:+.1f}")
    
    print(f"  ✅ {out_path}")
    return results

if __name__ == "__main__":
    lot_num = int(sys.argv[1])
    p_start = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    p_end = int(sys.argv[3]) if len(sys.argv) > 3 else 5
    run_lot(lot_num, p_start, p_end)
