"""Independent raw-row oracle; deliberately does not import candidate protocol.py."""
from math import ceil


def score_attempt(required, target_state, row):
    if row is None:
        return {"status": "missing", "step_score": None, "severity": "unknown",
                "critical_error": False, "active_seconds": None,
                "elapsed_seconds": None}
    observed = row.get("actions", [])
    matches = sum(i < len(observed) and observed[i] == step
                  for i, step in enumerate(required))
    fraction = matches / len(required) if required else 0.0
    if row.get("target") != "disposable-profile":
        state, severity, critical = "critical_error", "critical", True
    elif len(observed) == len(required) and all(
            actual == expected for actual, expected in zip(observed, required)) and \
            row.get("final_state") == target_state:
        state, severity, critical = "complete", "none", False
    else:
        state, severity, critical = "incomplete", "major", False
    return {"status": state, "step_score": fraction, "severity": severity,
            "critical_error": critical,
            "active_seconds": row.get("active_seconds"),
            "elapsed_seconds": row.get("elapsed_seconds")}


def audit_plan(plan):
    errors = []
    arms = plan.get("arms", [])
    expected_names = {"manual", "automation_only", "automation_retrieval"}
    labels = [arm.get("arm") for arm in arms]
    if set(labels) != expected_names or len(labels) != len(expected_names):
        errors.append("arm_set_invalid")
    n = plan.get("opportunities_per_arm")
    wanted = list(range(1, n + 1)) if isinstance(n, int) and not isinstance(n, bool) else []
    for arm in arms:
        if arm.get("opportunities") != wanted:
            errors.append("opportunity_count_mismatch")
        if arm.get("reset_each_opportunity") is not True:
            errors.append("opportunity_reset_missing")
        packets = arm.get("training_packets", [])
        if [packet.get("opportunity") for packet in packets] != wanted:
            errors.append("training_packet_count_mismatch")
        if any(packet.get("task_key") != arm.get("task_version")
               for packet in packets):
            errors.append("training_task_version_mismatch")
    for field, code in (("task_version", "task_exposure_mismatch"),
                        ("starting_state_source", "starting_state_mismatch"),
                        ("goal_card", "task_goal_mismatch"),
                        ("interface_evidence_version", "evidence_access_mismatch")):
        if len({arm.get(field) for arm in arms}) > 1:
            errors.append(code)
    by_name = {arm.get("arm"): arm for arm in arms}
    manual = by_name.get("manual", {})
    automatic = by_name.get("automation_only", {})
    retrieval = by_name.get("automation_retrieval", {})
    if manual.get("retrieval_prompts") != [] or automatic.get("retrieval_prompts") != []:
        errors.append("unexpected_retrieval_prompt")
    prompts = retrieval.get("retrieval_prompts", [])
    if [item.get("opportunity") for item in prompts] != [2, 4, 6]:
        errors.append("retrieval_schedule_invalid")
    if any(item.get("before_agent_action") is not True or
           item.get("before_feedback") is not True or
           item.get("allow_unsure") is not True for item in prompts):
        errors.append("retrieval_prompt_timing_invalid")

    blocked = {"delayed_test_scoring_key", "heldout_transfer_answer_key",
               "test_answer_key", "scoring_rubric_key"}

    def leaked(value):
        if isinstance(value, dict):
            for key, child in value.items():
                if key in blocked and child not in (None, "", [], {}):
                    return True
                if leaked(child):
                    return True
        elif isinstance(value, (tuple, list)):
            return any(leaked(child) for child in value)
        return False

    if any(leaked(arm.get("training_packets", [])) for arm in arms):
        errors.append("test_answer_key_leakage")
    train_keys = {packet.get("task_key") for arm in arms
                  for packet in arm.get("training_packets", [])}
    if plan.get("heldout_transfer_task") in train_keys:
        errors.append("transfer_task_not_held_out")
    return {"valid": not errors, "errors": sorted(set(errors))}


def sample_size(effect_sd):
    if effect_sd <= 0:
        return None
    n = ceil(2 * 3.34 ** 2 / effect_sd ** 2)
    return ceil(n / 0.85)


def score_takeover(observed, response, expected_next):
    checks = (observed.get("theme") == response.get("theme"),
              observed.get("save_status") == response.get("save_status"))
    return {"state_correct": all(checks),
            "next_step_correct": response.get("next_safe_step") == expected_next}


def score_vigilance(trials):
    truth_positive = [row for row in trials if row.get("anomaly") is True]
    truth_negative = [row for row in trials if row.get("anomaly") is False]
    return {
        "hits": sum(row.get("reported") is True for row in truth_positive),
        "misses": sum(row.get("reported") is False for row in truth_positive),
        "false_alarms": sum(row.get("reported") is True for row in truth_negative),
        "correct_rejections": sum(row.get("reported") is False for row in truth_negative),
    }
