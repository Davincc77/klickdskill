# .klickd v3 — Python TypedDict definitions
# SPDX-License-Identifier: CC0-1.0

from __future__ import annotations

from typing import Any, List, Literal, Optional
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


class KlickdPayload(TypedDict, total=False):
    payload_schema_version: Required[str]
    domain_schema_version: Required[str]
    identity: KlickdIdentity
    agent_instructions: str
    user_preferences: dict
    context: KlickdContext
    knowledge: KlickdKnowledge
    memory: List[KlickdMemoryEntry]
