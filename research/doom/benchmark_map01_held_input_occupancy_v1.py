"""Synthetic throughput benchmark for held-input posthoc reconstruction.

This benchmarks only analyzer compute overhead. It is not an Agent Interface
control-latency, model-latency, or gameplay benchmark.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import platform
import statistics
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "held", HERE / "analyze_map01_held_input_occupancy_v1.py")
held = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(held)

MS = 1_000_000


def dataset(count: int) -> list[dict]:
    events = []
    base = 0
    for index in range(count):
        identifier = f"p{index}"
        events.extend([
            {"event": "command", "command": {"op": "submit", "id": identifier,
                "steps": [{"op": "hold", "keys": ["a"], "duration_ms": 200}]},
             "received_ns": base + 1},
            {"event": "step_started", "id": identifier, "step": 0,
             "operation": "hold", "issued_ns": base + 10 * MS},
            {"event": "input_admission", "key": "a", "admitted_ns": base + 11 * MS,
             "input_ack_ns": base + 12 * MS},
            {"event": "keys_held", "id": identifier, "step": 0, "keys": ["a"],
             "input_ack_ns": base + 13 * MS},
            {"event": "observation", "id": identifier, "step": 0,
             "capture_ns": base + 100 * MS},
            {"event": "observation", "id": identifier, "step": 0,
             "capture_ns": base + 220 * MS},
            {"event": "step_completed", "id": identifier, "step": 0,
             "completed_ns": base + 230 * MS},
            {"event": "terminal", "id": identifier, "status": "completed",
             "release": {"verified": True, "keys_down": [], "reason": "release",
                         "verified_ns": base + 240 * MS},
             "terminal_ns": base + 241 * MS},
        ])
        base += 300 * MS
    return events


def cpu_name() -> str:
    try:
        for line in Path("/proc/cpuinfo").read_text(encoding="utf-8").splitlines():
            if line.startswith("model name"):
                return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return "unknown"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--holds", type=int, default=2000)
    parser.add_argument("--repetitions", type=int, default=25)
    parser.add_argument("--warmups", type=int, default=3)
    args = parser.parse_args()
    if args.holds <= 0 or args.repetitions <= 0 or args.warmups < 0:
        parser.error("positive holds/repetitions and nonnegative warmups required")
    events = dataset(args.holds)
    for _ in range(args.warmups):
        held.reconstruct_holds(events)
    samples_ms = []
    for _ in range(args.repetitions):
        started = time.perf_counter_ns()
        rows = held.reconstruct_holds(events)
        ended = time.perf_counter_ns()
        if len(rows) != args.holds:
            raise AssertionError("benchmark row count mismatch")
        samples_ms.append((ended - started) / 1e6)
    median = statistics.median(samples_ms)
    result = {
        "schema": "map01-held-input-occupancy-analyzer-benchmark-v1",
        "scope": "synthetic posthoc analyzer compute only; not runtime/control/model performance",
        "python": platform.python_version(),
        "kernel": platform.release(),
        "machine": platform.machine(),
        "cpu": cpu_name(),
        "visible_cpus": os.cpu_count(),
        "process_cpu_affinity": (len(os.sched_getaffinity(0))
                                 if hasattr(os, "sched_getaffinity") else None),
        "dataset_hold_steps": args.holds,
        "events": len(events),
        "repetitions": args.repetitions,
        "warmups": args.warmups,
        "median_ms": round(median, 3),
        "min_ms": round(min(samples_ms), 3),
        "max_ms": round(max(samples_ms), 3),
        "median_hold_steps_per_second": round(args.holds / (median / 1000), 1),
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
