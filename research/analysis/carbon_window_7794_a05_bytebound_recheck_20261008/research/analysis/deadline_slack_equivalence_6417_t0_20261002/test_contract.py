import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).parent
spec = importlib.util.spec_from_file_location("deadline_candidate", ROOT / "candidate.py")
candidate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate)


class ContractTests(unittest.TestCase):
    def test_three_slack_equivalent_cases_keep_feasible_set_and_choice(self):
        rows = {row["case_id"]: row for row in candidate.run()["pairs"]}
        for case_id in ("equiv_browser_sheet", "equiv_document_lookup", "equiv_cross_app_cleanup"):
            self.assertTrue(rows[case_id]["equivalent"])
            self.assertEqual(rows[case_id]["long"]["feasible"], rows[case_id]["short"]["feasible"])
            self.assertEqual(rows[case_id]["long"]["choice"], rows[case_id]["short"]["choice"])

    def test_slack_sensitive_control_switches_and_impossible_case_yields(self):
        rows = {row["case_id"]: row for row in candidate.run()["pairs"]}
        self.assertEqual(rows["sensitive_deadline_switch"]["long"]["choice"], "full_audit")
        self.assertEqual(rows["sensitive_deadline_switch"]["short"]["choice"], "bounded_check")
        self.assertEqual(rows["impossible_verification"]["short"]["choice"], "YIELD")

    def test_all_claimed_equivalent_mutations_are_rejected(self):
        rows = candidate.run()["invalid_claimed_equivalent"]
        self.assertEqual(len(rows), 3)
        self.assertTrue(all(row["result"]["equivalent"] is False for row in rows))
        self.assertTrue(all(row["result"]["reasons"] for row in rows))


if __name__ == "__main__":
    unittest.main()
