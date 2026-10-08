"""Frozen-corpus integration and raw corruption rejection tests."""

import copy
import json
import unittest

import audit
from corpus import build_cases
from run_host import run


class IndependentAuditTests(unittest.TestCase):
    def setUp(self):
        self.raw = run()
        self.corpus = json.dumps({"cases": build_cases()}, sort_keys=True).encode()
        # Audit's frozen corpus binding uses the exact persisted corpus bytes.
        self.corpus = (audit.ROOT / "cases.json").read_bytes()

    def test_frozen_eight_case_corpus_matches_independent_oracle(self):
        self.assertEqual(len(self.raw["rows"]), 8)
        self.assertEqual(audit.audit(self.raw, self.corpus), [])

    def test_tampered_decision_is_rejected(self):
        damaged = copy.deepcopy(self.raw)
        damaged["rows"][0]["decision"]["decisions"][0]["reason"] = "fake_pass"
        self.assertTrue(any(x.startswith("oracle_mismatch") for x in audit.audit(damaged, self.corpus)))

    def test_tampered_bound_input_is_rejected(self):
        damaged = copy.deepcopy(self.raw)
        damaged["rows"][0]["input"]["ir"]["checks"][0]["subject_ref"] = "other"
        self.assertTrue(any(x.startswith("input_binding") for x in audit.audit(damaged, self.corpus)))

    def test_extra_raw_field_is_rejected(self):
        damaged = copy.deepcopy(self.raw)
        damaged["rows"][0]["decision"]["decisions"][0]["unreviewed"] = True
        self.assertTrue(any(x.startswith("detail_schema") for x in audit.audit(damaged, self.corpus)))

    def test_cost_provenance_cannot_be_claimed_as_measurement(self):
        damaged = copy.deepcopy(self.raw)
        damaged["rows"][0]["decision"]["decisions"][0]["cost_provenance"] = "MEASURED"
        self.assertTrue(any(x.startswith("descriptor_binding") for x in audit.audit(damaged, self.corpus)))


if __name__ == "__main__":
    unittest.main()
