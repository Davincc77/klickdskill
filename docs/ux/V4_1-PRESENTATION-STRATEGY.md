# `.klickd v4.1` Chimera — `/klickdskill` presentation strategy

| | |
|---|---|
| **Status** | **Draft · NON-NORMATIVE · planning only** |
| **Track** | `.klickd v4.1` — Chimera (post-`v4.0.0` GA), future `/klickdskill` public catalog |
| **Created** | 2026-05-27 |
| **Supersedes** | nothing — companion to [`docs/ux/V4-UX-SPEC.md`](./V4-UX-SPEC.md), [`docs/chimera/README_V4_1.md`](../chimera/README_V4_1.md), [`docs/rfcs/RFC-009-chimera-v4.1.md`](../rfcs/RFC-009-chimera-v4.1.md) |
| **Audience** | Future `/klickdskill` site authors, design reviewers, RFC reviewers. NOT end-users; this is product/UX planning. |

> **This document is non-normative and triggers no release.** No tag, no `latest` on npm / PyPI, no DOI on Zenodo, no IANA action, no schema change, no SDK bump, no website edit. It is a **planning artefact for the future `/klickdskill` catalog** once v4.1 candidates reach `ship_ready` per [RFC-009 §8](../rfcs/RFC-009-chimera-v4.1.md). Catalog exposure is a separate decision per RFC-009 §7 and is gated on all P0 packs passing §8 plus the individual candidate passing §8. **Until that gate clears, `/klickdskill` does not list v4.1 skills.**
>
> The reachable artefacts referenced below already live in the repo under [`examples/v4.1/x-klickd-skills/`](../../examples/v4.1/x-klickd-skills/) and [`examples/v4/starter-skills/`](../../examples/v4/starter-skills/). This document does **not** add new `.klickd` files and does **not** edit any website.

---

## 0. Scope and strict exclusions

`/klickdskill` is the **public, brand-neutral, free Skill Library** for the open `.klickd v4.1` Chimera carrier-pack catalog. It is NOT the Klickd.app product surface.

The following MUST NEVER appear on `/klickdskill`:

| Excluded item | Lives instead at |
|---|---|
| Klickd.app product student carriers — `klickdapp.lu.klickd`, `klickdapp.fr.klickd`, `klickdapp.be.klickd`, `klickdapp.de.klickd` (or any other country scope) | [`examples/v4/klickdapp-skills/`](../../examples/v4/klickdapp-skills/) — Klickd.app product only. |
| Kai-side host skills — `skill.kai.tutor.socratic`, `skill.kai.assistant.base`, `skill.kai.dev.review`, `kai.tutor`, any other `kai.*` / `skill.kai.*` | Klickd / Kai host runtime; never `carrier_pack`s. |
| Agent-core artefacts — `core.Kai.klickd`, `core.<Agent>.klickd` | [RFC-006 `agent_core`](../rfcs/RFC-006-agent-core.md). |
| v4-preview persona anchors — `examples/v4/personas/*.klickd` | Anchors / inspiration only, never packs ([RFC-009 §6](../rfcs/RFC-009-chimera-v4.1.md)). |
| Any pack with `_pack_metadata.status != ship_ready` | Internal scaffolds, not catalog entries. |

This separation is non-negotiable. The validator under [`scripts/validate_v4_1_candidate_mapping.py`](../../scripts/validate_v4_1_candidate_mapping.py) already refuses cross-namespace bleeds; the catalog surface must mirror that refusal.

---

## 1. Target shape: 42 entries, two tiers

The catalog targets **42 ship-ready carrier-pack entries**, split into two tiers that share the **same card and detail layout** (homogeneity is mandatory — see §3) but differ on filter defaults, badge density, and loading strategy.

| Tier | Audience | Count | Loading strategy | Token ceiling |
|---|---|---:|---|---|
| **Lite** | Everyday users, learners, parents, citizens, creators starting out. | **8** | Full manifest in prompt. | `router_cost.tokens_estimate ≤ 900`. |
| **Pro** | Developers, researchers, compliance, security, operations, creators at scale. | **34** | `compact_index_plus_lazy_body`. | `router_cost.tokens_estimate ≤ 1,350` (Lite + 50 %). |

### 1.1 Current vs. planned

The catalog target is **42 cards** = **8 Lite + 34 Pro**. The P0 starter packs (`user`, `student`, `research`, `coding`) live under [`examples/v4/starter-skills/`](../../examples/v4/starter-skills/) and are **starter skills, not Pro-tier catalog entries**. They are surfaced on the catalog as a small "Foundations" affordance (category **C9**) attached to the catalog but **not counted toward the 8/34 totals**.

| | Lite | Pro | Total |
|---|---:|---:|---:|
| **`candidate_mapped` artefacts under `examples/v4.1/x-klickd-skills/{lite,pro}/`** as of PR #75 head | 8 | 34 | **42** |
| **P0 starter packs** (`examples/v4/starter-skills/`) — `user`, `student`, `research`, `coding`. Surfaced as "Foundations" affordance, **not** counted toward 8/34. | — | — | (4, separate) |

The 8 Lite + 34 Pro arithmetic is enforced upstream by [`scripts/validate_v4_1_candidate_mapping.py`](../../scripts/validate_v4_1_candidate_mapping.py) (`TIER_EXPECTED_COUNT = {"lite": 8, "pro": 34}`) and by `tests/test_v4_1_candidate_mapping.py::test_tier_artefact_counts_are_frozen_at_8_lite_and_34_pro`. This doc must stay aligned with that invariant.

### 1.2 Pro catalog roster (canonical, aligned with PR #75)

The 34 Pro entries below are the **canonical roster** at the head of PR #75 (`chore/chimera-v4-1-expand-42-skills`). This doc tracks that roster verbatim; if the roster changes by RFC, this section MUST be updated in the same PR that changes it.

**Already shipped before PR #75 (19 Pro)**

`llm-agent-security`, `llm-agent-engineering`, `identity-access-management`, `release-engineer`, `trust-evidence`, `eu-ai-act`, `gdpr-readiness`, `contract-review`, `privacy-product`, `evidence-desk`, `policy-analyst`, `second-brain`, `literature-review`, `project-operator`, `drone-operator`, `mission-control`, `game-design`, `rights-guard`, `video-production-pipeline`.

**Added by PR #75 (15 new Pro, B20..B34)**

`product-manager` (B20), `ux-researcher` (B21), `data-analyst` (B22), `api-integrator` (B23), `devops-operator` (B24), `security-incident-response` (B25), `sales-operator` (B26), `customer-support-operator` (B27), `finance-analyst` (B28), `accounting-operator` (B29), `technical-writer` (B30), `learning-designer` (B31), `sustainability-analyst` (B32), `healthcare-ai-safety-reviewer` (B33), `edge-ai-operator` (B34).

All 34 Pro packs carry `_pack_metadata.status = "candidate_mapped"` and `claims_v41_ga = false`. None is `ship_ready` yet. **Catalog exposure on `/klickdskill` remains gated on [RFC-009 §7 / §8](../rfcs/RFC-009-chimera-v4.1.md)**: until each pack passes §8 and all P0 packs pass §8, the live catalog does not list these entries. Until that gate clears, `/klickdskill` either renders nothing or renders a transparent "v4.1 catalog under construction" disclosure — **not** a half-populated grid.

The 8 Lite roster is fixed at: `work-assistant`, `media-planner`, `consumer-rights`, `social-literacy`, `artist`, `streaming-creator`, `game-literacy`, `parent-gaming`.

---

## 2. Categories

Nine categories, picked to (a) cover every domain present in current artefacts, (b) match how end-users describe their own goals, (c) keep colour count low enough to remain accessible (see §4).

| # | Category | Audience hook | Examples (current artefacts) |
|---|---|---|---|
| **C1** | **Everyday** | "Day-to-day life, citizen rights, parenting, money literacy." | Lite: `consumer-rights`, `social-literacy`, `parent-gaming`, `game-literacy`. |
| **C2** | **Work** | "Get the job done — communication, planning, projects." | Lite: `work-assistant`. Pro: `project-operator`, `product-manager`, `customer-support-operator`, `sales-operator`, `technical-writer`, `learning-designer`. |
| **C3** | **Creator / Media** | "Make and ship creative work." | Lite: `artist`, `streaming-creator`, `media-planner`. Pro: `game-design`, `video-production-pipeline`, `ux-researcher`. |
| **C4** | **Developer / AI** | "Build, ship, and operate software and AI agents." | Pro: `llm-agent-engineering`, `release-engineer`, `data-analyst`, `api-integrator`, `devops-operator`, `edge-ai-operator`. |
| **C5** | **Security / Trust** | "Defend systems, manage identity, ship trustworthy evidence." | Pro: `llm-agent-security`, `identity-access-management`, `trust-evidence`, `evidence-desk`, `security-incident-response`. |
| **C6** | **Legal / Compliance** | "Read the law, ship the audit." | Pro: `eu-ai-act`, `gdpr-readiness`, `contract-review`, `privacy-product`, `rights-guard`, `policy-analyst`, `finance-analyst`, `accounting-operator`, `sustainability-analyst`, `healthcare-ai-safety-reviewer`. |
| **C7** | **Research / Knowledge** | "Think, read, write at depth." | Pro: `second-brain`, `literature-review`. |
| **C8** | **Operations / Mission** | "Run things in the physical world." | Pro: `drone-operator`, `mission-control`. |
| **C9** | **Foundations (P0 starter affordance, not catalog tier)** | "The always-on packs every Chimera stack composes with — surfaced as an affordance, not counted in the 8/34 totals." | P0 starter packs from [`examples/v4/starter-skills/`](../../examples/v4/starter-skills/): `user`, `student`, `research`, `coding`. |

C2..C8 cover the **34 Pro + 8 Lite = 42** catalog entries exactly. C9 is the P0 starter affordance and is **not** counted toward the 42. Sensitive-domain Pro packs in C6 carry their RFC-002 `block` gates verbatim (e.g., `finance-analyst` blocks regulated investment advice; `healthcare-ai-safety-reviewer` blocks clinical claims without trial); the catalog never softens those gates at the card level.

**Rule:** every catalog card carries **exactly one** primary category, even if the underlying pack composes across domains. The composition is visible in the detail panel ("composes with…") and in the comparison table, never in the card chip. Multi-category chips create clutter and break the colour rule (§4.4).

---

## 3. Homogeneous card model

Every card — Lite or Pro, any category — uses the **same** information geometry. No category, no tier, gets a custom layout. This is the single hardest UX constraint, and the one most likely to be relaxed under pressure: hold the line.

### 3.1 Card (grid view)

```
┌──────────────────────────────────────────────────────────┐
│ [CATEGORY CHIP]    [TIER PILL: Lite | Pro]    [STATUS ●] │
│                                                          │
│ Pack name in plain language                              │
│ x.klickd/<canonical_name>                                │
│                                                          │
│ One-sentence carrier statement.                          │
│ "Who actually carries this pack — no PII."               │
│                                                          │
│ [framework] [framework] [framework] +N                   │
│                                                          │
│ ~tokens · composes-with: parent₁, parent₂ · v0.x         │
└──────────────────────────────────────────────────────────┘
```

Mandatory fields (in order):
1. Category chip (left, coloured per §4).
2. Tier pill (centre, neutral).
3. Status dot (right): `●` ship_ready (green), `◐` candidate_mapped (amber), `○` needs_mapping (grey). Only `●` appears on the live `/klickdskill` grid; the other two are visible only in the internal preview behind a flag.
4. Pack name in plain language (max 32 characters, sentence case).
5. Canonical pack id (`x.klickd/<canonical_name>`) in monospace, secondary colour.
6. One-sentence carrier statement, max 140 characters, drawn from the pack's `target_user`. No marketing language.
7. Up to 3 framework chips + overflow counter (`+N`). Frameworks shown in fixed priority order: ESCO → WEF → O*NET → DigComp → EQF → CEFR → LifeComp → NICE → ENISA → CIS → SFIA → others.
8. Footer: `~tokens` (router_cost.tokens_estimate, rounded to 50) · `composes-with` (parent packs, max 2 + overflow) · `v<pack_version>`.

Forbidden on the card:
- price, "popularity", "trending", star ratings, vanity counts;
- screenshots, illustrations, emoji;
- per-category bespoke fields ("hours saved", "compliance score", etc.);
- any field that does not exist verbatim in the underlying `.klickd` file.

### 3.2 Detail panel

Open via card click. Sticky right column on desktop, full-screen overlay on mobile. Sections, in this order, every time:

1. **Header** — pack name, canonical id, category, tier, status, version, last validated date.
2. **Carrier statement** — full `target_user` paragraph from the pack.
3. **Composes with** — parent packs, each linking to its own detail panel.
4. **Framework anchors** — full `frameworks[]` list with IRIs (no homegrown taxonomy ever).
5. **Competencies** — `competencies[]` rendered as a flat list with framework provenance per row.
6. **Gates + human authority** — `gates`, `raise_only`, `final_decision_owner` (per RFC-002).
7. **Source / evidence policy** — RFC-002 §8b reference, RFC-003 `verification_artifacts[]` shape, `pointer_only` flag.
8. **Router cost** — `router_cost` block verbatim (tokens_estimate, loading_strategy, compact_index ref for Pro).
9. **Exclusions** — explicit list of what this pack is **not** (e.g., "not a `host_skill`", "no behaviour", "no pedagogy").
10. **Verify offline** — copy-paste `sha256_file` and `sha256_canonical_json` from the relevant `manifest.json`.
11. **See also** — sibling packs in the same category, plus the per-pack scaffold under `docs/rfcs/chimera/packs/`.

Forbidden in the detail panel:
- per-pack styling tweaks; every section above uses the same typography and spacing as every other pack.
- collapsing the header or the "Verify offline" block — they are always visible.
- "Buy", "Get", "Install" buttons. `/klickdskill` is a catalog, not a store. The CTA is **"Copy pack id"** + **"Download `.klickd`"** + **"Open in viewer"**.

---

## 4. Colour, contrast, accessibility

Colour exists to encode category at a glance. It does NOT encode tier (Lite/Pro), status, or vendor. Tier is a textual pill; status is a neutral dot; vendor is not shown because the catalog is single-publisher.

### 4.1 Palette principles

- **One hue per category, period.** Nine categories → nine hues. No gradients, no per-card hue shifts.
- **Pair every hue with one neutral.** Card background is neutral; the chip is the only coloured surface above 60 px².
- **Use the hue only on the chip + a 2 px left rail on the card.** Never tint the whole card.
- **Pass WCAG 2.2 AA on text-against-chip and chip-against-background** at every accepted theme (light, dark, high-contrast).
- **Pass APCA Lc ≥ 60** for chip text on chip background; Lc ≥ 75 for body text on card background.
- **Test for the three most common colour-vision conditions** (deuteranopia, protanopia, tritanopia) — categories must remain distinguishable. Use [Sim Daltonism](https://michelf.ca/projects/sim-daltonism/) or equivalent before shipping.
- **Never encode meaning by hue alone.** Every chip carries its category letter (C1..C9) and label in text; the chip is decorative redundancy.

### 4.2 Suggested palette (light theme — illustrative, **not** normative)

| Cat | Name | Light bg chip | Light fg chip | Dark bg chip | Dark fg chip | AA against page bg? |
|---|---|---|---|---|---|---|
| C1 | Everyday | `#EAF4FF` | `#0B3D91` | `#0B2A4A` | `#CFE3FF` | ✓ |
| C2 | Work | `#F1F0E8` | `#3F3A1F` | `#2A2818` | `#E8E2C2` | ✓ |
| C3 | Creator / Media | `#FDE9F0` | `#7A1F45` | `#3D1224` | `#F7C7D5` | ✓ |
| C4 | Developer / AI | `#E8F0FB` | `#1F3A6B` | `#162640` | `#C8D8F2` | ✓ |
| C5 | Security / Trust | `#E6F2EC` | `#1F4F3A` | `#10261E` | `#BFE0CF` | ✓ |
| C6 | Legal / Compliance | `#F4ECF7` | `#4A1F66` | `#241236` | `#DCC4ED` | ✓ |
| C7 | Research / Knowledge | `#EEF1E6` | `#3A4A1F` | `#1E2610` | `#D2DCC0` | ✓ |
| C8 | Operations / Mission | `#FBEDE5` | `#7A3A14` | `#3D1E0B` | `#F2D0BD` | ✓ |
| C9 | Foundations | `#ECECEC` | `#222222` | `#161616` | `#D8D8D8` | ✓ |

These values are starting points to be tuned by the design reviewer against the live `/klickdskill` page background. The locked invariants are:

- nine distinct hues (or 8 hues + 1 neutral for C9 Foundations);
- chip contrast ≥ 4.5:1 (WCAG AA normal text) at every theme;
- background of the card is **always** the page neutral, never the category hue;
- the 2 px left rail uses the **dark-fg-chip** colour at the page background, never a saturated mid-tone.

### 4.3 Restraint rules

- **No more than two coloured chips visible per card** at once (category + optional "new since v4.1.0" pill, neutral grey).
- **No category icon.** Letters and labels are enough; icons drift into vendor-logo territory and add a fifth colour by default.
- **No coloured shadows, no glow, no animation on hover** beyond a 1 px outline change and a `cursor: pointer`.
- **No category recoloured to "match" a bundle theme** (§6). Bundles use a neutral surface; the bundled cards keep their own category hue.

### 4.4 Multi-category temptation — refuse it

A pack like `eu-ai-act` touches Legal **and** Developer/AI; `evidence-desk` touches Security **and** Research. The temptation is to render a striped chip or a two-tone rail. **Do not.** Pick the primary category (the one closest to the carrier's day-to-day responsibility) and surface the secondary in the detail panel under **"Also useful for"**. Striped chips break the colour invariant, fail APCA on the secondary stripe, and create a long tail of edge cases the design system cannot police.

---

## 5. UI patterns

`/klickdskill` is a **catalog**, optimised for browse + compare + bundle, not for content marketing. Page weight target: **< 200 KB initial HTML+CSS, < 50 KB JS for the no-bundle path, < 150 KB JS with the bundle builder loaded on demand.**

### 5.1 Layout

- **Top:** plain text intro (max 3 sentences), then category nav (9 chips in a single row, scrollable on mobile).
- **Left rail (desktop) / drawer (mobile):** filters (see §5.3).
- **Main grid:** cards. Default sort: category → tier → name. Optional sort: tokens, last validated, version. **Never** sort by popularity or recommendation.
- **Right rail (desktop only, opt-in):** bundle builder tray (see §5.6). Empty by default, persistent across navigation.
- **Bottom:** comparison table entry point + a "v4.1 readiness" disclosure showing how many of the 42 entries are currently `ship_ready` vs. `candidate_mapped` (today: 0 / 42 — none are `ship_ready` yet, and the catalog reflects that honestly).

### 5.2 Search

- Single input, top-left, sticky.
- Searches across: pack name, canonical id, carrier statement, framework prefLabels, parent pack ids. **Not** across keyword fields invented at presentation time.
- Match style: prefix + token; no fuzzy by default (fuzziness creates "looks like a search engine but isn't" results that hurt trust).
- "/" keybinding focuses the input on desktop.
- Empty result → suggest a category, not a recommendation.

### 5.3 Filters (cumulative AND, never OR-by-default)

| Filter | Values | Default |
|---|---|---|
| **Category** | C1..C9 | all |
| **Tier** | Lite / Pro | all |
| **Status** | ship_ready / preview | ship_ready only on `/klickdskill`; preview only behind internal flag |
| **Framework** | ESCO, WEF, O*NET, DigComp, EQF, CEFR, LifeComp, NICE, ENISA, CIS, SFIA | none (any) |
| **Composes with** | each P0 starter pack (`user`, `student`, `research`, `coding`) | none |
| **Token budget** | ≤ 900 / ≤ 1,350 / no limit | no limit |

Filter UI: checkbox group inside the left rail, with a count badge per value showing how many cards match. Clicking a category chip in the top nav sets the Category filter.

Forbidden filters:
- "Recommended", "Popular", "Featured", "New" — none of these correspond to a fact in the underlying `.klickd` files.
- Free-text tags — every filterable axis must trace back to a frozen field.

### 5.4 Accordion / dropdown

Reserved for the detail panel sections (§3.2) and for the framework chip overflow (`+N`). Never used to hide the carrier statement or framework anchors on the card itself — those are above the fold by definition.

### 5.5 Comparison table

- Triggered from the bundle tray or from a "Compare" button on each card.
- Up to 5 packs at once (mobile: 2). More than 5 destroys row-by-row scannability.
- Rows: every field from the card + the first 5 sections of the detail panel (header, carrier statement, composes-with, frameworks, competencies summary).
- Columns: one per pack, frozen header on scroll.
- No "winner" row. The catalog does not rank.

### 5.6 Bundle builder

The single piece of generative UI on the page. Everything else is read-only.

- **Tray:** persistent, max 7 packs (matches the seven-pack ceiling of [RFC-009 §5.3](../rfcs/RFC-009-chimera-v4.1.md) once `x.klickd/user` is implicit).
- **Token meter:** sum of `router_cost.tokens_estimate` across selected packs. Warns at 80 % of a configurable agent context budget, blocks at 100 %. The default agent budget is a placeholder until the per-pack RFCs land their router_cost rows; do not pretend the meter is normative.
- **Compose preview:** shows the resulting parent-chain graph (no cycles), highlights any pack that would violate the seven-pack ceiling.
- **Export:** "Copy bundle as JSON" (a list of canonical pack ids + versions). **Not** a `.klickd` file — bundles are pack lists, not carrier states. The catalog never composes a real carrier on the user's behalf.
- **Share link:** URL-encoded bundle list, no server-side state. The catalog has no backend.
- **No "Save bundle" account.** `/klickdskill` is signed-out by design.

### 5.7 What `/klickdskill` does NOT do

- No telemetry / analytics on which cards are viewed.
- No "Suggested for you" — there is no `you` because there is no account.
- No comments, ratings, reviews. Feedback funnels to existing channels in [`docs/community/FEEDBACK.md`](../community/FEEDBACK.md).
- No "Install" button. Pack ids and `.klickd` files are downloadable; what to do with them is the host runtime's job.

---

## 6. Tier surface differences

The card and detail layout are identical across tiers (§3). The only tier-driven differences are:

| Surface | Lite | Pro |
|---|---|---|
| Default category filter set | **Everyday + Work + Creator/Media + Foundations** highlighted in the top nav. | **all 9**, with **Developer/AI + Security + Legal + Operations** highlighted. |
| Default tier filter | Lite **and** Pro shown; Lite cards float to the top within each category. | both. |
| Framework chip density on card | up to 3 + overflow. | up to 3 + overflow. (Same — homogeneity rule.) |
| Detail panel "loading strategy" block | hidden by default, opens on click. | open by default. |
| Comparison table default columns | 3 (cards fit at 360 px viewport). | 5. |
| Bundle builder visible | yes, but the tray opens with a one-line note: "Lite packs are designed to work alone or with one Pro composition." | yes, full controls. |

Tier is a **discoverability** lever, not a paywall. There is no "upgrade" prompt. All 42 packs are equally free, equally readable, equally downloadable.

---

## 7. Page weight budget

| Surface | Target | Why |
|---|---|---|
| First paint (no bundle builder) | < 200 KB HTML + CSS, < 50 KB JS | The catalog has to load on a low-end Android in Europe. |
| Bundle builder hydrated | + 100 KB JS, lazy-loaded | Most visitors read 1–3 cards and leave. |
| Comparison table | + 30 KB JS | Triggered explicitly. |
| Card image / illustration weight | **0 KB** | The card has no images (§3.1). |
| Font weight | one variable font, subset, < 50 KB woff2 | No icon font. |

Hard rules:
- No client-side router beyond hash-based filter state.
- No analytics SDK, no ad SDK, no third-party CDN beyond the woff2 font (and even that should be self-hosted if practical).
- No web component framework unless it shrinks total JS — a static site with vanilla JS for filter/search/bundle is the default.

---

## 7a. Per-pack file-size budget (`/klickdskill` public catalog only)

The numbers below apply **only** to v4.1 Chimera carrier packs surfaced on the public `/klickdskill` catalog (the 8 Lite + 34 Pro tracked in §1). They do **not** apply to the Klickd.app product (`klickdapp.*`), to `kai.*` host skills, to `core.*` agent-core artefacts, or to any private/internal pack. Those surfaces follow their own budgets and are explicitly out of scope here per §0.

| Tier | File-size target | File-size ceiling | Loading strategy | `router_cost.tokens_estimate` ceiling |
|---|---|---|---|---|
| **Lite** | ≤ 8 KB | ≤ **12 KB** | Full manifest in prompt. | ≤ 900 tokens. |
| **Pro** | ≤ 16 KB | ≤ **24 KB** | `compact_index_plus_lazy_body` — compact index in prompt; full body lazy-loaded via `decision_router`. | ≤ 1,350 tokens. |

Rationale:
- Lite at ≤ 12 KB stays comfortably loadable on first interaction even on a low-end Android in Europe (matches the catalog page-weight stance above).
- Pro at ≤ 24 KB allows richer competency / gate detail without ever needing a network round-trip to read the pack body, while the **compact index** keeps prompt occupancy small enough that the seven-pack ceiling of [RFC-009 §5.3](../rfcs/RFC-009-chimera-v4.1.md) remains realistic.
- The 24 KB ceiling is a **catalog-surface ceiling**, not a wire-format ceiling. A pack that legitimately needs more substance should split into a smaller compact index plus a lazy-loaded body, or move to a `temporary_overlay` per [RFC-009 §5.4](../rfcs/RFC-009-chimera-v4.1.md) — **never** break the ceiling by inflating the in-prompt body.

Bundle-shape rule:
- **Bundles on `/klickdskill` MUST contain 3–7 packs.** Below 3, the bundle isn't a bundle (single packs are first-class on their own card). Above 7, the bundle violates the seven-pack agent-level ceiling of [RFC-009 §5.3](../rfcs/RFC-009-chimera-v4.1.md) and the bundle builder MUST refuse to export it.
- The bundle builder's token meter is advisory; the **pack-count limit (3–7) is binding**.
- Implicit `x.klickd/user` is **not** counted toward the 3–7 window.

These per-pack and per-bundle budgets exist so the catalog can promise a stable browsing experience without quietly shipping page weight. They are NOT a quality bar (a 5 KB pack is not worse than a 22 KB pack); they are a budget. Validator alignment for the file-size ceilings already exists in [`scripts/validate_v4_1_candidate_mapping.py`](../../scripts/validate_v4_1_candidate_mapping.py); any future tightening to the 12 / 24 KB numbers here MUST be accompanied by a matching validator update in the same PR.

---

## 8. Internationalisation (planning only)

- The catalog ships English first.
- Every translatable string lives in a flat key-value file. Pack names, carrier statements, and category labels are translatable. Canonical pack ids, framework IRIs, and version strings are **never** translated.
- Framework prefLabels follow the framework publisher's localisation (ESCO multi-lingual, DigComp via JRC), not Klickd's.
- RTL: the 2 px left rail becomes a 2 px right rail. Card geometry is otherwise unchanged.

---

## 9. Open questions (deferred to per-pack RFCs and design review)

1. Exact tuning of the 9-hue palette against the live page background (§4.2).
2. Whether the bundle token meter should default to a stated agent context budget or remain advisory only (§5.6).
3. Whether the 4 P0 starter packs get a "Foundations" home, or stay invisible until composed (this doc picks **C9 Foundations**, but RFC review may differ).
4. Whether the catalog renders cards for `candidate_mapped` packs behind a "preview" flag, or hides them entirely until `ship_ready` (§1.2 + §5.3 default).
5. Mobile bundle tray: bottom sheet vs. full-screen step.

---

## 10. See also

- [`docs/chimera/README_V4_1.md`](../chimera/README_V4_1.md) — planning index for v4.1 candidates.
- [`docs/chimera/V4_1_SKILL_CANDIDATE_MAPPING.md`](../chimera/V4_1_SKILL_CANDIDATE_MAPPING.md) — per-candidate mapping table.
- [`docs/rfcs/RFC-009-chimera-v4.1.md`](../rfcs/RFC-009-chimera-v4.1.md) — authoritative spec for v4.1.
- [`docs/rfcs/chimera/frameworks/README.md`](../rfcs/chimera/frameworks/README.md) — canonical admissible-frameworks list (ESCO / WEF / O*NET / DigComp / EQF / CEFR / LifeComp / NICE / ENISA / CIS / SFIA).
- [`docs/ux/V4-UX-SPEC.md`](./V4-UX-SPEC.md) — v4 viewer/decryptor UX, the source of the "simple by default + progressive disclosure" stance reused here.
- [`docs/demos/V4_1-CURATED-BUNDLES.md`](../demos/V4_1-CURATED-BUNDLES.md) — companion: curated bundles and demo agent-team sizes.
- [`docs/community/V4_1-CHALLENGE-CHIMERA-CUP.md`](../community/V4_1-CHALLENGE-CHIMERA-CUP.md) — companion: community challenge proposal.
- [`examples/v4.1/x-klickd-skills/`](../../examples/v4.1/x-klickd-skills/) — `candidate_mapped` artefacts referenced above (none are `ship_ready` yet).
- [`examples/v4/starter-skills/`](../../examples/v4/starter-skills/) — P0 starter packs (`user`, `student`, `research`, `coding`) — starter skills, not Pro-tier catalog entries.
