#!/usr/bin/env python3
"""Independent T13 auditor; reconstructs the sink policy without importing candidate code."""
import json
from pathlib import Path
import sqlite3
import sys

EXPECTED = {
    "exact_single": ([('d1', 'target-7', 'payload-1')], "CONFIRMED_SAME_ATTEMPT"),
    "exact_duplicate": ([('d1', 'target-7', 'payload-1'), ('d1', 'target-7', 'payload-1')], "CONFIRMED_SAME_ATTEMPT"),
    "conflicting_payload": ([('d1', 'target-7', 'payload-1'), ('d1', 'target-wrong', 'payload-2')], "UNKNOWN"),
    "distinct_delivery": ([('d1', 'target-7', 'payload-1'), ('d2', 'target-wrong', 'payload-2')], "UNKNOWN"),
    "out_of_order": ([('d2', 'target-wrong', 'payload-2'), ('d1', 'target-7', 'payload-1')], "UNKNOWN"),
}


def read_db(path):
    with sqlite3.connect(path) as db:
        receipt = db.execute("SELECT receipt_id,generation,state,attempt_id,delivery_id FROM receipts").fetchone()
    with sqlite3.connect(path.parent / "sink.sqlite") as db:
        rows = db.execute("SELECT delivery_id,attempt_id,target,payload FROM deliveries ORDER BY delivery_id").fetchall()
        target = db.execute("SELECT target FROM target_state WHERE singleton=1").fetchone()[0]
    receipt = dict(zip(("receipt_id", "generation", "state", "attempt_id", "delivery_id"), receipt))
    rows = [dict(zip(("delivery_id", "attempt_id", "target", "payload"), row)) for row in rows]
    return receipt, rows, target


def expected_sink(events):
    rows = {}
    outcomes = []
    target = "initial"
    for event in events:
        delivery = event["delivery_id"]
        value = (event["attempt_id"], event["target"], event["payload"])
        if delivery not in rows:
            rows[delivery] = value
            target = event["target"]
            outcomes.append("INSERTED")
        elif rows[delivery] == value:
            outcomes.append("IDENTICAL_DUPLICATE_SUPPRESSED")
        else:
            outcomes.append("CONFLICT_REJECTED")
    return rows, outcomes, target


def audit(path):
    lines = [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line]
    errors = []
    if len(lines) != 6 or lines[0].get("kind") != "manifest":
        errors.append("manifest_or_line_count")
    if not lines or lines[0].get("schema") != "issue-5508-affine-receipt-t13-v1":
        return {"audit": "FAIL", "errors": errors + ["schema"]}
    expected_counts = {"CONFIRMED_SAME_ATTEMPT": 0, "UNKNOWN": 0, "NOT_STARTED": 0}
    for trace in lines[1:]:
        cid = trace.get("case_id")
        if cid not in EXPECTED:
            errors.append(f"unexpected_case:{cid}")
            continue
        expected_calls, expected_recovery = EXPECTED[cid]
        calls = trace.get("calls", [])
        compact = [(e.get("delivery_id"), e.get("target"), e.get("payload")) for e in calls]
        if compact != expected_calls: errors.append(f"input_calls:{cid}")
        db_root = Path(path).parent / trace.get("receipt_db", "").removeprefix("raw/formal/")
        try:
            receipt, rows, target = read_db(db_root)
        except Exception as exc:
            errors.append(f"database_read:{cid}:{type(exc).__name__}")
            continue
        replay, outcomes, replay_target = expected_sink(calls)
        expected_rows = [dict(zip(("delivery_id", "attempt_id", "target", "payload"), (key, *value)))
                         for key, value in sorted(replay.items())]
        if [event.get("sink_outcome") for event in calls] != outcomes: errors.append(f"sink_outcomes:{cid}")
        if rows != expected_rows: errors.append(f"sink_rows:{cid}")
        if target != replay_target: errors.append(f"semantic_target:{cid}")
        expected_receipt = {"receipt_id": "receipt-t13", "generation": 1, "state": "CONSUMED",
                            "attempt_id": "attempt-t13", "delivery_id": "d1"}
        if receipt != expected_receipt or trace.get("receipt") != receipt: errors.append(f"receipt:{cid}")
        if trace.get("sink_rows") != rows or trace.get("semantic_target") != target: errors.append(f"snapshot:{cid}")
        conflict = "CONFLICT_REJECTED" in outcomes
        exact = len(rows) == 1 and rows == [{"delivery_id": "d1", "attempt_id": "attempt-t13",
                                             "target": "target-7", "payload": "payload-1"}]
        decision = "CONFIRMED_SAME_ATTEMPT" if exact and target == "target-7" and not conflict else "UNKNOWN"
        expected_counts[decision] += 1
        if decision != expected_recovery or trace.get("recovery") != decision:
            errors.append(f"recovery:{cid}")
    expected_decision = "PASS" if expected_counts == {"CONFIRMED_SAME_ATTEMPT": 2, "UNKNOWN": 3, "NOT_STARTED": 0} else "FAIL"
    if lines[0].get("scenario_count") != 5: errors.append("scenario_count")
    if lines[0].get("recovery_counts") != expected_counts: errors.append("manifest_counts")
    if lines[0].get("decision") != expected_decision: errors.append("manifest_decision")
    if len({trace.get("case_id") for trace in lines[1:]}) != 5: errors.append("case_uniqueness")
    return {"audit": "PASS" if not errors else "FAIL", "errors": errors,
            "independent_counts": expected_counts, "decision": expected_decision}


if __name__ == "__main__":
    print(json.dumps(audit(sys.argv[1]), sort_keys=True, separators=(",", ":")))
