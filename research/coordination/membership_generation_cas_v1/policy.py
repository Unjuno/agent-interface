def confirm_decision(membership, confirmation):
    if confirmation.get("membership_epoch") != membership.get("membership_epoch"):
        return "HOLD_MEMBERSHIP_CHANGED"
    if confirmation.get("members") != membership.get("members"):
        return "HOLD_MEMBERSHIP_CHANGED"
    receipts = confirmation.get("receipts", [])
    receipt_members = [r.get("receiver") for r in receipts]
    if receipt_members != membership.get("members"):
        return "HOLD_NOT_ALL_CONFIRMED"
    if any(r.get("status") != "CONFIRMED" for r in receipts):
        return "HOLD_NOT_ALL_CONFIRMED"
    return "ALL_CONFIRMED"


def canonical_membership(record):
    return {
        "membership_epoch": record["membership_epoch"],
        "members": record["members"],
    }
