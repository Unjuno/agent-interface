"""Private deterministic worker; never invokes a model, shell, GUI or network."""
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import sys
import time


def snapshot(db):
    def rows(name):
        return [dict(r) for r in db.execute(f"SELECT * FROM {name} ORDER BY rowid")]
    return {n: rows(n) for n in ("state", "admissions", "claims", "effects")}


def emit(value):
    sys.stdout.write(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")
    sys.stdout.flush()


def main():
    dbpath, policy, worker = sys.argv[1:]
    if policy not in ("PRECHECK_ONLY", "ATOMIC_CLAIM"):
        raise ValueError("unknown policy")
    db = sqlite3.connect(dbpath, isolation_level=None, timeout=2.0)
    db.row_factory = sqlite3.Row
    prepared = None
    active = None
    emit({"event": "hello", "pid": os.getpid(), "worker": worker,
          "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})
    for raw in sys.stdin.buffer:
        if len(raw) > 4096 or not raw.endswith(b"\n"):
            raise ValueError("invalid command frame")
        cmd = json.loads(raw)
        op = cmd["op"]
        entered = time.monotonic_ns()
        if op == "shutdown":
            emit({"event": "shutdown", "worker": worker, "pid": os.getpid()})
            db.close()
            return
        if op == "prepare":
            if prepared is not None:
                raise ValueError("prepare only once per process")
            db.execute("BEGIN")
            st = dict(db.execute("SELECT * FROM state").fetchone())
            db.execute("COMMIT")
            now = time.monotonic_ns()
            ready = st["predecessor_ok"] == 1 and st["cancelled"] == 0 and now < st["deadline_ns"]
            prepared = {"request": cmd["request"], "resource": cmd["resource"],
                        "generation": st["generation"], "session": st["session"],
                        "deadline_ns": st["deadline_ns"], "ready": ready}
            result = {"event": "prepared", "prepared": prepared, "observed": st, "time_ns": now}
        elif op == "start":
            if prepared is None or active is not None:
                raise ValueError("invalid start phase")
            db.execute("BEGIN IMMEDIATE")
            before = snapshot(db)
            st = before["state"][0]
            now = time.monotonic_ns()
            reason = "STARTED" if prepared["ready"] else "NOT_READY_AT_PREPARE"
            if policy == "ATOMIC_CLAIM" and reason == "STARTED":
                if st["session"] != prepared["session"] or st["generation"] != prepared["generation"]:
                    reason = "STALE_GENERATION"
                elif st["predecessor_ok"] != 1:
                    reason = "PREDECESSOR_FAILED"
                elif st["cancelled"] != 0:
                    reason = "CANCELLED"
                elif now >= min(st["deadline_ns"], prepared["deadline_ns"]):
                    reason = "EXPIRED"
                elif any(r["request"] == prepared["request"] for r in before["admissions"]):
                    reason = "DUPLICATE_OR_UNRESOLVED"
                elif any(r["resource"] == prepared["resource"] for r in before["claims"]):
                    reason = "RESOURCE_BUSY"
            if reason == "STARTED":
                active = worker + ":attempt"
                db.execute("INSERT INTO admissions VALUES (?,?,?,?,?,?,?,?,?,?)",
                           (active, prepared["request"], prepared["resource"], worker, os.getpid(),
                            prepared["generation"], now, None, "ACTIVE", st["generation"]))
                if policy == "ATOMIC_CLAIM":
                    db.execute("INSERT INTO claims VALUES (?,?,?)", (prepared["resource"], prepared["request"], active))
            db.execute("COMMIT")
            result = {"event": "start", "decision": reason, "attempt": active,
                      "time_ns": now, "observed": before}
        elif op == "work":
            if active is None:
                raise ValueError("work without admission")
            db.execute("BEGIN IMMEDIATE")
            current = db.execute("SELECT phase FROM admissions WHERE attempt=?", (active,)).fetchone()
            if current[0] != "ACTIVE":
                raise ValueError("work repeated")
            if policy == "ATOMIC_CLAIM" and db.execute("SELECT 1 FROM claims WHERE attempt=?", (active,)).fetchone() is None:
                raise ValueError("lost claim")
            now = time.monotonic_ns()
            db.execute("INSERT INTO effects VALUES (?,?,?,?,?,?)", (active, prepared["request"], prepared["resource"], os.getpid(), 1, now))
            db.execute("UPDATE admissions SET phase='DONE',end_ns=? WHERE attempt=?", (now, active))
            db.execute("DELETE FROM claims WHERE attempt=?", (active,))
            db.execute("COMMIT")
            result = {"event": "work", "attempt": active, "value": 1, "time_ns": now}
        else:
            raise ValueError("unknown command")
        result.update({"worker": worker, "pid": os.getpid(), "entered_ns": entered,
                       "returned_ns": time.monotonic_ns()})
        emit(result)
    db.close()


if __name__ == "__main__":
    main()
