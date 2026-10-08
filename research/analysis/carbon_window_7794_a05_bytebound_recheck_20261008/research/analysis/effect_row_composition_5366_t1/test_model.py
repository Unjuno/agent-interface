import audit
from model import CASES,evaluate
from runner import build_raw
def test_unknown_effect_stays_unknown():
    assert evaluate(CASES["native_unknown"])["status"]=="EFFECT_UNKNOWN"
    assert evaluate(CASES["remote_unknown"])["status"]=="EFFECT_UNKNOWN"
def test_composition_propagates_latent_network_and_nested_write():
    assert not evaluate(CASES["polymorphic_network_instantiation"])["admitted"]
    assert not evaluate(CASES["wrapper_masks_nested_write"])["admitted"]
def test_valid_rows_admit_and_union_reports_one_false_reject():
    assert evaluate(CASES["valid_transitive_read_observe"])["admitted"]
    assert evaluate(CASES["contained_effect_row"])["admitted"]
    assert evaluate(CASES["branch_union_false_reject"])["false_reject"]
def test_full_corpus_and_independent_audit():
    raw=build_raw();assert len(raw["rows"])==9;assert audit.audit(raw)==[]
def test_audit_detects_unknown_promotion_and_row_loss():
    raw=build_raw();raw["rows"][5]["admitted"]=True
    assert audit.audit(raw)
    raw=build_raw();raw["rows"].pop();assert "ROW_SET_MISMATCH" in audit.audit(raw)
