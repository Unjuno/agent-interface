import pathlib,json,hashlib
from saved_oracle import score_done
R=pathlib.Path('/data');O=pathlib.Path('/out');P=json.loads((R/'PLAN.json').read_text());errors=[];rows=[]
for p,h in P['source_hashes'].items():
 if hashlib.sha256((R/p).read_bytes()).hexdigest()!=h:errors.append('source pin '+p)
main=(R/'caller_main.py').read_bytes();reference=(R/'caller_retention.py').read_bytes();old=b'delivery="confirmed")\n        return finish("TASK_SUCCEEDED"';new=b'delivery="confirmed", execution_progress=execution)\n        return finish("TASK_SUCCEEDED"'
if main.count(old)!=1 or main.replace(old,new)!=reference:errors.append('one-line source contrast')
for spec in P['rows']:
 D=R/'runs'/('row'+str(spec['index']+1));raw=json.loads((D/'raw.json').read_text());host=json.loads((D/'HOST_RECEIPT.json').read_text());bad=[]
 if raw['spec']!=spec or raw['source_hashes']!=P['source_hashes'] or raw['errors'] or host['errors'] or host['exit_code']!=0:bad.append('source/infrastructure')
 if len(raw['tasks'])!=1 or raw['adapter_calls']!=['execute','verify']:bad.append('exactly one native execute and verify')
 score=score_done(D,raw['tasks'][0]);bad.extend(score['errors']);receipt=raw['tasks'][0]['receipt'];projection=raw['execution_projection']
 if projection['native_receipt_sha256']!=hashlib.sha256(json.dumps(receipt,sort_keys=True).encode()).hexdigest() or projection['caller_decision']!={'status':'completed'}:bad.append('exact typed native projection')
 c=raw['caller_result'];want=None if spec['arm']=='main' else {'status':'completed'}
 if (c['outcome'],c['reason'],c['task_effect'],c['delivery'],c['execution_progress'])!=('TASK_NOT_VERIFIED','unavailable','unavailable','confirmed',want):bad.append('partial-effect result')
 if c['input_authority']!='consumed_by_recorded_execute_stage' or c['accounting']['attempted_calls']!=0 or host['model_calls']!=0 or c['attempt_ledger'] or c['model_call_ledger']:bad.append('authority/model ledger')
 if c['stages']['execute']['status']!='completed' or c['stages']['verify_effect']['status']!='completed':bad.append('stage completion')
 if sum(e['event']=='adaptive_route_finished' for e in raw['caller_events'])!=1:bad.append('one terminal event')
 ex=receipt['execution'];rels=ex.get('releases',[])
 if ex['completed_ops']!=list(range(len(raw['tasks'][0]['program']['ops']))) or not rels or not all(x.get('verified') is True and x.get('keys_down')==[] and x.get('buttons_down')==[] for x in rels):bad.append('native/release')
 if raw['cleanup_physical']['keys'] or raw['cleanup_physical']['buttons']:bad.append('cleanup input')
 rows.append(dict(arm=spec['arm'],saved_score=score,caller_outcome=c['outcome'],execution_progress=c['execution_progress'],input_authority=c['input_authority'],native_attempts=len(raw['tasks']),model_calls=c['accounting']['attempted_calls'],errors=bad));errors.extend(bad)
out=dict(allocation=P['allocation'],errors=errors,rows=rows,disposition='REPRODUCED_MAIN_PROGRESS_LOSS; SUPPORT_ONE_LINE_RETENTION_SCOPED' if not errors else 'HOLD_OR_FAIL',scope='Controlled unavailable verifier over actual native save. Exact pinned source, stable fixture no-authority surrogates, not full semantic/recovery/current-main/economic qualification; same-worker independent saved reader, not blinded non-author.')
with (O/'AUDIT.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(out));raise SystemExit(bool(errors))
