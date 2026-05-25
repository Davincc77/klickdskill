# Demo storyboards (30–60s each)

Text-only storyboards for short demo videos — one per integration shape.
No video files live in this directory; the scripts are deliberately
provider-agnostic so the same beats can be recorded once and re-skinned
per channel.

> **Status:** docs-only, non-normative. No video is generated or stored.
> Anyone may record these clips, but no implied endorsement of any
> recorder, voice talent, or model output is conveyed.

## How to read a storyboard

Each file uses the same five-column shape:

| t (s) | Scene | On-screen text | Voice-over (≤ 12 words) | What the viewer learns |
|-------|-------|----------------|--------------------------|-------------------------|

Beats are paced for 30–60 s total. Cuts are hard. No motion graphics
required — the medium is "loom-style screen capture with optional
voice-over".

## Index

| # | Storyboard | Duration | Surface demoed |
|---|------------|----------|----------------|
| 1 | [`01-python-cli.md`](01-python-cli.md) | ~30 s | `pip install klickd==4.0.0` + CLI loader |
| 2 | [`02-web-dropzone.md`](02-web-dropzone.md) | ~45 s | Browser drag-drop, local-only parse |
| 3 | [`03-langchain.md`](03-langchain.md) | ~50 s | LangChain chain backed by `.klickd` |
| 4 | [`04-llamaindex.md`](04-llamaindex.md) | ~55 s | LlamaIndex docs + vector index from `.klickd` |
| 5 | [`05-xai-grok.md`](05-xai-grok.md) | ~45 s | xAI Grok with `.klickd` system prompt |
| 6 | [`06-student-multi-provider.md`](06-student-multi-provider.md) | ~60 s | One profile, 4 providers, same tutor |

## Constraints all storyboards respect

- **No real PII:** every persona shown is fictional. Use the examples
  under [`examples/v4/personas/`](../../../examples/v4/personas/) or
  [`examples/v4/student-walkthrough/`](../../../examples/v4/student-walkthrough/).
- **No secrets:** never show an API key on screen; redact with
  `XXX_REDACTED` or use `export KEY=...` off-camera.
- **No overclaims:** do not claim benchmark wins in voice-over. If a
  number must be quoted, source it from
  [`benchmarks/`](../../../benchmarks/) with a visible reference.
- **No vendor logos** unless authorised by the vendor.
