"""Side-effect-free native platform probes for Agent Interface.

These probes report native API and permission evidence only. They never emit
keyboard/pointer input, capture a screenshot, or grant side-effect authority.
"""
from __future__ import annotations

import ctypes
import ctypes.util
import os
import platform
from typing import Any, Mapping

from runtime.core_v1.platform_probe import probe_platform

SCHEMA = "agent-interface/native-platform-probe-v1"


def _base(os_name: str, backend: str) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "os": os_name,
        "candidate_backend": backend,
        "applicable": True,
        "support_claim": False,
        "input_authority": "none",
        "capture_authority": "none",
        "native_api": {},
        "permissions": {},
        "observations": {},
    }


def probe_windows(*, system: str | None = None) -> dict[str, Any]:
    actual = platform.system() if system is None else system
    row = _base("windows", "win32")
    if actual != "Windows":
        row.update(applicable=False, reason="not_windows")
        return row
    try:
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        row["native_api"] = {
            "user32": True,
            "SendInput": hasattr(user32, "SendInput"),
            "GetForegroundWindow": hasattr(user32, "GetForegroundWindow"),
            "GetSystemMetrics": hasattr(user32, "GetSystemMetrics"),
        }
        width = int(user32.GetSystemMetrics(0)) if hasattr(user32, "GetSystemMetrics") else 0
        height = int(user32.GetSystemMetrics(1)) if hasattr(user32, "GetSystemMetrics") else 0
        foreground = int(user32.GetForegroundWindow() or 0) if hasattr(user32, "GetForegroundWindow") else 0
        row["observations"] = {
            "screen_width": width,
            "screen_height": height,
            "foreground_window_nonzero": bool(foreground),
        }
        # Windows has no single permission bit equivalent to macOS Accessibility.
        # Session/interactivity and actual effects remain unknown until integration.
        row["permissions"] = {"desktop_automation": "unknown"}
    except Exception as error:
        row["native_api"] = {"user32": False}
        row["observations"] = {"probe_error": type(error).__name__}
        row["permissions"] = {"desktop_automation": "unknown"}
    return row


def _load_framework(name: str):
    candidates = [
        ctypes.util.find_library(name),
        f"/System/Library/Frameworks/{name}.framework/{name}",
    ]
    for candidate in candidates:
        if not candidate:
            continue
        try:
            return ctypes.CDLL(candidate)
        except OSError:
            continue
    return None


def probe_macos(*, system: str | None = None) -> dict[str, Any]:
    actual = platform.system() if system is None else system
    row = _base("macos", "quartz")
    if actual != "Darwin":
        row.update(applicable=False, reason="not_macos")
        return row

    core_graphics = _load_framework("CoreGraphics")
    app_services = _load_framework("ApplicationServices")
    row["native_api"] = {
        "CoreGraphics": core_graphics is not None,
        "ApplicationServices": app_services is not None,
    }

    width = height = None
    screen_preflight: bool | None = None
    accessibility_trusted: bool | None = None
    if core_graphics is not None:
        try:
            core_graphics.CGMainDisplayID.restype = ctypes.c_uint32
            display_id = int(core_graphics.CGMainDisplayID())
            if hasattr(core_graphics, "CGDisplayPixelsWide"):
                core_graphics.CGDisplayPixelsWide.argtypes = [ctypes.c_uint32]
                core_graphics.CGDisplayPixelsWide.restype = ctypes.c_size_t
                width = int(core_graphics.CGDisplayPixelsWide(display_id))
            if hasattr(core_graphics, "CGDisplayPixelsHigh"):
                core_graphics.CGDisplayPixelsHigh.argtypes = [ctypes.c_uint32]
                core_graphics.CGDisplayPixelsHigh.restype = ctypes.c_size_t
                height = int(core_graphics.CGDisplayPixelsHigh(display_id))
            if hasattr(core_graphics, "CGPreflightScreenCaptureAccess"):
                core_graphics.CGPreflightScreenCaptureAccess.restype = ctypes.c_bool
                screen_preflight = bool(core_graphics.CGPreflightScreenCaptureAccess())
        except Exception:
            pass
    if app_services is not None and hasattr(app_services, "AXIsProcessTrusted"):
        try:
            app_services.AXIsProcessTrusted.restype = ctypes.c_bool
            accessibility_trusted = bool(app_services.AXIsProcessTrusted())
        except Exception:
            pass

    row["observations"] = {
        "screen_width": width,
        "screen_height": height,
    }
    row["permissions"] = {
        "accessibility": (
            "granted" if accessibility_trusted is True
            else "required" if accessibility_trusted is False
            else "unknown"
        ),
        "screen_recording": (
            "granted" if screen_preflight is True
            else "required" if screen_preflight is False
            else "unknown"
        ),
    }
    return row


def probe_linux(*, system: str | None = None, env: Mapping[str, str] | None = None) -> dict[str, Any]:
    actual = platform.system() if system is None else system
    if actual != "Linux":
        row = _base("linux", "none")
        row.update(applicable=False, reason="not_linux")
        return row
    generic = probe_platform(system="Linux", env=os.environ if env is None else env)
    row = _base("linux", str(generic["candidate_backend"]))
    row["observations"] = {
        "session": generic["session"],
        "permission_hints": list(generic["permission_hints"]),
    }
    row["native_api"] = {
        "x11_candidate_integrated": generic["candidate_backend"] == "x11",
        "wayland_candidate_only": generic["candidate_backend"] == "wayland",
    }
    row["permissions"] = {"graphical_session": "observed" if generic["session"] else "missing"}
    return row


def probe_native(*, system: str | None = None, env: Mapping[str, str] | None = None) -> dict[str, Any]:
    actual = platform.system() if system is None else system
    if actual == "Windows":
        return probe_windows(system=actual)
    if actual == "Darwin":
        return probe_macos(system=actual)
    if actual == "Linux":
        return probe_linux(system=actual, env=env)
    row = _base("unknown", "unsupported-host")
    row.update(applicable=False, reason=f"unsupported_system:{actual}")
    return row
