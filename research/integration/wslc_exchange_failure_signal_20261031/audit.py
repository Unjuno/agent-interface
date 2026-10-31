"""Audit early stop on a deliberately persistent host-side receipt-read failure."""
from pathlib import Path
from zipfile import ZipFile
import hashlib,json
from jsonschema import Draft202012Validator
here=Path(__file__).resolve().parent
with ZipFile(here/'public.zip') as z:
 def raw(n):return z.read(n)
 def j(n):return json.loads(raw(n).decode('utf-8-sig'))
 m=j('frozen-manifest.json');assert all(hashlib.sha256(raw(n)).hexdigest()==h for n,h in m.items());assert raw('exchange_wait.py').replace(b'\r\n',b'\n')==(here/'exchange_wait.py').read_bytes().replace(b'\r\n',b'\n')
 c=j('av01/conditions.json');assert c['seed']==991031 and hashlib.sha256(raw('frozen-manifest.json')).hexdigest()==c['input_manifest_sha256'];v=j('source-verification.json');assert v['source_files_checked']==2029 and v['host_source_files_checked']==2033 and v['pre_and_post_mismatches']==0
 hs=j('host-source-hashes.json');assert hashlib.sha256(raw('schemas/compiled_form_grounding_schema_v1.json')).hexdigest()==hs['host-source/research/live_control/compiled_form_grounding_schema_v1.json']
 cleanup=j('cleanup-check.json');assert cleanup['list_exit']==0 and cleanup['present']==[] and len(cleanup['tested_names'])==1
 l=j('av01/launcher-result.json');ev=l['events'];keys=['start_ns','host_started_ns','preflight_ready_ns','schema_checked_ns','container_invoked_ns','container_exited_ns','host_exited_ns'];assert all(ev[a]<ev[b] for a,b in zip(keys,keys[1:])) and l['status']=='error' and not l['container_running'] and not l['host_running']
 pre=j('av01/preflight-summary.json');assert len(pre)==1 and pre[0]['attempted'] and pre[0]['completed'] and pre[0]['usage'] is not None and j('av01/preflight.json')['accepted'];assert not list(Draft202012Validator(j('schemas/compiled_form_grounding_schema_v1.json')).iter_errors(pre[0]['answer']))
 host=j('av01/host-summary.json');assert host['calls']==len(host['records'])==5 and 'PermissionError' in host['error'];marker=j('av01/exchange/host-error.json');assert marker=={'kind':'host_failed','error_type':'PermissionError','completed_calls':5}
 retries=[json.loads(x) for x in raw('av01/exchange-io.jsonl').splitlines()];assert len(retries)>1 and all(x['stage']=='request_read' and x['id']=='006' and x['attempt']==i for i,x in enumerate(retries,1)) and all(x['status']=='retry' for x in retries[:-1]) and retries[-1]['status']=='deadline'
 ids=set();usage=[pre[0]['usage']]
 for i,record in enumerate(host['records'],1):
  ident=f'{i:03d}';req=j(f'av01/exchange/{ident}.request.json');resp=j(f'av01/exchange/{ident}.response.json');call=j(f'av01/call-{ident}/result.json');digest=hashlib.sha256(raw(f'av01/exchange/{ident}.png')).hexdigest();assert req['id']==resp['id']==ident and req['image_sha256']==resp['image_sha256']==digest and resp==record and resp['ok'] and resp['attempted'] and call['call_id']==resp['call_id'] and call['usage']==resp['usage'] and call['turn_status']=='completed' and call['requested_model']=='gpt-6.1-sol' and call['requested_effort']=='low'
  assert resp['call_id'] not in ids;ids.add(resp['call_id']);usage.append(resp['usage'])
 req=j('av01/exchange/006.request.json');assert req['image_sha256']==hashlib.sha256(raw('av01/exchange/006.png')).hexdigest() and 'av01/exchange/006.response.json' not in z.namelist() and 'av01/call-006/result.json' not in z.namelist()
 r=j('av01/out/result.json');oracle=r['independent']['ephemeral'];rows=r['arms']['ephemeral'];details=j('av01/out/arms/ephemeral/task-details.json');history=[json.loads(x) for x in raw('av01/out/arms/ephemeral/runtime/submission-history.jsonl').splitlines() if x.strip()];assert not r['passed'] and r['calls']==6 and len(rows)==len(details)==6 and len(history)==5 and not oracle['success'] and oracle['missing']==['task-6']
 for i in range(5):
  assert rows[i]['typed_outcome']=='completed' and rows[i]['exact_submission'] and rows[i]['releases_verified'] and details[i]['submission_records']==[history[i]] and history[i]['exact']
 last=rows[-1];attempts=details[-1]['adaptive']['attempt_ledger'];assert last['task_id']=='task-6' and last['typed_outcome']=='failed' and last['pointer_admissions']==0 and last['submission_count']==0 and len(attempts)==1 and attempts[0]['status']=='failed' and attempts[0]['usage'] is None and attempts[0]['call_id'] is None and 'HostFailure' in attempts[0]['error']
 wait=(attempts[0]['completed_ns']-attempts[0]['started_ns'])/1e9;assert 0<wait<10
 events=[json.loads(x) for x in raw('av01/out/arms/ephemeral/runtime/events.jsonl').splitlines()];terminals=[x for x in events if x.get('event')=='terminal'];assert len(terminals)==42 and all(x['release']['verified'] is True and x['release']['keys_down']==[] and x['release']['buttons_down']==[] for x in terminals)
 print(json.dumps({'status':'audited','intentional_outcome':'incomplete','exact_submissions':len(history),'completed_host_task_calls':len(ids),'last_request_usage':'unavailable','failed_attempt_seconds':wait,'permission_retries':len(retries),'verified_terminal_events':len(terminals),'known_input_tokens':sum(x['input_tokens'] for x in usage),'known_output_tokens':sum(x['output_tokens'] for x in usage),'host_and_container_returned':True},indent=2))
