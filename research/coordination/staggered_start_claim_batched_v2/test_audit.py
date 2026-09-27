"""Finite evidence-corruption controls, including semantic tests with refreshed journals."""
import argparse
import base64
import copy
import gzip
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import audit


def response_edit(rows, policy, scenario, op, key, value):
    row = next(r for r in rows if r["policy"] == policy and r["scenario"] == scenario)
    event = next(e for e in row["events"] if e.get("op") == op)
    response = json.loads(event["response"])
    response[key] = value
    event["response"] = json.dumps(response, sort_keys=True, separators=(",", ":")) + "\n"


def run_controls(rows, repetitions, worker_hash):
    result = audit.audit_rows(rows, repetitions, worker_hash)
    if result["errors"]:
        raise ValueError("baseline audit does not pass")
    def generation(rs):
        row = next(r for r in rs if r["policy"] == "ATOMIC_CLAIM" and r["scenario"] == "generation_changed")
        row["initial"]["state"][0]["generation"] = 2
    def missing_exit(rs):
        row = rs[0]
        row["events"] = [e for e in row["events"] if e["kind"] != "exit"]
    def status(rs):
        row = rs[0]
        e = next(e for e in row["events"] if e["kind"] == "exit")
        e["returncode"] = True
    def generation_receipt(rs):
        row = rs[0]
        e = next(e for e in row["events"] if e.get("op") == "prepare")
        response = json.loads(e["response"])
        response["prepared"]["generation"] += 1
        e["response"] = json.dumps(response, sort_keys=True, separators=(",", ":")) + "\n"
    def wrong_source(rs):
        e = next(e for e in rs[0]["events"] if e["kind"] == "spawn")
        response = json.loads(e["response"]); response["source_sha256"] = "0" * 64
        e["response"] = json.dumps(response, sort_keys=True, separators=(",", ":")) + "\n"
    def database_effect(rs):
        row = rs[0]
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "data.sqlite3"
            p.write_bytes(gzip.decompress(base64.b64decode(row["database_gzip_b64"])))
            with sqlite3.connect(p) as db:
                db.execute("UPDATE effects SET value=9")
            b = p.read_bytes()
        row["database_sha256"] = hashlib.sha256(b).hexdigest()
        row["database_gzip_b64"] = base64.b64encode(gzip.compress(b, mtime=0)).decode()
    def dropped_claim(rs):
        row = next(r for r in rs if r["policy"] == "ATOMIC_CLAIM" and r["scenario"] == "claimed_process_crash")
        row["final"]["claims"] = []
    mutations = [
        ("missing_case", lambda rs: rs.pop()),
        ("duplicate_case", lambda rs: rs.__setitem__(-1, copy.deepcopy(rs[0]))),
        ("changed_effect_reply", lambda rs: response_edit(rs, "PRECHECK_ONLY", "ready", "work", "value", 2)),
        ("changed_generation", generation),
        ("missing_exit", missing_exit),
        ("boolean_rep", lambda rs: rs[0].__setitem__("rep", False)),
        ("boolean_exit_status", status),
        ("false_atomic_admission", lambda rs: response_edit(rs, "ATOMIC_CLAIM", "cancelled", "start", "decision", "STARTED")),
        ("transplanted_prepared_generation", generation_receipt),
        ("wrong_worker_source", wrong_source),
        ("database_effect_with_rehashed_bytes", database_effect),
        ("lost_unresolved_claim", dropped_claim),
    ]
    controls = []
    for name, mutate in mutations:
        changed = copy.deepcopy(rows)
        mutate(changed)
        # Refresh journal binding so semantic controls do not merely fail the hash gate.
        for r in changed:
            journal = b"".join((json.dumps(e, sort_keys=True, separators=(",", ":")) + "\n").encode() for e in r["events"])
            r["journal_sha256"] = hashlib.sha256(journal).hexdigest()
        answer = audit.audit_rows(changed, repetitions, worker_hash)
        controls.append({"name": name, "rejected": bool(answer["errors"]), "errors": answer["errors"]})
    require_all = all(c["rejected"] for c in controls)
    return {"decision": "PASS_CORRUPTION_CONTROLS" if require_all else "FAIL_CORRUPTION_CONTROLS",
            "controls": controls, "passed": sum(c["rejected"] for c in controls), "total": len(controls)}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("root"); ap.add_argument("--construction", action="store_true")
    args = ap.parse_args()
    rows = [json.loads(line) for line in (Path(args.root) / "RAW.jsonl").read_text().splitlines()]
    result = run_controls(rows, 1 if args.construction else 3,
                          hashlib.sha256((Path(__file__).parent / "worker.py").read_bytes()).hexdigest())
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(result["passed"] != result["total"])
