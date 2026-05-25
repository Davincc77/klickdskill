# Storyboard 03 — LangChain (~50 s)

**Goal:** show that a LangChain chain built on `.klickd` is provider-
agnostic — swap the chat model, keep the profile.

**Surfaces shown:** IDE + terminal.

| t (s) | Scene | On-screen text | Voice-over (≤ 12 words) | What the viewer learns |
|-------|-------|----------------|--------------------------|-------------------------|
| 0–4 | Title card | `.klickd × LangChain` | ".klickd is the state. LangChain is the chain." | Framing |
| 4–10 | IDE: open `examples/v4/integrations/langchain/klickd_langchain.py` | scroll to `klickd_to_system_prompt` | "One helper. Reads the profile. Builds a system prompt." | Adapter shape |
| 10–22 | IDE: split view, write a 6-line chain (`from klickd import load_klickd; …; chain = prompt | ChatOpenAI(...)`) | typed live, syntax-highlighted | "Six lines to wire it up." | Minimal LangChain code |
| 22–32 | Terminal: run script, model replies in Socratic style | model output streams | "Socratic mode comes from the profile, not the code." | Behavior driven by `.klickd` |
| 32–42 | Edit the chain: change `ChatOpenAI(model="gpt-4o")` → `ChatAnthropic(model="claude-opus-4-5")`, rerun | diff highlight | "Swap the model. Same profile. Same tutor." | Provider-agnostic |
| 42–48 | Side-by-side outputs from GPT and Claude, both Socratic | two terminal panes | "One soul. Any model." | Payoff |
| 48–50 | End card | `docs/integrations/langchain.md` | "Doc + code linked below." | CTA |

## Recording notes

- Use the [`student-multi-provider.klickd`](../../../examples/v4/student-walkthrough/student-multi-provider.klickd)
  profile so the same file appears in storyboard 06.
- API keys: `export OPENAI_API_KEY=... ANTHROPIC_API_KEY=...` off-camera.
  Never show the values; if they appear in any pane (e.g. `env`), use a
  cleared terminal session.
- Do not narrate "Claude is better than GPT" or vice versa — both
  outputs should be presented neutrally.
