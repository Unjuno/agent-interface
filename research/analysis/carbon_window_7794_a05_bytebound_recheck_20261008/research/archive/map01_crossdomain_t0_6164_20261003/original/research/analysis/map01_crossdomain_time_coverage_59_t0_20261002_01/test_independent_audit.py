import unittest

from independent_audit import candidate_claims_hold


class IndependentAuditGateTests(unittest.TestCase):
    def test_accepts_candidate_that_keeps_domain_and_cross_domain_unknown(self):
        candidate = {
            "status": "HOLD_CROSSDOMAIN_TIME_COVERAGE_UNIDENTIFIED",
            "cross_domain_time_coverage_identified": False,
            "domains": [{"time_coverage_identified": False},
                        {"time_coverage_identified": False}],
        }
        self.assertTrue(candidate_claims_hold(candidate))

    def test_rejects_candidate_that_promotes_one_domain_interval_to_transfer(self):
        candidate = {
            "status": "HOLD_CROSSDOMAIN_TIME_COVERAGE_UNIDENTIFIED",
            "cross_domain_time_coverage_identified": False,
            "domains": [{"time_coverage_identified": True},
                        {"time_coverage_identified": False}],
        }
        self.assertFalse(candidate_claims_hold(candidate))

    def test_rejects_candidate_that_calls_transfer_pass_without_denominator(self):
        candidate = {
            "status": "PASS_CROSSDOMAIN_TIME_COVERAGE_SCOPED",
            "cross_domain_time_coverage_identified": True,
            "domains": [{"time_coverage_identified": True},
                        {"time_coverage_identified": True}],
        }
        self.assertFalse(candidate_claims_hold(candidate))


if __name__ == "__main__":
    unittest.main()
