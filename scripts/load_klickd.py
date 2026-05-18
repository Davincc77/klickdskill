#!/usr/bin/env python3
"""
NOTICE: This file is a v2.5-era legacy script, retained for historical reference only.

The canonical v3.0 implementation is at the repository root:
  load_klickd.py   — decoder (v2.x + v3.0, Argon2id + PBKDF2)
  save_klickd.py   — encoder (v3.0 default, Argon2id)

SKILL.md frontmatter tools.script now correctly points to load_klickd.py (root).
Do not use this file for new implementations.
"""
import sys, os
# Redirect to root implementation
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root)
print("WARNING: scripts/load_klickd.py is deprecated. Use root load_klickd.py instead.", file=sys.stderr)
from load_klickd import *  # noqa: F401,F403 — re-export for backward compat
