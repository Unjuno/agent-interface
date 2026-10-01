#!/usr/bin/env python3
import json, sys, hashlib
from pathlib import Path
import numpy as np
SEEDS=[9101701,9101702,9101703,9101704]; DEPTH=4; ACTIONS=6; YIELD=7

def recompute(npz_path,case):
 z=np.load(npz_path); errors=[]
 for sn in ['ordinary','stress']:
  y=z[f'{sn}_y']; diff=z[f'{sn}_difficulty']; required=np.where(y==YIELD,DEPTH,diff)
  for mode in ['FULL_DEPTH','DIRECT_TTC','CONSECUTIVE_CONFIRM']:
   p=z[f'{sn}_{mode}_preds']; d=z[f'{sn}_{mode}_depths']; m=case[sn][mode]
   checks={'accuracy':float(np.mean(p==y)),'teacher_yield_to_exec':int(np.sum((y==YIELD)&(p<ACTIONS))),'premature_exec':int(np.sum((d<required)&(p<ACTIONS))),'premature_yield':int(np.sum((d<required)&(p==YIELD))),'mean_depth':float(d.mean()),'mean_normalized_compute':float(d.mean()/DEPTH),'exit_counts':[int(np.sum(d==k)) for k in range(1,DEPTH+1)]}
   for k,v in checks.items():
    if isinstance(v,float):
     if abs(v-float(m[k]))>1e-12: errors.append(f'{sn}:{mode}:{k}')
    elif v!=m[k]: errors.append(f'{sn}:{mode}:{k}')
  fp=z[f'{sn}_FULL_DEPTH_preds']
  for mode in ['DIRECT_TTC','CONSECUTIVE_CONFIRM']:
   agree=float(np.mean(fp==z[f'{sn}_{mode}_preds']))
   if abs(agree-case[sn][mode]['agreement_with_full'])>1e-12: errors.append(f'{sn}:{mode}:agreement')
 for mode in ['FULL_DEPTH','DIRECT_TTC','CONSECUTIVE_CONFIRM']:
  vals=z[f'lat_{mode}']; t=case['timing_ms'][mode]
  calc={'p50':float(np.percentile(vals,50,method='linear')),'p95':float(np.percentile(vals,95,method='linear')),'p99':float(np.percentile(vals,99,method='linear')),'max':float(vals.max()),'mean':float(vals.mean())}
  for k,v in calc.items():
   if abs(v-float(t[k]))>1e-12: errors.append(f'timing:{mode}:{k}')
 return errors

def main(root,result_path,out):
 result=json.loads(Path(result_path).read_text()); errors=[]; seen=[]
 for s in SEEDS:
  cpath=Path(root)/str(s)/'CASE.json'; npath=Path(root)/str(s)/'CASE_EVIDENCE.npz'
  if not cpath.exists() or not npath.exists(): errors.append(f'missing:{s}'); continue
  case=json.loads(cpath.read_text()); seen.append(case['seed']); errors.extend([f'{s}:{x}' for x in recompute(npath,case)])
 if seen!=SEEDS: errors.append('seed_order')
 if result.get('formal_reruns')!=0 or result.get('formal_cases')!=4: errors.append('formal_counts')
 audit={'pass':not errors,'errors':errors,'case_evidence_sha256':{str(s):hashlib.sha256((Path(root)/str(s)/'CASE_EVIDENCE.npz').read_bytes()).hexdigest() for s in SEEDS if (Path(root)/str(s)/'CASE_EVIDENCE.npz').exists()}}
 Path(out).write_text(json.dumps(audit,indent=2,sort_keys=True)+'\n'); print(json.dumps({'pass':audit['pass'],'errors':errors},sort_keys=True))
if __name__=='__main__': main(sys.argv[1],sys.argv[2],sys.argv[3])
