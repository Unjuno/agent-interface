import audit
from model import CASES,evaluate
from runner import build_raw
def test_two_parity_groups_recover_cross_group_losses():
    r=evaluate(CASES["cross_group_erasures"])
    assert r["presentation_complete"] and r["reconstructed"]==["a","c"] and not r["authority_eligible"]
def test_same_group_double_erasure_is_incomplete():
    assert not evaluate(CASES["same_group_double_erasure"])["presentation_complete"]
def test_reconstruction_never_grants_authority():
    for n in ("single_noncritical_erasure","single_critical_erasure","cross_group_erasures"):
        assert not evaluate(CASES[n])["authority_eligible"]
def test_order_invariance_and_exact_delivery_authority():
    assert evaluate(CASES["complete"])["decoded"]==evaluate(CASES["reordered_complete"])["decoded"]
    assert evaluate(CASES["complete"])["authority_eligible"]
    assert evaluate(CASES["parity_erasure_sources_complete"])["authority_eligible"]
def test_provenance_and_criticality_mismatch_fail_closed():
    for n in ("mixed_generation","criticality_metadata_mismatch"):
        assert not evaluate(CASES[n])["presentation_complete"]
def test_full_raw_audit_and_mutation():
    raw=build_raw();assert len(raw["rows"])==9 and audit.audit(raw)==[]
    raw["rows"][0]["authority_eligible"]=False
    assert audit.audit(raw)
