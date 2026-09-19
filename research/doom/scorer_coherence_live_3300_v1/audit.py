"""Fail-closed audit for live scorer coherence JSONL."""
import json
import sys
from pathlib import Path


REQUIRED = {
    "sample", "scheduled_ns", "sample_started_ns", "sample_finished_ns",
    "capture_ns", "typed_ready_ns", "frame_sha256", "epoch",
    "missed_periods_before", "decision", "input_emitted",
}


def audit(path):
    rows = [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]
    errors = []
    last_sample = None
    for index, row in enumerate(rows):
        missing = sorted(REQUIRED - row.keys())
        if missing:
            errors.append(f"row={index}: missing={missing}")
            continue
        times = [row[k] for k in ("scheduled_ns", "sample_started_ns", "capture_ns", "typed_ready_ns", "sample_finished_ns")]
        if any(type(value) is not int or value < 0 for value in times):
            errors.append(f"row={index}: invalid timestamps")
        elif not times[0] <= times[1] <= times[2] <= times[3] <= times[4]:
            errors.append(f"row={index}: timestamp order")
        if type(row["missed_periods_before"]) is not int or row["missed_periods_before"] < 0:
            errors.append(f"row={index}: invalid missed-period accounting")
        if last_sample is not None and row["sample"] <= last_sample:
            errors.append(f"row={index}: non-increasing sample")
        last_sample = row["sample"]
        if row["decision"] != "ACCEPT" and row["input_emitted"]:
            errors.append(f"row={index}: rejected row emitted input")
        if row["decision"] == "ACCEPT" and not row["frame_sha256"]:
            errors.append(f"row={index}: accepted row missing frame digest")
    status = "PASS_AUDIT" if rows and not errors else "HOLD_AUDIT"
    print(f"{status} rows={len(rows)} errors={len(errors)}")
    for error in errors:
        print(f"ERROR {error}")
    return 0 if status == "PASS_AUDIT" else 1


if __name__ == "__main__":
    raise SystemExit(audit(sys.argv[1]))
