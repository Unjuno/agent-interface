import pathlib,json,subprocess,time,hashlib,datetime
R=pathlib.Path(__file__).resolve().parent;O=R/'output';P=json.loads((R/'PLAN.json').read_text());F=json.loads((R/'FREEZE.json').read_text());calls=[];stopped=None
for n,d in F['files'].items():
 if hashlib.sha256((R/n).read_bytes()).hexdigest()!=d:raise RuntimeError('freeze:'+n)
if hashlib.sha256(pathlib.Path(P['CLI']).read_bytes()).hexdigest()!=F['cli_sha256']:raise RuntimeError('CLI_identity')
args=[r'C:\Program Files\WSL\wslc.exe','run','--rm','--network','none','--cpus','1','--memory','512M','--user','65534:65534','--volume',str(R)+':/study:ro','--volume',str(O)+':/out','--env','PYTHONDONTWRITEBYTECODE=1',P['image'],'/usr/bin/python3','/study/app.py']
(O/'container.argv.json').write_text(json.dumps(args,indent=2));stdout=(O/'container.stdout.log').open('wb');stderr=(O/'container.stderr.log').open('wb');proc=subprocess.Popen(args,stdout=stdout,stderr=stderr);deadline=time.monotonic()+300;processed=set()
while proc.poll() is None:
 for request in sorted(O.glob('*.request.json')):
  if request.name in processed:continue
  processed.add(request.name);name=request.name.removesuffix('.request.json');answer=O/(name+'.answer.json')
  cmd=[P['CLI'],'exec','--ephemeral','--ignore-user-config','--skip-git-repo-check','--sandbox','read-only','--json','--color','never','--model',P['model'],'-c','model_reasoning_effort="low"','-c','project_doc_max_bytes=0','-c','approval_policy="never"','--cd',str(R/'empty-workspace'),'--output-schema',str(R/'SCHEMA.json'),'--output-last-message',str(answer),'-']
  (O/(name+'.model.argv.json')).write_text(json.dumps(cmd,indent=2));start=time.monotonic_ns();timed=False;started=datetime.datetime.now(datetime.timezone.utc).isoformat()
  try:result=subprocess.run(cmd,input=request.read_bytes(),capture_output=True,timeout=P['seconds_per_call']);out=result.stdout;err=result.stderr;code=result.returncode
  except subprocess.TimeoutExpired as e:out=e.stdout or b'';err=e.stderr or b'';code=None;timed=True
  (O/(name+'.model.stdout.jsonl')).write_bytes(out);(O/(name+'.model.stderr.log')).write_bytes(err);events=[];parse_errors=[]
  for line in out.splitlines():
   try:events.append(json.loads(line))
   except Exception:parse_errors.append(line.decode(errors='replace'))
  tools=[e for e in events if e.get('item',{}).get('type') not in (None,'reasoning','agent_message')];completed=[e for e in events if e.get('type')=='turn.completed'];value=None
  try:value=json.loads(answer.read_text())
  except Exception:pass
  ok=code==0 and not timed and not parse_errors and not tools and len(completed)==1 and isinstance(value,dict) and set(value)=={'action','reason'} and value['action'] in ['COMMIT','RECHECK','ABORT','SAVE_AS_NEW']
  row={'id':name,'started_utc':started,'elapsed_ns':time.monotonic_ns()-start,'exit':code,'timeout':timed,'completed':completed,'events':events,'parse_errors':parse_errors,'tool_items':tools,'answer':value,'transport_ok':ok};calls.append(row)
  (O/'MODEL.json').write_text(json.dumps({'calls':calls,'attempted':len(calls)},indent=2));temp=O/(name+'.response.tmp');temp.write_text(json.dumps({'transport_ok':ok,'answer':value}));temp.rename(O/(name+'.response.json'));print(json.dumps({'id':name,'transport_ok':ok,'answer':value,'usage':[e.get('usage') for e in completed]}),flush=True)
 if time.monotonic()>deadline:proc.terminate();stopped='host_deadline';break
 time.sleep(.1)
code=proc.wait(timeout=10);stdout.close();stderr.close();(O/'HOST.json').write_text(json.dumps({'container_exit':code,'stop':stopped,'attempted_model_calls':len(calls)},indent=2));print(json.dumps({'container_exit':code,'calls':len(calls),'stop':stopped}));raise SystemExit(bool(code or stopped))
