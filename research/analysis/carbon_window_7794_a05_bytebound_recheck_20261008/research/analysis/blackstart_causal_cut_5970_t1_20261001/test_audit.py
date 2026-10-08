import json
import unittest
from pathlib import Path

from candidate import inspect

HERE = Path(__file__).resolve().parent


class TraceApplicabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
        import subprocess
        cls.root = Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip())
        cls.result = inspect(cls.root, cls.freeze["source_commit"], cls.freeze)

    def test_archive_and_formal_inventory_are_complete(self):
        self.assertTrue(self.result["frozen_inventory_ok"])
        self.assertEqual(324, self.result["expanded_file_count"])
        self.assertEqual(24, self.result["formal_case_count"])
        self.assertEqual(4, self.result["selected_positive_case_count"])

    def test_selected_raw_streams_match_aggregated_case_records(self):
        self.assertTrue(self.result["raw_aggregates_match"])

    def test_bootstrap_is_epoch_bound_to_observer_stream(self):
        self.assertTrue(self.result["bootstrap_epochs_match"])
        self.assertTrue(all(r["observer_event_epochs_match"] for r in self.result["selected_rows"]))

    def test_source_hashes_match_published_v2_freeze(self):
        self.assertTrue(self.result["frozen_source_hashes_match"])

    def test_relevant_state_exists_but_explicit_edges_are_absent(self):
        self.assertTrue(all(r["final_value"] == "b" and r["final_neutral"] for r in self.result["selected_rows"]))
        self.assertEqual(0, self.result["explicit_cross_source_edge_rows"])
        self.assertEqual("HOLD_CAUSAL_EDGE_PROVENANCE_MISSING", self.result["disposition"])

    def test_both_streams_have_monotonic_time_but_not_causal_ids(self):
        self.assertTrue(all(r["monotonic_timestamps_both_streams"] for r in self.result["selected_rows"]))
        self.assertTrue(all(not r["explicit_causal_edge_fields"] for r in self.result["selected_rows"]))


if __name__ == "__main__":
    unittest.main()
