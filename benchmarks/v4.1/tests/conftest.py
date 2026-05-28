"""Shared fixtures + path setup for v4.1 benchmark tests.

The directory name `v4.1` is not a valid Python identifier, so we import
modules from source files directly via importlib.util.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parent.parent


def load(name: str, relpath: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, ROOT / relpath)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


generator = load("v4_1_generator", "fixtures/generator.py")
runner = load("v4_1_runner", "runner/runner.py")
evaluator = load("v4_1_evaluator", "evaluator/evaluator.py")
rfc010 = load("v4_1_rfc010", "reference_runtime/rfc010_reference.py")
