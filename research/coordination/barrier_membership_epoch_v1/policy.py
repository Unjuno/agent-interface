def classify_batch(current_membership, batch):
    current_members = list(current_membership["members"])
    if batch["membership_epoch"] != current_membership["epoch"]:
        return {"decision": "HOLD_MEMBERSHIP_CHANGED", "advance": False}
    if list(batch["members"]) != current_members:
        return {"decision": "HOLD_MEMBERSHIP_CHANGED", "advance": False}
    receipts = list(batch["receipts"])
    ids = [r["receiver"] for r in receipts]
    if len(ids) != len(set(ids)) or sorted(ids) != sorted(current_members):
        return {"decision": "HOLD_INCOMPLETE", "advance": False}
    if any(r.get("status") != "CONFIRMED" for r in receipts):
        return {"decision": "HOLD_NOT_CONFIRMED", "advance": False}
    return {"decision": "ALL_CONFIRMED", "advance": True}
