import json,sys
from collections import Counter

def main(paths):
    rows=[json.load(open(p)) for p in paths]
    rows.sort(key=lambda r:r['start'])
    expected=0;errs=[];states=Counter();kinds=Counter()
    total={k:0 for k in ['count','mismatches','old_epoch_self_admissions','future_epoch_self_admissions','replay_self_admissions','wrong_key_self_admissions','authority_promotions','task_success_promotions','observations']}
    for r in rows:
        if r['start']!=expected:errs.append(f'coverage:{expected}->{r["start"]}')
        expected=r['end']
        for k in total:total[k]+=r[k]
        states.update(r['states']);kinds.update(r['kinds'])
    if expected!=240000:errs.append(f'end:{expected}')
    decision='PASS_MUTATION_ACTOR_RECEIPT_KEY_EPOCH_SCOPED' if not errs and all(total[k]==0 for k in ['mismatches','old_epoch_self_admissions','future_epoch_self_admissions','replay_self_admissions','wrong_key_self_admissions','authority_promotions','task_success_promotions']) else 'FAIL_GATE'
    print(json.dumps({'decision':decision,'batch_count':len(rows),'batch_reruns':0,'coverage_end':expected,'errors':errs,'formal_batch_invocations':len(rows),**total,'states':dict(states),'kinds':dict(kinds)},sort_keys=True))
if __name__=='__main__':main(sys.argv[1:])
