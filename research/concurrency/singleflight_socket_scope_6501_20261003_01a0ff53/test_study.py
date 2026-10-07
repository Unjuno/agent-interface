"""Real socket behaviors that would fail if scope/lifetime guards were omitted."""
import json
import unittest
from pathlib import Path

from study import run_case

CASES = {c["id"]: c for c in json.loads((Path(__file__).parent / "fixtures.json").read_text())["cases"]}


class ScopeTransferTests(unittest.TestCase):
    def test_equivalent_pending_calls_share_one_actual_socket_read(self):
        raw = run_case(CASES["equivalent_four"], "scope_inflight")
        self.assertEqual(len([e for e in raw["server_events"] if e["event"] == "server_received"]), 1)
        self.assertTrue(all(x["descriptive_match"] for x in raw["callers"]))
        self.assertEqual(raw["active_server_threads_after_cleanup"], 0)

    def test_distinct_target_origin_is_preserved(self):
        raw = run_case(CASES["different_target"], "scope_inflight")
        self.assertTrue(all(x["descriptive_match"] for x in raw["callers"]))
        self.assertEqual(len({x["call_id"] for x in raw["callers"]}), 2)

    def test_same_scope_late_caller_is_new_socket_read(self):
        raw = run_case(CASES["after_completion_same_scope"], "scope_inflight")
        self.assertEqual(len({x["call_id"] for x in raw["callers"]}), 2)
        self.assertTrue(all(x["descriptive_match"] for x in raw["callers"]))

    def test_predicate_only_control_exposes_wrong_scope_without_authority(self):
        raw = run_case(CASES["different_target"], "predicate_inflight")
        self.assertEqual([x["descriptive_match"] for x in raw["callers"]], [True, False])
        self.assertTrue(all(x["role"] == "read_only_descriptive" for x in raw["callers"]))


if __name__ == "__main__":
    unittest.main()
