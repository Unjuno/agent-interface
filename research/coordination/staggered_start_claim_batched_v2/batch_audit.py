"""Read-only batch/provenance audit, independently implemented from batch driver."""
import argparse
import hashlib
import json
from pathlib import Path
import audit

ROOT = Path(__file__).resolve().parent


def sha(data):
    return hashlib.sha256(data).hexdigest()


def verify(root):
    freeze_bytes = (ROOT / "FREEZE.json").read_bytes()
    freeze = json.loads(freeze_bytes)
    for name, digest in freeze["sha256"].items():
        audit.require(sha((ROOT / name).read_bytes()) == digest, "source:" + name)
    allocation = freeze["allocation"]
    execution_source = Path(freeze["execution_source_root"])
    execution_output = Path(freeze["formal_output"])
    raw = (root / "RAW.jsonl").read_bytes()
    lines = raw.splitlines(keepends=True)
    audit.require(len(lines) == 54 and all(l.endswith(b"\n") for l in lines), "raw_framing")
    start = json.loads((root / "STARTED.json").read_text())
    audit.require(audit.same(start, {"allocation": allocation, "source_freeze_sha256": sha(freeze_bytes)}), "allocation_start")
    markers = sorted(p.name for p in root.glob("batch-*.started.json"))
    receipts = sorted(p.name for p in root.glob("batch-*.done.json"))
    audit.require(markers == [f"batch-{i}.started.json" for i in range(9)], "consumed_batches")
    audit.require(receipts == [f"batch-{i}.done.json" for i in range(9)], "complete_batches")
    audit.require(not list(root.glob("*STOP*")), "stop_present")
    last_end = 0
    for i in range(9):
        m = json.loads((root / f"batch-{i}.started.json").read_text())
        d = json.loads((root / f"batch-{i}.done.json").read_text())
        for value in (m["index"], d["index"], d["cases"], d["start_row"], d["end_row_exclusive"], m["pid"],
                      m["start_ns"], d["start_ns"], d["end_ns"]):
            audit.require(type(value) is int, "batch_integer_type")
        audit.require(m["index"] == d["index"] == i and d["cases"] == 6, "batch_index")
        audit.require(m["allocation"] == d["allocation"] == allocation and m["source_freeze_sha256"] == sha(freeze_bytes), "batch_allocation")
        audit.require(m["argv"] == [str(execution_source / "batch_driver.py"), "--index", str(i)], "batch_command")
        audit.require(d["start_row"] == i * 6 and d["end_row_exclusive"] == (i + 1) * 6, "batch_range")
        audit.require(last_end <= m["start_ns"] == d["start_ns"] <= d["end_ns"], "batch_clock")
        last_end = d["end_ns"]
        audit.require(d["prefix_before"] == sha(b"".join(lines[:i * 6])), "prefix_before")
        audit.require(d["prefix_after"] == sha(b"".join(lines[:(i + 1) * 6])), "prefix_after")
        for line in lines[i * 6:(i + 1) * 6]:
            r = json.loads(line)
            audit.require(type(r["batch_index"]) is int and r["batch_index"] == i and r["allocation"] == allocation, "row_allocation")
            for e in r["events"]:
                first = e.get("send_ns", e.get("time_ns"))
                last = e.get("recv_ns", e.get("time_ns"))
                audit.require(d["start_ns"] <= first <= last <= d["end_ns"], "row_batch_clock")
                if e["kind"] == "spawn":
                    audit.require(e["argv"][2] == str(execution_source / "worker.py"), "worker_source_path")
                    audit.require(e["argv"][3] == str(execution_output / r["case_id"] / "state.sqlite3"), "worker_database_path")
    result = audit.audit_rows([json.loads(l) for l in lines], 3, freeze["sha256"]["worker.py"])
    audit.require(not result["errors"], "scientific_raw_audit")
    execution = json.loads((root / "EXECUTION.json").read_text())
    audit.require(audit.same(execution, {"execution": "COMPLETED", "cases": 54, "batches": 9,
                                        "raw_sha256": sha(raw), "allocation": allocation}), "execution_receipt")
    return {"decision": "PASS_BATCH_PROVENANCE", "batches": 9, "cases": 54, "raw_sha256": sha(raw), "errors": []}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("root"); args = ap.parse_args()
    print(json.dumps(verify(Path(args.root).resolve()), sort_keys=True))
