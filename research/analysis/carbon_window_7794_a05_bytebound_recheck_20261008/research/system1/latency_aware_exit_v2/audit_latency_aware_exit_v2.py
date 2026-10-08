#!/usr/bin/env python3
import argparse, hashlib, json
from pathlib import Path
import numpy as np
YIELD=6; DEPTH=4

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',required=True); ap.add_argument('--aggregate',required=True); ap.add_argument('--out',required=True); a=ap.parse_args()
    root=Path(a.root); agg=json.loads(Path(a.aggregate).read_text()); errors=[]; recomputed=[]
    case_paths=sorted(root.glob('case_*/CASE.json'))
    for cp in case_paths:
        r=json.loads(cp.read_text()); z=np.load(cp.with_name('CASE_EVIDENCE.npz'))
        for split,pkey,dkey,ykey in [('ordinary','po','do','yo'),('stress','ps','ds','ys')]:
            p=z[pkey]; d=z[dkey]; y=z[ykey]
            if len(p)!=len(y) or len(d)!=len(y): errors.append(f"{r['case_id']}:{split}:n")
            acc=float(np.mean(p==y)); ty=(y==YIELD); unsafe=int(np.sum(ty & (p!=YIELD)))
            yr=float(unsafe/max(1,int(ty.sum()))); py=int(np.sum(p==YIELD))
            counts=[int(np.sum(d==k)) for k in range(1,DEPTH+1)]; comp=float(np.mean(d)/DEPTH)
            if abs(acc-r[split]['accuracy'])>1e-12: errors.append(f"{r['case_id']}:{split}:accuracy")
            if unsafe!=r[split]['teacher_yield_to_exec'] or abs(yr-r[split]['teacher_yield_to_exec_rate'])>1e-12: errors.append(f"{r['case_id']}:{split}:yield")
            if py!=r[split]['predicted_yield_n']: errors.append(f"{r['case_id']}:{split}:pred_yield")
            if counts!=r[split]['exit_counts'] or abs(comp-r[split]['mean_normalized_compute'])>1e-12: errors.append(f"{r['case_id']}:{split}:depth")
        l=z['lats']; p95=float(np.percentile(l,95,method='linear'))
        if abs(p95-r['latency_ms']['p95'])>1e-9: errors.append(f"{r['case_id']}:p95")
        recomputed.append(r)
    expected={(s,arm) for s in [8891701,8891702,8891703,8891704] for arm in ['ACCURACY_ONLY','LATENCY_AWARE']}
    got={(r['seed'],r['arm']) for r in recomputed}
    if got!=expected: errors.append('case_set')
    by={}
    for r in recomputed: by.setdefault(r['seed'],{})[r['arm']]=r
    reds=[]; ol=[]; sl=[]; faster=0; comp=0; violations=[]
    if got==expected:
      for s,pair in sorted(by.items()):
        b=pair['ACCURACY_ONLY']; c=pair['LATENCY_AWARE']
        reds.append(1-c['latency_ms']['p95']/b['latency_ms']['p95']); faster+=c['latency_ms']['p95']<b['latency_ms']['p95']; comp+=c['ordinary']['mean_normalized_compute']<b['ordinary']['mean_normalized_compute']
        ol.append(b['ordinary']['accuracy']-c['ordinary']['accuracy']); sl.append(b['stress']['accuracy']-c['stress']['accuracy'])
        if c['ordinary']['accuracy']<.90: violations.append(f'{s}:ordinary_accuracy')
        if c['stress']['accuracy']<.80: violations.append(f'{s}:stress_accuracy')
        if c['ordinary']['teacher_yield_to_exec_rate']>b['ordinary']['teacher_yield_to_exec_rate']+.005: violations.append(f'{s}:yield_safety')
        if c['ordinary']['predicted_yield_n']==0: violations.append(f'{s}:yield_unreachable')
    medred=float(np.median(reds)) if reds else float('nan'); medol=float(np.median(ol)) if ol else float('nan'); medsl=float(np.median(sl)) if sl else float('nan')
    if errors: disp='FAIL_INTEGRITY'
    elif not violations and medred>=.20 and faster>=3 and medol<=.015 and medsl<=.025 and comp>=3: disp='PASS_LATENCY_AWARE_EARLY_EXIT_SCOPED'
    elif comp>=3 and medred<.20: disp='NO_MEASURED_LATENCY_EFFECT'
    elif comp>=3 or medred>0: disp='HOLD_LATENCY_OBJECTIVE_TRADEOFF_NOT_CLOSED'
    else: disp='REJECT_LATENCY_OBJECTIVE'
    if disp!=agg['decision']: errors.append('aggregate_decision_mismatch')
    audit={'audit':'PASS' if not errors else 'FAIL','decision':disp,'errors':errors,'recomputed_gates':{'median_p95_reduction':medred,'faster_pairs':int(faster),'median_ordinary_loss_pp':medol*100 if ol else None,'median_stress_loss_pp':medsl*100 if sl else None,'compute_better_pairs':int(comp),'violations':violations},'aggregate_sha256':hashlib.sha256(Path(a.aggregate).read_bytes()).hexdigest()}
    Path(a.out).write_text(json.dumps(audit,indent=2,sort_keys=True)+'\n'); print(json.dumps(audit,sort_keys=True))
if __name__=='__main__': main()
