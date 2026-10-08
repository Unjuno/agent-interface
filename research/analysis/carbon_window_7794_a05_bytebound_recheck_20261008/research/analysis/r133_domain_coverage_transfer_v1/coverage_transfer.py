"""Keep cross-domain evidence coverage as an axis-by-axis vector."""


def build_coverage(physical_result, occupancy_summary, feedback_summary, calc_result):
    """Normalize supplied evidence without imputing missing measurements."""
    formal = physical_result["formal"]
    physical_consistent = (
        physical_result.get("decision") == "PASS_MAP01_V12_PHYSICAL_OCCUPANCY_R1_SCOPED"
        and formal.get("sessions_completed") == formal.get("sessions_pass") == 3
        and formal.get("actuations") == 6
        and formal.get("all_precision_pass") is True
        and formal.get("all_owned_after_empty") is True
        and formal.get("all_post_sample_up") is True
        and formal.get("all_terminal_completed") is True
        and formal.get("all_errors_empty") is True
    )
    physical_axis = {
        "status": "MEASURED_BOUNDED" if physical_consistent else "INCONSISTENT_SOURCE_EVIDENCE",
        "scope": "XTEST_OWNER_BRACKETS",
        "paired_actuation_edges": formal.get("actuations"),
        "max_censor_width_ms": formal.get("max_censor_width_ms"),
        "continuous_map01_occupancy_duration_measured": False,
    }

    runs = occupancy_summary["runs"]
    normalized_runs = {}
    for source_key, key in (("map01-v38-integrated-threat-live-01", "v38"),
                            ("map01-v39-coast-liveness-live-01", "v39")):
        run = runs[source_key]
        normalized_runs[key] = {
            "hold_steps": run["hold_steps"],
            "lower_ms": run["physical_any_key_occupancy_lower_ms"],
            "upper_ms": run["physical_any_key_occupancy_upper_ms"],
            "interval_width_ms": run["occupancy_interval_width_ms"],
            "precision_gate_passed": run["informative_enough_for_next_matched_metric"],
        }

    plans = feedback_summary["plans"]
    state_feedback = sum(bool(plan["earliest_state_feedback"]) for plan in plans)
    task_effects = sum(bool(plan["stronger_task_effect_feedback"]) for plan in plans)
    feedback_status = (
        "PARTIAL_STATE_FEEDBACK_ONLY"
        if state_feedback and not task_effects
        else "INCONSISTENT_SOURCE_EVIDENCE"
    )

    rows = calc_result["rows"]
    calc_release_only = bool(rows) and all(row.get("release_verified") is True for row in rows)
    saved_correct = sum(row.get("saved_correct") is True for row in rows)
    extra = sum(row.get("extra_observations", 0) for row in rows)
    calc_domain = {
        "held_input_occupancy": {
            "status": "RELEASE_ONLY" if calc_release_only else "INCONSISTENT_SOURCE_EVIDENCE",
            "duration_measured": False,
        },
        "task_outcome": {
            "status": "SAVED_OUTPUT_VERIFIED_UNTIMED" if saved_correct == len(rows) else "INCONSISTENT_SOURCE_EVIDENCE",
            "verified_rows": saved_correct,
            "rows": len(rows),
        },
        "useful_feedback": {
            "status": "OBSERVATION_COUNT_ONLY",
            "extra_observations": extra,
            "first_useful_time_identifiable": False,
        },
    }
    return {
        "schema": "r133-domain-coverage-vector-v1",
        "domains": {
            "doom_physical_r1": {"held_input_occupancy": physical_axis},
            "doom_v38_v39": {
                "held_input_occupancy": {"status": "INTERVAL_CENSORED", "runs": normalized_runs},
                "useful_feedback": {
                    "status": feedback_status,
                    "plans_with_state_feedback": state_feedback,
                    "admitted_plans": len(plans),
                    "plan_bound_task_effects": task_effects,
                },
            },
            "calc_final_wait": calc_domain,
        },
    }


def audit_coverage(result, physical_result, occupancy_summary, feedback_summary, calc_result):
    """Check critical classifications against independent source predicates."""
    domains = result.get("domains", {})
    errors = []
    if "overall_coverage_score" in result:
        errors.append("scalar_promotion_forbidden")

    calc_axis = domains.get("calc_final_wait", {}).get("held_input_occupancy", {})
    if calc_axis.get("duration_measured") is not False or calc_axis.get("status") != "RELEASE_ONLY":
        errors.append("calc_duration_not_identifiable")

    feedback_axis = domains.get("doom_v38_v39", {}).get("useful_feedback", {})
    observed_effects = sum(bool(plan.get("stronger_task_effect_feedback")) for plan in feedback_summary["plans"])
    if feedback_axis.get("plan_bound_task_effects") != observed_effects:
        errors.append("task_effect_count_mismatch")

    runs = occupancy_summary["runs"]
    run_axis = domains.get("doom_v38_v39", {}).get("held_input_occupancy", {}).get("runs", {})
    for source_key, key in (("map01-v38-integrated-threat-live-01", "v38"),
                            ("map01-v39-coast-liveness-live-01", "v39")):
        expected = runs[source_key]["informative_enough_for_next_matched_metric"]
        actual = run_axis.get(key, {}).get("precision_gate_passed")
        if actual is not expected:
            errors.append("occupancy_gate_mismatch:" + key)

    formal = physical_result["formal"]
    physical = domains.get("doom_physical_r1", {}).get("held_input_occupancy", {})
    physical_ok = (
        formal.get("all_post_sample_up") is True
        and formal.get("all_terminal_completed") is True
        and formal.get("all_errors_empty") is True
    )
    if physical_ok and physical.get("status") != "MEASURED_BOUNDED":
        errors.append("physical_classification_mismatch")
    return {"passed": not errors, "errors": errors}
