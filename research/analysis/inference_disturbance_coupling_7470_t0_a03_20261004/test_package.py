import importlib.util
import itertools
import json
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = json.loads((HERE / "spec.json").read_text())
spec = importlib.util.spec_from_file_location("phase_candidate", HERE / "candidate.py")
candidate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate)


class CircularPhaseTests(unittest.TestCase):
    def test_all_and_only_unique_circular_shifts(self):
        rows = candidate.run(SPEC)["shifts"]
        expected = [SPEC["latency_period"][i:] + SPEC["latency_period"][:i] for i in range(4)]
        self.assertEqual([row["latency_sequence"] for row in rows], expected)
        self.assertEqual(len({tuple(row["latency_sequence"]) for row in rows}), 4)

    def test_each_stream_multiset_and_total_are_fixed(self):
        rows = candidate.run(SPEC)["shifts"]
        for row in rows:
            self.assertEqual(sorted(row["latency_sequence"]), sorted(SPEC["latency_period"]))
            self.assertEqual(row["interaction"]["disturbances"], SPEC["disturbance_period"])
            self.assertEqual(row["interaction"]["termination_release_tick"], 10)

    def test_null_is_phase_invariant_and_interaction_is_not(self):
        rows = candidate.run(SPEC)["shifts"]
        self.assertEqual(len({tuple(row["null"]["state_trace"]) for row in rows}), 1)
        self.assertGreater(len({row["interaction"]["peak_state"] for row in rows}), 1)

    def test_harness_gate_fixture(self):
        rows = candidate.run(SPEC)["shifts"]
        self.assertEqual(len(rows), 4)
        self.assertEqual(len(list(itertools.permutations(SPEC["latency_period"]))), 24)


if __name__ == "__main__":
    unittest.main()
