from __future__ import annotations
import json, hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent; OUT=HERE/'formal-output'; M=json.loads((OUT/'manifest.json').read_text())
EXPECTED=[['p01-stable','stable'],['p01-swap','swap'],['p02-swap','swap'],['p02-stable','stable'],['p03-stable','stable'],['p03-swap','swap'],['p04-swap','swap'],['p04-stable','stable'],['p05-stable','stable'],['p05-swap','swap'],['p06-swap','swap'],['p06-stable','stable']]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 e=[]; counts={'stable':0,'swap':0}; wrong=0
 if M.get('formal_invocations')!=1:e.append('formal_invocations')
 if M.get('reruns')!=0:e.append('reruns')
 if M.get('schedule')!=EXPECTED:e.append('schedule')
 if len(M.get('cases',[]))!=12:e.append('case_count')
 for cid,arm in EXPECTED:
  p=OUT/cid/'result.json'
  if not p.exists():e.append(f'{cid}:missing');continue
  r=json.loads(p.read_text());counts[arm]+=1
  if r.get('case_id')!=cid or r.get('arm')!=arm:e.append(f'{cid}:identity')
  if r.get('gate_contract')!={'radius':5,'max_pixel_error_le':8.0}:e.append(f'{cid}:gate_contract')
  if r.get('gate_eligible') is not True or r.get('gate_diff',999)>8:e.append(f'{cid}:gate')
  if len(r.get('clicks',[]))!=1:e.append(f'{cid}:click_count');continue
  click=r['clicks'][0]
  pre_done=r['captures']['pre'][1]; final_start=r['captures']['final'][0]
  if not(pre_done <= r['gated_ns'] < r['click_started_ns'] <= r['click_done_ns'] <= final_start):e.append(f'{cid}:timeline')
  if r.get('button1_down_terminal') is not False:e.append(f'{cid}:button_terminal')
  if arm=='stable':
   if r.get('mutation') is not None:e.append(f'{cid}:unexpected_mutation')
   if click.get('role')!='task-target':e.append(f'{cid}:stable_wrong_role')
   if r.get('final_patch_diff_from_gated')!=0:e.append(f'{cid}:stable_patch_changed')
  else:
   mut=r.get('mutation') or {}; mt=mut.get('time_ns')
   if not isinstance(mt,int) or not(r['gated_ns'] < mt < r['click_started_ns']):e.append(f'{cid}:mutation_order')
   if click.get('role')!='decoy':e.append(f'{cid}:swap_not_decoy')
   else:wrong+=1
   if not(r.get('final_patch_diff_from_gated',0)>8):e.append(f'{cid}:swap_patch_not_changed')
   kinds=[x.get('event') for x in r.get('events',[])]
   if kinds!=['mutation','click']:e.append(f'{cid}:event_sequence')
 if counts!={'stable':6,'swap':6}:e.append('arm_counts')
 decision='PASS_TARGET_GATE_TOCTOU_EXPOSED_SCOPED' if not e and wrong==6 else ('HOLD_NO_TOCTOU_DISCRIMINATOR' if not e else 'FAIL_INTEGRITY_OR_FACTOR')
 report={'decision':decision,'errors':e,'arm_counts':counts,'swap_decoy_clicks':wrong,'source_sha256':{n:sha(HERE/n) for n in ['PLAN.md','app.py','run_case.py','run_block.py','audit.py']}}
 (OUT/'audit.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps(report,sort_keys=True));raise SystemExit(bool(e))
if __name__=='__main__':main()
