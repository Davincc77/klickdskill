# klickd — Official Python library for .klickd portable AI context files
# SPDX-License-Identifier: CC0-1.0
#
# One soul. Any model. Any body.
#
# Repository: https://github.com/Davincc77/klickdskill
# DOI:        https://doi.org/10.5281/zenodo.20262530

from .decode import load_klickd
from .encode import save_klickd
from .errors import KlickdError, KlickdErrorCode, HTTP_STATUS
from .migrate import (
    migrate_payload,
    migrate_payload_iter_warnings,
    needs_migration,
)
from .validate import validate, validate_iter_errors
from ._types import (
    KlickdPayload,
    KlickdEnvelope,
    KlickdMemoryEntry,
    KlickdIdentity,
    KlickdContext,
    KlickdKnowledge,
    KlickdMediaProfileEntry,
    KlickdMediaProfileV1,
    KlickdGateEntry,
    KlickdVerificationGatesV1,
    KlickdHumanVetoPolicy,
    KlickdClaimSources,
    KlickdMigrationV1,
)

__version__ = "4.0.0a1"
__all__ = [
    "load_klickd",
    "save_klickd",
    "validate",
    "validate_iter_errors",
    "migrate_payload",
    "migrate_payload_iter_warnings",
    "needs_migration",
    "KlickdError",
    "KlickdErrorCode",
    "HTTP_STATUS",
    "KlickdPayload",
    "KlickdEnvelope",
    "KlickdMemoryEntry",
    "KlickdIdentity",
    "KlickdContext",
    "KlickdKnowledge",
    "KlickdMediaProfileEntry",
    "KlickdMediaProfileV1",
    "KlickdGateEntry",
    "KlickdVerificationGatesV1",
    "KlickdHumanVetoPolicy",
    "KlickdClaimSources",
    "KlickdMigrationV1",
    "__version__",
]
