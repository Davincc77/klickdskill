# Storyboard 06 — One profile, four providers (~60 s)

**Goal:** the headline demo. The same `.klickd` file drives four
providers in succession, each picking up the Socratic tutor mid-session.

**Surfaces shown:** terminal split into four panes, or four sequential
takes cut together.

| t (s) | Scene | On-screen text | Voice-over (≤ 12 words) | What the viewer learns |
|-------|-------|----------------|--------------------------|-------------------------|
| 0–4 | Title card | `One soul. Any model.` | "One profile. Four providers. Same tutor." | Headline |
| 4–10 | Show the file: `examples/v4/student-walkthrough/student-multi-provider.klickd` opened in a viewer; highlight `user_preferences`, `context.resume_trigger`, `verification_gates` | yellow rectangles | "This file lives on your device." | The asset |
| 10–22 | Pane 1: OpenAI (`gpt-4o`) replies in Socratic mode to "I'm stuck — sin(x²)" | OpenAI logo wordmark text only | "GPT-4o — Socratic." | Provider 1 |
| 22–34 | Pane 2: Claude (`claude-opus-4-5`) replies | Anthropic wordmark text only | "Claude — Socratic." | Provider 2 |
| 34–46 | Pane 3: Groq (`llama-3.3-70b-versatile`) replies | Groq wordmark text only | "Llama via Groq — Socratic." | Provider 3 |
| 46–55 | Pane 4: xAI Grok (`grok-2-latest`) replies | xAI wordmark text only | "Grok — Socratic." | Provider 4 |
| 55–58 | Overlay all four side-by-side; each starts with a question, none give the final derivative | grid view | "Same tutor. Four bodies." | Payoff |
| 58–60 | End card | `github.com/Davincc77/klickdskill` | "One soul. Any model." | CTA |

## Recording notes

- Run the four calls live with the snippets in
  [`examples/v4/student-walkthrough/README.md`](../../../examples/v4/student-walkthrough/README.md).
- Use **wordmark text only** for provider names — no logos unless
  authorised by the vendor.
- All four model outputs may legitimately differ in tone and quality.
  Do **not** edit them for parity; the demo is "all four follow the
  Socratic instruction", not "all four sound identical."
- API keys: `export OPENAI_API_KEY=… ANTHROPIC_API_KEY=… GROQ_API_KEY=… XAI_API_KEY=…`
  off-camera. Confirm no key is visible in any terminal pane before recording.
