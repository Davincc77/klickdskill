"""
save_klickd.py — .klickd v2.5 encryption module
================================================
Encrypts a Python dict payload with AES-256-GCM and writes a .klickd v2.5
JSON envelope to disk.

Envelope layout (all bytes fields are standard base64, RFC 4648 §4)
--------------------------------------------------------------------
klickd_version : "2.5"
encrypted      : true
domain         : str   caller-supplied, e.g. "general"
created_at     : str   UTC, RFC 3339, YYYY-MM-DDTHH:MM:SSZ (no fractional sec)
kdf_salt       : base64(16 random bytes) — PBKDF2-SHA256 salt
iv             : base64(12 random bytes) — AES-GCM nonce
ciphertext     : base64(ciphertext_bytes || 16-byte GCM tag)

AAD (Additional Authenticated Data)
-------------------------------------
Canonical JSON of exactly 4 fields:
    {klickd_version, encrypted, domain, created_at}
sorted keys, separators=(',',':'), ensure_ascii=True.
This matches the AAD that load_klickd.py expects.

Error classes (imported from load_klickd)
------------------------------------------
KlickdWeakPassphraseError  passphrase < 8 chars (hard reject)
(KlickdAuthError, KlickdVersionError, KlickdFormatError also re-exported)
"""

import base64
import json
import os
import uuid
import warnings
from datetime import datetime, timezone
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

# Shared error classes from load_klickd
from load_klickd import KlickdAuthError, KlickdVersionError, KlickdFormatError  # noqa: F401


# ---------------------------------------------------------------------------
# Additional error class
# ---------------------------------------------------------------------------

class KlickdWeakPassphraseError(Exception):
    """Raised when the passphrase is too short to meet the minimum security bar."""


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_KLICKD_VERSION   = "2.5"
_KDF_ITERATIONS   = 600_000
_KEY_BYTES        = 32
_SALT_BYTES       = 16
_IV_BYTES         = 12
_GCM_TAG_BYTES    = 16

_MIN_PASSPHRASE_REJECT = 8    # hard reject below this
_MIN_PASSPHRASE_WARN   = 12   # warn below this


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _derive_key(passphrase: str, salt: bytes) -> bytes:
    """Derive a 32-byte AES key via PBKDF2-SHA256 (600 000 iterations)."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=_KEY_BYTES,
        salt=salt,
        iterations=_KDF_ITERATIONS,
    )
    return kdf.derive(passphrase.encode("utf-8"))


def _build_aad(klickd_version: str, encrypted: bool,
               domain: str, created_at: str) -> bytes:
    """
    Build Additional Authenticated Data for the 4 canonical envelope fields.

    Canonical JSON: sorted keys, no spaces, ensure_ascii=True.
    """
    aad_dict = {
        "klickd_version": klickd_version,
        "encrypted":      encrypted,
        "domain":         domain,
        "created_at":     created_at,
    }
    return json.dumps(aad_dict, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True).encode("utf-8")


def _utc_now_rfc3339() -> str:
    """Return current UTC time as YYYY-MM-DDTHH:MM:SSZ (no fractional seconds)."""
    now = datetime.now(timezone.utc)
    return now.strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def save_klickd(
    payload: dict,
    passphrase: str,
    domain: str = "general",
    filepath: str = None,
) -> str:
    """
    Encrypt *payload* and write a .klickd v2.5 envelope to *filepath*.

    Parameters
    ----------
    payload : dict
        Arbitrary JSON-serialisable dict to encrypt.
    passphrase : str
        Encryption passphrase.  Must be >= 8 characters; >= 12 recommended.
    domain : str, optional
        Logical domain tag stored in the envelope (default: "general").
    filepath : str, optional
        Destination path.  If None, a UUID-named file is created under
        ``~/.klickd/memory/``.

    Returns
    -------
    str
        Absolute path to the written file.

    Raises
    ------
    KlickdWeakPassphraseError
        If *passphrase* is shorter than 8 characters.
    KlickdFormatError
        If *payload* is not JSON-serialisable.

    Warns
    -----
    UserWarning
        If *passphrase* is shorter than 12 characters.
    """
    # --- passphrase enforcement ---------------------------------------------
    if len(passphrase) < _MIN_PASSPHRASE_REJECT:
        raise KlickdWeakPassphraseError(
            f"Passphrase must be at least {_MIN_PASSPHRASE_REJECT} characters "
            f"(got {len(passphrase)})."
        )

    if len(passphrase) < _MIN_PASSPHRASE_WARN:
        warnings.warn(
            f"Passphrase is only {len(passphrase)} characters; "
            "a minimum of 12 is recommended.",
            UserWarning,
            stacklevel=2,
        )

    # --- serialise payload --------------------------------------------------
    try:
        plaintext = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise KlickdFormatError(f"Payload is not JSON-serialisable: {exc}") from exc

    # --- CSPRNG material ----------------------------------------------------
    salt = os.urandom(_SALT_BYTES)
    iv   = os.urandom(_IV_BYTES)

    # --- timestamp ----------------------------------------------------------
    created_at = _utc_now_rfc3339()

    # --- derive key ---------------------------------------------------------
    key = _derive_key(passphrase, salt)

    # --- build AAD (4 fields) -----------------------------------------------
    aad = _build_aad(_KLICKD_VERSION, True, domain, created_at)

    # --- encrypt AES-256-GCM ------------------------------------------------
    aesgcm = AESGCM(key)
    # cryptography lib appends the 16-byte GCM tag at the end automatically
    cipher_bytes = aesgcm.encrypt(iv, plaintext, aad)
    # cipher_bytes = ciphertext_bytes || 16-byte tag  ✓

    # --- base64-encode (RFC 4648 §4, standard padded) -----------------------
    kdf_salt_b64  = base64.b64encode(salt).decode("ascii")
    iv_b64        = base64.b64encode(iv).decode("ascii")
    ciphertext_b64 = base64.b64encode(cipher_bytes).decode("ascii")

    # --- build envelope -----------------------------------------------------
    envelope = {
        "klickd_version": _KLICKD_VERSION,
        "encrypted":      True,
        "domain":         domain,
        "created_at":     created_at,
        "kdf_salt":       kdf_salt_b64,
        "iv":             iv_b64,
        "ciphertext":     ciphertext_b64,
    }

    # --- resolve output path ------------------------------------------------
    if filepath is None:
        default_dir = Path.home() / ".klickd" / "memory"
        default_dir.mkdir(parents=True, exist_ok=True)
        filepath = str(default_dir / f"{uuid.uuid4()}.klickd")

    out_path = Path(filepath).expanduser()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # --- write file ---------------------------------------------------------
    out_path.write_text(
        json.dumps(envelope, indent=2, ensure_ascii=True),
        encoding="utf-8",
    )

    return str(out_path.resolve())
