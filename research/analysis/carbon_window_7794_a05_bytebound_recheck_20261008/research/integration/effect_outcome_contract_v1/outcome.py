"""Evidence-bounded typed effect outcome reduction.

This construction candidate preserves two retained distinctions:
1. pre-effect refusal is not post-effect contradiction;
2. verified compensation may restore current state without erasing effect history.

The reducer intentionally supports only the states covered by the retained
phase/compensation evidence. Unsupported histories fail closed.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable


class ContractError(ValueError):
    """Raised when evidence is malformed or outside the supported contract."""


class OperationKind(str, Enum):
    STAGEABLE = "stageable"
    DIRECT = "direct"


class TerminalPhase(str, Enum):
    REJECTED_PRE_EFFECT = "rejected_pre_effect"
    EFFECT_COMMITTED = "effect_committed"


class EventKind(str, Enum):
    EFFECT = "effect"
    COMPENSATION = "compensation"


class OutcomeKind(str, Enum):
    PUBLISHED_VERIFIED = "PUBLISHED_VERIFIED"
    REJECTED_PRE_EFFECT = "REJECTED_PRE_EFFECT"
    EFFECT_VERIFIED = "EFFECT_VERIFIED"
    EFFECT_CONTRADICTED_COMPENSATED = "EFFECT_CONTRADICTED_COMPENSATED"
    EFFECT_CONTRADICTED_UNCOMPENSATED = "EFFECT_CONTRADICTED_UNCOMPENSATED"


@dataclass(frozen=True, slots=True)
class Event:
    seq: int
    kind: EventKind
    value: str

    def __post_init__(self) -> None:
        if type(self.seq) is not int or self.seq <= 0:
            raise ContractError("event seq must be a positive integer")
        if not isinstance(self.kind, EventKind):
            raise ContractError("event kind must be EventKind")
        if type(self.value) is not str or not self.value:
            raise ContractError("event value must be a nonempty string")


@dataclass(frozen=True, slots=True)
class Outcome:
    kind: OutcomeKind
    operation_kind: OperationKind
    effect_occurred: bool
    intended_effect_verified: bool
    contradiction_observed: bool
    compensation_attempted: bool
    compensation_verified: bool
    current_state: str
    history: tuple[Event, ...]


def _normalize_history(events: Iterable[Event]) -> tuple[Event, ...]:
    try:
        history = tuple(events)
    except TypeError as error:
        raise ContractError("events must be iterable") from error
    if any(not isinstance(event, Event) for event in history):
        raise ContractError("history entries must be Event values")
    if any(left.seq >= right.seq for left, right in zip(history, history[1:])):
        raise ContractError("event sequence numbers must be strictly increasing")
    return history


def _validate_common(
    operation_kind: OperationKind,
    initial_state: str,
    intended_state: str,
    current_state: str,
    terminal_phase: TerminalPhase,
    history: tuple[Event, ...],
) -> None:
    if not isinstance(operation_kind, OperationKind):
        raise ContractError("operation_kind must be OperationKind")
    if not isinstance(terminal_phase, TerminalPhase):
        raise ContractError("terminal_phase must be TerminalPhase")
    for name, value in (
        ("initial_state", initial_state),
        ("intended_state", intended_state),
        ("current_state", current_state),
    ):
        if type(value) is not str or not value:
            raise ContractError(f"{name} must be a nonempty string")
    if initial_state == intended_state:
        raise ContractError("initial_state and intended_state must differ")
    if history and history[-1].value != current_state:
        raise ContractError("current_state must equal the value of the final event")


def reduce_outcome(
    *,
    operation_kind: OperationKind,
    initial_state: str,
    intended_state: str,
    current_state: str,
    terminal_phase: TerminalPhase,
    events: Iterable[Event] = (),
) -> Outcome:
    """Reduce explicit phase/state/history evidence to one supported outcome.

    No outcome is inferred from current state alone. Historical effects remain in
    the returned value even when compensation restores ``initial_state``.
    """
    history = _normalize_history(events)
    _validate_common(
        operation_kind,
        initial_state,
        intended_state,
        current_state,
        terminal_phase,
        history,
    )

    if terminal_phase is TerminalPhase.REJECTED_PRE_EFFECT:
        if history:
            raise ContractError("pre-effect rejection cannot contain effect history")
        if current_state != initial_state:
            raise ContractError("pre-effect rejection must preserve the initial state")
        return Outcome(
            kind=OutcomeKind.REJECTED_PRE_EFFECT,
            operation_kind=operation_kind,
            effect_occurred=False,
            intended_effect_verified=False,
            contradiction_observed=False,
            compensation_attempted=False,
            compensation_verified=False,
            current_state=current_state,
            history=history,
        )

    if not history:
        raise ContractError("effect-committed terminal phase requires effect history")
    if history[0].kind is not EventKind.EFFECT:
        raise ContractError("first committed event must be the direct/publication effect")
    effect_events = [event for event in history if event.kind is EventKind.EFFECT]
    if len(effect_events) != 1:
        raise ContractError("exactly one primary effect event is supported")
    compensation_events = [event for event in history if event.kind is EventKind.COMPENSATION]
    if len(compensation_events) > 1:
        raise ContractError("at most one compensation event is supported")
    if compensation_events and history[-1].kind is not EventKind.COMPENSATION:
        raise ContractError("compensation must follow the primary effect")

    primary = history[0]
    primary_verified = primary.value == intended_state

    if primary_verified:
        if len(history) != 1:
            raise ContractError("compensation after a verified intended effect is unsupported")
        if current_state != intended_state:
            raise ContractError("verified primary effect requires intended current state")
        kind = (
            OutcomeKind.PUBLISHED_VERIFIED
            if operation_kind is OperationKind.STAGEABLE
            else OutcomeKind.EFFECT_VERIFIED
        )
        return Outcome(
            kind=kind,
            operation_kind=operation_kind,
            effect_occurred=True,
            intended_effect_verified=True,
            contradiction_observed=False,
            compensation_attempted=False,
            compensation_verified=False,
            current_state=current_state,
            history=history,
        )

    if operation_kind is not OperationKind.DIRECT:
        raise ContractError("committed wrong stageable publication is outside retained evidence")

    if len(history) == 1:
        if current_state == initial_state:
            raise ContractError("wrong direct effect cannot be collapsed to no-effect by current state")
        return Outcome(
            kind=OutcomeKind.EFFECT_CONTRADICTED_UNCOMPENSATED,
            operation_kind=operation_kind,
            effect_occurred=True,
            intended_effect_verified=False,
            contradiction_observed=True,
            compensation_attempted=False,
            compensation_verified=False,
            current_state=current_state,
            history=history,
        )

    if len(history) != 2 or history[1].kind is not EventKind.COMPENSATION:
        raise ContractError("unsupported post-contradiction history")
    compensation = history[1]
    if compensation.value != initial_state or current_state != initial_state:
        raise ContractError("unsupported compensation: declared invariant was not restored")

    return Outcome(
        kind=OutcomeKind.EFFECT_CONTRADICTED_COMPENSATED,
        operation_kind=operation_kind,
        effect_occurred=True,
        intended_effect_verified=False,
        contradiction_observed=True,
        compensation_attempted=True,
        compensation_verified=True,
        current_state=current_state,
        history=history,
    )
