import json
import unittest
from pathlib import Path

from guard_replay import compute

ROOT = Path(__file__).resolve().parents[1]


class RetainedGuardReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = compute()
        cls.by_decision = {row["decision"]: row for row in cls.result["decisions"]}

    def test_floor_equality_preserves_policy(self):
        decision1 = self.by_decision[1]
        self.assertIn(62, decision1["floor_equal_sequences"])
        self.assertEqual(decision1["hard_events"], [])
        decision5 = self.by_decision[5]
        self.assertIn(200, decision5["floor_equal_sequences"])
        self.assertIn(212, decision5["floor_equal_sequences"])

    def test_only_below_floor_is_hard_in_retained_authored_windows(self):
        all_hard = [event for row in self.result["decisions"] for event in row["hard_events"]]
        self.assertEqual(all_hard, [{
            "sequence": 218,
            "health": 48,
            "reason": "below_hard_minimum",
            "grants_input_authority": False,
        }])
        self.assertEqual(self.result["recorded_policy_invalidations"], 1)

    def test_result_is_posthoc_and_source_bound(self):
        self.assertEqual(self.result["classification"], "POSTHOC_REPLAY_NOT_NEW_LIVE_ALLOCATION")
        self.assertEqual(self.result["current_main_commit"], "6ea1269defb6d48a607f13b08f1aa2d223ba06e9")
        retained = json.loads((ROOT / "GUARD_REPLAY.json").read_text(encoding="utf-8"))
        self.assertEqual(self.result, retained)


if __name__ == "__main__":
    unittest.main()
