import copy
import json
import unittest

from .audit_result_v2 import validate
from .run_audit import FREEZE, load_inputs


class FullResultAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.events, cls.owner, cls.report, cls.prior = load_inputs()
        cls.result = json.loads((__import__("pathlib").Path(__file__).parent /
                                 "RESULT.json").read_text(encoding="utf-8"))

    def test_frozen_result_passes_full_reconstruction(self):
        self.assertTrue(validate(self.result, self.events, self.owner, self.report,
                                 self.prior, FREEZE))

    def test_previously_unchecked_claim_mutations_are_rejected(self):
        mutations = {
            "main_commit": "0" * 40,
            "allocation_id": "different-allocation",
            "prior_audit_formal_pass": False,
            "all_cancellation_rows": [],
            "per_key_release_measurement_events": 99,
            "independent_useful_feedback_timestamp": True,
            "decision": "fabricated conclusion",
        }
        for key, value in mutations.items():
            with self.subTest(field=key):
                altered = copy.deepcopy(self.result)
                altered[key] = value
                with self.assertRaisesRegex(ValueError, "differs from canonical"):
                    validate(altered, self.events, self.owner, self.report,
                             self.prior, FREEZE)

    def test_unknown_result_field_is_rejected(self):
        altered = copy.deepcopy(self.result)
        altered["invented_claim"] = True
        with self.assertRaisesRegex(ValueError, "invented_claim"):
            validate(altered, self.events, self.owner, self.report, self.prior, FREEZE)


if __name__ == "__main__":
    unittest.main(verbosity=2)
