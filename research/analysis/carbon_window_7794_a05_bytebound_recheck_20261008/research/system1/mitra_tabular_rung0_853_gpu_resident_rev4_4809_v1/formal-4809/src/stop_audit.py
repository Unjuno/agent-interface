#!/usr/bin/env python3
"""Independent standard-library audit for an Issue #4809 typed STOP."""
import json
import sys
from pathlib import Path

ALLOCATION = "mitra-gpu-rung0-853-rev4-successor-local-20260927-01"


def validate(stop: dict) -> dict:
    errors = []
    if stop.get("schema") != "issue-4809-mitra-gpu-stop-v1":
        errors.append("schema")
    if stop.get("allocation") != ALLOCATION:
        errors.append("allocation")
    if not isinstance(stop.get("stage"), str) or not stop["stage"]:
        errors.append("stage")
    if not isinstance(stop.get("exception_type"), str) or not isinstance(stop.get("exception"), str):
        errors.append("exception")
    for name in ("optimizer_step_calls", "model_load_count", "partial_query_count"):
        if not isinstance(stop.get(name), int) or stop[name] < 0:
            errors.append(name)
    records = stop.get("partial_query_records")
    if not isinstance(records, list) or stop.get("partial_query_count") != len(records):
        errors.append("partial_query_records")
    elif any(not isinstance(row, dict) or row.get("phase") not in {"warmup", "formal", "repeat"} or not isinstance(row.get("index"), int) for row in records):
        errors.append("partial_query_shape")
    start, end = stop.get("start_unix_ns"), stop.get("stop_unix_ns")
    if not isinstance(start, int) or not isinstance(end, int) or end < start:
        errors.append("time_interval")
    return {"pass": not errors, "errors": errors, "allocation": stop.get("allocation"), "partial_query_count": stop.get("partial_query_count")}


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/out/STOP.json")
    result = validate(json.loads(path.read_text(encoding="utf-8")))
    print(json.dumps(result, sort_keys=True))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
