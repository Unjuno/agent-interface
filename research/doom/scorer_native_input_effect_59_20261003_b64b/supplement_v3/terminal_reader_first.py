"""Ordinary post-result reader over immutable recorded times; no source import."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys


def count_strict_tail(origin, last_scheduled, finish, period):
    if any(type(x) is not int for x in (origin, last_scheduled, finish, period)):
        raise ValueError("integer times required")
    if not (0 <= origin <= last_scheduled < finish and period > 0):
        raise ValueError("ordered times and positive period required")
    if (last_scheduled - origin) % period:
        raise ValueError("recorded schedule is off the origin grid")
    last_index = (last_scheduled - origin) // period
    last_interior = (finish - origin - 1) // period
    return max(0, last_interior - last_index)


def main():
    start = datetime.now(timezone.utc).isoformat()
    path, dest = map(Path, sys.argv[1:])
    data = path.read_bytes()
    raw = json.loads(data)
    boundaries = [(0, 0, 1, 10, 0), (0, 0, 10, 10, 0),
                  (0, 0, 11, 10, 1), (0, 20, 30, 10, 0),
                  (0, 20, 31, 10, 1), (0, 0, 35, 10, 3)]
    for a, b, c, p, expected in boundaries:
        if count_strict_tail(a, b, c, p) != expected:
            raise ValueError("literal boundary failed")
    rows = []
    for row in raw["rows"]:
        case = row["case"]
        result = {"id": case["id"], "case": case,
                  "original_disposition": row["disposition"]}
        if row["disposition"] != "finish":
            result.update(classification="DIAGNOSTIC_CUTOFF_SEPARATE",
                          strict_interior_tail_points=None)
        else:
            receipts = [e["receipt"] for e in row["events"]
                        if e["kind"] == "sink_begin"]
            finishes = [e["ns"] for e in row["events"]
                        if e["kind"] == "command" and e["line"] == "FINISH"]
            if not receipts or len(finishes) != 1:
                raise ValueError("missing or duplicate recorded endpoint")
            origin = receipts[0]["scheduled_ns"]
            last = receipts[-1]["scheduled_ns"]
            finish = finishes[0]
            period = row["period_ns"]
            tail = count_strict_tail(origin, last, finish, period)
            missed = sum(r["missed_periods_before"] for r in receipts)
            stats = row["stats"]
            if stats["missed_sample_periods"] != missed:
                raise ValueError("completed-case stats/receipt count differs")
            result.update(origin_ns=origin, last_scheduled_ns=last,
                          finish_command_ns=finish, period_ns=period,
                          source_recorded_misses=missed,
                          completed_samples=len(receipts),
                          strict_interior_tail_points=tail,
                          classification="TERMINAL_GRID_UNREPRESENTED" if tail
                          else "NO_STRICT_INTERIOR_TAIL_POINT")
        rows.append(result)
    output = {"kind": "exploratory post-result recorded-grid qualification",
              "raw_sha256": hashlib.sha256(data).hexdigest(),
              "utc_start": start, "utc_end": datetime.now(timezone.utc).isoformat(),
              "endpoint": "recorded FINISH command, before saving its effect",
              "boundary_cases": len(boundaries), "rows": rows,
              "not_actual_observation_coverage_or_counter_redefinition": True}
    with dest.open("x") as f:
        json.dump(output, f, sort_keys=True, indent=2)
        f.write("\n")


if __name__ == "__main__":
    main()
