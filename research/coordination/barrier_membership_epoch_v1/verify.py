import json
from pathlib import Path

from policy import classify_batch

ROOT = Path(__file__).resolve().parent


def load(name):
    return json.loads((ROOT / name).read_text())


stable_membership = load("membership_stable.json")
stable_batch = load("confirm_stable.json")
added_membership = load("membership_added.json")
added_batch = load("confirm_added.json")
replaced_membership = load("membership_replaced.json")
replaced_batch = load("confirm_replaced.json")
coord_stable = load("coord_stable.json")
coord_added = load("coord_added.json")
coord_replaced = load("coord_replaced.json")
result = load("result.json")

assert classify_batch(stable_membership, stable_batch) == {
    "decision": "ALL_CONFIRMED",
    "advance": True,
}
assert classify_batch(added_membership, added_batch) == {
    "decision": "HOLD_MEMBERSHIP_CHANGED",
    "advance": False,
}

old_replaced = {
    "membership_epoch": result["cases"]["member_replaced"]["old_confirmation"]["membership_epoch"],
    "members": result["cases"]["member_replaced"]["old_confirmation"]["members"],
    "receipts": [
        {"receiver": r, "status": "CONFIRMED"}
        for r in result["cases"]["member_replaced"]["old_confirmation"]["receivers"]
    ],
}
assert classify_batch(replaced_membership, old_replaced) == {
    "decision": "HOLD_MEMBERSHIP_CHANGED",
    "advance": False,
}
assert classify_batch(replaced_membership, replaced_batch) == {
    "decision": "ALL_CONFIRMED",
    "advance": True,
}

assert coord_stable["active_generation"] == 2
assert coord_added["active_generation"] == 1
assert coord_replaced["active_generation"] == 2
assert result["decision"] == "PASS_MEMBERSHIP_BOUND_ALL_CONFIRMED_SCOPED"
assert result["totals"]["coordination_advances_from_stale_membership"] == 0
assert result["totals"]["retired_receiver_required_after_current_membership_confirmation"] is False

print("PASS_MEMBERSHIP_BOUND_ALL_CONFIRMED_SCOPED")
