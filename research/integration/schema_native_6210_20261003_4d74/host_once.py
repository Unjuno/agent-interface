import hashlib,json,os,pathlib,subprocess,sys,time,traceback
R=pathlib.Path(__file__).resolve().parent;P=json.loads((R/'PLAN.json').read_text());W=r'C:\Program Files\WSL\wslc.exe';CLI=r'C:\Users\junny\AppData\Local\OpenAI\Codex\bin\8aaf1547b825b104\codex.exe';PY=sys.executable
def save(p,v):p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n',encoding='utf-8')
def wait_path(p,client,end):
 while not p.exists():
  if client.poll() is not None:raise RuntimeError('container exited before '+p.name)
  if time.monotonic()>end:raise RuntimeError('deadline '+p.name)
  time.sleep(.1)
 return json.loads(p.read_text())
indices=[-1] if sys.argv[1]=='diagnostic' else list(range(8));summary=[]
for index in indices:
 O=R/'runs'/('diagnostic03' if index<0 else 'row'+str(index+1).zfill(2));O.mkdir(parents=True,exist_ok=False);(O/'workspace').mkdir();name='schema6210-4d74-'+O.name
 args=[W,'run','--name',name,'--pull','never','--network','none','--cpus','1','--memory','512m','--user','65534:65534','--tmpfs','/tmp:rw,size=64m,mode=1777','--env','PYTHONDONTWRITEBYTECODE=1','--env','PYTHONPATH=/src/sources','--volume',str(R)+':/src:ro','--volume',str(O)+':/out','--workdir','/src',P['image'],'timeout','--signal=TERM','--kill-after=3s','180s','python3','-B','producer.py',str(index)]
 logs=[(O/'host.stdout.txt').open('wb'),(O/'host.stderr.txt').open('wb')];start=time.time_ns();client=subprocess.Popen(args,stdout=logs[0],stderr=logs[1]);record=dict(index=index,argv=args,host_pid=client.pid,started_wall_ns=start,model_invocations=0,errors=[])
 try:
  if index>=0:
   req=wait_path(O/'model.request.json',client,time.monotonic()+30);record['image_sha256']=json.loads((O/'initial.json').read_text())['artifact']['sha256'];record['model_invocations']=1
   env=dict(os.environ,CODEX_EXE=CLI,HOST_MODEL_BROKER_TIMEOUT_S='90');cmd=[PY,'-B',str(R/'sources/runtime/host_model_ipc_broker_v1.py'),'--ipc',str(O),'--repo',str(R),'--once'];record['broker_command']=cmd
   bm=subprocess.run(cmd,env=env,capture_output=True,timeout=100);(O/'broker.stdout.txt').write_bytes(bm.stdout);(O/'broker.stderr.txt').write_bytes(bm.stderr);record['broker_exit']=bm.returncode
   if bm.returncode:raise RuntimeError('broker first outcome nonzero')
   events=[json.loads(line) for line in (O/'model.response.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()];save(O/'events-parsed.json',events)
   if len([e for e in events if e.get('type')=='thread.started'])!=1 or len([e for e in events if e.get('type')=='turn.completed'])!=1:raise RuntimeError('thread/turn accounting gate')
   completed=[e['item'] for e in events if e.get('type')=='item.completed'];messages=[e for e in completed if e.get('type')=='agent_message'];other=[e for e in completed if e.get('type') not in ('agent_message','reasoning')]
   if len(messages)!=1 or other:raise RuntimeError('additional message/tool item gate')
   proposal=json.loads(messages[0]['text']);save(O/'proposal.json',proposal);record['usage']=[e['usage'] for e in events if e.get('type')=='turn.completed'][0]
  record['container_exit']=client.wait(timeout=20)
  if record['container_exit']:raise RuntimeError('container first outcome nonzero')
  if index<0:
   raw=json.loads((O/'raw.json').read_text());assert raw['effect']['history'][0]['label']=='GREEN' and len(raw['effect']['history'])==1 and raw['cleanup_release']['verified']
 except Exception:
  record['errors'].append(traceback.format_exc());stop=subprocess.run([W,'stop',name],capture_output=True,timeout=15);(O/'stop.stdout.txt').write_bytes(stop.stdout);(O/'stop.stderr.txt').write_bytes(stop.stderr)
  try:record['container_exit']=client.wait(timeout=10)
  except subprocess.TimeoutExpired:record['client_terminal_unknown']=True
 finally:
  for f in logs:f.close()
  record['ended_wall_ns']=time.time_ns();inspect=subprocess.run([W,'inspect',name],capture_output=True,timeout=15);(O/'container-terminal.json').write_bytes(inspect.stdout);(O/'inspect.stderr.txt').write_bytes(inspect.stderr);save(O/'HOST_RECEIPT.json',record);summary.append(record);print(json.dumps(dict(index=index,errors=record['errors'],usage=record.get('usage'))),flush=True)
 if record['errors']:break
save(R/('DIAGNOSTIC.json' if indices==[-1] else 'MODEL_EXECUTION.json'),dict(rows=summary,retries=0,status='STOP_FIRST_OUTCOME' if summary[-1]['errors'] else 'RETURNED',planned_rows=len(indices)));sys.exit(2 if summary[-1]['errors'] else 0)
