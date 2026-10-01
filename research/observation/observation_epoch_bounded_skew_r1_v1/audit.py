import argparse, copy, json
from pathlib import Path

def evaluate(r):
    e=[]; m=r.get('metrics',{}); d=r.get('directed',{})
    if r.get('task')!='OBSERVATION-EPOCH-BOUNDED-SKEW-R1-20260918-001': e.append('task')
    if r.get('reruns')!=0 or r.get('replacements')!=0 or r.get('tuning')!=0: e.append('counters')
    for k in ('candidate_oracle_mismatch','candidate_stale_critical_joins','candidate_cross_identity_generation_joins','candidate_malformed_missing_future_joins'):
        if m.get(k)!=0: e.append(k)
    if m.get('valid_candidate_joins',0)<=0: e.append('no_valid_join')
    if m.get('naive_stale_critical_joins',0)<=0: e.append('no_naive_discriminator')
    if d.get('focus_mutation')!={'candidate':False,'naive':True,'oracle':False}: e.append('focus_counterexample')
    if d.get('valid_stagger')!={'candidate':True,'strict':False,'oracle':True}: e.append('stagger_counterexample')
    if r.get('phase')=='formal':
        if r.get('formal_invocations')!=1 or m.get('rows')!=300000: e.append('formal_shape')
        if m.get('critical_expiry_rows',0)<50000: e.append('critical_stress')
        if m.get('valid_candidate_joins_rejected_by_strict',0)<50000: e.append('strict_value')
        if m.get('identity_generation_mismatch_rows',0)<50000: e.append('identity_stress')
        if m.get('malformed_missing_future_rows',0)<25000: e.append('malformed_stress')
    return sorted(set(e))

def controls(r):
    tests={}
    mods=[('oracle','candidate_oracle_mismatch',1),('stale','candidate_stale_critical_joins',1),
          ('identity','candidate_cross_identity_generation_joins',1),('malformed','candidate_malformed_missing_future_joins',1),
          ('naive','naive_stale_critical_joins',0)]
    for name,key,val in mods:
        q=copy.deepcopy(r); q['metrics'][key]=val; tests[name]=bool(evaluate(q))
    q=copy.deepcopy(r); q['directed']['focus_mutation']['candidate']=True; tests['directed']=bool(evaluate(q))
    return tests

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('result'); ap.add_argument('--out',required=True); a=ap.parse_args()
    r=json.loads(Path(a.result).read_text()); errs=evaluate(r); cc=controls(r)
    out={'pass':not errs and all(cc.values()),'errors':errs,'corruption_controls':cc,'controls_pass':all(cc.values())}
    Path(a.out).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,indent=2,sort_keys=True))
    raise SystemExit(0 if out['pass'] else 4)
