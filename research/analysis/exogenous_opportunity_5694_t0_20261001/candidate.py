#!/usr/bin/env python3
"""Frozen finite exogenous-opportunity ledger candidate for Issue #5694."""
import hashlib
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIXTURE = HERE / "fixtures.json"
ALLOCATION = "EXOGENOUS-OPPORTUNITY-5694-T0-20261001-01"


def busy_at(tick, intervals):
    return any(start <= tick < end for start, end in intervals)


def run_case(case, deadline):
    rows = []
    available = 0
    case_deadline = case.get("deadline_ticks", deadline)
    for index, onset in enumerate(case["opportunities"]):
        row = {
            "type": "opportunity",
            "allocation": ALLOCATION,
            "case_id": case["case_id"],
            "opportunity_id": f"{case['case_id']}:{index:02d}",
            "onset_tick": onset,
            "deadline_tick": case_deadline,
            "clock_synchronized": case["clock_synchronized"],
        }
        if not case["clock_synchronized"]:
            row.update({"dispatch": None, "completion_tick": None,
                        "latency_ticks": None, "outcome": "UNKNOWN_CLOCK_ALIGNMENT"})
        elif busy_at(onset, case["busy_intervals"]):
            row.update({"dispatch": False, "completion_tick": None,
                        "latency_ticks": None,
                        "outcome": "SAFE_STOP" if case["safe_stop_on_busy"] else "MISSED_BUSY"})
        else:
            start = max(onset, available)
            completion = start + case["service_ticks"]
            available = completion
            latency = completion - onset
            row.update({"dispatch": True, "completion_tick": completion,
                        "latency_ticks": latency,
                        "outcome": "USEFUL" if latency <= case_deadline else "LATE"})
        rows.append(row)
    return rows


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: candidate.py RAW.jsonl")
    out = Path(sys.argv[1])
    if out.exists():
        raise SystemExit("STOP_OUTPUT_EXISTS")
    fixture_bytes = FIXTURE.read_bytes()
    fixture = json.loads(fixture_bytes)
    header = {"type": "header", "schema": "exogenous-opportunity-5694-raw-v1",
              "allocation": ALLOCATION,
              "fixture_sha256": hashlib.sha256(fixture_bytes).hexdigest(),
              "case_count": len(fixture["cases"])}
    rows = [header]
    for case in fixture["cases"]:
        rows.extend(run_case(case, fixture["deadline_ticks"]))
    raw = "".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n"
                   for row in rows).encode("utf-8")
    out.write_bytes(raw)
    print(json.dumps({"status": "CANDIDATE_COMPLETE", "rows": len(rows),
                      "sha256": hashlib.sha256(raw).hexdigest()}, sort_keys=True))


if __name__ == "__main__":
    main()
