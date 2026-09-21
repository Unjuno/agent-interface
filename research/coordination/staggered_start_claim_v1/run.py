"""One-shot barrier-controlled process allocation. All effects are private SQLite rows."""
import argparse
import base64
import gzip
import hashlib
import json
import os
from pathlib import Path
import select
import sqlite3
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
SCENARIOS = ("ready", "generation_changed", "predecessor_failed", "cancelled", "expired",
             "competing_requests", "independent_resources", "completed_request_restart", "claimed_process_crash")
POLICIES = ("PRECHECK_ONLY", "ATOMIC_CLAIM")


def enc(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode() + b"\n"


def observe(path):
    with sqlite3.connect("file:" + str(path) + "?mode=ro", uri=True) as db:
        db.row_factory = sqlite3.Row
        db.execute("BEGIN")
        data = {n: [dict(r) for r in db.execute(f"SELECT * FROM {n} ORDER BY rowid")]
                for n in ("state", "admissions", "claims", "effects")}
        db.rollback()
        return data


def init_db(path, case_id, scenario):
    with sqlite3.connect(path) as db:
        db.executescript("""
        PRAGMA journal_mode=DELETE;
        PRAGMA synchronous=FULL;
        CREATE TABLE state(session TEXT,generation INTEGER,predecessor_ok INTEGER,cancelled INTEGER,deadline_ns INTEGER);
        CREATE TABLE admissions(attempt TEXT PRIMARY KEY,request TEXT,resource TEXT,worker TEXT,pid INTEGER,
          prepared_generation INTEGER,start_ns INTEGER,end_ns INTEGER,phase TEXT,observed_generation INTEGER);
        CREATE TABLE claims(resource TEXT PRIMARY KEY,request TEXT UNIQUE,attempt TEXT UNIQUE);
        CREATE TABLE effects(attempt TEXT PRIMARY KEY,request TEXT,resource TEXT,pid INTEGER,value INTEGER,time_ns INTEGER);
        """)
        # One second is a deadline fixture, not a production lease recommendation.
        horizon = 1_000_000_000 if scenario == "expired" else 60_000_000_000
        db.execute("INSERT INTO state VALUES (?,?,?,?,?)", (case_id, 1, 1, 0, time.monotonic_ns() + horizon))


class Case:
    def __init__(self, out, case_id, policy, scenario, rep):
        self.path = out / case_id
        self.path.mkdir()
        self.db = self.path / "state.sqlite3"
        init_db(self.db, case_id, scenario)
        self.record = {"case_id": case_id, "policy": policy, "scenario": scenario,
                       "rep": rep, "events": [], "initial": observe(self.db), "processes": []}
        self.workers = {}
        self.journal = (self.path / "events.jsonl").open("xb")

    def log(self, row):
        row["seq"] = len(self.record["events"])
        self.record["events"].append(row)
        self.journal.write(enc(row)); self.journal.flush()

    def read_frame(self, proc):
        deadline = time.monotonic() + 5
        buf = b""
        while b"\n" not in buf:
            remain = deadline - time.monotonic()
            if remain <= 0 or not select.select([proc.stdout], [], [], remain)[0]:
                raise TimeoutError("worker response timeout")
            part = os.read(proc.stdout.fileno(), 65536)
            if not part:
                raise RuntimeError("worker stdout EOF")
            buf += part
            if len(buf) > 65536:
                raise RuntimeError("oversized worker response")
        if buf.count(b"\n") != 1 or not buf.endswith(b"\n"):
            raise RuntimeError("unexpected response framing")
        return buf.decode()

    def spawn(self, name):
        worker = self.record["case_id"] + "." + name
        stderr = (self.path / (name + ".stderr")).open("xb")
        command = [sys.executable, "-I", str(ROOT / "worker.py"), str(self.db), self.record["policy"], worker]
        sent = time.monotonic_ns()
        proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=stderr,
                                env={"PATH": os.defpath, "LC_ALL": "C.UTF-8"}, bufsize=0)
        self.workers[name] = (proc, stderr, worker)
        frame = self.read_frame(proc)
        self.log({"kind": "spawn", "name": name, "worker": worker, "pid": proc.pid,
                  "argv": command, "send_ns": sent, "recv_ns": time.monotonic_ns(), "response": frame})

    def command(self, name, op, **fields):
        proc, _, worker = self.workers[name]
        request = enc({"op": op, **fields})
        before = observe(self.db)
        sent = time.monotonic_ns()
        proc.stdin.write(request); proc.stdin.flush()
        response = self.read_frame(proc)
        received = time.monotonic_ns()
        after = observe(self.db)
        self.log({"kind": "command", "worker": worker, "name": name, "op": op,
                  "request": request.decode(), "response": response, "send_ns": sent,
                  "recv_ns": received, "before": before, "after": after})
        return json.loads(response)

    def stop(self, name, kill=False):
        proc, stderr, worker = self.workers.pop(name)
        before = observe(self.db)
        start = time.monotonic_ns()
        if kill:
            proc.kill()
        out, _ = proc.communicate(timeout=5)
        stderr.close()
        row = {"worker": worker, "pid": proc.pid, "returncode": proc.returncode,
               "killed": kill, "extra_stdout": out.decode(),
               "stderr": (self.path / (name + ".stderr")).read_text(),
               "send_ns": start, "recv_ns": time.monotonic_ns()}
        self.record["processes"].append(row)
        self.log({"kind": "exit", "name": name, "worker": worker,
                  "before": before, "after": observe(self.db), **row})
        expected = -9 if kill else 0
        if proc.returncode != expected or out or row["stderr"]:
            raise RuntimeError("unexpected worker exit")

    def mutate(self, scenario):
        before = observe(self.db)
        start = time.monotonic_ns()
        if scenario == "expired":
            target = before["state"][0]["deadline_ns"] + 1_000_000
            while time.monotonic_ns() < target:
                time.sleep(max(0.0, min(0.01, (target - time.monotonic_ns()) / 1e9)))
        else:
            sql = {"generation_changed": "UPDATE state SET generation=2",
                   "predecessor_failed": "UPDATE state SET predecessor_ok=0",
                   "cancelled": "UPDATE state SET cancelled=1"}[scenario]
            with sqlite3.connect(self.db) as db:
                db.execute(sql)
        self.log({"kind": "transition", "transition": scenario, "send_ns": start,
                  "recv_ns": time.monotonic_ns(), "before": before, "after": observe(self.db)})

    def complete(self):
        for name in list(self.workers):
            self.command(name, "shutdown")
            self.stop(name)
        self.record["final"] = observe(self.db)
        raw = self.db.read_bytes()
        self.record["database_sha256"] = hashlib.sha256(raw).hexdigest()
        self.record["database_gzip_b64"] = base64.b64encode(gzip.compress(raw, mtime=0)).decode()
        self.journal.close()
        self.record["journal_sha256"] = hashlib.sha256((self.path / "events.jsonl").read_bytes()).hexdigest()
        return self.record


def run_case(out, case_id, policy, scenario, rep):
    c = Case(out, case_id, policy, scenario, rep)
    try:
        c.spawn("w1")
        ready = c.command("w1", "prepare", request="request-1", resource="resource-1")
        if ready["prepared"]["ready"] is not True:
            raise RuntimeError("positive preparation unavailable")
        if scenario in ("generation_changed", "predecessor_failed", "cancelled", "expired"):
            c.mutate(scenario)
        if scenario in ("competing_requests", "independent_resources"):
            c.spawn("w2")
            ready2 = c.command("w2", "prepare", request="request-2",
                               resource="resource-2" if scenario == "independent_resources" else "resource-1")
            if ready2["prepared"]["ready"] is not True:
                raise RuntimeError("second preparation unavailable")
        first = c.command("w1", "start")
        if scenario in ("competing_requests", "independent_resources"):
            second = c.command("w2", "start")
            c.log({"kind": "overlap_barrier", "time_ns": time.monotonic_ns(), "snapshot": observe(c.db)})
            if first["decision"] == "STARTED":
                c.command("w1", "work")
            if second["decision"] == "STARTED":
                c.command("w2", "work")
        elif scenario in ("completed_request_restart", "claimed_process_crash"):
            if first["decision"] != "STARTED":
                raise RuntimeError("restart control lacks first start")
            if scenario == "completed_request_restart":
                c.command("w1", "work"); c.command("w1", "shutdown")
            c.stop("w1", kill=(scenario == "claimed_process_crash"))
            c.spawn("w2")
            ready2 = c.command("w2", "prepare", request="request-1", resource="resource-1")
            if ready2["prepared"]["ready"] is not True:
                raise RuntimeError("restart preparation unavailable")
            second = c.command("w2", "start")
            if second["decision"] == "STARTED":
                c.command("w2", "work")
        elif first["decision"] == "STARTED":
            c.command("w1", "work")
        return c.complete()
    except BaseException:
        # Only this Case's processes are touched. Never erase partial journals/database.
        for name, (proc, stderr, worker) in list(c.workers.items()):
            if proc.poll() is None:
                proc.kill()
            proc.communicate(timeout=5); stderr.close()
        c.journal.close()
        (c.path / "PARTIAL.json").write_bytes(enc(c.record))
        raise


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--construction", action="store_true")
    args = ap.parse_args()
    out = Path(args.out).resolve()
    if args.construction:
        repetitions = 1
        source_hashes = {}
    else:
        freeze = json.loads((ROOT / "FREEZE.json").read_text())
        if out != Path(freeze["formal_output"]) or out.is_symlink():
            raise ValueError("formal output does not match frozen allocation")
        source_hashes = freeze["sha256"]
        for path, digest in source_hashes.items():
            if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != digest:
                raise ValueError("source hash mismatch: " + path)
        repetitions = 3
    out.mkdir(parents=True, exist_ok=False)
    (out / "STARTED.json").write_bytes(enc({"time_ns": time.monotonic_ns(), "argv": sys.argv,
                                           "pid": os.getpid(), "construction": args.construction}))
    start = time.monotonic_ns()
    try:
        with (out / "RAW.jsonl").open("xb") as raw:
            for scenario in SCENARIOS:
                for rep in range(repetitions):
                    # Alternating arm order prevents one arm always being first.
                    arms = POLICIES if rep % 2 == 0 else tuple(reversed(POLICIES))
                    for policy in arms:
                        case_id = f"{scenario}-{rep}-{policy.lower()}"
                        record = run_case(out, case_id, policy, scenario, rep)
                        raw.write(enc(record)); raw.flush(); os.fsync(raw.fileno())
        for path, digest in source_hashes.items():
            if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != digest:
                raise ValueError("source changed during formal: " + path)
        result = {"execution": "COMPLETED", "cases": 18 * repetitions,
                  "duration_ns": time.monotonic_ns() - start,
                  "raw_sha256": hashlib.sha256((out / "RAW.jsonl").read_bytes()).hexdigest()}
        (out / "EXECUTION.json").write_bytes(enc(result)); print(json.dumps(result))
    except BaseException as error:
        (out / "STOP.json").write_bytes(enc({"execution": "STOP", "error": repr(error)}))
        raise


if __name__ == "__main__":
    main()
