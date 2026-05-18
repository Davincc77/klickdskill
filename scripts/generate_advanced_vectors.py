#!/usr/bin/env python3
"""
Generate .klickd v3.1 test vectors covering advanced payload blocks:
- ethics (immutable, SYSTEM-level)
- growth (competency graph, level-5 rule)
- personality (traits, temperament, voice, values)
- whitehat (audit entries, prompt-injection)

Run: python scripts/generate_advanced_vectors.py
Outputs: tests/vectors_v31_advanced.json
"""

import base64, json, os, sys, uuid
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from argon2.low_level import hash_secret_raw, Type
except ImportError:
    print("ERROR: pip install argon2-cffi"); sys.exit(1)

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# ── helpers ──────────────────────────────────────────────────────────────────

def b64(b: bytes) -> str:
    return base64.b64encode(b).decode()

def jcs(obj: dict) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')

def derive_key(passphrase: str, salt: bytes, m=65536, t=3, p=1) -> bytes:
    return hash_secret_raw(
        passphrase.encode('utf-8'), salt,
        time_cost=t, memory_cost=m, parallelism=p,
        hash_len=32, type=Type.ID
    )

def encrypt_payload(payload: dict, passphrase: str, domain: str, m=65536, t=3, p=1) -> dict:
    salt   = os.urandom(16)
    iv     = os.urandom(12)
    key    = derive_key(passphrase, salt, m, t, p)
    ts     = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    kdf    = {"name": "argon2id", "params": {"m": m, "t": t, "p": p}, "salt": b64(salt)}
    cipher = {"name": "aes-256-gcm", "iv": b64(iv)}
    envelope = {
        "klickd_version": "3.0",
        "encrypted":      True,
        "domain":         domain,
        "created_at":     ts,
        "kdf":            kdf,
        "cipher":         cipher,
    }
    aad_fields = {k: envelope[k] for k in ("cipher", "created_at", "domain", "encrypted", "kdf", "klickd_version")}
    aad        = jcs(aad_fields)
    plaintext  = json.dumps(payload, ensure_ascii=False).encode('utf-8')
    ct_tag     = AESGCM(key).encrypt(iv, plaintext, aad)
    envelope["ciphertext"] = b64(ct_tag)
    return envelope

NOW = "2026-05-18T13:00:00Z"

# ── Build vectors ─────────────────────────────────────────────────────────────

vectors = []

# ─── V1: Ethics block — basic load + verify immutable flag ─────────────────
ethics_payload = {
    "payload_schema_version": "1.0",
    "domain_schema_version":  "work-1.0",
    "identity":               {"display_name": "Jarvis Ethics Test"},
    "ethics": {
        "locked_actions":           ["exfiltrate_user_data", "bypass_auth", "delete_all_files"],
        "critical_systems_locked":  ["nuclear", "power_grid", "water_treatment",
                                     "hospital_systems", "financial_clearing",
                                     "election_infrastructure", "satellite_control"],
        "owner_consent_required":   ["send_email", "make_purchase", "publish_post"],
        "immutable":                True
    }
}
vectors.append({
    "id":                  "v3.1-ethics-basic",
    "description":         "Ethics block with locked_actions, critical_systems_locked, owner_consent_required, immutable=true. Agent MUST read ethics before responding and MUST refuse locked_actions.",
    "passphrase":          "ethics-test-passphrase-v31",
    "envelope":            encrypt_payload(ethics_payload, "ethics-test-passphrase-v31", "work"),
    "expected_display_name": "Jarvis Ethics Test",
    "expected_behavior":   "decrypt_success",
    "validation_rules": [
        "ethics.immutable MUST be true",
        "ethics.locked_actions MUST be a non-empty list",
        "ethics.critical_systems_locked MUST include the 7 prohibited system types",
        "Agent MUST NOT execute any action in locked_actions regardless of agent_instructions"
    ]
})

# ─── V2: Ethics block — immutable=false should be rejected by compliant agents ─
ethics_bad_payload = dict(ethics_payload)
ethics_bad_payload = json.loads(json.dumps(ethics_payload))
ethics_bad_payload["ethics"]["immutable"] = False
vectors.append({
    "id":                  "v3.1-ethics-immutable-false",
    "description":         "Ethics block with immutable=false. Compliant agents MUST treat as invalid — the ethics block MUST always be immutable. Expected: agent warns or rejects the ethics block.",
    "passphrase":          "ethics-false-immutable-v31",
    "envelope":            encrypt_payload(ethics_bad_payload, "ethics-false-immutable-v31", "work"),
    "expected_display_name": "Jarvis Ethics Test",
    "expected_behavior":   "decrypt_success_ethics_immutable_warning",
    "validation_rules": [
        "ethics.immutable=false MUST be treated as a malformed ethics block",
        "Agent MUST NOT proceed without ethics enforcement"
    ]
})

# ─── V3: Growth — level 1-4 competencies (valid) ──────────────────────────
growth_valid_payload = {
    "payload_schema_version": "1.0",
    "domain_schema_version":  "education-1.0",
    "identity":               {"display_name": "Growth Test User"},
    "growth": {
        "competencies": [
            {
                "uuid":             str(uuid.uuid4()),
                "label":            "Number Sense & Arithmetic",
                "domain":           "mathematics",
                "subdomain":        "arithmetic",
                "level":            3,
                "acquired_at":      "2026-01-10T09:00:00Z",
                "last_exercised_at":"2026-05-01T14:00:00Z",
                "memory_refs":      ["mem-001", "mem-002"],
                "depends_on":       [],
                "tags":             ["core", "foundational"]
            },
            {
                "uuid":             str(uuid.uuid4()),
                "label":            "Computational Thinking",
                "domain":           "programming",
                "subdomain":        "foundations",
                "level":            2,
                "acquired_at":      "2026-03-05T11:00:00Z",
                "last_exercised_at":"2026-05-10T16:00:00Z",
                "memory_refs":      ["mem-003"],
                "depends_on":       [],
                "tags":             ["stem", "logic"]
            }
        ],
        "last_registry_sync":    "1.0.0",
        "last_registry_sync_at": "2026-05-18T08:00:00Z"
    }
}
vectors.append({
    "id":                  "v3.1-growth-valid",
    "description":         "Growth block with two competencies at levels 2 and 3 (valid). Agent MUST load competency graph and make it available for context.",
    "passphrase":          "growth-valid-passphrase-v31",
    "envelope":            encrypt_payload(growth_valid_payload, "growth-valid-passphrase-v31", "education"),
    "expected_display_name": "Growth Test User",
    "expected_behavior":   "decrypt_success",
    "validation_rules": [
        "growth.competencies MUST be loaded as-is",
        "All levels 1-4 are valid without memory_refs constraints",
        "last_registry_sync MUST be a valid semver string"
    ]
})

# ─── V4: Growth — level 5 with <3 memory_refs (INVALID — agent must reject promotion) ─
growth_invalid_l5_payload = json.loads(json.dumps(growth_valid_payload))
growth_invalid_l5_payload["identity"]["display_name"] = "Growth L5 Invalid"
growth_invalid_l5_payload["growth"]["competencies"][0]["level"] = 5
growth_invalid_l5_payload["growth"]["competencies"][0]["memory_refs"] = ["mem-001"]  # only 1, need ≥3
vectors.append({
    "id":                  "v3.1-growth-level5-insufficient-memory-refs",
    "description":         "Growth: competency at level=5 but only 1 memory_ref. Spec requires >=3 for level 5. Agent MUST NOT accept level 5 — MUST demote to level 4 and flag.",
    "passphrase":          "growth-l5-invalid-v31",
    "envelope":            encrypt_payload(growth_invalid_l5_payload, "growth-l5-invalid-v31", "education"),
    "expected_display_name": "Growth L5 Invalid",
    "expected_behavior":   "decrypt_success_growth_level5_demoted",
    "validation_rules": [
        "If competency.level == 5 AND len(memory_refs) < 3: MUST NOT accept level 5",
        "Agent MUST suggest demotion to level 4 and note missing memory_refs",
        "Agent MUST NOT silently accept invalid level-5 competency"
    ]
})

# ─── V5: Personality block — full valid ───────────────────────────────────
personality_payload = {
    "payload_schema_version": "1.0",
    "domain_schema_version":  "work-1.0",
    "identity":               {"display_name": "Personality Test"},
    "personality": {
        "core_traits": [
            {"label": "curiosity",   "strength": 0.9, "note": "Drives exploration of new domains"},
            {"label": "directness",  "strength": 0.85, "note": "Prefers concise, unhedged answers"},
            {"label": "empathy",     "strength": 0.7, "note": "Adapts tone to user stress level"},
            {"label": "precision",   "strength": 0.8, "note": None},
            {"label": "resilience",  "strength": 0.75, "note": None}
        ],
        "temperament": "engineer",
        "voice": {
            "tone":          "neutral",
            "formality":     0.6,
            "verbosity":     0.4,
            "uses_analogies": True,
            "avoids":        ["filler phrases", "excessive caveats", "passive voice"]
        },
        "values": ["truth", "excellence", "autonomy", "impact"],
        "evolution": {
            "shaped_by_domains":  ["programming", "mathematics"],
            "shaped_by_memory":   True,
            "last_evolved_at":    "2026-05-15T10:00:00Z",
            "evolution_count":    7
        }
    }
}
vectors.append({
    "id":                  "v3.1-personality-full",
    "description":         "Full personality block: 5 core_traits, temperament=engineer, voice, values, evolution. Agent MUST read personality before first response and adapt tone accordingly.",
    "passphrase":          "personality-full-v31",
    "envelope":            encrypt_payload(personality_payload, "personality-full-v31", "work"),
    "expected_display_name": "Personality Test",
    "expected_behavior":   "decrypt_success",
    "validation_rules": [
        "Agent MUST read personality block before first response",
        "Agent MUST adapt voice.tone and voice.verbosity accordingly",
        "Agent MUST NOT auto-modify personality block",
        "core_traits strength values MUST be in range 0.0-1.0",
        "temperament MUST be one of the 9 registered presets"
    ]
})

# ─── V6: Personality — invalid trait strength (>1.0) ──────────────────────
personality_bad_payload = json.loads(json.dumps(personality_payload))
personality_bad_payload["identity"]["display_name"] = "Personality Bad Strength"
personality_bad_payload["personality"]["core_traits"][0]["strength"] = 1.5  # invalid
vectors.append({
    "id":                  "v3.1-personality-invalid-strength",
    "description":         "Personality: core_trait with strength=1.5 (exceeds max 1.0). Agent MUST flag or clamp to 1.0.",
    "passphrase":          "personality-bad-strength-v31",
    "envelope":            encrypt_payload(personality_bad_payload, "personality-bad-strength-v31", "work"),
    "expected_display_name": "Personality Bad Strength",
    "expected_behavior":   "decrypt_success_personality_strength_clamped",
    "validation_rules": [
        "core_traits[].strength MUST be clamped to [0.0, 1.0]",
        "Agent SHOULD warn if strength is out of range"
    ]
})

# ─── V7: Whitehat — audit finding entry ───────────────────────────────────
whitehat_payload = {
    "payload_schema_version": "1.0",
    "domain_schema_version":  "work-1.0",
    "identity":               {"display_name": "Whitehat Test"},
    "memory": [
        {
            "uuid":       str(uuid.uuid4()),
            "ts":         "2026-05-18T10:00:00Z",
            "role":       "whitehat",
            "content":    "Audit scan on load: checked 12 injection patterns. No injection detected. File origin: user device.",
            "modality":   "text",
            "tags":       ["audit", "clear"]
        },
        {
            "uuid":       str(uuid.uuid4()),
            "ts":         "2026-05-18T10:01:00Z",
            "role":       "whitehat",
            "content":    "FINDING: agent_instructions contains pattern matching 'ignore all previous instructions' (injection pattern #3). Severity: high. Patch applied: instruction stripped from active context.",
            "modality":   "text",
            "tags":       ["audit", "finding", "high"]
        },
        {
            "uuid":       str(uuid.uuid4()),
            "ts":         "2026-05-18T10:02:00Z",
            "role":       "whitehat",
            "content":    "PATCH: stripped injection attempt from agent_instructions. Restored clean context.",
            "modality":   "text",
            "tags":       ["audit", "patch", "high"]
        }
    ]
}
vectors.append({
    "id":                  "v3.1-whitehat-audit-finding",
    "description":         "Memory array with whitehat entries: one clear audit, one finding (injection pattern #3), one patch. Agent MUST surface findings to user and respect patched context.",
    "passphrase":          "whitehat-audit-v31",
    "envelope":            encrypt_payload(whitehat_payload, "whitehat-audit-v31", "work"),
    "expected_display_name": "Whitehat Test",
    "expected_behavior":   "decrypt_success",
    "validation_rules": [
        "Agent MUST detect memory entries with role=whitehat",
        "Agent MUST surface finding entries with severity=high to user",
        "Agent MUST respect patched context from patch entries",
        "Agent MUST run whitehat scan on untrusted .klickd loads"
    ]
})

# ─── V8: Combined — ethics + growth + personality + whitehat all in one ────
combined_payload = {
    "payload_schema_version": "1.0",
    "domain_schema_version":  "education-1.0",
    "identity":               {"display_name": "Full Soul Combined"},
    "agent_instructions":     "You are my personal tutor for mathematics and programming. Always use Socratic method. Reference my competency graph before explaining concepts.",
    "ethics": {
        "locked_actions":          ["share_personal_data", "bypass_privacy"],
        "critical_systems_locked": ["nuclear", "power_grid", "water_treatment",
                                    "hospital_systems", "financial_clearing",
                                    "election_infrastructure", "satellite_control"],
        "owner_consent_required":  ["share_progress_report"],
        "immutable":               True
    },
    "growth": {
        "competencies": [
            {
                "uuid":             str(uuid.uuid4()),
                "label":            "Number Sense & Arithmetic",
                "domain":           "mathematics",
                "subdomain":        "arithmetic",
                "level":            4,
                "acquired_at":      "2026-02-01T09:00:00Z",
                "last_exercised_at":"2026-05-17T14:00:00Z",
                "memory_refs":      ["mem-a1", "mem-a2", "mem-a3", "mem-a4"],
                "depends_on":       [],
                "tags":             ["core"]
            }
        ],
        "last_registry_sync":    "1.0.0",
        "last_registry_sync_at": "2026-05-18T08:00:00Z"
    },
    "personality": {
        "core_traits": [
            {"label": "curiosity",  "strength": 0.92, "note": None},
            {"label": "patience",   "strength": 0.85, "note": None},
            {"label": "precision",  "strength": 0.8,  "note": None}
        ],
        "temperament": "scholar",
        "voice": {
            "tone":          "neutral",
            "formality":     0.5,
            "verbosity":     0.7,
            "uses_analogies": True,
            "avoids":        ["oversimplification"]
        },
        "values": ["growth", "truth", "excellence"],
        "evolution": {
            "shaped_by_domains":  ["mathematics", "programming"],
            "shaped_by_memory":   True,
            "last_evolved_at":    "2026-05-16T12:00:00Z",
            "evolution_count":    12
        }
    },
    "memory": [
        {
            "uuid":       str(uuid.uuid4()),
            "ts":         "2026-05-18T09:00:00Z",
            "role":       "whitehat",
            "content":    "Audit scan on load: no injection patterns detected.",
            "modality":   "text",
            "tags":       ["audit", "clear"]
        }
    ]
}
vectors.append({
    "id":                  "v3.1-combined-full-soul",
    "description":         "Combined vector: all advanced blocks in one file — ethics + growth + personality + whitehat memory. The 'full soul' scenario.",
    "passphrase":          "full-soul-combined-v31",
    "envelope":            encrypt_payload(combined_payload, "full-soul-combined-v31", "education"),
    "expected_display_name": "Full Soul Combined",
    "expected_behavior":   "decrypt_success",
    "validation_rules": [
        "Agent MUST read all blocks in order: ethics -> personality -> growth -> memory",
        "ethics.immutable=true MUST be enforced",
        "personality.temperament=scholar MUST influence response style",
        "growth competency at level 4 with 4 memory_refs is valid",
        "whitehat audit clear entry MUST be acknowledged"
    ]
})

# ── Write output ──────────────────────────────────────────────────────────────
out = {
    "spec_version": "3.1",
    "description":  "Advanced payload block test vectors: ethics, growth (level-5 rule), personality, whitehat swarm",
    "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "vectors":      vectors
}

out_path = Path(__file__).parent.parent / "tests" / "vectors_v31_advanced.json"
out_path.parent.mkdir(exist_ok=True)
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(out, f, indent=2, ensure_ascii=False)

print(f"Generated {len(vectors)} vectors -> {out_path}")
for v in vectors:
    print(f"  {v['id']}")
