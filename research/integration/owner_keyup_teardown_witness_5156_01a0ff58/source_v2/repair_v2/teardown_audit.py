"""Revision 2; compose with the unchanged, frozen C01 supplement."""
from boundary_audit import audit as previous_audit


def audit(raw):
    errors = previous_audit(raw)
    if errors:
        return errors
    caller_fields = {"release_call_started_ns", "release_call_returned_ns"}
    for case in raw["cases"]:
        if case["event"] != "teardown":
            continue
        receipt = case["receipt"]
        start = receipt.get("release_call_started_ns")
        finish = receipt.get("release_call_returned_ns")
        verified = receipt.get("verified_ns")
        if not (type(start) is int and type(finish) is int and type(verified) is int
                and start <= verified <= finish):
            errors.append("teardown_verified_outside_caller:" + case["case"])
        # Only the caller's two timing fields are absent from the owner record.
        projection = {key: value for key, value in receipt.items() if key not in caller_fields}
        matches = [row for row in raw["owner_snapshots_final"] if row == projection]
        if len(matches) != 1:
            errors.append("teardown_final_witness_mismatch:" + case["case"])
        # Cancellation has already cleaned up autonomously; its final teardown
        # has no appended capture in A18, but still has an exact final witness.
        if case["case"] in ("single", "two_key") and case.get("owner_rows_appended") != [projection]:
            errors.append("teardown_appended_witness_mismatch:" + case["case"])
    return sorted(set(errors))
