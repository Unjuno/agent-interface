"""Reconcile preflight, lifecycle timers, model attempts, fixture and releases."""
from pathlib import Path
from zipfile import ZipFile
import hashlib,json
from jsonschema import Draft202012Validator
here=Path(__file__).resolve().parent
with ZipFile(here/'public.zip') as z:
 def raw(n):return z.read(n)
 def j(n):return json.loads(raw(n).decode('utf-8-sig'))
 manifest=j('frozen-manifest.json');assert all(hashlib.sha256(raw(n)).hexdigest()==h for n,h in manifest.items())
 src=j('source-hashes.json');hs=j('host-source-hashes.json');verification=j('source-verification.json');assert len(src)==verification['source_files_checked']==2029 and len(hs)==verification['host_source_files_checked']==2033 and verification['pre_and_post_mismatches']==0
 assert verification['source_manifest_sha256']==hashlib.sha256(raw('source-hashes.json')).hexdigest() and verification['host_source_manifest_sha256']==hashlib.sha256(raw('host-source-hashes.json')).hexdigest()
 for n in ('plain_form_points_schema_v1.json','compiled_form_grounding_schema_v1.json'):assert hashlib.sha256(raw('schemas/'+n)).hexdigest()==hs['host-source/research/live_control/'+n]
 cleanup=j('cleanup-check.json');assert cleanup['list_exit']==0 and not cleanup['present'] and len(cleanup['tested_names'])==3
 reports=[];all_ids=set();last_end=None;tasks_by_arm={}
 for allocation,arm,count in [('as01','ephemeral',6),('as02','persistent',2),('as03','plain',6)]:
  c=j(f'{allocation}/conditions.json');l=j(f'{allocation}/launcher-result.json');events=l['events'];assert c['arm']==l['arm']==arm and c['allocation']==l['allocation']==allocation and hashlib.sha256(raw('frozen-manifest.json')).hexdigest()==c['input_manifest_sha256']
  keys=['start_ns','host_started_ns','preflight_ready_ns','schema_checked_ns','container_invoked_ns','container_exited_ns','host_exited_ns'];assert all(type(events[k]) is int for k in keys) and all(events[a]<events[b] for a,b in zip(keys,keys[1:]))
  assert last_end is None or last_end<events['start_ns'];last_end=events['host_exited_ns'];assert l['status']=='completed' and l['lifecycle_ns']==events['host_exited_ns']-events['start_ns'] and l['host_exit']==l['container_exit']==0
  pre=j(f'{allocation}/preflight-summary.json');flag=j(f'{allocation}/preflight.json');check=j(f'{allocation}/schema-audit.json');assert len(pre)==1 and pre[0]['arm']==arm and pre[0]['attempted'] and pre[0]['completed'] and pre[0]['usage'] is not None and flag['accepted'] and check['arm']==arm and check['valid'] and not check['errors']
  schema='plain_form_points_schema_v1.json' if arm=='plain' else 'compiled_form_grounding_schema_v1.json';assert not list(Draft202012Validator(j('schemas/'+schema)).iter_errors(pre[0]['answer']))
  assert pre[0]['call_id'] not in all_ids;all_ids.add(pre[0]['call_id']);host=j(f'{allocation}/host-summary.json');assert host['error'] is None and host['calls']==count and len(host['records'])==count
  all_usage=[pre[0]['usage']];call_ids=set();threads=set()
  for i,record in enumerate(host['records'],1):
   ident=f'{i:03d}';req=j(f'{allocation}/exchange/{ident}.request.json');resp=j(f'{allocation}/exchange/{ident}.response.json');call=j(f'{allocation}/call-{ident}/result.json');digest=hashlib.sha256(raw(f'{allocation}/exchange/{ident}.png')).hexdigest()
   assert req['id']==resp['id']==record['id']==ident and req['arm']==arm and req['image_sha256']==resp['image_sha256']==record['image_sha256']==digest and record==resp and resp['ok'] and resp['attempted']
   assert call['call_id']==resp['call_id'] and call['usage']==resp['usage'] and call['grounding']==resp['grounding'] and call['turn_status']=='completed' and call['requested_model']=='gpt-6.1-sol' and call['requested_effort']=='low'
   assert resp['call_id'] not in all_ids and resp['call_id'] not in call_ids;call_ids.add(resp['call_id']);all_ids.add(resp['call_id']);threads.add(call['thread_id']);all_usage.append(resp['usage'])
  assert len(threads)==1 and all(0<=u['cached_input_tokens']<=u['input_tokens'] and u['output_tokens']>=0 for u in all_usage)
  r=j(f'{allocation}/out/result.json');rows=r['arms'][arm];oracle=r['independent'][arm];details=j(f'{allocation}/out/arms/{arm}/task-details.json');history=[json.loads(x) for x in raw(f'{allocation}/out/arms/{arm}/runtime/submission-history.jsonl').splitlines() if x.strip()]
  assert r['passed'] and r['calls']==count and len(rows)==len(details)==len(history)==6 and oracle['success'] and oracle['record_count']==6 and not oracle['duplicates'] and not oracle['missing'] and not oracle['unexpected']
  taskids=set();ledger_ids=set()
  for row,detail in zip(rows,details):
   tid=row['task_id'];matches=[h for h in history if h['task_id']==tid];assert tid not in taskids and len(matches)==1 and matches[0]['exact'] and detail['submission_records']==matches and detail['trace']==row;taskids.add(tid)
   assert row['typed_outcome']=='completed' and row['exact_submission'] and row['submission_count']==1 and row['releases_verified']
   for x in row['model_calls']:assert x['call_id'] in call_ids and x['call_id'] not in ledger_ids;ledger_ids.add(x['call_id'])
  assert ledger_ids==call_ids and taskids=={f'task-{i}' for i in range(1,7)};tasks_by_arm[arm]=[(x['task_id'],x['layout']) for x in rows]
  if arm=='persistent':assert [x['route'] for x in rows]==['cold','reuse','reuse','repair','reuse','reuse'] and rows[3]['repair']['old_reference_status']=='missing' and rows[3]['repair']['old_reference_pointer_admissions']==0
  records=[json.loads(x) for x in raw(f'{allocation}/out/arms/{arm}/runtime/events.jsonl').splitlines() if x.strip()];terminals=[x for x in records if x.get('event')=='terminal'];assert terminals and all(x['release']['verified'] is True and x['release']['keys_down']==[] and x['release']['buttons_down']==[] for x in terminals)
  reports.append({'arm':arm,'allocation':allocation,'lifecycle_seconds':l['lifecycle_ns']/1e9,'preflight_to_ready_seconds':(events['preflight_ready_ns']-events['start_ns'])/1e9,'container_phase_seconds':(events['container_exited_ns']-events['container_invoked_ns'])/1e9,'task_seconds_sum':sum(x['elapsed_ns'] for x in rows)/1e9,'task_calls':count,'preflight_calls':1,'input_tokens':sum(u['input_tokens'] for u in all_usage),'cached_input_tokens_subset':sum(u['cached_input_tokens'] for u in all_usage),'output_tokens':sum(u['output_tokens'] for u in all_usage),'exact_tasks':len(taskids),'verified_terminals':len(terminals)})
 assert tasks_by_arm['plain']==tasks_by_arm['persistent']==tasks_by_arm['ephemeral']
 print(json.dumps({'status':'audited','runs':reports},indent=2))
