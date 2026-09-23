#!/usr/bin/env python3
import argparse, json, hashlib
from pathlib import Path

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--result',required=True); ap.add_argument('--out',required=True); a=ap.parse_args()
 r=json.loads(Path(a.result).read_text()); errors=[]
 if r.get('formal_invocations')!=1 or r.get('formal_reruns')!=0: errors.append('formal_count')
 if len(r.get('rows',[]))!=4: errors.append('row_count')
 seeds=[x.get('seed') for x in r.get('rows',[])]
 if seeds!=[9051701,9051702,9051703,9051704]: errors.append('seed_order')
 if r.get('config',{}).get('exec_conf')!=0.90: errors.append('exec_conf')
 viol=[]; mean_red=[]; p50_red=[]; faster=0; p95_reg=[]
 for row in r.get('rows',[]):
  s=row['seed']; o=row['ordinary']; st=row['stress']; tf=row['timing_ms']['FULL_DEPTH']; ta=row['timing_ms']['DIRECT_TTC']
  for setname,m,amin,agmin in [('ordinary',o,.98,.99),('stress',st,.94,.98)]:
   if m['FULL_DEPTH']['accuracy']<amin: viol.append(f'{s}:{setname}:full_accuracy')
   if m['DIRECT_TTC']['accuracy']<amin: viol.append(f'{s}:{setname}:ttc_accuracy')
   if m['DIRECT_TTC']['agreement_with_full']<agmin: viol.append(f'{s}:{setname}:agreement')
   if m['DIRECT_TTC']['teacher_yield_to_exec_rate']-m['FULL_DEPTH']['teacher_yield_to_exec_rate']>.0025+1e-12: viol.append(f'{s}:{setname}:yield_exec_delta')
   if m['DIRECT_TTC']['premature_yield']!=0: viol.append(f'{s}:{setname}:premature_yield')
  if o['DIRECT_TTC']['premature_exec']!=0: viol.append(f'{s}:ordinary:premature_exec')
  if st['DIRECT_TTC']['premature_exec_rate']>.001+1e-12: viol.append(f'{s}:stress:premature_exec')
  if o['DIRECT_TTC']['mean_normalized_compute']>.70: viol.append(f'{s}:ordinary:compute')
  if st['DIRECT_TTC']['mean_normalized_compute']>.80: viol.append(f'{s}:stress:compute')
  if sum(1 for c in o['DIRECT_TTC']['exit_counts'] if c>0)<3: viol.append(f'{s}:exit_diversity')
  mr=1-ta['mean']/tf['mean']; pr=1-ta['p50']/tf['p50']; rr=ta['p95']/tf['p95']-1
  mean_red.append(mr);p50_red.append(pr);p95_reg.append(rr)
  if ta['mean']<tf['mean']: faster+=1
  if rr>.10: viol.append(f'{s}:p95_regression')
 import numpy as np
 medm=float(np.median(mean_red)); medp=float(np.median(p50_red))
 competence=not any('full_accuracy' in v for v in viol)
 correctness=not any(any(k in v for k in ['ttc_accuracy','agreement','yield_exec_delta','premature_yield','premature_exec']) for v in viol)
 speed=medm>=.25 and medp>=.25 and faster>=3
 compute=not any(('compute' in v or 'exit_diversity' in v) for v in viol)
 if competence and correctness and speed and compute and not any('p95_regression' in v for v in viol): dec='PASS_DIRECT_TTC_SCOPED'
 elif not competence: dec='HOLD_COMPETENCE_NOT_CLOSED'
 elif not correctness: dec='HOLD_TTC_SAFETY_OR_TRANSFER'
 elif compute and not speed: dec='NO_REALIZED_TTC_SPEEDUP'
 else: dec='HOLD_TTC_SAFETY_OR_TRANSFER'
 if dec!=r.get('decision'): errors.append(f'decision:{dec}!={r.get("decision")}')
 if viol!=r.get('gates',{}).get('violations'): errors.append('violations_mismatch')
 audit={'audit':'PASS' if not errors else 'FAIL','errors':errors,'result_sha256':sha(a.result),'recomputed_decision':dec,'recomputed':{'median_mean_latency_reduction':medm,'median_p50_latency_reduction':medp,'adaptive_mean_faster_pairs':faster,'p95_regressions':p95_reg,'violations':viol}}
 Path(a.out).write_text(json.dumps(audit,indent=2,sort_keys=True)+'\n'); print(json.dumps(audit,sort_keys=True))
if __name__=='__main__': main()
