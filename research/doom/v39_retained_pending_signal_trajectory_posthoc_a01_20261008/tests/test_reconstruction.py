"""Pure offline regression tests for the retained trajectory package."""
import json
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import analyze
import audit


class RetainedTrajectoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs = analyze.load_inputs()
        cls.result = analyze.derive(cls.inputs)

    def test_frozen_inputs_are_exact_and_event_copies_match(self):
        for name, data in self.inputs.items():
            self.assertEqual(len(data), analyze.FREEZE["inputs"][name]["bytes"])
            self.assertTrue(analyze.verify_bytes(name, data))
        self.assertEqual(self.inputs["events"], self.inputs["delivered"])

    def test_mutated_input_is_rejected(self):
        data = self.inputs["events"]
        mutated = data[:-1] + (b" " if data[-1:] != b" " else b"\t")
        with self.assertRaises(analyze.EvidenceError):
            analyze.verify_bytes("events", mutated)

    def test_six_window_transitions_match_frozen_expectation(self):
        expected = analyze.FREEZE["expected"]["windows"]
        actual = self.result["windows"]
        self.assertEqual(len(actual), 6)
        for row, frozen in zip(actual, expected):
            self.assertEqual(row["decision"], frozen["decision"])
            self.assertEqual(row["source_sequence"], frozen["source_sequence"])
            self.assertEqual(row["source_health"], frozen["source_health"])
            self.assertEqual(row["source_ammo"], frozen["source_ammo"])
            self.assertEqual(row["end_sequence"], frozen["end_sequence"])
            self.assertEqual(row["health_ammo_changes"], frozen["changes"])

    def test_strict_health_floor_boundary_matches_retained_event(self):
        rows = self.result["active_cover_guard_windows"]
        self.assertEqual([row["decision"] for row in rows], [1, 4, 5])
        by_decision = {row["decision"]: row for row in rows}
        self.assertEqual(by_decision[1]["equal_sequences"], list(range(62, 71)))
        self.assertEqual(by_decision[1]["below_sequences"], [])
        self.assertEqual(by_decision[4]["hard_minimum"], 55)
        self.assertEqual(by_decision[4]["source_health"], 65)
        self.assertEqual(by_decision[4]["below_sequences"], [])
        self.assertEqual(by_decision[5]["equal_sequences"], list(range(200, 218)))
        self.assertEqual(by_decision[5]["below_sequences"], [218])
        self.assertEqual(by_decision[5]["reported_invalidation_sequence"], 218)

    def test_independent_audit_passes_and_rejects_changed_result(self):
        self.assertEqual(audit.audit_result(self.result)["status"],
                         "PASS_INDEPENDENT_RAW_RECONSTRUCTION")
        changed = json.loads(json.dumps(self.result))
        changed["windows"][4]["health_ammo_changes"][-1][1] = 62
        with self.assertRaises(audit.AuditError):
            audit.audit_result(changed)

    def test_score_is_alive_but_unfinished(self):
        self.assertEqual(self.result["episode_disposition"]["kills"], 1)
        self.assertEqual(self.result["episode_disposition"]["deaths"], 0)
        self.assertFalse(self.result["episode_disposition"]["map_exit"])
        self.assertFalse(self.result["episode_disposition"]["episode_finished"])


if __name__ == "__main__":
    unittest.main()