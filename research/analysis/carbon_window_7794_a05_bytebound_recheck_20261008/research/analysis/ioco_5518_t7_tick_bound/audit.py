#!/usr/bin/env python3
"""Independently replay Issue #5518 T7 traces using a separately written oracle."""
import json
from pathlib import Path
import sys

EXPECTED = {
    "receipt_before_deadline": (True, None),
    "quiescent_at_deadline": (True, None),
    "quiescent_after_deadline": (False, 1),
    "explicit_unknown_after_deadline": (True, None),
    "late_receipt": (False, 1),
    "cancel_then_quiescent": (False, 2),
}
BOUND = 2


def oracle(events):
    phase = "unstarted"
    requested_at = None
    clock = -1
    for i, event in enumerate(events):
        t, kind, label = event.get("tick"), event.get("direction"), event.get("label")
        if not isinstance(t, int) or t < clock:
            return False, i
        clock = t
        if kind == "internal":
            if label != "TAU_RETRY":
                return False, i
            continue
        if phase == "unstarted":
            if kind == "input" and label == "OBSERVE":
                requested_at, phase = t, "observation_open"
                continue
            if kind == "input" and label == "CANCEL":
                phase = "cancel_ack_due"
                continue
            return False, i
        if phase == "observation_open":
            if kind != "output":
                return False, i
            if label == "UNKNOWN":
                phase = "closed"
                continue
            if label == "RECEIPT" and t - requested_at <= BOUND:
                phase = "closed"
                continue
            if label == "QUIESCENT" and t - requested_at <= BOUND:
                continue
            return False, i
        if phase == "cancel_ack_due":
            if kind == "output" and label == "CANCELLED" and t == 0:
                phase = "cancelled"
                continue
            return False, i
        return False, i
    return True, None


def audit(path):
    lines = [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line]
    errors = []
    if len(lines) != 7 or lines[0].get("kind") != "manifest":
        errors.append("manifest_or_line_count")
    if not lines or lines[0].get("schema") != "issue-5518-ioco-t7-v1":
        return {"audit": "FAIL", "errors": errors + ["schema"]}
    counts = {"conformant": 0, "rejected": 0}
    seen = set()
    for trace in lines[1:]:
        case_id = trace.get("case_id")
        if case_id not in EXPECTED or case_id in seen:
            errors.append(f"case_identity:{case_id}")
            continue
        seen.add(case_id)
        expected_decision, expected_cex = EXPECTED[case_id]
        actual_decision, actual_cex = oracle(trace.get("events", []))
        counts["conformant" if actual_decision else "rejected"] += 1
        if (actual_decision, actual_cex) != (expected_decision, expected_cex):
            errors.append(f"oracle_contract:{case_id}")
        if trace.get("expected_conformant") != expected_decision:
            errors.append(f"declared_expected:{case_id}")
        if trace.get("expected_counterexample_index") != expected_cex:
            errors.append(f"declared_cex:{case_id}")
        if trace.get("conformant") != actual_decision or trace.get("counterexample_index") != actual_cex:
            errors.append(f"candidate_disagreement:{case_id}")
    if seen != set(EXPECTED): errors.append("case_set")
    decision = "PASS" if counts == {"conformant": 3, "rejected": 3} else "FAIL"
    if lines[0].get("scenario_count") != 6 or lines[0].get("deadline_tick") != BOUND:
        errors.append("manifest_dimensions")
    if lines[0].get("decision") != decision: errors.append("manifest_decision")
    return {"audit": "PASS" if not errors else "FAIL", "errors": errors,
            "independent_counts": counts, "decision": decision}


if __name__ == "__main__":
    print(json.dumps(audit(sys.argv[1]), sort_keys=True, separators=(",", ":")))
