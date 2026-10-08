#!/usr/bin/env python3
"""T12: crash a child between durable receipt and external-effect boundaries."""
import argparse
import json
import os
from pathlib import Path
import signal
import sqlite3
import subprocess
import sys

TARGET = "target-7"
CASES = (
    {"case_id": "pre_consume", "crash": "before_consume", "effect": None, "observer": True, "retry": False},
    {"case_id": "post_consume", "crash": "after_consume", "effect": None, "observer": True, "retry": True},
    {"case_id": "effect_pre_observation", "crash": "after_effect", "effect": "matching", "observer": True, "retry": True},
    {"case_id": "wrong_target", "crash": None, "effect": "wrong_target", "observer": True, "retry": False},
    {"case_id": "foreign_lineage", "crash": None, "effect": "foreign_lineage", "observer": True, "retry": False},
    {"case_id": "observer_unavailable", "crash": None, "effect": "matching", "observer": False, "retry": False},
    {"case_id": "normal_valid", "crash": None, "effect": "matching", "observer": True, "retry": False},
)


def connect(path):
    db = sqlite3.connect(path, timeout=5)
    db.execute("PRAGMA journal_mode=DELETE")
    db.execute("PRAGMA synchronous=FULL")
    return db


def init_stores(journal_path, effect_path, case_id):
    with connect(journal_path) as db:
        db.execute("CREATE TABLE receipts(receipt_id TEXT PRIMARY KEY, generation INTEGER NOT NULL, state TEXT NOT NULL, attempt_id TEXT, delivery_id TEXT)")
        db.execute("INSERT INTO receipts VALUES(?,1,'AVAILABLE',NULL,NULL)", (f"receipt-{case_id}",))
    with connect(effect_path) as db:
        db.execute("CREATE TABLE deliveries(delivery_id TEXT PRIMARY KEY, attempt_id TEXT NOT NULL, target TEXT NOT NULL, effect TEXT NOT NULL)")
        db.execute("CREATE TABLE target_state(singleton INTEGER PRIMARY KEY CHECK(singleton=1), target TEXT NOT NULL, effect TEXT NOT NULL)")
        db.execute("INSERT INTO target_state VALUES(1,'initial','NONE')")


def worker(journal_path, effect_path, case_id, phase, effect_kind):
    print("READY", flush=True)
    if sys.stdin.readline().strip() != "GO":
        return 10
    receipt_id = f"receipt-{case_id}"
    attempt_id = f"attempt-{case_id}"
    delivery_id = f"delivery-{case_id}"
    with connect(journal_path) as db:
        db.execute("BEGIN IMMEDIATE")
        cur = db.execute("UPDATE receipts SET state='CONSUMED',attempt_id=?,delivery_id=? WHERE receipt_id=? AND generation=1 AND state='AVAILABLE'",
                         (attempt_id, delivery_id, receipt_id))
        admitted = cur.rowcount == 1
        db.commit()
    if not admitted:
        print("REJECTED_REPLAY", flush=True)
        return 0
    print("RECEIPT_CONSUMED", flush=True)
    if phase == "after_consume":
        print("KILL_BARRIER", flush=True)
        sys.stdin.readline()
        return 11
    if effect_kind:
        if effect_kind == "foreign_lineage":
            effect_attempt, effect_delivery, target = "attempt-foreign", "delivery-foreign", TARGET
        elif effect_kind == "wrong_target":
            effect_attempt, effect_delivery, target = attempt_id, delivery_id, "target-wrong"
        else:
            effect_attempt, effect_delivery, target = attempt_id, delivery_id, TARGET
        with connect(effect_path) as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("INSERT INTO deliveries VALUES(?,?,?,?)", (effect_delivery, effect_attempt, target, "WRITE"))
            db.execute("UPDATE target_state SET target=?,effect='WRITE' WHERE singleton=1", (target,))
            db.commit()
        print("EFFECT_COMMITTED", flush=True)
        if phase == "after_effect":
            print("KILL_BARRIER", flush=True)
            sys.stdin.readline()
            return 12
    print("DONE", flush=True)
    return 0


def run_worker(case, journal_path, effect_path, phase, effect_kind):
    argv = [sys.executable, "-B", str(Path(__file__).resolve()), "--worker",
            str(journal_path), str(effect_path), case, phase or "none", effect_kind or "none"]
    proc = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True, bufsize=1)
    events = []
    first = proc.stdout.readline().strip()
    events.append(first)
    if first != "READY":
        out, err = proc.communicate(timeout=5)
        return {"exit_code": proc.returncode, "events": events + out.splitlines(), "stderr": err}
    if phase == "before_consume":
        proc.kill()
        proc.wait(timeout=5)
        return {"exit_code": proc.returncode, "events": events, "stderr": ""}
    proc.stdin.write("GO\n"); proc.stdin.flush()
    while True:
        line = proc.stdout.readline()
        if not line:
            break
        line = line.strip(); events.append(line)
        if line == "KILL_BARRIER":
            proc.kill(); proc.wait(timeout=5)
            return {"exit_code": proc.returncode, "events": events, "stderr": ""}
    err = proc.stderr.read()
    proc.wait(timeout=5)
    return {"exit_code": proc.returncode, "events": events, "stderr": err}


def observer(effect_path, available):
    argv = [sys.executable, "-B", str(Path(__file__).with_name("observer.py")),
            str(effect_path), "--available" if available else "--unavailable"]
    result = subprocess.run(argv, check=True, capture_output=True, text=True, timeout=5)
    return json.loads(result.stdout)


def snapshots(journal_path, effect_path):
    with connect(journal_path) as db:
        receipt = [dict(zip(("receipt_id", "generation", "state", "attempt_id", "delivery_id"), row))
                   for row in db.execute("SELECT * FROM receipts ORDER BY receipt_id")]
    with connect(effect_path) as db:
        deliveries = [dict(zip(("delivery_id", "attempt_id", "target", "effect"), row))
                      for row in db.execute("SELECT * FROM deliveries ORDER BY delivery_id")]
    return receipt, deliveries


def recover(receipts, observation):
    if len(receipts) != 1:
        return "UNKNOWN"
    receipt = receipts[0]
    if receipt["state"] == "AVAILABLE":
        return "NOT_STARTED"
    if receipt["state"] != "CONSUMED" or not observation.get("available"):
        return "UNKNOWN"
    matches = [d for d in observation.get("deliveries", [])
               if d["delivery_id"] == receipt["delivery_id"]
               and d["attempt_id"] == receipt["attempt_id"]]
    if len(matches) == 1 and observation.get("target") == TARGET and matches[0]["target"] == TARGET:
        return "CONFIRMED_SAME_ATTEMPT"
    return "UNKNOWN"


def execute_case(spec, root):
    case_id = spec["case_id"]
    folder = root / case_id
    folder.mkdir(parents=True)
    journal_path, effect_path = folder / "receipt.sqlite", folder / "effects.sqlite"
    init_stores(journal_path, effect_path, case_id)
    worker_result = run_worker(case_id, journal_path, effect_path, spec["crash"], spec["effect"])
    retry_result = None
    if spec["retry"]:
        retry_result = run_worker(case_id, journal_path, effect_path, None, None)
    receipt_rows, effect_rows = snapshots(journal_path, effect_path)
    observed = observer(effect_path, spec["observer"])
    decision = recover(receipt_rows, observed)
    return {"case": spec, "worker": worker_result, "retry": retry_result,
            "receipt_rows": receipt_rows, "effect_rows": effect_rows,
            "observer": observed, "recovery": decision,
            "journal_db": f"raw/db/{case_id}/receipt.sqlite",
            "effect_db": f"raw/db/{case_id}/effects.sqlite"}


def main(outdir):
    root = Path(outdir)
    root.mkdir(parents=True, exist_ok=True)
    traces = [execute_case(spec, root / "db") for spec in CASES]
    counts = {name: sum(row["recovery"] == name for row in traces)
              for name in ("NOT_STARTED", "UNKNOWN", "CONFIRMED_SAME_ATTEMPT")}
    decision = "PASS" if counts == {"NOT_STARTED": 1, "UNKNOWN": 4, "CONFIRMED_SAME_ATTEMPT": 2} else "FAIL"
    print(json.dumps({"kind": "manifest", "schema": "issue-5508-affine-receipt-t12-v1",
                      "scenario_count": len(traces), "decision": decision, "recovery_counts": counts,
                      "scope": "local file-backed SQLite and child-process SIGKILL; authored effect/observer simulators"},
                     sort_keys=True, separators=(",", ":")))
    for row in traces:
        print(json.dumps({"kind": "trace", **row}, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", nargs=5, metavar=("JOURNAL", "EFFECTS", "CASE", "PHASE", "EFFECT"))
    parser.add_argument("--outdir")
    args = parser.parse_args()
    if args.worker:
        jp, ep, case, phase, effect = args.worker
        raise SystemExit(worker(jp, ep, case, None if phase == "none" else phase,
                                None if effect == "none" else effect))
    if not args.outdir:
        parser.error("--outdir is required")
    main(args.outdir)
