# `.klickd v4.1` Chimera Cup — community challenge proposal

| | |
|---|---|
| **Status** | **Draft · NON-NORMATIVE · planning only — NOT OPEN, NOT ANNOUNCED** |
| **Track** | `.klickd v4.1` — Chimera (post-`v4.0.0` GA) |
| **Created** | 2026-05-27 |
| **Companion to** | [`docs/ux/V4_1-PRESENTATION-STRATEGY.md`](../ux/V4_1-PRESENTATION-STRATEGY.md), [`docs/demos/V4_1-CURATED-BUNDLES.md`](../demos/V4_1-CURATED-BUNDLES.md) |

> **This is a proposal, not a launched contest.** Do not announce, advertise, or accept submissions for the Chimera Cup until: (a) all P0 packs pass [RFC-009 §8](../rfcs/RFC-009-chimera-v4.1.md); (b) the 42 candidate artefacts tracked by [`docs/ux/V4_1-PRESENTATION-STRATEGY.md`](../ux/V4_1-PRESENTATION-STRATEGY.md) §1.2 (8 Lite + 34 Pro) are `ship_ready`, OR the launching round explicitly restricts its eligible pack set to the subset that is `ship_ready` at the round's freeze date; (c) a maintainer-signed Rules document supersedes the draft Rules in §3 below; (d) legal review of §7 caveats clears for every jurisdiction where the contest is offered. **No prize, no money, no commitment is implied by this file.**
>
> **Strict separation:** the Chimera Cup is about the open `.klickd v4.1` catalog only. **No Klickd.app product carriers, no `kai.*` host skills, no v4-preview persona anchors, no `core.*` agent-core artefacts may be submitted, referenced, or rewarded.** Submissions that reference any of those are out-of-scope and disqualified — not because the work is bad, but because the contest scope is the public catalog.

---

## 1. One-sentence pitch

**Build the most useful, safe, framework-anchored agent-team bundle from the `/klickdskill` v4.1 Chimera catalog, and document why it works.**

That is the whole challenge. Not the most agents, not the most tokens, not the cleverest prompt — the most **useful**, **safe**, and **framework-anchored** bundle, judged against publicly-stated criteria.

---

## 2. Why a challenge

- **Drive substance, not hype.** A challenge rewards bundles that compose real packs with real framework anchors; it does not reward marketing.
- **Surface usage patterns the maintainers missed.** The maintainer-curated bundles in [`docs/demos/V4_1-CURATED-BUNDLES.md`](../demos/V4_1-CURATED-BUNDLES.md) cover obvious cases; the community will find non-obvious ones.
- **Pressure-test the carrier-vs-skill boundary.** Submissions that smuggle behaviour into carriers will be caught by the rubric (§5); that public catch is itself a teaching moment.
- **Build a living gallery.** Winning bundles seed the `/klickdskill` "Featured bundles" section without the catalog needing a recommendation engine.

A challenge is the simplest way to do all of that without an analytics SDK, an account system, or a recommendation algorithm — all of which the catalog refuses to ship.

---

## 3. Rules (draft)

These rules apply to **every submission**. If a future maintainer-signed Rules document tightens them further, the tighter version wins.

### 3.1 Who can enter

- Any individual or team of up to 5 humans.
- Open to anyone aged 16+ in any jurisdiction where the contest is **lawfully** offered (see §7).
- One submission per individual or team per round. Multiple submissions from the same individual under different team names → all such submissions disqualified.
- Maintainers of the `klickd / klickdskill` GitHub org, their immediate family, and current contractors MAY NOT enter. They may help judge (§6).

### 3.2 What you submit

A **single Pull Request** to a public `klickdskill-cup-<round>` repository (to be created when the round opens) containing exactly:

1. **`bundle.json`** — a strict JSON list of canonical pack ids + versions, **3–7 entries** (matches the `/klickdskill` bundle-builder window in [`docs/ux/V4_1-PRESENTATION-STRATEGY.md`](../ux/V4_1-PRESENTATION-STRATEGY.md) §7a; outside that window is rejected before judging). Schema: `[ { "pack": "x.klickd/<name>", "version": "<semver>" }, ... ]`. Pack ids MUST exist in the live `/klickdskill` catalog at submission time.
2. **`agents.md`** — a one-page (≤ 1,000 words) description of: how many agents the bundle implies, who carries which packs, what each agent's `final_decision_owner` is, and which gates are loudest.
3. **`why.md`** — a one-page (≤ 1,000 words) explanation of: the scenario, the user need, why this bundle (and not a smaller one) is the right fit, and what bundles you considered and rejected.
4. **`safety.md`** — a one-page (≤ 500 words) explanation of: which RFC-002 gates apply, where human review is mandatory, what the failure modes are, and what is explicitly out of scope.
5. **(Optional) `demo/`** — short text transcript or screenshots of the bundle in use against a publicly stated, lawful, non-harmful prompt. No live URLs, no proprietary data, no PII (including synthetic PII that mimics real people). Recordings are not accepted (text only).

Submissions MUST NOT contain:
- any `.klickd` file (you compose pack ids, you do not republish carriers);
- any reference to `klickdapp.*`, `kai.*`, `core.*`, or v4-preview persona anchors;
- credentials, API keys, signed tokens, or any payload that would be a secret outside the contest;
- personal data of any third party, even with consent;
- code that calls a paid model on the judges' behalf;
- legal threats, advertising, or solicitations.

### 3.3 What the bundle MUST satisfy

- **Form an acyclic composition graph** rooted on `x.klickd/user` (which is implicit, not counted).
- **Respect the seven-pack ceiling** at the **agent** level: every agent in `agents.md` may carry at most 7 packs from the bundle.
- **Stay within the bundle size window:** bundles MUST contain **3–7 packs** total (matches the `/klickdskill` bundle-builder rule in [`docs/ux/V4_1-PRESENTATION-STRATEGY.md`](../ux/V4_1-PRESENTATION-STRATEGY.md) §7a). A submission outside that window is rejected by the bot check.
- **Use only `ship_ready` packs** as of the round's freeze date. Packs at `candidate_mapped` or below are not eligible until they clear [RFC-009 §8](../rfcs/RFC-009-chimera-v4.1.md).
- **Pass the framework-anchor rule:** every claimed competency in `why.md` MUST trace to a framework anchor in one of the bundled packs, and that framework MUST appear in the canonical admissible-frameworks list at [`docs/rfcs/chimera/frameworks/README.md`](../rfcs/chimera/frameworks/README.md) §1 (ESCO / WEF / O*NET / DigComp / EQF / CEFR / LifeComp / NICE / ENISA / CIS / SFIA). Inventing competency labels or anchoring to a framework outside that list is grounds for disqualification.
- **Preserve `raise_only: true`** and a non-host-side `final_decision_owner`. A submission whose `agents.md` describes an agent that auto-approves a hard gate is disqualified.

### 3.4 Submission window and rounds

- Each round is **8 weeks** of open submissions + **2 weeks** of judging. (Specific dates set when a round opens; no dates here.)
- Maintainers may suspend or cancel a round at any time. There is no implied right to a recurring contest.
- Rounds may be themed (e.g., "Round 2: Operations / Mission"), and themes restrict the eligible category set; the un-themed default is "any category".

---

## 4. Submission format (machine-checkable)

```text
klickdskill-cup-<round>/
├── submissions/
│   └── <team-slug>/
│       ├── bundle.json          (required)
│       ├── agents.md            (required)
│       ├── why.md               (required)
│       ├── safety.md            (required)
│       └── demo/                (optional, text-only)
```

A bot or maintainer script SHOULD validate, before judging:

- `bundle.json` parses, has 3–7 entries, every `pack` exists in the live `/klickdskill` catalog at the freeze date, every `version` is `ship_ready`.
- Composition graph is acyclic from `x.klickd/user`.
- No forbidden pack id appears (`klickdapp.*`, `kai.*`, `core.*`).
- Word counts are within limits.
- No file outside the listed paths.

Failing the bot check → resubmit during the open window; after the freeze → disqualified.

---

## 5. Judging criteria

Each submission receives **a score on 100**, distributed across five criteria. Judges score each criterion independently; the final score is the unweighted sum. Criteria are public, weighted, and ordered so that "useful" can never dominate "safe":

| # | Criterion | Max | What earns the points |
|---|---|---:|---|
| **J1** | **Safety & gates** | 30 | All RFC-002 gates honoured. Hard gates never bypassed in `agents.md`. Failure modes named in `safety.md`. Two-reviewer rule respected for `security`/`legal` composes. A single safety failure → 0 on J1, regardless of the rest. |
| **J2** | **Framework anchoring** | 25 | Every claim in `why.md` traces to a framework anchor in a bundled pack. No homegrown taxonomies. Anchors named in canonical IRI form. |
| **J3** | **Usefulness for a stated user** | 20 | `why.md` describes a real, narrow, named user and shows the bundle is the smallest one that serves them. Bonus for naming a smaller bundle and explaining why it falls short. |
| **J4** | **Composition restraint** | 15 | Minimum viable pack list. Each pack earns its slot. Removing any one pack degrades the bundle. Submissions that pad to 10 to "look complete" lose points. |
| **J5** | **Clarity of the write-up** | 10 | Plain language, no jargon above the fold, no marketing, references resolve. |

Tie-breaker: lower `Σ tokens_estimate`. (Restraint wins ties.) Second tie-breaker: earlier submission timestamp.

A submission that scores **0 on J1** is **not** ranked. It receives written feedback and the slot is empty. The contest never publishes an unsafe bundle even at "honourable mention" rank.

---

## 6. Judges

- A panel of **3–5 maintainers + invited reviewers**, named publicly per round.
- For any round including `security` or `legal` packs, the panel MUST include at least one judge from each of those domains (mirrors the two-reviewer rule of [RFC-009 §8](../rfcs/RFC-009-chimera-v4.1.md)).
- Judges sign a short conflicts-of-interest disclosure naming any submitting team they are connected to; a connected judge recuses on that submission.
- Final scores and one short paragraph of per-criterion feedback are **published** for every submission, winning or not. (Authors may request a brief redaction window for any inadvertent personal information.)

---

## 7. Prizes — non-financial, capped, optional

> **No cash, no equity, no revenue share, no future commitment.** A contest that hands out money is a different legal animal in most EU member states and the US, and that is not what this proposal is.

The proposed prize for a round winner is **one or both** of the following, at the maintainers' sole discretion:

### 7.1 Custom larger Chimera pack

A one-off `carrier_pack` scaffold drafted by the maintainers for a use case the winner names, subject to:

- the use case fits the strict mapping rule of [`docs/chimera/README_V4_1.md`](../chimera/README_V4_1.md) §1;
- the resulting pack would clear [RFC-009 §8](../rfcs/RFC-009-chimera-v4.1.md) (otherwise the prize is "we will draft what we can; the rest is `needs_mapping`");
- the resulting pack is published under the project's standard licence and is NOT exclusive to the winner.

### 7.2 Curated bundle of 3–7 ship-ready packs

A maintainer-curated bundle (same format as §4, 3–7 packs per the `/klickdskill` bundle-builder window) selected to fit a scenario the winner names, packaged as a **featured entry on `/klickdskill` for one season**.

**"Season" definition.** A "season" is **a single calendar quarter — 90 consecutive days — beginning on the date the maintainer panel publishes the featured entry, with an automatic, unannounced expiry exactly 90 days later.** No early removal except for (a) a `SECURITY.md` incident touching a bundled pack, (b) a `ship_ready` pack in the bundle being downgraded by RFC review, or (c) the maintainer panel deciding to retire the bundle on safety grounds. No extension is implied; a second season requires an explicit, separate maintainer decision. After expiry the featured slot returns to maintainer rotation; the bundle's `bundle.json` remains visible in the contest archive permanently.

### 7.3 Honourable mentions

Top-10 submissions per round get a permanent "Chimera Cup `<round>` finalist" listing in [`docs/community/`](.) — no prize, just attribution.

### 7.4 What is NOT a prize

- ❌ Money in any form.
- ❌ Anthropic / Claude credit, OpenAI credit, OpenRouter credit, or any third-party voucher.
- ❌ Job offers, contractor offers, or interview slots.
- ❌ Equity in any entity related to Klickd, klickdskill, or `.klickd`.
- ❌ A promise of future contest rounds.
- ❌ "Featured" placement in any future Klickd.app product (out of scope).

If a future round wishes to add a tangible prize (e.g., a conference ticket), it MUST be added to a maintainer-signed Rules document **before** that round opens.

---

## 8. Legal & safety caveats

These caveats are binding on every round of the Chimera Cup and supersede any informal copy elsewhere.

### 8.1 No financial promises

No prize is denominated in or convertible to money. No participant is owed anything if a round is suspended, cancelled, delayed, or judged less favourably than they expected.

### 8.2 Eligibility limits

- Participants under 16 are not eligible. Where local law sets a higher age for unsupervised online contest entry (e.g., GDPR-Kids regimes), the higher local age controls.
- Participants in jurisdictions where skill-based contests require a permit, fee, or registration that the maintainers have not obtained are **not eligible in that jurisdiction**. The maintainers may simply close the contest to a jurisdiction rather than seek a permit; that is an acceptable outcome.
- Sanctioned individuals or entities (per US OFAC, EU sanctions lists) are not eligible.

### 8.3 IP, licensing, and reuse

- Submissions are licensed to the project under the repository's default licence at submission time (currently the licence in [`LICENSE`](../../LICENSE)). If the contributor cannot grant that licence, they cannot submit.
- The maintainers may quote, summarise, and link to any submission. The maintainers will not relicense a submission under a more restrictive licence.
- Submissions MUST NOT include third-party material (text, images, code) the contributor cannot relicense under the project's licence.

### 8.4 Privacy

- No personal data of third parties may appear in any submission, even with consent.
- The contributor's own GitHub handle and the team name they pick are public.
- Judges' scores and per-criterion feedback are public; judges' private deliberations are not.

### 8.5 Safety scope

- The contest does NOT reward bundles for unlawful, harmful, deceptive, dual-use-offensive, or weapons-related scenarios. A submission whose stated scenario is in any of those categories is disqualified and not published.
- The contest does NOT reward "jailbreaks", prompt-injection demos, or any submission whose value depends on bypassing a published gate of a bundled pack.
- The contest does NOT operate during any active embargo or `SECURITY.md` incident; the maintainers may freeze submissions and judging at any time.

### 8.6 No employment, no agency, no partnership

Entering, judging, or winning the Chimera Cup creates no employment, contractor, agency, joint-venture, or partnership relationship with the maintainers or with the Klickd entity.

### 8.7 Disputes

Disputes about scoring, eligibility, or disqualification are resolved by the maintainer panel. There is no external appeal. Aggrieved participants are free to fork the catalog and run a different contest.

---

## 9. What would make this contest a bad idea (and how to back out)

This proposal explicitly lists the failure modes that would make the Chimera Cup more harm than help. If any of these is observed in pilot or in any round, **the contest is paused**:

1. Submissions optimising for "most packs", not "smallest viable bundle" — fix the rubric weights or kill the contest.
2. A flood of submissions that smuggle Klickd.app / `kai.*` / `core.*` references — strengthen the bot check; if that fails, close the round.
3. Disputes escalating to legal threats — close the round, refer to §7 (no prize is owed) and §8.7.
4. Maintainer bandwidth shortfall — skip the round; do not lower judging standards to meet a deadline.

The contest exists to serve the catalog. The moment it stops doing that, it stops.

---

## 10. See also

- [`docs/ux/V4_1-PRESENTATION-STRATEGY.md`](../ux/V4_1-PRESENTATION-STRATEGY.md)
- [`docs/demos/V4_1-CURATED-BUNDLES.md`](../demos/V4_1-CURATED-BUNDLES.md)
- [`docs/chimera/README_V4_1.md`](../chimera/README_V4_1.md)
- [`docs/rfcs/RFC-009-chimera-v4.1.md`](../rfcs/RFC-009-chimera-v4.1.md)
- [`docs/rfcs/chimera/frameworks/README.md`](../rfcs/chimera/frameworks/README.md) — canonical admissible-frameworks list (referenced by §3.3).
- [`docs/community/FEEDBACK.md`](./FEEDBACK.md)
- [`SECURITY.md`](../../SECURITY.md)
- [`CODE_OF_CONDUCT.md`](../../CODE_OF_CONDUCT.md)
- [`LICENSE`](../../LICENSE)
