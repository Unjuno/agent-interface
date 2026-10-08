import copy
import unittest
from pathlib import Path

import auditor
import candidate

HERE = Path(__file__).parent


class IndependentAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases, cls.digest = candidate.read_cases(HERE / "cases.json")
        cls.raw = candidate.simulate(cls.cases, cls.digest)

    def test_accepts_frozen_policy_contrast(self):
        report = auditor.audit(self.cases, self.digest, self.raw)
        self.assertEqual(report["status"], "PASS_METHOD_SCOPED")
        self.assertEqual(report["errors"], [])

    def assert_corruption_fails(self, mutate):
        altered = copy.deepcopy(self.raw)
        mutate(altered)
        report = auditor.audit(self.cases, self.digest, altered)
        self.assertEqual(report["status"], "FAIL_RAW_AUDIT")
        self.assertTrue(report["errors"])

    def test_rejects_dropped_offer(self):
        self.assert_corruption_fails(lambda raw: raw["cases"][0]["policies"]["recipient_specific_routing"]["offers"].pop())

    def test_rejects_forbidden_route(self):
        def mutate(raw):
            row = raw["cases"][4]["policies"]["recipient_specific_routing"]["offers"][1]
            row["resource"] = "disjoint"
        self.assert_corruption_fails(mutate)

    def test_rejects_placebo_that_changes_actual_outcomes(self):
        def mutate(raw):
            row = raw["cases"][0]["policies"]["wording_placebo"]["offers"][0]
            row["outcome"] = "DEADLINE_MISS"
            row["resolved"] = False
        self.assert_corruption_fails(mutate)

    def test_rejects_over_capacity_overlap(self):
        def mutate(raw):
            rows = raw["cases"][0]["policies"]["generic_retry"]["offers"]
            rows[1]["attempts"][0]["start_tick"] = 0
            rows[1]["attempts"][0]["end_tick"] = 1
            rows[1]["attempts"][1]["start_tick"] = 1
            rows[1]["attempts"][1]["end_tick"] = 2
        self.assert_corruption_fails(mutate)

    def test_rejects_expired_offer_execution(self):
        def mutate(raw):
            row = raw["cases"][6]["policies"]["recipient_specific_routing"]["offers"][0]
            row["outcome"] = "RESOLVED_VERIFIED"
            row["resolved"] = True
            row["resource"] = "shared"
            row["attempts"] = [{"number": 1, "start_tick": 2, "end_tick": 3, "receipt": "NOT_APPLIED_VERIFIED", "idempotency_key": "idem:e0"}, {"number": 2, "start_tick": 3, "end_tick": 4, "receipt": "APPLIED_VERIFIED", "idempotency_key": "idem:e0"}]
        self.assert_corruption_fails(mutate)

    def test_rejects_retry_after_uncertain_effect(self):
        def mutate(raw):
            row = raw["cases"][7]["policies"]["recipient_specific_routing"]["offers"][0]
            row["outcome"] = "RESOLVED_VERIFIED"
            row["resolved"] = True
            row["resource"] = "shared"
            row["attempts"] = [{"number": 1, "start_tick": 0, "end_tick": 1, "receipt": "NOT_APPLIED_VERIFIED", "idempotency_key": "idem:u0"}, {"number": 2, "start_tick": 1, "end_tick": 2, "receipt": "APPLIED_VERIFIED", "idempotency_key": "idem:u0"}]
        self.assert_corruption_fails(mutate)

    def test_rejects_censored_denominator(self):
        def mutate(raw):
            p = raw["cases"][0]["policies"]["abandon_eligible_control"]
            p["offers"].pop()
        self.assert_corruption_fails(mutate)

    def test_rejects_changed_fixture_digest(self):
        altered = copy.deepcopy(self.raw)
        altered["cases_sha256"] = "0" * 64
        report = auditor.audit(self.cases, self.digest, altered)
        self.assertEqual(report["status"], "FAIL_RAW_AUDIT")
        self.assertTrue(report["errors"])


if __name__ == "__main__":
    unittest.main()
