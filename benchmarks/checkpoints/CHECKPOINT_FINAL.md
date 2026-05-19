# Checkpoint FINAL — 2026-05-19 20:44

**Simulations terminées :** 46
**Tokens totaux :** 328,860

## Stats cumulées

| Métrique | Valeur |
|---|---|
| Sims avec .klickd | 23 |
| Sims sans .klickd | 23 |
| Taux restauration contexte AVEC | 17/23 (73%) |
| Taux restauration contexte SANS | 9/23 (39%) |
| Qualité 'perfect' avec .klickd | 16/23 (70%) |
| Qualité 'perfect' sans .klickd | 6/23 (26%) |
| Tokens prompt moyen S2 AVEC | ~699 |
| Tokens prompt moyen S2 SANS | ~130 |

## Dernières simulations

- `switch_llama70_to_llama8b_with_klickd` | llama-3.3-70b→llama-3.1-8b | WITH | ✓ perfect
- `switch_llama70_to_llama8b_no_klickd` | llama-3.3-70b→llama-3.1-8b | WITHOUT | ✗ none
- `switch_llama8b_to_llama70_with_klickd` | llama-3.1-8b→llama-3.3-70b | WITH | ✓ partial
- `switch_llama8b_to_llama70_no_klickd` | llama-3.1-8b→llama-3.3-70b | WITHOUT | ✗ none
- `switch_gemini_to_gemma9b_with_klickd` | gemini→gemma9b (décommissionné) | WITH | ✗ none
- `switch_gemini_to_llama8b_astro_with_klickd` | gemini→llama8b (astro) | WITH | ✓ perfect
- `switch_gemini_to_llama8b_philo_with_klickd` | gemini→llama8b (philo) | WITH | ✓ perfect
- `stress_test_with_klickd_gemini_to_llama8b` | gemini→llama8b stress | WITH | ✓ perfect
- `stress_test_no_klickd_gemini_to_llama8b` | gemini→llama8b stress | WITHOUT | ✗ partial

## Observations clés finales

1. **Downgrade de modèle** (llama-3.3-70b → llama-3.1-8b) : 100% restauration WITH vs 0% WITHOUT — delta maximal observé.
2. **Stress test multi-domaines** : .klickd reconstruit fidèlement un contexte 4 sujets (tables×thermo×Kant×entropie) après switch de modèle. Sans .klickd, seul le sujet mentionné dans la question de reprise est traité.
3. **Gemini asymétrie** : llama→gemini échoue (0%) même avec .klickd car Gemini reformule sans citer. gemini→llama fonctionne parfaitement (100%) avec .klickd.
4. **gemma2-9b-it décommissionné** sur Groq au moment du test.
5. **Overhead négligeable** : +569 tokens prompt = <0.05 ct USD par session.
