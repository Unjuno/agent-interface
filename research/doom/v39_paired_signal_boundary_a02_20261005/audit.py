import copy,json,sys
from pathlib import Path
EXPECTED={'valid_pair_preserves_cover':(None,None),'health_ammo_sequence_mismatch':('signal_pair_epoch_mismatch','UNKNOWN'),'health_ammo_capture_mismatch':('signal_pair_epoch_mismatch','UNKNOWN'),'health_ammo_binding_mismatch':('signal_pair_epoch_mismatch','UNKNOWN'),'health_below_floor':('health:below_floor','HARD_INVALIDATED'),'ammo_below_floor':('ammo:below_floor','HARD_INVALIDATED'),'duplicate_epoch_same_projection':(None,None),'duplicate_epoch_frame_disagreement':('signal_pair_duplicate_epoch_mismatch','UNKNOWN'),'missing_typed_signal':('signal_pair_epoch_mismatch','UNKNOWN')}
def validate(raw):
 errors=[]; cases=raw.get('cases')
 if type(cases) is not list or len(cases)!=len(EXPECTED): return ['case_count']
 names=[]
 for c in cases:
  name=c.get('case'); names.append(name)
  if name not in EXPECTED: errors.append(f'{name}:unexpected_case'); continue
  er,es=EXPECTED[name]; r=c.get('observed')
  if c.get('expected')!={'reason':er,'outcome_status':es}: errors.append(f'{name}:expected_contract')
  if er is None:
   if r is not None: errors.append(f'{name}:expected_no_invalidation')
   continue
  if type(r) is not dict: errors.append(f'{name}:missing_receipt'); continue
  if r.get('event')!='paired_signal_invalidation' or r.get('reason')!=er: errors.append(f'{name}:event_reason')
  if r.get('requires_new_decision') is not True: errors.append(f'{name}:top_requires_decision')
  if r.get('grants_input_authority') is not False: errors.append(f'{name}:top_grants_authority')
  o=r.get('outcome')
  if type(o) is not dict: errors.append(f'{name}:missing_outcome'); continue
  if o.get('status')!=es: errors.append(f'{name}:outcome_status')
  if o.get('requires_new_decision') is not True: errors.append(f'{name}:outcome_requires_decision')
  if o.get('grants_input_authority') is not False: errors.append(f'{name}:outcome_grants_authority')
  if o.get('may_only_preserve_or_reduce_existing_authority') is not True: errors.append(f'{name}:outcome_authority_bound')
  if o.get('task_success_verified') is not False: errors.append(f'{name}:task_success')
 if len(set(names))!=len(EXPECTED) or set(names)!=set(EXPECTED): errors.append('case_identity_set')
 for key in ('real_input_used','live_game_used','planner_used'):
  if raw.get(key) is not False: errors.append(f'scope:{key}')
 return errors
def selftest(raw):
 checks=0
 assert validate(raw)==[]; checks+=1
 for path,value in [(('cases',1,'observed','grants_input_authority'),True),(('cases',1,'observed','requires_new_decision'),False),(('cases',1,'observed','outcome','grants_input_authority'),True),(('cases',1,'observed','outcome','requires_new_decision'),False),(('cases',4,'observed','outcome','task_success_verified'),True)]:
  bad=copy.deepcopy(raw); cur=bad
  for k in path[:-1]: cur=cur[k]
  cur[path[-1]]=value
  assert validate(bad),path
  checks+=1
 return checks
r=json.loads(Path(sys.argv[1]).read_text()); errs=validate(r)
if errs: print(json.dumps({'audit':'FAIL','errors':errs})); raise SystemExit(1)
checks=selftest(r)
print(json.dumps({'audit':'PASS','raw_checks':9*8+4,'mutation_rejections':5,'checks':checks+9*8+4,'source_sha256':r['source_sha256']}))
