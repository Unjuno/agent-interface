"""Offline model for the Issue #4536 policy-invalidation clock boundary.

This deliberately models the final-admission contract only. It does not call
the game, a planner, or an input backend.
"""
from __future__ import annotations

from dataclasses import dataclass


MAX_OFFSET_WIDTH_NS = 2_000_000


@dataclass(frozen=True)
class Calibration:
    session_id: str
    host_domain: str
    runtime_domain: str
    offset_lower_ns: int
    offset_upper_ns: int

    def validate(self, expected_session: str) -> None:
        if self.session_id != expected_session:
            raise ValueError("stale or wrong-session calibration")
        if not self.host_domain or not self.runtime_domain or self.host_domain == self.runtime_domain:
            raise ValueError("invalid clock domains")
        if type(self.offset_lower_ns) is not int or type(self.offset_upper_ns) is not int:
            raise ValueError("integer offset bounds required")
        width = self.offset_upper_ns - self.offset_lower_ns
        if width < 0 or width > MAX_OFFSET_WIDTH_NS:
            raise ValueError("invalid or over-wide offset interval")

    def host_to_runtime(self, host_ns: int, expected_session: str) -> int:
        self.validate(expected_session)
        if type(host_ns) is not int or host_ns < 0:
            raise ValueError("invalid host timestamp")
        # A conservative lower bound avoids claiming the event happened later
        # in runtime time than the evidence permits.
        converted = host_ns + self.offset_lower_ns
        if converted < 0:
            raise ValueError("converted timestamp outside runtime domain")
        return converted


@dataclass(frozen=True)
class Invalidation:
    session_id: str
    event_id: str
    reason: str
    host_domain: str
    outcome_evaluated_host_ns: int


@dataclass(frozen=True)
class Decision:
    session_id: str
    decision_id: str
    runtime_domain: str
    decided_runtime_ns: int
    planner_interrupted: bool


@dataclass(frozen=True)
class Receipt:
    event_id: str
    reason: str
    host_domain: str
    outcome_evaluated_host_ns: int
    runtime_domain: str
    outcome_evaluated_runtime_ns: int
    calibration_session_id: str


@dataclass(frozen=True)
class Admission:
    status: str
    admitted: bool
    executor_input_calls: int
    receipt: Receipt


def final_action_admission(
    invalidation: Invalidation,
    decision: Decision,
    calibration: Calibration | None = None,
) -> Admission:
    """Raise on mixed domains; otherwise reject invalidated turn, no input."""
    if invalidation.session_id != decision.session_id:
        raise ValueError("session mismatch")
    if invalidation.host_domain == decision.runtime_domain:
        evaluated_runtime_ns = invalidation.outcome_evaluated_host_ns
        calibration_session_id = "same-domain"
    else:
        if calibration is None:
            raise ValueError("incomparable clock domains")
        evaluated_runtime_ns = calibration.host_to_runtime(
            invalidation.outcome_evaluated_host_ns, decision.session_id
        )
        calibration_session_id = calibration.session_id
    receipt = Receipt(
        event_id=invalidation.event_id,
        reason=invalidation.reason,
        host_domain=invalidation.host_domain,
        outcome_evaluated_host_ns=invalidation.outcome_evaluated_host_ns,
        runtime_domain=decision.runtime_domain,
        outcome_evaluated_runtime_ns=evaluated_runtime_ns,
        calibration_session_id=calibration_session_id,
    )
    if evaluated_runtime_ns > decision.decided_runtime_ns:
        raise ValueError("policy invalidation follows controller decision")
    if decision.planner_interrupted:
        return Admission("REJECTED_POLICY_INVALIDATED", False, 0, receipt)
    return Admission("REJECTED_POLICY_INVALIDATED", False, 0, receipt)
