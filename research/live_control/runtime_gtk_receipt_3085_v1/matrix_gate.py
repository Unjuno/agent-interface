"""Fixed-order, model-free evidence gate for the formal GTK successor experiment."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

CASES = (
    "USEFUL_EFFECT",
    "UNAVAILABLE_BEFORE_INPUT",
    "GUARDED_REFUSAL",
    "ACCEPTED_NO_EFFECT",
    "PARTIAL_COLLATERAL",
    "STALE_REPAIR",
    "AMBIGUOUS_DELIVERY",
    "TERMINAL_CLEANUP_FAILURE",
)

EXPECTED = {
    "USEFUL_EFFECT": "USEFUL",
    "UNAVAILABLE_BEFORE_INPUT": "UNAVAILABLE",
    "GUARDED_REFUSAL": "REFUSED",
    "ACCEPTED_NO_EFFECT": "NO_EFFECT",
    "PARTIAL_COLLATERAL": "PARTIAL",
    "STALE_REPAIR": "REPAIRED",
    "AMBIGUOUS_DELIVERY": "UNKNOWN",
    "TERMINAL_CLEANUP_FAILURE": "CLEANUP_FAILURE",
}


@dataclass(frozen=True)
class GateResult:
    case: str
    outcome: str
    ready: bool
    reason: str


def gate(receipt: Mapping[str, Any]) -> GateResult:
    case = receipt.get("case")
    if case not in CASES:
        return GateResult(str(case), "UNKNOWN", False, "case")
    if receipt.get("authority_grants") != 0:
        return GateResult(case, "UNKNOWN", False, "authority")
    required = (
        "session_id", "window_id", "observation_revision",
        "binding_revision", "input_ledger", "effect_receipt", "cleanup",
    )
    if any(key not in receipt for key in required):
        return GateResult(case, "UNKNOWN", False, "missing_evidence")
    if not receipt["session_id"] or not receipt["window_id"]:
        return GateResult(case, "UNKNOWN", False, "identity")
    if receipt["observation_revision"] != receipt["binding_revision"]:
        return GateResult(case, "UNKNOWN", False, "stale_binding")
    if not isinstance(receipt["input_ledger"], list):
        return GateResult(case, "UNKNOWN", False, "input_ledger")
    if not isinstance(receipt["effect_receipt"], Mapping):
        return GateResult(case, "UNKNOWN", False, "effect_receipt")
    if not isinstance(receipt["cleanup"], Mapping):
        return GateResult(case, "UNKNOWN", False, "cleanup")
    if case == "AMBIGUOUS_DELIVERY":
        delivery = receipt.get("delivery")
        if not isinstance(delivery, Mapping):
            return GateResult(case, "UNKNOWN", False, "ambiguous_delivery_evidence")
        if delivery.get("status") != "ambiguous" or not delivery.get("reason"):
            return GateResult(case, "UNKNOWN", False, "ambiguous_delivery_evidence")
        if receipt.get("replay_allowed") is not False:
            return GateResult(case, "UNKNOWN", False, "ambiguous_replay_policy")
        if receipt.get("replay_count") != 0:
            return GateResult(case, "UNKNOWN", False, "ambiguous_replay")
        return GateResult(case, "UNKNOWN", True, "ambiguous_no_replay")
    if case == "TERMINAL_CLEANUP_FAILURE":
        cleanup = receipt["cleanup"]
        if cleanup.get("status") != "failed":
            return GateResult(case, "CLEANUP_FAILURE", False, "cleanup_status")
        if not cleanup.get("failure_reason"):
            return GateResult(case, "CLEANUP_FAILURE", False, "cleanup_failure_evidence")
        if cleanup.get("release_verified") is not True:
            return GateResult(case, "CLEANUP_FAILURE", False, "cleanup_release_truth")
        return GateResult(case, "CLEANUP_FAILURE", True, "cleanup_failure_recorded")
    return GateResult(case, EXPECTED[case], True, "classified")


def audit_order(receipts: Sequence[Mapping[str, Any]]) -> tuple[bool, str]:
    if len(receipts) != len(CASES):
        return False, "case_count"
    actual = tuple(item.get("case") for item in receipts)
    if actual != CASES:
        return False, "case_order"
    return True, "fixed_order"
