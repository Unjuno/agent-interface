import unittest


try:
    from candidate import evaluate
except ModuleNotFoundError:
    evaluate = None


def case(case_id, model_after_ms):
    return {
        "id": case_id,
        "selector": "min_cost",
        "routes": [
            {"id": "model", "baseline_ms": 130, "intervention_ms": model_after_ms},
            {"id": "alternate", "baseline_ms": 260, "intervention_ms": 260},
        ],
    }


class CandidateContractTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(evaluate, "candidate.evaluate must exist")

    def test_halved_model_cost_keeps_route_and_allows_minus_50ms_delta(self):
        result = evaluate(case("half_model", 80))
        self.assertEqual(result["status"], "ROUTE_STABLE")
        self.assertEqual(result["baseline_optima"], ["model"])
        self.assertEqual(result["intervention_optima"], ["model"])
        self.assertEqual(result["endpoint_delta_ms"], -50)

    def test_plus_80ms_keeps_model_route_and_allows_80ms_delta(self):
        result = evaluate(case("plus_80", 210))
        self.assertEqual(result["status"], "ROUTE_STABLE")
        self.assertEqual(result["baseline_optima"], ["model"])
        self.assertEqual(result["intervention_optima"], ["model"])
        self.assertEqual(result["endpoint_delta_ms"], 80)

    def test_cost_280ms_changes_optimum_and_withholds_numeric_delta(self):
        result = evaluate(case("route_switch", 280))
        self.assertEqual(result["status"], "NONSTATIONARY_INTERVENTION")
        self.assertEqual(result["baseline_optima"], ["model"])
        self.assertEqual(result["intervention_optima"], ["alternate"])
        self.assertIsNone(result["endpoint_delta_ms"])

    def test_exact_post_intervention_tie_is_reported_as_set(self):
        result = evaluate(case("exact_tie", 260))
        self.assertEqual(result["status"], "TIE_SET")
        self.assertEqual(result["baseline_optima"], ["model"])
        self.assertEqual(result["intervention_optima"], ["alternate", "model"])
        self.assertIsNone(result["endpoint_delta_ms"])

    def test_explicit_max_cost_selector_is_not_silently_treated_as_min_cost(self):
        fixture = case("max_cost_control", 120)
        fixture["selector"] = "max_cost"
        result = evaluate(fixture)
        self.assertEqual(result["status"], "ROUTE_STABLE")
        self.assertEqual(result["baseline_optima"], ["alternate"])
        self.assertEqual(result["intervention_optima"], ["alternate"])
        self.assertEqual(result["endpoint_delta_ms"], 0)

    def test_unknown_selector_is_rejected(self):
        fixture = case("bad_selector", 210)
        fixture["selector"] = "first_route"
        with self.assertRaises(ValueError):
            evaluate(fixture)


if __name__ == "__main__":
    unittest.main()
