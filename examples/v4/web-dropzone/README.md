# `examples/v4/web-dropzone/` — Zero-install browser demo (R4-PV-2)

A single static HTML file that lets a user drag-and-drop a plain `.klickd`
profile and see the parsed payload in their browser. Local-only — the
file never leaves the device.

> **Status:** non-normative, docs-only.
> **Scope:** plain payloads (`encrypted: false`). For encrypted envelopes
> use the existing [`/demo/`](../../../demo/) page which carries the full
> AES-GCM + Argon2id decrypt path.

---

## Run it

The page is self-contained — no build step. Either:

**A. Open the file directly** (works for drag-and-drop, but the
"Load example" button requires `fetch`, which most browsers block on
`file://`):

```bash
xdg-open examples/v4/web-dropzone/index.html
# or just double-click it
```

**B. Serve over local http** (recommended):

```bash
python -m http.server 8000
# then open http://localhost:8000/examples/v4/web-dropzone/
```

## What it does

1. Drop a `.klickd` file on the dropzone (or click / Enter to pick one).
2. The page parses the JSON in-browser and renders:
   - A compact summary (identity, domain, context, expertise level, gates).
   - The full pretty-printed payload underneath.
3. Encrypted envelopes (`encrypted: true`) are detected and the user is
   pointed at the canonical `/demo/` page that handles decrypt.

## What it does NOT do

- No network requests after page load (the only `fetch` is the optional
  "Load example" button, pointed at `examples/student_fr.klickd`).
- No telemetry, no third-party scripts, no inline analytics.
- No write-back: the file is read once into memory and discarded when the
  page is closed.

## When to point users at `klickd.app` instead

If the project's hosted SPA at <https://klickd.app/klickdskill> covers the
same surface (drop / inspect / re-export), prefer linking there from the
README and treat this folder as the reproducible offline equivalent for
auditors and CI.
