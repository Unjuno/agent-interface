import copy, hashlib, json, subprocess, sys, unittest
from pathlib import Path
from join import join
P=Path(__file__).resolve().parent
raw=json.loads((P/'RAW.json').read_text())
source_lock=json.loads((P/'SOURCE_LOCK.json').read_text())
loader=unittest.defaultTestLoader
suite=loader.discover(str(P),pattern='test_join.py')
res=unittest.TextTestRunner(verbosity=2).run(suite)
if not res.wasSuccessful(): raise SystemExit(1)
base=join(raw)
# Bounded fail-closed fault table, always generated from the exact retained input.
cases={}
r=copy.deepcopy(raw); r['events']=[e for e in r['events'] if e['event']!='input_release_transition']; cases['missing_release']=join(r)['status']
r=copy.deepcopy(raw); u=next(e for e in r['events'] if e['event']=='input_release_transition'); r['events'].append(copy.deepcopy(u)); cases['duplicate_release']=join(r)['status']
r=copy.deepcopy(raw); d=next(e for e in r['events'] if e['event']=='input_admission'); r['events'].append(copy.deepcopy(d)); cases['duplicate_admission']=join(r)['status']
for field,val in [('key','F9'),('owner_id','wrong-owner'),('intent_token','wrong-token'),('step',99)]:
 r=copy.deepcopy(raw); u=next(e for e in r['events'] if e['event']=='input_release_transition'); u[field]=val; cases['release_'+field]=join(r)['status']
r=copy.deepcopy(raw); u=next(e for e in r['events'] if e['event']=='input_release_transition'); u['owner_thread_keyup_receipt']['key']='F9'; cases['receipt_key_mismatch']=join(r)['status']
r=copy.deepcopy(raw); u=next(e for e in r['events'] if e['event']=='input_release_transition'); u['physical_verification_authoritative']=True; cases['authority_overclaim']=join(r)['status']
r=copy.deepcopy(raw); u=next(e for e in r['events'] if e['event']=='input_release_transition'); u['owner_thread_keyup_receipt']['owner_keyrelease_started_ns']=u['release_call_returned_ns']+1; cases['reversed_time']=join(r)['status']
r=copy.deepcopy(raw); ups=[i for i,op in enumerate(r['operations']) if op.get('op')=='key-up']; r['operations'][ups[0]],r['operations'][ups[1]]=r['operations'][ups[1]],r['operations'][ups[0]]; cases['reordered_keyup_operation']=join(r)['status']
r=copy.deepcopy(raw); ups=[i for i,op in enumerate(r['operations']) if op.get('op')=='key-up']; q={'op':'query_keymap','at_ns':r['operations'][ups[0]]['at_ns']+1}; r['operations'].insert(ups[0]+1,q); ups=[i for i,op in enumerate(r['operations']) if op.get('op')=='key-up']; r['between_up_operations']=r['operations'][ups[0]+1:ups[1]]; cases['inter_up_keymap_query']=join(r)['status']
raw_sha=hashlib.sha256((P/'RAW.json').read_bytes()).hexdigest()
source_hashes={p:sha for p,entry in source_lock['sources'].items() for sha in [entry['sha256_lf_normalized']]}
ops=raw['operations']; up_indices=[i for i,op in enumerate(ops) if op.get('op')=='key-up']; up_rows=sorted([e for e in raw['events'] if e.get('event')=='input_release_transition'],key=lambda row:row['release_call_started_ns']); between=ops[up_indices[0]+1:up_indices[1]]
release_order_checks={'key_up_count':len(up_indices),'event_keycodes':[e['owner_thread_keyup_receipt']['keycode'] for e in up_rows],'operation_keycodes':[ops[i].get('keycode') for i in up_indices],'order_matches':len(up_indices)==len(up_rows) and [ops[i].get('keycode') for i in up_indices]==[e['owner_thread_keyup_receipt']['keycode'] for e in up_rows],'between_up_operations_matches_copy':between==raw.get('between_up_operations'),'keymap_queries_between_ups':sum(op.get('op')=='query_keymap' for op in between),'declared_keymap_queries_between_ups':raw.get('keymap_queries_between_ups')}
result={'schema':'v39-effect-identity-join-result-v1','current_main_commit':source_lock['current_main_commit'],'raw_origin_commit':source_lock['v39_release_order_run_source_commit'],'raw_sha256':raw_sha,'source_hashes':source_hashes,'unit_tests':{'run':res.testsRun,'failures':len(res.failures),'errors':len(res.errors)},'mutation_cases':cases,'release_order_checks':release_order_checks,'independent_audit':{'pairs':base['pairs'],'overall_status':base['status']},'conclusion':'PASS_IDENTITY_JOIN_SCOPED; HOLD_MISSING_TASK_EFFECT','scope':'CPU-only replay of retained synthetic fake-X JSON rows; no game, model, live X11, OS input, allocation, or runtime replay'}
(P/'RESULT.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps({'unit_tests':result['unit_tests'],'mutation_cases':cases,'conclusion':result['conclusion']},sort_keys=True))
