from pathlib import Path
import sys
import unittest


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from v31_running_action_guard_replay_v1 import run


class V31RunningActionGuardReplayTests(unittest.TestCase):
    def test_retained_primary_frames_and_breach_controls(self):
        result = run()
        self.assertTrue(result["passed"])
        self.assertEqual(result["historical_program_count"], 5)
        self.assertEqual(result["historical_exact_running_frames"], 22)
        self.assertEqual(result["historical_invalidations"], 0)
        self.assertEqual([row["invalidation_reason"] for row in result["injected_controls"]],
                         ["health_max_decrease_from_source_failed", "ammo_minimum_failed"])


if __name__ == "__main__":
    unittest.main()
