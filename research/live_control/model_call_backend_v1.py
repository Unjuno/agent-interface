"""Explicit model-call backend seam for the integrated-efficiency runner.

The legacy WSL/Windows caller remains the default. A non-legacy backend must be
named explicitly and expose a compatible call function; missing or invalid
configuration fails closed before any model call.
"""
from __future__ import annotations

import importlib
import os
from collections.abc import Callable
from typing import Any


def resolve(default_call: Callable[..., Any]) -> Callable[..., Any]:
    module = _selected_module()
    if module is None:
        return default_call
    selected = getattr(module, "call", None)
    if not callable(selected):
        raise RuntimeError("STOP_MODEL_BACKEND_MISSING_CALL:" + module.__name__)
    return selected


def _selected_module():
    backend = os.environ.get("AGENT_INTERFACE_MODEL_BACKEND", "legacy")
    if backend == "legacy":
        return None
    if backend != "module":
        raise RuntimeError("STOP_MODEL_BACKEND_UNSUPPORTED:" + backend)
    module_name = os.environ.get("AGENT_INTERFACE_MODEL_CALL_MODULE", "")
    if not module_name:
        raise RuntimeError("STOP_MODEL_BACKEND_UNCONFIGURED")
    return importlib.import_module(module_name)


def resolve_preflight_call(default_call: Callable[..., Any]) -> Callable[..., Any]:
    """Resolve the no-image schema-probe transport independently of task calls."""
    module = _selected_module()
    if module is None:
        return default_call
    selected = getattr(module, "preflight_call", None)
    if not callable(selected):
        raise RuntimeError("STOP_MODEL_BACKEND_MISSING_PREFLIGHT_CALL:" + module.__name__)
    return selected


def resolve_preflight_identity(default_identity: Callable[..., Any]) -> Callable[..., Any]:
    """Resolve cache identity for the selected schema-probe transport."""
    module = _selected_module()
    if module is None:
        return default_identity
    selected = getattr(module, "preflight_identity", None)
    if not callable(selected):
        raise RuntimeError("STOP_MODEL_BACKEND_MISSING_PREFLIGHT_IDENTITY:" + module.__name__)
    return selected
