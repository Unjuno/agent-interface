#!/usr/bin/env python3
"""Independent standard-library validation for typed Issue #4821 STOPs."""
import json
from pathlib import Path

EXPECTED_ALLOCATION = "mitra-gpu-rung0-853-label-encoding-successor-local-20260927-01"
OUT = Path("/out")


def main():
    stop = json.loads((OUT / "STOP.json").read_text(encoding="utf-8"))
    errors = []
    if stop.get("schema") != "issue-4821-mitra-gpu-stop-v1": errors.append("schema")
    if stop.get("allocation") != EXPECTED_ALLOCATION: errors.append("allocation")
    if stop.get("stage") not in {"preflight", "support_context_setup", "warmup", "formal_queries", "repeat_queries"}: errors.append("stage")
    if not isinstance(stop.get("exception_type"), str) or not stop["exception_type"]: errors.append("exception_type")
    if not isinstance(stop.get("exception"), str) or not stop["exception"]: errors.append("exception")
    if stop.get("model_load_count", -1) < 0 or stop.get("optimizer_step_calls", -1) < 0: errors.append("counts")
    if stop.get("partial_query_count") != len(stop.get("partial_query_records", [])): errors.append("partial_queries")
    if not isinstance(stop.get("start_unix_ns"), int) or not isinstance(stop.get("stop_unix_ns"), int) or stop["stop_unix_ns"] < stop["start_unix_ns"]: errors.append("timestamps")
    result = {"schema":"issue-4821-stop-audit-v1","allocation":EXPECTED_ALLOCATION,"pass":not errors,"errors":errors,"partial_query_count":stop.get("partial_query_count")}
    (OUT / "STOP_AUDIT.json").write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
