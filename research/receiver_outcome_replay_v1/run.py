"""Finite first-outcome runner; only newly-created private output directories."""
from __future__ import annotations
import argparse
import hashlib
import itertools
import json
import os
import platform
import random
import sqlite3
import subprocess
import sys
import time
import traceback
from pathlib import Path
from receiver import initialize, POLICIES, SCOPE

HERE = Path(__file__).resolve().parent
SCENARIOS = ("applied_stable", "applied_then_revoked", "applied_then_replaced",
             "applied_then_unrelated", "rejected_then_allowed", "precommit_then_revoked",
             "changed_payload", "new_id_after_revocation")
SEED = 34020260916

def dump(path, value):
    Path(path).write_text(json.dumps(value, sort_keys=True, indent=2)+"\n", encoding="utf-8")

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def schedule():
    result = [{"policy": p, "scenario": s, "rep": n}
              for p, s, n in itertools.product(POLICIES, SCENARIOS, range(5))]
    random.Random(SEED).shuffle(result)
    return result

def snapshot(dbpath):
    con = sqlite3.connect(dbpath)
    con.row_factory = sqlite3.Row
    result = {table: [dict(r) for r in con.execute("SELECT * FROM "+table+" ORDER BY rowid")]
              for table in ("context", "effects", "decisions")}
    con.close()
    return result

def invoke(casepath, req, policy, crash, phase):
    args = [sys.executable, str(HERE/"receiver.py"), "--db", str(casepath/"receiver.sqlite"),
            "--policy", policy, "--crash", crash, "--events", str(casepath/(phase+".events.jsonl"))]
    t0 = time.monotonic_ns()
    proc = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        stdout, stderr = proc.communicate(json.dumps(req), timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        stdout, stderr = proc.communicate()
        (casepath/(phase+".stdout")).write_text(stdout)
        (casepath/(phase+".stderr")).write_text(stderr)
        raise
    result = {"pid": proc.pid, "returncode": proc.returncode, "started_ns": t0,
              "ended_ns": time.monotonic_ns(), "stdout": stdout, "stderr": stderr,
              "response": json.loads(stdout) if stdout.strip() else None}
    dump(casepath/(phase+".process.json"), result)
    expected_code = {"none": 0, "before_commit": 74, "after_commit": 73}[crash]
    if proc.returncode != expected_code or stderr:
        raise RuntimeError(f"unexpected receiver termination {phase}: {result}")
    if crash != "none" and stdout:
        raise RuntimeError("crashed initial attempt unexpectedly delivered a response")
    return result

def mutate(dbpath, scenario):
    con = sqlite3.connect(dbpath, isolation_level=None)
    con.execute("PRAGMA synchronous=FULL")
    con.execute("BEGIN IMMEDIATE")
    if scenario in ("applied_then_revoked", "precommit_then_revoked", "new_id_after_revocation"):
        con.execute("UPDATE context SET allowed=0")
    elif scenario == "applied_then_replaced":
        con.execute("UPDATE context SET generation=generation+1")
    elif scenario == "applied_then_unrelated":
        con.execute("UPDATE context SET unrelated=unrelated+1")
    elif scenario == "rejected_then_allowed":
        con.execute("UPDATE context SET allowed=1")
    con.execute("COMMIT")
    con.close()

def main(out):
    out.mkdir(parents=True, exist_ok=False)
    protocol = json.loads((HERE/"protocol.json").read_text())
    if protocol["schedule"] != schedule():
        raise RuntimeError("schedule does not match freeze")
    for name, digest in protocol["sources"].items():
        if sha(HERE/name) != digest:
            raise RuntimeError("source changed after freeze: "+name)
    cpu = next((line.split(":",1)[1].strip() for line in Path("/proc/cpuinfo").read_text().splitlines()
                if line.startswith("model name")), "unavailable")
    dump(out/"environment.json", {"python": sys.version, "sqlite": sqlite3.sqlite_version,
         "platform": platform.platform(), "cpu": cpu, "visible_cpus": os.cpu_count(),
         "frequency_pinned": False, "clock": "monotonic_ns", "gui_model_network_calls": 0})
    dump(out/"protocol.json", protocol)
    completed = 0
    try:
        with (out/"records.jsonl").open("x") as ledger:
            for i, cell in enumerate(protocol["schedule"]):
                case = out/f"case-{i+1:03d}"
                case.mkdir()
                s, p = cell["scenario"], cell["policy"]
                req = {"scope": SCOPE, "command_id": f"cmd-{i+1:03d}", "context_id": "A",
                       "generation": 1, "allowed": True, "delta": 1}
                initialize(case/"receiver.sqlite", allowed=s != "rejected_then_allowed")
                start = snapshot(case/"receiver.sqlite")
                first = invoke(case, req, p, "before_commit" if s == "precommit_then_revoked" else "after_commit", "first")
                after_first = snapshot(case/"receiver.sqlite")
                mutation_started_ns = time.monotonic_ns()
                mutate(case/"receiver.sqlite", s)
                mutation_ended_ns = time.monotonic_ns()
                before_retry = snapshot(case/"receiver.sqlite")
                retry_req = dict(req)
                if s == "changed_payload":
                    retry_req["delta"] = 2
                elif s == "new_id_after_revocation":
                    retry_req["command_id"] += "-new"
                second = invoke(case, retry_req, p, "none", "second")
                after_second = snapshot(case/"receiver.sqlite")
                third = invoke(case, retry_req, p, "none", "third")
                final = snapshot(case/"receiver.sqlite")
                row = {"ordinal": i+1, **cell, "mutation_started_ns": mutation_started_ns,
                       "mutation_ended_ns": mutation_ended_ns, "request": req, "retry_request": retry_req,
                       "start": start, "after_first": after_first, "before_retry": before_retry,
                       "after_second": after_second, "final": final,
                       "first": first, "second": second, "third": third,
                       "db_path": str(case.relative_to(out)/"receiver.sqlite")}
                dump(case/"record.json", row)
                ledger.write(json.dumps(row, sort_keys=True)+"\n")
                ledger.flush()
                completed += 1
                if completed % 20 == 0:
                    print(json.dumps({"completed": completed, "total": len(protocol["schedule"])}), flush=True)
        dump(out/"disposition.json", {"status": "COMPLETED", "cases": completed, "receiver_processes": completed*3})
    except Exception:
        dump(out/"disposition.json", {"status": "INCOMPLETE", "cases": completed, "error": traceback.format_exc()})
        raise
    finally:
        manifest = {str(p.relative_to(out)): sha(p) for p in sorted(out.rglob("*")) if p.is_file()}
        dump(out/"manifest.json", manifest)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, type=Path)
    main(parser.parse_args().out)
