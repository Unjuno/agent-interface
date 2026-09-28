"""Finite-grid audit for open/close interval authority boundaries."""
import itertools
import json
from pathlib import Path

from lease_authority_candidate_v4 import evaluate
from lease_authority_oracle_v4 import audit


def interval(lo, hi):
    return {"lower_ns": lo, "upper_ns": hi, "censoring": "bounded"}


def expected(edge, opened, closed, close_lease, close_action):
    if not isinstance(opened, tuple):
        return "HOLD_UNKNOWN_LEASE_OPEN_TIME"
    if edge[1] < opened[0]:
        return "REJECT_EDGE_BEFORE_LEASE_OPEN"
    if opened[1] >= edge[0]:
        return "HOLD_EDGE_LEASE_OPEN_ORDER_UNCERTAIN"
    if closed is None:
        return "AUTHORIZED_MATCH"
    if close_lease != "L":
        return "AUTHORIZED_MATCH"
    if close_action != "A":
        return "HOLD_CLOSE_LINEAGE_UNRESOLVED"
    if not isinstance(closed, tuple):
        return "HOLD_UNKNOWN_CLOSE_TIME"
    if closed[1] < edge[0]:
        return "REJECT_EDGE_AFTER_LEASE_CLOSE"
    if edge[1] >= closed[0]:
        return "HOLD_EDGE_CLOSE_ORDER_UNCERTAIN"
    return "AUTHORIZED_MATCH"


def main():
    intervals = [(lo, hi) for lo in range(6) for hi in range(lo, 6)]
    openings = [None, *intervals, "unknown", "invalid"]
    closings = [None, *intervals, "unknown", "invalid"]
    terminals = [None, *intervals, "unknown", "invalid"]
    lineages = [("L", "A"), ("L", "FOREIGN"), ("L", None), ("OTHER", "A")]
    fixture_path = Path(__file__).parents[1] / "o2-w2-independent-audit-20260928" / "trace-cases.json"
    import copy
    fixture = json.loads(fixture_path.read_bytes())
    template = next(c for c in fixture["cases"] if c["case_id"] == "release-before-terminal")["events"]
    checked = 0
    mismatches = []
    for edge, opened, closed, (close_lease, close_action), terminal in itertools.product(
            intervals, openings, closings, lineages, terminals):
        if opened is None:
            opened_row_time = {"lower_ns": None, "upper_ns": None, "censoring": "unknown"}
        elif opened == "unknown":
            opened_row_time = {"lower_ns": None, "upper_ns": None, "censoring": "unknown"}
        elif opened == "invalid":
            opened_row_time = {"lower_ns": 3, "upper_ns": 2, "censoring": "invalid"}
        else:
            opened_row_time = interval(*opened)
        if closed in (None, "unknown"):
            close_time = {"lower_ns": None, "upper_ns": None, "censoring": "unknown"}
        elif closed == "invalid":
            close_time = {"lower_ns": 3, "upper_ns": 2, "censoring": "invalid"}
        else:
            close_time = interval(*closed)

        rows = copy.deepcopy(template)
        open_row = next(row for row in rows if row["event_type"] == "LEASE_OPEN")
        open_row["lineage"]["lease_id"] = "L"
        open_row["lineage"]["actuation_id"] = "A"
        open_row["time"] = opened_row_time
        edge_row = next(row for row in rows if row["event_type"] == "INPUT_EDGE_BRACKET" and row.get("payload", {}).get("edge") == "up")
        edge_row["lineage"]["lease_id"] = "L"
        edge_row["lineage"]["actuation_id"] = "A"
        edge_row["payload"]["transition_interval_ns"] = list(edge)
        edge_row["time"] = interval(*edge)
        rows[:] = [row for row in rows if row["event_type"] != "LEASE_CLOSE"]
        if closed is not None:
            rows.append({"event_id": "v4-close", "event_type": "LEASE_CLOSE", "time": close_time,
                         "lineage": {"lease_id": close_lease, "actuation_id": close_action}, "payload": {}})
        rows[:] = [row for row in rows if row["event_type"] != "PROGRAM_TERMINAL"]
        if terminal is not None:
            t = {"lower_ns": None, "upper_ns": None, "censoring": "unknown"} if terminal == "unknown" else (
                {"lower_ns": 3, "upper_ns": 2, "censoring": "invalid"} if terminal == "invalid" else interval(*terminal))
            rows.append({"event_id": "v4-terminal", "event_type": "PROGRAM_TERMINAL", "time": t,
                         "lineage": {"lease_id": "L", "actuation_id": "A"}, "payload": {}})
        want = expected(edge, opened,
                        closed,
                        close_lease, close_action)
        got = evaluate(rows)[-1]["status"]
        oracle = audit(rows)[-1]["status"]
        checked += 1
        if got != want or oracle != want:
            mismatches.append({"case": checked, "expected": want, "candidate": got, "oracle": oracle,
                               "edge": edge, "open": opened, "close": closed, "close_lineage": [close_lease, close_action], "terminal": terminal})
            if len(mismatches) >= 10:
                break
    print(json.dumps({"checked": checked, "mismatch_count": len(mismatches), "first_mismatches": mismatches}, indent=2))
    raise SystemExit(bool(mismatches))


if __name__ == "__main__":
    main()
