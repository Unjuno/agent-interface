from pathlib import Path
import sys
import unittest


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from map01_action_admission_paths_v33 import run


class Map01ActionAdmissionPathsV33Tests(unittest.TestCase):
    def test_all_paths_preserve_receipt_acceptance_cardinality(self):
        result = run()
        self.assertTrue(result["passed"])
        self.assertEqual(result["total_cases"], 8)
        self.assertEqual(result["zero_primary_admission_cases"], 6)
        self.assertEqual(sum(row["historical_executor_acceptances"]
                             for row in result["cases"]), 2)


if __name__ == "__main__":
    unittest.main()
