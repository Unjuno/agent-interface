import unittest

from audit_only import candidate_summary_errors, event_count


def candidate():
    return {
        "status": "HOLD_CROSSDOMAIN_TIME_COVERAGE_UNIDENTIFIED",
        "cross_domain_time_coverage_identified": False,
        "shared_time_denominator_identified": False,
        "domains": [
            {"domain": "doom_v38", "event_counts": {"input_admission": 11,
             "post_control_score": 1}, "time_coverage_identified": False,
             "per_actuation_occupancy_identified": False,
             "effect_clock_join_identified": False,
             "first_useful_feedback_verified": False},
            {"domain": "openttd", "event_counts": {"input_admission": 2,
             "pointer_admission": 29}, "time_coverage_identified": False,
             "per_actuation_occupancy_identified": False,
             "effect_clock_join_identified": False,
             "observer_records": 263, "observer_record_count": 263,
             "observer_transition_witness_count": 1,
             "observer_transition_indices": [91], "observer_unique_states": 2,
             "pointer_button_down_admissions": 7,
             "per_button_up_admissions": 0,
             "same_program_verified_neutral_terminal_joins": 7},
        ],
    }


class AuditOnlyTests(unittest.TestCase):
    def test_absent_event_kind_is_zero_not_none(self):
        self.assertEqual(event_count([], "input_released"), 0)

    def test_existing_event_kind_counts_raw_rows(self):
        self.assertEqual(event_count([{"event": "input_released"},
                                      {"event": "accepted"}], "input_released"), 1)

    def test_accepts_source_consistent_sparse_maps_and_hold(self):
        raw = {"doom_v38": {"input_admission": 11, "post_control_score": 1},
               "openttd": {"input_admission": 2, "pointer_admission": 29}}
        self.assertEqual(candidate_summary_errors(candidate(), raw, observer_count=263,
            transitions=[91], unique_states=2,
            pointer_counts={"pointer_button_down_admissions": 7,
                            "per_button_up_admissions": 0,
                            "same_program_verified_neutral_terminal_joins": 7}), [])

    def test_rejects_candidate_count_drift_and_observer_alias(self):
        value = candidate()
        value["domains"][0]["event_counts"]["post_control_score"] = 0
        value["domains"][1]["observer_records"] = 1
        raw = {"doom_v38": {"input_admission": 11, "post_control_score": 1},
               "openttd": {"input_admission": 2, "pointer_admission": 29}}
        errors = candidate_summary_errors(value, raw, observer_count=263,
            transitions=[91], unique_states=2)
        self.assertTrue(any("doom_v38 event_counts" in error for error in errors))
        self.assertTrue(any("observer record count" in error for error in errors))

    def test_rejects_candidate_coverage_overclaim(self):
        value = candidate()
        value["domains"][1]["time_coverage_identified"] = True
        raw = {"doom_v38": {"input_admission": 11, "post_control_score": 1},
               "openttd": {"input_admission": 2, "pointer_admission": 29}}
        errors = candidate_summary_errors(value, raw, observer_count=263,
            transitions=[91], unique_states=2)
        self.assertTrue(any("time_coverage_identified overclaim" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
