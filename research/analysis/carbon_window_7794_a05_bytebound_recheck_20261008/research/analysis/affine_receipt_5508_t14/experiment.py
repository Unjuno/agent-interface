#!/usr/bin/env python3
"""Two-case concurrent SQLite sink experiment for Issue #5508."""
import argparse
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import time

ATTEMPT = "attempt-t14"
EXPECTED_TARGET = "target-7"
WORKERS = 8
CASES = (
    ("same_delivery_race", ["d1"] * WORKERS),
    ("distinct_delivery_race", [f"d{i}" for i in range(1, WORKERS + 1)]),
)


def connect(path):
    db = sqlite3.connect(path, timeout=15)
    db.execute("PRAGMA journal_mode=DELETE")
    db.execute("PRAGMA synchronous=FULL")
    return db


def worker(db_path, gate_path, delivery_id, worker_id):
    print("READY", flush=True)
    deadline = time.monotonic() + 15
    while not Path(gate_path).exists():
        if time.monotonic() >= deadline:
            print(json.dumps({"worker_id": worker_id, "error": "gate_timeout"}), flush=True)
            return 21
        time.sleep(0.001)
    with connect(db_path) as db:
        db.execute("BEGIN IMMEDIATE")
        try:
            db.execute("INSERT INTO deliveries VALUES(?,?,?,?)",
                       (delivery_id, ATTEMPT, EXPECTED_TARGET, "payload-1"))
        except sqlite3.IntegrityError:
            prior = db.execute(
                "SELECT attempt_id,target,payload FROM deliveries WHERE delivery_id=?",
                (delivery_id,)).fetchone()
            db.rollback()
            outcome = "IDENTICAL_DUPLICATE_SUPPRESSED" if prior == (ATTEMPT, EXPECTED_TARGET, "payload-1") else "CONFLICT_REJECTED"
        else:
            db.execute("UPDATE target_state SET target=? WHERE singleton=1", (EXPECTED_TARGET,))
            db.commit()
            outcome = "INSERTED"
    print(json.dumps({"worker_id": worker_id, "delivery_id": delivery_id,
                      "attempt_id": ATTEMPT, "target": EXPECTED_TARGET,
                      "payload": "payload-1", "outcome": outcome},
                     sort_keys=True, separators=(",", ":")), flush=True)
    return 0


def run_case(case_id, delivery_ids, root):
    folder = root / case_id
    folder.mkdir(parents=True)
    journal, sink, gate = folder / "receipt.sqlite", folder / "sink.sqlite", folder / "release.gate"
    with connect(journal) as db:
        db.execute("CREATE TABLE receipts(receipt_id TEXT PRIMARY KEY,generation INTEGER,state TEXT,attempt_id TEXT,delivery_id TEXT)")
        db.execute("INSERT INTO receipts VALUES('receipt-t14',1,'CONSUMED',?,'d1')", (ATTEMPT,))
    with connect(sink) as db:
        db.execute("CREATE TABLE deliveries(delivery_id TEXT PRIMARY KEY,attempt_id TEXT NOT NULL,target TEXT NOT NULL,payload TEXT NOT NULL)")
        db.execute("CREATE TABLE target_state(singleton INTEGER PRIMARY KEY CHECK(singleton=1),target TEXT NOT NULL)")
        db.execute("INSERT INTO target_state VALUES(1,'initial')")
    procs = []
    try:
        for worker_id, delivery_id in enumerate(delivery_ids):
            proc = subprocess.Popen(
                [sys.executable, "-B", str(Path(__file__).resolve()), "--worker",
                 str(sink), str(gate), delivery_id, str(worker_id)],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
            procs.append(proc)
        readiness = []
        for worker_id, proc in enumerate(procs):
            line = proc.stdout.readline().strip()
            readiness.append({"worker_id": worker_id, "ready": line == "READY", "event": line})
        if not all(item["ready"] for item in readiness):
            raise RuntimeError(f"worker readiness failed: {readiness}")
        gate.write_text("release\n", encoding="utf-8")
        results, exits = [], []
        for proc in procs:
            line = proc.stdout.readline().strip()
            results.append(json.loads(line) if line else {"error": "missing_worker_result"})
            stderr = proc.stderr.read()
            code = proc.wait(timeout=20)
            exits.append({"returncode": code, "stderr": stderr})
    except Exception:
        for proc in procs:
            if proc.poll() is None:
                proc.kill()
        for proc in procs:
            proc.wait(timeout=5)
        raise
    with connect(journal) as db:
        raw_receipt = db.execute("SELECT receipt_id,generation,state,attempt_id,delivery_id FROM receipts").fetchone()
    receipt = dict(zip(("receipt_id", "generation", "state", "attempt_id", "delivery_id"), raw_receipt))
    with connect(sink) as db:
        raw_rows = db.execute("SELECT delivery_id,attempt_id,target,payload FROM deliveries ORDER BY delivery_id").fetchall()
        target = db.execute("SELECT target FROM target_state WHERE singleton=1").fetchone()[0]
    rows = [dict(zip(("delivery_id", "attempt_id", "target", "payload"), row)) for row in raw_rows]
    matching = [row for row in rows if row["delivery_id"] == receipt["delivery_id"]
                and row["attempt_id"] == receipt["attempt_id"] and row["target"] == EXPECTED_TARGET]
    recovery = "CONFIRMED_SAME_ATTEMPT" if len(rows) == 1 and len(matching) == 1 and target == EXPECTED_TARGET else "UNKNOWN"
    return {"kind": "trace", "case_id": case_id, "readiness": readiness,
            "workers": sorted(results, key=lambda row: row.get("worker_id", -1)),
            "exits": exits, "receipt": receipt, "sink_rows": rows,
            "semantic_target": target, "recovery": recovery,
            "receipt_db": f"raw/formal/db/{case_id}/receipt.sqlite",
            "sink_db": f"raw/formal/db/{case_id}/sink.sqlite"}


def main(outdir):
    root = Path(outdir)
    (root / "db").mkdir(parents=True, exist_ok=True)
    traces = [run_case(case_id, delivery_ids, root / "db") for case_id, delivery_ids in CASES]
    counts = {state: sum(row["recovery"] == state for row in traces)
              for state in ("CONFIRMED_SAME_ATTEMPT", "UNKNOWN")}
    passed = counts == {"CONFIRMED_SAME_ATTEMPT": 1, "UNKNOWN": 1}
    print(json.dumps({"kind": "manifest", "schema": "issue-5508-affine-receipt-t14-v1",
                      "worker_count_per_case": WORKERS, "scenario_count": len(traces),
                      "decision": "PASS" if passed else "FAIL", "recovery_counts": counts},
                     sort_keys=True, separators=(",", ":")))
    for trace in traces:
        print(json.dumps(trace, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", nargs=4, metavar=("SINK", "GATE", "DELIVERY", "WORKER_ID"))
    parser.add_argument("--outdir")
    args = parser.parse_args()
    if args.worker:
        sink, gate, delivery, worker_id = args.worker
        raise SystemExit(worker(sink, gate, delivery, int(worker_id)))
    if not args.outdir:
        parser.error("--outdir is required")
    main(args.outdir)
