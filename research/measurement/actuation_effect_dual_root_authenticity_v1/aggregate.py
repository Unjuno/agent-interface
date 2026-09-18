import json,sys
from collections import Counter

def main(paths):
    rows=[json.load(open(p)) for p in paths]; rows.sort(key=lambda r:r['start'])
    expected=0; errors=[]; states=Counter(); families=Counter()
    sums={k:0 for k in ['count','mismatches','dual_root_false_self_credit','scorer_only_false_self_credit','replay_escape','authority_promotions']}
    for r in rows:
        if r['start']!=expected: errors.append(f'coverage:{expected}->{r["start"]}')
        expected=r['end']
        for k in sums: sums[k]+=r[k]
        states.update(r['states']); families.update(r['families'])
    if expected!=240000: errors.append(f'end:{expected}')
    decision='PASS_EFFECT_DUAL_ROOT_SINGLE_COMPROMISE_SCOPED' if (not errors and sums['mismatches']==0 and sums['dual_root_false_self_credit']==0 and sums['replay_escape']==0 and sums['scorer_only_false_self_credit']>0 and sums['authority_promotions']==0) else 'FAIL_GATE'
    print(json.dumps({'decision':decision,'batch_count':len(rows),'batch_reruns':0,'formal_batch_invocations':len(rows),'coverage_end':expected,'errors':errors,**sums,'states':dict(states),'families':dict(families)},sort_keys=True))
if __name__=='__main__': main(sys.argv[1:])
