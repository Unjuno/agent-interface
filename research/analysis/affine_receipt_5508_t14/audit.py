#!/usr/bin/env python3
"""Independent auditor for T14; recomputes expected serialization outcomes."""
import json
from pathlib import Path
import sqlite3
import sys

WORKERS = 8
CASES = {
    "same_delivery_race": ["d1"] * WORKERS,
    "distinct_delivery_race": [f"d{i}" for i in range(1, WORKERS + 1)],
}


def read_state(receipt_path):
    with sqlite3.connect(receipt_path) as db:
        receipt = db.execute("SELECT receipt_id,generation,state,attempt_id,delivery_id FROM receipts").fetchone()
    with sqlite3.connect(receipt_path.parent / "sink.sqlite") as db:
        rows = db.execute("SELECT delivery_id,attempt_id,target,payload FROM deliveries ORDER BY delivery_id").fetchall()
        target = db.execute("SELECT target FROM target_state WHERE singleton=1").fetchone()[0]
    return (dict(zip(("receipt_id", "generation", "state", "attempt_id", "delivery_id"), receipt)),
            [dict(zip(("delivery_id", "attempt_id", "target", "payload"), row)) for row in rows], target)


def audit(path):
    lines = [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line]
    errors = []
    if len(lines) != 3 or lines[0].get("kind") != "manifest":
        errors.append("manifest_or_line_count")
    if not lines or lines[0].get("schema") != "issue-5508-affine-receipt-t14-v1":
        return {"audit": "FAIL", "errors": errors + ["schema"]}
    counts = {"CONFIRMED_SAME_ATTEMPT": 0, "UNKNOWN": 0}
    seen = set()
    for trace in lines[1:]:
        case_id = trace.get("case_id")
        if case_id not in CASES or case_id in seen:
            errors.append(f"case_identity:{case_id}")
            continue
        seen.add(case_id)
        delivery_ids = CASES[case_id]
        workers = trace.get("workers", [])
        expected = [{"worker_id": i, "delivery_id": delivery, "attempt_id": "attempt-t14",
                     "target": "target-7", "payload": "payload-1"}
                    for i, delivery in enumerate(delivery_ids)]
        if len(workers) != WORKERS: errors.append(f"worker_count:{case_id}")
        for i, (worker, expected_input) in enumerate(zip(workers, expected)):
            if {key: worker.get(key) for key in expected_input} != expected_input:
                errors.append(f"worker_input:{case_id}:{i}")
        if len(trace.get("readiness", [])) != WORKERS or not all(x.get("ready") is True for x in trace.get("readiness", [])):
            errors.append(f"readiness:{case_id}")
        if len(trace.get("exits", [])) != WORKERS or any(x.get("returncode") != 0 for x in trace.get("exits", [])):
            errors.append(f"worker_exit:{case_id}")
        sink_path = Path(path).parent / trace.get("receipt_db", "").removeprefix("raw/formal/")
        try:
            receipt, rows, target = read_state(sink_path)
        except Exception as exc:
            errors.append(f"database_read:{case_id}:{type(exc).__name__}")
            continue
        expected_receipt = {"receipt_id": "receipt-t14", "generation": 1, "state": "CONSUMED",
                            "attempt_id": "attempt-t14", "delivery_id": "d1"}
        if receipt != expected_receipt or trace.get("receipt") != receipt: errors.append(f"receipt:{case_id}")
        if target != "target-7" or trace.get("semantic_target") != target: errors.append(f"target:{case_id}")
        if trace.get("sink_rows") != rows: errors.append(f"snapshot:{case_id}")
        if case_id == "same_delivery_race":
            if len(rows) != 1 or rows != [{"delivery_id": "d1", "attempt_id": "attempt-t14", "target": "target-7", "payload": "payload-1"}]:
                errors.append("same_delivery_cardinality")
            outcomes = [worker.get("outcome") for worker in workers]
            if outcomes.count("INSERTED") != 1 or outcomes.count("IDENTICAL_DUPLICATE_SUPPRESSED") != 7:
                errors.append("same_delivery_outcomes")
            decision = "CONFIRMED_SAME_ATTEMPT"
        else:
            if len(rows) != WORKERS or [row["delivery_id"] for row in rows] != [f"d{i}" for i in range(1, WORKERS + 1)]:
                errors.append("distinct_delivery_cardinality")
            if any(worker.get("outcome") != "INSERTED" for worker in workers): errors.append("distinct_delivery_outcomes")
            decision = "UNKNOWN"
        counts[decision] += 1
        if trace.get("recovery") != decision: errors.append(f"recovery:{case_id}")
    if seen != set(CASES): errors.append("case_set")
    expected_decision = "PASS" if counts == {"CONFIRMED_SAME_ATTEMPT": 1, "UNKNOWN": 1} else "FAIL"
    if lines[0].get("scenario_count") != 2 or lines[0].get("worker_count_per_case") != WORKERS:
        errors.append("manifest_dimensions")
    if lines[0].get("recovery_counts") != counts: errors.append("manifest_counts")
    if lines[0].get("decision") != expected_decision: errors.append("manifest_decision")
    return {"audit": "PASS" if not errors else "FAIL", "errors": errors,
            "independent_counts": counts, "decision": expected_decision}


if __name__ == "__main__":
    print(json.dumps(audit(sys.argv[1]), sort_keys=True, separators=(",", ":")))
