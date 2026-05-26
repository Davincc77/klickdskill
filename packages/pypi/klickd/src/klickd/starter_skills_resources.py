# klickd — starter skill helper
# SPDX-License-Identifier: CC0-1.0
#
# The four v4.0-envelope starter .klickd skills ship as package data under
# klickd/starter_skills/. They are non-normative (see the bundled README).

from __future__ import annotations

import json
from importlib import resources
from importlib.resources.abc import Traversable
from typing import Any


_RESOURCE_PKG = "klickd.starter_skills"


def _root() -> Traversable:
    return resources.files(_RESOURCE_PKG)


def get_starter_skills_dir() -> str:
    """Return the filesystem path to the bundled starter-skills directory.

    For wheels installed normally this resolves to a real path. When the
    package is loaded from a zip importer, callers should prefer the byte /
    manifest accessors which do not require an on-disk path.
    """
    root = _root()
    return str(root)


def list_starter_skills() -> list[str]:
    """Return sorted file names of the bundled .klickd starter skills."""
    return sorted(
        entry.name
        for entry in _root().iterdir()
        if entry.is_file() and entry.name.endswith(".klickd")
    )


def get_starter_skill_bytes(name: str) -> bytes:
    """Return the raw bytes of a bundled starter skill by file name."""
    if not name.endswith(".klickd"):
        raise ValueError(f"starter skill name must end with .klickd: {name!r}")
    if "/" in name or "\\" in name or ".." in name:
        raise ValueError(f"invalid starter skill name: {name!r}")
    return _root().joinpath(name).read_bytes()


def get_starter_skills_manifest() -> dict[str, Any]:
    """Return the bundled manifest.json as a parsed dict."""
    raw = _root().joinpath("manifest.json").read_text(encoding="utf-8")
    return json.loads(raw)
