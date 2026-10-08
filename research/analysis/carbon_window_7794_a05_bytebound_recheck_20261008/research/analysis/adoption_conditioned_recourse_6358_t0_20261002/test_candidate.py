import unittest
from pathlib import Path

import candidate

HERE = Path(__file__).parent


class CohortSimulationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases, cls.digest = candidate.read_cases(HERE / "cases.json")
        cls.raw = candidate.simulate(cls.cases, cls.digest)
        cls.by_case = {row["case_id"]: row["policies"] for row in cls.raw["cases"]}

    def test_primary_public_stagger_vs_private_routing(self):
        p = self.by_case["shared-high-adoption"]
        self.assertEqual([p[k]["metrics"]["resolved_verified"] for k in ("generic_retry", "witness_only", "public_warning_stagger", "recipient_specific_routing", "wording_placebo")], [2, 2, 2, 4, 2])
        self.assertEqual(p["recipient_specific_routing"]["metrics"]["offered"], 4)
        rows = {row["id"]: row for row in p["recipient_specific_routing"]["offers"]}
        self.assertEqual(rows["h0"]["resource"], "disjoint")
        self.assertEqual(rows["h2"]["resource"], "disjoint")

    def test_wording_placebo_does_not_change_routes_or_outcomes(self):
        p = self.by_case["shared-high-adoption"]
        primary = {r["id"]: r for r in p["generic_retry"]["offers"]}
        placebo = {r["id"]: r for r in p["wording_placebo"]["offers"]}
        for offer_id in primary:
            self.assertEqual((primary[offer_id]["resource"], primary[offer_id]["outcome"]), (placebo[offer_id]["resource"], placebo[offer_id]["outcome"]))
            self.assertIn(placebo[offer_id]["advice_variant"], ("A", "B"))

    def test_class_disparity_and_all_offer_denominators_are_explicit(self):
        p = self.by_case["shared-high-adoption"]
        routed = p["recipient_specific_routing"]["metrics"]["recipient_classes"]
        self.assertEqual(routed["flexible"], {"offered": 2, "resolved": 2, "deadline_misses": 0})
        self.assertEqual(routed["shared_only"], {"offered": 2, "resolved": 2, "deadline_misses": 0})
        self.assertEqual(p["abandon_eligible_control"]["metrics"]["offered"], 4)
        self.assertEqual(p["abandon_eligible_control"]["metrics"]["eligible_suppressed"], 2)

    def test_advice_budget_is_equal_per_offered_stop_except_no_advice(self):
        for case in self.cases["cases"]:
            for policy, result in self.by_case[case["id"]].items():
                expected = 0 if policy == "no_advice" else len(case["offers"])
                self.assertEqual(result["metrics"]["advice_issued"], expected)

    def test_authorization_and_slow_alternative_counterexamples(self):
        forbidden = {r["id"]: r for r in self.by_case["forbidden-alternative"]["recipient_specific_routing"]["offers"]}
        self.assertEqual(forbidden["f0"]["resource"], "disjoint")
        self.assertTrue(all(forbidden[f"f{i}"]["resource"] == "shared" for i in (1, 2)))
        self.assertEqual(forbidden["f3"]["outcome"], "NO_FEASIBLE_RECOURSE")
        slow = self.by_case["slow-alternative"]["recipient_specific_routing"]["offers"]
        self.assertNotIn("slow", [r["resource"] for r in slow])

    def test_low_adoption_disjoint_null_no_route_and_holds(self):
        low = self.by_case["shared-low-adoption"]["recipient_specific_routing"]["metrics"]
        self.assertEqual((low["offered"], low["resolved_verified"]), (4, 2))
        disjoint = self.by_case["disjoint-resource-null"]["recipient_specific_routing"]["metrics"]
        self.assertEqual((disjoint["offered"], disjoint["resolved_verified"]), (4, 4))
        no_route = self.by_case["no-feasible-fallback"]["recipient_specific_routing"]["metrics"]
        self.assertEqual((no_route["offered"], no_route["resolved_verified"], no_route["no_feasible_recourse"]), (4, 1, 3))
        for case_id, outcome in (("expired-advice", "STALE_ADVICE"), ("uncertain-delivery", "UNKNOWN_NO_RETRY")):
            row = self.by_case[case_id]["recipient_specific_routing"]["offers"][0]
            self.assertEqual(row["outcome"], outcome)
            self.assertEqual(row["attempts"], [])

    def test_every_policy_keeps_every_offer_exactly_once(self):
        for case in self.cases["cases"]:
            expected = {offer["id"] for offer in case["offers"]}
            for result in self.by_case[case["id"]].values():
                got = [row["id"] for row in result["offers"]]
                self.assertEqual(len(got), len(set(got)))
                self.assertEqual(set(got), expected)


if __name__ == "__main__":
    unittest.main()
