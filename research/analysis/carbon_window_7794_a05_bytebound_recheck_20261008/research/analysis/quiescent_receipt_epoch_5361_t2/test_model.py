import audit
from model import CASES,evaluate
from runner import build_raw
def test_only_exact_complete_receipts_allow_reclamation():
    assert evaluate(CASES["valid_complete_bundle"])["reclaim_allowed"]
    for n in ("receipt_epoch_too_old","receipt_epoch_too_new","receipt_epoch_missing","wrong_retired_authority","reader_missing","registry_changed","duplicate_receipt_identity","valid_new_action_reclaim_blocked"):
        assert not evaluate(CASES[n])["reclaim_allowed"]
def test_current_action_is_independent_of_old_object_reclamation():
    r=evaluate(CASES["valid_new_action_reclaim_blocked"])
    assert r["action_admitted"] and not r["reclaim_allowed"]
def test_stale_action_refused_even_when_reclamation_is_complete():
    r=evaluate(CASES["stale_action_valid_reclaim"])
    assert not r["action_admitted"] and r["reclaim_allowed"]
def test_full_raw_and_independent_audit():
    raw=build_raw();assert len(raw["rows"])==10;assert audit.audit(raw)==[]
def test_audit_rejects_wrong_epoch_mutation():
    raw=build_raw();row=next(r for r in raw["rows"] if r["case_id"]=="valid_complete_bundle")
    row["inputs"]["receipts"][0]["epoch"]=3
    assert any(e.startswith("OUTCOME_MISMATCH") or e.startswith("RECEIPT_EPOCH") for e in audit.audit(raw))
