# .klickd v3 — encode (save) implementation
# SPDX-License-Identifier: CC0-1.0

from __future__ import annotations

import base64
import json
import os
from typing import Any

import jcs
from argon2.low_level import hash_secret_raw, Type
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from .errors import KlickdError, KlickdErrorCode

KLICKD_VERSION = "3.0.0"
DEFAULT_KDF_PARAMS = {"m": 65536, "t": 3, "p": 1}


def _b64_encode(data: bytes) -> str:
    """RFC 4648 §4 standard padded base64."""
    return base64.b64encode(data).decode("ascii")


def _derive_key_argon2id(passphrase: str, salt: bytes, m: int, t: int, p: int) -> bytes:
    """Derive a 32-byte key using Argon2id."""
    return hash_secret_raw(
        secret=passphrase.encode("utf-8"),
        salt=salt,
        time_cost=t,
        memory_cost=m,
        parallelism=p,
        hash_len=32,
        type=Type.ID,
    )


def save_klickd(
    payload: dict[str, Any],
    passphrase: str,
    domain: str = "education",
    kdf_params: dict[str, int] | None = None,
) -> bytes:
    """
    Encrypt a KlickdPayload dict and return a .klickd JSON envelope as UTF-8 bytes.

    Args:
        payload:    Dict conforming to KlickdPayload schema.
                    Must include ``payload_schema_version``.
        passphrase: Encryption passphrase (minimum 8 characters).
        domain:     .klickd domain tag. Default: ``"education"``.
        kdf_params: Argon2id parameter overrides.
                    Defaults to ``{"m": 65536, "t": 3, "p": 1}``.

    Returns:
        UTF-8 bytes of the complete .klickd JSON envelope.

    Raises:
        KlickdError: On validation or cryptographic failure.
    """
    params = kdf_params or DEFAULT_KDF_PARAMS

    # Validate passphrase
    if not passphrase or len(passphrase) < 8:
        raise KlickdError(KlickdErrorCode.WEAK_PASS, "Passphrase must be at least 8 characters.")

    # Validate payload schema version
    if not payload.get("payload_schema_version"):
        raise KlickdError(KlickdErrorCode.SCHEMA, "payload_schema_version is required.")

    # Generate fresh CSPRNG salt (16 bytes) and IV (12 bytes)
    salt = os.urandom(16)
    iv = os.urandom(12)

    # Derive 32-byte key
    key = _derive_key_argon2id(
        passphrase, salt, params["m"], params["t"], params["p"]
    )

    # Build the 6-field envelope object for AAD (without ciphertext)
    from datetime import datetime, timezone
    created_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    envelope_for_aad: dict[str, Any] = {
        "klickd_version": KLICKD_VERSION,
        "encrypted": True,
        "domain": domain,
        "created_at": created_at,
        "kdf": {
            "name": "argon2id",
            "params": {"m": params["m"], "t": params["t"], "p": params["p"]},
            "salt": _b64_encode(salt),
        },
        "cipher": {
            "name": "AES-256-GCM",
            "iv": _b64_encode(iv),
        },
    }

    # AAD = RFC 8785 JCS (JSON Canonicalization Scheme)
    aad: bytes = jcs.canonicalize(envelope_for_aad)

    # Encrypt payload JSON with AES-256-GCM
    # cryptography's AESGCM appends the 16-byte tag to ciphertext
    aesgcm = AESGCM(key)
    plaintext = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ciphertext_with_tag = aesgcm.encrypt(iv, plaintext, aad)

    # Build final envelope
    envelope: dict[str, Any] = {
        **envelope_for_aad,
        "ciphertext": _b64_encode(ciphertext_with_tag),
    }

    return json.dumps(envelope, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
