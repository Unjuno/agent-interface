import copy
import importlib.util
import json
from pathlib import Path
import unittest

import candidate

HERE = Path(__file__).parent
spec = importlib.util.spec_from_file_location("independent_auditor", HERE / "auditor.py")
auditor = importlib.util.module_from_spec(spec) if spec and (HERE / "auditor.py").is_file() else None
if auditor is not None and spec and spec.loader:
    spec.loader.exec_module(auditor)


class IndependentCardAuditTests(unittest.TestCase):
    def setUp(self):
        self.specification = {"families": [{"id": "F1", "operation": "save", "target": "D1", "status": "pending", "evidence": "not sent"}]}
        self.cards = candidate.build_cards(self.specification)

    def test_independent_oracle_accepts_complete_fixture(self):
        self.assertIsNotNone(auditor, "independent auditor has not been implemented")
        self.assertEqual(auditor.audit(self.specification, self.cards), [])

    def test_rejects_authority_or_fact_mutation(self):
        self.assertIsNotNone(auditor, "independent auditor has not been implemented")
        for field, value in (("authority_boundary", "Selection authorizes dispatch."), ("target", "D2"), ("operation_status", "completed")):
            altered = copy.deepcopy(self.cards)
            altered[0][field] = value
            self.assertTrue(auditor.audit(self.specification, altered), field)

    def test_rejects_missing_stop_duplicate_options_and_bad_key(self):
        self.assertIsNotNone(auditor, "independent auditor has not been implemented")
        altered = copy.deepcopy(self.cards)
        altered[0]["options"] = altered[0]["options"][1:]
        self.assertTrue(auditor.audit(self.specification, altered))
        altered = copy.deepcopy(self.cards)
        altered[0]["options"][1]["id"] = "stop"
        self.assertTrue(auditor.audit(self.specification, altered))
        altered = copy.deepcopy(self.cards)
        altered[0]["comprehension_key"][3]["answer"] = "Yes"
        self.assertTrue(auditor.audit(self.specification, altered))

    def test_rejects_card_denominator_or_duplicate_identity(self):
        self.assertIsNotNone(auditor, "independent auditor has not been implemented")
        self.assertTrue(auditor.audit(self.specification, self.cards[:-1]))
        altered = copy.deepcopy(self.cards)
        altered[1]["condition"] = altered[0]["condition"]
        self.assertTrue(auditor.audit(self.specification, altered))


if __name__ == "__main__":
    unittest.main()
