"""Side-effect-free host/platform probe.

Environment presence is reported as evidence for selecting a backend candidate,
not as a support claim and not as permission to emit input.
"""
from __future__ import annotations

import os
import platform
from typing import Mapping


def _normalized_os(system: str) -> str:
    mapping = {"Linux": "linux", "Windows": "windows", "Darwin": "macos"}
    return mapping.get(system, "unknown")


def probe_platform(
    *,
    system: str | None = None,
    env: Mapping[str, str] | None = None,
) -> dict[str, object]:
    env = os.environ if env is None else env
    raw_system = platform.system() if system is None else system
    os_name = _normalized_os(raw_system)

    if os_name == "windows":
        candidate = "win32"
        session = "native"
        permissions = ["desktop-session"]
    elif os_name == "macos":
        candidate = "quartz"
        session = "native"
        permissions = ["accessibility", "screen-recording"]
    elif os_name == "linux":
        if env.get("WAYLAND_DISPLAY"):
            candidate = "wayland"
            session = env.get("WAYLAND_DISPLAY", "")
            permissions = ["compositor-session", "portal-may-be-required"]
        elif env.get("DISPLAY"):
            candidate = "x11"
            session = env.get("DISPLAY", "")
            permissions = ["x11-display-access"]
        else:
            candidate = "none"
            session = ""
            permissions = ["graphical-session-missing"]
    else:
        candidate = "unsupported-host"
        session = ""
        permissions = []

    return {
        "schema": "agent-interface/platform-probe-v1",
        "os": os_name,
        "raw_system": raw_system,
        "candidate_backend": candidate,
        "session": session,
        "permission_hints": permissions,
        "support_claim": False,
        "input_authority": "none",
    }
