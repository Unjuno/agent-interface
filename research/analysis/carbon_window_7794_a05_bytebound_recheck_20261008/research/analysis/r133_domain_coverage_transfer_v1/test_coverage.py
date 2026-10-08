import unittest

try:
    from coverage_transfer import build_coverage
except ImportError:
    build_coverage = None


DOOM_PHYSICAL = {
    "decision": "PASS_MAP01_V12_PHYSICAL_OCCUPANCY_R1_SCOPED",
    "formal": {
        "sessions_completed": 3,
        "sessions_pass": 3,
        "actuations": 6,
        "max_censor_width_ms": 0.559054,
        "all_precision_pass": True,
        "all_owned_after_empty": True,
        "all_post_sample_up": True,
        "all_terminal_completed": True,
        "all_errors_empty": True,
    },
}

DOOM_OCCUPANCY = {
    "decision": "SCHEMA_CENSORING_TOO_WIDE",
    "runs": {
        "map01-v38-integrated-threat-live-01": {
            "hold_steps": 11,
            "physical_any_key_occupancy_lower_ms": 3048.89,
            "physical_any_key_occupancy_upper_ms": 4039.878,
            "occupancy_interval_width_ms": 990.987,
            "width_to_occupancy_upper": 0.24530121949227177,
            "informative_enough_for_next_matched_metric": True,
        },
        "map01-v39-coast-liveness-live-01": {
            "hold_steps": 29,
            "physical_any_key_occupancy_lower_ms": 6301.2,
            "physical_any_key_occupancy_upper_ms": 8452.733,
            "occupancy_interval_width_ms": 2151.534,
            "width_to_occupancy_upper": 0.25453708285828974,
            "informative_enough_for_next_matched_metric": False,
        },
    },
}

DOOM_FEEDBACK = {
    "state_feedback_all_admitted_plans": False,
    "stronger_task_effect_all_admitted_plans": False,
    "plans": [
        {"earliest_state_feedback": None, "stronger_task_effect_feedback": None},
        {"earliest_state_feedback": {"changed": ["ammo"]}, "stronger_task_effect_feedback": None},
        {"earliest_state_feedback": {"changed": ["health", "ammo"]}, "stronger_task_effect_feedback": None},
        {"earliest_state_feedback": {"changed": ["ammo"]}, "stronger_task_effect_feedback": None},
    ],
}

CALC = {
    "decision": "HOLD_PRODUCTION_ADOPTION",
    "rows": [
        {"saved_correct": True, "release_verified": True, "extra_observations": 1},
        {"saved_correct": True, "release_verified": True, "extra_observations": 0},
        {"saved_correct": True, "release_verified": True, "extra_observations": 0},
        {"saved_correct": True, "release_verified": True, "extra_observations": 1},
    ],
    "unavailable": ["host image-render endpoint", "separate host receipt timestamp"],
}


def coverage():
    if not callable(build_coverage):
        raise AssertionError("coverage_transfer.build_coverage is not implemented")
    return build_coverage(DOOM_PHYSICAL, DOOM_OCCUPANCY, DOOM_FEEDBACK, CALC)


class CoverageTransferTests(unittest.TestCase):
    def test_physical_down_up_measurement_is_not_confused_with_occupancy_duration(self):
        result = coverage()
        axis = result["domains"]["doom_physical_r1"]["held_input_occupancy"]
        self.assertEqual(axis["status"], "MEASURED_BOUNDED")
        self.assertEqual(axis["paired_actuation_edges"], 6)
        self.assertEqual(axis["max_censor_width_ms"], 0.559054)

    def test_partial_posthoc_width_gate_does_not_become_a_global_pass(self):
        result = coverage()
        axis = result["domains"]["doom_v38_v39"]["held_input_occupancy"]
        self.assertEqual(axis["status"], "INTERVAL_CENSORED")
        self.assertTrue(axis["runs"]["v38"]["precision_gate_passed"])
        self.assertFalse(axis["runs"]["v39"]["precision_gate_passed"])

    def test_health_or_ammo_change_is_state_feedback_not_useful_task_effect(self):
        result = coverage()
        axis = result["domains"]["doom_v38_v39"]["useful_feedback"]
        self.assertEqual(axis["status"], "PARTIAL_STATE_FEEDBACK_ONLY")
        self.assertEqual(axis["plans_with_state_feedback"], 3)
        self.assertEqual(axis["admitted_plans"], 4)
        self.assertEqual(axis["plan_bound_task_effects"], 0)

    def test_calc_releases_and_saved_correctness_do_not_invent_timing(self):
        result = coverage()
        domain = result["domains"]["calc_final_wait"]
        self.assertEqual(domain["held_input_occupancy"]["status"], "RELEASE_ONLY")
        self.assertFalse(domain["held_input_occupancy"]["duration_measured"])
        self.assertEqual(domain["task_outcome"]["status"], "SAVED_OUTPUT_VERIFIED_UNTIMED")
        self.assertEqual(domain["task_outcome"]["verified_rows"], 4)
        self.assertEqual(domain["useful_feedback"]["status"], "OBSERVATION_COUNT_ONLY")
        self.assertEqual(domain["useful_feedback"]["extra_observations"], 2)
        self.assertFalse(domain["useful_feedback"]["first_useful_time_identifiable"])

    def test_vector_keeps_axes_separate_without_scalar_promotion(self):
        result = coverage()
        self.assertNotIn("overall_coverage_score", result)
        self.assertEqual(set(result["domains"]), {"doom_physical_r1", "doom_v38_v39", "calc_final_wait"})

    def test_impossible_physical_terminal_refuses_measured_classification(self):
        source = dict(DOOM_PHYSICAL)
        source["formal"] = dict(DOOM_PHYSICAL["formal"], all_post_sample_up=False)
        result = build_coverage(source, DOOM_OCCUPANCY, DOOM_FEEDBACK, CALC)
        axis = result["domains"]["doom_physical_r1"]["held_input_occupancy"]
        self.assertEqual(axis["status"], "INCONSISTENT_SOURCE_EVIDENCE")

    def test_audit_rejects_promoting_calc_release_into_duration_measurement(self):
        from coverage_transfer import audit_coverage

        result = coverage()
        result["domains"]["calc_final_wait"]["held_input_occupancy"]["duration_measured"] = True
        audit = audit_coverage(result, DOOM_PHYSICAL, DOOM_OCCUPANCY, DOOM_FEEDBACK, CALC)
        self.assertFalse(audit["passed"])
        self.assertIn("calc_duration_not_identifiable", audit["errors"])

    def test_audit_rejects_promoting_unscored_state_change_to_task_effect(self):
        from coverage_transfer import audit_coverage

        result = coverage()
        result["domains"]["doom_v38_v39"]["useful_feedback"]["plan_bound_task_effects"] = 1
        audit = audit_coverage(result, DOOM_PHYSICAL, DOOM_OCCUPANCY, DOOM_FEEDBACK, CALC)
        self.assertFalse(audit["passed"])
        self.assertIn("task_effect_count_mismatch", audit["errors"])

    def test_audit_rejects_v39_precision_gate_flip(self):
        from coverage_transfer import audit_coverage

        result = coverage()
        result["domains"]["doom_v38_v39"]["held_input_occupancy"]["runs"]["v39"]["precision_gate_passed"] = True
        audit = audit_coverage(result, DOOM_PHYSICAL, DOOM_OCCUPANCY, DOOM_FEEDBACK, CALC)
        self.assertFalse(audit["passed"])
        self.assertIn("occupancy_gate_mismatch:v39", audit["errors"])


if __name__ == "__main__":
    unittest.main()
