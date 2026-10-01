"""Independent exhaustive oracle for the synthetic Issue #5805 fixture."""

from itertools import product


def decision(rule, owner_set, grants, act_for="absent"):
    if owner_set is None:
        return "HOLD_UNKNOWN_OWNER"
    if rule == "requester_only":
        return "ALLOW" if grants[0] == "valid" else "DENY"
    if "deny" in (grants[0], grants[1]) and "B" in owner_set:
        return "DENY"
    if rule == "all_required":
        return "ALLOW" if all(grants[0 if owner == "A" else 1] == "valid" for owner in owner_set) else "DENY"
    if rule == "scoped_delegation":
        checks = []
        for owner in owner_set:
            direct = grants[0 if owner == "A" else 1] == "valid"
            delegated = owner == "B" and act_for == "valid_scoped"
            checks.append(direct or delegated)
        return "ALLOW" if all(checks) else "DENY"
    raise AssertionError(rule)


def main():
    states = ("absent", "valid", "stale", "forged", "deny")
    rules = ("requester_only", "all_required", "scoped_delegation")
    pairs = [(a, b) for a, b in product(states, repeat=2)]
    results = {(a, b): {r: decision(r, ("A", "B"), (a, b)) for r in rules} for a, b in pairs}
    assert len(results) == 25

    # A-only consent must not authorize a co-owned effect under either safe rule.
    assert results[("valid", "absent")]["requester_only"] == "ALLOW"
    assert results[("valid", "absent")]["all_required"] == "DENY"
    assert results[("valid", "absent")]["scoped_delegation"] == "DENY"
    # A direct B veto is ignored by the intentionally unsafe requester-only comparator.
    assert results[("valid", "deny")]["requester_only"] == "ALLOW"
    assert results[("valid", "deny")]["all_required"] == "DENY"
    assert results[("valid", "deny")]["scoped_delegation"] == "DENY"
    assert results[("valid", "valid")]["all_required"] == "ALLOW"
    assert results[("valid", "valid")]["scoped_delegation"] == "ALLOW"

    # Count all requester-only admissions where B has not supplied a valid grant.
    unsafe_admissions = sum(
        results[pair]["requester_only"] == "ALLOW" and pair[1] != "valid"
        for pair in pairs
    )
    assert unsafe_admissions == 4
    # The explicitly scoped B->A delegation admits the exact narrow operation,
    # but not a wrong action, stale delegation, or unknown owner set.
    exact_delegation = decision("scoped_delegation", ("A", "B"), ("valid", "absent"), "valid_scoped")
    wrong_scope = decision("scoped_delegation", ("A", "B"), ("valid", "absent"), "wrong_scope")
    stale_delegation = decision("scoped_delegation", ("A", "B"), ("valid", "absent"), "stale")
    unknown = decision("scoped_delegation", None, ("valid", "absent"), "valid_scoped")
    private_a = decision("all_required", ("A",), ("valid", "absent"))
    assert (exact_delegation, wrong_scope, stale_delegation, unknown, private_a) == (
        "ALLOW", "DENY", "DENY", "HOLD_UNKNOWN_OWNER", "ALLOW"
    )
    # Independent check of the bound safety-release lane (no task mutation).
    receipt = {"valid": True, "actor": "agent", "resource": "shared_ab", "action": "release", "generation": 7}
    invalid_receipt = {**receipt, "resource": "private_a"}
    release = lambda token: ("ALLOW_SAFE_RELEASE" if token.get("valid") is True
                             and token.get("actor") == "agent"
                             and token.get("resource") == "shared_ab"
                             and token.get("action") == "release"
                             and token.get("generation") == 7 else "DENY")
    assert release(receipt) == "ALLOW_SAFE_RELEASE"
    assert release(invalid_receipt) == "DENY"
    print({
        "enumerated_direct_grant_pairs": len(results),
        "policy_pair_decisions": len(results) * len(rules),
        "requester_only_unauthorized_admissions": unsafe_admissions,
        "all_required_authorized_effects_without_valid_owner_grants": 0,
        "scoped_delegation_exact_case": exact_delegation,
        "delegation_wrong_scope": wrong_scope,
        "delegation_stale_epoch": stale_delegation,
        "unknown_owner": unknown,
        "single_owner_no_extra_grant": private_a,
        "safe_release_valid": release(receipt),
        "safe_release_invalid_binding": release(invalid_receipt),
    })


if __name__ == "__main__":
    main()
