"""Typed effect outcomes with pre-effect invariant-manifest binding.

Construction v3 preserves the v2 required-invariant semantics and adds one
binding rule: the invariant manifest used for post-effect compensation
verification must be the same manifest that the executed command carried
before the effect occurred.

This is an evidence-bounded construction candidate, not a security protocol.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import re
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


_HEX64 = re.compile(r"^[0-9a-f]{64}$")


def _nonempty(value: object, label: str) -> str:
    if type(value) is not str or not value:
        raise ContractError(f"{label} must be a nonempty string")
    return value


def _manifest_id(value: object, label: str) -> str:
    text = _nonempty(value, label)
    if _HEX64.fullmatch(text) is None:
        raise ContractError(f"{label} must be a lowercase SHA-256 hex digest")
    return text


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
        _nonempty(self.value, "event value")


@dataclass(frozen=True, slots=True)
class InvariantRequirement:
    name: str
    expected: str

    def __post_init__(self) -> None:
        _nonempty(self.name, "invariant requirement name")
        _nonempty(self.expected, "invariant requirement expected")


@dataclass(frozen=True, slots=True)
class InvariantEvidence:
    name: str
    observed: str
    independently_verified: bool

    def __post_init__(self) -> None:
        _nonempty(self.name, "invariant evidence name")
        _nonempty(self.observed, "invariant evidence observed")
        if type(self.independently_verified) is not bool:
            raise ContractError("independently_verified must be bool")


@dataclass(frozen=True, slots=True)
class InvariantManifest:
    scope_id: str
    requirements: tuple[InvariantRequirement, ...]
    manifest_id: str

    def __post_init__(self) -> None:
        _nonempty(self.scope_id, "manifest scope_id")
        if not self.requirements:
            raise ContractError("invariant manifest requires at least one requirement")
        if any(not isinstance(item, InvariantRequirement) for item in self.requirements):
            raise ContractError("manifest requirements must be InvariantRequirement values")
        _manifest_id(self.manifest_id, "manifest_id")


@dataclass(frozen=True, slots=True)
class ExecutionBinding:
    command_id: str
    invariant_manifest_id: str

    def __post_init__(self) -> None:
        _nonempty(self.command_id, "command_id")
        _manifest_id(self.invariant_manifest_id, "execution invariant_manifest_id")


@dataclass(frozen=True, slots=True)
class VerificationReceipt:
    invariant_manifest_id: str
    evidence: tuple[InvariantEvidence, ...]

    def __post_init__(self) -> None:
        _manifest_id(self.invariant_manifest_id, "verification invariant_manifest_id")
        if any(not isinstance(item, InvariantEvidence) for item in self.evidence):
            raise ContractError("verification evidence must be InvariantEvidence values")


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
    invariant_manifest_id: str | None
    invariant_status: InvariantStatus | None


def _unique_requirements(values: Iterable[InvariantRequirement]) -> tuple[InvariantRequirement, ...]:
    items = tuple(values)
    if not items:
        raise ContractError("invariant manifest requires at least one requirement")
    if any(not isinstance(item, InvariantRequirement) for item in items):
        raise ContractError("requirements must contain InvariantRequirement values")
    seen: set[str] = set()
    for item in items:
        if item.name in seen:
            raise ContractError(f"duplicate requirement name: {item.name}")
        seen.add(item.name)
    return tuple(sorted(items, key=lambda item: item.name))


def _canonical_manifest_bytes(scope_id: str, requirements: tuple[InvariantRequirement, ...]) -> bytes:
    payload = {
        "schema": "effect-outcome-invariant-manifest-v1",
        "scope_id": scope_id,
        "requirements": [
            {"name": item.name, "expected": item.expected}
            for item in requirements
        ],
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def bind_invariant_manifest(
    scope_id: str,
    requirements: Iterable[InvariantRequirement],
) -> InvariantManifest:
    """Create a deterministic manifest identity before effect execution."""
    scope = _nonempty(scope_id, "manifest scope_id")
    reqs = _unique_requirements(requirements)
    digest = hashlib.sha256(_canonical_manifest_bytes(scope, reqs)).hexdigest()
    return InvariantManifest(scope, reqs, digest)


def _validate_manifest(manifest: InvariantManifest) -> None:
    if not isinstance(manifest, InvariantManifest):
        raise ContractError("manifest must be InvariantManifest")
    reqs = _unique_requirements(manifest.requirements)
    if reqs != manifest.requirements:
        raise ContractError("manifest requirements must use canonical name order")
    expected = hashlib.sha256(_canonical_manifest_bytes(manifest.scope_id, reqs)).hexdigest()
    if expected != manifest.manifest_id:
        raise ContractError("manifest_id does not match manifest content")


def _unique_evidence(values: tuple[InvariantEvidence, ...]) -> dict[str, InvariantEvidence]:
    result: dict[str, InvariantEvidence] = {}
    for item in values:
        if item.name in result:
            raise ContractError(f"duplicate evidence name: {item.name}")
        result[item.name] = item
    return result


def evaluate_bound_invariants(
    manifest: InvariantManifest,
    execution_binding: ExecutionBinding,
    verification_receipt: VerificationReceipt,
) -> InvariantStatus:
    """Evaluate only evidence bound to the exact pre-effect manifest."""
    _validate_manifest(manifest)
    if not isinstance(execution_binding, ExecutionBinding):
        raise ContractError("execution_binding must be ExecutionBinding")
    if not isinstance(verification_receipt, VerificationReceipt):
        raise ContractError("verification_receipt must be VerificationReceipt")
    if execution_binding.invariant_manifest_id != manifest.manifest_id:
        raise ContractError("executed command is bound to a different invariant manifest")
    if verification_receipt.invariant_manifest_id != manifest.manifest_id:
        raise ContractError("verification receipt is bound to a different invariant manifest")

    req_by_name = {item.name: item for item in manifest.requirements}
    ev_by_name = _unique_evidence(verification_receipt.evidence)
    missing: list[str] = []
    unverified: list[str] = []
    contradicted: list[str] = []
    for name, requirement in req_by_name.items():
        item = ev_by_name.get(name)
        if item is None:
            missing.append(name)
            continue
        if not item.independently_verified:
            unverified.append(name)
            continue
        if item.observed != requirement.expected:
            contradicted.append(name)
    extra = sorted(set(ev_by_name) - set(req_by_name))
    return InvariantStatus(
        complete=not (missing or unverified or contradicted),
        missing=tuple(sorted(missing)),
        unverified=tuple(sorted(unverified)),
        contradicted=tuple(sorted(contradicted)),
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


def _validate_binding_pair(
    manifest: InvariantManifest | None,
    execution_binding: ExecutionBinding | None,
) -> str | None:
    if (manifest is None) != (execution_binding is None):
        raise ContractError("manifest and execution_binding must be supplied together")
    if manifest is None:
        return None
    assert execution_binding is not None
    _validate_manifest(manifest)
    if execution_binding.invariant_manifest_id != manifest.manifest_id:
        raise ContractError("executed command is bound to a different invariant manifest")
    return manifest.manifest_id


def reduce_outcome(
    *,
    operation_kind: OperationKind,
    initial_state: str,
    intended_state: str,
    current_state: str,
    terminal_phase: TerminalPhase,
    events: Iterable[Event] = (),
    invariant_manifest: InvariantManifest | None = None,
    execution_binding: ExecutionBinding | None = None,
    verification_receipt: VerificationReceipt | None = None,
) -> Outcome:
    """Reduce phase/history/evidence while preserving the pre-effect manifest binding."""
    history = _normalize_history(events)
    bound_manifest_id = _validate_binding_pair(invariant_manifest, execution_binding)

    if not isinstance(operation_kind, OperationKind):
        raise ContractError("operation_kind must be OperationKind")
    if not isinstance(terminal_phase, TerminalPhase):
        raise ContractError("terminal_phase must be TerminalPhase")
    initial_state = _nonempty(initial_state, "initial_state")
    intended_state = _nonempty(intended_state, "intended_state")
    current_state = _nonempty(current_state, "current_state")
    if initial_state == intended_state:
        raise ContractError("initial_state and intended_state must differ")
    if history and history[-1].value != current_state:
        raise ContractError("current_state must equal the value of the final event")

    if terminal_phase is TerminalPhase.REJECTED_PRE_EFFECT:
        if history:
            raise ContractError("pre-effect rejection cannot contain effect history")
        if current_state != initial_state:
            raise ContractError("pre-effect rejection must preserve the initial state")
        if verification_receipt is not None:
            raise ContractError("verification receipt requires a compensation event")
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
            bound_manifest_id,
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
        if verification_receipt is not None:
            raise ContractError("verification receipt requires a compensation event")
        kind = OutcomeKind.PUBLISHED_VERIFIED if operation_kind is OperationKind.STAGEABLE else OutcomeKind.EFFECT_VERIFIED
        return Outcome(
            kind, operation_kind, True, True, False, False, False,
            current_state, history, bound_manifest_id, None,
        )

    if operation_kind is not OperationKind.DIRECT:
        raise ContractError("committed wrong stageable publication is outside retained evidence")

    if len(history) == 1:
        if verification_receipt is not None:
            raise ContractError("verification receipt requires a compensation event")
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
            bound_manifest_id,
            None,
        )

    if len(history) != 2 or history[1].kind is not EventKind.COMPENSATION:
        raise ContractError("unsupported post-contradiction history")
    if invariant_manifest is None or execution_binding is None:
        raise ContractError("compensation requires a pre-effect invariant manifest binding")
    if verification_receipt is None:
        raise ContractError("compensation requires a verification receipt")

    status = evaluate_bound_invariants(invariant_manifest, execution_binding, verification_receipt)
    kind = (
        OutcomeKind.EFFECT_CONTRADICTED_COMPENSATED
        if status.complete
        else OutcomeKind.EFFECT_CONTRADICTED_COMPENSATION_INCOMPLETE
    )
    return Outcome(
        kind,
        operation_kind,
        True,
        False,
        True,
        True,
        status.complete,
        current_state,
        history,
        invariant_manifest.manifest_id,
        status,
    )
