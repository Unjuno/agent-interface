from __future__ import annotations
import json,hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent;OUT=HERE/'formal-output';M=json.loads((OUT/'manifest.json').read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 e=[];counts={};stats={'no_reval_swap_decoy':0,'reval_swap_stale_zero_click':0,'reval_stable_target':0,'no_reval_stable_target':0}
 if M.get('formal_invocations')!=1:e.append('formal_invocations')
 if M.get('reruns')!=0:e.append('reruns')
 if len(M.get('cases',[]))!=16:e.append('case_count')
 for entry in M.get('cases',[]):
  cid=entry['case_id'];state=entry['state'];policy=entry['policy'];k=f'{state}:{policy}';counts[k]=counts.get(k,0)+1
  p=OUT/cid/'result.json'
  if not p.exists():e.append(f'{cid}:missing');continue
  r=json.loads(p.read_text());clicks=r.get('clicks',[])
  if not r.get('initial_gate_eligible') or r.get('initial_gate_diff',999)>8:e.append(f'{cid}:initial_gate')
  if r.get('gate_contract')!={'radius':5,'max_pixel_error_le':8.0}:e.append(f'{cid}:contract')
  if r.get('button1_down_terminal') is not False:e.append(f'{cid}:button')
  if policy=='revalidate':
   rv=r.get('revalidation')
   if not isinstance(rv,dict):e.append(f'{cid}:missing_revalidation');continue
   if state=='stable':
    if not(rv.get('patch_diff')==0 and r.get('disposition')=='CURRENT_TARGET' and len(clicks)==1 and clicks[0].get('role')=='task-target'):e.append(f'{cid}:stable_candidate')
    else:stats['reval_stable_target']+=1
   else:
    mt=(r.get('mutation') or {}).get('time_ns');rs=rv.get('capture_started_ns')
    if not(isinstance(mt,int) and isinstance(rs,int) and r['gated_ns']<mt<rs):e.append(f'{cid}:mutation_reval_order')
    if not(rv.get('patch_diff',0)>8 and r.get('disposition')=='STALE_TARGET' and r.get('input_allowed') is False and len(clicks)==0):e.append(f'{cid}:swap_candidate_escape')
    else:stats['reval_swap_stale_zero_click']+=1
  else:
   if r.get('revalidation') is not None:e.append(f'{cid}:unexpected_revalidation')
   if state=='stable':
    if not(len(clicks)==1 and clicks[0].get('role')=='task-target'):e.append(f'{cid}:stable_control')
    else:stats['no_reval_stable_target']+=1
   else:
    if not(len(clicks)==1 and clicks[0].get('role')=='decoy'):e.append(f'{cid}:predecessor_not_reproduced')
    else:stats['no_reval_swap_decoy']+=1
 if counts!={'stable:no_revalidation':4,'stable:revalidate':4,'swap:no_revalidation':4,'swap:revalidate':4}:e.append('matrix_counts')
 if e:decision='FAIL_INTEGRITY_OR_REVALIDATION'
 elif stats['no_reval_swap_decoy']!=4:decision='HOLD_PREDECESSOR_NOT_REPRODUCED'
 else:decision='PASS_PREINPUT_PATCH_REVALIDATION_SCOPED'
 report={'decision':decision,'errors':e,'counts':counts,'stats':stats,'source_sha256':{n:sha(HERE/n) for n in ['PLAN.md','app.py','run_case.py','run_block.py','audit.py']}}
 (OUT/'audit.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps(report,sort_keys=True));raise SystemExit(bool(e))
if __name__=='__main__':main()
