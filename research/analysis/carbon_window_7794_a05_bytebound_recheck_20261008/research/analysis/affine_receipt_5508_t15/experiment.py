#!/usr/bin/env python3
"""Kill a sink writer after INSERT and before its SQLite COMMIT (Issue #5508 T15)."""
import argparse
import json
from pathlib import Path
import sqlite3
import subprocess
import sys

ATTEMPT = "attempt-t15"
DELIVERY = "d1"
TARGET = "target-7"


def connect(path):
    db = sqlite3.connect(path, timeout=10)
    db.execute("PRAGMA journal_mode=DELETE")
    db.execute("PRAGMA synchronous=FULL")
    return db


def init(journal, sink):
    with connect(journal) as db:
        db.execute("CREATE TABLE receipts(receipt_id TEXT PRIMARY KEY,generation INTEGER,state TEXT,attempt_id TEXT,delivery_id TEXT)")
        db.execute("INSERT INTO receipts VALUES('receipt-t15',1,'CONSUMED',?,?)", (ATTEMPT, DELIVERY))
    with connect(sink) as db:
        db.execute("CREATE TABLE deliveries(delivery_id TEXT PRIMARY KEY,attempt_id TEXT NOT NULL,target TEXT NOT NULL,payload TEXT NOT NULL)")
        db.execute("CREATE TABLE target_state(singleton INTEGER PRIMARY KEY CHECK(singleton=1),target TEXT NOT NULL)")
        db.execute("INSERT INTO target_state VALUES(1,'initial')")


def worker(sink):
    with connect(sink) as db:
        db.execute("BEGIN IMMEDIATE")
        db.execute("INSERT INTO deliveries VALUES(?,?,?,?)", (DELIVERY, ATTEMPT, TARGET, "payload-1"))
        print("PRECOMMIT", flush=True)
        sys.stdin.readline()
        db.execute("UPDATE target_state SET target=? WHERE singleton=1", (TARGET,))
        db.commit()
    return 0


def snapshot(journal, sink):
    with connect(journal) as db:
        raw = db.execute("SELECT receipt_id,generation,state,attempt_id,delivery_id FROM receipts").fetchone()
    receipt = dict(zip(("receipt_id", "generation", "state", "attempt_id", "delivery_id"), raw))
    with connect(sink) as db:
        raw_rows = db.execute("SELECT delivery_id,attempt_id,target,payload FROM deliveries ORDER BY delivery_id").fetchall()
        target = db.execute("SELECT target FROM target_state WHERE singleton=1").fetchone()[0]
    rows = [dict(zip(("delivery_id", "attempt_id", "target", "payload"), row)) for row in raw_rows]
    return receipt, rows, target


def main(outdir):
    root = Path(outdir)
    root.mkdir(parents=True, exist_ok=True)
    journal, sink = root / "receipt.sqlite", root / "sink.sqlite"
    init(journal, sink)
    proc = subprocess.Popen([sys.executable, "-B", str(Path(__file__).resolve()), "--worker", str(sink)],
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True, bufsize=1)
    barrier = proc.stdout.readline().strip()
    if barrier != "PRECOMMIT":
        out, err = proc.communicate(timeout=10)
        exit_code = proc.returncode
        events = [barrier, *out.splitlines()]
    else:
        proc.kill()
        exit_code = proc.wait(timeout=10)
        events = [barrier]
        err = proc.stderr.read()
    receipt, rows, target = snapshot(journal, sink)
    recovery = "UNKNOWN" if receipt["state"] == "CONSUMED" and not rows else "CONFIRMED_SAME_ATTEMPT"
    decision = "PASS" if (barrier == "PRECOMMIT" and exit_code == -9 and err == ""
                            and receipt == {"receipt_id": "receipt-t15", "generation": 1, "state": "CONSUMED",
                                            "attempt_id": ATTEMPT, "delivery_id": DELIVERY}
                            and rows == [] and target == "initial" and recovery == "UNKNOWN") else "FAIL"
    trace = {"kind": "trace", "events": events, "child_exit": exit_code, "child_stderr": err,
             "receipt": receipt, "sink_rows": rows, "semantic_target": target, "recovery": recovery}
    print(json.dumps({"kind": "manifest", "schema": "issue-5508-affine-receipt-t15-v1",
                      "scenario_count": 1, "decision": decision}, sort_keys=True, separators=(",", ":")))
    print(json.dumps(trace, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker")
    parser.add_argument("--outdir")
    args = parser.parse_args()
    if args.worker:
        raise SystemExit(worker(args.worker))
    if not args.outdir:
        parser.error("--outdir is required")
    main(args.outdir)
