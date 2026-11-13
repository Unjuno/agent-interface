from __future__ import annotations

import csv
import json
import platform
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: probe_clocks.py OUTPUT.json")

    samples: list[tuple[int, int, int, int, int]] = []
    for index in range(2000):
        monotonic_before_ns = time.monotonic_ns()
        perf_counter_ns = time.perf_counter_ns()
        monotonic_after_ns = time.monotonic_ns()
        samples.append(
            (
                index,
                monotonic_before_ns,
                perf_counter_ns,
                monotonic_after_ns,
                perf_counter_ns - ((monotonic_before_ns + monotonic_after_ns) // 2),
            )
        )

    deltas = [sample[4] for sample in samples]
    brackets = [sample[3] - sample[1] for sample in samples]
    result = {
        "schema": "map01-clock-correlation-probe-v1",
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "platform": platform.platform(),
        "python": sys.version,
        "monotonic_clock": str(time.get_clock_info("monotonic")),
        "perf_counter_clock": str(time.get_clock_info("perf_counter")),
        "sample_count": len(samples),
        "raw_csv": Path(sys.argv[1]).with_suffix(".csv").name,
        "summary": {
            "pair_delta_min_ns": min(deltas),
            "pair_delta_median_ns": statistics.median(deltas),
            "pair_delta_max_ns": max(deltas),
            "monotonic_bracket_max_ns": max(brackets),
        },
    }
    output = Path(sys.argv[1])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    with output.with_suffix(".csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(
            [
                "index",
                "monotonic_before_ns",
                "perf_counter_ns",
                "monotonic_after_ns",
                "perf_minus_monotonic_midpoint_ns",
            ]
        )
        writer.writerows(samples)
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
