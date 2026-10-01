import argparse,copy,json
from pathlib import Path
def evaluate(r):
    e=[];q=r['random'];d=r['directed']
    if r['exhaustive_mismatch']!=0:e.append('exhaustive_mismatch')
    if r['exhaustive_order_mismatch']!=0:e.append('exhaustive_order')
    if q['candidate_oracle_mismatch']!=0:e.append('random_mismatch')
    if q['unsafe_selected']!=0:e.append('unsafe')
    if q['label_permutation_changes']!=0:e.append('labels')
    if q['entropy_worse_worstcase']<=0:e.append('no_entropy_discriminator')
    if d['minimax_example']!=1 or d['entropy_example']!=0 or d['minimax_worst']!=3 or d['entropy_worst']!=4:e.append('directed_entropy')
    if d['unsafe_perfect_ignored']!=1:e.append('unsafe_directed')
    if d['empty_safe'] is not None:e.append('empty_safe')
    if r['phase']=='formal':
        if r['formal_invocations']!=1 or q['rows']!=250000 or r['exhaustive_max_n']!=16:e.append('formal_shape')
    if r['reruns']!=0 or r['replacements']!=0 or r['tuning']!=0:e.append('counters')
    return sorted(set(e))
def controls(r):
    t={}
    q=copy.deepcopy(r);q['random']['unsafe_selected']=1;t['unsafe_selection']=bool(evaluate(q))
    q=copy.deepcopy(r);q['exhaustive_mismatch']=1;t['expected_not_worst']=bool(evaluate(q))
    q=copy.deepcopy(r);q['directed']['minimax_example']=0;t['reverse_inequality']=bool(evaluate(q))
    q=copy.deepcopy(r);q['directed']['empty_safe']=0;t['empty_safe_fallback']=bool(evaluate(q))
    q=copy.deepcopy(r);q['random']['label_permutation_changes']=1;t['label_identity']=bool(evaluate(q))
    return t
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('result');ap.add_argument('--out',required=True);a=ap.parse_args();r=json.loads(Path(a.result).read_text());errs=evaluate(r);cc=controls(r);o={'pass':not errs and all(cc.values()),'errors':errs,'corruption_controls':cc,'controls_pass':all(cc.values())};Path(a.out).write_text(json.dumps(o,indent=2,sort_keys=True)+'\n');print(json.dumps(o,indent=2,sort_keys=True));raise SystemExit(0 if o['pass'] else 4)
