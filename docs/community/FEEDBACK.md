# Feedback we are looking for

`.klickd` has clone traffic and very little spoken feedback. This file exists so a developer who just tried it has a clear, short place to tell us what happened.

There are three ways to leave feedback, in order of preference:

1. **Open a Discussion** (once enabled — see [`DISCUSSION_PROMPTS.md`](./DISCUSSION_PROMPTS.md)). Best for anything open-ended.
2. **Open an issue** using `.github/ISSUE_TEMPLATE/bug_report.yml` or `feature_request.yml`. Best for concrete bugs and asks.
3. **Private disclosure** for security findings — **always** use [`SECURITY.md`](../../SECURITY.md), never a public issue or discussion.

---

## The five questions

Answer whichever ones you have a one-line answer to. You do not need to answer all five.

### 1. What model / runtime did you try `.klickd` with?

Examples: `gpt-4o via OpenAI SDK`, `claude-sonnet-4-6 via Anthropic SDK`, `qwen3-32b via Groq`, `Llama 3 via Ollama local`, `OpenRouter`, `LangChain + …`, `LlamaIndex + …`, `local llama.cpp`, `vLLM`, `Bedrock`, …

We are trying to learn which surfaces are most worth supporting first. Even a single line — "tried it with X, worked" or "tried it with X, did not work because Y" — is useful.

### 2. What integration did you actually want?

The repo ships guides for OpenAI, Anthropic, Groq, OpenRouter, xAI Grok, LangChain, LlamaIndex, Copilot, and a generic pattern. If the integration you wanted is not in that list, name it. If the integration is in the list but the guide did not match what you actually needed to do, say where it diverged.

### 3. What broke?

Be specific. The best shape is:

> "On `<OS>` with `<Python|Node version>` and package version `<x.y.z>`, when I ran `<command or code snippet>`, I got `<exact error>`. I expected `<what>`."

Skip prose. Paste the trace.

If nothing broke and the 5-minute path actually took ~5 minutes, that is also useful — say so. Silence reads the same as failure.

### 4. What would make adoption easier?

Honest answers, even if they are uncomfortable. Examples of things that would be useful to hear:

- "The docs are too long; I bounced before finding the install line."
- "I want a one-file `.klickd` that I can paste into a system prompt without any SDK."
- "I need a `<provider>` integration that you do not have yet."
- "The security claims are not auditable enough for me to use it in `<context>`."
- "I do not understand the relationship between `.klickd` and `<other thing>`."
- "It does too much / it does too little."
- "I do not trust a CC0 spec to remain stable — I need a versioning commitment."

### 5. Would you contribute back?

No pressure. If yes, what shape — an integration guide, a test vector, a translation, a cross-language port, a security review, a benchmark replication, a UX critique? See [`CONTRIBUTING.md`](../../CONTRIBUTING.md) for what we accept and what we do not.

---

## What we will do with your answers

- Aggregate them. We will refer to ranges and themes, not to individual posters, when summarising publicly.
- Use them to prioritise integration guides, docs rewrites, and RFC scope.
- **Not** auto-add you to any list. There is no mailing list. There is no newsletter.

If your feedback contains anything you do not want quoted publicly, say so explicitly — "do not quote" — and we will not.

---

## What we will not promise

- A response within a fixed time window. This is a small project. Replies happen when they happen.
- That every request will land. Some integrations are out of scope; some asks conflict with the security model; some will simply not make the cut.
- That `.klickd` will pivot to fit a single use case. The format is deliberately small. Most "can it also do X" answers will be "no, but X composes on top of it."

We will, however, read every reply. That is the deal.
