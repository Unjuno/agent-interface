"""Fail-closed selector for promoted native runtime backends."""
from __future__ import annotations

from dataclasses import dataclass
import os
import sys
from typing import Mapping


class BackendUnavailable(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class BackendPlan:
    platform: str
    backend_id: str | None
    available: bool
    reason: str
    target_kind: str | None
    side_effect_authority: bool


def _env(value: Mapping[str, str] | None) -> Mapping[str, str]:
    return os.environ if value is None else value


def select_backend(platform: str | None = None, environ: Mapping[str, str] | None = None) -> BackendPlan:
    platform = sys.platform if platform is None else platform
    env = _env(environ)
    if platform.startswith("linux"):
        if env.get("DISPLAY"):
            return BackendPlan("linux", "x11-v1", True, "promoted X11 backend available", "x11_window_id", False)
        if env.get("WAYLAND_DISPLAY"):
            return BackendPlan("linux", None, False, "WAYLAND_BACKEND_NOT_PROMOTED", None, False)
        return BackendPlan("linux", None, False, "NO_INTERACTIVE_DISPLAY", None, False)
    if platform == "win32":
        return BackendPlan("windows", "win32-v1", True, "promoted Win32 backend available", "hwnd", False)
    if platform == "darwin":
        return BackendPlan("macos", "quartz-v1", True, "promoted Quartz backend available subject to TCC", "pid", False)
    return BackendPlan(platform, None, False, "UNSUPPORTED_PLATFORM", None, False)


def validate_targets(targets: Mapping[str, int]) -> dict[str, int]:
    if not isinstance(targets, Mapping) or not targets:
        raise BackendUnavailable("explicit target registry is required")
    normalized: dict[str, int] = {}
    for name, value in targets.items():
        if not isinstance(name, str) or not name or len(name) > 64:
            raise BackendUnavailable("invalid target name")
        if type(value) is not int or value <= 0:
            raise BackendUnavailable(f"invalid target identity for {name}")
        normalized[name] = value
    return normalized


def open_session(targets: Mapping[str, int], *, display_name: str | None = None):
    """Open the promoted backend for the *actual* host only.

    This function intentionally has no platform override: tests may inspect
    foreign selection plans, but cannot instantiate a foreign backend and
    thereby create a false support result.
    """
    registry = validate_targets(targets)
    selection_env = dict(os.environ)
    if display_name is not None:
        if not isinstance(display_name, str) or not display_name.strip():
            raise BackendUnavailable("explicit display must be a nonempty string")
        selection_env["DISPLAY"] = display_name
    plan = select_backend(environ=selection_env)
    if not plan.available or plan.backend_id is None:
        raise BackendUnavailable(plan.reason)

    if plan.backend_id == "x11-v1":
        display = display_name or os.environ.get("DISPLAY")
        if not display:
            raise BackendUnavailable("X11 DISPLAY is required")
        try:
            from runtime.backends.x11_v1.backend import X11Backend
            from runtime.backends.x11_v1.session import X11RuntimeSession
        except Exception as error:
            raise BackendUnavailable(f"X11 backend dependency unavailable: {error}") from error
        return X11RuntimeSession(X11Backend(display, registry))

    if plan.backend_id == "win32-v1":
        try:
            from runtime.backends.win32_v1.backend import Win32Backend
            from runtime.backends.win32_v1.session import Win32RuntimeSession
        except Exception as error:
            raise BackendUnavailable(f"Win32 backend unavailable: {error}") from error
        return Win32RuntimeSession(Win32Backend(registry))

    if plan.backend_id == "quartz-v1":
        try:
            from runtime.backends.quartz_v1.backend import QuartzBackend
            from runtime.backends.quartz_v1.session import QuartzRuntimeSession
        except Exception as error:
            raise BackendUnavailable(f"Quartz backend unavailable: {error}") from error
        return QuartzRuntimeSession(QuartzBackend(registry))

    raise BackendUnavailable(f"unhandled promoted backend {plan.backend_id}")
