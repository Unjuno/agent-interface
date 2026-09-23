import json,sys

def main(paths):
    rows=[json.load(open(p)) for p in paths]; rows.sort(key=lambda r:r['start'])
    expected=0; errors=[]
    sums={k:0 for k in ['count','legit_accept','compromised_accept','visible_byte_identical_pairs','wrong_key_reject','altered_after_sign_reject','authority_promotions']}
    for r in rows:
        if r['start']!=expected: errors.append(f'coverage:{expected}->{r["start"]}')
        expected=r['end']
        for k in sums: sums[k]+=r[k]
    if expected!=200000: errors.append(f'end:{expected}')
    n=sums['count']
    decision='PASS_SINGLE_SCORER_ROOT_COMPROMISE_INSUFFICIENT_SCOPED' if (not errors and n==200000 and sums['legit_accept']==n and sums['compromised_accept']==n and sums['visible_byte_identical_pairs']==n and sums['wrong_key_reject']==n and sums['altered_after_sign_reject']==n and sums['authority_promotions']==0) else 'FAIL_GATE'
    print(json.dumps({'decision':decision,'batch_count':len(rows),'batch_reruns':0,'formal_batch_invocations':len(rows),'coverage_end':expected,'errors':errors,**sums},sort_keys=True))
if __name__=='__main__': main(sys.argv[1:])
