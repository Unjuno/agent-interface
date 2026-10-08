import argparse,copy,json
from pathlib import Path

def evaluate(r):
    e=[];ex=r['exhaustive'];q=r['random'];d=r['directed']
    if ex['rows']!=12096:e.append('exhaustive_rows')
    for k in ('candidate_oracle_mismatch','unsafe_selected','impossible_mismatch'):
        if ex[k]!=0:e.append('exhaustive_'+k)
        if q[k]!=0:e.append('random_'+k)
    if q['label_permutation_changes']!=0:e.append('labels')
    if q['greedy_suboptimal']<=0:e.append('no_greedy_discriminator')
    if d['expensive_perfect']['optimal']!=[2,1] or d['expensive_perfect']['oracle']!=[2,1] or d['expensive_perfect']['greedy_cost']!=10:e.append('directed_expensive')
    if d['unsafe_perfect']['optimal']!=[2,1]:e.append('directed_unsafe')
    if d['impossible']['optimal']!=[None,None]:e.append('directed_impossible')
    if d['noinfo']['optimal']!=[2,1]:e.append('directed_noinfo')
    if r['phase']=='formal' and (r['formal_invocations']!=1 or q['rows']!=100000):e.append('formal_shape')
    if r['reruns']!=0 or r['replacements']!=0 or r['tuning']!=0:e.append('counters')
    return sorted(set(e))

def controls(r):
    t={}
    q=copy.deepcopy(r);q['random']['unsafe_selected']=1;t['unsafe_use']=bool(evaluate(q))
    q=copy.deepcopy(r);q['directed']['expensive_perfect']['optimal']=[1,1];t['drop_cost']=bool(evaluate(q))
    q=copy.deepcopy(r);q['directed']['expensive_perfect']['optimal']=[6,1];t['mean_not_max']=bool(evaluate(q))
    q=copy.deepcopy(r);q['directed']['impossible']['optimal']=[9,0];t['false_finite']=bool(evaluate(q))
    q=copy.deepcopy(r);q['random']['label_permutation_changes']=1;t['label_identity']=bool(evaluate(q))
    return t

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('result');ap.add_argument('--out',required=True);a=ap.parse_args();r=json.loads(Path(a.result).read_text());errs=evaluate(r);cc=controls(r);o={'pass':not errs and all(cc.values()),'errors':errs,'corruption_controls':cc,'controls_pass':all(cc.values())};Path(a.out).write_text(json.dumps(o,indent=2,sort_keys=True)+'\n');print(json.dumps(o,indent=2,sort_keys=True));raise SystemExit(0 if o['pass'] else 4)
