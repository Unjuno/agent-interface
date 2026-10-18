import copy
import json
import unittest

import auditor
import candidate


class ConstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open("candidate_inputs.json", encoding="utf-8") as f:
            cls.source = json.load(f)
        with open("oracle.json", encoding="utf-8") as f:
            cls.expected = json.load(f)
        cls.raw = candidate.run(cls.source)

    def test_frozen_expected_rows(self):
        result = auditor.audit(self.source, self.raw, self.expected)
        self.assertEqual(result["status"], "PASS_METHOD_SCOPED")
        self.assertEqual(result["rows"], 10)
        self.assertTrue(result["late_sliding_false_acceptance"])

    def test_all_six_mutations_are_effective(self):
        result = auditor.audit(self.source, self.raw, self.expected)
        self.assertEqual(set(result["mutations_rejected"]),
                         {"now", "source_expiry", "source_epoch", "query", "scope", "kind"})
        self.assertTrue(all(result["mutations_rejected"].values()))

    def test_time_boundary_is_exclusive(self):
        by_id = {r["case_id"]: r for r in self.raw["rows"]}
        self.assertEqual(by_id["C07"]["absolute"], "EXPIRED")
        self.assertEqual(by_id["C07"]["sliding"], "NO_MATCH")

    def test_timeout_never_becomes_negative(self):
        by_id = {r["case_id"]: r for r in self.raw["rows"]}
        self.assertEqual(by_id["C08"]["absolute"], "TIMEOUT")
        self.assertEqual(by_id["C08"]["sliding"], "TIMEOUT")

    def test_each_handoff_is_retained(self):
        by_id = {r["case_id"]: r for r in self.raw["rows"]}
        self.assertEqual([r["decision"] for r in by_id["C02"]["absolute_trace"]],
                         ["NO_MATCH", "EXPIRED"])
        self.assertEqual([r["decision"] for r in by_id["C02"]["sliding_trace"]],
                         ["NO_MATCH", "NO_MATCH"])
        self.assertEqual(len(by_id["C01"]["absolute_trace"]), 2)

    def test_raw_mutation_is_not_silently_accepted(self):
        damaged = copy.deepcopy(self.raw)
        damaged["rows"][1]["absolute"] = "NO_MATCH"
        result = auditor.audit(self.source, damaged, self.expected)
        self.assertIn("raw_reconstruction", result["errors"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
