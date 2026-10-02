import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_eligibility import audit
import json


class T1EligibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs = json.loads((Path(__file__).resolve().parent / "eligibility_inputs.json").read_text(encoding="utf-8"))

    def test_cited_inventory_has_no_eligible_empirical_cohort(self):
        result = audit(self.inputs)
        self.assertEqual(result["status"], "HOLD_NO_ELIGIBLE_RETAINED_COHORT")
        self.assertEqual(result["candidate_count"], 6)
        self.assertEqual(result["eligible_count"], 0)

    def test_all_five_gates_required(self):
        row = {gate: True for gate in ("case_level_pre_post_evidence", "source_clock", "independent_cause_label", "eligible_safe_slack_failure", "diagnosis_or_reproducer_utility_outcome")}
        row["id"] = "synthetic_control"
        self.assertEqual(audit({"inventory": [row]})["status"], "ELIGIBLE_COHORT_FOUND")
        for gate in tuple(row):
            if gate == "id":
                continue
            mutant = copy.deepcopy(row)
            mutant[gate] = False
            result = audit({"inventory": [mutant]})
            self.assertEqual(result["eligible_count"], 0, gate)

    def test_duplicate_candidate_identity_fails_closed(self):
        mutant = copy.deepcopy(self.inputs)
        mutant["inventory"].append(copy.deepcopy(mutant["inventory"][0]))
        self.assertEqual(audit(mutant)["status"], "FAIL_AUDIT")


if __name__ == "__main__":
    unittest.main(verbosity=2)
