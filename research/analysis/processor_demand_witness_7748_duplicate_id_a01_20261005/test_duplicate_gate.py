import copy
import importlib.util
import json
import pathlib
import unittest

import audit
import candidate

ROOT = pathlib.Path(__file__).parent
CASES = json.loads((ROOT / "cases.json").read_text(encoding="utf-8"))["cases"]
PREDECESSOR_PATH = ROOT.parent / "processor_demand_witness_7748_t0_20261005" / "candidate.py"
SPEC = importlib.util.spec_from_file_location("predecessor_7748_candidate", PREDECESSOR_PATH)
PREDECESSOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PREDECESSOR)


class DuplicateJobIdentityTests(unittest.TestCase):
    def test_predecessor_misclassifies_duplicate_id_canary(self):
        distinct = copy.deepcopy(CASES[0])
        duplicate = copy.deepcopy(CASES[2])
        self.assertEqual(PREDECESSOR.classify({"jobs": distinct["jobs"]})["diagnosis"], "POLICY_MISS_ON_FEASIBLE_TRACE")
        self.assertEqual(PREDECESSOR.classify({"jobs": duplicate["jobs"]})["diagnosis"], "FEASIBLE_NO_POLICY_MISS")

    def test_duplicate_job_identity_holds_before_feasibility(self):
        case = copy.deepcopy(CASES[2])
        result = candidate.classify(case)
        self.assertEqual(result, {"status": "HOLD_DUPLICATE_JOB_ID"})

    def test_empty_and_non_string_job_ids_hold(self):
        for value in ("", None, 7):
            case = copy.deepcopy(CASES[0])
            case["jobs"][0]["id"] = value
            with self.subTest(job_id=value):
                self.assertEqual(candidate.classify(case), {"status": "HOLD_NO_SCHEDULABILITY_INPUTS"})

    def test_distinct_valid_job_ids_preserve_expected_results(self):
        self.assertEqual(candidate.classify(CASES[0])["status"], "ELIGIBLE")
        self.assertEqual(candidate.classify(CASES[1])["status"], "ELIGIBLE")

    def test_raw_auditor_reconstructs_duplicate_identity_hold(self):
        raw = candidate.run(CASES)
        result = audit.audit(raw, CASES)
        self.assertEqual(result["status"], "PASS_DUPLICATE_ID_BOUNDARY_SCOPED")
        self.assertEqual(raw["rows"][2]["result"], {"status": "HOLD_DUPLICATE_JOB_ID"})

    def test_raw_auditor_rejects_duplicate_id_marked_eligible(self):
        raw = candidate.run(CASES)
        raw["rows"][2]["result"] = {"status": "ELIGIBLE", "control_feasible": True, "all_feasible": True}
        self.assertEqual(audit.audit(raw, CASES)["status"], "FAIL_AUDIT")


if __name__ == "__main__":
    unittest.main()
