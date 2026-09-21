"""Immutable six-case batches; do not resume an incomplete consumed batch."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import run

ROOT = Path(__file__).resolve().parent


def digest(data):
    return hashlib.sha256(data).hexdigest()


def validate_prefix(root, index):
    if type(index) is not int or not 0 <= index < 9:
        raise ValueError("invalid batch index")
    raw = (root / "RAW.jsonl").read_bytes()
    lines = raw.splitlines(keepends=True)
    if len(lines) != index * 6 or (raw and not raw.endswith(b"\n")):
        raise ValueError("prefix row count")
    for prior in range(index):
        started = json.loads((root / f"batch-{prior}.started.json").read_text())
        receipt = json.loads((root / f"batch-{prior}.done.json").read_text())
        if started["index"] != prior or receipt["index"] != prior:
            raise ValueError("prefix batch identity")
        if receipt["prefix_before"] != digest(b"".join(lines[:prior * 6])):
            raise ValueError("prefix before hash")
        if receipt["prefix_after"] != digest(b"".join(lines[:(prior + 1) * 6])):
            raise ValueError("prefix after hash")
    if (root / f"batch-{index}.started.json").exists():
        raise ValueError("batch already consumed; no retry")
    return raw


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--index", type=int, required=True)
    args = ap.parse_args()
    index = args.index
    if not 0 <= index < 9:
        raise ValueError("invalid index")
    freeze_bytes = (ROOT / "FREEZE.json").read_bytes()
    freeze = json.loads(freeze_bytes)
    for path, sha in freeze["sha256"].items():
        if digest((ROOT / path).read_bytes()) != sha:
            raise ValueError("source mismatch:" + path)
    out = Path(freeze["formal_output"])
    if index == 0:
        out.mkdir(parents=True, exist_ok=False)
        (out / "RAW.jsonl").write_bytes(b"")
        (out / "STARTED.json").write_bytes(run.enc({"allocation": freeze["allocation"],
                                                   "source_freeze_sha256": digest(freeze_bytes)}))
    with (out / ".batch.lock").open("ab") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        before = validate_prefix(out, index)
        start = time.monotonic_ns()
        marker = {"index": index, "allocation": freeze["allocation"], "pid": os.getpid(),
                  "argv": sys.argv, "start_ns": start, "source_freeze_sha256": digest(freeze_bytes)}
        with (out / f"batch-{index}.started.json").open("xb") as f:
            f.write(run.enc(marker)); f.flush(); os.fsync(f.fileno())
        try:
            scenario = run.SCENARIOS[index]
            with (out / "RAW.jsonl").open("ab") as raw:
                for rep in range(3):
                    for policy in (run.POLICIES if rep % 2 == 0 else tuple(reversed(run.POLICIES))):
                        cid = f"{scenario}-{rep}-{policy.lower()}"
                        record = run.run_case(out, cid, policy, scenario, rep)
                        record["allocation"] = freeze["allocation"]
                        record["batch_index"] = index
                        raw.write(run.enc(record)); raw.flush(); os.fsync(raw.fileno())
            for path, sha in freeze["sha256"].items():
                if digest((ROOT / path).read_bytes()) != sha:
                    raise ValueError("source changed:" + path)
            after = (out / "RAW.jsonl").read_bytes()
            if len(after.splitlines()) != (index + 1) * 6 or not after.startswith(before):
                raise ValueError("batch append cardinality")
            done = {"index": index, "allocation": freeze["allocation"],
                    "start_row": index * 6, "end_row_exclusive": (index + 1) * 6,
                    "prefix_before": digest(before), "prefix_after": digest(after),
                    "start_ns": start, "end_ns": time.monotonic_ns(), "cases": 6}
            with (out / f"batch-{index}.done.json").open("xb") as f:
                f.write(run.enc(done)); f.flush(); os.fsync(f.fileno())
            if index == 8:
                execution = {"execution": "COMPLETED", "cases": 54, "batches": 9,
                             "raw_sha256": digest(after), "allocation": freeze["allocation"]}
                (out / "EXECUTION.json").write_bytes(run.enc(execution))
            print(json.dumps(done, sort_keys=True), flush=True)
        except BaseException as error:
            (out / f"batch-{index}.STOP.json").write_bytes(run.enc({"disposition": "STOP_BATCH", "error": repr(error)}))
            raise


if __name__ == "__main__":
    main()
