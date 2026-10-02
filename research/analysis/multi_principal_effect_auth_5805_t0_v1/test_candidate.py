import candidate


def test_all_owner_policy_blocks_single_requester_and_veto_cases():
    output = candidate.run()
    scenarios = output["scenarios"]
    assert scenarios["shared_only_a"]["requester_only"] == "ALLOW"
    assert scenarios["shared_only_a"]["all_required"] == "DENY"
    assert scenarios["shared_only_a"]["scoped_delegation"] == "DENY"
    assert scenarios["shared_b_veto"]["requester_only"] == "ALLOW"
    assert scenarios["shared_b_veto"]["all_required"] == "DENY"
    assert scenarios["shared_b_veto"]["scoped_delegation"] == "DENY"


def test_valid_joint_grants_and_exact_delegation_preserve_progress():
    output = candidate.run()
    assert set(output["scenarios"]["shared_joint_valid"].values()) == {"ALLOW"}
    assert output["scenarios"]["delegation_exact"]["scoped_delegation"] == "ALLOW"
    assert output["scenarios"]["delegation_exact"]["all_required"] == "DENY"


def test_stale_forged_unknown_and_out_of_scope_authority_fail_closed():
    output = candidate.run()
    for name in ("shared_b_stale", "shared_b_forged", "unknown_owner", "delegation_wrong_action", "delegation_stale_epoch"):
        assert output["scenarios"][name]["all_required"] != "ALLOW"
        assert output["scenarios"][name]["scoped_delegation"] != "ALLOW"
    assert output["scenarios"]["unknown_owner"]["scoped_delegation"] == "HOLD_UNKNOWN_OWNER"


def test_single_owner_does_not_require_unrelated_owner_and_release_bypasses_mutation_grants():
    output = candidate.run()
    assert set(output["scenarios"]["private_a_valid"].values()) == {"ALLOW"}
    assert set(output["valid_emergency_release"].values()) == {"ALLOW_SAFE_RELEASE"}
    assert set(output["invalid_emergency_release"].values()) == {"DENY"}


def test_all_25_direct_grant_pairs_are_enumerated_and_safe_rules_are_fail_closed():
    output = candidate.run()
    assert output["pair_count"] == 25
    for row in output["grant_state_pairs"]:
        if row["A"] == "valid" and row["B"] != "valid":
            assert row["all_required"] == "DENY"
            assert row["scoped_delegation"] == "DENY"
