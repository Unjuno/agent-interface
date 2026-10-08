import copy
import json
import unittest

from audit_t0 import audit
from run_t0 import run


class OracleBracketTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open("spec.json", encoding="utf-8") as f:
            cls.spec = json.load(f)
        cls.raw = run(cls.spec)

    def test_nominal_equivalent_version_pass_and_in_deck_drift_holds(self):
        result = audit(self.spec, self.raw)
        self.assertEqual(result["status"], "PASS_METHOD_SCOPED")
        self.assertEqual(result["false_promotions_blocked"], 1)
        self.assertEqual(result["equivalent_version_rejected"], 0)

    def test_out_of_deck_drift_is_unknown_coverage(self):
        result = audit(self.spec, self.raw)
        self.assertEqual(result["out_of_deck_disposition"], "UNKNOWN_COVERAGE")

    def test_omitted_postcheck_is_rejected(self):
        bad = copy.deepcopy(self.raw)
        bad["scenarios"]["in_deck_semantic_drift"]["postcheck"] = None
        self.assertTrue(audit(self.spec, bad)["errors"])

    def test_swapped_reference_labels_are_rejected(self):
        bad = copy.deepcopy(self.spec)
        bad["check_deck"][0]["expected"] = not bad["check_deck"][0]["expected"]
        self.assertTrue(audit(bad, self.raw)["errors"])

    def test_unknown_reclassified_as_pass_is_rejected(self):
        bad = copy.deepcopy(self.raw)
        bad["scenarios"]["out_of_deck_drift"]["promotion"] = "PASS"
        self.assertTrue(audit(self.spec, bad)["errors"])

    def test_backfilled_reference_is_rejected(self):
        bad = copy.deepcopy(self.raw)
        bad["reference_timestamp"] = "after-candidate"
        self.assertTrue(audit(self.spec, bad)["errors"])


if __name__ == "__main__":
    unittest.main()
