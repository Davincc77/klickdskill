"""
load_klickd.py — .klickd v2.5 decryption module
=================================================
Reads a .klickd JSON envelope (v2.4 / v2.5) from disk, derives the AES-256
key via PBKDF2-SHA256 (600 000 iterations), and decrypts the payload with
AES-256-GCM.

Envelope fields
---------------
klickd_version : str   e.g. "2.5"
encrypted      : bool  always True for v2.4+
domain         : str   e.g. "general"
created_at     : str   RFC 3339 timestamp, no fractional seconds, Z suffix
kdf_salt       : str   base64-encoded 16-byte PBKDF2 salt
iv             : str   base64-encoded 12-byte GCM nonce
ciphertext     : str   base64-encoded (ciphertext_bytes || 16-byte GCM tag)

AAD (Additional Authenticated Data)
------------------------------------
Canonical JSON of exactly 4 envelope fields:
    {klickd_version, encrypted, domain, created_at}
Sorted keys, no spaces, separators=(',',':'), ensure_ascii=True.
The tag protects both the payload and these 4 metadata fields.

Error classes
-------------
KlickdAuthError        Wrong passphrase / tampered ciphertext (GCM tag mismatch)
KlickdVersionError     Unrecognised major version number
KlickdFormatError      Malformed file, bad base64, missing fields, etc.
"""

import base64
import hashlib
import json
import os
import warnings
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.exceptions import InvalidTag


# ---------------------------------------------------------------------------
# Public error classes
# ---------------------------------------------------------------------------

class KlickdAuthError(Exception):
    """Raised when AES-GCM authentication fails (wrong passphrase or tampered data)."""


class KlickdVersionError(Exception):
    """Raised when the envelope contains an unrecognised major version."""


class KlickdFormatError(Exception):
    """Raised when the envelope is structurally invalid (missing/malformed fields)."""


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_REQUIRED_FIELDS = ("klickd_version", "encrypted", "domain", "created_at",
                    "kdf_salt", "iv", "ciphertext")

_SUPPORTED_MAJOR_VERSIONS = {2}  # extend as new major versions land

_MIN_PASSPHRASE_WARN = 12   # chars — emit a warning below this
_GCM_TAG_BYTES = 16


def _decode_b64(field_name: str, value: str) -> bytes:
    """Decode a standard (RFC 4648 §4) base64 string; raise KlickdFormatError on failure."""
    try:
        return base64.b64decode(value, validate=True)
    except Exception as exc:
        raise KlickdFormatError(
            f"Field '{field_name}' contains invalid base64: {exc}"
        ) from exc


def _derive_key(passphrase: str, salt: bytes) -> bytes:
    """Derive a 32-byte AES key from *passphrase* and *salt* using PBKDF2-SHA256."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=600_000,
    )
    return kdf.derive(passphrase.encode("utf-8"))


def _build_aad(envelope: dict) -> bytes:
    """
    Build Additional Authenticated Data from the 4 canonical envelope fields.

    AAD = canonical JSON of {klickd_version, encrypted, domain, created_at}
          sorted keys, separators=(',',':'), ensure_ascii=True.
    """
    aad_dict = {
        "klickd_version": envelope["klickd_version"],
        "encrypted":      envelope["encrypted"],
        "domain":         envelope["domain"],
        "created_at":     envelope["created_at"],
    }
    return json.dumps(aad_dict, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True).encode("utf-8")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_klickd(filepath: str, passphrase: str) -> dict:
    """
    Decrypt a .klickd v2.4/v2.5 file and return the plaintext payload dict.

    Parameters
    ----------
    filepath : str
        Path to the .klickd file.
    passphrase : str
        Passphrase used when the file was created.

    Returns
    -------
    dict
        Decrypted JSON payload.

    Raises
    ------
    KlickdFormatError
        If the file cannot be parsed, required fields are missing, or base64
        values are malformed.
    KlickdVersionError
        If the envelope major version is not supported.
    KlickdAuthError
        If AES-GCM authentication fails (wrong passphrase or tampered data).

    Warns
    -----
    UserWarning
        If *passphrase* is shorter than 12 characters.
    """
    # --- passphrase strength hint -------------------------------------------
    if len(passphrase) < _MIN_PASSPHRASE_WARN:
        warnings.warn(
            f"Passphrase is only {len(passphrase)} characters; "
            "a minimum of 12 is recommended.",
            UserWarning,
            stacklevel=2,
        )

    # --- load & parse file ---------------------------------------------------
    path = Path(filepath).expanduser()
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise KlickdFormatError(f"Cannot read file '{filepath}': {exc}") from exc

    try:
        envelope = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise KlickdFormatError(f"File is not valid JSON: {exc}") from exc

    if not isinstance(envelope, dict):
        raise KlickdFormatError("Envelope must be a JSON object.")

    # --- required fields -----------------------------------------------------
    for field in _REQUIRED_FIELDS:
        if field not in envelope:
            raise KlickdFormatError(f"Missing required field: '{field}'")

    # --- version check -------------------------------------------------------
    version_str = envelope["klickd_version"]
    try:
        major = int(str(version_str).split(".")[0])
    except (ValueError, AttributeError) as exc:
        raise KlickdVersionError(
            f"Cannot parse major version from '{version_str}'"
        ) from exc

    if major not in _SUPPORTED_MAJOR_VERSIONS:
        raise KlickdVersionError(
            f"Unsupported major version {major} (supported: "
            f"{sorted(_SUPPORTED_MAJOR_VERSIONS)})"
        )

    # --- decode base64 fields ------------------------------------------------
    salt_bytes   = _decode_b64("kdf_salt",   envelope["kdf_salt"])
    iv_bytes     = _decode_b64("iv",          envelope["iv"])
    cipher_bytes = _decode_b64("ciphertext",  envelope["ciphertext"])

    # --- validate ciphertext length ------------------------------------------
    if len(cipher_bytes) < _GCM_TAG_BYTES:
        raise KlickdFormatError(
            f"Ciphertext too short ({len(cipher_bytes)} bytes); "
            f"must be at least {_GCM_TAG_BYTES} bytes (GCM tag alone)."
        )

    # --- derive key ----------------------------------------------------------
    key = _derive_key(passphrase, salt_bytes)

    # --- build AAD (4 fields) ------------------------------------------------
    aad = _build_aad(envelope)

    # --- decrypt AES-256-GCM -------------------------------------------------
    # ciphertext field = ciphertext_bytes || 16-byte tag  (cryptography lib
    # expects the tag appended at the end, which is exactly our layout).
    aesgcm = AESGCM(key)
    try:
        plaintext = aesgcm.decrypt(iv_bytes, cipher_bytes, aad)
    except InvalidTag as exc:
        raise KlickdAuthError(
            "AES-GCM authentication failed — wrong passphrase or tampered data."
        ) from exc

    # --- parse payload -------------------------------------------------------
    try:
        payload = json.loads(plaintext.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise KlickdFormatError(f"Decrypted payload is not valid JSON: {exc}") from exc

    # --- post-process known fields ------------------------------------------
    # Use display_name (not name) for identity display
    identity = payload.get("identity", {})
    display_name = identity.get("display_name")  # correct field name

    # Resolve memory path — default to ~/.klickd/memory/ (not /.memory/)
    memory_path = payload.get(
        "memory_path",
        str(Path.home() / ".klickd" / "memory")
    )
    payload.setdefault("_resolved_memory_path", os.path.expanduser(memory_path))

    return payload
