"""Independent raw-ledger verifier. Does not import candidate policy code."""

from __future__ import annotations

import json
import sys


POLICIES = ("EPOCH_ONLY", "TIME_DELAY", "ACCOUNTED_QUIESCENCE")
SNAPSHOTS = ("boundary", "grace_deadline", "horizon")
EVENT_KINDS = {
    "ADMISSION", "TAKEOVER", "ENQUEUE", "START", "EFFECT",
    "COMPLETE_ACK", "CANCEL_ACK", "INPUT_DOWN", "INPUT_RELEASE_ACK",
    "OBSERVATION", "BACKEND_RESTART", "RECONCILIATION_ACK",
}


def _independent_certificate(events: list[dict], cutoff: int) -> bool:
    observed = [e for e in events if e["t"] <= cutoff]
    handoffs = [e for e in observed if e["kind"] == "TAKEOVER"]
    if len(handoffs) != 1:
        return False
    handoff = handoffs[0]
    handoff_order = (handoff["t"], handoff["seq"])
    admissions: dict[str, list[dict]] = {}
    for e in observed:
        if e["kind"] != "ADMISSION":
            continue
        event_order = (e["t"], e["seq"])
        if e.get("epoch") == 1 and event_order > handoff_order:
            if e.get("decision") != "REJECTED_STALE":
                return False
        if e.get("decision") == "ACCEPTED":
            admissions.setdefault(e.get("op_id", ""), []).append(e)

    current_generation = max((e.get("backend_gen", 1) for e in observed), default=1)
    for op_id, starts in admissions.items():
        if not op_id or len(starts) != 1:
            return False
        own = [e for e in observed if e.get("op_id") == op_id]
        valid_terminals = []
        for terminal in own:
            at = (terminal["t"], terminal["seq"])
            before = [e for e in own if (e["t"], e["seq"]) < at]
            if terminal["kind"] == "COMPLETE_ACK":
                has_effect = any(e["kind"] == "EFFECT"
                                 and e.get("backend_gen") == terminal.get("backend_gen")
                                 for e in before)
                if has_effect:
                    valid_terminals.append(terminal)
            elif terminal["kind"] == "CANCEL_ACK":
                prior_kinds = {e["kind"] for e in before}
                before_start = (terminal.get("outcome") == "CANCELLED_BEFORE_START"
                                and "START" not in prior_kinds and "EFFECT" not in prior_kinds)
                before_effect = (terminal.get("outcome") == "CANCELLED_BEFORE_EFFECT"
                                 and "EFFECT" not in prior_kinds)
                if before_start or before_effect:
                    valid_terminals.append(terminal)
            elif terminal["kind"] == "RECONCILIATION_ACK":
                if (terminal.get("backend_gen") == current_generation
                        and terminal.get("outcome") in
                        {"COMPLETED", "CANCELLED_BEFORE_START", "CANCELLED_BEFORE_EFFECT"}):
                    valid_terminals.append(terminal)
        if not valid_terminals:
            return False
        latest_terminal = max(valid_terminals, key=lambda e: (e["t"], e["seq"]))
        restart_after_admission = any(
            e["kind"] == "BACKEND_RESTART"
            and (e["t"], e["seq"]) > (starts[0]["t"], starts[0]["seq"])
            for e in observed
        )
        if (restart_after_admission
                and latest_terminal.get("backend_gen") != current_generation):
            return False

    held = {(e.get("op_id"), e.get("input")) for e in observed
            if e["kind"] == "INPUT_DOWN"}
    released = {(e.get("op_id"), e.get("input")) for e in observed
                if e["kind"] == "INPUT_RELEASE_ACK"}
    if held - released:
        return False

    for receipt in observed:
        if receipt["kind"] == "OBSERVATION" and receipt.get("epoch") == 2:
            if receipt.get("freshness") != "FRESH" or receipt["t"] <= handoff["t"]:
                continue
            prior_state = max((e["seq"] for e in observed
                               if e["seq"] < receipt["seq"]
                               and e["kind"] != "OBSERVATION"), default=0)
            if receipt.get("covers_through_seq", -1) >= prior_state:
                return True
    return False


def audit(raw: dict) -> dict:
    errors: list[str] = []
    rows = raw.get("rows")
    if raw.get("schema") != "observable-quiescence-raw-v1" or not isinstance(rows, list):
        return {"status": "FAIL_METHOD", "errors": ["invalid_top_level_schema"]}
    seen_cases = set()
    false_quiescent = {name: 0 for name in POLICIES}
    compared = 0
    for row in rows:
        case_id = row.get("case_id")
        if not isinstance(case_id, str) or case_id in seen_cases:
            errors.append("duplicate_or_missing_case_identity")
            continue
        seen_cases.add(case_id)
        events = row.get("events")
        decisions = row.get("decisions")
        if not isinstance(events, list) or not isinstance(decisions, list):
            errors.append(f"missing_ledger_or_decisions:{case_id}")
            continue
        if [e.get("seq") for e in events] != list(range(1, len(events) + 1)):
            errors.append(f"noncontiguous_event_sequence:{case_id}")
        if events != sorted(events, key=lambda e: (e.get("t", -1), e.get("seq", -1))):
            errors.append(f"event_order_violation:{case_id}")
        if any(e.get("kind") not in EVENT_KINDS for e in events):
            errors.append(f"unknown_event_kind:{case_id}")
        accepted_ids = {e.get("op_id") for e in events
                        if e.get("kind") == "ADMISSION"
                        and e.get("decision") == "ACCEPTED"}
        bound_kinds = {"ENQUEUE", "START", "EFFECT", "COMPLETE_ACK",
                       "CANCEL_ACK", "INPUT_DOWN", "INPUT_RELEASE_ACK",
                       "RECONCILIATION_ACK"}
        for e in events:
            if e.get("kind") in bound_kinds and e.get("op_id") not in accepted_ids:
                errors.append(f"unbound_operation_event:{case_id}:{e.get('seq')}")
            if e.get("kind") == "ADMISSION" and e.get("decision") not in {
                "ACCEPTED", "REJECTED_STALE"
            }:
                errors.append(f"invalid_admission_decision:{case_id}:{e.get('seq')}")
        takeover_for_order = next((e for e in events if e.get("kind") == "TAKEOVER"), None)
        if takeover_for_order:
            boundary_key = (takeover_for_order["t"], takeover_for_order["seq"])
            for e in events:
                if (e.get("kind") == "ADMISSION" and e.get("epoch") == 1
                        and (e["t"], e["seq"]) > boundary_key
                        and e.get("decision") != "REJECTED_STALE"):
                    errors.append(f"old_epoch_admission_accepted:{case_id}")
        handoffs = [e for e in events if e.get("kind") == "TAKEOVER"]
        if len(handoffs) != 1:
            errors.append(f"takeover_cardinality:{case_id}")
            continue
        boundary = handoffs[0]["t"]
        horizon = max(e["t"] for e in events)
        expected = {(p, s) for p in POLICIES for s in SNAPSHOTS}
        actual = {(d.get("policy"), d.get("snapshot")) for d in decisions}
        if actual != expected or len(decisions) != len(expected):
            errors.append(f"decision_matrix_mismatch:{case_id}")
            continue
        by_key = {(d["policy"], d["snapshot"]): d for d in decisions}
        for snap, instant in (("boundary", boundary),
                              ("grace_deadline", boundary + 1),
                              ("horizon", horizon)):
            certified = _independent_certificate(events, instant)
            compared += 1
            for policy in POLICIES:
                decision = by_key[(policy, snap)]
                if decision.get("t") != instant or decision.get("status") not in {
                    "QUIESCENT", "UNKNOWN"
                }:
                    errors.append(f"malformed_decision:{case_id}:{policy}:{snap}")
                    continue
                expected_q = (policy == "EPOCH_ONLY"
                              or (policy == "TIME_DELAY" and instant >= boundary + 1)
                              or (policy == "ACCOUNTED_QUIESCENCE" and certified))
                if (decision["status"] == "QUIESCENT") != expected_q:
                    errors.append(f"decision_mismatch:{case_id}:{policy}:{snap}")
                if decision["status"] == "QUIESCENT" and not certified:
                    false_quiescent[policy] += 1
                if policy == "ACCOUNTED_QUIESCENCE" and decision.get("reasons") is None:
                    errors.append(f"missing_reason_field:{case_id}:{snap}")
    if not rows:
        errors.append("empty_experiment")
    if false_quiescent["ACCOUNTED_QUIESCENCE"]:
        errors.append("accounted_false_quiescent")
    if false_quiescent["EPOCH_ONLY"] == 0 or false_quiescent["TIME_DELAY"] == 0:
        errors.append("comparators_not_discriminated")
    return {"status": "PASS_METHOD_SCOPED" if not errors else "FAIL_METHOD",
            "case_count": len(seen_cases), "snapshot_count": compared,
            "false_quiescent": false_quiescent, "errors": errors}


if __name__ == "__main__":
    result = audit(json.load(sys.stdin))
    json.dump(result, sys.stdout, sort_keys=True, indent=2)
    sys.stdout.write("\n")
    raise SystemExit(0 if result["status"] == "PASS_METHOD_SCOPED" else 1)
