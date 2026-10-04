import sys
from pathlib import Path
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parent))
from final_action_admission_paths_v1 import run


class FinalActionAdmissionPathReplayTests(unittest.TestCase):
    def test_all_branch_cardinality(self):
        result = run()
        self.assertTrue(result["passed"])
        self.assertEqual(result["total_cases"], 6)
        by_name = {row["case"]: row for row in result["cases"]}
        self.assertEqual(by_name["policy_before_admission"][
            "historical_executor_acceptances"], 0)
        self.assertEqual(by_name["active_first_acceptance"][
            "historical_executor_acceptances"], 1)
        self.assertTrue(by_name["active_first_acceptance"]["current_input_authority"])
        self.assertEqual(by_name["active_then_revoked"][
            "historical_executor_acceptances"], 1)
        self.assertFalse(by_name["active_then_revoked"]["current_input_authority"])


if __name__ == "__main__":
    unittest.main()
