#!/usr/bin/env python3
"""Frozen one-shot queue-cost runner for Issue #5044."""
import argparse
import hashlib
import heapq
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

SRC = Path(__file__).resolve().parent
POLICIES = ("STABLE_LIST_SCAN", "STABLE_SORTED_LIST", "ELIGIBLE_HEAP")
SIZES = (8, 32, 128, 512, 2048)
BLOCKS = 15


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load_contract(input_path):
    freeze = json.loads((SRC / "FREEZE.json").read_text(encoding="utf-8"))
    for name, expected in freeze["source_sha256"].items():
        actual = sha((SRC / name).read_bytes())
        if actual != expected:
            raise RuntimeError("SOURCE_SHA256_MISMATCH:" + name)
    schedule_bytes = Path(input_path).read_bytes()
    if sha(schedule_bytes) != freeze["schedule_sha256"]:
        raise RuntimeError("SCHEDULE_SHA256_MISMATCH")
    schedule = json.loads(schedule_bytes)
    if (schedule.get("schema") != "scheduler-cost-schedule-v1" or
            schedule.get("sizes") != list(SIZES) or
            schedule.get("blocks_per_size") != BLOCKS):
        raise RuntimeError("SCHEDULE_CONTRACT_MISMATCH")
    if "heapq" not in sys.modules:
        raise RuntimeError("HEAPQ_NOT_IMPORTED_BEFORE_WORKER")
    return freeze, schedule


def select(candidates, policy):
    """Construct a queue and drain it; called only inside the timer."""
    if policy == "STABLE_LIST_SCAN":
        queue = [tuple(row) for row in candidates]
        trace = []
        while queue:
            chosen = min(queue)
            trace.append(chosen[3])
            queue.remove(chosen)
        return trace
    if policy == "STABLE_SORTED_LIST":
        queue = sorted(tuple(row) for row in candidates)
        trace = []
        while queue:
            trace.append(queue.pop(0)[3])
        return trace
    if policy == "ELIGIBLE_HEAP":
        queue = [tuple(row) for row in candidates]
        heapq.heapify(queue)
        trace = []
        while queue:
            trace.append(heapq.heappop(queue)[3])
        return trace
    raise ValueError("UNKNOWN_POLICY")


def case_candidates(schedule, size, block):
    for case in schedule["cases"]:
        if case["size"] == size:
            for item in case["blocks"]:
                if item["block"] == block:
                    return item["candidates"]
    raise KeyError("CASE_NOT_FOUND:%d:%d" % (size, block))


def worker(input_path, size, block, policy):
    freeze, schedule = load_contract(input_path)
    candidates = case_candidates(schedule, size, block)
    heapq_loaded_before_timer = "heapq" in sys.modules
    if not heapq_loaded_before_timer:
        raise RuntimeError("HEAPQ_NOT_IMPORTED_AT_TIMER_START")
    cpu_start = time.process_time_ns()
    wall_start = time.perf_counter_ns()
    trace = select(candidates, policy)
    wall_ns = time.perf_counter_ns() - wall_start
    cpu_ns = time.process_time_ns() - cpu_start
    return {
        "schema": "scheduler-cost-import-boundary-worker-v1",
        "size": size,
        "block": block,
        "policy": policy,
        "selected_count": len(trace),
        "trace": trace,
        "trace_sha256": sha(json.dumps(trace, separators=(",", ":")).encode()),
        "queue_process_cpu_ns": cpu_ns,
        "queue_wall_ns": wall_ns,
        "heapq_loaded_before_timer": heapq_loaded_before_timer,
        "schedule_sha256": freeze["schedule_sha256"],
    }


def policy_order(size, block):
    value = sha(("5021-order:%d:%d" % (size, block)).encode("ascii"))
    offset = int(value[:8], 16) % len(POLICIES)
    return POLICIES[offset:] + POLICIES[:offset]


def formal(input_path, out_dir):
    freeze, schedule = load_contract(input_path)
    if out_dir.exists() and any(out_dir.iterdir()):
        raise RuntimeError("FORMAL_OUTPUT_NOT_EMPTY")
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for size in SIZES:
        for block in range(BLOCKS):
            for policy in policy_order(size, block):
                command = [sys.executable, "-B", str(Path(__file__).resolve()),
                           "--input", str(Path(input_path).resolve()), "--worker",
                           str(size), str(block), policy]
                env = dict(os.environ)
                env["PYTHONHASHSEED"] = "0"
                started = time.perf_counter_ns()
                try:
                    result = subprocess.run(command, cwd=str(SRC), env=env,
                                             capture_output=True, text=True, timeout=30)
                    elapsed_ns = time.perf_counter_ns() - started
                    parsed = None
                    parse_error = None
                    try:
                        parsed = json.loads(result.stdout)
                    except Exception as exc:
                        parse_error = repr(exc)
                    rows.append({
                        "size": size, "block": block, "policy": policy,
                        "worker_exit_code": result.returncode,
                        "worker_elapsed_ns_including_startup_import_and_io": elapsed_ns,
                        "worker_stdout": result.stdout,
                        "worker_stderr": result.stderr,
                        "worker_parse_error": parse_error,
                        "result": parsed,
                    })
                except subprocess.TimeoutExpired as exc:
                    rows.append({
                        "size": size, "block": block, "policy": policy,
                        "worker_exit_code": None,
                        "worker_elapsed_ns_including_startup_import_and_io":
                            time.perf_counter_ns() - started,
                        "worker_stdout": (exc.stdout or b"").decode("utf-8", "replace"),
                        "worker_stderr": (exc.stderr or b"").decode("utf-8", "replace"),
                        "worker_parse_error": "WORKER_TIMEOUT", "result": None,
                    })
    raw = {
        "schema": "scheduler-cost-import-boundary-raw-v1",
        "issue": 5044,
        "parent_issue": 2868,
        "predecessor_issue": 5021,
        "allocation": freeze["allocation"],
        "freeze_parent_commit": freeze["base_main_sha"],
        "source_sha256": freeze["source_sha256"],
        "schedule_sha256": freeze["schedule_sha256"],
        "runtime": {"python": sys.version, "implementation": platform.python_implementation(),
                    "platform": platform.platform(), "machine": platform.machine()},
        "worker_processes_expected": len(SIZES) * BLOCKS * len(POLICIES),
        "worker_processes_observed": len(rows),
        "policies": list(POLICIES), "sizes": list(SIZES), "blocks_per_size": BLOCKS,
        "rows": rows,
    }
    data = (json.dumps(raw, sort_keys=True, separators=(",", ":")) + "\n").encode()
    (out_dir / "raw.json").write_bytes(data)
    (out_dir / "raw.sha256").write_text(sha(data) + "  raw.json\n", encoding="ascii")
    print(json.dumps({"raw_sha256": sha(data), "rows": len(rows),
                      "worker_processes": len(rows), "output_bytes": len(data)}, sort_keys=True))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--worker", nargs=3, metavar=("SIZE", "BLOCK", "POLICY"))
    parser.add_argument("--formal", type=Path)
    args = parser.parse_args()
    if args.worker:
        result = worker(args.input, int(args.worker[0]), int(args.worker[1]), args.worker[2])
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        return 0
    if args.formal is None:
        parser.error("--formal output-directory required")
    formal(args.input, args.formal)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
