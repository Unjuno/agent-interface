import copy
import unittest

import auditor
import candidate
from generate_fixture import generate


class ProtocolTests(unittest.TestCase):
    def setUp(self):
        self.public, self.oracle = generate()
        self.oracle_sha256 = auditor.oracle_digest(self.oracle)
        self.output = candidate.evaluate(self.public)

    def test_public_oracle_separation(self):
        self.assertTrue(all("y" not in r and "oracle_y" not in r for r in self.public["rows"]))
        self.assertTrue(all("label" not in r for r in self.oracle["rows"]))

    def test_raw_audit_reconstructs_fixture(self):
        self.assertTrue(auditor.audit(self.public, self.oracle, self.output, self.oracle_sha256)["ok"])

    def test_unobserved_truth_mutation_is_detected(self):
        bad = copy.deepcopy(self.oracle)
        idx = next(i for i, row in enumerate(self.public["rows"]) if not row["observed"])
        bad["rows"][idx]["y"] ^= 1
        result = auditor.audit(self.public, bad, self.output, self.oracle_sha256)
        self.assertIn("oracle_hash_mismatch", result["errors"])

    def test_public_propensity_mutation_is_detected(self):
        bad = copy.deepcopy(self.public)
        bad["rows"][0]["pi"] = 0.9
        result = auditor.audit(bad, self.oracle, self.output, self.oracle_sha256)
        self.assertIn("stratum_or_propensity_mismatch", result["errors"])

    def test_dropped_assignment_is_detected(self):
        bad = copy.deepcopy(self.public)
        bad["rows"].pop()
        self.assertIn("assignment_denominator_mismatch", auditor.audit(bad, self.oracle, self.output, self.oracle_sha256)["errors"])

    def test_mutated_candidate_estimate_is_detected(self):
        bad = copy.deepcopy(self.output)
        bad["cohort_ht"][0] += 0.1
        self.assertFalse(auditor.audit(self.public, self.oracle, bad, self.oracle_sha256)["ok"])

    def test_zero_support_returns_unknown(self):
        bad = copy.deepcopy(self.public)
        for row in bad["rows"]:
            if row["x"] == 0:
                row["pi"] = 0.0
        self.assertEqual(candidate.evaluate(bad)["status"], "UNKNOWN")

    def test_propensity_above_one_returns_unknown(self):
        bad = copy.deepcopy(self.public)
        for row in bad["rows"]:
            if row["x"] == 1:
                row["pi"] = 1.1
        self.assertEqual(candidate.evaluate(bad)["status"], "UNKNOWN")

    def test_missing_assumption_contract_returns_unknown(self):
        bad = copy.deepcopy(self.public)
        bad["contract"]["conditional_independence"] = False
        self.assertEqual(candidate.evaluate(bad)["status"], "UNKNOWN")

    def test_observationally_equivalent_worlds_share_only_conditional_output(self):
        world_a = copy.deepcopy(self.oracle)
        world_b = copy.deepcopy(self.oracle)
        hidden_index = next(i for i, row in enumerate(self.public["rows"]) if not row["observed"])
        world_a["rows"][hidden_index]["y"] = 0
        world_b["rows"][hidden_index]["y"] = 1
        self.assertNotEqual(world_a, world_b)
        self.assertEqual(candidate.evaluate(self.public), candidate.evaluate(self.public))
        self.assertEqual(self.output["status"], "ASSUMPTION_CONDITIONAL")

    def test_hidden_label_leak_returns_unknown(self):
        bad = copy.deepcopy(self.public)
        row = next(r for r in bad["rows"] if not r["observed"])
        row["label"] = 1
        self.assertEqual(candidate.evaluate(bad)["status"], "UNKNOWN")


if __name__ == "__main__":
    unittest.main(verbosity=2)
