from pathlib import Path
import sys
import unittest


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from map01_running_action_paths_v35 import run


class Map01RunningActionPathsV35Tests(unittest.TestCase):
    def test_all_program_binding_and_current_authority_paths(self):
        result = run()
        self.assertTrue(result["passed"])
        self.assertEqual(result["case_count"], 5)
        self.assertEqual(result["program_bindings"], 7)
        self.assertEqual(result["executor_attestations"], 7)
        self.assertEqual(result["current_authority_true_at_terminal"], 0)
        self.assertEqual([row["state"] for row in result["cases"]],
            ["COMPLETED", "COMPLETED", "COMPLETED",
             "REVOKED_ACTION_NOT_CURRENT", "REJECTED_BEFORE_PROGRAM_ADMISSION"])


if __name__ == "__main__": unittest.main()
