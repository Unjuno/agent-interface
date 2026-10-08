"""Synthetic T0 policy fixture for Issue #5805. No external authorization."""

from __future__ import annotations

from itertools import product


GRANT_STATES = ("absent", "valid", "stale", "forged", "deny")
POLICIES = ("requester_only", "all_required", "scoped_delegation")
OWNERS = {"private_a": ("A",), "shared_ab": ("A", "B"), "unknown": None}
RELEASE_BINDING = {"actor": "agent", "resource": "shared_ab", "action": "release", "generation": 7}


def valid_grant(state: str) -> bool:
    return state == "valid"


def decide(policy: str, owners: tuple[str, ...] | None, grants: dict[str, str],
           delegation: str = "absent") -> str:
    if owners is None:
        return "HOLD_UNKNOWN_OWNER"
    if policy == "requester_only":
        return "ALLOW" if valid_grant(grants.get("A", "absent")) else "DENY"
    if any(grants.get(owner, "absent") == "deny" for owner in owners):
        return "DENY"
    if policy == "all_required":
        return "ALLOW" if all(valid_grant(grants.get(owner, "absent")) for owner in owners) else "DENY"
    if policy == "scoped_delegation":
        return "ALLOW" if all(
            valid_grant(grants.get(owner, "absent")) or
            (owner == "B" and delegation == "valid_scoped")
            for owner in owners
        ) else "DENY"
    raise ValueError(policy)


def release_decision(receipt: dict) -> str:
    if receipt.get("valid") is True and all(receipt.get(k) == v for k, v in RELEASE_BINDING.items()):
        return "ALLOW_SAFE_RELEASE"
    return "DENY"


def run():
    pair_rows = []
    for a_state, b_state in product(GRANT_STATES, repeat=2):
        grants = {"A": a_state, "B": b_state}
        pair_rows.append({"A": a_state, "B": b_state,
                          **{p: decide(p, OWNERS["shared_ab"], grants) for p in POLICIES}})
    scenarios = {
        "private_a_valid": {"owners": OWNERS["private_a"], "grants": {"A": "valid", "B": "absent"}},
        "shared_joint_valid": {"owners": OWNERS["shared_ab"], "grants": {"A": "valid", "B": "valid"}},
        "shared_only_a": {"owners": OWNERS["shared_ab"], "grants": {"A": "valid", "B": "absent"}},
        "shared_b_veto": {"owners": OWNERS["shared_ab"], "grants": {"A": "valid", "B": "deny"}},
        "shared_b_stale": {"owners": OWNERS["shared_ab"], "grants": {"A": "valid", "B": "stale"}},
        "shared_b_forged": {"owners": OWNERS["shared_ab"], "grants": {"A": "valid", "B": "forged"}},
        "unknown_owner": {"owners": OWNERS["unknown"], "grants": {"A": "valid"}},
        "delegation_exact": {"owners": OWNERS["shared_ab"], "grants": {"A": "valid", "B": "absent"}, "delegation": "valid_scoped"},
        "delegation_wrong_action": {"owners": OWNERS["shared_ab"], "grants": {"A": "valid", "B": "absent"}, "delegation": "wrong_scope"},
        "delegation_stale_epoch": {"owners": OWNERS["shared_ab"], "grants": {"A": "valid", "B": "absent"}, "delegation": "stale"},
    }
    decisions = {}
    for name, case in scenarios.items():
        decisions[name] = {p: decide(p, case["owners"], case["grants"], case.get("delegation", "absent"))
                           for p in POLICIES}
    valid_receipt = {"valid": True, **RELEASE_BINDING}
    invalid_receipt = {"valid": True, **RELEASE_BINDING, "resource": "private_a"}
    emergency = {p: release_decision(valid_receipt) for p in POLICIES}
    return {"grant_state_pairs": pair_rows, "scenarios": decisions,
            "valid_emergency_release": emergency,
            "invalid_emergency_release": {p: release_decision(invalid_receipt) for p in POLICIES},
            "pair_count": len(pair_rows)}


if __name__ == "__main__":
    import json
    print(json.dumps(run(), indent=2, sort_keys=True))
