#!/usr/bin/env python3
import argparse, json, hashlib
from pathlib import Path
import numpy as np
YIELD=6; DEPTH=4

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--result',required=True); ap.add_argument('--evidence',required=True); ap.add_argument('--out',required=True); a=ap.parse_args()
 r=json.loads(Path(a.result).read_text()); z=np.load(a.evidence)
 errors=[]; rows=[]
 for row in r['rows']:
  seed=row['seed']; arm=row['arm']; pre=f'{seed}_{arm}'
  for split in ['ordinary','stress']:
   p=z[f'{pre}_'+('po' if split=='ordinary' else 'ps')]; d=z[f'{pre}_'+('do' if split=='ordinary' else 'ds')]
   # Reconstruct teacher labels from result-free deterministic fixture source is not duplicated here; verify retained aggregate structural metrics.
   if len(p)!=row[split]['n'] or len(d)!=row[split]['n']: errors.append(f'{pre}:{split}:n')
   if not np.all((p>=0)&(p<=YIELD)): errors.append(f'{pre}:{split}:vocab')
   if not np.all((d>=1)&(d<=DEPTH)): errors.append(f'{pre}:{split}:depth')
   counts=[int(np.sum(d==k)) for k in range(1,DEPTH+1)]
   if counts!=row[split]['exit_counts']: errors.append(f'{pre}:{split}:exit_counts')
   if abs(float(np.mean(d)/DEPTH)-row[split]['mean_normalized_compute'])>1e-12: errors.append(f'{pre}:{split}:compute')
  l=z[f'{pre}_lats']
  p95=float(np.percentile(l,95,method='linear'))
  if abs(p95-row['latency_ms']['p95'])>1e-9: errors.append(f'{pre}:p95')
 # Independently recompute decision gates from retained summaries.
 by={}
 for row in r['rows']: by.setdefault(row['seed'],{})[row['arm']]=row
 reds=[]; ol=[]; sl=[]; faster=0; comp=0; violations=[]
 for s,pair in sorted(by.items()):
  b=pair['ACCURACY_ONLY']; c=pair['LATENCY_AWARE']
  reds.append(1-c['latency_ms']['p95']/b['latency_ms']['p95']); faster+=c['latency_ms']['p95']<b['latency_ms']['p95']; comp+=c['ordinary']['mean_normalized_compute']<b['ordinary']['mean_normalized_compute']
  ol.append(b['ordinary']['accuracy']-c['ordinary']['accuracy']); sl.append(b['stress']['accuracy']-c['stress']['accuracy'])
  if c['ordinary']['accuracy']<.90: violations.append(f'{s}:ordinary_accuracy')
  if c['stress']['accuracy']<.80: violations.append(f'{s}:stress_accuracy')
  if c['ordinary']['teacher_yield_to_exec_rate']>b['ordinary']['teacher_yield_to_exec_rate']+.005: violations.append(f'{s}:yield_safety')
  if c['ordinary']['predicted_yield_n']==0: violations.append(f'{s}:yield_unreachable')
 medred=float(np.median(reds)); medol=float(np.median(ol)); medsl=float(np.median(sl))
 if not violations and medred>=.20 and faster>=3 and medol<=.015 and medsl<=.025 and comp>=3: disp='PASS_LATENCY_AWARE_EARLY_EXIT_SCOPED'
 elif comp>=3 and medred<.20: disp='NO_MEASURED_LATENCY_EFFECT'
 elif comp>=3 or medred>0: disp='HOLD_LATENCY_OBJECTIVE_TRADEOFF_NOT_CLOSED'
 else: disp='REJECT_LATENCY_OBJECTIVE'
 if disp!=r['decision']: errors.append('decision_mismatch')
 audit={'audit':'PASS' if not errors else 'FAIL','decision':disp,'errors':errors,'recomputed':{'median_p95_reduction':medred,'faster_pairs':int(faster),'median_ordinary_loss_pp':medol*100,'median_stress_loss_pp':medsl*100,'compute_better_pairs':int(comp),'violations':violations},'result_sha256':hashlib.sha256(Path(a.result).read_bytes()).hexdigest(),'evidence_sha256':hashlib.sha256(Path(a.evidence).read_bytes()).hexdigest()}
 Path(a.out).write_text(json.dumps(audit,indent=2,sort_keys=True)+'\n'); print(json.dumps(audit,sort_keys=True))
if __name__=='__main__': main()
