import base64,hashlib,json,pathlib,queue,subprocess,sys,threading,time,traceback
from saved_oracle import score_done
R=pathlib.Path(__file__).resolve().parent;P=json.loads((R/'PLAN.json').read_text(encoding='utf-8'));W=r'C:\Program Files\WSL\wslc.exe';CLI=P['app_server_argv'][0];summaries=[]
def save(p,v):p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n',encoding='utf-8')
def wait_path(p,native,seconds=155):
 end=time.monotonic()+seconds
 while not p.exists():
  if native.poll() is not None:raise RuntimeError('native terminal before '+p.name)
  if time.monotonic()>end:raise RuntimeError('path deadline '+p.name)
  time.sleep(.02)
 return json.loads(p.read_text(encoding='utf-8'))
def wait_outcome(O,label,native):
 end=time.monotonic()+15
 while time.monotonic()<end:
  for suffix in ('DONE','REFUSED'):
   p=O/(label+'.'+suffix+'.json')
   if p.exists():return suffix,json.loads(p.read_text(encoding='utf-8'))
  if native.poll() is not None:raise RuntimeError('native terminal before outcome '+label)
  time.sleep(.02)
 raise RuntimeError('native outcome deadline')
def ground(O,label,ready,task,native):
 stage=O/('model-'+label);stage.mkdir(exist_ok=False);workspace=stage/'workspace';workspace.mkdir();q=queue.Queue();record=dict(label=label,started_wall_ns=time.time_ns(),errors=[],sent=[],received=[],dynamic_calls=0,turn_start_requests=0)
 err=(stage/'stderr.txt').open('wb');app=subprocess.Popen(P['app_server_argv'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=err);record['app_server_pid']=app.pid
 def reader():
  for line in app.stdout:
   try:q.put(json.loads(line))
   except Exception:q.put(dict(non_json_stdout=line.decode('utf8','replace')))
 threading.Thread(target=reader,daemon=True).start()
 def send(obj):record['sent'].append(obj);app.stdin.write((json.dumps(obj)+'\n').encode('utf8'));app.stdin.flush()
 def response(identity):
  end=time.monotonic()+30
  while time.monotonic()<end:
   try:obj=q.get(timeout=.2)
   except queue.Empty:
    if app.poll() is not None:raise RuntimeError('app-server terminal')
    continue
   record['received'].append(obj)
   if obj.get('id')==identity:
    if 'error' in obj:raise RuntimeError('RPC error '+json.dumps(obj['error']))
    return obj['result']
  raise RuntimeError('RPC response deadline')
 proposal=None
 try:
  artifact=ready['image']['artifact'];image=O/'images'/artifact['path'].rsplit('/',1)[-1]
  if hashlib.sha256(image.read_bytes()).hexdigest()!=artifact['sha256']:raise RuntimeError('initial PNG digest')
  record['model_input_png_sha256']=artifact['sha256']
  send(dict(id=1,method='initialize',params=dict(clientInfo=dict(name='calc3311-measured-client',version='1'),capabilities=dict(experimentalApi=True))));record['initialize']=response(1);send(dict(method='initialized',params={}))
  params=dict(model=P['model'],cwd=str(workspace),ephemeral=True,sandbox='read-only',approvalPolicy='never',environments=[],selectedCapabilityRoots=[],allowProviderModelFallback=False,dynamicTools=[P['tool']],baseInstructions=P['base_instructions'],config=dict(project_doc_max_bytes=0,model_reasoning_effort='low'))
  send(dict(id=2,method='thread/start',params=params));record['thread_start']=response(2);thread=record['thread_start']['thread']['id']
  if record['thread_start']['model']!=P['model'] or record['thread_start']['reasoningEffort']!='low':raise RuntimeError('model settings echo')
  record['turn_start_requests']=1
  prompt='In this actual Calc screenshot, ground an interior point of cell A2 (column A, row 2, directly below the a header). Use enter_product exactly once. The tool will fill A2 with '+str(task['a'])+', B2 with '+str(task['b'])+', C2 with =A2*B2 and save. It does not navigate to A2 for you: your clicked position must be A2. After the exact feedback image, report what is visible. Do not repeat input or use other tools.'
  send(dict(id=3,method='turn/start',params=dict(threadId=thread,effort='low',input=[dict(type='text',text=prompt),dict(type='localImage',path=str(image))])));record['turn_start']=response(3)
  end=time.monotonic()+110
  while time.monotonic()<end:
   try:obj=q.get(timeout=.2)
   except queue.Empty:
    if app.poll() is not None:raise RuntimeError('app-server terminal during turn')
    continue
   record['received'].append(obj);method=obj.get('method','');v=obj.get('params',{})
   if method.startswith('mcpServer/') and v.get('status') not in ('disabled',None):raise RuntimeError('unexpected MCP startup')
   if method=='item/started' and v['item']['type'] not in ('reasoning','agentMessage','dynamicToolCall','userMessage'):raise RuntimeError('unexpected item')
   if 'id' in obj and method:
    if method!='item/tool/call' or record['dynamic_calls'] or v.get('tool')!=P['tool']['name'] or v.get('threadId')!=thread:raise RuntimeError('unexpected/duplicate tool request')
    args=v['arguments'];args=json.loads(args) if isinstance(args,str) else args
    if set(args)!=set(('x','y')) or any(type(args[k]) is not int for k in ('x','y')) or not 0<=args['x']<1280 or not 0<=args['y']<800:raise RuntimeError('arguments rejected before input')
    proposal=dict(x=args['x'],y=args['y'],binding=ready['geometry']);save(O/(label+'.proposal.json'),proposal);record['dynamic_calls']=1;record['tool_request']=obj
    done_label=label.split('-repair')[0];done=wait_path(O/(done_label+'.DONE.json'),native,15)
    artifact=done['image']['image']['artifact'];png=O/'images'/artifact['path'].rsplit('/',1)[-1];data=png.read_bytes()
    if hashlib.sha256(data).hexdigest()!=artifact['sha256']:raise RuntimeError('feedback digest')
    record['model_feedback_png_sha256']=artifact['sha256']
    send(dict(id=obj['id'],result=dict(success=True,contentItems=[dict(type='inputText',text='Native input completed and was released. Inspect the exact resulting screenshot; completion is not a claim that the document is correct.'),dict(type='inputImage',imageUrl='data:image/png;base64,'+base64.b64encode(data).decode())])))
   if method=='turn/completed':
    record['turn_completed']=v
    if v['turn']['status']!='completed' or record['dynamic_calls']!=1:raise RuntimeError('turn status/call count')
    usage=[m['params']['tokenUsage'] for m in record['received'] if m.get('method')=='thread/tokenUsage/updated']
    if not usage:raise RuntimeError('usage unavailable')
    record['usage']=usage[-1]['total'];record['usage_updates']=len(usage);break
  else:raise RuntimeError('turn deadline')
 except Exception:record['errors'].append(traceback.format_exc())
 finally:
  app.stdin.close()
  try:record['app_server_exit']=app.wait(10)
  except subprocess.TimeoutExpired:app.terminate();record['forced_terminate']=True;record['app_server_exit']=app.wait(5)
  while not q.empty():record['received'].append(q.get())
  err.close();record['ended_wall_ns']=time.time_ns();save(stage/'HOST_RECORD.private.json',record)
 if record['errors']:raise RuntimeError('model stage failed '+label+' '+record['errors'][0])
 return proposal,dict(label=label,usage=record['usage'],thread_id=thread,dynamic_calls=record['dynamic_calls'],wall_ns=record['ended_wall_ns']-record['started_wall_ns'])
for index,mode in enumerate(P['sessions']):
 O=R/'runs'/('session'+str(index+1)+'-'+mode);O.mkdir(parents=True,exist_ok=False);name='calc3311-4d74-'+O.name
 argv=[W,'run','--name',name,'--pull','never','--network','none','--cpus','1','--memory','512m','--user','65534:65534','--tmpfs','/tmp:rw,size=64m,mode=1777','--env','PYTHONDONTWRITEBYTECODE=1','--env','PYTHONPATH=/src/sources','--volume',str(R/'candidate-input')+':/src:ro','--volume',str(O)+':/out','--workdir','/src',P['image'],'timeout','--signal=TERM','--kill-after=3s','900s','python3','-B','native_sequence.py',str(index)]
 record=dict(index=index,mode=mode,argv=argv,started_wall_ns=time.time_ns(),errors=[],model_stages=[],tasks=[],cache_attempts=[]);native=None;f=e=None
 try:
  if hashlib.sha256(pathlib.Path(CLI).read_bytes()).hexdigest()!=P['cli_sha256']:raise RuntimeError('CLI binary drift')
  for p,digest in P['source_hashes'].items():
   if hashlib.sha256((R/'candidate-input'/p).read_bytes()).hexdigest()!=digest:raise RuntimeError('frozen source drift '+p)
  f=(O/'native.stdout.txt').open('wb');e=(O/'native.stderr.txt').open('wb');native=subprocess.Popen(argv,stdout=f,stderr=e);record['native_pid']=native.pid;cache=None
  for task in P['tasks']:
   label='task'+str(task['index']);ready=wait_path(O/(label+'.READY.json'),native)
   if mode=='persistent' and cache is not None:
    save(O/(label+'.proposal.json'),cache);kind,outcome=wait_outcome(O,label,native);record['cache_attempts'].append(dict(label=label,outcome=kind,decision=outcome.get('decision')))
    if kind=='REFUSED':
     if outcome['decision']!='STALE_GEOMETRY' or outcome['input_dispatches']!=0:raise RuntimeError('non-repairable refusal')
     cache,stage=ground(O,label+'-repair',outcome,task,native);record['model_stages'].append(stage)
   else:
    cache,stage=ground(O,label,ready,task,native);record['model_stages'].append(stage)
   done=wait_path(O/(label+'.DONE.json'),native,15);score=score_done(O,done);record['tasks'].append(dict(index=task['index'],label=done['label'],score=score))
   save(O/'SESSION.json',record)
   if score['errors']:raise RuntimeError('first saved-effect failure '+json.dumps(score['errors']))
  record['native_exit']=native.wait(15)
  if record['native_exit']:raise RuntimeError('native exit nonzero')
 except Exception:
  record['errors'].append(traceback.format_exc())
  if native and native.poll() is None:
   stopped=subprocess.run([W,'stop',name],capture_output=True,timeout=15);(O/'stop.stdout.txt').write_bytes(stopped.stdout);(O/'stop.stderr.txt').write_bytes(stopped.stderr)
   try:record['native_exit']=native.wait(10)
   except subprocess.TimeoutExpired:record['native_exit_unknown']=True
 finally:
  if f:f.close()
  if e:e.close()
  record['ended_wall_ns']=time.time_ns();save(O/'SESSION.json',record);summaries.append(record);save(R/'EXECUTION.json',dict(sessions=summaries,application_retries=0,status='STOP_FIRST_FAILURE' if record['errors'] else 'RETURNED'))
  inspection=subprocess.run([W,'inspect',name],capture_output=True,timeout=15);(O/'CONTAINER_TERMINAL.txt').write_bytes(inspection.stdout);(O/'inspect.stderr.txt').write_bytes(inspection.stderr)
  print(json.dumps(dict(index=index,mode=mode,errors=record['errors'],tasks=len(record['tasks']),model_stages=len(record['model_stages']))),flush=True)
 if record['errors']:break
sys.exit(bool(summaries[-1]['errors']))
