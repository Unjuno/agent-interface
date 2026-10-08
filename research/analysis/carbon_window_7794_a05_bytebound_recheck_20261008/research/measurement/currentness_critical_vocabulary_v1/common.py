import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
KINDS={'FOCUS_CHANGED','AUTHORITY_REVOKED','LEASE_EXPIRED','ACTION_REJECTED','SAFETY_VIOLATION','EFFECT_VERIFIED'}
def load(): return json.loads((HERE/'fixture.json').read_text())
def validate(f):
    assert f['task']=='CURRENTNESS-CRITICAL-VOCABULARY-ADEQUACY-20260918-001'
    assert set(f['kind_predicates'])==KINDS
    for k,req in f['kind_predicates'].items(): assert len(req)==1 and isinstance(req[0],str)
    assert len(f['required_guard_cases'])==5
    return True
def admissible(f,facts): return sorted(k for k,reqs in f['kind_predicates'].items() if all(facts.get(x) is True for x in reqs))
def evaluate(f):
    validate(f)
    rows=[{'name':c['name'],'status':c['status'],'reason':c['reason'],'admissible':admissible(f,c['facts'])} for c in f['required_guard_cases']]
    controls=[{'name':c['name'],'admissible':admissible(f,c['facts']),'expected':sorted(c['expected'])} for c in f['controls']]
    gap=all(not r['admissible'] for r in rows); controls_ok=all(c['admissible']==c['expected'] for c in controls)
    if gap and controls_ok: d='PASS_CURRENTNESS_VOCABULARY_GAP_SCOPED'
    elif (not gap) and controls_ok: d='PASS_EXISTING_KIND_SUFFICIENT_SCOPED'
    else: d='FAIL_SEMANTIC_LAUNDERING'
    return {'decision':d,'required_cases':rows,'controls':controls,'gap_retained':gap,'controls_ok':controls_ok}
