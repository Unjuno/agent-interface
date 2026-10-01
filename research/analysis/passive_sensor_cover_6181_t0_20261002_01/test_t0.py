import copy
import unittest
import candidate
import audit
import fixture_data

class PassiveCoverConstructionTests(unittest.TestCase):
    def setUp(self):
        self.fixture=fixture_data.FIXTURE

    def test_exhaustive_16_subsets(self):
        self.assertEqual(len(candidate.all_subsets(self.fixture)),16)

    def test_unique_preregistered_minimum(self):
        self.assertEqual(candidate.minimum_cover(self.fixture),
                         {"status":"COVER","channels":["app_status","os_focus_input"],
                          "cost":7,"minimum_tie_count":1,"cover_count":1})

    def test_mandatory_safety_sensor(self):
        for row in candidate.all_subsets(self.fixture):
            if row["status"]=="COVER":
                self.assertIn("os_focus_input",row["channels"])

    def test_screen_only_and_effect_alias_are_impossible(self):
        self.assertEqual(candidate.assess(self.fixture,["screenshot"])["status"],
                         "NO_SUFFICIENT_PASSIVE_COVER")
        self.assertEqual(candidate.solve(self.fixture)["impossible_effect_alias"]["status"],
                         "NO_SUFFICIENT_PASSIVE_COVER")

    def test_greedy_and_full_cost_comparison(self):
        result=candidate.solve(self.fixture)
        self.assertEqual(result["greedy"]["cost"],8)
        self.assertEqual(result["minimum"]["cost"],7)
        self.assertEqual(result["full_bundle"]["cost"],11)

    def test_required_producer_loss_fails_closed(self):
        drop=candidate.solve(self.fixture)["producer_dropout_from_minimum"]
        self.assertEqual(set(drop),{"app","os"})
        self.assertTrue(all(v["status"]=="NO_SUFFICIENT_PASSIVE_COVER" for v in drop.values()))

    def test_four_mutation_controls_rejected_by_raw_oracle(self):
        expected=candidate.solve(self.fixture)
        controls=audit.mutation_controls(self.fixture,expected)
        self.assertEqual(set(controls),{"crop_relabel_as_independent","missing_observation",
          "stale_generation","dispatch_substituted_for_effect"})
        self.assertTrue(all(x["rejected"] for x in controls.values()))

if __name__=="__main__":
    unittest.main()
