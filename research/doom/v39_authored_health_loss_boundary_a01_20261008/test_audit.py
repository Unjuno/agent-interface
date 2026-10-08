import copy
import json
import unittest
from pathlib import Path

from .audit import validate


class AuthoredHealthBoundaryAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = json.loads((Path(__file__).parent / "RESULT.json").read_text(encoding="utf-8"))

    def test_candidate_result_matches_independent_full_sweep(self):
        self.assertTrue(validate(self.result))
        self.assertEqual(self.result["rows"][12]["triage_value_84"]["status"], "HARD_INVALIDATED")
        self.assertEqual(self.result["rows"][16]["triage_value_84"]["status"], "SOFT_CHANGED")
        self.assertEqual(self.result["rows"][20]["triage_value_84"]["status"], "SOFT_CHANGED")

    def test_mutated_result_claims_are_rejected(self):
        mutations = [
            lambda r: r.update(main_commit="0" * 40),
            lambda r: r["rows"][12].update(hard_minimum=80),
            lambda r: r["rows"][16]["triage_value_84"].update(status="HARD_INVALIDATED"),
            lambda r: r["rows"][16]["exact_floor"].update(requires_new_decision=True),
            lambda r: r["rows"].append(copy.deepcopy(r["rows"][-1])),
        ]
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                altered = copy.deepcopy(self.result)
                mutate(altered)
                with self.assertRaises(ValueError):
                    validate(altered)


if __name__ == "__main__":
    unittest.main(verbosity=2)
