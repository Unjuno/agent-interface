"""Backend protocol boundary for the promoted portable runtime core.

Implementations may be X11, Wayland, Win32, Quartz, or future backends. The
semantic core never imports platform-native modules directly.
"""
from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Backend(Protocol):
    """Minimum product-side interface expected of a native backend."""

    def manifest(self) -> dict[str, Any]: ...
    def monotonic_ns(self) -> int: ...
    def execute(self, program: dict[str, Any]) -> dict[str, Any]: ...
    def release_all(self) -> dict[str, Any]: ...


class BackendUnavailable(RuntimeError):
    """Raised when no backend can safely satisfy the requested operation."""
