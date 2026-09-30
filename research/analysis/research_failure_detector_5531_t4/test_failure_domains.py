import unittest

from audit import audit_results
from detector import decide


def witness(observer, domain_path, generation=7):
    return {
        "observer": observer,
        "domain_path": domain_path,
        "generation": generation,
        "kind": "independent_crash_witness",
    }


class HierarchicalFailureDomainTests(unittest.TestCase):
    def test_distinct_hosts_in_the_same_rack_are_not_independent(self):
        result = decide(
            [
                witness("worker-a", ["site-a", "rack-7", "host-a"]),
                witness("worker-b", ["site-a", "rack-7", "host-b"]),
            ],
            current_generation=7,
            independence_depth=1,
            required_domains=2,
        )

        self.assertEqual("SUSPECTED_UNAVAILABLE", result["state"])
        self.assertEqual(1, result["independent_domain_count"])

    def test_distinct_racks_in_one_site_remain_correlated_at_site_cut(self):
        result = decide(
            [
                witness("worker-a", ["site-a", "rack-7", "host-a"]),
                witness("worker-c", ["site-a", "rack-8", "host-c"]),
            ],
            current_generation=7,
            independence_depth=1,
            required_domains=2,
        )

        self.assertEqual("SUSPECTED_UNAVAILABLE", result["state"])
        self.assertEqual(1, result["independent_domain_count"])

    def test_distinct_sites_prove_failure_at_declared_site_cut(self):
        result = decide(
            [
                witness("worker-a", ["site-a", "rack-7", "host-a"]),
                witness("worker-c", ["site-b", "rack-8", "host-c"]),
            ],
            current_generation=7,
            independence_depth=1,
            required_domains=2,
        )

        self.assertEqual("FAILED", result["state"])
        self.assertEqual(2, result["independent_domain_count"])

    def test_stale_generation_does_not_supply_a_second_domain_witness(self):
        result = decide(
            [
                witness("worker-a", ["site-a", "rack-7", "host-a"], 7),
                witness("worker-c", ["site-b", "rack-8", "host-c"], 6),
            ],
            current_generation=7,
            independence_depth=1,
            required_domains=2,
        )

        self.assertEqual("SUSPECTED_UNAVAILABLE", result["state"])
        self.assertEqual(1, result["independent_domain_count"])

    def test_one_observer_cannot_claim_two_independent_failure_domains(self):
        result = decide(
            [
                witness("worker-a", ["site-a", "rack-7", "host-a"]),
                witness("worker-a", ["site-b", "rack-8", "host-a"]),
                witness("worker-c", ["site-a", "rack-9", "host-c"]),
            ],
            current_generation=7,
            independence_depth=1,
            required_domains=2,
        )

        self.assertEqual("SUSPECTED_UNAVAILABLE", result["state"])
        self.assertEqual(1, result["independent_domain_count"])
        self.assertEqual(1, result["valid_witness_count"])

    def test_independent_auditor_rejects_host_count_as_failure_domain_count(self):
        bad_candidate = {
            "case_id": "same_rack_same_site_distinct_hosts",
            "state": "FAILED",
            "independent_domain_count": 2,
        }

        errors = audit_results([bad_candidate])

        self.assertTrue(any("same_rack_same_site_distinct_hosts" in error for error in errors))
        self.assertTrue(any("state" in error for error in errors))

    def test_independent_auditor_accepts_the_literal_site_boundary(self):
        results = [
            {"case_id": "same_rack_same_site_distinct_hosts", "state": "SUSPECTED_UNAVAILABLE", "independent_domain_count": 1, "valid_witness_count": 2},
            {"case_id": "different_racks_same_site", "state": "SUSPECTED_UNAVAILABLE", "independent_domain_count": 1, "valid_witness_count": 2},
            {"case_id": "different_sites", "state": "FAILED", "independent_domain_count": 2, "valid_witness_count": 2},
            {"case_id": "stale_generation_second_site", "state": "SUSPECTED_UNAVAILABLE", "independent_domain_count": 1, "valid_witness_count": 1},
            {"case_id": "one_observer_two_site_claims", "state": "SUSPECTED_UNAVAILABLE", "independent_domain_count": 1, "valid_witness_count": 1},
        ]

        self.assertEqual([], audit_results(results))


if __name__ == "__main__":
    unittest.main()
