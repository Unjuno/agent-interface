#!/usr/bin/env python3
import argparse, hashlib, json
from pathlib import Path
import numpy as np

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',required=True); ap.add_argument('--out',required=True); a=ap.parse_args()
    root=Path(a.root); cases=sorted(root.glob('case_*/CASE.json'))
    rows=[json.loads(p.read_text()) for p in cases]
    errors=[]
    expected={(s,arm) for s in [8891701,8891702,8891703,8891704] for arm in ['ACCURACY_ONLY','LATENCY_AWARE']}
    got={(r['seed'],r['arm']) for r in rows}
    if got!=expected: errors.append({'case_set':{'missing':sorted(expected-got),'extra':sorted(got-expected)}})
    by={}
    for r in rows: by.setdefault(r['seed'],{})[r['arm']]=r
    reds=[]; ol=[]; sl=[]; faster=0; comp=0; violations=[]
    if not errors:
      for s,pair in sorted(by.items()):
        b=pair['ACCURACY_ONLY']; c=pair['LATENCY_AWARE']
        reds.append(1-c['latency_ms']['p95']/b['latency_ms']['p95'])
        faster+=c['latency_ms']['p95']<b['latency_ms']['p95']
        comp+=c['ordinary']['mean_normalized_compute']<b['ordinary']['mean_normalized_compute']
        ol.append(b['ordinary']['accuracy']-c['ordinary']['accuracy'])
        sl.append(b['stress']['accuracy']-c['stress']['accuracy'])
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
    result={'task':'LOCAL-SYSTEM1-LATENCY-AWARE-EARLY-EXIT-20260917-001','allocation':'A2_SPLIT_DISPATCH','formal_cases':len(rows),'formal_case_reruns':0,'a1_retained':'STOPPED_FORMAL_OUTER_TIMEOUT','decision':disp,'errors':errors,'gates':{'median_p95_reduction':medred,'faster_pairs':int(faster),'median_ordinary_loss_pp':medol*100 if ol else None,'median_stress_loss_pp':medsl*100 if sl else None,'compute_better_pairs':int(comp),'violations':violations},'rows':rows}
    Path(a.out).write_text(json.dumps(result,indent=2,sort_keys=True)+'\n'); print(json.dumps({'decision':disp,'gates':result['gates'],'errors':errors},sort_keys=True))
if __name__=='__main__': main()
