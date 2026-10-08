"""Candidate classifier for Issue #6532's finite authored receipt table."""
import json
import hashlib
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "results" / "candidate.json"


def parse(value):
    stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if stamp.tzinfo is None or stamp.utcoffset() is None:
        raise ValueError("timestamp lacks an explicit UTC offset")
    return stamp


def classify(fixture, case):
    try:
        start, end = parse(fixture["allocation"]["start"]), parse(fixture["allocation"]["end"])
        spans = [case["candidate"], case["auditor"]]
        points = [(parse(x["start"]), parse(x["end"])) for x in spans]
        reported = parse(case["reported_at"])
    except (KeyError, TypeError, ValueError):
        return "HOLD_INVALID_OR_AMBIGUOUS_TIME"
    if end <= start or any(b <= a for a, b in points):
        return "STOP_INVALID_INTERVAL"
    receipt = {key: case[key] for key in ("candidate", "auditor", "reported_at")}
    actual_hash = hashlib.sha256(json.dumps(receipt, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    if case.get("receipt_sha256") != actual_hash:
        return "HOLD_RECEIPT_INTEGRITY"
    expected_clock = fixture["allocation"].get("clock_id")
    if any(x.get("clock_id") != expected_clock for x in spans):
        return "HOLD_CLOCK_UNMAPPED"
    if not all(start <= a and b < end for a, b in points):
        return "STOP_OUTSIDE_ALLOCATION"
    if reported < points[0][0] or reported < points[1][1]:
        return "HOLD_REPORT_PRECEDES_EXECUTION"
    return "ELIGIBLE_FOR_TIMING_GATE_ONLY"


def run():
    fixture = json.loads((HERE / "fixture.json").read_text())
    result = {
        "schema": "6532-timing-candidate-v1",
        "cases": [
            {"id": case["id"], "status": classify(fixture, case),
             "candidate": case["candidate"], "auditor": case["auditor"],
             "reported_at": case["reported_at"], "receipt_sha256": case["receipt_sha256"]}
            for case in fixture["cases"]
        ],
        "scope": "authored finite timestamp contract only; not clock truth or historical-run evidence",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    if OUT.exists():
        raise FileExistsError(f"refusing to overwrite {OUT}")
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"cases": len(result["cases"]), "status": "CANDIDATE_COMPLETE"}, sort_keys=True))


if __name__ == "__main__":
    run()
