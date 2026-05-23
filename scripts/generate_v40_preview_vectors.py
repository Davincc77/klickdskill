#!/usr/bin/env python3
"""
Generate v4.0.0-preview.1 .klickd test vectors.

Vectors exercise the additive v4 preview payload surface defined in SPEC §33:
  - minimal preview payload
  - media_profile
  - verification_gates
  - claim_sources + verification_artifacts
  - migration report (v3 -> v4 preview)
  - context_cost

NOTE — preview track is purely additive:
  • The wire envelope stays at klickd_version="3.0" (v3 envelope crypto/wire).
  • Only the inner plaintext payload uses payload_schema_version="4.0.0-preview.1".
  • Decoders MUST preserve unknown v4 preview fields; no strict business validation
    is performed on this track.

Outputs:
  tests/vectors_v40_preview.json

Run:
  python3 scripts/generate_v40_preview_vectors.py
"""
from __future__ import annotations

import base64
import json
import os
import sys
from pathlib import Path

from argon2.low_level import hash_secret_raw, Type as Argon2Type
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import jcs


REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_PATH = REPO_ROOT / "tests" / "vectors_v40_preview.json"


def b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def derive_key(passphrase: str, salt: bytes, m: int = 65536, t: int = 3, p: int = 1) -> bytes:
    return hash_secret_raw(
        secret=passphrase.encode("utf-8"),
        salt=salt,
        time_cost=t,
        memory_cost=m,
        parallelism=p,
        hash_len=32,
        type=Argon2Type.ID,
    )


def canonical_aad_v3(envelope: dict) -> bytes:
    """AAD = JCS over exactly: cipher, created_at, domain, encrypted, kdf, klickd_version."""
    fields = {
        k: envelope[k]
        for k in ("cipher", "created_at", "domain", "encrypted", "kdf", "klickd_version")
    }
    return jcs.canonicalize(fields)


def encrypt_v3(
    payload_dict: dict,
    passphrase: str,
    domain: str,
    created_at: str,
    salt: bytes,
    iv: bytes,
    m: int = 65536,
    t: int = 3,
    p: int = 1,
) -> dict:
    """Encrypt a payload dict into a v3.0 envelope dict using fixed salt+iv."""
    key = derive_key(passphrase, salt, m=m, t=t, p=p)

    kdf_block = {
        "name": "argon2id",
        "params": {"m": m, "t": t, "p": p},
        "salt": b64(salt),
    }
    cipher_block = {
        "name": "AES-256-GCM",
        "iv": b64(iv),
    }

    envelope = {
        "klickd_version": "3.0",
        "encrypted": True,
        "domain": domain,
        "created_at": created_at,
        "kdf": kdf_block,
        "cipher": cipher_block,
    }

    aad = canonical_aad_v3(envelope)
    # Match SDK serialisation: ensure_ascii=False, no whitespace.
    plaintext = json.dumps(payload_dict, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ciphertext = AESGCM(key).encrypt(iv, plaintext, aad)

    envelope["ciphertext"] = b64(ciphertext)
    return envelope


PASSPHRASE = "correct-horse-battery-staple"
CREATED_AT = "2026-05-23T00:00:00Z"


# Deterministic salts/IVs so vectors stay byte-stable across regenerations.
def s(seed: int) -> bytes:
    return bytes((seed + i) & 0xFF for i in range(16))


def iv(seed: int) -> bytes:
    return bytes(((seed * 7) + i) & 0xFF for i in range(12))


# ── Payload builders ─────────────────────────────────────────────────────────

def payload_minimal() -> dict:
    return {
        "payload_schema_version": "4.0.0-preview.1",
        "domain_schema_version": "1.0.0",
        "preview": "v4.0.0-preview.1",
        "profile_kind": "learner",
        "identity": {
            "name": "Preview Tester",
            "language": "en",
            "timezone": "Europe/Luxembourg",
        },
        "agent_instructions": "Treat unknown fields as additive and preserve them on round-trip.",
        "user_preferences": "Continuing a calculus session.",
    }


def payload_media_profile() -> dict:
    base = payload_minimal()
    base["media_profile"] = {
        "modalities": ["text", "image", "audio"],
        "generation_consent": "explicit",
        "voice_profile": None,
    }
    return base


def payload_verification_gates() -> dict:
    base = payload_minimal()
    base["verification_gates"] = {
        "factual_claim_about_person": "block",
        "public_post": "confirm",
        "casual_media_generation": "silent",
    }
    return base


def payload_claim_sources_and_artifacts() -> dict:
    base = payload_minimal()
    base["claim_sources"] = {
        "prefer": ["user_supplied", "tool:web_search"],
        "require_citation_for": ["factual_claim_about_person"],
    }
    base["verification_artifacts"] = [
        {
            "id": "00000000-0000-4000-a000-000000000010",
            "kind": "citation",
            "uri": "https://example.org/source",
            "ts": "2026-05-23T00:00:00Z",
        }
    ]
    return base


def payload_migration_report() -> dict:
    base = payload_minimal()
    base["migration"] = {
        "from_version": "3.5.1",
        "to_version": "4.0.0-preview.1",
        "notes": "Additive only; no field removals.",
    }
    return base


def payload_context_cost() -> dict:
    base = payload_minimal()
    base["context_cost"] = {
        "tokens_in": 1234,
        "tokens_out": 567,
        "estimated_usd": 0.01,
    }
    return base


def payload_unknown_field_passthrough() -> dict:
    """Negative-ish positive: unknown v4 preview field should round-trip untouched."""
    base = payload_minimal()
    base["x_experimental_preview_field"] = {
        "note": "Permissive: decoders preserve unknown fields on the v4 preview track.",
        "marker": 42,
    }
    return base


VECTORS_SPEC = [
    (
        "v4.0-preview-minimal",
        "Minimal v4.0.0-preview.1 payload — only mandatory + identity, no preview features.",
        payload_minimal(),
        ["payload_schema_version", "preview", "identity", "profile_kind"],
    ),
    (
        "v4.0-preview-media-profile",
        "Payload with media_profile (modalities, generation_consent, voice_profile).",
        payload_media_profile(),
        ["media_profile"],
    ),
    (
        "v4.0-preview-verification-gates",
        "Payload with verification_gates declaring block/confirm/silent actions.",
        payload_verification_gates(),
        ["verification_gates"],
    ),
    (
        "v4.0-preview-claim-sources-and-artifacts",
        "Payload with claim_sources prefs and one verification_artifacts entry.",
        payload_claim_sources_and_artifacts(),
        ["claim_sources", "verification_artifacts"],
    ),
    (
        "v4.0-preview-migration-report",
        "Payload with migration block (3.5.1 -> 4.0.0-preview.1).",
        payload_migration_report(),
        ["migration"],
    ),
    (
        "v4.0-preview-context-cost",
        "Payload with context_cost block (tokens_in/out + estimated_usd).",
        payload_context_cost(),
        ["context_cost"],
    ),
    (
        "v4.0-preview-unknown-field-passthrough",
        "Permissive: unknown v4 preview field is preserved on decode (additive policy).",
        payload_unknown_field_passthrough(),
        ["x_experimental_preview_field"],
    ),
]


def build() -> dict:
    vectors = []
    for i, (vid, desc, payload, must_preserve) in enumerate(VECTORS_SPEC):
        envelope = encrypt_v3(
            payload,
            passphrase=PASSPHRASE,
            domain="education",
            created_at=CREATED_AT,
            salt=s(i),
            iv=iv(i),
        )
        vectors.append(
            {
                "id": vid,
                "description": desc,
                "passphrase": PASSPHRASE,
                "envelope": envelope,
                "expected_payload": payload,
                "expected_payload_schema_version": "4.0.0-preview.1",
                "must_preserve_fields": must_preserve,
                "expected_behavior": "decrypt_success",
            }
        )

    return {
        "description": ".klickd v4.0.0-preview.1 positive test vectors (preview track)",
        "spec_version": "4.0.0-preview.1",
        "envelope_version": "3.0",
        "notes": [
            "Preview track — additive, permissive. NOT GA.",
            "Wire envelope crypto/version remains v3.0 (AAD = JCS over cipher, created_at, domain, encrypted, kdf, klickd_version).",
            "Inner payload carries payload_schema_version='4.0.0-preview.1'.",
            "Verifiers MUST check decrypt success and preservation of v4 preview fields, NOT strict business validation.",
            "Unknown preview fields MUST be preserved on decode (additive policy).",
        ],
        "vectors": vectors,
    }


def main() -> int:
    data = build()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(data['vectors'])} v4 preview vectors → {OUT_PATH.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
