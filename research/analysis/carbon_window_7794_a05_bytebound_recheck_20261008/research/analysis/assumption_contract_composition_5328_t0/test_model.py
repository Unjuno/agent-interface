import audit
from model import CASES,evaluate
from runner import build_raw
def test_only_fully_discharged_baseline_composes_pass():
    assert evaluate(CASES["baseline"])["composed_status"]=="PASS"
    for n in ("backend_stability_false","capability_expired","assumption_evidence_missing","verifier_digest_stale"):
        assert evaluate(CASES[n])["composed_status"]=="UNKNOWN"
def test_protocol_mismatch_and_false_guarantee_stop():
    assert evaluate(CASES["protocol_mismatch"])["composed_status"]=="STOP"
    assert evaluate(CASES["component_guarantee_false"])["composed_status"]=="STOP"
def test_local_pass_does_not_survive_invalid_environment():
    assert all(evaluate(CASES[n])["flat_local_pass"] for n in ("backend_stability_false","capability_expired","assumption_evidence_missing","verifier_digest_stale"))
def test_full_raw_matches_independent_audit():
    raw=build_raw();assert len(raw["rows"])==7;assert audit.audit(raw)==[]
def test_audit_detects_composed_pass_after_assumption_failure():
    raw=build_raw();raw["rows"][1]["composed_status"]="PASS"
    assert any(e.startswith("ORACLE_MISMATCH") or e.startswith("UNJUSTIFIED_PASS") for e in audit.audit(raw))
