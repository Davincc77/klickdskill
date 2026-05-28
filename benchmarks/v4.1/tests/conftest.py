"""Shared fixtures + path setup for v4.1 benchmark tests.

The directory name `v4.1` is not a valid Python identifier, so we import
modules from source files directly via importlib.util. The providers and
prompts packages are loaded under a synthetic top-level ``_v4_1_pkg`` so
their internal relative imports resolve.
"""
from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parent.parent


def _register_pkg(name: str) -> None:
    if name in sys.modules:
        return
    pkg = types.ModuleType(name)
    pkg.__path__ = [str(ROOT)]
    sys.modules[name] = pkg


def _load_pkg(full_name: str, init_path: Path, search_dir: Path) -> ModuleType:
    if full_name in sys.modules:
        return sys.modules[full_name]
    spec = importlib.util.spec_from_file_location(
        full_name, init_path,
        submodule_search_locations=[str(search_dir)],
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[full_name] = mod
    spec.loader.exec_module(mod)
    return mod


def _load_module(full_name: str, file_path: Path) -> ModuleType:
    if full_name in sys.modules:
        return sys.modules[full_name]
    spec = importlib.util.spec_from_file_location(full_name, file_path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[full_name] = mod
    spec.loader.exec_module(mod)
    return mod


def load(name: str, relpath: str) -> ModuleType:
    return _load_module(name, ROOT / relpath)


# Standalone modules used by older tests.
generator = load("v4_1_generator", "fixtures/generator.py")
evaluator = load("v4_1_evaluator", "evaluator/evaluator.py")
rfc010 = load("v4_1_rfc010", "reference_runtime/rfc010_reference.py")

# Package-relative modules (providers, prompts, executor) need the synthetic
# parent package so ``..providers`` style imports resolve at runtime.
_register_pkg("_v4_1_pkg")
providers = _load_pkg(
    "_v4_1_pkg.providers", ROOT / "providers" / "__init__.py", ROOT / "providers"
)
prompts = _load_pkg(
    "_v4_1_pkg.prompts", ROOT / "prompts" / "__init__.py", ROOT / "prompts"
)
_register_pkg("_v4_1_pkg.runner")
sys.modules["_v4_1_pkg.runner"].__path__ = [str(ROOT / "runner")]
runner = _load_module("_v4_1_pkg.runner.runner", ROOT / "runner" / "runner.py")
executor = _load_module("_v4_1_pkg.runner.executor", ROOT / "runner" / "executor.py")
audit = _load_module("_v4_1_pkg.runner.audit", ROOT / "runner" / "audit.py")
