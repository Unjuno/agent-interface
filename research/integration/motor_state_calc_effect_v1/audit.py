import argparse,json
from pathlib import Path

def evaluate(rows):
 e=[]; ids=set(); wrong=0; cand_wrong=0; stable_ok=0; mismatch_refuse=0; unknown_refuse=0; unsupported_act=0
 for r in rows:
  cid=r.get('case_id')
  if cid in ids:e.append('duplicate:'+str(cid))
  ids.add(cid)
  if r.get('status')!='ok':e.append('status:'+str(cid)); continue
  if not r.get('held_observed') or not r.get('release_observed') or not r.get('neutral_final'):e.append('release:'+str(cid))
  cell=r.get('app_effect',{}).get('string',''); helper=r.get('helper_effect',''); s=r['scenario']; p=r['policy']; d=r['decision']
  if s=='stable':
   if d!='ACT' or cell!='7' or helper!='':e.append('stable:'+cid)
   else: stable_ok+=1
  elif s=='focus_transferred':
   if p=='naive_command':
    if d!='ACT' or cell!='' or helper!='7':e.append('naive_wrong_surface:'+cid)
    else: wrong+=1
   else:
    if d!='REFUSE_MISMATCH' or r.get('task_input_dispatched') or cell!='' or helper!='':e.append('guard_mismatch:'+cid)
    else:mismatch_refuse+=1
  elif s=='observer_unavailable':
   if p=='naive_command':
    if d!='ACT' or cell!='7':e.append('naive_unknown:'+cid)
    else:unsupported_act+=1
   else:
    if d!='REFUSE_UNKNOWN' or r.get('task_input_dispatched') or cell!='' or helper!='':e.append('guard_unknown:'+cid)
    else:unknown_refuse+=1
  if p=='observed_guard' and helper=='7':cand_wrong+=1
 if len(rows)!=18:e.append('rows:'+str(len(rows)))
 if len(ids)!=18:e.append('ids:'+str(len(ids)))
 exp={'stable_correct_effects':6,'naive_wrong_surface_effects':3,'candidate_wrong_surface_effects':0,'candidate_mismatch_refusals':3,'candidate_unknown_refusals':3,'naive_unsupported_actions':3}
 got={'stable_correct_effects':stable_ok,'naive_wrong_surface_effects':wrong,'candidate_wrong_surface_effects':cand_wrong,'candidate_mismatch_refusals':mismatch_refuse,'candidate_unknown_refusals':unknown_refuse,'naive_unsupported_actions':unsupported_act}
 if got!=exp:e.append('counts:'+json.dumps(got,sort_keys=True))
 return {'rows':len(rows),'counts':got,'errors':e,'decision':'PASS_MOTOR_STATE_EFFECT_GUARD_SCOPED' if not e else 'FAIL_OR_HOLD'}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('dirs',nargs='+');a=ap.parse_args();rows=[]
 for d in a.dirs:rows+=json.loads((Path(d)/'RAW.json').read_text())['rows']
 out=evaluate(rows);print(json.dumps(out,sort_keys=True));return 0 if not out['errors'] else 2
if __name__=='__main__':raise SystemExit(main())
