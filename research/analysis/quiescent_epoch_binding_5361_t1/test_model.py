import audit
from model import CASES,POLICIES,evaluate
from runner import build_raw
def test_inflight_old_completion_refused():
    assert evaluate(CASES["inflight_old_completion"],"REVOKE_ONLY")["action_admitted"]
    assert not evaluate(CASES["inflight_old_completion"],"EPOCH_BOUND")["action_admitted"]
def test_new_epoch_action_and_complete_reclamation():
    assert evaluate(CASES["fresh_new_epoch"],"EPOCH_BOUND")=={"action_admitted":True,"reclaim_allowed":True}
def test_missing_or_mismatched_receipts_block_reclamation():
    for n in ("crashed_reader_unreported","wrong_retired_authority_receipt","reader_registered_after_snapshot"): assert not evaluate(CASES[n],"EPOCH_BOUND")["reclaim_allowed"]
def test_authority_and_lease_bound_action_admission():
    for n in ("wrong_authority_same_epoch","expired_lease"): assert not evaluate(CASES[n],"EPOCH_BOUND")["action_admitted"]
def test_sixteen_rows_match_independent_oracle():
    assert len(build_raw()["rows"])==len(CASES)*len(POLICIES)==16
    assert audit.audit(build_raw())==[]
def test_audit_detects_missing_and_changed_rows():
    raw=build_raw();raw["rows"].pop();assert "ROW_SET_MISMATCH" in audit.audit(raw)
    raw=build_raw();raw["rows"][0]["action_admitted"]=not raw["rows"][0]["action_admitted"]
    assert any(e.startswith("OUTCOME_MISMATCH") for e in audit.audit(raw))
