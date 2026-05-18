# .klickd v3 — decode (load) implementation
# SPDX-License-Identifier: CC0-1.0

from __future__ import annotations

import base64
import hashlib
import json
from typing import Any

import jcs
from argon2.low_level import hash_secret_raw, Type
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from .errors import KlickdError, KlickdErrorCode

SUPPORTED_MAJOR = 3
REQUIRED_ENVELOPE_FIELDS = frozenset(
    ["klickd_version", "encrypted", "domain", "created_at", "kdf", "cipher", "ciphertext"]
)


def _b64_decode(s: str) -> bytes:
    """RFC 4648 §4 standard padded base64 decode."""
    return base64.b64decode(s)


def _derive_key_argon2id(passphrase: str, salt: bytes, m: int, t: int, p: int) -> bytes:
    return hash_secret_raw(
        secret=passphrase.encode("utf-8"),
        salt=salt,
        time_cost=t,
        memory_cost=m,
        parallelism=p,
        hash_len=32,
        type=Type.ID,
    )


def _derive_key_pbkdf2(passphrase: str, salt: bytes, iterations: int) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", passphrase.encode("utf-8"), salt, iterations, dklen=32)


def load_klickd(
    file_bytes: bytes,
    passphrase: str | None = None,
    legacy: bool = False,
) -> dict[str, Any]:
    """
    Decrypt and parse a .klickd envelope.

    Args:
        file_bytes: Raw .klickd file content (UTF-8 JSON bytes).
        passphrase: Decryption passphrase.
        legacy:     Set ``True`` to allow legacy PBKDF2-SHA256/600k v2.x files.
                    Default: ``False``.

    Returns:
        The decrypted payload as a dict (KlickdPayload-compatible).

    Raises:
        KlickdError: On any format, version, authentication, or schema error.
    """
    # Parse envelope JSON
    try:
        envelope: dict[str, Any] = json.loads(file_bytes.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise KlickdError(KlickdErrorCode.FORMAT, f"Invalid JSON envelope: {exc}") from exc

    if not isinstance(envelope, dict):
        raise KlickdError(KlickdErrorCode.FORMAT, "Envelope must be a JSON object.")

    # Validate required fields
    missing = REQUIRED_ENVELOPE_FIELDS - envelope.keys()
    if missing:
        raise KlickdError(
            KlickdErrorCode.FORMAT,
            f"Missing required envelope fields: {', '.join(sorted(missing))}",
        )

    # Check major version
    try:
        major = int(str(envelope["klickd_version"]).split(".")[0])
    except (ValueError, IndexError) as exc:
        raise KlickdError(
            KlickdErrorCode.VERSION,
            f"Cannot parse klickd_version: {envelope['klickd_version']}",
        ) from exc

    if major != SUPPORTED_MAJOR:
        raise KlickdError(
            KlickdErrorCode.VERSION,
            f"Unsupported klickd_version major: {envelope['klickd_version']}. "
            f"This library supports v{SUPPORTED_MAJOR}.x.",
        )

    # Reconstruct AAD: JCS over the 6 canonical fields
    envelope_for_aad: dict[str, Any] = {
        "klickd_version": envelope["klickd_version"],
        "encrypted": envelope["encrypted"],
        "domain": envelope["domain"],
        "created_at": envelope["created_at"],
        "kdf": envelope["kdf"],
        "cipher": envelope["cipher"],
    }
    aad: bytes = jcs.canonicalize(envelope_for_aad)

    # Require passphrase
    if not passphrase:
        raise KlickdError(
            KlickdErrorCode.AUTH,
            "A passphrase is required to decrypt this file.",
        )

    # Derive key
    kdf = envelope["kdf"]
    kdf_name: str = kdf.get("name", "")

    if kdf_name == "argon2id":
        try:
            salt = _b64_decode(kdf["salt"])
            params = kdf["params"]
            key = _derive_key_argon2id(passphrase, salt, params["m"], params["t"], params["p"])
        except (KeyError, TypeError) as exc:
            raise KlickdError(KlickdErrorCode.FORMAT, f"Invalid Argon2id KDF params: {exc}") from exc

    elif kdf_name == "pbkdf2-sha256":
        if not legacy:
            raise KlickdError(
                KlickdErrorCode.KDF,
                "Legacy PBKDF2 KDF detected. Set legacy=True to enable reading legacy v2.x files.",
            )
        try:
            salt = _b64_decode(kdf["salt"])
            iterations = kdf["params"]["iterations"]
            key = _derive_key_pbkdf2(passphrase, salt, iterations)
        except (KeyError, TypeError) as exc:
            raise KlickdError(KlickdErrorCode.FORMAT, f"Invalid PBKDF2 KDF params: {exc}") from exc

    else:
        raise KlickdError(KlickdErrorCode.KDF, f"Unknown KDF: '{kdf_name}'.")

    # Decode ciphertext (ciphertext || 16-byte GCM tag, per AESGCM convention)
    try:
        ciphertext_with_tag = _b64_decode(envelope["ciphertext"])
    except Exception as exc:
        raise KlickdError(KlickdErrorCode.FORMAT, f"Invalid ciphertext base64: {exc}") from exc

    if len(ciphertext_with_tag) < 16:
        raise KlickdError(KlickdErrorCode.FORMAT, "Ciphertext too short.")

    # Decrypt AES-256-GCM
    try:
        iv = _b64_decode(envelope["cipher"]["iv"])
    except (KeyError, Exception) as exc:
        raise KlickdError(KlickdErrorCode.FORMAT, f"Invalid cipher IV: {exc}") from exc

    try:
        aesgcm = AESGCM(key)
        plaintext = aesgcm.decrypt(iv, ciphertext_with_tag, aad)
    except InvalidTag as exc:
        raise KlickdError(
            KlickdErrorCode.AUTH,
            "Decryption failed: wrong passphrase or corrupted file.",
        ) from exc

    # Parse payload JSON
    try:
        payload: dict[str, Any] = json.loads(plaintext.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise KlickdError(KlickdErrorCode.FORMAT, f"Decrypted data is not valid JSON: {exc}") from exc

    # Validate payload_schema_version
    if not payload.get("payload_schema_version"):
        raise KlickdError(
            KlickdErrorCode.SCHEMA,
            "Decrypted payload is missing payload_schema_version.",
        )

    return payload
