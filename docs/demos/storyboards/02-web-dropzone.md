# Storyboard 02 — Browser dropzone (~45 s)

**Goal:** show that any user with a browser can drop a `.klickd` file and
see the parsed payload, with zero install.

**Surfaces shown:** browser only (no terminal).

| t (s) | Scene | On-screen text | Voice-over (≤ 12 words) | What the viewer learns |
|-------|-------|----------------|--------------------------|-------------------------|
| 0–3 | Title card | `.klickd — zero install, local only` | "No server. No upload. Local only." | Hook |
| 3–10 | Open `examples/v4/web-dropzone/index.html` in browser | URL bar shows `file:///…` or `localhost` | "Open the page. That's all." | No backend |
| 10–18 | Drag `examples/v4/personas/03-fullstack-developer-en.klickd` from Finder/Explorer onto the dropzone | dropzone highlights blue | "Drop your profile." | Drag-drop affordance |
| 18–30 | Summary card animates in (display_name, domain, current_state, expertise_level, gates) | yellow rectangles around each row | "Identity. Context. Gates. All read in your browser." | Structured render |
| 30–38 | Scroll to "Parsed payload" card showing the raw JSON | scroll capture | "Full JSON if you want it." | Power-user path |
| 38–43 | Cut to Network tab: zero outgoing requests | DevTools Network panel empty | "Nothing leaves your machine." | Privacy claim, demonstrable |
| 43–45 | End card | `klickd.app/klickdskill` | "One soul. Any model." | CTA |

## Recording notes

- Use the dropzone at
  [`examples/v4/web-dropzone/`](../../../examples/v4/web-dropzone/) — it
  is purpose-built for this clip.
- The DevTools Network capture must show zero requests *after* the page
  loads. If running off `file://`, the only request will be the initial
  HTML; if running off `localhost`, ditto. Do not record the optional
  "Load example" fetch — drop the file manually instead.
- Persona used is fictional.
