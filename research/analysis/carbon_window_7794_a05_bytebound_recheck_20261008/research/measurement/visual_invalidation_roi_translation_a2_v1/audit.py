from __future__ import annotations
import argparse, copy, hashlib, json
from pathlib import Path

TASK='VISUAL-INVALIDATION-ROI-TRANSLATION-ENVELOPE-A2-20260918-002'
DIRECTIONS=('horizontal','vertical','diagonal')
EXPECTED_CONSTANTS={'roi':48,'target':12,'background':64,'target_base':128,'target_changed':144,'sigma':2.0,'pixel_delta':12,'count_threshold':100}

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def evaluate(r):
    errs=[]
    if r.get('task')!=TASK: errs.append('task')
    if r.get('phase')!='characterization': errs.append('phase')
    if r.get('seed')!=149520260918002: errs.append('seed')
    if r.get('trials_per_class_per_cell')!=1000: errs.append('trials')
    if r.get('characterization_invocations')!=1 or r.get('reruns')!=0 or r.get('replacements')!=0 or r.get('tuning')!=0: errs.append('execution_contract')
    if r.get('constants')!=EXPECTED_CONSTANTS: errs.append('constants')
    cells=r.get('cells',[])
    if len(cells)!=75: errs.append('cell_count')
    idx={(c.get('direction'),c.get('d')):c for c in cells}
    for direction in DIRECTIONS:
        for d in range(25):
            c=idx.get((direction,d))
            if not c: errs.append(f'missing:{direction}:{d}'); continue
            if c.get('trials_per_class')!=1000: errs.append(f'cell_trials:{direction}:{d}')
            if not (0.0<=c.get('fpr',-1)<=1.0 and 0.0<=c.get('fnr',-1)<=1.0): errs.append(f'rate:{direction}:{d}')
        if any((direction,d) not in idx for d in range(25)): continue
        safe=[d for d in range(1,25) if idx[(direction,d)]['fpr']<=0.01 and idx[(direction,d)]['fnr']<=0.01]
        fail=[d for d in range(1,25) if idx[(direction,d)]['fpr']>0.01]
        hard=[d for d in range(1,25) if idx[(direction,d)]['fpr']>=0.99]
        b=r.get('bounds',{}).get(direction,{})
        if b.get('last_d_fpr_le_1pct')!=(max(safe) if safe else None): errs.append(f'bound_safe:{direction}')
        if b.get('first_d_fpr_gt_1pct')!=(min(fail) if fail else None): errs.append(f'bound_fail:{direction}')
        if b.get('first_d_fpr_ge_99pct')!=(min(hard) if hard else None): errs.append(f'bound_hard:{direction}')
    if len(idx)==75:
        d0=max(idx[(k,0)]['fnr'] for k in DIRECTIONS)
        if abs(r.get('d0_max_fnr',-1)-d0)>1e-12: errs.append('d0')
        if d0>0.01: expected='FAIL_DETECTOR_SENSITIVITY'
        elif any(idx[(k,1)]['fpr']>0.01 for k in DIRECTIONS): expected='REJECT_FIXED_ROI_TRANSLATION_TOLERANCE'
        elif all(r.get('bounds',{}).get(k,{}).get('last_d_fpr_le_1pct') is not None and r.get('bounds',{}).get(k,{}).get('first_d_fpr_ge_99pct') is not None for k in DIRECTIONS): expected='RETAIN_FIXED_ROI_TRANSLATION_ENVELOPE_SCOPED'
        else: expected='FAIL_INTEGRITY'
        if r.get('decision')!=expected: errs.append('decision')
    return {'pass':not errs,'errors':errs}

def controls(r):
    tests={}
    q=copy.deepcopy(r); q['seed']=0; tests['seed']=not evaluate(q)['pass']
    q=copy.deepcopy(r); q['cells']=q['cells'][:-1]; tests['missing_cell']=not evaluate(q)['pass']
    q=copy.deepcopy(r); q['constants']['roi']=49; tests['constant']=not evaluate(q)['pass']
    q=copy.deepcopy(r); q['bounds']['horizontal']['first_d_fpr_gt_1pct']=99; tests['bound']=not evaluate(q)['pass']
    q=copy.deepcopy(r); q['reruns']=1; tests['rerun']=not evaluate(q)['pass']
    q=copy.deepcopy(r); q['decision']='PASS_ANY'; tests['decision']=not evaluate(q)['pass']
    return tests

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('result'); ap.add_argument('--out'); a=ap.parse_args()
    r=json.loads(Path(a.result).read_text()); out=evaluate(r); out['result_sha256']=sha(a.result); out['corruption_controls']=controls(r); out['controls_pass']=all(out['corruption_controls'].values()); out['pass']=out['pass'] and out['controls_pass']
    s=json.dumps(out,indent=2,sort_keys=True)+'\n'; print(s,end='')
    if a.out: Path(a.out).write_text(s)
    raise SystemExit(0 if out['pass'] else 4)
if __name__=='__main__': main()
