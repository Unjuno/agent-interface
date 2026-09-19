from __future__ import annotations
import json
from pathlib import Path

REQUIRED_TOP = {
    "schema", "base_commit", "task_id", "status", "objective", "arms",
    "matched_constraints", "required_instrumentation", "recovery_authority",
    "primary_metrics", "hard_gates", "decision_rule", "execution_policy",
    "product_hunt_claim_boundary"
}


def validate(plan: dict) -> None:
    missing = REQUIRED_TOP - set(plan)
    if missing:
        raise AssertionError(f"missing top-level fields: {sorted(missing)}")
    assert plan["schema"] == "map01-recovery-cover-matched-v1-prereg"
    assert plan["status"] == "FROZEN_CONSTRUCTION_ONLY_NO_LIVE_LEASE"
    assert len(plan["arms"]) == 2
    assert [a["name"] for a in plan["arms"]] == ["COAST_CONTROL", "BOUNDED_RECOVERY"]
    mc = plan["matched_constraints"]
    for key in (
        "same_initial_fixture", "same_map_seed_schedule", "same_model",
        "same_model_prompt_schema", "same_resolution", "same_game_speed",
        "same_observation_path", "same_input_backend",
        "same_independent_scorer_contract", "same_release_telemetry_contract"
    ):
        assert mc[key] is True, key
    assert mc["arm_difference_only"] == "planner_wait_fallback"
    ins = plan["required_instrumentation"]
    assert ins["controller_visible_scorer_events"] is False
    assert ins["same_monotonic_clock_or_explicit_mapping"] is True
    auth = plan["recovery_authority"]
    for key in (
        "must_be_explicit", "must_have_expiry", "must_have_observable_guard",
        "must_bind_source_observation", "must_not_rebase_budget_silently",
        "must_cancel_on_guard_failure", "must_verify_empty_release"
    ):
        assert auth[key] is True, key
    assert 0 < auth["max_single_lease_ms"] <= 2000
    gates = plan["hard_gates"]
    assert gates["stale_authority_admissions"] == 0
    assert gates["release_failures"] == 0
    assert gates["controller_visible_privileged_scorer_events"] == 0
    assert gates["all_accepted_programs_have_terminal_release"] is True
    ep = plan["execution_policy"]
    assert ep["no_retry_same_allocation"] is True
    assert ep["retain_first_outcome"] is True
    assert ep["do_not_overwrite_results"] is True
    assert ep["live_execution_requires_separate_formal_lease"] is True
    assert set(plan["decision_rule"]) == {"PASS", "FAIL", "UNCERTAIN", "HOLD"}


def synthetic_gate_checks(plan: dict) -> None:
    hard = plan["hard_gates"]
    passing = {
        "stale_authority_admissions": 0,
        "release_failures": 0,
        "controller_visible_privileged_scorer_events": 0,
        "all_accepted_programs_have_terminal_release": True,
    }
    assert all(passing[k] == v for k, v in hard.items())
    for bad_key, bad_value in (
        ("stale_authority_admissions", 1),
        ("release_failures", 1),
        ("controller_visible_privileged_scorer_events", 1),
        ("all_accepted_programs_have_terminal_release", False),
    ):
        sample = dict(passing)
        sample[bad_key] = bad_value
        assert any(sample[k] != v for k, v in hard.items())


def main(path: str) -> None:
    plan = json.loads(Path(path).read_text(encoding="utf-8"))
    validate(plan)
    synthetic_gate_checks(plan)
    print("PASS prereg schema + fail-closed gate checks")


if __name__ == "__main__":
    import sys
    main(sys.argv[1])
