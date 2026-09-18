import argparse,json,hashlib,copy
from pathlib import Path
EVENTS=3; EFFECTS=4; TIMING=4; FOCUS=2; DIGEST=4
EXPECTED=EVENTS*EFFECTS*TIMING*FOCUS*DIGEST
SPECIFIC=('TIMING','EVENT_SHAPE','FOCUS','EFFECT_SHAPE','COMPOSITE')

def validate(r):
    errs=[]
    if EXPECTED!=384: errs.append('auditor_math')
    if r.get('pairs')!=EXPECTED or r.get('histories')!=2*EXPECTED: errs.append('cardinality')
    if r.get('identical_observable_pairs')!=EXPECTED: errs.append('equivalence')
    hs=r.get('heuristics',{})
    for n in SPECIFIC:
        x=hs.get(n,{})
        if x.get('errors')!=EXPECTED or x.get('pair_specific_error_min')!=1: errs.append('specific_'+n)
    u=hs.get('UNATTRIBUTED',{})
    if u.get('false_specific_claims')!=0: errs.append('unattributed_claim')
    if r.get('trusted_witness_pairs_separated')!=EXPECTED or r.get('trusted_witness_errors')!=0: errs.append('witness')
    if r.get('authority_promotions')!=0 or r.get('task_success_promotions')!=0: errs.append('promotion')
    if r.get('formal_invocations')!=1 or r.get('reruns')!=0: errs.append('invocation')
    if r.get('decision')!='PASS_PROVENANCE_FREE_ACTOR_INDISTINGUISHABILITY_SCOPED': errs.append('decision')
    return errs

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--result',required=True);ap.add_argument('--output',required=True);a=ap.parse_args()
    r=json.loads(Path(a.result).read_text()); errors=validate(r)
    corruptions=[]
    specs=[('decision',lambda x:x.__setitem__('decision','PASS_BOGUS')),
           ('pairs',lambda x:x.__setitem__('pairs',383)),
           ('equivalence',lambda x:x.__setitem__('identical_observable_pairs',383)),
           ('specific_errors',lambda x:x['heuristics']['TIMING'].__setitem__('errors',383)),
           ('authority',lambda x:x.__setitem__('authority_promotions',1)),
           ('witness',lambda x:x.__setitem__('trusted_witness_errors',1)),
           ('rerun',lambda x:x.__setitem__('reruns',1))]
    for name,mut in specs:
        x=copy.deepcopy(r);mut(x); rejected=bool(validate(x));corruptions.append({'name':name,'rejected':rejected})
    out={'status':'PASS' if not errors and all(c['rejected'] for c in corruptions) else 'FAIL',
         'independent_expected_pairs':EXPECTED,'errors':errors,'corruptions':corruptions,
         'result_sha256':hashlib.sha256(Path(a.result).read_bytes()).hexdigest()}
    Path(a.output).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
    raise SystemExit(0 if out['status']=='PASS' else 1)
if __name__=='__main__':main()
