"""Allocation-02 receipt classifier; argparse prevents --help side effects."""
import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path


def parse(value):
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError("offset required")
    return dt


def receipt_hash(row):
    fields = {k: row[k] for k in ("candidate", "auditor", "reported_at")}
    return hashlib.sha256(json.dumps(fields, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def classify(fixture, row):
    try:
        start, end = parse(fixture["allocation"]["start"]), parse(fixture["allocation"]["end"])
        c0, c1 = parse(row["candidate"]["start"]), parse(row["candidate"]["end"])
        a0, a1 = parse(row["auditor"]["start"]), parse(row["auditor"]["end"])
        posted = parse(row["reported_at"])
    except (KeyError, TypeError, ValueError):
        return "HOLD_INVALID_OR_AMBIGUOUS_TIME"
    if end <= start or c1 <= c0 or a1 <= a0:
        return "STOP_INVALID_INTERVAL"
    try:
        if row.get("receipt_sha256", receipt_hash(row)) != receipt_hash(row):
            return "HOLD_RECEIPT_INTEGRITY"
    except (KeyError, TypeError, ValueError):
        return "HOLD_RECEIPT_INTEGRITY"
    clock = fixture["allocation"].get("clock_id")
    if any(x.get("clock_id") != clock for x in (row["candidate"], row["auditor"])):
        return "HOLD_CLOCK_UNMAPPED"
    if c0 < start or c1 >= end or a0 < start or a1 >= end:
        return "STOP_OUTSIDE_ALLOCATION"
    if posted < c0 or posted < a1:
        return "HOLD_REPORT_PRECEDES_EXECUTION"
    return "ELIGIBLE_FOR_TIMING_GATE_ONLY"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    fixture = json.loads(args.fixture.read_text())
    rows = []
    for row in fixture["cases"]:
        raw = dict(row)
        raw.setdefault("receipt_sha256", receipt_hash(row))
        rows.append({**raw, "status": classify(fixture, raw)})
    result = {"schema": "6532-timing-candidate-a02-v1", "cases": rows,
              "scope": "authored finite timing gate only"}
    if args.output.exists():
        raise FileExistsError(args.output)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"cases": len(rows), "status": "CANDIDATE_COMPLETE"}, sort_keys=True))


if __name__ == "__main__":
    main()
