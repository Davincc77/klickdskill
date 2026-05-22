---
title: 'klickdskill: An Open Encrypted File Format for Portable AI User Context'
tags:
  - AI
  - portable context
  - encryption
  - educational technology
  - LLM
  - privacy
  - GDPR
authors:
  - name: Vincenzo Cirilli
    affiliation: 1
affiliations:
  - name: Klickd / Luxlearn, Luxembourg
    index: 1
date: 20 May 2026
bibliography: paper.bib
---

# Summary

`.klickd` is an open, encrypted file format for portable AI user context. It addresses a structural problem in current AI systems: user context (conversation history, preferences, decisions, project state) is stored in provider cloud infrastructure, creating storage costs, GDPR liability, and context loss when switching AI models. `.klickd` relocates context storage from provider infrastructure to the user's own device using AES-256-GCM encryption with Argon2id key derivation (m=65536, t=3, p=4). The file is generated client-side, requires no server communication, and is readable by any AI agent implementing the open specification [@klickd2026].

# Statement of Need

Contemporary AI assistants maintain user context through cloud-hosted memory systems. This architecture creates three compounding problems: (1) infrastructure cost at scale — at 500 million active users generating ~10 KB/day, providers accumulate ~1.8 PB annually; (2) GDPR liability under Articles 5, 17, 20, and 25 [@gdpr2016]; (3) context loss at model boundaries — when switching providers, users must re-establish their full session state from scratch.

Existing approaches are insufficient. `context.json` [@contextjson2025] lacks encryption. Anthropic's Model Context Protocol [@mcp2024] is server-mediated. No existing format combines client-side encryption, zero-server architecture, and AI-provider-agnostic portability in an open standard.

# Format Design

A `.klickd` file is a UTF-8 JSON document. The outer envelope contains routing metadata in plaintext; the inner payload is encrypted. The payload contains five top-level objects: `identity`, `context`, `knowledge`, `session_history`, and `agent_instructions`. The `agent_instructions` field is the primary handoff mechanism — a plain-text string injected verbatim at the start of the receiving agent's system prompt.

Version 3.4.2 introduced 26 new payload fields covering UX/emotional modes (`ux_emotional_mode`, `compression_policy`, `teaching_mode`), accessibility (`known_disabilities`, `latex_rendering`), learning analytics (`learning_goal`, `error_patterns`), and two normative rules: §29c Privacy Guards (re-identification prohibition across agent transitions) and §14bis.1 (on_new_agent event limited to 120 characters). The current release (v3.5.1, DOI [10.5281/zenodo.20320480](https://doi.org/10.5281/zenodo.20320480)) consolidates ATLAS conformance fixes — canonical `cipher.name = "AES-256-GCM"`, `user_preferences` typed as `string`, and a unified schema index distinguishing envelope vs. payload schemas.

# Encryption

From v3.0, key derivation uses Argon2id [@argon2015] with parameters m=65536, t=3, p=4, providing resistance against brute-force and side-channel attacks. The derived 256-bit key encrypts the payload via AES-256-GCM. All encryption is performed client-side; no passphrase or plaintext transits any network. Legacy v2.x files using PBKDF2-SHA256 are auto-detected via the `kdf` envelope field.

# SDK and Reference Implementation

The repository includes:

- Python reference implementation (`load_klickd.py`, `save_klickd.py`) with 52 tests
- TypeScript/ESM package (`@klickd/core`) with 6 tests and CI via GitHub Actions
- JSON Schema (Draft 2020-12) for envelope and payload validation
- 5 canonical example `.klickd` files covering education, professional, and family domains
- Curriculum files for 7 countries (LU, FR, DE, BE, CH, NL, CA)

# Benchmark Evaluation

The `benchmarks/v35/` directory contains a complete LLM-as-judge evaluation framework. The scorer (`scorer_v35.py`) uses `llama-3.3-70b-versatile` [@llama2024] as judge on a /10 grid: Continuity /3 + Pedagogical Precision /3 + Adaptation /2 + Language /2. Evaluation across three cohorts demonstrates consistent gains: modern languages cohort (Lot 89, n=5) improved from Δ−1.0 to Δ+17.8 after correcting a language-evaluation bug; arts/music cohort (Lot 91) and law cohort (Lot 94) each achieved Δ+10.8.

# Production Deployment

`.klickd` is deployed in production in the Klickd educational AI platform (klickd.app, Luxembourg) since May 2026, used for learner profile persistence across AI tutor sessions.

# References
