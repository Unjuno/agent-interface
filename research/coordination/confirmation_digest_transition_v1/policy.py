def confirmation_identity(document):
    return (document["content_id"], int(document["revision"]))


def classify(canonical, confirmation):
    if int(canonical["membership_epoch"]) != int(confirmation["membership_epoch"]):
        return "HOLD_MEMBERSHIP_CHANGED"
    if list(canonical["members"]) != list(confirmation["members"]):
        return "HOLD_MEMBERSHIP_CHANGED"
    expected_content = canonical.get("confirmation_content_id")
    expected_revision = canonical.get("confirmation_revision")
    if expected_content is not None:
        if expected_content != confirmation["content_id"]:
            return "HOLD_CONFIRMATION_CHANGED"
        if int(expected_revision) != int(confirmation["revision"]):
            return "HOLD_CONFIRMATION_CHANGED"
    receipts = confirmation["receipts"]
    if [r["receiver"] for r in receipts] != list(canonical["members"]):
        return "HOLD_CONFIRMATION_CHANGED"
    if any(r["status"] != "CONFIRMED" for r in receipts):
        return "HOLD_CONFIRMATION_CHANGED"
    return "ALL_CONFIRMED"
