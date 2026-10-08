"""Independent full-permutation lifecycle oracle and raw-only DPOR audit."""

from __future__ import annotations

import json
from itertools import permutations
from math import factorial


_RESOURCE_FIELDS = ("reads", "writes", "guards", "enables", "effects", "authority_epoch")


def _initial():
    return {
        "task_generation": 1,
        "observation_generation": 1,
        "lease_open": True,
        "authority_epoch": 1,
        "cancelled": False,
        "dispatch_accepted": False,
        "physical_release": False,
        "effect_receipt": False,
        "acknowledged": False,
        "diagnostic_markers": [],
        "violations": [],
    }


def _execute(state, event):
    following = dict(state)
    following["violations"] = list(state["violations"])
    identifier = event["id"]
    kind = event["kind"]
    if kind == "observation_update":
        following["observation_generation"] = state["observation_generation"] + 1
        result = "updated"
    elif kind == "lease_revoke":
        following["lease_open"] = False
        following["authority_epoch"] = state["authority_epoch"] + 1
        result = "revoked"
    elif kind == "cancel":
        following["cancelled"] = True
        result = "cancelled"
    elif kind == "dispatch":
        if not state["lease_open"] or state["cancelled"]:
            result = "blocked_authority_or_cancel"
        elif state["observation_generation"] != state["task_generation"]:
            result = "blocked_stale_generation"
        else:
            following["dispatch_accepted"] = True
            result = "accepted"
    elif kind == "release":
        if not state["dispatch_accepted"]:
            result = "blocked_no_dispatch"
        elif not state["lease_open"]:
            result = "blocked_revoked_authority"
        elif state["observation_generation"] != state["task_generation"]:
            result = "blocked_stale_generation"
        else:
            following["physical_release"] = True
            result = "released"
    elif kind == "effect_receipt":
        if state["physical_release"]:
            following["effect_receipt"] = True
            result = "verified_effect"
        else:
            result = "unknown_no_release_receipt"
    elif kind == "acknowledgement":
        if state["effect_receipt"]:
            following["acknowledged"] = True
            result = "acknowledged"
        else:
            following["violations"].append("ACK_BEFORE_EFFECT_RECEIPT")
            result = "violation_ack_without_receipt"
    elif kind == "diagnostic_marker":
        following["diagnostic_markers"] = sorted([*state["diagnostic_markers"], identifier])
        result = "marker_recorded"
    else:
        raise ValueError(f"unknown event kind: {kind}")
    receipt = {"event_id": identifier, "kind": kind, "status": result}
    return following, receipt


def _key(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _outcome(state, receipts):
    by_event = {receipt["event_id"]: receipt for receipt in receipts}
    return _key({"final_state": state, "outputs_by_event": by_event})


def _declared_independence(events):
    footprints = {}
    for event in events:
        identifier = event.get("id")
        if not isinstance(identifier, str) or not identifier or identifier in footprints:
            return None
        if event.get("unknown_dependency"):
            footprints[identifier] = None
            continue
        if any(not isinstance(event.get(field), list) for field in _RESOURCE_FIELDS):
            footprints[identifier] = None
            continue
        resources = set()
        for field in _RESOURCE_FIELDS:
            resources.update(event[field])
        footprints[identifier] = resources
    identifiers = sorted(footprints)
    result = set()
    for index, left in enumerate(identifiers):
        for right in identifiers[index + 1 :]:
            a, b = footprints[left], footprints[right]
            if a is not None and b is not None and a.isdisjoint(b):
                result.add(frozenset((left, right)))
    return result


def _raw_pairs(values):
    try:
        return {frozenset(pair) for pair in values if len(pair) == 2}
    except (TypeError, ValueError):
        return set()


def _replay(events, order):
    by_id = {event["id"]: event for event in events}
    state = _initial()
    receipts = []
    for identifier in order:
        state, receipt = _execute(state, by_id[identifier])
        receipts.append(receipt)
    return state, receipts


def _full_oracle(events):
    identifiers = tuple(event["id"] for event in events)
    outcomes = set()
    violation_names = set()
    witnesses = {}
    reachable = {}
    for order in permutations(identifiers):
        state = _initial()
        receipts = []
        remaining = set(identifiers)
        for depth, identifier in enumerate(order):
            state_key = _key(state)
            if len(remaining) > 1:
                reachable[(state_key, tuple(sorted(remaining)))] = state
            state, receipt = _execute(state, next(event for event in events if event["id"] == identifier))
            receipts.append(receipt)
            remaining.remove(identifier)
            for violation in state["violations"]:
                violation_names.add(violation)
                witnesses.setdefault(violation, list(order[: depth + 1]))
        outcomes.add(_outcome(state, receipts))
    return outcomes, violation_names, witnesses, reachable


def _pair_is_commutative(states, left, right, by_id):
    for state in states:
        after_left, left_receipt = _execute(state, by_id[left])
        left_right, right_after_left = _execute(after_left, by_id[right])
        after_right, right_receipt = _execute(state, by_id[right])
        right_left, left_after_right = _execute(after_right, by_id[left])
        if left_right != right_left:
            return False
        if {left_receipt["event_id"]: left_receipt, right_after_left["event_id"]: right_after_left} != {
            right_receipt["event_id"]: right_receipt,
            left_after_right["event_id"]: left_after_right,
        }:
            return False
    return True


def audit(public, truth, raw):
    errors = []
    expected_counts = truth.get("expected_full_schedule_counts", {})
    raw_rows = raw.get("cases", []) if isinstance(raw, dict) else []
    rows_by_id = {row.get("case_id"): row for row in raw_rows if isinstance(row, dict)}
    if raw.get("schema") != "bounded-dpor-candidate-v1":
        errors.append("candidate schema mismatch")
    if len(rows_by_id) != len(public.get("cases", [])):
        errors.append("case coverage mismatch")
    summary = {"full_schedules": 0, "reduced_schedules": 0, "violations": [], "cases": {}}

    for case in public.get("cases", []):
        case_id = case["case_id"]
        events = case["events"]
        identifiers = [event["id"] for event in events]
        row = rows_by_id.get(case_id)
        if row is None:
            errors.append(f"missing candidate case: {case_id}")
            continue
        expected_pairs = _declared_independence(events)
        actual_pairs = _raw_pairs(row.get("independent_pairs", []))
        if expected_pairs is None or actual_pairs != expected_pairs:
            errors.append(f"dependency declaration mismatch: {case_id}")
        outcomes, violations, full_witnesses, reachable = _full_oracle(events)
        summary["full_schedules"] += factorial(len(identifiers))
        traces = row.get("schedule_traces", [])
        if len(traces) != row.get("reduced_schedule_count") or not traces:
            errors.append(f"trace count mismatch: {case_id}")
        if len({trace.get("schedule_id") for trace in traces}) != len(traces):
            errors.append(f"duplicate schedule identity: {case_id}")
        candidate_outcomes = set()
        candidate_orders = set()
        violation_witness_found = set()
        by_id = {event["id"]: event for event in events}
        for trace in traces:
            order = trace.get("order", [])
            if len(order) != len(identifiers) or set(order) != set(identifiers) or tuple(order) in candidate_orders:
                errors.append(f"invalid or duplicate schedule: {case_id}")
                continue
            candidate_orders.add(tuple(order))
            state, receipts = _replay(events, order)
            if trace.get("final_state") != state or trace.get("outputs") != receipts:
                errors.append(f"replay mismatch: {case_id}")
                continue
            candidate_outcomes.add(_outcome(state, receipts))
            for violation in state["violations"]:
                violation_witness_found.add(violation)
        for violation in violations:
            if violation not in violation_witness_found and violation in truth.get("required_violations", [truth.get("required_violation")]):
                errors.append(f"violation witness missing: {case_id}:{violation}")
        if candidate_outcomes != outcomes:
            errors.append(f"outcome set mismatch: {case_id}")
        baseline = row.get("ordered_pair_baseline", {})
        expected_ordered_pairs = set(permutations(identifiers, 2))
        actual_ordered_pairs = {
            tuple(pair) for pair in baseline.get("ordered_pairs", []) if isinstance(pair, list) and len(pair) == 2
        }
        pair_traces = baseline.get("pair_traces", [])
        if (
            baseline.get("trace_count") != len(expected_ordered_pairs)
            or len(pair_traces) != len(expected_ordered_pairs)
            or actual_ordered_pairs != expected_ordered_pairs
        ):
            errors.append(f"ordered-pair baseline coverage mismatch: {case_id}")
        frozen_pair_count = truth.get("expected_ordered_pair_baseline_counts", {}).get(case_id)
        if frozen_pair_count is not None and baseline.get("trace_count") != frozen_pair_count:
            errors.append(f"frozen ordered-pair baseline count mismatch: {case_id}")
        for pair_trace in pair_traces:
            pair_order = pair_trace.get("order", [])
            if tuple(pair_order) not in expected_ordered_pairs:
                errors.append(f"invalid ordered-pair baseline trace: {case_id}")
                continue
            pair_state, pair_receipts = _replay(events, pair_order)
            if pair_trace.get("final_state") != pair_state or pair_trace.get("outputs") != pair_receipts:
                errors.append(f"ordered-pair baseline replay mismatch: {case_id}")
        if row.get("full_schedule_count") != expected_counts.get(case_id):
            errors.append(f"frozen full schedule count mismatch: {case_id}")
        for pair in actual_pairs:
            left, right = sorted(pair)
            pair_states = [state for (_, remaining), state in reachable.items() if left in remaining and right in remaining]
            if not _pair_is_commutative(pair_states, left, right, by_id):
                errors.append(f"unsound independence: {case_id}:{left}:{right}")
        summary["reduced_schedules"] += len(traces)
        summary["violations"].extend(sorted(violations))
        summary["cases"][case_id] = {
            "full_schedule_count": row.get("full_schedule_count"),
            "reduced_schedule_count": len(traces),
            "reachable_outcome_count": len(outcomes),
            "independent_pair_count": len(actual_pairs),
            "ordered_pair_baseline_trace_count": baseline.get("trace_count"),
            "violations": sorted(violations),
            "witnesses": full_witnesses,
        }

    summary["violations"] = sorted(set(summary["violations"]))
    required_violations = truth.get("required_violations", [])
    if "required_violation" in truth:
        required_violations = [*required_violations, truth["required_violation"]]
    for required in required_violations:
        if required not in summary["violations"]:
            errors.append(f"frozen required violation not reproduced: {required}")
    control = summary["cases"].get("commuting_heavy_diagnostics")
    if control and control["full_schedule_count"]:
        summary["commuting_control_reduction_fraction"] = 1 - (
            control["reduced_schedule_count"] / control["full_schedule_count"]
        )
        minimum_reduction = truth.get("minimum_commuting_control_reduction_fraction", 0.2)
        if summary["commuting_control_reduction_fraction"] < minimum_reduction:
            errors.append("commuting control reduction below frozen 20% gate")
    return {
        "status": "PASS_DPOR_METHOD_SCOPED" if not errors else "FAIL_AUDIT",
        "errors": errors,
        "summary": summary,
    }
