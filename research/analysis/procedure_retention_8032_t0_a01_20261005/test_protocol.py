import json
from pathlib import Path
import unittest

try:
    import protocol
except ModuleNotFoundError:
    protocol = None
try:
    import audit
except ModuleNotFoundError:
    audit = None


class ProcedureRetentionScoringTests(unittest.TestCase):
    def require_protocol(self):
        self.assertIsNotNone(protocol, "protocol scorer/validator is not implemented")

    def test_exact_unaided_steps_and_final_state_score_as_complete(self):
        self.require_protocol()
        result = protocol.score_attempt(
            expected_steps=["open_preferences", "select_appearance", "choose_dark", "apply"],
            expected_state={"theme": "dark"},
            attempt={"target": "disposable-profile", "actions": [
                "open_preferences", "select_appearance", "choose_dark", "apply"],
                "final_state": {"theme": "dark"}, "active_seconds": 42,
                "elapsed_seconds": 67})
        self.assertEqual(result, {
            "status": "complete", "step_score": 1.0, "severity": "none",
            "critical_error": False, "active_seconds": 42, "elapsed_seconds": 67})

    def test_wrong_profile_is_critical_even_when_steps_and_state_match(self):
        self.require_protocol()
        result = protocol.score_attempt(
            expected_steps=["open_preferences", "apply"],
            expected_state={"theme": "dark"},
            attempt={"target": "non_disposable-profile", "actions": [
                "open_preferences", "apply"], "final_state": {"theme": "dark"},
                "active_seconds": 10, "elapsed_seconds": 12})
        self.assertEqual(result["status"], "critical_error")
        self.assertEqual(result["severity"], "critical")
        self.assertFalse(result["critical_error"] is False)
        self.assertEqual(result["step_score"], 1.0)

    def test_wrong_action_order_is_not_complete_despite_matching_final_state(self):
        self.require_protocol()
        result = protocol.score_attempt(
            expected_steps=["open_preferences", "select_appearance", "choose_dark", "apply"],
            expected_state={"theme": "dark"},
            attempt={"target": "disposable-profile", "actions": [
                "open_preferences", "choose_dark", "select_appearance", "apply"],
                "final_state": {"theme": "dark"}, "active_seconds": 50,
                "elapsed_seconds": 70})
        self.assertNotEqual(result["status"], "complete")
        self.assertEqual(result["severity"], "major")

    def test_missing_delayed_outcome_is_retained_without_imputation(self):
        self.require_protocol()
        result = protocol.score_attempt(
            expected_steps=["open_preferences"], expected_state={"theme": "dark"},
            attempt=None)
        self.assertEqual(result["status"], "missing")
        self.assertIsNone(result["step_score"])
        self.assertIsNone(result["active_seconds"])
        self.assertIsNone(result["elapsed_seconds"])

    def test_baseline_competency_requires_two_of_three_without_critical_error(self):
        self.require_protocol()
        attempts = [
            {"status": "complete", "critical_error": False},
            {"status": "complete", "critical_error": False},
            {"status": "incomplete", "critical_error": False},
        ]
        self.assertTrue(protocol.baseline_eligible(attempts))
        attempts[0] = {"status": "complete", "critical_error": True}
        self.assertFalse(protocol.baseline_eligible(attempts))

    def valid_plan(self):
        arms = []
        for arm, mode, prompts in (
                ("manual", "manual", []),
                ("automation_only", "agent", []),
                ("automation_retrieval", "agent", [2, 4, 6])):
            arms.append({
                "arm": arm, "mode": mode, "opportunities": list(range(1, 7)),
                "task_version": "theme-procedure-v1", "reset_each_opportunity": True,
                "starting_state_source": "disposable-profile-v1",
                "goal_card": "change the disposable profile appearance",
                "interface_evidence_version": "same-visible-state-v1",
                "retrieval_prompts": [{
                    "opportunity": n, "before_agent_action": True,
                    "before_feedback": True, "allow_unsure": True,
                    "text": "Without acting, state or select the next safe step; unsure is okay."}
                    for n in prompts],
                "training_packets": [{"opportunity": n,
                    "task_key": "theme-procedure-v1",
                    "delayed_test_scoring_key": None,
                    "heldout_transfer_answer_key": None}
                    for n in range(1, 7)],
            })
        return {"arms": arms, "opportunities_per_arm": 6,
                "delayed_interval_hours": 48,
                "heldout_transfer_task": "status-bar-procedure-v1"}

    def require_validator(self):
        self.require_protocol()
        validator = getattr(protocol, "validate_study_plan", None)
        self.assertIsNotNone(validator, "matched-exposure validator is not implemented")
        return validator

    def test_matched_three_arm_schedule_accepts_pre_feedback_spaced_prompts(self):
        validate = self.require_validator()
        result = validate(self.valid_plan())
        self.assertEqual(result, {"valid": True, "errors": []})

    def test_mismatched_opportunity_or_evidence_access_is_rejected(self):
        validate = self.require_validator()
        plan = self.valid_plan()
        plan["arms"][1]["opportunities"] = [1, 2, 3, 4, 5]
        plan["arms"][2]["interface_evidence_version"] = "different-v2"
        result = validate(plan)
        self.assertFalse(result["valid"])
        self.assertIn("opportunity_count_mismatch", result["errors"])
        self.assertIn("evidence_access_mismatch", result["errors"])
        independent = audit.audit_plan(plan)
        self.assertFalse(independent["valid"])
        self.assertIn("evidence_access_mismatch", independent["errors"])

    def test_training_packet_count_must_match_the_six_task_opportunities(self):
        validate = self.require_validator()
        plan = self.valid_plan()
        plan["arms"][0]["training_packets"].pop()
        result = validate(plan)
        self.assertFalse(result["valid"])
        self.assertIn("training_packet_count_mismatch", result["errors"])
        self.assertIn("training_packet_count_mismatch", audit.audit_plan(plan)["errors"])

    def test_retrieval_prompts_must_precede_action_and_feedback(self):
        validate = self.require_validator()
        plan = self.valid_plan()
        plan["arms"][2]["retrieval_prompts"][1]["before_feedback"] = False
        result = validate(plan)
        self.assertFalse(result["valid"])
        self.assertIn("retrieval_prompt_timing_invalid", result["errors"])

    def test_test_scoring_and_transfer_answer_keys_must_not_enter_training_packets(self):
        validate = self.require_validator()
        plan = self.valid_plan()
        plan["arms"][2]["training_packets"][0]["heldout_transfer_answer_key"] = [
            "open_view_menu", "enable_line_numbers"]
        result = validate(plan)
        self.assertFalse(result["valid"])
        self.assertIn("test_answer_key_leakage", result["errors"])
        plan = self.valid_plan()
        plan["arms"][1]["training_packets"][0]["task_key"] = "status-bar-procedure-v1"
        result = validate(plan)
        self.assertFalse(result["valid"])
        self.assertIn("transfer_task_not_held_out", result["errors"])

    def test_takeover_state_comprehension_is_separate_from_delayed_retention(self):
        self.require_protocol()
        scorer = getattr(protocol, "score_takeover", None)
        self.assertIsNotNone(scorer, "takeover scoring is not implemented")
        result = scorer(
            observed_state={"theme": "dark", "save_status": "pending"},
            answer={"theme": "dark", "save_status": "saved",
                    "next_safe_step": "verify_save"},
            expected_next_safe_step="verify_save")
        self.assertEqual(result, {"state_correct": False,
                                  "next_step_correct": True})
        self.assertNotIn("retention_score", result)

    def test_vigilance_trials_are_scored_as_signal_detection_not_procedure_retention(self):
        self.require_protocol()
        scorer = getattr(protocol, "score_vigilance", None)
        self.assertIsNotNone(scorer, "vigilance scoring is not implemented")
        result = scorer([
            {"anomaly": True, "reported": True},
            {"anomaly": True, "reported": False},
            {"anomaly": False, "reported": True},
            {"anomaly": False, "reported": False},
        ])
        self.assertEqual(result, {"hits": 1, "misses": 1,
                                  "false_alarms": 1, "correct_rejections": 1})
        self.assertNotIn("retention_score", result)

    def test_independent_oracle_reconstructs_takeover_and_vigilance_separately(self):
        self.assertIsNotNone(audit, "independent oracle is not implemented")
        takeover = getattr(audit, "score_takeover", None)
        vigilance = getattr(audit, "score_vigilance", None)
        self.assertIsNotNone(takeover, "independent takeover oracle is missing")
        self.assertIsNotNone(vigilance, "independent vigilance oracle is missing")
        cases = json.loads((Path(__file__).parent / "synthetic_cases.json").read_text())
        t = cases["takeover_counterexample"]
        self.assertEqual(takeover(t["observed_state"], t["answer"],
                                  t["expected_next_safe_step"]), t["expected_score"])
        v = cases["vigilance_counterexample"]
        self.assertEqual(vigilance(v["trials"]), v["expected_score"])

    def test_independent_auditor_reconstructs_scoring_without_candidate_import(self):
        self.assertIsNotNone(audit, "independent oracle is not implemented")
        result = audit.score_attempt(
            ["open", "select", "apply"], {"theme": "dark"},
            {"target": "disposable-profile", "actions": ["open", "select", "apply"],
             "final_state": {"theme": "dark"}, "active_seconds": 20,
             "elapsed_seconds": 31})
        self.assertEqual(result, {"status": "complete", "step_score": 1.0,
                                  "severity": "none", "critical_error": False,
                                  "active_seconds": 20, "elapsed_seconds": 31})

    def test_independent_auditor_rejects_answer_key_leakage_and_matched_exposure_mutations(self):
        self.assertIsNotNone(audit, "independent oracle is not implemented")
        plan = self.valid_plan()
        self.assertEqual(audit.audit_plan(plan), {"valid": True, "errors": []})
        plan["arms"][2]["training_packets"][0]["delayed_test_scoring_key"] = {
            "steps": ["open", "select", "apply"]}
        result = audit.audit_plan(plan)
        self.assertFalse(result["valid"])
        self.assertIn("test_answer_key_leakage", result["errors"])
        plan = self.valid_plan()
        plan["arms"][0]["training_packets"][0]["task_key"] = "status-bar-procedure-v1"
        self.assertIn("transfer_task_not_held_out", audit.audit_plan(plan)["errors"])
        plan = self.valid_plan()
        plan["arms"][2]["retrieval_prompts"][0]["before_agent_action"] = False
        self.assertIn("retrieval_prompt_timing_invalid", audit.audit_plan(plan)["errors"])

    def test_independent_power_recomputation_matches_the_preregistered_sensitivity_grid(self):
        self.assertIsNotNone(audit, "independent oracle is not implemented")
        self.assertEqual(audit.sample_size(.5), 106)
        self.assertEqual(audit.sample_size(.35), 216)

    def test_power_feasibility_rationale_includes_attrition_without_claiming_an_effect(self):
        self.require_protocol()
        planner = getattr(protocol, "sample_size_rationale", None)
        self.assertIsNotNone(planner, "power/feasibility rationale is not implemented")
        self.assertEqual(planner(.5), {
            "assumed_standardized_effect": .5,
            "completers_per_arm": 90,
            "recruited_per_arm_at_15pct_attrition": 106,
            "total_recruited_three_arms": 318,
            "status": "planning_assumption_only"})
        self.assertEqual(planner(.35)["total_recruited_three_arms"], 648)

    def test_frozen_t0_packet_has_no_people_and_candidate_matches_independent_rows(self):
        self.require_protocol()
        self.assertIsNotNone(audit, "independent oracle is not implemented")
        root = Path(__file__).parent
        plan_path = root / "study_plan.json"
        cases_path = root / "synthetic_cases.json"
        self.assertTrue(plan_path.exists(), "frozen study plan is missing")
        self.assertTrue(cases_path.exists(), "scoring counterexamples are missing")
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        cases = json.loads(cases_path.read_text(encoding="utf-8"))
        self.assertFalse(cases["contains_participant_data"])
        self.assertEqual(protocol.validate_study_plan(plan), {"valid": True, "errors": []})
        self.assertEqual(audit.audit_plan(plan), {"valid": True, "errors": []})
        self.assertTrue(plan["exclusions_and_stops"]["no_recruitment_or_observation_in_T0"])
        self.assertIn("ethics/privacy approval", plan["T1_gate"])
        for sensitivity in plan["sample_feasibility"]["standardized_effect_sensitivity"]:
            candidate = protocol.sample_size_rationale(sensitivity["assumed_d"])
            recruited = audit.sample_size(sensitivity["assumed_d"])
            self.assertEqual(candidate["completers_per_arm"],
                             sensitivity["completers_per_arm"])
            self.assertEqual(recruited, sensitivity["recruited_per_arm"])
            self.assertEqual(candidate["total_recruited_three_arms"],
                             sensitivity["total_recruited"])
        for row in cases["retention_cases"]:
            actual = protocol.score_attempt(row["expected_steps"], row["expected_state"],
                                            row["attempt"])
            independently = audit.score_attempt(row["expected_steps"],
                                                  row["expected_state"], row["attempt"])
            self.assertEqual(actual, row["expected_score"], row["case_id"])
            self.assertEqual(independently, row["expected_score"], row["case_id"])


if __name__ == "__main__":
    unittest.main()
