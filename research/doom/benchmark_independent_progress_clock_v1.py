from __future__ import annotations

import json
import os
from pathlib import Path
import platform
import statistics
import sys
import time

from independent_progress_clock_v1 import ProgressClock, ProgressSample


def cpu_model() -> str | None:
    path = Path("/proc/cpuinfo")
    if not path.exists():
        return None
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.lower().startswith("model name"):
            return line.split(":", 1)[1].strip()
    return None


def run(n: int) -> tuple[int, int]:
    clock = ProgressClock()
    emitted = 0
    clock.ingest(ProgressSample(1, 0, 0, False, False, False))
    kills = 0
    deaths = 0
    for index in range(1, n + 1):
        # Sparse deterministic events: positive kill every 25k samples;
        # negative death every 40k. No episode terminal in the compute loop.
        if index % 25_000 == 0:
            kills += 1
        if index % 40_000 == 0:
            deaths += 1
        emitted += len(clock.ingest(ProgressSample(
            1 + index,
            kills,
            deaths,
            False,
            False,
            False,
        )))
    return n, emitted


def main() -> None:
    n = 100_000
    warmups = 3
    repetitions = 15
    for _ in range(warmups):
        run(n)
    elapsed_ms = []
    event_counts = []
    for _ in range(repetitions):
        start = time.perf_counter_ns()
        processed, emitted = run(n)
        elapsed_ms.append((time.perf_counter_ns() - start) / 1e6)
        event_counts.append(emitted)
    med = statistics.median(elapsed_ms)
    affinity = sorted(os.sched_getaffinity(0)) if hasattr(os, "sched_getaffinity") else None
    result = {
        "schema": "independent-progress-clock-benchmark-v1",
        "environment": {
            "python": sys.version.split()[0],
            "implementation": platform.python_implementation(),
            "kernel": platform.release(),
            "machine": platform.machine(),
            "cpu_model": cpu_model(),
            "cpu_affinity": affinity,
            "cpu_clock": "not pinned / unavailable",
            "concurrency": "single Python process, single thread",
        },
        "workload": {
            "samples_per_repetition": n,
            "warmups": warmups,
            "measured_repetitions": repetitions,
            "batch": "one ProgressSample per ingest call",
            "event_counts": event_counts,
        },
        "elapsed_ms": {
            "median": med,
            "min": min(elapsed_ms),
            "max": max(elapsed_ms),
            "all": elapsed_ms,
        },
        "throughput_samples_per_second_median": n / (med / 1000),
        "scope": "pure scorer state-machine compute only; not ViZDoom polling, runtime latency, or model latency",
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
