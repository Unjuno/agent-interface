from __future__ import annotations

import hashlib
import itertools
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = HERE / "cases.json"
RAW = HERE / "candidate.raw.json"
OUT = HERE / "audit.raw.json"
EXPECTED = {
    "positive_same_epoch": "CONSISTENT",
    "cross_epoch_after_invalidation": "CONTRADICTORY",
    "release_message_in_flight": "INCOMPLETE_IN_FLIGHT",
    "missing_causal_parent": "UNKNOWN",
    "reset_midway": "CONTRADICTORY",
    "genuine_alternative_root_wrong_epoch": "CONTRADICTORY",
}


def oracle_cut_count(trace: list[dict]) -> int | None:
    index = {event["id"]: n for n, event in enumerate(trace)}
    if len(index) != len(trace) or any(parent not in index for event in trace for parent in event.get("parents", [])):
        return None
    valid_count = 0
    for mask in range(1 << len(trace)):
        selected = {trace[i]["id"] for i in range(len(trace)) if mask & (1 << i)}
        rejected = False
        for event in trace:
            if event["id"] not in selected:
                continue
            if not set(event.get("parents", ())).issubset(selected):
                rejected = True
                break
            same_stream_predecessors = (prior for prior in trace if prior["stream"] == event["stream"] and prior["seq"] < event["seq"])
            if any(prior["id"] not in selected for prior in same_stream_predecessors):
                rejected = True
                break
        valid_count += int(not rejected)
    return valid_count


def main() -> None:
    if OUT.exists():
        raise SystemExit("STOP_AUDIT_OUTPUT_ALREADY_EXISTS")
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    raw = RAW.read_bytes()
    result = json.loads(raw)
    rows = {row.get("case_id"): row for row in result.get("cases", [])}
    errors = []
    if set(rows) != set(EXPECTED):
        errors.append("CASE_SET_MISMATCH")
    graph_false_ready = []
    for case in spec["cases"]:
        row = rows.get(case["case_id"], {})
        expected = EXPECTED[case["case_id"]]
        if row.get("cut_status") != expected:
            errors.append(f"{case['case_id']}:CLASS_MISMATCH")
        expected_ready = expected == "CONSISTENT"
        if row.get("ready") is not expected_ready:
            errors.append(f"{case['case_id']}:AUTHORITY_MISMATCH")
        if row.get("graph_only_ready") is not True:
            errors.append(f"{case['case_id']}:GRAPH_ONLY_CONTRAST_MISSING")
        if not expected_ready and row.get("graph_only_ready") is True:
            graph_false_ready.append(case["case_id"])
        independently_counted = oracle_cut_count(case["events"])
        if row.get("legal_cut_count") != independently_counted:
            errors.append(f"{case['case_id']}:LEGAL_CUT_COUNT_MISMATCH")
        if case.get("expect") != expected:
            errors.append(f"{case['case_id']}:FROZEN_ORACLE_SPEC_MISMATCH")
    ready_ids = [case_id for case_id, row in rows.items() if row.get("ready") is True]
    status = "PASS_METHOD_SCOPED" if not errors and ready_ids == ["positive_same_epoch"] and len(graph_false_ready) == 5 else "FAIL_ORACLE_MISMATCH"
    audit = {"schema": "blackstart-causal-cut-independent-audit-v1", "status": status,
             "candidate_sha256": hashlib.sha256(raw).hexdigest(), "cases": len(EXPECTED),
             "graph_only_false_ready_ids": graph_false_ready, "cut_aware_ready_ids": ready_ids,
             "independent_errors": errors}
    OUT.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(audit, sort_keys=True))
    raise SystemExit(0 if not errors and status == "PASS_METHOD_SCOPED" else 1)


if __name__ == "__main__":
    main()
