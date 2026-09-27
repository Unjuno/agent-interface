import random
from generator import entry,valid_evidence,terminal_evidence,CONTROL_KINDS,trace
from cache import monitor
from oracle import decide
from mechanics import evaluate_trace

e=entry(1)
for j in range(3):
    assert monitor(e,valid_evidence(e,j))['disposition']=='KEEP'
for kind in CONTROL_KINDS:
    v=terminal_evidence(e,3,kind)
    assert monitor(e,v)['disposition']=='YIELD'
    assert decide(e,v)['disposition']=='YIELD'
rng=random.Random(1155)
for i in range(100):
    e,rows,_=trace(i,rng); r=evaluate_trace(e,rows)
    assert r['mismatches']==r['stale_continuation_attempts']==r['missed_hard_invalidations']==0
    assert r['unnecessary_yields']==r['authority_errors']==r['wrong_effects']==0
    assert r['candidate_effect']==r['reference_effect']
print('MECHANICS_PASS')
