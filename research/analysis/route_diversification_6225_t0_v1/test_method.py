import json
import hashlib
import unittest
from pathlib import Path

import candidate
import audit


HERE = Path(__file__).resolve().parent


class RouteDiversificationMethodTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads((HERE / "fixture.json").read_text())

    def test_hidden_shock_can_reward_precommitted_diversity(self):
        case = self.fixture["cases"][0]
        mix = candidate.run_case(case, "prospective_mixture")
        baseline = candidate.run_case(case, "best_mean_reactive")
        self.assertGreater(mix["mission_survival"], baseline["mission_survival"])
        self.assertEqual(0, mix["wrong_effects"])

    def test_contextual_policy_dominates_mixing_when_regime_observable(self):
        case = self.fixture["cases"][1]
        context = candidate.run_case(case, "context_gated")
        mix = candidate.run_case(case, "prospective_mixture")
        self.assertEqual(1, context["mission_survival"])
        self.assertGreater(context["verified_successes"], mix["verified_successes"])

    def test_common_shock_yields_no_diversification_benefit(self):
        case = self.fixture["cases"][2]
        outcomes = [candidate.run_case(case, policy) for policy in candidate.POLICIES]
        self.assertEqual({0}, {row["mission_survival"] for row in outcomes})

    def test_idle_decay_is_charged_to_the_complete_session(self):
        case = self.fixture["cases"][4]
        mix = candidate.run_case(case, "prospective_mixture")
        self.assertEqual(5, mix["verified_successes"])
        self.assertEqual(1, mix["unresolved_obligations"])

    def test_no_eligible_b_never_selects_it(self):
        case = self.fixture["cases"][6]
        for policy in candidate.POLICIES:
            self.assertNotIn("B", candidate.run_case(case, policy)["route_schedule"])

    def test_hand_calculated_decision_table(self):
        expected = {
            "hidden_a_specific_shock": {"best_mean_reactive": (0, 1, 1), "context_gated": (0, 1, 1), "prospective_mixture": (1, 3, 0), "oracle_diagnostic": (1, 3, 0)},
            "observable_shock": {"best_mean_reactive": (0, 1, 1), "context_gated": (1, 4, 0), "prospective_mixture": (0, 2, 1), "oracle_diagnostic": (1, 4, 0)},
            "shared_failure_shock": {"best_mean_reactive": (0, 1, 1), "context_gated": (0, 1, 1), "prospective_mixture": (0, 1, 1), "oracle_diagnostic": (0, 1, 1)},
            "stable_a_dominant": {p: (1, 4, 0) for p in candidate.POLICIES},
            "b_idle_decay": {"best_mean_reactive": (1, 6, 0), "context_gated": (1, 6, 0), "prospective_mixture": (1, 5, 0), "oracle_diagnostic": (1, 6, 0)},
            "route_induced_queue_carryover": {p: (1, 4, 0) for p in candidate.POLICIES},
            "no_eligible_b": {p: (1, 4, 0) for p in candidate.POLICIES},
        }
        for case in self.fixture["cases"]:
            for policy in candidate.POLICIES:
                row = candidate.run_case(case, policy)
                self.assertEqual(expected[case["id"]][policy], (row["mission_survival"], row["verified_successes"], row["wrong_effects"]))
                if "latency" in case["expect"][policy]:
                    self.assertEqual(case["expect"][policy]["latency"], row["latency"])

    def test_session_policy_carries_queue_cost_forward(self):
        case = next(row for row in self.fixture["cases"] if row["id"] == "route_induced_queue_carryover")
        mix = candidate.run_case(case, "prospective_mixture")
        best = candidate.run_case(case, "best_mean_reactive")
        self.assertEqual(9, mix["latency"])
        self.assertEqual(4, best["latency"])

    def test_independent_enumerator_agrees_on_all_rows(self):
        rows = [candidate.run_case(case, policy) for case in self.fixture["cases"] for policy in candidate.POLICIES]
        independent = [audit.oracle(case, policy) for case in self.fixture["cases"] for policy in audit.POLICIES]
        self.assertEqual(independent, rows)

    def test_independent_mutation_suite_rejects_all_corruptions(self):
        rows = [candidate.run_case(case, policy) for case in self.fixture["cases"] for policy in candidate.POLICIES]
        raw = {"allocation": self.fixture["allocation"], "fixture_sha256": hashlib.sha256((HERE / "fixture.json").read_bytes()).hexdigest(), "rows": rows}
        expected = [audit.oracle(case, policy) for case in self.fixture["cases"] for policy in audit.POLICIES]
        controls = audit.corruptions(raw, expected, self.fixture)
        self.assertEqual(10, len(controls))
        self.assertTrue(all(controls.values()), controls)


if __name__ == "__main__":
    unittest.main()
