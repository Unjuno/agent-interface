import unittest

from comparator import cost_frontier, decisions_for_cues, preimage, proposal_local, total_correct


class ComparatorConstructionTests(unittest.TestCase):
    def test_total_correctness_is_universal_and_forbids_prefix(self):
        good = {"effect": "exact_target_saved", "forbidden_prefix": [], "release": "empty_verified", "terminated": True, "steps": 2}
        bad = {**good, "forbidden_prefix": ["wrong_target"]}
        self.assertTrue(total_correct(good, 3))
        self.assertFalse(total_correct(bad, 3))
        self.assertFalse(total_correct({**good, "steps": 4}, 3))

    def test_partial_observation_keeps_alias_unknown(self):
        states = [
            {"id": "safe", "cues": {"pixels": "same"}},
            {"id": "unsafe", "cues": {"pixels": "same"}},
        ]
        result = decisions_for_cues({"states": states}, {"safe"}, ("pixels",))
        self.assertEqual(result[0]["decision"], "UNKNOWN_NOT_OBSERVABLE")

    def test_pareto_does_not_require_weights(self):
        cues = {
            "pixels": "same", "generation_fresh": True,
            "already_committed_fresh": False, "release_available": True,
            "termination_bounded": True, "effect_contract_reliable": True,
            "certificate_status": "verified",
        }
        model = {"states": [{"id": "s", "cues": cues}]}
        result = cost_frontier(model, {"s"})
        self.assertIn("pareto_frontier", result)
        self.assertIn("weight_sensitivity", result)

    def test_preimage_empty_when_one_nondeterministic_outcome_fails(self):
        model = {"horizon_steps": 3, "states": [{"id": "s", "outcomes": [
            {"effect": "exact_target_saved", "forbidden_prefix": [], "release": "empty_verified", "terminated": True, "steps": 2},
            {"effect": "no_effect", "forbidden_prefix": [], "release": "empty_verified", "terminated": True, "steps": 2},
        ]}]}
        self.assertEqual(preimage(model), set())


if __name__ == "__main__":
    unittest.main()
