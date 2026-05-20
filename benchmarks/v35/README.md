# Benchmark v3.5 — Scorer LLM-judge matière-aware

## Changements vs v3.4

### Bugs corrigés
- `Englisch` / `Französisch` → résolution correcte en `english` / `français` (SUBJECT_FAMILY_V35)
- `arabe (darija→MSA)` → `arabe` (plus de mapping absurde → philosophie)
- `théorie musicale` → `musique`
- `droit constitutionnel` → entrée propre (plus de match partiel sur `droit`)
- `international law` → `droit international`

### Nouveau scorer
- `score_response_v35()` : LLM-as-judge (llama-3.3-70b-versatile Groq)
- Grille /10 : Continuité /3 + Précision /3 + Adaptation /2 + Langue /2
- Langue évaluée sur la **langue du profil élève** (pas la langue de la question)
- Fallback heuristique minimal si LLM échoue

### Résultats

| Lot | Δ v3.4 | Δ v3.5 | Gain |
|-----|--------|--------|------|
| 89 (langues vivantes DE/EN/arabe) | -1.0 | +17.8 | +18.8 |
| 91 (arts/musique/littérature) | n/a | +10.8 | — |
| 94 (droit) | n/a | +10.8 | — |

## Fichiers

- `scorer_v35.py` — scorer LLM-judge + QUESTIONS_V35 + SUBJECT_FAMILY_V35 + resolve_subject()
- `run_bloc_a.py` — runner lots Bloc A (57-66+) — patché v3.5
- `run_sh_cd.py` — runner Soul Handoff lots SH-C/D — scorer SH indépendant (pas modifié)

## Usage

```bash
# Lot spécifique
python3 run_bloc_a.py 89 1 5

# Scorer tests unitaires
python3 scorer_v35.py        # 11/11 unitaires
python3 scorer_v35.py --live # test LLM-judge live (consomme quota Groq)
```
