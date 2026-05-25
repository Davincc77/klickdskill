# Storyboard 05 — xAI Grok (~45 s)

**Goal:** show that xAI's OpenAI-compatible endpoint takes `.klickd`
directly — no provider-specific glue.

**Surfaces shown:** IDE + terminal.

| t (s) | Scene | On-screen text | Voice-over (≤ 12 words) | What the viewer learns |
|-------|-------|----------------|--------------------------|-------------------------|
| 0–4 | Title card | `.klickd × xAI Grok` | "Grok speaks OpenAI. So does .klickd." | Framing |
| 4–12 | IDE: open `examples/v4/integrations/xai_grok/klickd_xai.py` | scroll to `XAI_BASE_URL = "https://api.x.ai/v1"` | "Same client. Different base URL." | OpenAI-compatible |
| 12–22 | IDE: write the 8-line call (`from openai import OpenAI; client = OpenAI(base_url=…, api_key=…)`) | typed live | "Eight lines." | Minimal code |
| 22–34 | Terminal: run the script; Grok replies in-persona to the student profile | model output streams | "Same profile. New model. Same tutor." | Payoff |
| 34–42 | Code overlay: highlight `klickd_to_system_prompt(payload)` | yellow box | "The profile builds the system message — once, identically across providers." | Cross-provider invariance |
| 42–45 | End card | `docs/integrations/xai_grok.md` | "Doc + code linked." | CTA |

## Recording notes

- Set `XAI_API_KEY` off-camera; never show the value, even partially.
- Use [`student-multi-provider.klickd`](../../../examples/v4/student-walkthrough/student-multi-provider.klickd)
  so the same profile threads through storyboards 03, 05, and 06.
- Do not claim Grok-vs-other-model superiority in voice-over.
