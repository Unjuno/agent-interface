"""Independent raw-only integrity and join audit; intentionally does not import join.py."""
import copy, hashlib, json, subprocess
from pathlib import Path

PKG=Path(__file__).resolve().parent
raw_bytes=(PKG/'RAW.json').read_bytes(); raw=json.loads(raw_bytes)
lock=json.loads((PKG/'SOURCE_LOCK.json').read_text())
freeze=json.loads((PKG/'FREEZE.json').read_text())
refresh=json.loads((PKG/'BASE_REFRESH.json').read_text())
result=json.loads((PKG/'RESULT.json').read_text())
errors=[]
if hashlib.sha256(raw_bytes).hexdigest()!=result['raw_sha256']: errors.append('raw_hash')
if lock['current_main_commit']!=result['current_main_commit']: errors.append('source_commit')
if hashlib.sha256((PKG/'SOURCE_LOCK.json').read_bytes()).hexdigest()!=freeze.get('source_lock_sha256'): errors.append('source_lock_hash')
for name, expected in freeze.get('analysis_code_sha256', {}).items():
 if hashlib.sha256((PKG/name).read_bytes()).hexdigest()!=expected: errors.append('analysis_code_hash:'+name)
for line in (PKG/'SHA256SUMS').read_text().splitlines():
 expected, rel = line.split('  ', 1)
 if hashlib.sha256((PKG/rel).read_bytes()).hexdigest()!=expected: errors.append('manifest_hash:'+rel)
root=PKG.parents[2]
refresh_matches=0
for rel, item in lock['sources'].items():
 if item.get('source_commit')!=lock['current_main_commit']: errors.append('source_commit_binding:'+rel)
 fetched=subprocess.run(['git','-C',str(root),'show',f"{lock['current_main_commit']}:{rel}"],capture_output=True)
 if fetched.returncode or hashlib.sha256(fetched.stdout.replace(b'\r\n',b'\n')).hexdigest()!=item['sha256_lf_normalized']: errors.append('pinned_main_source:'+rel)
 if item['sha256_lf_normalized']!=result['source_hashes'].get(rel): errors.append('result_source_hash:'+rel)
 refreshed=subprocess.run(['git','-C',str(root),'show',f"{refresh['publication_base_main_at_refresh']}:{rel}"],capture_output=True)
 if not refreshed.returncode and hashlib.sha256(refreshed.stdout.replace(b'\r\n',b'\n')).hexdigest()==item['sha256_lf_normalized']: refresh_matches+=1
if refresh_matches!=refresh.get('locked_source_count') or refresh_matches!=refresh.get('locked_sources_identical_at_publication_base'): errors.append('base_refresh_source_parity')
# Separate implementation: use a tuple map and cross-check every authoritative identity field.
def ident(row): return (row.get('id'),row.get('step'),row.get('intent_token'),row.get('owner_id'),row.get('key'))
rows=raw.get('events',[])
downs=[r for r in rows if r.get('event')=='input_admission']; ups=[r for r in rows if r.get('event')=='input_release_transition']
dmap={}; umap={}
for r in downs:
 k=ident(r); dmap.setdefault(k,[]).append(r)
for r in ups:
 k=ident(r); umap.setdefault(k,[]).append(r)
if len(downs)!=2 or len(ups)!=2: errors.append('unexpected_event_counts')
if set(dmap)!=set(umap): errors.append('identity_sets')
if any(len(v)!=1 for v in list(dmap.values())+list(umap.values())): errors.append('identity_multiplicity')
audited=[]
for k in sorted(set(dmap)&set(umap), key=lambda x:(x[1],x[4])):
 d,u=dmap[k][0],umap[k][0]; rec=u.get('owner_thread_keyup_receipt')
 if not isinstance(rec,dict): errors.append('receipt_missing'); continue
 if tuple(rec.get(x) for x in ('intent_token','owner_id','key')) != (u.get('intent_token'),u.get('owner_id'),u.get('key')): errors.append('receipt_identity')
 if rec.get('operation')!='up' or rec.get('server_sync_completed') is not True: errors.append('receipt_unverified')
 times=(d.get('admitted_ns'),u.get('release_call_started_ns'),rec.get('owner_keyrelease_started_ns'),rec.get('owner_sync_returned_ns'),u.get('release_call_returned_ns'))
 if any(type(x) is not int for x in times) or tuple(sorted(times))!=times: errors.append('time_order')
 audited.append({'identity':dict(zip(('id','step','intent_token','owner_id','key'),k)),'admitted_ns':times[0],'release_call_started_ns':times[1],'owner_keyrelease_started_ns':times[2],'owner_sync_returned_ns':times[3],'release_call_returned_ns':times[4],'physical_verification_authoritative':False})
if audited!=result['independent_audit']['pairs']: errors.append('pair_reconstruction')
if 'independent_task_effects' in raw: errors.append('unexpected_effect_rows')
if result['independent_audit']['overall_status']!='PASS_IDENTITY_JOIN_SCOPED; HOLD_MISSING_TASK_EFFECT': errors.append('effect_boundary')
def independent_status(data):
 ev=data.get('events')
 if type(ev) is not list: return 'HOLD_INVALID_EVENT_CONTAINER'
 ds=[x for x in ev if type(x) is dict and x.get('event')=='input_admission']
 us=[x for x in ev if type(x) is dict and x.get('event')=='input_release_transition']
 fields=('id','step','intent_token','owner_id','key')
 def key(x):
  values=tuple(x.get(f) for f in fields)
  return values if type(values[0]) is str and type(values[1]) is int and all(type(v) is str and v for v in values[2:]) else None
 dk=[key(x) for x in ds]; uk=[key(x) for x in us]
 if any(x is None for x in dk+uk): return 'HOLD_MISSING_IDENTITY'
 from collections import Counter
 dc,uc=Counter(dk),Counter(uk)
 if any(n!=1 for n in list(dc.values())+list(uc.values())): return 'HOLD_AMBIGUOUS_IDENTITY'
 if dc!=uc: return 'HOLD_UNMATCHED_ADMISSION_OR_RELEASE'
 for u in us:
  r=u.get('owner_thread_keyup_receipt')
  if type(r) is not dict: return 'HOLD_MISSING_OWNER_RECEIPT'
  if any(r.get(f)!=u.get(f) for f in ('intent_token','owner_id','key')): return 'HOLD_RECEIPT_IDENTITY_MISMATCH'
  if r.get('operation')!='up' or r.get('server_sync_completed') is not True: return 'HOLD_UNVERIFIED_OWNER_RECEIPT'
  if u.get('owner_thread_keyup_verified') is not True or u.get('physical_verification_authoritative') is not False: return 'HOLD_RECEIPT_SCOPE_OR_VERIFICATION'
  d=next(d for d in ds if key(d)==key(u)); ts=(d.get('admitted_ns'),u.get('release_call_started_ns'),r.get('owner_keyrelease_started_ns'),r.get('owner_sync_returned_ns'),u.get('release_call_returned_ns'))
  if any(type(t) is not int for t in ts) or tuple(sorted(ts))!=ts: return 'FAIL_INVALID_OR_REVERSED_TIME_ORDER'
 ops=data.get('operations')
 if type(ops) is not list: return 'HOLD_MISSING_OPERATION_TRACE'
 idx=[i for i,x in enumerate(ops) if type(x) is dict and x.get('op')=='key-up']
 if len(idx)!=len(us): return 'HOLD_OPERATION_RELEASE_COUNT_MISMATCH'
 ordered=sorted(us,key=lambda x:x.get('release_call_started_ns',-1))
 if [ops[i].get('keycode') for i in idx]!=[x.get('owner_thread_keyup_receipt',{}).get('keycode') for x in ordered]: return 'FAIL_RELEASE_OPERATION_ORDER_MISMATCH'
 gap=ops[idx[0]+1:idx[1]] if len(idx)>=2 else []
 if gap!=data.get('between_up_operations'): return 'FAIL_INTER_UP_TRACE_MISMATCH'
 if any(x.get('op')=='query_keymap' for x in gap): return 'FAIL_INTER_UP_KEYMAP_QUERY'
 if data.get('keymap_queries_between_ups')!=0: return 'FAIL_INTER_UP_QUERY_COUNT'
 effects=data.get('independent_task_effects')
 return 'PASS_IDENTITY_JOIN_SCOPED; HOLD_MISSING_TASK_EFFECT' if type(effects) is not list or not effects else 'HOLD_EFFECT_LINKAGE_NOT_IMPLEMENTED'
mutations={}
x=copy.deepcopy(raw); x['events']=[e for e in x['events'] if e.get('event')!='input_release_transition']; mutations['missing_release']=x
x=copy.deepcopy(raw); u=next(e for e in x['events'] if e.get('event')=='input_release_transition'); x['events'].append(copy.deepcopy(u)); mutations['duplicate_release']=x
x=copy.deepcopy(raw); d=next(e for e in x['events'] if e.get('event')=='input_admission'); x['events'].append(copy.deepcopy(d)); mutations['duplicate_admission']=x
for field,value in [('key','F9'),('owner_id','wrong-owner'),('intent_token','wrong-token'),('step',99)]:
 x=copy.deepcopy(raw); u=next(e for e in x['events'] if e.get('event')=='input_release_transition'); u[field]=value; mutations['release_'+field]=x
x=copy.deepcopy(raw); u=next(e for e in x['events'] if e.get('event')=='input_release_transition'); u['owner_thread_keyup_receipt']['key']='F9'; mutations['receipt_key_mismatch']=x
x=copy.deepcopy(raw); u=next(e for e in x['events'] if e.get('event')=='input_release_transition'); u['physical_verification_authoritative']=True; mutations['authority_overclaim']=x
x=copy.deepcopy(raw); u=next(e for e in x['events'] if e.get('event')=='input_release_transition'); u['owner_thread_keyup_receipt']['owner_keyrelease_started_ns']=u['release_call_returned_ns']+1; mutations['reversed_time']=x
x=copy.deepcopy(raw); ix=[i for i,o in enumerate(x['operations']) if o.get('op')=='key-up']; x['operations'][ix[0]],x['operations'][ix[1]]=x['operations'][ix[1]],x['operations'][ix[0]]; mutations['reordered_keyup_operation']=x
x=copy.deepcopy(raw); ix=[i for i,o in enumerate(x['operations']) if o.get('op')=='key-up']; q={'op':'query_keymap','at_ns':x['operations'][ix[0]]['at_ns']+1}; x['operations'].insert(ix[0]+1,q); ix=[i for i,o in enumerate(x['operations']) if o.get('op')=='key-up']; x['between_up_operations']=x['operations'][ix[0]+1:ix[1]]; mutations['inter_up_keymap_query']=x
independent_mutations={name:independent_status(data) for name,data in mutations.items()}
if independent_mutations!=result.get('mutation_cases'): errors.append('mutation_reconstruction')
ops=raw.get('operations',[]); up_idx=[i for i,row in enumerate(ops) if row.get('op')=='key-up']; chronological=sorted(ups,key=lambda row:row.get('release_call_started_ns',-1)); actual_codes=[ops[i].get('keycode') for i in up_idx]; receipt_codes=[row.get('owner_thread_keyup_receipt',{}).get('keycode') for row in chronological]
if len(up_idx)!=len(ups) or actual_codes!=receipt_codes: errors.append('operation_release_order')
segment=ops[up_idx[0]+1:up_idx[1]] if len(up_idx)>=2 else []
if segment!=raw.get('between_up_operations'): errors.append('inter_up_copy')
if any(row.get('op')=='query_keymap' for row in segment) or raw.get('keymap_queries_between_ups')!=0: errors.append('inter_up_query')
checks=result.get('release_order_checks',{})
if checks.get('order_matches') is not True or checks.get('between_up_operations_matches_copy') is not True or checks.get('keymap_queries_between_ups')!=0: errors.append('result_order_checks')
report={'schema':'v39-effect-identity-independent-audit-v1','status':'PASS_RAW_JOIN_AUDIT_SCOPED' if not errors else 'FAIL','errors':errors,'raw_sha256':hashlib.sha256(raw_bytes).hexdigest(),'admission_count':len(downs),'release_count':len(ups),'joined_pair_count':len(audited),'release_operation_order_matches':actual_codes==receipt_codes,'mutation_case_count':len(independent_mutations),'mutations_independently_reproduced':independent_mutations==result.get('mutation_cases'),'keymap_queries_between_ups':sum(row.get('op')=='query_keymap' for row in segment),'independent_effect_rows_present':'independent_task_effects' in raw,'overall_claim':'identity/timestamp join only; independent task-effect linkage remains HOLD'}
(PKG/'AUDIT.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
print(json.dumps(report,sort_keys=True))
raise SystemExit(bool(errors))
