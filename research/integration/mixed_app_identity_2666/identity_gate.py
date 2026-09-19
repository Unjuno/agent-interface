"""Fail-closed typed identity gate for the #2499 successor."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence


EXPECTED_APPS = ("inkscape", "libreoffice", "chromium")


@dataclass(frozen=True)
class IdentityDecision:
    admitted: bool
    reason: str


def _valid_identity(item: Any, display: str) -> bool:
    if not isinstance(item, Mapping):
        return False
    window_id = item.get("window_id")
    pid = item.get("pid")
    return (
        type(window_id) is int and window_id > 0
        and type(pid) is int and pid > 0
        and item.get("display") == display
        and isinstance(item.get("title"), str) and bool(item["title"])
        and isinstance(item.get("wm_class"), str) and bool(item["wm_class"])
    )


def evaluate_identities(
    selected: Mapping[str, Any],
    repeated: Mapping[str, Any],
    *,
    display: str,
    expected_apps: Sequence[str] = EXPECTED_APPS,
) -> IdentityDecision:
    if not isinstance(display, str) or not display:
        return IdentityDecision(False, "display")
    apps = tuple(expected_apps)
    if apps != EXPECTED_APPS or len(set(apps)) != len(apps):
        return IdentityDecision(False, "expected_apps")
    if not isinstance(selected, Mapping) or not isinstance(repeated, Mapping):
        return IdentityDecision(False, "shape")
    if set(selected) != set(apps) or set(repeated) != set(apps):
        return IdentityDecision(False, "app_set")
    identities = []
    for app in apps:
        first = selected[app]
        again = repeated[app]
        if isinstance(first, list) or isinstance(again, list):
            return IdentityDecision(False, "ambiguous")
        if not _valid_identity(first, display) or not _valid_identity(again, display):
            return IdentityDecision(False, "identity")
        if first != again:
            return IdentityDecision(False, "unstable")
        identities.append((first["window_id"], first["pid"]))
    if len(set(identities)) != len(identities):
        return IdentityDecision(False, "duplicate")
    return IdentityDecision(True, "admitted")
