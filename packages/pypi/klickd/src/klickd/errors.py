# .klickd error definitions
# SPDX-License-Identifier: CC0-1.0

from enum import Enum


class KlickdErrorCode(str, Enum):
    AUTH = "KLICKD_E_AUTH"          # Wrong passphrase / GCM tag mismatch
    VERSION = "KLICKD_E_VERSION"    # Unsupported klickd_version major
    FORMAT = "KLICKD_E_FORMAT"      # Malformed envelope JSON / missing fields
    KDF = "KLICKD_E_KDF"            # Unknown/unsupported KDF
    WEAK_PASS = "KLICKD_E_WEAK_PASS"  # Passphrase < 8 characters
    SCHEMA = "KLICKD_E_SCHEMA"      # Missing payload_schema_version


HTTP_STATUS: dict[KlickdErrorCode, int] = {
    KlickdErrorCode.AUTH: 401,
    KlickdErrorCode.VERSION: 400,
    KlickdErrorCode.FORMAT: 400,
    KlickdErrorCode.KDF: 400,
    KlickdErrorCode.WEAK_PASS: 422,
    KlickdErrorCode.SCHEMA: 400,
}


class KlickdError(Exception):
    """Raised for all .klickd format and cryptographic errors."""

    def __init__(self, code: KlickdErrorCode, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.http_status: int = HTTP_STATUS[code]
