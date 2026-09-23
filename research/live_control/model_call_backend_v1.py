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
    backend = os.environ.get("AGENT_INTERFACE_MODEL_BACKEND", "legacy")
    if backend == "legacy":
        return default_call
    if backend != "module":
        raise RuntimeError("STOP_MODEL_BACKEND_UNSUPPORTED:" + backend)
    module_name = os.environ.get("AGENT_INTERFACE_MODEL_CALL_MODULE", "")
    if not module_name:
        raise RuntimeError("STOP_MODEL_BACKEND_UNCONFIGURED")
    module = importlib.import_module(module_name)
    selected = getattr(module, "call", None)
    if not callable(selected):
        raise RuntimeError("STOP_MODEL_BACKEND_MISSING_CALL:" + module_name)
    return selected
