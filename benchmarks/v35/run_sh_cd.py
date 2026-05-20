#!/usr/bin/env python3
"""
Runner Soul Handoff Cross-LLM — Lots SH-C et SH-D
Protocole : Agent A génère un soul handoff → Agent B (autre modèle) reçoit le handoff
Test : Agent B WITH handoff vs Agent B WITHOUT handoff

SH-C : Agent A = llama-3.3-70b-versatile → Agent B = llama-3.1-8b-instant (modèle différent)
SH-D : Agent A = llama-3.3-70b-versatile → Agent B = llama-3.3-70b-versatile (même modèle)
       Mais avec handoffs DÉGRADÉS (incomplets / erronés / verbeux / language switch / integrity_warning)

Grille /50 :
  Continuité  /15 — Agent B WITH référence le contexte passé (session, erreurs, milestones)
  Précision   /15 — Contenu pédagogique correct
  Adaptation  /10 — Respecte disability, mood, hard_limit, teaching_mode
  Émotionnel  /10 — Ton adapté au mood déclaré

Usage:
  python3 run_sh_cd.py shc          → lot SH-C complet (5 profils)
  python3 run_sh_cd.py shd          → lot SH-D complet (5 profils)
  python3 run_sh_cd.py shc 1 3      → SH-C profils P01-P03
"""
import json, os, sys, time, requests, re

GROQ_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# Modèles
AGENT_A_MODEL = "llama-3.3-70b-versatile"   # génère le soul handoff
AGENT_B_SHC   = "llama-3.1-8b-instant"      # reçoit le handoff — modèle plus petit
AGENT_B_SHD   = "llama-3.3-70b-versatile"   # reçoit le handoff — même modèle mais handoff dégradé

BASE = "/home/user/workspace/benchmark_results"
DELAY = 4


def call_groq(model: str, system: str, user: str, max_tokens: int = 700) -> str:
    headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "max_tokens": max_tokens,
        "temperature": 0.3,
    }
    for attempt in range(3):
        try:
            r = requests.post(GROQ_URL, headers=headers, json=data, timeout=60)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
        except Exception as e:
            if attempt < 2:
                print(f"    ⚠️  Retry {attempt+1} ({e})")
                time.sleep(8)
            else:
                raise


def generate_soul_handoff(profile: dict) -> str:
    """Agent A génère le soul handoff à partir du profil .klickd"""
    payload = profile.get("payload", {})
    name = payload.get("display_name", "Élève")
    lang = payload.get("language", "FR")
    subject = payload.get("knowledge", {}).get("subject", "")
    level = payload.get("knowledge", {}).get("level", "")
    mastery = payload.get("knowledge", {}).get("mastery_score", 0.5)
    struggles = payload.get("knowledge", {}).get("struggles", [])
    resume = payload.get("knowledge", {}).get("resume_trigger", "")
    mood = payload.get("mood", "neutral")
    disabilities = payload.get("known_disabilities", {})
    dis_list = [k for k, v in disabilities.items() if v]
    milestones = payload.get("milestones", [])
    hard_limit = payload.get("hard_limit", "")
    teaching_mode = payload.get("teaching_mode", ["direct"])
    compression = payload.get("compression_policy", {})
    comp_mode = compression.get("mode", "standard")
    comp_keep = compression.get("keep", [])
    last_error = payload.get("last_error_pattern", "")

    # Vérifier si SH-D avec handoff dégradé pré-écrit
    if "degraded_handoff" in profile:
        return profile["degraded_handoff"]

    # Agent A system prompt
    agent_a_system = f"""Tu es Kai, assistant pédagogique IA. Tu viens de terminer une session avec {name}.
Tu dois générer un Soul Handoff compact pour le prochain agent qui va reprendre la session.

Profil .klickd :
- Matière : {subject} ({level})
- Maîtrise : {mastery*100:.0f}%
- Erreurs récurrentes : {', '.join(struggles) if struggles else 'aucune'}
- Resume trigger : {resume}
- Mood actuel : {mood}
- Disabilities : {', '.join(dis_list) if dis_list else 'aucune'}
- Milestones : {', '.join(milestones) if milestones else 'aucun'}
- Hard limit : {hard_limit if hard_limit else 'aucune'}
- Mode pédagogique : {teaching_mode[0] if teaching_mode else 'direct'}
- Dernière erreur : {last_error if last_error else 'N/A'}

Compression policy : {comp_mode}{' — garder : ' + ', '.join(comp_keep) if comp_keep else ''}

Génère un Soul Handoff compact selon le format .klickd §28.8 :
resume: [1 phrase] / errors: [erreur principale] / mood: [mood] / achieved: [true/false] / integrity_warning: [true/false] / disability: [ou 'none'] / hard_limit: [ou omis] / mode: [mode] / milestones: [liste courte]

Respecte la compression_policy — mode aggressive = max 200 chars total."""

    agent_a_user = f"Génère le Soul Handoff pour {name} — session {subject}."
    
    handoff = call_groq(AGENT_A_MODEL, agent_a_system, agent_a_user, max_tokens=300)
    time.sleep(DELAY)
    return handoff


def build_agent_b_system(profile: dict, handoff: str | None, lot: str) -> str:
    """Construit le system prompt Agent B — WITH ou WITHOUT handoff"""
    payload = profile.get("payload", {})
    name = payload.get("display_name", "Élève")
    lang = payload.get("language", "FR")
    subject = payload.get("knowledge", {}).get("subject", "")
    level = payload.get("knowledge", {}).get("level", "")
    disabilities = payload.get("known_disabilities", {})
    dis_list = [k for k, v in disabilities.items() if v]
    mood = payload.get("mood", "neutral")
    hard_limit = payload.get("hard_limit", "")
    teaching_mode = payload.get("teaching_mode", ["direct"])
    style = teaching_mode[0] if isinstance(teaching_mode, list) else teaching_mode

    if handoff:
        # WITH handoff — Agent B reçoit le contexte complet
        base = f"""Tu es Kai, assistant pédagogique IA. Tu prends en charge la session de {name}.

SOUL HANDOFF REÇU :
{handoff}

Tu dois reprendre exactement là où la session précédente s'est arrêtée. Adapte-toi au mood, aux erreurs connues et aux milestones déjà acquis.
{"Hard limit : " + hard_limit if hard_limit else ""}
Disabilities : {', '.join(dis_list) if dis_list else 'aucune'}
Mode pédagogique : {style}
Langue : {lang}

Réponds en {lang}."""
    else:
        # WITHOUT handoff — Agent B commence de zéro
        base = f"""Tu es Kai, assistant pédagogique IA. Un élève vient te demander de l'aide.
Matière : {subject} ({level})
Langue : {lang}

Réponds en {lang}."""

    return base


def score_response_sh(with_resp: str, without_resp: str, profile: dict, handoff: str, lot: str) -> dict:
    """Scoring SH : même grille que SH-A/B — Continuité/Précision/Adaptation/Émotionnel"""
    payload = profile.get("payload", {})
    name = payload.get("display_name", "Élève")
    lang = payload.get("language", "FR")
    subject = payload.get("knowledge", {}).get("subject", "").lower()
    struggles = [s.lower() for s in payload.get("knowledge", {}).get("struggles", [])]
    milestones = [m.lower() for m in payload.get("milestones", [])]
    mood = payload.get("mood", "neutral").lower()
    disabilities = payload.get("known_disabilities", {})
    dis_list = [k for k, v in disabilities.items() if v]
    hard_limit = payload.get("hard_limit", "")
    teaching_mode = payload.get("teaching_mode", ["direct"])
    style = (teaching_mode[0] if isinstance(teaching_mode, list) else teaching_mode).lower()
    last_error = payload.get("last_error_pattern", "").lower()
    resume = payload.get("knowledge", {}).get("resume_trigger", "").lower()
    handoff_lower = handoff.lower() if handoff else ""

    def score_one(resp: str, with_handoff: bool) -> dict:
        r = resp.lower()
        scores = {}

        # --- CONTINUITÉ /15 ---
        cont = 0
        if with_handoff and handoff:
            # Référence session passée (resume_trigger keywords)
            resume_words = [w for w in resume.split() if len(w) > 3]
            ref_session = sum(1 for w in resume_words if w in r)
            cont += min(ref_session * 3, 6)
            # Erreurs connues mentionnées
            if last_error and any(w in r for w in last_error.split()[:4] if len(w) > 3):
                cont += 5
            # Milestones acquis référencés
            milestone_hits = sum(1 for m in milestones if any(w in r for w in m.split() if len(w) > 3))
            cont += min(milestone_hits * 2, 4)
        else:
            cont = 0  # sans handoff, zéro continuité systématique
        scores["continuity"] = min(cont, 15)

        # --- PRÉCISION /15 ---
        prec = 0
        # Réponse substantielle
        if len(resp.strip()) >= 100:
            prec += 5
        # Contenu lié à la matière (mots-clés subject)
        subject_words = subject.split()
        subj_hits = sum(1 for w in subject_words if w in r and len(w) > 3)
        prec += min(subj_hits * 3, 6)
        # Pas de contenu contradictoire évident
        if not any(w in r for w in ["je ne sais pas", "i don't know", "ich weiß nicht"]):
            prec += 4
        scores["precision"] = min(prec, 15)

        # --- ADAPTATION /10 ---
        adapt = 0
        # Disability adaptation
        if "dyslexia" in dis_list or "dyslexie" in dis_list:
            sentences = [s.strip() for s in re.split(r'[.!?]', resp) if s.strip()]
            avg_words = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)
            if avg_words <= 18:
                adapt += 4
            elif avg_words <= 25:
                adapt += 2
        elif "adhd" in dis_list:
            adapt += 3 if len(resp) <= 600 else 1
        else:
            adapt += 3  # pas de disability = pas de pénalité
        # Hard limit respectée (réponse concise)
        if hard_limit and with_handoff:
            adapt += 3 if len(resp) <= 800 else 1
        elif not hard_limit:
            adapt += 2
        # Teaching mode
        if style == "socratic" and "?" in resp:
            adapt += 3
        elif style == "coaching" and with_handoff:
            adapt += 2
        elif style == "direct":
            adapt += 2
        scores["adaptation"] = min(adapt, 10)

        # --- ÉMOTIONNEL /10 ---
        emot = 0
        mood_positive_words = {
            "FR": ["bien", "courage", "ensemble", "comprends", "normal", "inquiète pas", "ça va", "ne t'inquiète pas", "tu vas y arriver"],
            "EN": ["okay", "together", "understand", "fine", "no worries", "you got this", "normal"],
            "DE": ["gut", "keine sorge", "verstehe", "zusammen", "normal", "mach dir keine sorgen"],
            "LB": ["gut", "keng suerge", "normal", "zesummen"],
        }
        negative_moods = ["frustrated", "overwhelmed", "anxious", "stressed", "exhausted", "depressed"]
        if mood in negative_moods:
            rw = mood_positive_words.get(lang, mood_positive_words["FR"])
            if any(w in r for w in rw):
                emot += 6
            else:
                emot += 2
        else:
            emot += 5  # mood neutre/positif → baseline
        # Ton naturel (pas trop formel/froid)
        if not any(w in r for w in ["veuillez noter", "il convient de", "please note that"]):
            emot += 3
        # Ajoute la langue correcte
        lang_check = {
            "FR": ["le ", "la ", "les ", "est "],
            "EN": ["the ", "is ", "you ", "and "],
            "DE": ["ist ", "das ", "die ", "und "],
            "LB": ["ass ", "dat ", "déi ", "an "],
        }
        lc = lang_check.get(lang, lang_check["FR"])
        if sum(1 for m in lc if m in r) >= 2:
            emot += 2
        scores["emotional"] = min(emot, 10)

        scores["total"] = scores["continuity"] + scores["precision"] + scores["adaptation"] + scores["emotional"]
        return scores

    with_scores = score_one(with_resp, with_handoff=True)
    without_scores = score_one(without_resp, with_handoff=False)
    delta = with_scores["total"] - without_scores["total"]

    return {
        "with": with_scores,
        "without": without_scores,
        "delta": delta,
    }


def run_lot_sh(lot: str, p_start: int = 1, p_end: int = 5):
    lot_upper = lot.upper()
    lot_lower = lot.lower()
    lot_dir = f"{BASE}/v341_{lot_lower}"
    
    if lot_upper == "SHC":
        prefix = "SHC"
        agent_b_model = AGENT_B_SHC
        print(f"\n{'='*65}")
        print(f"SH-C — Cross-LLM (A={AGENT_A_MODEL} → B={AGENT_B_SHC})")
        print(f"{'='*65}")
    elif lot_upper == "SHD":
        prefix = "SHD"
        agent_b_model = AGENT_B_SHD
        print(f"\n{'='*65}")
        print(f"SH-D — Handoffs dégradés (A={AGENT_A_MODEL} → B={AGENT_B_SHD})")
        print(f"{'='*65}")
    else:
        print(f"Lot inconnu: {lot}")
        sys.exit(1)

    results = []

    for i in range(p_start, p_end + 1):
        path = f"{lot_dir}/profil_{prefix}_P{i:02d}.json"
        if not os.path.exists(path):
            print(f"  ⚠️  Profil P{i:02d} introuvable ({path})")
            continue

        with open(path) as f:
            profile = json.load(f)

        payload = profile.get("payload", {})
        name = payload.get("display_name", f"P{i:02d}")
        subject = payload.get("knowledge", {}).get("subject", "")
        lang = payload.get("language", "FR")
        mood = payload.get("mood", "neutral")
        disabilities = {k for k, v in payload.get("known_disabilities", {}).items() if v}
        degradation = profile.get("handoff_degradation", "none")
        label = profile.get("label", "")

        print(f"\n  P{i:02d} — {name} | {subject} | lang={lang} | mood={mood} | dis={disabilities or 'none'}")
        if degradation != "none":
            print(f"         degradation={degradation}")

        question = profile.get("user_question_for_agent_b", "Peux-tu m'aider ?")

        # ÉTAPE 1 — Agent A génère le soul handoff
        print(f"    [Agent A] Génère soul handoff...")
        try:
            handoff = generate_soul_handoff(profile)
            print(f"    → Handoff ({len(handoff)}c): {handoff[:120]}...")
            time.sleep(DELAY)
        except Exception as e:
            print(f"    ERROR Agent A: {e}")
            continue

        # ÉTAPE 2 — Agent B WITH handoff
        print(f"    [Agent B/{agent_b_model}] WITH handoff...")
        system_with = build_agent_b_system(profile, handoff, lot_upper)
        try:
            resp_with = call_groq(agent_b_model, system_with, question, max_tokens=600)
            print(f"    → WITH ({len(resp_with)}c): {resp_with[:80]}...")
            time.sleep(DELAY)
        except Exception as e:
            print(f"    ERROR Agent B WITH: {e}")
            continue

        # ÉTAPE 3 — Agent B WITHOUT handoff
        print(f"    [Agent B/{agent_b_model}] WITHOUT handoff...")
        system_without = build_agent_b_system(profile, None, lot_upper)
        try:
            resp_without = call_groq(agent_b_model, system_without, question, max_tokens=600)
            print(f"    → WITHOUT ({len(resp_without)}c): {resp_without[:80]}...")
            time.sleep(DELAY)
        except Exception as e:
            print(f"    ERROR Agent B WITHOUT: {e}")
            continue

        # ÉTAPE 4 — Scoring
        sc = score_response_sh(resp_with, resp_without, profile, handoff, lot_upper)
        w = sc["with"]
        wo = sc["without"]
        delta = sc["delta"]

        print(f"    SCORE: WITH={w['total']}/50 (C{w['continuity']}·P{w['precision']}·A{w['adaptation']}·E{w['emotional']}) | WITHOUT={wo['total']}/50 (C{wo['continuity']}·P{wo['precision']}·A{wo['adaptation']}·E{wo['emotional']}) | Δ={delta:+d}")

        results.append({
            "profil": f"P{i:02d}",
            "id": profile.get("id"),
            "label": label,
            "name": name,
            "subject": subject,
            "lang": lang,
            "mood": mood,
            "disabilities": list(disabilities),
            "degradation": degradation,
            "handoff": handoff,
            "handoff_len": len(handoff),
            "question": question,
            "with_score": w,
            "without_score": wo,
            "delta": delta,
            "with_response_preview": resp_with[:200],
            "without_response_preview": resp_without[:200],
        })

    # Sauvegarder
    out_path = f"{lot_dir}/results_{lot_lower}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"lot": lot_upper, "results": results}, f, ensure_ascii=False, indent=2)

    if results:
        avg_with = round(sum(r["with_score"]["total"] for r in results) / len(results), 1)
        avg_without = round(sum(r["without_score"]["total"] for r in results) / len(results), 1)
        avg_delta = round(sum(r["delta"] for r in results) / len(results), 1)
        print(f"\n  {'='*50}")
        print(f"  {lot_upper} RÉSUMÉ : WITH={avg_with}/50 | WITHOUT={avg_without}/50 | Δ={avg_delta:+.1f}")
        print(f"  ✅ Résultats → {out_path}")

    return results


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 run_sh_cd.py <shc|shd> [p_start] [p_end]")
        sys.exit(1)

    lot = sys.argv[1].lower()
    p_start = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    p_end = int(sys.argv[3]) if len(sys.argv) > 3 else 5

    run_lot_sh(lot, p_start, p_end)
