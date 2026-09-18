import json,sys
from collections import Counter

def main(paths):
    rows=[json.load(open(p)) for p in paths]
    rows=sorted(rows,key=lambda x:x['start'])
    expected=0; errs=[]; states=Counter(); kinds=Counter()
    sums={k:0 for k in ['mismatches','forged_self_admissions','replay_attempts','replay_self_admissions','authority_promotions','task_success_promotions','count']}
    for r in rows:
        if r['start']!=expected: errs.append(f"coverage:{expected}->{r['start']}")
        expected=r['end']
        for k in sums: sums[k]+=r[k]
        states.update(r['states']); kinds.update(r['kinds'])
    if expected!=360000: errs.append(f"end:{expected}")
    decision='PASS_MUTATION_ACTOR_RECEIPT_AUTHENTICITY_SCOPED' if not errs and sums['mismatches']==0 and sums['forged_self_admissions']==0 and sums['replay_self_admissions']==0 and sums['authority_promotions']==0 and sums['task_success_promotions']==0 else 'FAIL_GATE'
    out={'decision':decision,'batch_count':len(rows),'coverage_end':expected,'errors':errs,**sums,'states':dict(states),'kinds':dict(kinds),'formal_batch_invocations':len(rows),'batch_reruns':0}
    print(json.dumps(out,sort_keys=True))
if __name__=='__main__': main(sys.argv[1:])
