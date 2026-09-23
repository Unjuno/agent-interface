#!/usr/bin/env python3
import argparse,json,pathlib
SCHEDULES=("EARLY_SHORT","NEAR_SHORT","EARLY_LONG","NEAR_LONG"); LONG={"EARLY_LONG","NEAR_LONG"}
def load(root):
 rows=[]
 for rep in range(3):
  for sched in SCHEDULES:
   rows += json.loads((pathlib.Path(root)/f"r{rep}-{sched}"/"ROWS.json").read_text())
 return rows
def audit_rows(rows):
 errors=[]; ids=set()
 if len(rows)!=36: errors.append(f"row_count:{len(rows)}!=36")
 for r in rows:
  cid=r['case_id']
  if cid in ids: errors.append('duplicate:'+cid)
  ids.add(cid)
  if type(r['rep']) is not int or r['rep'] not in (0,1,2): errors.append('rep:'+cid)
  if r['authority'] is not False: errors.append('authority:'+cid)
  if r['app_exit']!=0: errors.append('app_exit:'+cid)
  if r['proposal_ready_elapsed_ms']>120 or r['predispatch_elapsed_ms']>120: errors.append('pre_handoff_late:'+cid)
  ar=r['app_receipt']
  if not isinstance(ar,dict) or ar.get('type')!='APP_RESULT': errors.append('app_receipt:'+cid); continue
  if ar.get('app_check_ns',10**30)>r['start_ns']+120_000_000: errors.append('app_check_late:'+cid)
  if ar.get('sink_exit')!=0: errors.append('sink_exit:'+cid)
  sr=ar.get('sink_receipt'); eff=r.get('effect_file'); long=r['schedule'] in LONG
  if not isinstance(sr,dict): errors.append('sink_receipt:'+cid); continue
  if eff is not None and (eff.get('case_id')!=cid or eff.get('sink_pid')!=sr.get('sink_pid') or eff.get('effect_ns')!=sr.get('effect_ns')): errors.append('effect_lineage:'+cid)
  if r['policy'] in ('APP_CHECK_ONLY','SINK_POSTHOC_CHECK'):
   if not sr.get('effect_committed') or eff is None: errors.append('baseline_noeffect:'+cid)
   if long and sr.get('within_deadline') is not False: errors.append('baseline_long_not_late:'+cid)
   if not long and sr.get('within_deadline') is not True: errors.append('baseline_short_not_ontime:'+cid)
   if r['policy']=='SINK_POSTHOC_CHECK' and sr.get('posthoc') != ('LATE' if long else 'ON_TIME'): errors.append('posthoc:'+cid)
  else:
   if long and (sr.get('effect_committed') or sr.get('effect_ns') is not None or eff is not None or sr.get('type')!='SINK_REFUSED_DEADLINE'): errors.append('candidate_late_effect:'+cid)
   if not long and (not sr.get('effect_committed') or eff is None or sr.get('within_deadline') is not True): errors.append('candidate_short_refuse:'+cid)
 return {'decision':'PASS_EFFECT_OWNER_DEADLINE_SCOPED' if not errors else 'FAIL_OR_HOLD','rows':len(rows),'errors':errors}
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('root'); ap.add_argument('--out'); a=ap.parse_args(); result=audit_rows(load(a.root)); s=json.dumps(result,indent=2,sort_keys=True)+'\n';
 if a.out:pathlib.Path(a.out).write_text(s)
 print(s,end=''); raise SystemExit(0 if not result['errors'] else 1)
if __name__=='__main__': main()
