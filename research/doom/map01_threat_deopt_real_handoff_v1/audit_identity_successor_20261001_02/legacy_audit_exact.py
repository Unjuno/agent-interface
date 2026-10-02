import argparse,json
from pathlib import Path

def release_ok(execrow):
 if not execrow:return False
 t=execrow.get('terminal',{});r=t.get('release',{})
 return t.get('status')=='completed' and r.get('verified') is True and r.get('keys_down')==[] and r.get('buttons_down')==[]
def audit(rows):
 errors=[]
 if len(rows)!=6:errors.append('case_count')
 if [r.get('arm') for r in rows]!=['baseline','candidate','candidate','baseline','baseline','candidate']:errors.append('order')
 for r in rows:
  i=r.get('id');a=r.get('active_arbitration',{});p=r.get('post_handoff_arbitration',{})
  if a.get('selected',{}).get('locomotion',{}).get('proposal_id')!='threat-g1':errors.append(i+':active_selection')
  if any(d.get('proposal_id')=='deopt-g1' for d in a.get('selected',{}).values()):errors.append(i+':active_deopt')
  if not release_ok(r.get('threat_exec')):errors.append(i+':threat_release')
  sc=r.get('score',{})
  if any(k not in sc or sc.get(k) is None for k in ('kill_count','death_count','map_exit','player_dead')):errors.append(i+':score_evidence')
  if r.get('final_health') is None or r.get('final_ammo') is None:errors.append(i+':signal_evidence')
  if 'Traceback' in r.get('stderr',''):errors.append(i+':stderr')
  if r.get('arm')=='baseline':
   if p.get('selected',{}).get('locomotion',{}).get('proposal_id')!='deopt-g1':errors.append(i+':baseline_stale_selection')
   if r.get('stale_submit_count')!=1 or not release_ok(r.get('stale_exec')):errors.append(i+':baseline_stale_exec')
   if r.get('fresh_exec') is not None:errors.append(i+':baseline_fresh')
  else:
   if 'locomotion' in p.get('selected',{}):errors.append(i+':candidate_stale_selected')
   if not any(d.get('proposal_id')=='deopt-g1' and d.get('reason')=='STALE_RESOURCE_GENERATION' for d in p.get('deferred',[])):errors.append(i+':candidate_stale_reason')
   if r.get('stale_submit_count')!=0 or r.get('stale_exec') is not None:errors.append(i+':candidate_stale_submit')
   if r.get('fresh_arbitration',{}).get('selected',{}).get('locomotion',{}).get('proposal_id')!='deopt-g2':errors.append(i+':candidate_fresh_selection')
   if not release_ok(r.get('fresh_exec')):errors.append(i+':candidate_fresh_exec')
 return {'decision':'PASS_REAL_MAP01_AUTHORITY_HANDOFF_FENCE_SCOPED' if not errors else 'FAIL_REAL_MAP01_AUTHORITY_HANDOFF_FENCE_SCOPED','errors':errors,'case_count':len(rows),'baseline_stale_execs':sum(r.get('stale_submit_count',0) for r in rows if r.get('arm')=='baseline'),'candidate_stale_execs':sum(r.get('stale_submit_count',0) for r in rows if r.get('arm')=='candidate'),'candidate_fresh_execs':sum(1 for r in rows if r.get('arm')=='candidate' and r.get('fresh_exec'))}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('root',type=Path);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();rows=[]
 plan=json.loads((a.root/'plan.json').read_text())
 for c in plan['cases']:rows.append(json.loads((a.root/c['id']/'result.json').read_text()))
 o=audit(rows);a.out.write_text(json.dumps(o,indent=2,sort_keys=True)+'\n');print(json.dumps(o,indent=2,sort_keys=True))
if __name__=='__main__':main()
