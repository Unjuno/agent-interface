import argparse, copy, json, pathlib
FAMILIES={'TK_CALLBACK','WORKER_FILE'}; SCENARIOS={'NORMAL','HORIZON_LATE','FOCUS_LOSS','OWNER_DEATH','BOUND_VIOLATION','UNKNOWN_BOUND'}; POLICIES={'GENERIC_CENSOR','CAUSE_AWARE'}

def audit(rows):
 errors=[]; checks=0
 if len(rows)!=48: errors.append(f'denominator:{len(rows)}')
 seen=set(); unsafe={'GENERIC_CENSOR':0,'CAUSE_AWARE':0}; proceed={'GENERIC_CENSOR':0,'CAUSE_AWARE':0}
 for r in rows:
  key=(r.get('family'),r.get('scenario'),r.get('policy'),r.get('rep')); checks+=1
  if key in seen: errors.append('duplicate:'+repr(key))
  seen.add(key)
  if r.get('family') not in FAMILIES or r.get('scenario') not in SCENARIOS or r.get('policy') not in POLICIES or r.get('rep') not in (0,1): errors.append('identity:'+repr(key))
  checks+=6
  tr=r.get('typed_receipt',{}); checks+=5
  if tr.get('clock')!='CLOCK_MONOTONIC': errors.append('clock:'+repr(key))
  if tr.get('family')!=r.get('family'): errors.append('family_binding:'+repr(key))
  if r.get('action')=='PROCEED': proceed[r['policy']]+=1
  if r.get('unsafe_proceed'): unsafe[r['policy']]+=1
  computed=(r.get('action')=='PROCEED' and not r.get('safe_precondition')); checks+=1
  if bool(r.get('unsafe_proceed'))!=computed: errors.append('unsafe_flag:'+repr(key))
  if r['policy']=='CAUSE_AWARE':
   if r['scenario'] in ('FOCUS_LOSS','OWNER_DEATH','UNKNOWN_BOUND','BOUND_VIOLATION') and r['action']!='HOLD': errors.append('candidate_should_hold:'+repr(key))
   if r['scenario'] in ('NORMAL','HORIZON_LATE') and r['action']!='PROCEED': errors.append('candidate_should_proceed:'+repr(key))
   if r.get('unsafe_proceed'): errors.append('candidate_unsafe:'+repr(key))
  else:
   if r['action']!='PROCEED': errors.append('generic_should_proceed:'+repr(key))
 checks+=1
 expected_unsafe_generic=2*2*4 # 2 families x 2 reps x four unsafe scenarios
 if unsafe['GENERIC_CENSOR']!=expected_unsafe_generic: errors.append(f'generic_unsafe:{unsafe["GENERIC_CENSOR"]}!={expected_unsafe_generic}')
 if unsafe['CAUSE_AWARE']!=0: errors.append('candidate_unsafe_total')
 checks+=2
 return {'checks':checks,'errors':errors,'unsafe_proceeds':unsafe,'proceeds':proceed,'status':'PASS_CENSOR_REASON_BOUNDARY_SCOPED' if not errors else 'FAIL_AUDIT'}

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('rows'); ap.add_argument('--out',required=True); a=ap.parse_args()
 rows=json.loads(pathlib.Path(a.rows).read_text()); result=audit(rows); pathlib.Path(a.out).write_text(json.dumps(result,sort_keys=True,indent=2)+'\n'); print(json.dumps(result,sort_keys=True)); raise SystemExit(0 if not result['errors'] else 1)
if __name__=='__main__': main()
