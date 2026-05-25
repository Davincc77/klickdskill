"""klickd_llamaindex — minimal LlamaIndex adapter for .klickd v4.0.0.

Two integration shapes are demonstrated:

1. ``klickd_to_system_prompt(payload)`` — same shape as the LangChain
   helper, returns a ready-to-inject system string.
2. ``klickd_to_documents(payload)`` — turns the structured fields of a
   `.klickd` profile into LlamaIndex `Document` objects so they can be
   embedded into a vector index alongside the rest of the user's data.

LlamaIndex imports are deferred so this file remains importable without
LlamaIndex installed.

SPDX-License-Identifier: CC0-1.0
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from klickd import load_klickd


def _load_any(file_bytes: bytes, passphrase: str | None = None) -> dict[str, Any]:
    obj = json.loads(file_bytes.decode("utf-8"))
    if isinstance(obj, dict) and (obj.get("encrypted") is True or "ciphertext" in obj):
        return load_klickd(file_bytes, passphrase=passphrase)
    if not isinstance(obj, dict):
        raise ValueError("top-level JSON must be an object")
    return obj


def klickd_to_system_prompt(payload: dict[str, Any]) -> str:
    """Build a system prompt from a decoded .klickd payload (mirrors LangChain helper)."""
    payload = {k: v for k, v in payload.items() if not k.startswith("_")}
    parts: list[str] = []
    if payload.get("user_preferences"):
        parts.append(payload["user_preferences"].strip())
    ctx = payload.get("context") or {}
    ctx_lines = [
        f"current_project: {ctx['current_project']}" if ctx.get("current_project") else None,
        f"current_state: {ctx['current_state']}" if ctx.get("current_state") else None,
        ctx.get("resume_trigger"),
    ]
    ctx_lines = [line for line in ctx_lines if line]
    if ctx_lines:
        parts.append("Resume context:\n" + "\n".join(ctx_lines))
    if payload.get("agent_instructions"):
        parts.append(payload["agent_instructions"].strip())
    return "\n\n".join(parts).strip()


def _doc_records(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Internal: list of {text, metadata} records, before LlamaIndex wrapping."""
    payload = {k: v for k, v in payload.items() if not k.startswith("_")}
    records: list[dict[str, Any]] = []
    base_meta = {
        "source": "klickd",
        "klickd_version": payload.get("klickd_version"),
        "payload_schema_version": payload.get("payload_schema_version"),
        "domain": payload.get("domain"),
        "profile_kind": payload.get("profile_kind"),
    }

    if payload.get("user_preferences"):
        records.append(
            {"text": payload["user_preferences"], "metadata": {**base_meta, "section": "user_preferences"}}
        )

    ctx = payload.get("context") or {}
    if ctx:
        ctx_text_parts = []
        for key in ("summary", "current_project", "current_state", "resume_trigger"):
            if ctx.get(key):
                ctx_text_parts.append(f"{key}: {ctx[key]}")
        if ctx_text_parts:
            records.append(
                {"text": "\n".join(ctx_text_parts), "metadata": {**base_meta, "section": "context"}}
            )

    knowledge = payload.get("knowledge") or {}
    if knowledge:
        kn_parts = []
        if knowledge.get("expertise_level"):
            kn_parts.append(f"expertise_level: {knowledge['expertise_level']}")
        if knowledge.get("mastered"):
            kn_parts.append("mastered: " + ", ".join(map(str, knowledge["mastered"])))
        struggles = knowledge.get("struggles") or []
        if struggles:
            kn_parts.append(
                "struggles: "
                + "; ".join(s.get("topic", "?") if isinstance(s, dict) else str(s) for s in struggles)
            )
        if kn_parts:
            records.append(
                {"text": "\n".join(kn_parts), "metadata": {**base_meta, "section": "knowledge"}}
            )

    for entry in payload.get("memory") or []:
        text = entry.get("content") if isinstance(entry, dict) else None
        if not text:
            continue
        records.append(
            {
                "text": str(text),
                "metadata": {
                    **base_meta,
                    "section": "memory",
                    "memory_id": entry.get("id"),
                    "tags": entry.get("tags"),
                },
            }
        )

    return records


def klickd_to_documents(payload: dict[str, Any]) -> list[Any]:
    """Wrap _doc_records() in `llama_index.core.Document` objects."""
    from llama_index.core import Document  # type: ignore[import-not-found]
    return [Document(text=r["text"], metadata=r["metadata"]) for r in _doc_records(payload)]


def load_klickd_path(path: str | Path, passphrase: str | None = None) -> dict[str, Any]:
    return _load_any(Path(path).read_bytes(), passphrase=passphrase)
