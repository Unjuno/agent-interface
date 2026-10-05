"""Deterministic scorer for the disposable-procedure T0 construction."""
from math import ceil


def score_attempt(expected_steps, expected_state, attempt,
                  expected_target="disposable-profile"):
    if attempt is None:
        return {"status": "missing", "step_score": None, "severity": "unknown",
                "critical_error": False, "active_seconds": None,
                "elapsed_seconds": None}
    actions = attempt.get("actions", [])
    step_score = (sum(a == b for a, b in zip(actions, expected_steps)) /
                  len(expected_steps)) if expected_steps else 0.0
    if attempt.get("target") != expected_target:
        return {"status": "critical_error", "step_score": step_score,
                "severity": "critical", "critical_error": True,
                "active_seconds": attempt.get("active_seconds"),
                "elapsed_seconds": attempt.get("elapsed_seconds")}
    exact_sequence = actions == expected_steps
    state_match = attempt.get("final_state") == expected_state
    if exact_sequence and state_match:
        status, severity = "complete", "none"
    else:
        status, severity = "incomplete", "major"
    return {"status": status, "step_score": step_score, "severity": severity,
            "critical_error": False,
            "active_seconds": attempt.get("active_seconds"),
            "elapsed_seconds": attempt.get("elapsed_seconds")}


def baseline_eligible(attempts):
    if len(attempts) != 3 or any(row.get("critical_error") for row in attempts):
        return False
    return sum(row.get("status") == "complete" for row in attempts) >= 2


def validate_study_plan(plan):
    errors = []
    arms = plan.get("arms", [])
    expected = {"manual", "automation_only", "automation_retrieval"}
    by_name = {row.get("arm"): row for row in arms}
    if set(by_name) != expected or len(by_name) != len(arms):
        errors.append("arm_set_invalid")
    count = plan.get("opportunities_per_arm")
    expected_opportunities = list(range(1, count + 1)) if type(count) is int else []
    if not expected_opportunities:
        errors.append("opportunity_count_invalid")
    for row in arms:
        if row.get("opportunities") != expected_opportunities:
            errors.append("opportunity_count_mismatch")
        if row.get("reset_each_opportunity") is not True:
            errors.append("opportunity_reset_missing")
        packets = row.get("training_packets", [])
        if [packet.get("opportunity") for packet in packets] != expected_opportunities:
            errors.append("training_packet_count_mismatch")
        if any(packet.get("task_key") != row.get("task_version")
               for packet in packets):
            errors.append("training_task_version_mismatch")
    for field, error in (("task_version", "task_exposure_mismatch"),
                         ("starting_state_source", "starting_state_mismatch"),
                         ("goal_card", "task_goal_mismatch"),
                         ("interface_evidence_version", "evidence_access_mismatch")):
        if len({row.get(field) for row in arms}) != 1:
            errors.append(error)
    required_prompts = [2, 4, 6]
    for name in ("manual", "automation_only"):
        if name in by_name and by_name[name].get("retrieval_prompts") != []:
            errors.append("unexpected_retrieval_prompt")
    retrieval = by_name.get("automation_retrieval", {}).get("retrieval_prompts", [])
    if [p.get("opportunity") for p in retrieval] != required_prompts:
        errors.append("retrieval_schedule_invalid")
    if any(p.get("before_agent_action") is not True or
           p.get("before_feedback") is not True or p.get("allow_unsure") is not True
           for p in retrieval):
        errors.append("retrieval_prompt_timing_invalid")

    def key_leaked(value):
        forbidden = {"delayed_test_scoring_key", "heldout_transfer_answer_key",
                     "test_answer_key", "scoring_rubric_key"}
        if isinstance(value, dict):
            for key, item in value.items():
                if key in forbidden and item not in (None, [], {}, ""):
                    return True
                if key_leaked(item):
                    return True
        elif isinstance(value, list):
            return any(key_leaked(item) for item in value)
        return False

    if any(key_leaked(row.get("training_packets", [])) for row in arms):
        errors.append("test_answer_key_leakage")
    training_tasks = {row.get("task_key") for arm in arms
                      for row in arm.get("training_packets", [])}
    if plan.get("heldout_transfer_task") in training_tasks:
        errors.append("transfer_task_not_held_out")
    return {"valid": not errors, "errors": sorted(set(errors))}


def score_takeover(observed_state, answer, expected_next_safe_step):
    return {"state_correct": answer.get("theme") == observed_state.get("theme") and
            answer.get("save_status") == observed_state.get("save_status"),
            "next_step_correct": answer.get("next_safe_step") == expected_next_safe_step}


def score_vigilance(trials):
    counts = {"hits": 0, "misses": 0, "false_alarms": 0,
              "correct_rejections": 0}
    for row in trials:
        anomaly, reported = row["anomaly"], row["reported"]
        if anomaly and reported:
            counts["hits"] += 1
        elif anomaly:
            counts["misses"] += 1
        elif reported:
            counts["false_alarms"] += 1
        else:
            counts["correct_rejections"] += 1
    return counts


def sample_size_rationale(effect_size_sd):
    if effect_size_sd <= 0:
        raise ValueError("unsupported planning inputs")
    # Normal approximation: four co-primary contrasts, Bonferroni alpha=.0125,
    # two-sided z_alpha/2 ~= 2.498 and 80% power z ~= .842 (sum rounded to 3.34).
    complete = ceil(2 * 3.34 ** 2 / effect_size_sd ** 2)
    recruited = ceil(complete / 0.85)
    return {"assumed_standardized_effect": effect_size_sd,
            "completers_per_arm": complete,
            "recruited_per_arm_at_15pct_attrition": recruited,
            "total_recruited_three_arms": recruited * 3,
            "status": "planning_assumption_only"}
