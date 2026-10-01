import candidate


def test_private_and_passive_modes_preserve_shared_interaction_invariants():
    result = candidate.run()
    for name in ("no_cue", "model_only", "shared_passive"):
        assert result["controls"][name]["decision"] == "METHOD_PASS_SCOPED"
    assert result["model_only_shared_state_unchanged"]
    assert result["passive_overlay_has_no_interaction_delta"]


def test_intrusive_negative_control_is_detected():
    result = candidate.run()
    item = result["controls"]["shared_intrusive_negative_control"]
    assert item["decision"] == "FAIL_NONINTERFERENCE"
    assert len(item["violations"]) == len(candidate.DIMENSIONS)


def test_unobservable_assistive_technology_surface_is_hold_not_pass():
    result = candidate.run()
    assert result["controls"]["at_backend_unavailable"]["decision"] == "HOLD_AT_ORACLE_UNAVAILABLE"


def test_exhaustive_single_and_multi_axis_fault_injection():
    result = candidate.run()
    assert result["profile_count"] == 2 ** len(candidate.DIMENSIONS) == 512
    decisions = {row["mutation_mask"]: row["decision"] for row in result["mutation_profiles"]}
    assert decisions[0] == "METHOD_PASS_SCOPED"
    assert all(decisions[mask] == "FAIL_NONINTERFERENCE" for mask in range(1, 512))
