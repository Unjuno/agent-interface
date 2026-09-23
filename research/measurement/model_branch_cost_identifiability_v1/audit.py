import json, hashlib, itertools, sys
from pathlib import Path
HERE=Path(__file__).parent
KEYS=['run','i','img','input','cached','output','reasoning','model_ns','effect','state','primary','branches','session']
def R(x):return dict(zip(KEYS,x))
def admissible(a,b):
    return (a['img']==b['img'] and a['effect']==b['effect'] and a['state']==b['state'] and
            a['primary']==b['primary'] and (a['input'],a['cached'])==(b['input'],b['cached']) and
            a['session']==b['session'] and a['branches']!=b['branches'])
def verify(result,ledger):
    e=[]; rows=[R(x) for x in ledger['rows']]; g=[x for x in rows if x['run']=='grouped'];u=[x for x in rows if x['run']=='ungrouped']
    n=sum(admissible(a,b) for a,b in itertools.product(g,u))
    same=sum(a['img']==b['img'] for a,b in itertools.product(g,u))
    if result.get('rows')!=24 or result.get('candidate_pairs')!=144:e.append('counts')
    if result.get('admissible_pair_count')!=n:e.append('admissible_count')
    if result.get('same_image_pairs')!=same:e.append('same_image_count')
    endpoint=all(p.get('audit_passed') and all(type(p.get(k)) is int and p[k]>=0 for k in ('input','cached','output','reasoning')) for p in ledger['probe_usage'])
    if result.get('provider_usage_endpoint_confirmed')!=endpoint:e.append('usage_endpoint')
    if result.get('per_branch_cost_emitted') is not False:e.append('causal_cost_laundering')
    diag=result.get('whole_run_noncausal_diagnostic',{})
    if diag.get('causal_per_branch_estimate') is not None:e.append('diagnostic_laundering')
    expected='PASS_RETAINED_MODEL_BRANCH_COST_NOT_IDENTIFIABLE_SCOPED' if endpoint and n==0 else ('PASS_RETAINED_MODEL_BRANCH_COST_IDENTIFIABLE_SCOPED' if endpoint else 'HOLD_SOURCE_GAP')
    if result.get('decision')!=expected:e.append('decision')
    return {'audit_pass':not e,'errors':e,'recomputed_admissible_pairs':n,'recomputed_same_image_pairs':same,'decision':result.get('decision')}
def main():
    r=json.loads((HERE/'RESULT.json').read_text()); l=json.loads((HERE/'ledger.json').read_text()); o=verify(r,l)
    o['result_sha256']=hashlib.sha256((HERE/'RESULT.json').read_bytes()).hexdigest();o['ledger_sha256']=hashlib.sha256((HERE/'ledger.json').read_bytes()).hexdigest()
    (HERE/'AUDIT.json').write_text(json.dumps(o,indent=2,sort_keys=True)+'\n');print(json.dumps(o,indent=2,sort_keys=True));raise SystemExit(0 if o['audit_pass'] else 1)
if __name__=='__main__':main()
