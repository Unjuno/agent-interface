from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load(name):
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


candidate = load("candidate")


class FixedMarginalCouplingTests(unittest.TestCase):
    def setUp(self):
        self.spec = json.loads((HERE / "spec.json").read_text())

    def test_exhaustive_pairing_space_and_fixed_marginals(self):
        self.assertEqual(len(tuple(__import__("itertools").permutations(self.spec["latencies"]))), 24)
        self.assertEqual(sorted(self.spec["latencies"]), [1, 2, 3, 4])
        self.assertEqual(sorted(self.spec["disturbances"]), [0, 1, 2, 3])
        self.assertEqual(sum(self.spec["latencies"]), 10)

    def test_null_plant_outcomes_are_pairing_invariant(self):
        null = candidate.trajectory((4, 3, 2, 1), (0, 1, 2, 3), self.spec["null_gain"], self.spec)
        self.assertEqual(null["state_trace"], [0.0, 0.0, 1.0, 3.0])
        self.assertEqual(null["outside_envelope_event_ticks"], 0)

    def test_planted_aligned_pairing_exceeds_reversed(self):
        aligned = candidate.trajectory((1, 2, 3, 4), (0, 1, 2, 3), self.spec["interaction_gain"], self.spec)
        reversed_row = candidate.trajectory((4, 3, 2, 1), (0, 1, 2, 3), self.spec["interaction_gain"], self.spec)
        self.assertEqual(aligned["peak_state"], 8.0)
        self.assertEqual(reversed_row["peak_state"], 5.5)
        self.assertEqual(aligned["stale_severity_exposure"], 20)
        self.assertEqual(reversed_row["stale_severity_exposure"], 10)
        self.assertEqual(aligned["events"][1]["useful_fresh_action_at_tick"], 3)
        self.assertEqual(reversed_row["events"][1]["useful_fresh_action_at_tick"], 7)

    def test_auditor_is_a_separate_raw_only_entrypoint(self):
        auditor_source = (HERE / "audit.py").read_text()
        self.assertNotIn("import candidate", auditor_source)
        self.assertIn('RAW = HERE / "results" / "candidate.json"', auditor_source)

    def test_formal_output_is_absent_before_launch(self):
        self.assertFalse((HERE / "results").exists())


if __name__ == "__main__":
    unittest.main()
