"""Typed effect outcome construction with explicit required-invariant evidence.

Evidence-bounded v2 candidate. Historical effect occurrence is independent from
current restoration. A compensation is complete only when every declared
required invariant has independently verified matching evidence.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable


class ContractError(ValueError):
    """Malformed or unsupported evidence/contract input."""


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
    EFFECT_CONTRADICTED_COMPENSATION_INCOMPLETE = "EFFECT_CONTRADICTED_COMPENSATION_INCOMPLETE"
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
class InvariantRequirement:
    name: str
    expected: str

    def __post_init__(self) -> None:
        if type(self.name) is not str or not self.name:
            raise ContractError("invariant requirement name must be nonempty")
        if type(self.expected) is not str or not self.expected:
            raise ContractError("invariant requirement expected must be nonempty")


@dataclass(frozen=True, slots=True)
class InvariantEvidence:
    name: str
    observed: str
    independently_verified: bool

    def __post_init__(self) -> None:
        if type(self.name) is not str or not self.name:
            raise ContractError("invariant evidence name must be nonempty")
        if type(self.observed) is not str or not self.observed:
            raise ContractError("invariant evidence observed must be nonempty")
        if type(self.independently_verified) is not bool:
            raise ContractError("independently_verified must be bool")


@dataclass(frozen=True, slots=True)
class InvariantStatus:
    complete: bool
    missing: tuple[str, ...]
    unverified: tuple[str, ...]
    contradicted: tuple[str, ...]
    extra_evidence: tuple[str, ...]


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
    invariant_status: InvariantStatus | None


def _unique_by_name(values: tuple, label: str) -> dict[str, object]:
    result: dict[str, object] = {}
    for value in values:
        name = value.name
        if name in result:
            raise ContractError(f"duplicate {label} name: {name}")
        result[name] = value
    return result


def evaluate_required_invariants(
    requirements: Iterable[InvariantRequirement],
    evidence: Iterable[InvariantEvidence],
) -> InvariantStatus:
    reqs = tuple(requirements)
    evid = tuple(evidence)
    if not reqs:
        raise ContractError("compensation requires at least one declared invariant")
    if any(not isinstance(item, InvariantRequirement) for item in reqs):
        raise ContractError("requirements must contain InvariantRequirement values")
    if any(not isinstance(item, InvariantEvidence) for item in evid):
        raise ContractError("evidence must contain InvariantEvidence values")
    req_by_name = _unique_by_name(reqs, "requirement")
    ev_by_name = _unique_by_name(evid, "evidence")

    missing: list[str] = []
    unverified: list[str] = []
    contradicted: list[str] = []
    for name, requirement in req_by_name.items():
        item = ev_by_name.get(name)
        if item is None:
            missing.append(name)
            continue
        assert isinstance(requirement, InvariantRequirement)
        assert isinstance(item, InvariantEvidence)
        if not item.independently_verified:
            unverified.append(name)
            continue
        if item.observed != requirement.expected:
            contradicted.append(name)

    extra = sorted(set(ev_by_name) - set(req_by_name))
    missing.sort()
    unverified.sort()
    contradicted.sort()
    complete = not (missing or unverified or contradicted)
    return InvariantStatus(
        complete=complete,
        missing=tuple(missing),
        unverified=tuple(unverified),
        contradicted=tuple(contradicted),
        extra_evidence=tuple(extra),
    )


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


def reduce_outcome(
    *,
    operation_kind: OperationKind,
    initial_state: str,
    intended_state: str,
    current_state: str,
    terminal_phase: TerminalPhase,
    events: Iterable[Event] = (),
    compensation_requirements: Iterable[InvariantRequirement] = (),
    compensation_evidence: Iterable[InvariantEvidence] = (),
) -> Outcome:
    history = _normalize_history(events)
    requirements = tuple(compensation_requirements)
    evidence = tuple(compensation_evidence)

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

    has_invariant_inputs = bool(requirements or evidence)

    if terminal_phase is TerminalPhase.REJECTED_PRE_EFFECT:
        if history:
            raise ContractError("pre-effect rejection cannot contain effect history")
        if current_state != initial_state:
            raise ContractError("pre-effect rejection must preserve the initial state")
        if has_invariant_inputs:
            raise ContractError("compensation invariant evidence requires a compensation event")
        return Outcome(
            OutcomeKind.REJECTED_PRE_EFFECT,
            operation_kind,
            False,
            False,
            False,
            False,
            False,
            current_state,
            history,
            None,
        )

    if not history:
        raise ContractError("effect-committed terminal phase requires effect history")
    if history[0].kind is not EventKind.EFFECT:
        raise ContractError("first committed event must be the primary effect")
    effect_events = tuple(event for event in history if event.kind is EventKind.EFFECT)
    compensation_events = tuple(event for event in history if event.kind is EventKind.COMPENSATION)
    if len(effect_events) != 1:
        raise ContractError("exactly one primary effect event is supported")
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
        if has_invariant_inputs:
            raise ContractError("compensation invariant evidence requires a compensation event")
        kind = (
            OutcomeKind.PUBLISHED_VERIFIED
            if operation_kind is OperationKind.STAGEABLE
            else OutcomeKind.EFFECT_VERIFIED
        )
        return Outcome(kind, operation_kind, True, True, False, False, False, current_state, history, None)

    if operation_kind is not OperationKind.DIRECT:
        raise ContractError("committed wrong stageable publication is outside retained evidence")

    if len(history) == 1:
        if has_invariant_inputs:
            raise ContractError("compensation invariant evidence requires a compensation event")
        if current_state == initial_state:
            raise ContractError("wrong direct effect cannot be collapsed to no-effect by current state")
        return Outcome(
            OutcomeKind.EFFECT_CONTRADICTED_UNCOMPENSATED,
            operation_kind,
            True,
            False,
            True,
            False,
            False,
            current_state,
            history,
            None,
        )

    if len(history) != 2 or history[1].kind is not EventKind.COMPENSATION:
        raise ContractError("unsupported post-contradiction history")

    status = evaluate_required_invariants(requirements, evidence)
    if status.complete:
        return Outcome(
            OutcomeKind.EFFECT_CONTRADICTED_COMPENSATED,
            operation_kind,
            True,
            False,
            True,
            True,
            True,
            current_state,
            history,
            status,
        )
    return Outcome(
        OutcomeKind.EFFECT_CONTRADICTED_COMPENSATION_INCOMPLETE,
        operation_kind,
        True,
        False,
        True,
        True,
        False,
        current_state,
        history,
        status,
    )
