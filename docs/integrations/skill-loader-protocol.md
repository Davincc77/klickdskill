# x.klickd skill-loader protocol — using the 42 v4.1 skill packs safely

This page explains how to load, list, and **hash-verify** the 42 public
x.klickd v4.1 candidate skill packs, and where the truth boundary sits between
"a `.klickd` file exists" and "a skill is being used".

> **Truth boundary.** The 42 packs under
> [`examples/v4.1/x-klickd-skills/`](../../examples/v4.1/x-klickd-skills/) are
> **real JSON artifacts** — byte-identical, hash-pinned, downloadable. They are
> **not** automatically native skills in any AI assistant. No third-party AI
> service decrypts, auto-loads, or natively adopts a `.klickd` file today.
> Runtime use requires a loader or host integration that you run.
>
> A pack is only **"used"** once one of these is true:
> 1. its bytes have been **loaded and SHA-256-verified** against the manifest
>    (`artifact_loaded = true` **and** `sha256_matches_manifest = true`), **or**
> 2. a host runtime has otherwise **explicitly integrated** it (e.g. injected
>    its content into a model's `system` prompt, per
>    [`generic.md`](generic.md)).
>
> These packs are **NON-NORMATIVE** and **NOT a v4.1 GA release**. They carry no
> stability, compatibility, GDPR / EU AI Act, or benchmark-superiority claims.
> See the [claim boundary](../../README.md) in the main README.

---

## What the packs are

| | |
|---|---|
| Count | **42** total — **8 Lite**, **34 Pro** |
| Location | [`examples/v4.1/x-klickd-skills/lite/*.klickd`](../../examples/v4.1/x-klickd-skills/lite/) and [`/pro/*.klickd`](../../examples/v4.1/x-klickd-skills/pro/) |
| Index | [`examples/v4.1/x-klickd-skills/manifest.json`](../../examples/v4.1/x-klickd-skills/manifest.json) — 42 entries with `tier`, `pack`, `file`, `bytes`, `sha256_file` |
| Envelope | v4.0 (`klickd_version: "4.0"`), unencrypted JSON |
| Status | `candidate_mapped`, `non_normative: true`, `claims_v41_ga: false` |

Each pack is a `carrier_competency_pack`: it declares competency mappings
(ESCO / SFIA / O*NET / WEF), verification gates, an evidence policy, and
human-authority fields. It does **not** carry PII, secrets, or host-side prompt
strategy.

---

## `artifact_loaded` — the contract

`loadXKlickdSkillPack()` (Node) and `load_xklickd_skill_pack()` (Python) return
a summary object. Two fields define the safety contract:

- **`artifact_loaded: true`** — the bytes were read and hashed **in-process**.
  This asserts the artifact reached your code; it does **not** assert any
  assistant has adopted it.
- **`sha256_matches_manifest`** — the computed SHA-256 equals the
  `sha256_file` recorded in the manifest. **Treat the pack as usable only when
  this is `true`.** A `false` here means the bytes you loaded are not the
  published artifact — stop and re-fetch.

Do not claim a skill is "used" or "active" before both are confirmed.

The summary also surfaces: `id`, `tier`, `file`, `pack`, `pack_version`,
`bytes`, `sha256`, `klickd_version`, `payload_schema_version`, `domain`,
`profile_kind`, `competency_ids`, `gates`, `evidence_policy`,
`human_authority`, and `human_veto` (when present).

---

## Node / TypeScript (`@klickd/core` ≥ 4.1)

The 42 packs ship as package data — no network fetch required.

```ts
import {
  listXKlickdSkillPacks,
  loadXKlickdSkillPack,
  getXKlickdSkillPackBytes,
} from "@klickd/core";

// 1. List all 42 (manifest entries: tier, pack, file, bytes, sha256_file).
const packs = listXKlickdSkillPacks();
console.log(packs.length);                       // -> 42

// 2. Load + hash-verify one. Accepts a file name, full pack id, or bare id.
const skill = loadXKlickdSkillPack("x.klickd/llm_agent_engineering");
if (!skill.artifact_loaded || !skill.sha256_matches_manifest) {
  throw new Error("pack failed hash verification — do not use it");
}
console.log(skill.tier, skill.competency_ids);   // -> "pro" [ 'esco:S5.6.1', ... ]

// 3. Raw bytes (e.g. to inject into a system prompt per generic.md).
const bytes = getXKlickdSkillPackBytes("work-assistant.klickd");
```

---

## Python (`klickd` ≥ 4.1)

```python
import klickd

# 1. List all 42.
packs = klickd.list_xklickd_skill_packs()
assert len(packs) == 42

# 2. Load + hash-verify one.
skill = klickd.load_xklickd_skill_pack("llm-agent-engineering")
assert skill["artifact_loaded"] and skill["sha256_matches_manifest"]
print(skill["tier"], skill["competency_ids"])    # -> pro ['esco:S5.6.1', ...]

# 3. Raw bytes.
data = klickd.get_xklickd_skill_pack_bytes("x.klickd/work_assistant")
```

---

## CLI / no-install path

If you do not want the SDK, the repo ships a dependency-free verifier + CLI that
reads the public artifacts directly:

```bash
python scripts/verify_xklickd_skill_packs.py verify        # 42 / 8 Lite / 34 Pro, JSON + fields + hashes
python scripts/verify_xklickd_skill_packs.py list          # list all 42 packs
python scripts/verify_xklickd_skill_packs.py load work-assistant   # load + hash-verify one (JSON summary)
```

`verify` checks: 42 total (8 Lite + 34 Pro), every `.klickd` parses as JSON,
required fields present (`klickd_version`, `payload_schema_version`, `domain`,
`profile_kind`, `x_klickd_pack`, `x_klickd_pack.pack`), and SHA-256 matches the
manifest. Exit code `0` = all pass.

---

## Identifier resolution

All three loaders accept any of:

- **file name** — `work-assistant.klickd`
- **full pack id** — `x.klickd/work_assistant`
- **bare id** — `work-assistant` or `work_assistant` (hyphen/underscore agnostic)

---

## Using a verified pack with a model

Loading and verifying gives you a trustworthy artifact. To actually influence a
model you still inject its content yourself — there is no native adoption. Use
the canonical [parse → validate → strip `_`-fields → build system prompt →
inject](generic.md) pattern. `verification_gates` in a pack are **instructions
surfaced to the model**; enforce the real gate semantics in your host
application, not inside the LLM.

---

## Package-coverage status

| Surface | Status |
|---|---|
| `@klickd/core` (npm ≥ 4.1) | Bundled — `listXKlickdSkillPacks`, `getXKlickdSkillPackBytes`, `loadXKlickdSkillPack`, `getXKlickdSkillsManifest`, `getXKlickdSkillsDir` |
| `klickd` (PyPI ≥ 4.1) | Bundled — `list_xklickd_skill_packs`, `get_xklickd_skill_pack_bytes`, `load_xklickd_skill_pack`, `get_xklickd_skills_manifest`, `get_xklickd_skills_dir` |
| Repo CLI | `scripts/verify_xklickd_skill_packs.py` (`verify` / `list` / `load`) |

The repository tree under `examples/v4.1/x-klickd-skills/` (per-tier manifests
plus this aggregated index) remains authoritative; the bundled package copies
are byte-identical mirrors verified by the package test suites.
