from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import FrozenSet, Iterable

class CapabilityState(str, Enum):
    SUPPORTED = "supported"
    UNSUPPORTED = "unsupported"
    UNKNOWN = "unknown"
    PERMISSION_REQUIRED = "permission_required"

class TextCoverage(str, Enum):
    ASCII = "ascii"
    UNICODE = "unicode"

class SideEffect(str, Enum):
    CLIPBOARD_CONTENT = "clipboard_content"
    CLIPBOARD_OWNER = "clipboard_owner"
    CLIPBOARD_TARGETS = "clipboard_targets"
    GLOBAL_KEYMAP = "global_keymap"
    ACCESSIBILITY_WRITE = "accessibility_write"
    IME_STATE = "ime_state"

# Lower is preferred only after all hard gates pass.
SIDE_EFFECT_COST = {
    SideEffect.ACCESSIBILITY_WRITE: 1,
    SideEffect.IME_STATE: 2,
    SideEffect.CLIPBOARD_CONTENT: 2,
    SideEffect.CLIPBOARD_OWNER: 3,
    SideEffect.CLIPBOARD_TARGETS: 3,
    SideEffect.GLOBAL_KEYMAP: 10,
}

ROUTE_RANK = {
    "accessibility_set_value": 10,
    "native_ime": 20,
    "direct_keys": 30,
    "clipboard_utf8": 40,
    "keymap_remap": 90,
}

@dataclass(frozen=True)
class Route:
    name: str
    state: CapabilityState
    coverage: FrozenSet[TextCoverage]
    side_effects: FrozenSet[SideEffect]
    exact_semantics_observed: bool
    permission: str | None = None

@dataclass(frozen=True)
class Request:
    coverage: TextCoverage
    allowed_side_effects: FrozenSet[SideEffect]
    require_observed_exact: bool = True

@dataclass(frozen=True)
class Decision:
    selected: str | None
    reason: str
    rejected: tuple[tuple[str, str], ...]

def _reject_reason(route: Route, request: Request) -> str | None:
    if route.state is CapabilityState.PERMISSION_REQUIRED:
        return f"permission_required:{route.permission or 'unspecified'}"
    if route.state is CapabilityState.UNKNOWN:
        return "capability_unknown"
    if route.state is CapabilityState.UNSUPPORTED:
        return "capability_unsupported"
    if request.coverage not in route.coverage:
        return "text_coverage_insufficient"
    if request.require_observed_exact and not route.exact_semantics_observed:
        return "exact_semantics_unproven"
    undeclared = route.side_effects - request.allowed_side_effects
    if undeclared:
        return "side_effect_forbidden:" + ",".join(sorted(x.value for x in undeclared))
    return None

def choose_route(routes: Iterable[Route], request: Request) -> Decision:
    accepted: list[Route] = []
    rejected: list[tuple[str, str]] = []
    seen: set[str] = set()
    for route in routes:
        if route.name in seen:
            raise ValueError(f"duplicate route: {route.name}")
        seen.add(route.name)
        reason = _reject_reason(route, request)
        if reason is None:
            accepted.append(route)
        else:
            rejected.append((route.name, reason))
    if not accepted:
        return Decision(None, "no_eligible_route", tuple(rejected))
    accepted.sort(key=lambda r: (sum(SIDE_EFFECT_COST[x] for x in r.side_effects), max((SIDE_EFFECT_COST[x] for x in r.side_effects), default=0), ROUTE_RANK.get(r.name, 1000), r.name))
    return Decision(accepted[0].name, "selected_minimum_declared_side_effect_route", tuple(rejected))

def x11_evidence_profile() -> tuple[Route, ...]:
    """Evidence-derived profile. This is scoped to retained X11 findings."""
    return (
        Route("direct_keys", CapabilityState.SUPPORTED, frozenset({TextCoverage.ASCII}), frozenset(), True),
        Route("clipboard_utf8", CapabilityState.SUPPORTED, frozenset({TextCoverage.ASCII, TextCoverage.UNICODE}), frozenset({SideEffect.CLIPBOARD_CONTENT, SideEffect.CLIPBOARD_OWNER, SideEffect.CLIPBOARD_TARGETS}), True),
        Route("keymap_remap", CapabilityState.SUPPORTED, frozenset({TextCoverage.ASCII, TextCoverage.UNICODE}), frozenset({SideEffect.GLOBAL_KEYMAP}), False),
        Route("accessibility_set_value", CapabilityState.UNKNOWN, frozenset({TextCoverage.ASCII, TextCoverage.UNICODE}), frozenset({SideEffect.ACCESSIBILITY_WRITE}), False),
        Route("native_ime", CapabilityState.UNKNOWN, frozenset({TextCoverage.ASCII, TextCoverage.UNICODE}), frozenset({SideEffect.IME_STATE}), False),
    )
