import unittest

from safety_filter_5317 import POLICIES, run_case


CASES = {
    "two_step_unsafe": {
        "initial": "A", "plan": ["prepare", "commit"],
        "model": {("A", "prepare"): ["B"], ("B", "commit"): ["BAD"]},
        "truth": {("A", "prepare"): ["B"], ("B", "commit"): ["BAD"]},
        "forbidden": ["BAD"], "goals": ["DONE"], "recoveries": ["RECOVER"],
        "model_quality": "exact"},
    "dead_end": {
        "initial": "A", "plan": ["close_backup"],
        "model": {("A", "close_backup"): ["STRANDED"]},
        "truth": {("A", "close_backup"): ["STRANDED"]},
        "forbidden": [], "goals": ["DONE"], "recoveries": ["RECOVER"],
        "model_quality": "exact"},
    "safe_goal": {
        "initial": "A", "plan": ["advance", "finish"],
        "model": {("A", "advance"): ["B"], ("B", "finish"): ["DONE"],
                  ("B", "backtrack"): ["RECOVER"]},
        "truth": {("A", "advance"): ["B"], ("B", "finish"): ["DONE"],
                  ("B", "backtrack"): ["RECOVER"]},
        "forbidden": [], "goals": ["DONE"], "recoveries": ["RECOVER"],
        "model_quality": "exact"},
    "bounded_safe": {
        "initial": "A", "plan": ["advance"],
        "model": {("A", "advance"): ["B", "C"], ("B", "recover"): ["RECOVER"],
                  ("C", "recover"): ["RECOVER"]},
        "truth": {("A", "advance"): ["B", "C"], ("B", "recover"): ["RECOVER"],
                  ("C", "recover"): ["RECOVER"]},
        "forbidden": [], "goals": ["DONE"], "recoveries": ["RECOVER"],
        "model_quality": "bounded"},
    "bounded_with_bad_outcome": {
        "initial": "A", "plan": ["advance"],
        "model": {("A", "advance"): ["B", "BAD"]},
        "truth": {("A", "advance"): ["B", "BAD"]},
        "forbidden": ["BAD"], "goals": ["DONE"], "recoveries": ["RECOVER"],
        "model_quality": "bounded"},
    "missing_transition": {
        "initial": "A", "plan": ["act"], "model": {},
        "truth": {("A", "act"): ["DONE"]},
        "forbidden": [], "goals": ["DONE"], "recoveries": ["RECOVER"],
        "model_quality": "missing"},
    "stale_optimistic": {
        "initial": "A", "plan": ["act"],
        "model": {("A", "act"): ["B"]},
        "truth": {("A", "act"): ["BAD"]},
        "forbidden": ["BAD"], "goals": ["DONE"], "recoveries": ["RECOVER"],
        "model_quality": "stale"},
}


class SafetyFilterTests(unittest.TestCase):
    def test_horizon_catches_unsafe_two_step_prefix_before_execution(self):
        case = CASES["two_step_unsafe"]
        self.assertTrue(run_case(case, "ONE_STEP_FILTER")["unsafe_prefix"])
        self.assertFalse(run_case(case, "HORIZON_FILTER")["admitted"])
        self.assertFalse(run_case(case, "VIABILITY_FILTER")["admitted"])

    def test_viability_blocks_safe_but_irrecoverable_dead_end(self):
        case = CASES["dead_end"]
        self.assertTrue(run_case(case, "ONE_STEP_FILTER")["stranded"])
        self.assertTrue(run_case(case, "HORIZON_FILTER")["stranded"])
        self.assertFalse(run_case(case, "VIABILITY_FILTER")["admitted"])

    def test_known_safe_completion_is_preserved(self):
        for policy in POLICIES:
            got = run_case(CASES["safe_goal"], policy)
            self.assertTrue(got["admitted"], policy)
            self.assertTrue(got["goal_reached"], policy)

    def test_bounded_safe_uncertainty_is_robustly_admitted_except_uniform_unknown_arm(self):
        for policy in ("ONE_STEP_FILTER", "HORIZON_FILTER", "VIABILITY_FILTER"):
            self.assertTrue(run_case(CASES["bounded_safe"], policy)["admitted"], policy)
        self.assertFalse(run_case(CASES["bounded_safe"], "UNKNOWN_FAIL_CLOSED")["admitted"])

    def test_adversarial_bounded_outcome_is_rejected(self):
        for policy in POLICIES[1:]:
            self.assertFalse(run_case(CASES["bounded_with_bad_outcome"], policy)["admitted"], policy)

    def test_missing_and_stale_models_fail_closed(self):
        for name in ("missing_transition", "stale_optimistic"):
            for policy in POLICIES[1:]:
                self.assertFalse(run_case(CASES[name], policy)["admitted"], f"{name}/{policy}")

    def test_filters_never_create_authority_or_external_effect_truth(self):
        for case in CASES.values():
            for policy in POLICIES:
                got = run_case(case, policy)
                self.assertFalse(got["authority_created"])
                self.assertFalse(got["effect_claim_created"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
