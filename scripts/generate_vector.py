#!/usr/bin/env python3
"""
generate_vector.py — generate live encrypted .klickd test vectors
Part of the .klickd open standard (CC0)
https://github.com/Davincc77/klickdskill

Usage:
  python scripts/generate_vector.py --domain finance --passphrase test-vector-2
  python scripts/generate_vector.py --domain robotics --passphrase test-vector-3

Output:
  Prints a valid encrypted .klickd envelope to stdout.
  Use to replace GENERATE_WITH_SCRIPTS_SEE_BELOW placeholders in tests/vectors.json.
"""

import json
import base64
import os
import argparse
from datetime import datetime, timezone

PAYLOADS = {
    "finance": {
        "identity": {
            "name": "Alex",
            "language": "en",
            "timezone": "Europe/London",
            "communication_style": "concise, direct"
        },
        "agent_instructions": "Resuming portfolio review with Alex. BTC at 35%, ETH staking under review.",
        "context": {
            "current_state": "ETH staking under review.",
            "decisions_locked": ["Always display amounts in EUR equivalent"],
            "artifacts": [],
            "summary": "Portfolio rebalancing, session 2."
        }
    },
    "robotics": {
        "identity": {
            "name": "Jordan",
            "language": "en",
            "timezone": "America/New_York",
            "communication_style": "casual"
        },
        "agent_instructions": "Resuming household management with Jordan's Optimus unit. Jordan prefers morning briefings. Kitchen and bedroom are privacy zones.",
        "context": {
            "current_state": "Morning routine configured. Evening mode pending.",
            "decisions_locked": ["Never enter bedroom without explicit request"],
            "artifacts": [],
            "summary": "Household robot onboarding, session 1."
        },
        "robot_profile": {
            "user_preferences": "Morning briefings at 7am, casual tone",
            "household_rules": "Kitchen access: free. Bedroom: no entry without request.",
            "family_context": "Single occupant.",
            "interaction_log": "Session 1: onboarding complete.",
            "trust_scope": "Autonomous: kitchen, living room. Supervised: all other areas.",
            "model_handoff_notes": "First firmware load — no prior state."
        }
    }
}


def encrypt(payload: dict, passphrase: str, domain: str, created_at: str) -> dict:
    try:
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    except ImportError:
        import sys
        sys.exit("ERROR: pip install cryptography")

    salt = os.urandom(16)
    iv   = os.urandom(12)

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=600000,
    )
    key = kdf.derive(passphrase.encode("utf-8"))

    # AAD = envelope metadata (same fields as load_klickd.py)
    aad_fields = {
        "klickd_version": "2.0",
        "encrypted": True,
        "domain": domain,
        "created_at": created_at,
    }
    aad = json.dumps(aad_fields, sort_keys=True, separators=(",", ":")).encode("utf-8")

    plaintext = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    # Wire format: ciphertext || 16-byte GCM tag (AESGCM appends tag automatically)
    ciphertext = AESGCM(key).encrypt(iv, plaintext, aad)

    return {
        "klickd_version": "2.0",
        "encrypted": True,
        "encryption": "AES-256-GCM",
        "domain": domain,
        "created_at": created_at,
        "updated_at": created_at,
        "salt": base64.b64encode(salt).decode(),
        "iv": base64.b64encode(iv).decode(),
        "payload": base64.b64encode(ciphertext).decode(),
    }


def main():
    parser = argparse.ArgumentParser(description="Generate a .klickd test vector")
    parser.add_argument("--domain", choices=list(PAYLOADS.keys()), required=True)
    parser.add_argument("--passphrase", required=True)
    args = parser.parse_args()

    created_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    payload    = PAYLOADS[args.domain]
    envelope   = encrypt(payload, args.passphrase, args.domain, created_at)

    print(json.dumps(envelope, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
