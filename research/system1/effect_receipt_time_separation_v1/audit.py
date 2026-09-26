#!/usr/bin/env python3
import argparse,json,pathlib
SCHEDULES={'ON_TIME_FAST_RECEIPT','ON_TIME_LATE_RECEIPT','LATE_COMMIT_FAST_RECEIPT','NO_COMMIT'}
POLICIES={'RECEIPT_ARRIVAL_DEADLINE','OWNER_COMMIT_DEADLINE','COMMIT_FIELD_UNVERIFIED'}
def audit(root,reps):
 rows=json.loads((pathlib.Path(root)/'ROWS.json').read_text()); errors=[]
 if len(rows)!=reps*12: errors.append(f'row_count:{len(rows)}')
 ids=set()
 for r in rows:
  cid=r['case_id'];
  if cid in ids: errors.append('duplicate:'+cid)
  ids.add(cid)
  if r['owner_exit']!=0: errors.append('exit:'+cid)
  if r['authority'] or r['retry_authority']: errors.append('authority:'+cid)
  rec=r['receipt']; j=r['journal']; s=r['schedule']; p=r['policy']; d=r['deadline_ns']
  if s=='NO_COMMIT':
   if r['effect_exists'] or j is not None or r['decision']!='NO_EFFECT': errors.append('no_commit:'+cid)
   continue
  if not r['effect_exists'] or not j: errors.append('missing_effect:'+cid); continue
  if j['commit_ns']!=rec['commit_ns'] or j['session']!=rec['session'] or j['request']!=rec['request']: errors.append('identity:'+cid)
  ontime=j['commit_ns']<=d; receipt_ontime=rec['receipt_ns']<=d
  if s.startswith('ON_TIME_') and not ontime: errors.append('expected_commit_ontime:'+cid)
  if s=='LATE_COMMIT_FAST_RECEIPT' and ontime: errors.append('expected_commit_late:'+cid)
  if p=='RECEIPT_ARRIVAL_DEADLINE':
   exp='ON_TIME' if receipt_ontime else 'LATE'
  elif p=='OWNER_COMMIT_DEADLINE': exp='ON_TIME' if ontime else 'LATE'
  else: exp='UNKNOWN'
  if r['decision']!=exp: errors.append('decision:'+cid)
 return {'decision':'PASS_EFFECT_RECEIPT_TIME_SEPARATION_SCOPED' if not errors else 'FAIL_OR_HOLD','rows':len(rows),'errors':errors}
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('root'); ap.add_argument('--reps',type=int,required=True); ap.add_argument('--out'); a=ap.parse_args(); res=audit(a.root,a.reps); t=json.dumps(res,indent=2,sort_keys=True)+'\n'; print(t,end='');
 if a.out:pathlib.Path(a.out).write_text(t)
 raise SystemExit(0 if not res['errors'] else 1)
if __name__=='__main__': main()
