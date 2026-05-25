# Storyboard 01 — Python CLI (~30 s)

**Goal:** show that `pip install klickd==4.0.0` + ~10 lines of Python is
enough to read a portable profile.

**Surfaces shown:** terminal only.

| t (s) | Scene | On-screen text | Voice-over (≤ 12 words) | What the viewer learns |
|-------|-------|----------------|--------------------------|-------------------------|
| 0–3 | Black title card | `.klickd v4.0.0 — one file, any model` | "Your AI forgets you. .klickd doesn't." | Hook |
| 3–8 | Terminal: `pip install klickd==4.0.0` | command typed live | "One pip install." | Install path |
| 8–14 | Terminal: `python examples/v4/cli/klickd_cli.py examples/v4/personas/01-eleve-terminale-fr.klickd` | command + scrolling output | "Drop in any profile." | Loader works on real personas |
| 14–22 | Highlight the summary fields (display_name, domain, current_state, gates) | yellow rectangles in capture | "Identity, context, gates — read straight from the file." | Structured payload |
| 22–28 | Cut to `--json` flag; full payload pretty-prints | `python … --json` | "Or get the full JSON." | Power-user path |
| 28–30 | End card: GitHub URL + DOI badge | `github.com/Davincc77/klickdskill` | "One soul. Any model." | CTA |

## Recording notes

- Terminal font ≥ 16pt, dark background — readable on phones.
- The `examples/v4/personas/01-eleve-terminale-fr.klickd` file is
  fictional; no PII handling required.
- Off-camera setup: `cd` into the repo root, ensure `klickd==4.0.0` is
  installed in the active env, no `KLICKD_*` env vars leaking secrets.
