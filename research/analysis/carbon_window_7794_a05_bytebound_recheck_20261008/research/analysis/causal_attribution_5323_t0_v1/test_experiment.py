import json
import pathlib
import unittest

from policy import POLICIES, classify

ROOT=pathlib.Path(__file__).resolve().parent
CASES=json.loads((ROOT/"cases.json").read_text())["cases"]

class FirstUnitTests(unittest.TestCase):
    def test_matrix_shape(self):
        self.assertEqual(8*5, len(CASES)*len(POLICIES))

    def test_posthoc_is_fooled_by_known_competitor(self):
        c=next(x for x in CASES if x["id"]=="concurrent_human")
        self.assertEqual("CAUSAL_EFFECT_IDENTIFIED", classify(c,"POSTHOC_ASSOCIATION"))
        self.assertEqual("ATTRIBUTION_UNKNOWN", classify(c,"UNKNOWN_ON_CONFOUNDING"))

    def test_unknown_on_hidden_graph_gap(self):
        c=next(x for x in CASES if x["id"]=="hidden_background_drift")
        self.assertEqual("ATTRIBUTION_UNKNOWN", classify(c,"CAUSAL_MODEL"))
        self.assertEqual("CAUSAL_EFFECT_IDENTIFIED", classify(c,"POSTHOC_ASSOCIATION"))

    def test_control_is_link_not_identification(self):
        c=next(x for x in CASES if x["id"]=="direct_effect")
        self.assertEqual("EFFECT_LINKED_UNDER_CONTROL_ASSUMPTIONS", classify(c,"CONTROL_BASELINE"))

    def test_failed_action_cannot_be_identified(self):
        c=next(x for x in CASES if x["id"]=="failed_action_background_effect")
        self.assertEqual("ATTRIBUTION_UNKNOWN", classify(c,"UNKNOWN_ON_CONFOUNDING"))

    def test_no_effect_not_attributed(self):
        c=next(x for x in CASES if x["id"]=="successful_action_no_effect")
        for p in POLICIES:
            self.assertEqual("NO_EFFECT", classify(c,p))

    def test_unknown_policy_refuses(self):
        with self.assertRaises(ValueError):
            classify(CASES[0],"NOT_A_POLICY")

if __name__=="__main__": unittest.main()
