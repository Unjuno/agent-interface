"""Fresh, typed action-validity checks before final Executor admission.

This module only decides whether a planner-authored action remains eligible to
reach the Executor admission boundary.  It never issues input and never grants
input authority.
"""
from copy import deepcopy
import hashlib
import json
import math


CONTRACT_FORMAT = "action-validity-contract-v1"
SNAPSHOT_FORMAT = "action-admission-snapshot-v1"
RESULT_FORMAT = "action-validity-admission-v1"
_OPERATORS = {"equals", "minimum", "maximum", "max_decrease_from_source"}


def action_fingerprint(action):
    """Return a stable binding for the exact action payload."""
    if type(action) not in (dict, list):
        raise ValueError("action must be a JSON object or array")
    encoded = json.dumps(
        action, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _binding(value):
    expected = {"focus", "surface", "geometry"}
    if (type(value) is not dict or set(value) != expected or
            type(value["focus"]) is not int or type(value["surface"]) is not int or
            type(value["geometry"]) is not list or len(value["geometry"]) != 4 or
            any(type(item) is not int for item in value["geometry"])):
        raise ValueError("exact focus/surface/geometry binding required")
    return value


def _signals(value, *, source):
    if type(value) is not dict or not value:
        raise ValueError("nonempty typed signals required")
    checked = {}
    for signal_id, signal in value.items():
        if not isinstance(signal_id, str) or not signal_id:
            raise ValueError("nonempty signal id required")
        if source:
            if (type(signal) is not dict or set(signal) != {"status", "value"} or
                    signal["status"] != "observed"):
                raise ValueError("source signals must be observed")
        else:
            if (type(signal) is not dict or set(signal) != {"status", "value"} or
                    signal["status"] not in ("observed", "unknown") or
                    (signal["status"] == "unknown" and signal["value"] is not None)):
                raise ValueError("current signal must be observed or explicit unknown")
        checked[signal_id] = signal
    return checked


def _contract(value):
    expected = {"format", "action_fingerprint", "source", "max_current_age_ms",
                "predicates"}
    if (type(value) is not dict or set(value) != expected or
            value["format"] != CONTRACT_FORMAT or
            not isinstance(value["action_fingerprint"], str) or
            len(value["action_fingerprint"]) != 64 or
            any(char not in "0123456789abcdef" for char in value["action_fingerprint"]) or
            type(value["max_current_age_ms"]) is not int or
            not 1 <= value["max_current_age_ms"] <= 30_000 or
            type(value["predicates"]) is not list or not value["predicates"]):
        raise ValueError("exact nonempty action-validity contract required")
    source = value["source"]
    if (type(source) is not dict or
            set(source) != {"sequence", "capture_ns", "binding", "signals"} or
            type(source["sequence"]) is not int or source["sequence"] < 0 or
            type(source["capture_ns"]) is not int or source["capture_ns"] < 0):
        raise ValueError("exact source evidence required")
    _binding(source["binding"])
    signals = _signals(source["signals"], source=True)
    seen = set()
    for predicate in value["predicates"]:
        if (type(predicate) is not dict or
                set(predicate) != {"signal_id", "operator", "value"} or
                not isinstance(predicate["signal_id"], str) or
                predicate["signal_id"] not in signals or
                predicate["operator"] not in _OPERATORS):
            raise ValueError("predicate must bind a source signal and known operator")
        key = (predicate["signal_id"], predicate["operator"])
        if key in seen:
            raise ValueError("duplicate predicate")
        seen.add(key)
        reference = predicate["value"]
        if predicate["operator"] == "equals":
            if type(reference) not in (bool, int, str):
                raise ValueError("equals requires a scalar JSON value")
        elif (type(reference) not in (int, float) or type(reference) is bool or
              not math.isfinite(reference)):
            raise ValueError("numeric predicate requires a number")
        if predicate["operator"] == "max_decrease_from_source" and reference < 0:
            raise ValueError("maximum decrease must be nonnegative")
    return value


def _snapshot(value):
    expected = {"format", "sequence", "capture_ns", "binding", "signals"}
    if (type(value) is not dict or set(value) != expected or
            value["format"] != SNAPSHOT_FORMAT or
            type(value["sequence"]) is not int or value["sequence"] < 0 or
            type(value["capture_ns"]) is not int or value["capture_ns"] < 0):
        raise ValueError("exact current snapshot required")
    _binding(value["binding"])
    _signals(value["signals"], source=False)
    return value


def _result(status, reason, contract, snapshot, decided_ns, checks):
    return {
        "format": RESULT_FORMAT,
        "status": status,
        "reason": reason,
        "action_may_proceed_to_executor_admission": status == "VALID_CURRENT",
        "requires_new_decision": status != "VALID_CURRENT",
        "grants_input_authority": False,
        "contract": deepcopy(contract),
        "snapshot": deepcopy(snapshot),
        "controller_decided_ns": decided_ns,
        "checks": checks,
    }


def evaluate_action_validity(action, contract, snapshot, controller_decided_ns):
    """Re-evaluate only authored observable predicates on the freshest snapshot."""
    contract = _contract(contract)
    snapshot = _snapshot(snapshot)
    if type(controller_decided_ns) is not int or controller_decided_ns < 0:
        raise ValueError("controller_decided_ns must be a monotonic integer time")
    checks = []
    actual_fingerprint = action_fingerprint(action)
    if actual_fingerprint != contract["action_fingerprint"]:
        return _result("REJECTED_ACTION_BINDING", "action_fingerprint_mismatch",
                       contract, snapshot, controller_decided_ns, checks)
    source = contract["source"]
    if snapshot["binding"] != source["binding"]:
        return _result("REJECTED_STATE_BINDING", "focus_surface_or_geometry_changed",
                       contract, snapshot, controller_decided_ns, checks)
    if (snapshot["sequence"] < source["sequence"] or
            snapshot["capture_ns"] < source["capture_ns"]):
        return _result("REJECTED_SEQUENCE", "snapshot_precedes_source",
                       contract, snapshot, controller_decided_ns, checks)
    if controller_decided_ns < snapshot["capture_ns"]:
        raise ValueError("controller decision precedes current snapshot")
    age_ns = controller_decided_ns - snapshot["capture_ns"]
    if age_ns > contract["max_current_age_ms"] * 1_000_000:
        return _result("REJECTED_STALE", "current_snapshot_too_old",
                       contract, snapshot, controller_decided_ns, checks)
    for predicate in contract["predicates"]:
        signal_id = predicate["signal_id"]
        current = snapshot["signals"].get(signal_id)
        if current is None or current["status"] != "observed":
            return _result("REJECTED_SIGNAL_UNKNOWN", f"{signal_id}_unavailable",
                           contract, snapshot, controller_decided_ns, checks)
        observed = current["value"]
        operator = predicate["operator"]
        expected = predicate["value"]
        try:
            if operator == "equals":
                passed = type(observed) is type(expected) and observed == expected
            elif operator == "minimum":
                passed = observed >= expected
            elif operator == "maximum":
                passed = observed <= expected
            else:
                source_value = source["signals"][signal_id]["value"]
                passed = observed >= source_value - expected
        except TypeError:
            passed = False
        check = {"signal_id": signal_id, "operator": operator,
                 "expected": expected, "observed": observed, "passed": passed}
        checks.append(check)
        if not passed:
            return _result("REJECTED_PREDICATE", f"{signal_id}_{operator}_failed",
                           contract, snapshot, controller_decided_ns, checks)
    return _result("VALID_CURRENT", "all_authored_observable_predicates_hold",
                   contract, snapshot, controller_decided_ns, checks)
