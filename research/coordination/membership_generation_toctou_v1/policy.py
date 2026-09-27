from __future__ import annotations

def validate_membership(membership: dict, confirmations: dict) -> bool:
    members = sorted(membership["members"])
    return (
        confirmations["membership_epoch"] == membership["membership_epoch"]
        and sorted(confirmations["members"]) == members
        and sorted(confirmations["confirmed"]) == members
    )

def split_transition(coordination: dict) -> dict:
    if coordination != {"active_generation": 1}:
        raise ValueError("unexpected coordination state")
    return {"active_generation": 2}

def unified_transition(state: dict) -> dict:
    if state["active_generation"] != 1:
        raise ValueError("unexpected generation")
    out = dict(state)
    out["active_generation"] = 2
    return out
