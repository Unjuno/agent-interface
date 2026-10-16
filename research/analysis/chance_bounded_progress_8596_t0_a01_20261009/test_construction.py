import copy
import unittest
from fractions import Fraction
from pathlib import Path
import json
import auditor
import candidate

ROOT=Path(__file__).resolve().parent


class ConstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixtures=json.loads((ROOT/"fixtures.json").read_text())

    def test_dynamic_recurrence_matches_independent_history_enumeration(self):
        for probs in ((Fraction(1,4),),(Fraction(1,4),Fraction(1,2)),(Fraction(2,3),)*4):
            self.assertEqual(candidate.dynamic_hit(probs),auditor.enumerate_histories(probs))

    def test_wide_interval_midpoint_can_overstate_robust_deadline_reachability(self):
        result=candidate.evaluate(self.fixtures); row=result["cases"]["geometric_wide"]["curve"][3]
        self.assertEqual(row["lower"],"175/256")
        self.assertEqual(row["midpoint_probability"],"3471/4096")
        self.assertEqual(row["upper"],"15/16")
        self.assertFalse(row["lower_meets_threshold"])
        self.assertTrue(row["midpoint_meets_threshold"])

    def test_high_geometric_interval_has_chance_threshold_without_sure_bound(self):
        row=candidate.evaluate(self.fixtures)["cases"]["geometric_high"]
        self.assertEqual(row["curve"][3]["lower"],"15/16")
        self.assertEqual(row["curve"][3]["all_miss_probability_at_max_endpoint"],"1/256")
        self.assertFalse(row["universal_finite_sure_bound"])
        self.assertTrue(row["curve"][3]["lower_meets_threshold"])

    def test_rare_trigger_scales_safe_progress_and_hard_safety_is_separate(self):
        cases=candidate.evaluate(self.fixtures)["cases"]
        safe=cases["rare_disturbance_safe_yield"]
        unsafe=cases["rare_disturbance_unsafe"]
        self.assertEqual(safe["stochastic_bounds"]["lower"],"5425/8192")
        self.assertEqual(safe["hard_safety"],"PASS")
        self.assertEqual(unsafe["hard_safety"],"FAIL")
        self.assertEqual(unsafe["adversarial_worst_case_lower"],"0/1")

    def test_equal_mean_delay_laws_have_different_four_opportunity_tails(self):
        d=candidate.evaluate(self.fixtures)["cases"]["same_mean_delay"]
        self.assertTrue(d["means_equal"])
        self.assertEqual(d["arms"]["benign"]["mean_opportunities"],"2/1")
        self.assertEqual(d["arms"]["rare_tail"]["mean_opportunities"],"2/1")
        self.assertEqual(d["arms"]["benign"]["probability_by_deadline"],"1/1")
        self.assertEqual(d["arms"]["rare_tail"]["probability_by_deadline"],"9/10")
        self.assertEqual(d["arms"]["rare_tail"]["probability_after_deadline"],"1/10")

    def test_unmodeled_case_has_no_numeric_probability(self):
        unknown=candidate.evaluate(self.fixtures)["cases"]["unmodeled_delay"]
        self.assertEqual(unknown["status"],"NOT_IDENTIFIABLE")
        self.assertNotIn("probability",unknown)

    def test_independent_enumerator_reconstructs_candidate_whole_payload(self):
        self.assertEqual(candidate.evaluate(self.fixtures),auditor.expected_payload(self.fixtures))

    def test_all_seven_saved_output_mutations_are_detected(self):
        raw=candidate.evaluate(self.fixtures); expected=auditor.expected_payload(self.fixtures)
        self.assertEqual(raw,expected)
        mutations=(
            lambda x:x["cases"]["geometric_wide"]["curve"][3].__setitem__("lower","1/1"),
            lambda x:x["cases"]["geometric_wide"]["curve"][3].__setitem__("lower",x["cases"]["geometric_wide"]["curve"][3]["midpoint_probability"]),
            lambda x:x["cases"]["geometric_high"].__setitem__("universal_finite_sure_bound",True),
            lambda x:x["cases"]["same_mean_delay"]["arms"]["rare_tail"]["support"].pop(),
            lambda x:x["cases"]["rare_disturbance_unsafe"].__setitem__("hard_safety","PASS"),
            lambda x:x["cases"]["unmodeled_delay"].__setitem__("numeric_probability_reported",True),
            lambda x:x["cases"]["geometric_high"].__setitem__("marker_visible_to_policy",True),
        )
        self.assertTrue(all((lambda changed:changed!=expected)(self._mutated(raw,mutate)) for mutate in mutations))

    @staticmethod
    def _mutated(raw,mutate):
        changed=copy.deepcopy(raw); mutate(changed); return changed


if __name__=="__main__": unittest.main()
