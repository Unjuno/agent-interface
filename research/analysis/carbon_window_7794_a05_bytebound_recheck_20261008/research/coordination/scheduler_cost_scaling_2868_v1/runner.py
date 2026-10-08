#!/usr/bin/env python3
"""One-shot paired queue-cost experiment for Issue #5021."""
import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
POLICIES = ("STABLE_LIST_SCAN", "STABLE_SORTED_LIST", "ELIGIBLE_HEAP")
SIZES = (8, 32, 128, 512, 2048)
BLOCKS = 15


def sha(data):
    return hashlib.sha256(data).hexdigest()


def contract():
    freeze = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
    for name, expected in freeze["source_sha256"].items():
        actual = sha((ROOT / name).read_bytes())
        if actual != expected:
            raise RuntimeError("SOURCE_SHA256_MISMATCH:" + name)
    schedule_bytes = (ROOT / "scenarios.json").read_bytes()
    if sha(schedule_bytes) != freeze["schedule_sha256"]:
        raise RuntimeError("SCHEDULE_SHA256_MISMATCH")
    schedule = json.loads(schedule_bytes)
    if (schedule.get("schema") != "scheduler-cost-schedule-v1" or
            schedule.get("sizes") != list(SIZES) or
            schedule.get("blocks_per_size") != BLOCKS):
        raise RuntimeError("SCHEDULE_CONTRACT_MISMATCH")
    return freeze, schedule


def execute(candidates, policy):
    """Build the representation and drain it; caller surrounds timing."""
    if policy == "STABLE_LIST_SCAN":
        queue = [tuple(row) for row in candidates]
        trace = []
        while queue:
            selected = min(queue)
            trace.append(selected[3])
            queue.remove(selected)
        return trace
    if policy == "STABLE_SORTED_LIST":
        queue = sorted(tuple(row) for row in candidates)
        trace = []
        while queue:
            trace.append(queue.pop(0)[3])
        return trace
    if policy == "ELIGIBLE_HEAP":
        import heapq
        queue = [tuple(row) for row in candidates]
        heapq.heapify(queue)
        trace = []
        while queue:
            trace.append(heapq.heappop(queue)[3])
        return trace
    raise ValueError("UNKNOWN_POLICY")


def worker(schedule, size, block, policy):
    case = next(row for row in schedule["cases"] if row["size"] == size)
    candidates = case["blocks"][block]["candidates"]
    cpu_start = time.process_time_ns()
    wall_start = time.perf_counter_ns()
    trace = execute(candidates, policy)
    wall_ns = time.perf_counter_ns() - wall_start
    cpu_ns = time.process_time_ns() - cpu_start
    encoded_trace = json.dumps(trace, separators=(",", ":")).encode()
    return {
        "schema": "scheduler-cost-worker-v1",
        "size": size,
        "block": block,
        "policy": policy,
        "selected_count": len(trace),
        "trace": trace,
        "trace_sha256": sha(encoded_trace),
        "process_cpu_ns": cpu_ns,
        "wall_ns": wall_ns,
    }


def policy_order(size, block):
    value = sha(("5021-order:%d:%d" % (size, block)).encode("ascii"))
    offset = int(value[:8], 16) % len(POLICIES)
    return POLICIES[offset:] + POLICIES[:offset]


def formal(out_dir):
    freeze, schedule = contract()
    rows = []
    for size in SIZES:
        for block in range(BLOCKS):
            for policy in policy_order(size, block):
                command = [sys.executable, "-B", str(Path(__file__).resolve()),
                           "--worker", str(size), str(block), policy]
                env = dict(os.environ)
                env["PYTHONHASHSEED"] = "0"
                started = time.perf_counter_ns()
                try:
                    result = subprocess.run(command, cwd=str(ROOT), env=env,
                                             capture_output=True, text=True, timeout=30)
                    duration_ns = time.perf_counter_ns() - started
                    row = None
                    parse_error = None
                    try:
                        row = json.loads(result.stdout)
                    except Exception as exc:
                        parse_error = repr(exc)
                    rows.append({
                        "size": size, "block": block, "policy": policy,
                        "worker_exit_code": result.returncode,
                        "worker_elapsed_ns_including_startup": duration_ns,
                        "worker_stdout": result.stdout,
                        "worker_stderr": result.stderr,
                        "worker_parse_error": parse_error,
                        "result": row,
                    })
                except subprocess.TimeoutExpired as exc:
                    rows.append({
                        "size": size, "block": block, "policy": policy,
                        "worker_exit_code": None,
                        "worker_elapsed_ns_including_startup": time.perf_counter_ns() - started,
                        "worker_stdout": (exc.stdout or b"").decode("utf-8", "replace"),
                        "worker_stderr": (exc.stderr or b"").decode("utf-8", "replace"),
                        "worker_parse_error": "WORKER_TIMEOUT", "result": None,
                    })
    raw = {
        "schema": "scheduler-cost-raw-v1",
        "issue": 5021,
        "parent_issue": 2868,
        "allocation": freeze["allocation"],
        "freeze_parent_commit": freeze["freeze_parent_commit"],
        "source_sha256": freeze["source_sha256"],
        "schedule_sha256": freeze["schedule_sha256"],
        "runtime": {"python": sys.version, "implementation": platform.python_implementation(),
                    "platform": platform.platform(), "machine": platform.machine()},
        "worker_processes_expected": len(SIZES) * BLOCKS * len(POLICIES),
        "worker_processes_observed": len(rows),
        "policies": list(POLICIES),
        "sizes": list(SIZES),
        "blocks_per_size": BLOCKS,
        "rows": rows,
    }
    data = (json.dumps(raw, sort_keys=True, separators=(",", ":")) + "\n").encode()
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "raw.json").write_bytes(data)
    (out_dir / "raw.sha256").write_text(sha(data) + "  raw.json\n", encoding="ascii")
    print(json.dumps({"raw_sha256": sha(data), "rows": len(rows),
                      "worker_processes": len(rows), "output_bytes": len(data)}, sort_keys=True))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", nargs=3, metavar=("SIZE", "BLOCK", "POLICY"))
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    _, schedule = contract()
    if args.worker:
        row = worker(schedule, int(args.worker[0]), int(args.worker[1]), args.worker[2])
        print(json.dumps(row, sort_keys=True, separators=(",", ":")))
        return 0
    if args.out is None:
        parser.error("--out required for formal orchestration")
    formal(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
