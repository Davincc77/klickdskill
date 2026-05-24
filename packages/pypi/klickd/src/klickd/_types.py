# .klickd v3 — Python TypedDict definitions
# SPDX-License-Identifier: CC0-1.0

from __future__ import annotations

from typing import Any, List, Literal, Optional, Union
from typing_extensions import TypedDict, Required


class KlickdKdfArgon2idParams(TypedDict):
    m: int
    t: int
    p: int


class KlickdKdfArgon2id(TypedDict):
    name: Literal["argon2id"]
    params: KlickdKdfArgon2idParams
    salt: str  # base64


class KlickdKdfPbkdf2Params(TypedDict):
    iterations: int


class KlickdKdfPbkdf2(TypedDict):
    name: Literal["pbkdf2-sha256"]
    params: KlickdKdfPbkdf2Params
    salt: str  # base64


class KlickdCipher(TypedDict):
    name: Literal["AES-256-GCM"]
    iv: str  # base64


class KlickdEnvelope(TypedDict, total=False):
    klickd_version: Required[str]
    encrypted: Required[bool]
    domain: Required[str]
    created_at: Required[str]       # RFC 3339 UTC Z
    kdf: Required[dict]             # KlickdKdfArgon2id | KlickdKdfPbkdf2
    cipher: Required[KlickdCipher]
    ciphertext: Required[str]       # base64


class KlickdMemoryEntry(TypedDict, total=False):
    id: Required[str]               # UUID v4
    ts: Required[str]               # RFC 3339 UTC Z
    role: Required[str]             # user | assistant | system
    content: Required[str]
    modality: Required[str]         # text | image | audio | tool_call
    tags: List[str]


class KlickdIdentity(TypedDict, total=False):
    name: str
    language: str
    timezone: str
    communication_style: str


class KlickdContext(TypedDict, total=False):
    current_state: str
    decisions_locked: List[str]
    artifacts: List[Any]
    summary: str


class KlickdKnowledge(TypedDict, total=False):
    mastered: List[str]
    gaps: List[str]
    next_steps: List[str]


class KlickdMediaProfileEntryHash(TypedDict):
    algo: Literal["blake3"]
    value: str


class KlickdMediaProfileEntry(TypedDict, total=False):
    id: Required[str]
    modality: Required[Literal["voice", "image", "document", "embedding"]]
    hash: Required[KlickdMediaProfileEntryHash]
    label: str
    language: str
    uri: str
    media_type: str
    byte_size: int
    duration_ms: int
    bytes_b64: str
    producer: dict
    consent: dict


class KlickdMediaProfileV1(TypedDict, total=False):
    version: Required[Literal[1]]
    entries: Required[List[KlickdMediaProfileEntry]]


KlickdGateLevel = Literal["silent", "warn", "confirm", "block", "require-owner"]


class KlickdGateEntry(TypedDict, total=False):
    action_class: Required[str]
    level: Required[KlickdGateLevel]
    id: str
    reason: str


class KlickdVerificationGatesV1(TypedDict, total=False):
    version: Required[Literal[1]]
    gates: Required[List[KlickdGateEntry]]
    user_default: KlickdGateLevel


class KlickdHumanVetoPolicy(TypedDict, total=False):
    applies_to: List[str]
    second_party: Optional[str]
    min_level: KlickdGateLevel
    rationale: str


class KlickdClaimSources(TypedDict, total=False):
    prefer: List[str]
    require_citation_for: List[str]
    records: List[Any]


class KlickdMigrationV1(TypedDict, total=False):
    source_version: str
    migrated_at: str
    migration_report_ref: str
    backup_ref: str


class KlickdPayload(TypedDict, total=False):
    payload_schema_version: Required[str]
    domain_schema_version: Required[str]
    identity: KlickdIdentity
    agent_instructions: str
    # Canonical type = str (SPEC.md §22.6, max 32,768 bytes UTF-8).
    # dict retained for backward compatibility with pre-v3.4 files.
    user_preferences: Union[str, dict]
    context: KlickdContext
    knowledge: KlickdKnowledge
    memory: List[KlickdMemoryEntry]
    # v4 additive surface (preview + GA). Strict shape on v1-frozen fields.
    profile_kind: str
    preview: str
    onboarding_trigger: str
    media_profile: Union[KlickdMediaProfileV1, dict]
    verification_gates: Union[KlickdVerificationGatesV1, dict]
    human_veto_policy: Optional[KlickdHumanVetoPolicy]
    claim_sources: Optional[KlickdClaimSources]
    migration: Optional[KlickdMigrationV1]
    risk_thresholds: Optional[dict]
    preflight_checks: Optional[List[Any]]
    error_journal: Optional[List[Any]]
    verification_artifacts: Optional[List[Any]]
    contract_tests: Optional[List[Any]]
    success_criteria: Optional[Any]
    reversibility: Optional[dict]
    blast_radius: Optional[dict]
    context_cost: Optional[dict]
    gaming_profile: Optional[dict]
    deprecated_fields: Optional[List[Any]]
