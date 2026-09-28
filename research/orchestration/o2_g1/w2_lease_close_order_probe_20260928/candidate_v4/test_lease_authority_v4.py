"""Focused lease-open/close interval tests for contract-aligned candidate v4."""
import copy
import json
import unittest
from pathlib import Path

from lease_authority_candidate_v4 import evaluate
from lease_authority_oracle_v4 import audit


FIXTURE = Path(__file__).parents[1] / "o2-w2-independent-audit-20260928" / "trace-cases.json"


def trace(edge=(100, 102), opened=(0, 0), closed=None, terminal=(500, 500)):
    document = json.loads(FIXTURE.read_bytes())
    case = copy.deepcopy(next(c for c in document["cases"] if c["case_id"] == "release-before-terminal"))
    open_row = next(e for e in case["events"] if e["event_type"] == "LEASE_OPEN")
    open_row["lineage"]["actuation_id"] = "A4"
    open_row["time"] = {"lower_ns": opened[0], "upper_ns": opened[1], "censoring": "bounded"}
    terminal_row = next(e for e in case["events"] if e["event_type"] == "PROGRAM_TERMINAL")
    if terminal is None:
        case["events"].remove(terminal_row)
    else:
        terminal_row["time"] = {"lower_ns": terminal[0], "upper_ns": terminal[1], "censoring": "bounded"}
    up = next(e for e in case["events"] if e.get("payload", {}).get("edge") == "up")
    up["time"].update({"lower_ns": edge[0], "upper_ns": edge[1]})
    up["payload"]["transition_interval_ns"] = list(edge)
    if closed is not None:
        close_time = {"lower_ns": closed[0], "upper_ns": closed[1], "censoring": "bounded"}
        case["events"].append({"event_id": "close-v4", "event_type": "LEASE_CLOSE", "source_role": "executor",
            "clock": copy.deepcopy(open_row["clock"]), "time": close_time, "input_authority": "false",
            "semantic_authority": "false", "lineage": {"lease_id": "L4", "actuation_id": "A4", "parent_event_ids": []}, "payload": {}})
    return case["events"]


class LeaseAuthorityV4Test(unittest.TestCase):
    def assert_match(self, rows, wanted):
        candidate, oracle = evaluate(rows), audit(rows)
        self.assertEqual(candidate, oracle)
        self.assertEqual(candidate[1]["status"], wanted)

    def test_edge_before_future_open_rejects(self):
        self.assert_match(trace(edge=(100, 102), opened=(200, 200)), "REJECT_EDGE_BEFORE_LEASE_OPEN")

    def test_edge_interval_overlapping_open_is_held(self):
        self.assert_match(trace(edge=(199, 201), opened=(200, 200)), "HOLD_EDGE_LEASE_OPEN_ORDER_UNCERTAIN")

    def test_edge_strictly_after_open_can_be_authorized(self):
        self.assert_match(trace(edge=(201, 202), opened=(199, 200)), "AUTHORIZED_MATCH")

    def test_unknown_open_time_holds(self):
        rows = trace(edge=(201, 202), opened=(199, 200))
        next(e for e in rows if e["event_type"] == "LEASE_OPEN")["time"] = {"lower_ns": None, "upper_ns": None, "censoring": "unknown"}
        self.assert_match(rows, "HOLD_UNKNOWN_LEASE_OPEN_TIME")

    def test_missing_lease_open_holds(self):
        rows = trace(edge=(201, 202), opened=(199, 200))
        rows[:] = [e for e in rows if e["event_type"] != "LEASE_OPEN"]
        candidate, oracle = evaluate(rows), audit(rows)
        self.assertEqual(candidate, oracle)
        self.assertEqual(candidate[1]["status"], "HOLD_LEASE_OPEN_MISSING")

    def test_terminal_alone_does_not_close_authority(self):
        self.assert_match(trace(edge=(510, 512), opened=(0, 0), terminal=(500, 500)), "AUTHORIZED_MATCH")

    def test_explicit_close_still_bounds_authority(self):
        self.assert_match(trace(edge=(510, 512), opened=(0, 0), closed=(500, 500)), "REJECT_EDGE_AFTER_LEASE_CLOSE")


if __name__ == "__main__":
    unittest.main(verbosity=2)
