"""Fail-closed audit for acknowledged producer refresh intervals."""


SUCCESS_STATUS = "REFRESH_RETURNED_RUNTIME_QUALIFICATION_PENDING"


def audit_refresh(row):
    """Require one actual episode-tic edge and a stable score-read boundary."""
    if not isinstance(row, dict) or row.get("status") != SUCCESS_STATUS:
        return {"qualified": False, "reason": "refresh_not_returned"}
    before = row.get("tic_before")
    after = row.get("tic_after")
    after_read = row.get("tic_after_read")
    if any(type(value) is not int or value < 0 for value in (before, after, after_read)):
        return {"qualified": False, "reason": "missing_or_invalid_tic_ack"}
    if after != before + 1:
        return {"qualified": False, "reason": "tic_did_not_advance_exactly_one"}
    if after_read != after:
        return {"qualified": False, "reason": "tic_changed_during_score_read"}
    return {"qualified": True, "reason": "one_tic_acknowledged_and_read_stable"}
