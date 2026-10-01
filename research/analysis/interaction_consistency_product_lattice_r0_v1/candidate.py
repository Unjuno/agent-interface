from __future__ import annotations

from dataclasses import dataclass, asdict
from enum import IntEnum
from typing import Dict, Iterable


class Decision(IntEnum):
    SERIAL = 0
    PHASE_OVERLAP = 1
    FULL_PARALLEL = 2


@dataclass(frozen=True)
class State:
    surface_disjoint: bool
    readset_complete: bool
    readset_current: bool
    global_conflict_free: bool
    effects_commute: bool
    actuator_independent: bool
    simultaneous_input_requested: bool

    def to_dict(self) -> Dict[str, bool]:
        return asdict(self)


def requested_concurrency(state: State) -> Decision:
    return Decision.FULL_PARALLEL if state.simultaneous_input_requested else Decision.PHASE_OVERLAP


def oracle(state: State) -> Decision:
    base_ok = (
        state.readset_complete
        and state.readset_current
        and state.global_conflict_free
        and state.effects_commute
    )
    if not base_ok:
        return Decision.SERIAL
    if state.simultaneous_input_requested:
        return Decision.FULL_PARALLEL if state.actuator_independent else Decision.SERIAL
    return Decision.PHASE_OVERLAP


def safe_serial(state: State) -> Decision:
    return Decision.SERIAL


def surface_only(state: State) -> Decision:
    return requested_concurrency(state) if state.surface_disjoint else Decision.SERIAL


def readset_only(state: State) -> Decision:
    return requested_concurrency(state) if (state.readset_complete and state.readset_current) else Decision.SERIAL


def actuator_only(state: State) -> Decision:
    if state.simultaneous_input_requested:
        return Decision.FULL_PARALLEL if state.actuator_independent else Decision.SERIAL
    return Decision.PHASE_OVERLAP


def strict_full_only(state: State) -> Decision:
    base_ok = (
        state.readset_complete
        and state.readset_current
        and state.global_conflict_free
        and state.effects_commute
        and state.actuator_independent
        and state.simultaneous_input_requested
    )
    return Decision.FULL_PARALLEL if base_ok else Decision.SERIAL


def product_contract(state: State) -> Decision:
    return oracle(state)


POLICIES = {
    "SAFE_SERIAL": safe_serial,
    "SURFACE_ONLY": surface_only,
    "READSET_ONLY": readset_only,
    "ACTUATOR_ONLY": actuator_only,
    "STRICT_FULL_ONLY": strict_full_only,
    "PRODUCT": product_contract,
}


def is_unsafe(candidate: Decision, truth: Decision) -> bool:
    return int(candidate) > int(truth)


def raw_surface_admits(state: State) -> bool:
    return state.surface_disjoint


def raw_readset_admits(state: State) -> bool:
    return state.readset_complete and state.readset_current
