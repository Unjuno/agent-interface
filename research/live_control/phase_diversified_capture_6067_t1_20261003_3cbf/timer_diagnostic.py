"""Excluded wait-boundary qualification, no X11 or formal cue exposures."""
import hashlib
import json
import time
from pathlib import Path

from common import until, write


def coarse_spin(deadline):
    remain = deadline - time.monotonic_ns()
    if remain > 15_000_000:
        time.sleep((remain - 15_000_000) / 1e9)
    while time.monotonic_ns() < deadline:
        pass


def stats():
    return {key: int(value) for key, value in
            (line.split() for line in Path("/sys/fs/cgroup/cpu.stat").read_text().splitlines())}


def main():
    before = stats()
    samples = []
    order = ["sleep", "coarse_spin", "coarse_spin", "sleep"] * 4
    for index, arm in enumerate(order):
        due = time.monotonic_ns() + 120_000_000
        cpu_start = time.process_time_ns()
        (until if arm == "sleep" else coarse_spin)(due)
        actual = time.monotonic_ns()
        cpu_end = time.process_time_ns()
        samples.append({"index": index, "arm": arm, "due_ns": due,
                        "returned_ns": actual, "lateness_ns": actual - due,
                        "process_cpu_ns": cpu_end - cpu_start})
    result = {"kind": "EXCLUDED_TIMER_CONSTRUCTION", "samples": samples,
              "common_sha256": hashlib.sha256(Path(__file__).with_name("common.py").read_bytes()).hexdigest(),
              "before_cpu_stat": before, "after_cpu_stat": stats(),
              "cgroups": {n: Path("/sys/fs/cgroup", n).read_text().strip()
                          for n in ("cpu.max", "memory.max", "memory.swap.max", "pids.max")},
              "scientific_cells": 0, "x11_cells": 0, "input_events": 0,
              "model_calls": 0, "note": "timer-only comparison is not proof of the original X11 cause"}
    write("/out/timer.json", result)
    print(json.dumps({arm: {"max_lateness_ns": max(r["lateness_ns"] for r in samples if r["arm"] == arm),
                           "mean_process_cpu_ns": sum(r["process_cpu_ns"] for r in samples if r["arm"] == arm) // 8}
                      for arm in ("sleep", "coarse_spin")}))


if __name__ == "__main__":
    main()
