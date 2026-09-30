#!/usr/bin/env python3
"""One frozen five-case SQLite sink delivery experiment for Issue #5508."""
import argparse
import json
from pathlib import Path
import sqlite3

ATTEMPT = "attempt-t13"
EXPECTED_DELIVERY = "d1"
EXPECTED_TARGET = "target-7"
CASES = (
    ("exact_single", (("d1", "target-7", "payload-1"),)),
    ("exact_duplicate", (("d1", "target-7", "payload-1"), ("d1", "target-7", "payload-1"))),
    ("conflicting_payload", (("d1", "target-7", "payload-1"), ("d1", "target-wrong", "payload-2"))),
    ("distinct_delivery", (("d1", "target-7", "payload-1"), ("d2", "target-wrong", "payload-2"))),
    ("out_of_order", (("d2", "target-wrong", "payload-2"), ("d1", "target-7", "payload-1"))),
)


def connect(path):
    db = sqlite3.connect(path, timeout=5)
    db.execute("PRAGMA journal_mode=DELETE")
    db.execute("PRAGMA synchronous=FULL")
    return db


def apply_sink_call(db_path, delivery_id, target, payload):
    with connect(db_path) as db:
        db.execute("BEGIN IMMEDIATE")
        try:
            db.execute("INSERT INTO deliveries VALUES(?,?,?,?)",
                       (delivery_id, ATTEMPT, target, payload))
        except sqlite3.IntegrityError:
            existing = db.execute(
                "SELECT attempt_id,target,payload FROM deliveries WHERE delivery_id=?",
                (delivery_id,)).fetchone()
            db.rollback()
            if existing == (ATTEMPT, target, payload):
                return "IDENTICAL_DUPLICATE_SUPPRESSED"
            return "CONFLICT_REJECTED"
        db.execute("UPDATE target_state SET target=? WHERE singleton=1", (target,))
        db.commit()
        return "INSERTED"


def load_state(journal_path, sink_path):
    with connect(journal_path) as db:
        receipt = db.execute(
            "SELECT receipt_id,generation,state,attempt_id,delivery_id FROM receipts").fetchone()
    with connect(sink_path) as db:
        rows = db.execute(
            "SELECT delivery_id,attempt_id,target,payload FROM deliveries ORDER BY delivery_id").fetchall()
        target = db.execute("SELECT target FROM target_state WHERE singleton=1").fetchone()[0]
    return dict(zip(("receipt_id", "generation", "state", "attempt_id", "delivery_id"), receipt)), [
        dict(zip(("delivery_id", "attempt_id", "target", "payload"), row)) for row in rows], target


def execute(case_id, calls, root):
    folder = root / case_id
    folder.mkdir(parents=True)
    journal, sink = folder / "receipt.sqlite", folder / "sink.sqlite"
    with connect(journal) as db:
        db.execute("CREATE TABLE receipts(receipt_id TEXT PRIMARY KEY,generation INTEGER,state TEXT,attempt_id TEXT,delivery_id TEXT)")
        db.execute("INSERT INTO receipts VALUES('receipt-t13',1,'CONSUMED',?,?)", (ATTEMPT, EXPECTED_DELIVERY))
    with connect(sink) as db:
        db.execute("CREATE TABLE deliveries(delivery_id TEXT PRIMARY KEY,attempt_id TEXT NOT NULL,target TEXT NOT NULL,payload TEXT NOT NULL)")
        db.execute("CREATE TABLE target_state(singleton INTEGER PRIMARY KEY CHECK(singleton=1),target TEXT NOT NULL)")
        db.execute("INSERT INTO target_state VALUES(1,'initial')")
    events = []
    for index, (delivery_id, target, payload) in enumerate(calls):
        outcome = apply_sink_call(sink, delivery_id, target, payload)
        events.append({"index": index, "delivery_id": delivery_id, "attempt_id": ATTEMPT,
                       "target": target, "payload": payload, "sink_outcome": outcome})
    receipt, rows, semantic_target = load_state(journal, sink)
    matches = [row for row in rows if row["delivery_id"] == EXPECTED_DELIVERY
               and row["attempt_id"] == receipt["attempt_id"]
               and row["target"] == EXPECTED_TARGET]
    conflict = any(event["sink_outcome"] == "CONFLICT_REJECTED" for event in events)
    recovery = ("CONFIRMED_SAME_ATTEMPT" if receipt["state"] == "CONSUMED"
                and len(rows) == 1 and len(matches) == 1 and semantic_target == EXPECTED_TARGET
                and not conflict else "UNKNOWN")
    return {"kind": "trace", "case_id": case_id, "calls": events,
            "receipt": receipt, "sink_rows": rows, "semantic_target": semantic_target,
            "recovery": recovery, "receipt_db": f"raw/formal/db/{case_id}/receipt.sqlite",
            "sink_db": f"raw/formal/db/{case_id}/sink.sqlite"}


def main(outdir):
    root = Path(outdir)
    (root / "db").mkdir(parents=True, exist_ok=True)
    traces = [execute(case_id, calls, root / "db") for case_id, calls in CASES]
    counts = {state: sum(row["recovery"] == state for row in traces)
              for state in ("CONFIRMED_SAME_ATTEMPT", "UNKNOWN", "NOT_STARTED")}
    passed = counts == {"CONFIRMED_SAME_ATTEMPT": 2, "UNKNOWN": 3, "NOT_STARTED": 0}
    print(json.dumps({"kind": "manifest", "schema": "issue-5508-affine-receipt-t13-v1",
                      "scenario_count": len(traces), "decision": "PASS" if passed else "FAIL",
                      "recovery_counts": counts}, sort_keys=True, separators=(",", ":")))
    for trace in traces:
        print(json.dumps(trace, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--outdir", required=True)
    main(parser.parse_args().outdir)
