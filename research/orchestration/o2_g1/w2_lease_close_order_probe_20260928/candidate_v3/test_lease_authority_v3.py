"""Contract-aligned W2 lease-authority boundary tests."""
import copy
import json
import unittest
from pathlib import Path

from lease_authority_candidate_v3 import decide
from lease_authority_oracle_v3 import reconstruct


FIXTURE = Path(__file__).parents[1] / "o2-w2-independent-audit-20260928" / "trace-cases.json"


def make_case(edge=(510, 512), close=None, terminal=(500, 500)):
    document = json.loads(FIXTURE.read_bytes())
    case = copy.deepcopy(next(c for c in document["cases"] if c["case_id"] == "release-before-terminal"))
    opened = next(e for e in case["events"] if e["event_type"] == "LEASE_OPEN")
    opened["lineage"]["actuation_id"] = "A4"
    release = next(e for e in case["events"] if e.get("payload", {}).get("edge") == "up")
    release["time"].update({"lower_ns": edge[0], "upper_ns": edge[1]})
    release["payload"]["transition_interval_ns"] = list(edge)
    terminal_row = next(e for e in case["events"] if e["event_type"] == "PROGRAM_TERMINAL")
    terminal_row["time"] = {"lower_ns": terminal[0], "upper_ns": terminal[1], "censoring": "bounded"}
    if close is not None:
        lo, hi = close
        case["events"].append({
            "event_id": "lease-close-v3", "event_type": "LEASE_CLOSE", "source_role": "executor",
            "clock": copy.deepcopy(opened["clock"]),
            "time": {"lower_ns": lo, "upper_ns": hi, "censoring": "bounded" if lo != hi else "exact"},
            "input_authority": "false", "semantic_authority": "false",
            "lineage": {"lease_id": "L4", "actuation_id": "A4", "parent_event_ids": []}, "payload": {},
        })
    return case["events"]


class LeaseAuthorityV3Test(unittest.TestCase):
    def test_terminal_alone_does_not_close_an_open_matching_lease(self):
        rows = make_case(edge=(510, 512), close=None, terminal=(500, 500))
        expected = [{"event_id": "r2", "status": "AUTHORIZED_MATCH"},
                    {"event_id": "r3", "status": "AUTHORIZED_MATCH"}]
        self.assertEqual(decide(rows), expected)
        self.assertEqual(reconstruct(rows), expected)

    def test_explicit_close_before_edge_rejects_even_after_terminal(self):
        rows = make_case(edge=(510, 512), close=(500, 500), terminal=(450, 450))
        self.assertEqual(decide(rows), reconstruct(rows))
        self.assertEqual(decide(rows)[1]["status"], "REJECT_EDGE_AFTER_LEASE_CLOSE")

    def test_close_after_edge_preserves_authority(self):
        rows = make_case(edge=(400, 402), close=(450, 450), terminal=(350, 350))
        self.assertEqual(decide(rows), reconstruct(rows))
        self.assertEqual(decide(rows)[1]["status"], "AUTHORIZED_MATCH")

    def test_edge_interval_overlapping_close_is_held(self):
        rows = make_case(edge=(499, 501), close=(500, 500), terminal=(400, 400))
        self.assertEqual(decide(rows), reconstruct(rows))
        self.assertEqual(decide(rows)[1]["status"], "HOLD_EDGE_CLOSE_ORDER_UNCERTAIN")

    def test_close_missing_lineage_is_not_filled_from_terminal_or_chronology(self):
        rows = make_case(edge=(510, 512), close=(500, 500), terminal=(450, 450))
        close = next(e for e in rows if e["event_type"] == "LEASE_CLOSE")
        close["lineage"].pop("actuation_id")
        self.assertEqual(decide(rows), reconstruct(rows))
        self.assertEqual(decide(rows)[1]["status"], "HOLD_CLOSE_LINEAGE_UNRESOLVED")


if __name__ == "__main__":
    unittest.main(verbosity=2)
