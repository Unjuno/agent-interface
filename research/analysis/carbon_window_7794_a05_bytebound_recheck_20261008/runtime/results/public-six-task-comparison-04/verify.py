"""Read-only audit: does not extract, launch a GUI, submit input or rewrite raw records."""
import pathlib,json,hashlib,tarfile,io,base64
root=pathlib.Path(__file__).resolve().parent
def check(ok,why):
 if not ok:raise ValueError(why)
def sha(b):return hashlib.sha256(b).hexdigest()
a=(root/'raw.tar.gz').read_bytes();manifest=json.loads((root/'manifest.json').read_text());check(sha(a)==manifest['archive_sha256'],'archive hash')
with tarfile.open(fileobj=io.BytesIO(a),mode='r:gz') as t:
 members=t.getmembers();check(all(x.isfile() and not x.name.startswith('/') and '..' not in pathlib.Path(x.name).parts for x in members),'unsafe member');check(len({x.name for x in members})==len(members),'duplicates');raw={x.name:t.extractfile(x).read() for x in members}
check(set(raw)=={x['path'] for x in manifest['files']},'manifest coverage')
for x in manifest['files']:check(len(raw[x['path']])==x['bytes'] and sha(raw[x['path']])==x['sha256'],'member '+x['path'])
def j(n):return json.loads(raw[n])
check(j('current/PLAN.json')['source_revision']=='7477466a9c11442a7af307fc5bc20e1ee5dd9863' and j('current/PLAN.json')['seed']==992004,'freeze')
check(sha(raw['current/runtime.pyz'])==j('current/MANIFEST.json')['sha256'],'package')
for i in range(3):check(j(f'current/preflight-{i}-result.json')['static_valid'] is True,'static caller pattern')
metrics=j('current/metrics.json');check(len(metrics['tasks'])==12 and metrics['integration_acceptance']=='HOLD_INTEGRATION_INCOMPLETE','scope/accounting')
report={}
for route,total in [('direct',21),('guarded',25)]:
 prefix=f'current/{route}/';reps={i:j(prefix+f'host/reply-{i}.json') for i in range(1,total+1)};reqs={i:j(prefix+f'host/request-{i}.json') for i in range(1,total+1)};payload={i:json.loads(r['result']['content'][0]['text']) for i,r in reps.items()}
 for i,r in reps.items():check(r['status']=='returned' and r['id']==i and r['sdk_entry_ns']<=r['sdk_return_ns'] and reqs[i]['tool']==r['tool'],'SDK identities')
 history=[json.loads(l) for l in raw[prefix+'submission-history.jsonl'].splitlines()];check(len(history)==6,'history rows')
 ev=j(prefix+'evaluation-at-close.json');check(ev['success'] and ev['record_count']==6 and not ev['unexpected'] and not ev['duplicates'] and not ev['missing'],'independent score')
 for i,rec in enumerate(history,1):check(rec['task_id']==f'task-{i}' and rec['submitted_values']==[f't992004-{i}'] and rec['exact'] is True and rec['layout']==('A' if i<=3 else 'B'),'exact token/layout')
 releases=[]
 for i,r in reps.items():
  if r['tool'] not in ['interface_dispatch','interface_guarded_input']:continue
  m=payload[i];body=m['receipt']['source']['raw_report']['result'] if route=='direct' else m['result']
  if body['status']=='completed':releases+=body['execution']['releases']
 check(len(releases)==18 and all(x['verified'] and not x['keys_down'] and not x['buttons_down'] for x in releases),'input releases')
 check(payload[total]['status']=='closed' and payload[total]['release']['verified'],'close release')
 check(payload[total-1]['operation_invoked'] is False and payload[total-1]['call_id']==payload[total-2]['call_id'],'read-only continuation')
 check(j(prefix+'host/exit.json')['code']==0 and j('current/terminal.json')[route]['exit_code']==0,'terminal')
 check([x['returncode'] for x in j(prefix+'cleanup.json')]==[0,1,0],'cleanup accounting')
 events=[json.loads(l) for l in raw[prefix+'host/host-events.jsonl'].splitlines()];presented={x['attempt'] for x in events if x['kind']=='presentation_callbacks_completed'}
 png_hashes={sha(v) for n,v in raw.items() if n.startswith(prefix+'server/') and n.endswith('.png')}
 for i in presented:
  for c in reps[i]['result']['content']:
   if c['type']=='image':
    b=base64.b64decode(c['data'],validate=True);check(c['mimeType']=='image/png' and b.startswith(b'\x89PNG\r\n\x1a\n') and sha(b) in png_hashes,'delivered PNG matches retained native artifact')
 images=sum(sum(c['type']=='image' for c in reps[i]['result']['content']) for i in presented);check(images==({'direct':19,'guarded':20}[route]),'delivered images')
 check(sum(c['type']=='image' for c in reps[total-1]['result']['content'])==({'direct':1,'guarded':0}[route]),'lookup image deviation')
 for task in range(1,7):
  row=next(x for x in metrics['tasks'] if x['route']==route and x['task']==task);first=row['entry_attempt'];end=row['save_attempt']
  sdk=sum((reps[i]['sdk_return_ns']-reps[i]['sdk_entry_ns'])/1e6 for i in range(first,end+1));check(abs(sdk-row['sdk_selected_calls_ms'])<1e-6,'SDK sum')
  effect=(history[task-1]['received_ns']-reps[first]['sdk_entry_ns'])/1e6;check(abs(effect-row['sdk_input_to_independent_submission_ms'])<1e-6,'effect time')
  start=next(x for x in events if x['kind']=='send_requested' and x['attempt']==first);feedback=next(x for x in events if x['kind']=='presentation_callbacks_completed' and x['attempt']==first)
  check(abs(feedback['host_monotonic_ms']-start['host_monotonic_ms']-row['first_reply_presentation_ms'])<1e-6,'presentation time')
  for phase,column in [('pre-save','input_to_presave_annotation_ms'),('result','input_to_result_annotation_ms')]:
   e=next(x for x in events if x['kind']=='review_recorded' and x.get('task')==f'task-{task}' and x.get('phase')==phase);check(abs(e['host_monotonic_ms']-start['host_monotonic_ms']-row[column])<1e-6,'annotation time')
  check(row['visual_completion_cue_in_save_image']==(not(route=='direct' and task==6)),'visual cue scope')
 report[route]={'exact_tasks':6,'public_calls':total,'delivered_images':images,'input_releases':len(releases)}
 if route=='guarded':
  check(payload[14]['status']=='refused' and payload[14]['result']['input_dispatched'] is False and payload[14]['result']['guard_checks'][0]['status']=='MISSING','changed region refusal')
  check(reqs[15]['arguments']['source_sequence']==45 and reqs[16]['arguments']['alias']=='field_b','explicit reground')
  seq=[]
  for n in raw:
   if n.startswith(prefix+'server/guarded-session-') and pathlib.Path(n).name.startswith('observation-'):
    o=j(n);artifact=o['native']['artifact'];base='/var/tmp/agent-interface-integrated-main/results-local/public-six-task-comparison-04/';check(artifact['path'].startswith(base),'artifact scope');check(sha(raw['current/'+artifact['path'][len(base):]])==artifact['sha256'],'PNG digest');check(o['image_source']=='exact_capture_rgb_handoff' and artifact['source_raw_sha256']==o['native']['sha256'],'RGB/raw link');seq.append(o['sequence'])
  check(sorted(seq)==list(range(1,82)),'guard81 native captures')
 else:
  check(len([n for n in raw if n.startswith(prefix+'server/') and n.endswith('.png')])==19,'direct19 native captures')
check(j('interrupted02/interruption-after-wsl-restart.json')['status']=='STOP_USER_AUTHORIZED_WSL_RESTART','retained restart')
check(len(j('interrupted02/interruption-after-wsl-restart.json')['rows'])==12 and j('interrupted02/guarded/evaluation-current.json')['record_count']==3,'interrupted accounting')
check(j('interrupted02/transport-terminal-after-restart.json')['guarded_relay_exit']['code']==1,'interrupted terminal')
check(j('caller-stop03/STOP.json')['status']=='STOP_CALLER_PROGRAM_CONSTRUCTION' and len(j('caller-stop03/STOP.json')['rows'])==6,'caller stop rows')
check(j('caller-stop03/direct/evaluation-at-close.json')['record_count']==0,'caller no saved tasks')
usage=j('current/model-usage-projection.json')['calls'];check(len(usage)==44 and all(len(x['usage_records_before_output'])==1 and x['local_context']['model']=='gpt-6.1-sol' for x in usage),'whole-context usage projection')
check(len({x['usage_records_before_output'][0]['ordinal'] for x in usage})==44,'unique usage records')
print(json.dumps({'status':'PASS_PUBLIC_SIX_TASK_CORRECTNESS_SCOPED','acceptance':'HOLD_INTEGRATION_INCOMPLETE','raw_files':len(raw),'routes':report,'limits':'One serial cooperative pair; direct last visual cue incomplete; exact perception, provider cost and human comparison unmeasured.'},indent=2))
