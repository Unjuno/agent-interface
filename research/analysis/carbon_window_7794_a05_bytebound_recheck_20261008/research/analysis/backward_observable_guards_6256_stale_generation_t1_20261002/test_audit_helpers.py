import unittest

from audit_stale_generation import matches_exact_guard, total_correct, universal_preimage


class AuditConstructionTests(unittest.TestCase):
    def setUp(self):
        self.model = {
            "horizon_steps": 3,
            "required_effect": "saved",
            "forbidden_prefix_tags": ["wrong_target"],
            "required_release": "empty",
            "states": [
                {"id": "ready", "cues": {"generation_fresh": True}, "outcomes": [
                    {"terminated": True, "steps": 2, "effect": "saved", "forbidden_prefix": [], "release": "empty"}
                ]},
                {"id": "stale", "cues": {"generation_fresh": False}, "outcomes": [
                    {"terminated": True, "steps": 2, "effect": "wrong", "forbidden_prefix": ["wrong_target"], "release": "empty"}
                ]},
            ],
        }

    def test_total_correctness_checks_all_dimensions(self):
        good = self.model["states"][0]["outcomes"][0]
        bad = dict(good, terminated=False)
        self.assertTrue(total_correct(good, self.model))
        self.assertFalse(total_correct(bad, self.model))

    def test_preimage_is_universal_over_state_outcomes(self):
        self.model["states"][0]["outcomes"].append({
            "terminated": True, "steps": 2, "effect": "no_effect", "forbidden_prefix": [], "release": "empty"
        })
        self.assertEqual(universal_preimage(self.model), set())

    def test_generation_deletion_admits_stale_mutant(self):
        safe = self.model["states"][0]
        stale = self.model["states"][1]
        self.assertFalse(matches_exact_guard(stale, safe))
        self.assertTrue(matches_exact_guard(stale, safe, omit_generation=True))


if __name__ == "__main__":
    unittest.main()
