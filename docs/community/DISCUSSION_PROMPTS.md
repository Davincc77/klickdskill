# Discussion prompts — drafts for first GitHub Discussions

> **Status:** **DRAFT.** Not posted. **Each prompt below requires explicit Vince approval before it is posted to GitHub Discussions.** No automation should post these.
>
> **Audience:** developers landing on the repo from clone traffic, search, or referral. Tone is honest, factual, no hype, no claims of an active community we don't have yet.
>
> **Why these five:** they cover the entry points a developer is most likely to want — a place to say hello, share what they built, propose an integration, request a security look, and react to v4.1 candidate work without thinking v4.1 is GA.

---

## How to use this file

1. Vince picks a prompt below.
2. Vince (or an approved maintainer) creates the matching Discussion category in GitHub Settings → Discussions if it does not exist yet (suggested mapping is in each section).
3. The prompt is pasted in **verbatim or edited first**, then posted as the seed post for that category.
4. The category is pinned only if Vince says so.

Posting cadence suggestion: post **one** prompt first (Welcome), let it sit for 48h, then add Show & tell + Integration ideas. Hold Security review request and v4.1 feedback until at least one real reply exists in the first three — otherwise the page looks empty and self-talking.

---

## 1. Welcome — what `.klickd` is, what it isn't, what's useful here

**Category suggestion:** `Announcements` (maintainer-only post) or `General`.

**Title:** `Welcome — what .klickd is, what it isn't, what you can do here`

**Body:**

```markdown
Hi — thanks for finding this repo.

`.klickd` is one file. It carries AI user-context (preferences, level, goals, gates) in a portable encrypted JSON format. No server, no account, no SDK lock-in. AES-256-GCM + Argon2id, client-side. The format is CC0.

What this repo is:

- The open spec (`SPEC.md`) and strict JSON Schemas (Draft 2020-12).
- Two reference SDKs at v4.0.0 — Python (`klickd`) and TypeScript (`@klickd/core`).
- A v3.x → v4 non-destructive migrator.
- Cross-implementation strict test vectors.
- A growing set of starter `.klickd` skills (`examples/v4/starter-skills/`).

What this repo is **not**:

- Not a hosted memory service. There is no server. We do not store your `.klickd` files.
- Not a replacement for long-context models — it is a complementary state layer (see README §"Long context vs portable state").
- Not v4.1 GA. The `docs/chimera/` and `examples/v4.1/` material is **candidate / non-normative**, no release tag, no `latest` on npm or PyPI.

What is useful here for you as a developer:

- A 5-minute try path: [`docs/community/TRY_IT.md`](../community/TRY_IT.md).
- Integration guides for OpenAI, Anthropic, Groq, OpenRouter, xAI, LangChain, LlamaIndex, Copilot, and a generic pattern: [`docs/integrations/`](../integrations/).
- Security model and threat surface: [`SECURITY.md`](../../SECURITY.md).
- A feedback form for what works / what does not: [`docs/community/FEEDBACK.md`](../community/FEEDBACK.md).

Things I'd like to hear from you:

1. Which model or runtime did you try it with first?
2. Did the 5-minute path actually take ~5 minutes, or did something break?
3. What integration do you wish existed?

— Vince
```

**Notes for Vince before posting:**

- Replace "Vince" with whichever signature you prefer.
- If GitHub Discussions is not yet enabled, enable it in repo Settings → Features → Discussions first.
- Consider pinning this post only after one real reply exists.

---

## 2. Show & tell — what did you carry in a `.klickd`?

**Category suggestion:** `Show and tell`.

**Title:** `Show & tell — what did you put in your first .klickd?`

**Body:**

```markdown
This thread is for sharing what you built or carried in a `.klickd` file. It does **not** need to be a finished project — a screenshot of one prompt working across two models is enough.

Useful things to include in a reply:

- **What runtime / model** you loaded it into (e.g. GPT-4o via OpenAI SDK, Claude Sonnet via Anthropic SDK, Llama via Groq, local Ollama, OpenRouter, LangChain).
- **Which starter skill** you started from, if any (`user.klickd`, `student.klickd`, `research.klickd`, `coding.klickd`) — or that you wrote your own.
- **One concrete thing the model picked up** that it would not have picked up from a cold prompt (level, preference, constraint, gate).
- **One thing that did not work** as you expected.

Please **do not paste real user data**. Strip names, emails, account ids, and anything that would identify a learner. The format is CC0 but the data you put in it is yours — treat what you post here as public.

If you are unsure whether your example is safe to share, post a redacted JSON snippet instead of the full file.
```

**Notes for Vince before posting:**

- This is the lowest-friction first response. Keep the bar deliberately low.
- If a reply contains PII, ask the poster to redact and re-post.

---

## 3. Integration ideas — which provider / framework should be next?

**Category suggestion:** `Ideas`.

**Title:** `Integration ideas — which provider, framework, or runtime should be documented next?`

**Body:**

```markdown
The repo already has integration guides for:

- OpenAI, Anthropic, Groq, OpenRouter, xAI Grok
- LangChain, LlamaIndex
- GitHub Copilot / M365 Copilot (hybrid pattern)
- A generic pattern for any provider

What I would like to hear from you:

1. **Which runtime or framework do you wish had a `.klickd` integration guide?** (Examples: Ollama, vLLM, LM Studio, llama.cpp, MLX, AutoGen, CrewAI, Semantic Kernel, Bedrock, Vertex, Azure OpenAI, Together, Fireworks, Hugging Face Inference, Pydantic-AI, …)
2. **What is the smallest version of that integration** that would be useful to you? (System-prompt-only? Tool/function injection? Full agent loop?)
3. **Is there a non-LLM target** worth documenting — game engine, robotics middleware, IDE extension, browser extension, mobile shell?

A reply of the form *"Ollama, system-prompt-only, because I run everything offline"* is exactly what is helpful. You do not have to propose the implementation — naming the target is the contribution.

If you actually want to **write** an integration guide, see [`CONTRIBUTING.md`](../../CONTRIBUTING.md) and open a PR against `docs/integrations/`.
```

**Notes for Vince before posting:**

- Keep this open-ended; the goal is signal, not a roadmap commitment.
- If an idea attracts ≥3 distinct +1 replies, it is worth turning into an issue.

---

## 4. Security review request — please poke holes in the model

**Category suggestion:** `Q&A` (or a dedicated `Security` category if you create one — note that **vulnerabilities still belong in private disclosure**, not here).

**Title:** `Security review request — please poke holes in the .klickd threat model`

**Body:**

```markdown
> **Read this first:** if you believe you have found a **vulnerability**, do **not** post it here. Use the private disclosure process in [`SECURITY.md`](../../SECURITY.md). This thread is for **design-level** review of the documented threat model.

`.klickd` makes a small set of security claims. The relevant docs are:

- [`SECURITY.md`](../../SECURITY.md) — threat model, crypto choices, what is in scope and what is not.
- [`SPEC.md`](../../SPEC.md) — normative behaviour, JSON Injection Guard, AAD, Argon2id floors, GCM tag handling.

What I would like reviewers to push on (public, design-level only):

1. **Crypto choices.** Are AES-256-GCM + Argon2id with the documented floors the right defaults in 2026? Is the AAD construction sufficient?
2. **JSON injection.** Is the JSON Injection Guard described in `SPEC.md` actually sufficient against the attack classes you would expect, or are there obvious bypasses on the reader side?
3. **Migration surface.** The v3.x → v4 migrator is non-destructive. Does the documented preservation rule (unknown-field preservation) create any practical attack surface for a malicious upstream payload?
4. **Out-of-scope claims.** `.klickd` explicitly does **not** replace provider security, model alignment, or app-level access control. Is anything in `README.md` or `SPEC.md` accidentally over-claiming?
5. **Documentation gaps.** Is there something a security reviewer would expect to be documented that currently is not?

Replies that point at a specific line in `SPEC.md` / `SECURITY.md` are most useful. "Section 4.2 says X but does not address Y" is the ideal shape.

If your finding crosses from "design comment" into "exploit", **stop and use private disclosure**.
```

**Notes for Vince before posting:**

- Hold this prompt until at least one of #1 / #2 / #3 has real replies — otherwise it reads as bait.
- Reiterate the private-disclosure-for-vulns line in the first comment too if anyone gets close to the line.

---

## 5. v4.1 Chimera candidate feedback — non-GA, no release

**Category suggestion:** `Ideas` or a dedicated `v4.1 candidates` category.

**Title:** `v4.1 Chimera — candidate feedback (non-normative, no release)`

**Body:**

```markdown
> **Status:** v4.1 Chimera material in this repo is **candidate / non-normative**. There is **no v4.1 tag**, no `latest` bump on npm or PyPI, no DOI, no IANA action, no schema change. v4.0.0 remains the GA. Nothing in this thread should be read as a v4.1 release announcement.

The planning index for v4.1 candidate work is here:

- [`docs/chimera/README_V4_1.md`](../chimera/README_V4_1.md) — what `docs/chimera/` is and is not.
- [`docs/chimera/V4_1_SKILL_CANDIDATE_MAPPING.md`](../chimera/V4_1_SKILL_CANDIDATE_MAPPING.md) — the candidate list with mapping status (`needs_mapping` / `candidate_mapped` / `ship_ready`).
- [`docs/rfcs/RFC-009-chimera-v4.1.md`](../rfcs/RFC-009-chimera-v4.1.md) — authoritative RFC.
- [`examples/v4.1/chimera-skills/`](../../examples/v4.1/chimera-skills/) — concrete `candidate_mapped` artefacts (lite/ and pro/ tiers).

What would help most at this stage:

1. **Mapping critique.** For any candidate currently marked `candidate_mapped`, do the listed framework anchors (ESCO / DigComp / EQF / CEFR / SFIA / NICE / ENISA / CIS / LifeComp) actually match what a practitioner would expect? Where would you map differently?
2. **`needs_mapping` candidates.** For candidates not yet mapped, is there an authoritative framework you would propose, with a citable IRI?
3. **Pack composition.** Are there candidates that should **not** be their own pack and should compose with an existing one instead?
4. **What is missing entirely.** Is there a skill area you would expect to see as a candidate that is not on the list?

Please do **not** treat replies here as a commitment to ship. Promotion past `candidate_mapped` happens via RFC-009 amendments, not via this thread. This thread exists so the RFC track gets external signal earlier rather than later.
```

**Notes for Vince before posting:**

- This one is the highest risk for being misread as a release announcement. The framing paragraph at the top is load-bearing — do not delete it.
- If anyone in replies starts treating v4.1 as released, correct in-thread immediately and link to `README_V4_1.md`.
