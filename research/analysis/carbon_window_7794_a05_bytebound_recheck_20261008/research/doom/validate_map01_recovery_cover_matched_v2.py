from __future__ import annotations

import argparse
import json
from pathlib import Path

REQUIRED_TOP = {
    "schema",
    "base_commit",
    "task_id",
    "allocation_id",
    "status",
    "objective",
    "supersedes_construction",
    "forbidden_reuse",
    "required_dependencies",
    "arms",
    "matched_constraints",
    "required_instrumentation",
    "recovery_authority",
    "primary_metrics",
    "hard_gates",
    "exposure_gate",
    "decision_rule",
    "execution_policy",
    "product_hunt_claim_boundary",
}

TRUE_MATCHED = {
    "same_initial_fixture",
    "same_seed_schedule",
    "same_model",
    "same_model_prompt_schema",
    "same_resolution",
    "same_game_speed",
    "same_observation_path",
    "same_input_backend",
    "same_release_telemetry",
    "same_independent_scorer",
    "same_planner_timeout",
}

TRUE_AUTHORITY = {
    "must_be_explicit",
    "must_bind_source_observation",
    "must_have_observable_guard",
    "must_have_expiry",
    "must_cancel_on_guard_failure",
    "must_cancel_on_source_staleness",
    "must_not_rebase_budget_silently",
    "must_verify_empty_release",
}

TRUE_EXECUTION = {
    "one_run_per_allocation",
    "no_retry_same_allocation",
    "retain_first_outcome",
    "do_not_overwrite_results",
    "live_execution_requires_separate_formal_lease",
    "runner_implementation_requires_separate_write_lease",
    "workflow_integration_requires_new_versioned_path",
}


def validate(plan: dict) -> None:
    missing = REQUIRED_TOP - set(plan)
    if missing:
        raise AssertionError(f"missing top-level fields: {sorted(missing)}")

    assert plan["schema"] == "map01-recovery-cover-matched-v2-prereg"
    assert plan["status"] == "FROZEN_CONSTRUCTION_ONLY_NO_LIVE_LEASE"
    assert plan["allocation_id"] not in set(plan["forbidden_reuse"])

    supersedes = plan["supersedes_construction"]
    assert supersedes["pr"] == 74
    assert supersedes["schema"] == "map01-recovery-cover-matched-v1-prereg"

    deps = plan["required_dependencies"]
    mechanics = deps["measurement_mechanics"]
    assert mechanics["terminal_score_audit_required"] is True
    assert mechanics["status"] == "REPLICATED_2_OF_2_BUT_PRIOR_FORMAL_ALLOCATION_INVALID"
    single = deps["single_execution"]
    assert single["launch_owner_required"] is True
    assert single["external_non_cancelling_serialization_required"] is True
    assert single["cancel_in_progress"] is False
    assert single["formal_step_requires_canonical_owner"] is True

    assert [arm["name"] for arm in plan["arms"]] == ["COAST_CONTROL", "BOUNDED_RECOVERY"]
    assert plan["arms"][0]["input_authority"] == "none"
    assert plan["arms"][1]["input_authority"] == "separately_admitted_bounded_program"

    matched = plan["matched_constraints"]
    for key in TRUE_MATCHED:
        assert matched[key] is True, key
    assert matched["arm_difference_only"] == "planner_wait_fallback"

    instrumentation = plan["required_instrumentation"]
    assert instrumentation["controller_visible_privileged_scorer_events"] is False
    for key in (
        "planner_wait_intervals",
        "direct_retained_input_bounds",
        "release_transition_receipts",
        "independent_progress_samples",
        "terminal_score_agreement",
        "same_monotonic_clock_or_explicit_mapping",
        "launch_owner_receipt",
    ):
        assert instrumentation[key] is True, key

    authority = plan["recovery_authority"]
    for key in TRUE_AUTHORITY:
        assert authority[key] is True, key
    assert 0 < int(authority["max_single_lease_ms"]) <= 1500

    gates = plan["hard_gates"]
    assert gates == {
        "formal_run_count_for_allocation": 1,
        "launch_owner_result": "PASS_CANONICAL_OWNER",
        "terminal_score_agreement": True,
        "stale_authority_admissions": 0,
        "release_failures": 0,
        "controller_visible_privileged_scorer_events": 0,
        "all_accepted_programs_have_terminal_release": True,
    }

    exposure = plan["exposure_gate"]
    assert exposure["recovery_interval_with_acknowledged_input_before_planner_completion_required"] is True
    assert exposure["matched_planner_wait_interval_required"] is True

    assert set(plan["decision_rule"]) == {
        "PASS",
        "HOLD_MECHANISM_ONLY",
        "FAIL",
        "UNCERTAIN",
        "HOLD",
    }

    execution = plan["execution_policy"]
    for key in TRUE_EXECUTION:
        assert execution[key] is True, key
    assert execution["results_path"].endswith(plan["allocation_id"])

    boundary = plan["product_hunt_claim_boundary"]
    assert boundary["allowed_only_if_PASS"]
    assert boundary["allowed_if_HOLD_MECHANISM_ONLY"]
    forbidden = set(boundary["forbidden"])
    assert "human-level reaction time" in forbidden
    assert "general speedup" in forbidden


def synthetic_fail_closed_checks(plan: dict) -> None:
    gates = plan["hard_gates"]
    passing = dict(gates)
    assert passing == gates
    negatives = {
        "formal_run_count_for_allocation": 2,
        "launch_owner_result": "FAIL_NOT_CANONICAL_OWNER",
        "terminal_score_agreement": False,
        "stale_authority_admissions": 1,
        "release_failures": 1,
        "controller_visible_privileged_scorer_events": 1,
        "all_accepted_programs_have_terminal_release": False,
    }
    for key, bad in negatives.items():
        sample = dict(passing)
        sample[key] = bad
        assert sample != gates, key


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    plan = json.loads(args.path.read_text(encoding="utf-8"))
    validate(plan)
    synthetic_fail_closed_checks(plan)
    print(json.dumps({
        "schema": plan["schema"],
        "allocation_id": plan["allocation_id"],
        "decision": "PASS construction validation",
        "formal_live_authority": False,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
