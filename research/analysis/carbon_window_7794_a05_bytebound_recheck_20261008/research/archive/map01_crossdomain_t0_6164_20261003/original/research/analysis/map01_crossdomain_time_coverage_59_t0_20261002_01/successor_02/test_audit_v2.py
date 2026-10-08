import unittest

from audit_v2 import candidate_consistency_errors


def valid_candidate():
    return {
        "status": "HOLD_CROSSDOMAIN_TIME_COVERAGE_UNIDENTIFIED",
        "cross_domain_time_coverage_identified": False,
        "shared_time_denominator_identified": False,
        "candidate_invocations": 1,
        "retries": 0,
        "domains": [
            {"domain": "doom_v38", "event_counts": {"input_admission": 11,
             "keys_held": 11, "input_released": 0, "post_control_score": 1},
             "admitted_actuations": 11, "time_coverage_identified": False,
             "per_actuation_occupancy_identified": False,
             "effect_clock_join_identified": False,
             "first_useful_feedback_verified": False},
            {"domain": "doom_v39", "event_counts": {"input_admission": 39,
             "keys_held": 28, "input_released": 1, "post_control_score": 1},
             "admitted_actuations": 39, "time_coverage_identified": False,
             "per_actuation_occupancy_identified": False,
             "effect_clock_join_identified": False,
             "first_useful_feedback_verified": False},
            {"domain": "openttd", "event_counts": {"input_admission": 2,
             "pointer_admission": 29, "terminal": 25}, "admitted_actuations": 9,
             "pointer_button_down_admissions": 7, "per_button_up_admissions": 0,
             "same_program_verified_neutral_terminal_joins": 7,
             "observer_records": 263, "observer_record_count": 263,
             "observer_unique_states": 2,
             "observer_transition_witness_count": 1,
             "observer_transition_indices": [91],
             "time_coverage_identified": False,
             "per_actuation_occupancy_identified": False,
             "effect_clock_join_identified": False},
        ],
    }


class AuditV2Tests(unittest.TestCase):
    def setUp(self):
        self.raw_counts = {
            "doom_v38": {"input_admission": 11, "keys_held": 11,
                          "input_released": 0, "post_control_score": 1},
            "doom_v39": {"input_admission": 39, "keys_held": 28,
                          "input_released": 1, "post_control_score": 1},
            "openttd": {"input_admission": 2, "pointer_admission": 29,
                        "terminal": 25},
        }

    def test_accepts_only_source_consistent_hold(self):
        self.assertEqual(candidate_consistency_errors(
            valid_candidate(), self.raw_counts, observer_count=263,
            transition_indices=[91], unique_states=2), [])

    def test_rejects_predecessor_v38_score_expectation_bug(self):
        candidate = valid_candidate()
        candidate["domains"][0]["event_counts"]["post_control_score"] = 0
        self.assertTrue(any("doom_v38 event_counts" in error for error in
                            candidate_consistency_errors(candidate, self.raw_counts,
                                observer_count=263, transition_indices=[91])))

    def test_rejects_inconsistent_observer_record_alias(self):
        candidate = valid_candidate()
        candidate["domains"][2]["observer_records"] = 1
        self.assertTrue(any("observer record count" in error for error in
                            candidate_consistency_errors(candidate, self.raw_counts,
                                observer_count=263, transition_indices=[91])))

    def test_rejects_overclaim_and_transition_drift(self):
        candidate = valid_candidate()
        candidate["domains"][2]["time_coverage_identified"] = True
        candidate["domains"][2]["observer_transition_indices"] = [90]
        errors = candidate_consistency_errors(candidate, self.raw_counts,
                                               observer_count=263,
                                               transition_indices=[91])
        self.assertTrue(any("coverage" in error for error in errors))
        self.assertTrue(any("transition" in error for error in errors))

    def test_rejects_observer_state_count_drift(self):
        candidate = valid_candidate()
        candidate["domains"][2]["observer_unique_states"] = 1
        self.assertTrue(any("unique-state" in error for error in
                            candidate_consistency_errors(candidate, self.raw_counts,
                                observer_count=263, transition_indices=[91],
                                unique_states=2)))


if __name__ == "__main__":
    unittest.main()
