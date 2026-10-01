from __future__ import annotations
import argparse, copy, hashlib, json
from pathlib import Path

DIRECTIONS=('horizontal','vertical','diagonal')
TASK='VISUAL-INVALIDATION-ROI-TRANSLATION-ENVELOPE-20260918-001'

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def evaluate(r):
    errs=[]
    if r.get('task')!=TASK: errs.append('task')
    if r.get('phase')!='characterization': errs.append('phase')
    if r.get('seed')!=149420260918001: errs.append('seed')
    if r.get('trials_per_class_per_cell')!=1000: errs.append('trials')
    if r.get('formal_invocations')!=0 or r.get('reruns')!=0 or r.get('replacements')!=0 or r.get('tuning')!=0: errs.append('execution_contract')
    cells=r.get('cells',[])
    if len(cells)!=75: errs.append('cell_count')
    index={(c.get('direction'),c.get('d')):c for c in cells}
    for direction in DIRECTIONS:
        for d in range(25):
            c=index.get((direction,d))
            if not c: errs.append(f'missing:{direction}:{d}'); continue
            if not (0<=c.get('fpr',-1)<=1 and 0<=c.get('fnr',-1)<=1): errs.append(f'rate:{direction}:{d}')
        b=r.get('bounds',{}).get(direction,{})
        safe=[d for d in range(1,25) if index[(direction,d)]['fpr']<=0.01 and index[(direction,d)]['fnr']<=0.01]
        fail=[d for d in range(1,25) if index[(direction,d)]['fpr']>0.01]
        hard=[d for d in range(1,25) if index[(direction,d)]['fpr']>=0.99]
        if b.get('last_d_fpr_le_1pct')!=(max(safe) if safe else None): errs.append(f'bound_safe:{direction}')
        if b.get('first_d_fpr_gt_1pct')!=(min(fail) if fail else None): errs.append(f'bound_fail:{direction}')
        if b.get('first_d_fpr_ge_99pct')!=(min(hard) if hard else None): errs.append(f'bound_hard:{direction}')
    d0=max(index[(d,0)]['fnr'] for d in DIRECTIONS)
    if abs(d0-r.get('d0_max_fnr',-1))>1e-12: errs.append('d0')
    expected='FAIL_DETECTOR_SENSITIVITY' if d0>0.01 else ('REJECT_FIXED_ROI_TRANSLATION_TOLERANCE' if any(index[(k,1)]['fpr']>0.01 for k in DIRECTIONS) else 'RETAIN_FIXED_ROI_TRANSLATION_ENVELOPE_SCOPED')
    if r.get('decision')!=expected: errs.append('decision')
    return {'pass':not errs,'errors':errs,'expected_decision':expected,'result_sha256':None}

def controls(r):
    tests={}
    q=copy.deepcopy(r); q['seed']=1; tests['seed']=not evaluate(q)['pass']
    q=copy.deepcopy(r); q['cells']=q['cells'][:-1]; tests['missing_cell']=not evaluate(q)['pass']
    q=copy.deepcopy(r); q['bounds']['horizontal']['first_d_fpr_gt_1pct']=99; tests['bound']=not evaluate(q)['pass']
    q=copy.deepcopy(r); q['decision']='PASS_ANYTHING'; tests['decision']=not evaluate(q)['pass']
    q=copy.deepcopy(r); q['reruns']=1; tests['rerun']=not evaluate(q)['pass']
    return tests

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('result'); ap.add_argument('--out'); a=ap.parse_args()
    r=json.loads(Path(a.result).read_text()); out=evaluate(r); out['result_sha256']=sha(a.result); out['corruption_controls']=controls(r); out['controls_pass']=all(out['corruption_controls'].values()); out['pass']=out['pass'] and out['controls_pass']
    if a.out: Path(a.out).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,indent=2,sort_keys=True)); raise SystemExit(0 if out['pass'] else 4)
if __name__=='__main__': main()
