import json
import unittest
from pathlib import Path

from runner import classify


DATA = json.loads((Path(__file__).parent / "inputs.json").read_text(encoding="utf-8"))


class InvocationBoundaryTests(unittest.TestCase):
    def test_single_tagged_invocation_passes(self):
        row = classify(DATA["cases"][0], 1)
        self.assertEqual(row["decision"], "PASS_INVOCATION_BOUNDARY_CONTRACT")
        self.assertEqual(row["invocation_count"], 1)

    def test_historical_unbound_conflict_stops_without_retroactive_ids(self):
        row = classify(DATA["cases"][1], 1)
        self.assertEqual(row["decision"], "STOP_INVOCATION_PROVENANCE_OR_BOUNDARY")
        self.assertIn(None, row["invocation_ids"])
        self.assertIn("invocation identity missing; legacy artifacts remain unbound", row["errors"])
        self.assertIsNone(row["invocation_count"])
        self.assertIn("legacy artifact set cannot establish invocation count", row["errors"])

    def test_mixed_runner_state_and_raw_events_stop(self):
        self.assertEqual(classify(DATA["cases"][3], 1)["decision"],
                         "STOP_INVOCATION_PROVENANCE_OR_BOUNDARY")

    def test_duplicate_invocation_id_stops(self):
        case = next(c for c in DATA["cases"] if c["case_id"] == "duplicate_invocation_id")
        self.assertIn("invocation identity duplicated",
                      classify(case, 1)["errors"])

    def test_cross_invocation_path_stops(self):
        case = next(c for c in DATA["cases"] if c["case_id"] == "cross_invocation_artifact_path")
        self.assertIn("artifact path escapes invocation namespace: inv-005",
                      classify(case, 1)["errors"])

    def test_audit_after_nonzero_runner_stops(self):
        case = next(c for c in DATA["cases"] if c["case_id"] == "audit_after_runner_failure")
        self.assertIn("audit invoked without runner exit 0: inv-007",
                      classify(case, 1)["errors"])

    def test_two_uniquely_tagged_invocations_confirm_limit_exceeded(self):
        case = next(c for c in DATA["cases"] if c["case_id"] == "two_tagged_invocations_exceed_limit")
        row = classify(case, 1)
        self.assertEqual(row["invocation_count"], 2)
        self.assertIn("allocation invocation limit exceeded: 2>1", row["errors"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
