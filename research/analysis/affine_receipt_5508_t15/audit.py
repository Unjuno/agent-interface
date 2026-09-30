#!/usr/bin/env python3
"""Independent auditor for the one-case T15 pre-commit kill boundary."""
import json
from pathlib import Path
import sqlite3
import sys


def read_db(root):
    with sqlite3.connect(root / "receipt.sqlite") as db:
        receipt = db.execute("SELECT receipt_id,generation,state,attempt_id,delivery_id FROM receipts").fetchone()
    with sqlite3.connect(root / "sink.sqlite") as db:
        rows = db.execute("SELECT delivery_id,attempt_id,target,payload FROM deliveries ORDER BY delivery_id").fetchall()
        target = db.execute("SELECT target FROM target_state WHERE singleton=1").fetchone()[0]
    return (dict(zip(("receipt_id", "generation", "state", "attempt_id", "delivery_id"), receipt)),
            [dict(zip(("delivery_id", "attempt_id", "target", "payload"), row)) for row in rows], target)


def audit(output):
    output = Path(output)
    lines = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines() if line]
    errors = []
    if len(lines) != 2 or lines[0].get("kind") != "manifest": errors.append("manifest_or_line_count")
    if not lines or lines[0].get("schema") != "issue-5508-affine-receipt-t15-v1":
        return {"audit": "FAIL", "errors": errors + ["schema"]}
    trace = lines[1]
    root = output.parent
    try:
        receipt, rows, target = read_db(root)
    except Exception as exc:
        return {"audit": "FAIL", "errors": errors + [f"database_read:{type(exc).__name__}"]}
    expected_receipt = {"receipt_id": "receipt-t15", "generation": 1, "state": "CONSUMED",
                        "attempt_id": "attempt-t15", "delivery_id": "d1"}
    if trace.get("events") != ["PRECOMMIT"]: errors.append("precommit_barrier")
    if trace.get("child_exit") != -9 or trace.get("child_stderr") != "": errors.append("child_kill")
    if receipt != expected_receipt or trace.get("receipt") != receipt: errors.append("receipt_lineage")
    if rows != [] or trace.get("sink_rows") != rows: errors.append("uncommitted_row_persisted")
    if target != "initial" or trace.get("semantic_target") != target: errors.append("target_state")
    expected_recovery = "UNKNOWN" if receipt["state"] == "CONSUMED" and not rows else "CONFIRMED_SAME_ATTEMPT"
    if trace.get("recovery") != expected_recovery or expected_recovery != "UNKNOWN": errors.append("recovery")
    if lines[0].get("scenario_count") != 1 or lines[0].get("decision") != "PASS": errors.append("manifest")
    return {"audit": "PASS" if not errors else "FAIL", "errors": errors,
            "independent_recovery": expected_recovery,
            "decision": "PASS" if not errors else "FAIL"}


if __name__ == "__main__":
    print(json.dumps(audit(sys.argv[1]), sort_keys=True, separators=(",", ":")))
