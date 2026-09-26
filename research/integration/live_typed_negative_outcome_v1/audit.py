from __future__ import annotations
import argparse, copy, json, pathlib, sys
EXPECTED_REQUIRED={
 'SUCCEEDED':'none','IN_PROGRESS':'wait_or_reobserve','BLOCKED':'clear_blocker','AUTHORITY_REQUIRED':'fresh_authority',
 'TARGET_NOT_FOUND':'new_target_or_observation','CAPABILITY_UNSUPPORTED':'different_action','CONFLICT':'reobserve_or_reconcile',
 'IMPOSSIBLE_UNDER_CONSTRAINTS':'planner_reconsideration','FAILED_UNKNOWN':'new_observation'}
def oracle(e):
 effects=e['effect_receipts']
 if len(effects)>1 and len({x['value'] for x in effects})>1: return 'CONFLICT'
 if not e['evidence_complete']: return 'FAILED_UNKNOWN'
 if not e['constraints_satisfiable']: return 'IMPOSSIBLE_UNDER_CONSTRAINTS'
 if not e['capability_supported']: return 'CAPABILITY_UNSUPPORTED'
 if not e['target_present']: return 'TARGET_NOT_FOUND'
 if not e['authority_current']: return 'AUTHORITY_REQUIRED'
 if e['modal_blocking']: return 'BLOCKED'
 if len(effects)==1 and effects[0]['request_id']==e['request_id'] and effects[0]['value']=='DONE': return 'SUCCEEDED'
 if e['input_dispatched'] and e['app_request_seen'] and e['pending_receipt']: return 'IN_PROGRESS'
 return 'FAILED_UNKNOWN'
def check(root):
 rows=[]; errors=[]
 for p in sorted(pathlib.Path(root).glob('case-*/raw.json')):
  r=json.loads(p.read_text()); rows.append(r); o=oracle(r['evidence'])
  if o!=r['decision']['label']: errors.append([r['case_index'],'oracle',o,r['decision']['label']])
  if r['decision']['label']!=r['expected']: errors.append([r['case_index'],'expected',r['expected'],r['decision']['label']])
  if r['decision']['authority_granted'] is not False: errors.append([r['case_index'],'authority'])
  if r['decision']['identical_retry_allowed'] is not False: errors.append([r['case_index'],'retry'])
  if r['decision']['required_change']!=EXPECTED_REQUIRED[r['decision']['label']]: errors.append([r['case_index'],'required'])
  if r['app_exit']!=0: errors.append([r['case_index'],'app_exit'])
 # semantics independent of scenario names where possible
 for r in rows:
  e=r['evidence']; lab=r['decision']['label']
  if lab in {'BLOCKED','AUTHORITY_REQUIRED','TARGET_NOT_FOUND','CAPABILITY_UNSUPPORTED','IMPOSSIBLE_UNDER_CONSTRAINTS'} and e['input_dispatched']:
   errors.append([r['case_index'],'precondition_input'])
  if lab=='SUCCEEDED' and not r['scoring_final']['hidden_effect']: errors.append([r['case_index'],'success_effect'])
  if lab=='IN_PROGRESS' and not r['scoring_final']['hidden_effect']: errors.append([r['case_index'],'progress_never_completed'])
 return rows,errors
def mutations(root):
 rows,_=check(root); base=copy.deepcopy(rows[0]); muts=[]
 def rejected(tag,mut):
  e=mut['evidence']; d=mut['decision']; return oracle(e)!=d['label'] or d.get('authority_granted') is not False or d.get('identical_retry_allowed') is not False or d.get('required_change')!=EXPECTED_REQUIRED.get(d.get('label'))
 m=copy.deepcopy(base); m['decision']['label']='SUCCEEDED'; m['evidence']['effect_receipts']=[]; muts.append(('false_success',rejected('x',m)))
 m=copy.deepcopy(base); m['decision']['authority_granted']=True; muts.append(('authority',rejected('x',m)))
 m=copy.deepcopy(base); m['decision']['identical_retry_allowed']=True; muts.append(('retry',rejected('x',m)))
 m=copy.deepcopy(base); m['decision']['required_change']='different_action'; muts.append(('required',rejected('x',m)))
 m=copy.deepcopy(base); m['evidence']['evidence_complete']=False; muts.append(('completeness',rejected('x',m)))
 m=copy.deepcopy(base); m['evidence']['target_present']=False; muts.append(('target',rejected('x',m)))
 m=copy.deepcopy(base); m['evidence']['authority_current']=False; muts.append(('authority_current',rejected('x',m)))
 m=copy.deepcopy(base); m['evidence']['capability_supported']=False; muts.append(('capability',rejected('x',m)))
 m=copy.deepcopy(base); m['evidence']['constraints_satisfiable']=False; muts.append(('constraint',rejected('x',m)))
 m=copy.deepcopy(base); m['evidence']['modal_blocking']=True; muts.append(('modal',rejected('x',m)))
 return dict(muts)
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('root'); ap.add_argument('--mutations',action='store_true'); args=ap.parse_args()
 rows,errors=check(args.root); out={'rows':len(rows),'errors':errors}
 if args.mutations: out['mutations']=mutations(args.root)
 print(json.dumps(out,indent=2,sort_keys=True)); raise SystemExit(1 if errors else 0)
if __name__=='__main__': main()
