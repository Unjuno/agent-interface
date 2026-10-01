from __future__ import annotations

from dataclasses import dataclass
from typing import FrozenSet, Optional

CURRENT = "CURRENT"
TEMPORAL = "TEMPORAL"
VERIFY = "VERIFY"
ROLES = frozenset({CURRENT, TEMPORAL, VERIFY})


@dataclass(frozen=True)
class Variant:
    name: str
    cost: int
    evidence: FrozenSet[str]
    rank: int


CATALOG = (
    Variant("CURRENT", 1, frozenset({CURRENT}), 0),
    Variant("TEMPORAL", 3, frozenset({CURRENT, TEMPORAL}), 1),
    Variant("VERIFY", 3, frozenset({CURRENT, VERIFY}), 2),
    Variant("FULL", 6, frozenset({CURRENT, TEMPORAL, VERIFY}), 3),
)
BY_NAME = {v.name: v for v in CATALOG}


@dataclass(frozen=True)
class State:
    slack: int
    reserve: int
    required: FrozenSet[str]


def safe_variant(state: State, variant: Variant) -> bool:
    return state.required.issubset(variant.evidence) and variant.cost + state.reserve <= state.slack


def feasible(state: State) -> bool:
    return any(safe_variant(state, v) for v in CATALOG)


def scalar_raw_highest(state: State) -> Optional[str]:
    fitting = [v for v in CATALOG if v.cost <= state.slack]
    return max(fitting, key=lambda v: v.rank).name if fitting else None


def scalar_reserved_highest(state: State) -> Optional[str]:
    fitting = [v for v in CATALOG if v.cost + state.reserve <= state.slack]
    return max(fitting, key=lambda v: v.rank).name if fitting else None


def scalar_reserved_postcheck(state: State) -> Optional[str]:
    chosen = scalar_reserved_highest(state)
    if chosen is None:
        return None
    return chosen if state.required.issubset(BY_NAME[chosen].evidence) else None


def current_only(state: State) -> Optional[str]:
    v = BY_NAME["CURRENT"]
    return v.name if safe_variant(state, v) else None


def typed_reserved(state: State) -> Optional[str]:
    fitting = [v for v in CATALOG if safe_variant(state, v)]
    if not fitting:
        return None
    return max(fitting, key=lambda v: (len(v.evidence), v.rank)).name


POLICIES = {
    "SCALAR_RAW_HIGHEST": scalar_raw_highest,
    "SCALAR_RESERVED_HIGHEST": scalar_reserved_highest,
    "SCALAR_RESERVED_POSTCHECK": scalar_reserved_postcheck,
    "CURRENT_ONLY": current_only,
    "TYPED_RESERVED": typed_reserved,
}
