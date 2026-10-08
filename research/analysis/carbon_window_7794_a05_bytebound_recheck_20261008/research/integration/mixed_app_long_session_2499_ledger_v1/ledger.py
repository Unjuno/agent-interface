REQUIRED = ("session_id","transition_seq","app","window_id","pid","display","surface_generation","observation_hash","capability_generation","invalidation_reason","recovery_mode","authority_grants","input_receipt","effect_receipt","cleanup")

def validate(rows):
    if not rows:
        return "HOLD_NO_INTEGRATED_TRACE"
    missing = sorted({key for row in rows for key in REQUIRED if key not in row})
    if missing:
        return "HOLD_LEDGER_FIELDS_MISSING:" + ",".join(missing)
    session = {row["session_id"] for row in rows}
    if len(session) != 1:
        return "FAIL_MULTIPLE_SESSIONS"
    seq = [row["transition_seq"] for row in rows]
    if seq != list(range(len(rows))):
        return "FAIL_TRANSITION_ORDER"
    if any(row["recovery_mode"] != "observe_only" for row in rows):
        return "FAIL_RECOVERY_AUTHORITY"
    if any(row["authority_grants"] for row in rows):
        return "FAIL_AUTHORITY_LEAK"
    if any(not row["cleanup"] for row in rows):
        return "FAIL_CLEANUP_EVIDENCE"
    return "PASS_LEDGER_CONTRACT_SCOPED"
