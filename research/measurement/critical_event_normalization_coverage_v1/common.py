from __future__ import annotations
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
EXPECTED_BLOBS={
'queue_contract':'404a452aa304b4bde73ec0182450d241e2a744af',
'queue_formal_report':'9abebff10c9fc78aaa70098e080579c83e5eef7f',
'input_owner':'341b3c01649943ddaad5f28431a792c4889cc36e',
'signal_guard':'c0955f976e3a0af6ce926f22cee4a5ddf70ef543'}
EXPECTED_KINDS={'ACTION_REJECTED','AUTHORITY_REVOKED','EFFECT_VERIFIED','FOCUS_CHANGED','LEASE_EXPIRED','SAFETY_VIOLATION'}
def load_fixture(): return json.loads((HERE/'fixture.json').read_text())
def validate_fixture(f):
    assert f['task']=='CRITICAL-EVENT-NORMALIZATION-COVERAGE-20260918-001'
    assert set(f['queue_critical_kinds'])==EXPECTED_KINDS
    assert {k:v['git_blob'] for k,v in f['sources'].items()}==EXPECTED_BLOBS
    assert f['search_evidence']['scope_note'].startswith('NOT_FOUND_IN_SEARCH_SCOPE')
    for r in f['inventory']:
        assert type(r['must_preserve']) is bool
        if r['must_preserve']:
            assert r['candidate_kind'] in EXPECTED_KINDS
        else:
            assert r['candidate_kind'] is None
    return True
def evaluate(f):
    validate_fixture(f)
    required=[r for r in f['inventory'] if r['must_preserve']]
    mapped=[r for r in required if r['executable_mapping']]
    ordinary_promoted=[r for r in f['inventory'] if not r['must_preserve'] and r['executable_mapping']]
    if ordinary_promoted: decision='FAIL_CRITICAL_MISCLASSIFICATION'
    elif len(mapped)==len(required): decision='PASS_CRITICAL_NORMALIZATION_COVERAGE_SCOPED'
    else: decision='HOLD_CRITICAL_NORMALIZATION_MISSING'
    return {'decision':decision,'required_edges':len(required),'mapped_required_edges':len(mapped),'missing_required_edges':[{'producer':r['producer'],'raw':r['raw'],'candidate_kind':r['candidate_kind']} for r in required if not r['executable_mapping']], 'ordinary_promoted':len(ordinary_promoted)}
