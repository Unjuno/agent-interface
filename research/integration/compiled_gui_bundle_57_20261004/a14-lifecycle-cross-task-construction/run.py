import hashlib,json,pathlib,subprocess,time,datetime,struct
HERE=pathlib.Path(__file__).resolve().parent; ROOT=HERE.parents[3]
MAN=json.loads((HERE/'manifest.json').read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def require(x,m):
 if not x: raise SystemExit(m)
require(sha(HERE/'PLAN.md')==MAN['pins']['plan_sha256'],'plan pin mismatch')
require(sha(ROOT/'research/integration/compiled_gui_bundle_57_20261004/a13-predicate-lifecycle-prompt-check/PROMPT.txt')==MAN['pins']['template_prompt_sha256'],'prompt template pin mismatch')
require(sha(ROOT/'research/integration/compiled_gui_bundle_57_20261004/a13-predicate-lifecycle-prompt-check/schema.json')==MAN['pins']['schema_sha256'],'schema pin mismatch')
require(sha(ROOT/'research/integration/compiled_gui_bundle_57_20261004/a12-predicate-lifecycle-guard/candidate.py')==MAN['pins']['candidate_sha256'],'candidate pin mismatch')
for t in MAN['tasks']:
 row=ROOT/t['row_path']; img=ROOT/t['image_path']; dest=HERE/f"task-{t['task_index']}"
 require(sha(row)==t['row_sha256'] and sha(img)==t['image_sha256'],'row/image pin mismatch')
 rd=json.loads(row.read_text()); st=rd['caller']['selected_target']
 require(rd['task']['task_id']==f"task-{t['task_index']}" and rd['task']['token']==t['token'],'manifest task identity mismatch')
 require(st['aliases']==t['aliases'] and st['model_call_id']==t['call_id'],'manifest alias/call identity mismatch')
 require(pathlib.Path(rd['source']['image']).name==img.name,'manifest source-image mapping mismatch')
 require(sha(dest/'PROMPT.txt')==t['prompt_sha256'] and sha(dest/'schema.json')==t['schema_sha256'],'task prompt/schema pin mismatch')
 require(struct.unpack('>II',(img.read_bytes())[16:24])==(1280,800),'unexpected image dimensions')
# No task may receive a second attempt. A started-without-RAW attempt is unresolved and is deliberately not retried.
for t in MAN['tasks']:
 idx=t['task_index']; dest=HERE/f'task-{idx}'; rawp=dest/'RAW.json'; started=dest/'CALL_STARTED.json'
 if rawp.exists(): continue
 if started.exists():
  (dest/'RAW.json').write_text(json.dumps({'status':'INTERRUPTED_UNKNOWN_NO_RETRY','provider_attempts':1,'start_record':json.loads(started.read_text())},indent=2,sort_keys=True)+'\n'); continue
 row=ROOT/t['row_path']; img=ROOT/t['image_path']
 cmd=['codex','exec','--ephemeral','--ignore-user-config','--ignore-rules','--disable','plugins','--disable','remote_plugin','--disable','shell_snapshot','--disable','shell_tool','--skip-git-repo-check','--sandbox','read-only','--json','--color','never','--model',MAN['model'],'-c',f'model_reasoning_effort="{MAN["effort"]}"','-c','project_doc_max_bytes=0','-c','approval_policy="never"','--cd',str(ROOT),'--output-schema',str(dest/'schema.json'),'--output-last-message',str(dest/'answer.json'),'--image',str(img),'-']
 argv=dest/'argv.json'; argv.write_text(json.dumps(cmd,indent=2)+'\n')
 started_data={'task_index':idx,'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'attempt':1,'argv_sha256':sha(argv),'prompt_sha256':sha(dest/'PROMPT.txt'),'image_sha256':sha(img)}
 started.write_text(json.dumps(started_data,indent=2,sort_keys=True)+'\n')
 tic=time.monotonic_ns()
 try:
  p=subprocess.run(cmd,input=(dest/'PROMPT.txt').read_bytes(),capture_output=True,timeout=MAN['timeout_seconds_per_task'])
  outcome={'exit_code':p.returncode,'timed_out':False,'elapsed_ns':time.monotonic_ns()-tic}; (dest/'stdout.jsonl').write_bytes(p.stdout); (dest/'stderr.txt').write_bytes(p.stderr)
 except subprocess.TimeoutExpired as e:
  outcome={'exit_code':None,'timed_out':True,'elapsed_ns':time.monotonic_ns()-tic}; (dest/'stdout.jsonl').write_bytes(e.stdout or b''); (dest/'stderr.txt').write_bytes(e.stderr or b'')
 ans=(dest/'answer.json').read_bytes() if (dest/'answer.json').exists() else b''
 events=[]; usage=[]; thread_ids=[]
 for line in (dest/'stdout.jsonl').read_text(errors='replace').splitlines():
  try: e=json.loads(line)
  except json.JSONDecodeError: continue
  events.append(e.get('type')); usage.extend([e for e in [e] if 'usage' in e]);
  if e.get('type')=='thread.started': thread_ids.append(e.get('thread_id'))
 raw={'status':'captured','provider_attempts':1,'requested_model':MAN['model'],'requested_effort':MAN['effort'],'cli_version':MAN['cli_version'],'thread_ids':thread_ids,'event_types':events,'usage_events':usage,'task_index':idx,'task_row_sha256':sha(row),'image_sha256':sha(img),'prompt_sha256':sha(dest/'PROMPT.txt'),'schema_sha256':sha(dest/'schema.json'),'candidate_sha256':MAN['pins']['candidate_sha256'],'argv_sha256':sha(argv),'stdout_sha256':sha(dest/'stdout.jsonl'),'stderr_sha256':sha(dest/'stderr.txt'),'answer_sha256':hashlib.sha256(ans).hexdigest() if ans else None,'answer':json.loads(ans) if ans else None,**outcome}
 (dest/'RAW.json').write_text(json.dumps(raw,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'task':idx,'exit_code':raw['exit_code'],'timed_out':raw['timed_out'],'answer_sha256':raw['answer_sha256']}),flush=True)
