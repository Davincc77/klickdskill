#!/usr/bin/env python3
"""
Generate v3.0 .klickd test vectors (positive + negative).

Outputs:
  tests/vectors_v30.json         — 6 positive vectors
  tests/negative_vectors_v30.json — 8 negative vectors
"""
import base64
import json
import os
import sys
from pathlib import Path

from argon2.low_level import hash_secret_raw, Type as Argon2Type
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import jcs

# ── helpers ──────────────────────────────────────────────────────────────────

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
    fields = {k: envelope[k] for k in ("cipher", "created_at", "domain", "encrypted", "kdf", "klickd_version")}
    return jcs.canonicalize(fields)

def encrypt_v3(
    payload_dict: dict,
    passphrase: str,
    domain: str,
    created_at: str = "2026-05-18T12:00:00Z",
    m: int = 65536,
    t: int = 3,
    p: int = 1,
) -> dict:
    """Encrypt a payload dict into a v3.0 envelope dict."""
    salt = os.urandom(16)
    iv   = os.urandom(12)

    key = derive_key(passphrase, salt, m=m, t=t, p=p)

    kdf_block = {
        "name":   "argon2id",
        "params": {"m": m, "t": t, "p": p},
        "salt":   b64(salt),
    }
    cipher_block = {
        "name": "AES-256-GCM",
        "iv":   b64(iv),
    }

    envelope = {
        "klickd_version": "3.0",
        "encrypted":      True,
        "domain":         domain,
        "created_at":     created_at,
        "kdf":            kdf_block,
        "cipher":         cipher_block,
    }

    aad        = canonical_aad_v3(envelope)
    plaintext  = json.dumps(payload_dict, ensure_ascii=False).encode("utf-8")
    # AESGCM.encrypt returns ciphertext || 16-byte GCM tag
    ciphertext = AESGCM(key).encrypt(iv, plaintext, aad)

    envelope["ciphertext"] = b64(ciphertext)
    return envelope


# ── positive vectors ──────────────────────────────────────────────────────────

def make_positive_vectors() -> list:
    vectors = []

    # 1. v3.0-basic-ascii
    env1 = encrypt_v3(
        {"display_name": "Alice", "user_preferences": "Be concise."},
        passphrase="correct-battery-horse",
        domain="test",
    )
    vectors.append({
        "id":                  "v3.0-basic-ascii",
        "description":         "Basic ASCII payload — domain=test, Argon2id + JCS AAD, should decrypt successfully",
        "passphrase":          "correct-battery-horse",
        "envelope":            env1,
        "expected_display_name": "Alice",
        "expected_behavior":   "decrypt_success",
    })

    # 2. v3.0-french-utf8
    env2 = encrypt_v3(
        {"display_name": "Léa Müller", "user_preferences": "Répondre en français. Préférer les explications claires."},
        passphrase="motdepasse-v30",
        domain="education",
    )
    vectors.append({
        "id":                  "v3.0-french-utf8",
        "description":         "UTF-8 French payload with accented characters — non-ASCII only in payload, not in AAD fields",
        "passphrase":          "motdepasse-v30",
        "envelope":            env2,
        "expected_display_name": "Léa Müller",
        "expected_behavior":   "decrypt_success",
    })

    # 3. v3.0-tampered — flip last byte of ciphertext
    env3_base = encrypt_v3(
        {"display_name": "Alice", "user_preferences": "tamper test"},
        passphrase="correct-battery-horse",
        domain="test",
    )
    ct_bytes = bytearray(base64.b64decode(env3_base["ciphertext"]))
    ct_bytes[-1] ^= 0xFF  # flip last byte (inside GCM tag)
    env3_tampered = dict(env3_base)
    env3_tampered["ciphertext"] = b64(bytes(ct_bytes))
    vectors.append({
        "id":                "v3.0-tampered",
        "description":       "Last byte of ciphertext XOR'd (inside GCM tag) — MUST raise KlickdAuthError",
        "passphrase":        "correct-battery-horse",
        "envelope":          env3_tampered,
        "expected_behavior": "KlickdAuthError — KLICKD_E_AUTH (tampered ciphertext)",
    })

    # 4. v3.0-wrong-passphrase — reuse env1 with wrong passphrase
    vectors.append({
        "id":                "v3.0-wrong-passphrase",
        "description":       "Correct v3.0 envelope, wrong passphrase — MUST raise KlickdAuthError",
        "passphrase":        "wrong-passphrase-xyz",
        "envelope":          env1,
        "expected_behavior": "KlickdAuthError — KLICKD_E_AUTH (wrong passphrase)",
    })

    # 5. v3.0-short-passphrase — passphrase "ab" (< 8 chars)
    # We build a valid-looking envelope; decoder raises KlickdWeakPassphraseError before KDF
    env5 = encrypt_v3(
        {"display_name": "Alice", "user_preferences": "weak pass test"},
        passphrase="correct-battery-horse",  # use valid pass to build envelope
        domain="test",
    )
    vectors.append({
        "id":                "v3.0-short-passphrase",
        "description":       "Passphrase 'ab' (< 8 chars) — MUST raise KlickdWeakPassphraseError",
        "passphrase":        "ab",
        "envelope":          env5,
        "expected_behavior": "KlickdWeakPassphraseError — KLICKD_E_WEAK_PASS (passphrase < 8 chars)",
    })

    # 6. v3.0-warn-passphrase — passphrase "12345678" (8 chars, < 12 recommended)
    env6 = encrypt_v3(
        {"display_name": "Bob", "user_preferences": "warn test"},
        passphrase="12345678",
        domain="test",
    )
    vectors.append({
        "id":                  "v3.0-warn-passphrase",
        "description":         "Passphrase '12345678' (8 chars, < 12 recommended) — decrypt_success with stderr warning",
        "passphrase":          "12345678",
        "envelope":            env6,
        "expected_display_name": "Bob",
        "expected_behavior":   "UserWarning emitted + decrypt_success (passphrase 8 chars: >= min, < 12 recommended)",
    })

    return vectors


# ── negative vectors ──────────────────────────────────────────────────────────

def make_negative_vectors() -> list:
    vectors = []

    # Build a base valid v3.0 envelope to use as template for negatives
    base_env = encrypt_v3(
        {"display_name": "Alice", "user_preferences": "neg test"},
        passphrase="correct-battery-horse",
        domain="test",
    )

    # 1. v3.0-neg-argon2-m-too-low — kdf.params.m=1
    neg1 = json.loads(json.dumps(base_env))
    neg1["kdf"]["params"]["m"] = 1
    vectors.append({
        "id":                "v3.0-neg-argon2-m-too-low",
        "description":       "kdf.params.m=1 (below minimum 65536) — MUST raise KlickdFormatError (KLICKD_E_KDF)",
        "passphrase":        "correct-battery-horse",
        "envelope":          neg1,
        "expected_behavior": "KlickdFormatError — KLICKD_E_KDF (m below minimum)",
    })

    # 2. v3.0-neg-argon2-t-too-low — kdf.params.t=0
    neg2 = json.loads(json.dumps(base_env))
    neg2["kdf"]["params"]["t"] = 0
    vectors.append({
        "id":                "v3.0-neg-argon2-t-too-low",
        "description":       "kdf.params.t=0 (below minimum 3) — MUST raise KlickdFormatError (KLICKD_E_KDF)",
        "passphrase":        "correct-battery-horse",
        "envelope":          neg2,
        "expected_behavior": "KlickdFormatError — KLICKD_E_KDF (t below minimum)",
    })

    # 3. v3.0-neg-argon2-p-too-low — kdf.params.p=0
    neg3 = json.loads(json.dumps(base_env))
    neg3["kdf"]["params"]["p"] = 0
    vectors.append({
        "id":                "v3.0-neg-argon2-p-too-low",
        "description":       "kdf.params.p=0 (below minimum 1) — MUST raise KlickdFormatError (KLICKD_E_KDF)",
        "passphrase":        "correct-battery-horse",
        "envelope":          neg3,
        "expected_behavior": "KlickdFormatError — KLICKD_E_KDF (p below minimum)",
    })

    # 4. v3.0-neg-unsupported-cipher — cipher.name="aes-128-gcm"
    neg4 = json.loads(json.dumps(base_env))
    neg4["cipher"]["name"] = "aes-128-gcm"
    vectors.append({
        "id":                "v3.0-neg-unsupported-cipher",
        "description":       "cipher.name='aes-128-gcm' (unsupported) — MUST raise KlickdAuthError or KlickdFormatError",
        "passphrase":        "correct-battery-horse",
        "envelope":          neg4,
        "expected_behavior": "KlickdAuthError — KLICKD_E_AUTH (cipher name in AAD changed, GCM tag mismatch; or KLICKD_E_FORMAT if cipher name validated first)",
    })

    # 5. v3.0-neg-unsupported-kdf — kdf.name="scrypt"
    neg5 = json.loads(json.dumps(base_env))
    neg5["kdf"]["name"] = "scrypt"
    vectors.append({
        "id":                "v3.0-neg-unsupported-kdf",
        "description":       "kdf.name='scrypt' (unsupported) — MUST raise KlickdFormatError (KLICKD_E_KDF)",
        "passphrase":        "correct-battery-horse",
        "envelope":          neg5,
        "expected_behavior": "KlickdFormatError — KLICKD_E_KDF (unsupported kdf.name='scrypt')",
    })

    # 6. v3.0-neg-tampered-aad-kdf-params — mutate kdf.params.m AFTER encryption
    neg6 = json.loads(json.dumps(base_env))
    # Change m from 65536 to 131072 — this changes the AAD string used to compute GCM tag
    neg6["kdf"]["params"]["m"] = 131072
    vectors.append({
        "id":                "v3.0-neg-tampered-aad-kdf-params",
        "description":       "kdf.params.m mutated post-encryption (kdf is in AAD) — MUST raise KlickdAuthError (GCM tag mismatch)",
        "passphrase":        "correct-battery-horse",
        "envelope":          neg6,
        "expected_behavior": "KlickdAuthError — KLICKD_E_AUTH (kdf.params.m changed post-encryption, AAD mismatch causes GCM auth failure)",
    })

    # 7. v3.0-neg-missing-kdf-block — no kdf field
    neg7 = json.loads(json.dumps(base_env))
    del neg7["kdf"]
    vectors.append({
        "id":                "v3.0-neg-missing-kdf-block",
        "description":       "kdf field absent — MUST raise KlickdFormatError (KLICKD_E_FORMAT)",
        "passphrase":        "correct-battery-horse",
        "envelope":          neg7,
        "expected_behavior": "KlickdFormatError — KLICKD_E_FORMAT (missing 'kdf' block)",
    })

    # 8. v3.0-neg-missing-cipher-block — no cipher field
    neg8 = json.loads(json.dumps(base_env))
    del neg8["cipher"]
    vectors.append({
        "id":                "v3.0-neg-missing-cipher-block",
        "description":       "cipher field absent — MUST raise KlickdFormatError (KLICKD_E_FORMAT)",
        "passphrase":        "correct-battery-horse",
        "envelope":          neg8,
        "expected_behavior": "KlickdFormatError — KLICKD_E_FORMAT (missing 'cipher' block)",
    })

    return vectors


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    repo_dir   = Path(__file__).parent.parent
    tests_dir  = repo_dir / "tests"
    tests_dir.mkdir(exist_ok=True)

    print("Generating positive v3.0 vectors...")
    pos_vectors = make_positive_vectors()
    pos_out = {
        "description":  ".klickd v3.0 positive test vectors",
        "spec_version": "3.0",
        "notes": [
            "AAD = JCS (RFC 8785) over exactly: cipher, created_at, domain, encrypted, kdf, klickd_version",
            "KDF = Argon2id with m=65536, t=3, p=1 (minimum compliant params)",
            "Cipher = AES-256-GCM; ciphertext = AESGCM.encrypt output (ciphertext || 16-byte GCM tag), base64-encoded",
            "Wire format: RFC 4648 §4 standard padded base64",
        ],
        "vectors": pos_vectors,
    }
    pos_path = tests_dir / "vectors_v30.json"
    with open(pos_path, "w", encoding="utf-8") as f:
        json.dump(pos_out, f, indent=2, ensure_ascii=False)
    print(f"  Written {pos_path} ({len(pos_vectors)} vectors)")

    print("Generating negative v3.0 vectors...")
    neg_vectors = make_negative_vectors()
    neg_out = {
        "description":  ".klickd v3.0 negative test vectors",
        "spec_version": "3.0",
        "notes": [
            "N1-N3: Argon2id param floor violations → KlickdFormatError (KLICKD_E_KDF)",
            "N4:    unsupported cipher name → KlickdAuthError (cipher name is in AAD; tag mismatch) or KlickdFormatError",
            "N5:    unsupported kdf.name → KlickdFormatError (KLICKD_E_KDF)",
            "N6:    kdf.params.m mutated post-encryption → KlickdAuthError (GCM AAD mismatch)",
            "N7-N8: missing required blocks → KlickdFormatError (KLICKD_E_FORMAT)",
        ],
        "vectors": neg_vectors,
    }
    neg_path = tests_dir / "negative_vectors_v30.json"
    with open(neg_path, "w", encoding="utf-8") as f:
        json.dump(neg_out, f, indent=2, ensure_ascii=False)
    print(f"  Written {neg_path} ({len(neg_vectors)} vectors)")
    print("Done.")


if __name__ == "__main__":
    main()
