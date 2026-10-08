"""Measured registered-tool client; no coding delegation, host tools or GUI authority."""
import base64,hashlib,json,os,pathlib,queue,subprocess,sys,threading,time,traceback
R=pathlib.Path(__file__).resolve().parent;P=json.loads((R/'PLAN.json').read_text());W=r'C:\Program Files\WSL\wslc.exe';CLI=r'C:\Users\junny\AppData\Local\OpenAI\Codex\bin\8aaf1547b825b104\codex.exe';summary=[]
def save(p,obj):p.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n',encoding='utf-8')
def wait_path(p,client,seconds):
 end=time.monotonic()+seconds
 while not p.exists():
  if client.poll() is not None:raise RuntimeError('native producer exited before '+p.name)
  if time.monotonic()>end:raise RuntimeError('file deadline '+p.name)
  time.sleep(.02)
 return json.loads(p.read_text(encoding='utf-8'))
for spec in (P['rows'] if sys.argv[1]=='formal' else [dict(index=-1,variant='A',target='GREEN')]):
 i=spec['index'];O=R/'runs'/('diagnostic01' if i<0 else 'row'+str(i+1).zfill(2));O.mkdir(parents=True,exist_ok=False);(O/'workspace').mkdir();name='schema6210-dyn-4d74-'+O.name
 argv=[W,'run','--name',name,'--pull','never','--network','none','--cpus','1','--memory','512m','--user','65534:65534','--tmpfs','/tmp:rw,size=64m,mode=1777','--env','PYTHONDONTWRITEBYTECODE=1','--env','PYTHONPATH=/src/sources','--volume',str(R)+':/src:ro','--volume',str(O)+':/out','--workdir','/src',P['image'],'timeout','--signal=TERM','--kill-after=3s','180s','python3','-B','producer.py',str(i)]
 f=(O/'native.stdout.txt').open('wb');e=(O/'native.stderr.txt').open('wb');native=subprocess.Popen(argv,stdout=f,stderr=e);app=None;appErr=None;q=queue.Queue();record=dict(spec=spec,argv=argv,native_pid=native.pid,started_wall_ns=time.time_ns(),errors=[],sent=[],received=[],dynamic_calls=0,turn_start_requests=0)
 def send(obj):record['sent'].append(obj);app.stdin.write((json.dumps(obj)+'\n').encode());app.stdin.flush()
 def read_response(identity,seconds=30):
  end=time.monotonic()+seconds
  while time.monotonic()<end:
   try:obj=q.get(timeout=.2)
   except queue.Empty:
    if app.poll() is not None:raise RuntimeError('app-server exited')
    continue
   record['received'].append(obj)
   if obj.get('id')==identity:
    if 'error' in obj:raise RuntimeError('RPC error '+json.dumps(obj['error']))
    return obj['result']
  raise RuntimeError('RPC response deadline')
 try:
  if hashlib.sha256(pathlib.Path(CLI).read_bytes()).hexdigest()!=P['cli_sha256']:raise RuntimeError('CLI source drift')
  if i>=0:
   ready=wait_path(O/'READY_FOR_MODEL.json',native,15);initial=ready['image']['artifact'];image=O/'images'/pathlib.Path(initial['path']).name
   if hashlib.sha256(image.read_bytes()).hexdigest()!=initial['sha256']:raise RuntimeError('image custody')
   appErr=(O/'app-server.stderr.txt').open('wb');app=subprocess.Popen(P['app_server_argv'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=appErr);record['app_server_pid']=app.pid
   def reader(pipe=app.stdout):
    for line in pipe:
     try:q.put(json.loads(line))
     except Exception:q.put(dict(non_json_stdout=line.decode('utf8','replace')))
   threading.Thread(target=reader,daemon=True).start()
   send(dict(id=1,method='initialize',params=dict(clientInfo=dict(name='schema6210-native-dynamic',version='1'),capabilities=dict(experimentalApi=True))));record['initialize']=read_response(1);send(dict(method='initialized',params={}))
   thread_params=dict(model='gpt-5.6-luna',cwd=str(O/'workspace'),ephemeral=True,sandbox='read-only',approvalPolicy='never',environments=[],selectedCapabilityRoots=[],allowProviderModelFallback=False,dynamicTools=[P['tools'][spec['variant']]],baseInstructions=P['base_instructions'],config=dict(project_doc_max_bytes=0,model_reasoning_effort='low'))
   send(dict(id=2,method='thread/start',params=thread_params));start=read_response(2);record['thread_start']=start
   if start['model']!='gpt-5.6-luna' or start['reasoningEffort']!='low':raise RuntimeError('model/settings echo mismatch')
   thread=start['thread']['id'];record['turn_start_requests']=1;record['model_input_png_sha256']=initial['sha256']
   send(dict(id=3,method='turn/start',params=dict(threadId=thread,effort='low',input=[dict(type='text',text='Use the registered coordinate tool exactly once to select the '+spec['target']+' button visible in the screenshot. Ground coordinates only in the screenshot. After its feedback image, report the selection. Do not use other tools or repeat the click.'),dict(type='localImage',path=str(image))])));record['turn_start']=read_response(3)
   deadline=time.monotonic()+110
   while True:
    if time.monotonic()>deadline:raise RuntimeError('turn deadline')
    try:obj=q.get(timeout=.2)
    except queue.Empty:
     if app.poll() is not None:raise RuntimeError('app-server exited during turn')
     continue
    record['received'].append(obj);method=obj.get('method','');params=obj.get('params',{})
    if method.startswith('mcpServer/') and params.get('status') not in ('disabled',None):raise RuntimeError('unexpected MCP exposure startup')
    if method=='item/started' and params['item']['type'] not in ('reasoning','agentMessage','dynamicToolCall','userMessage'):raise RuntimeError('unexpected model tool/item')
    if 'id' in obj and method:
     if method!='item/tool/call' or record['dynamic_calls'] or params.get('tool')!=P['tools'][spec['variant']]['name'] or params.get('threadId')!=thread:raise RuntimeError('unexpected/duplicate server request')
     args=params['arguments'];args=json.loads(args) if isinstance(args,str) else args;keys=('x','y') if spec['variant']=='A' else ('horizontal','vertical')
     if set(args)!=set(keys) or any(type(args[k])!=int for k in keys) or not 0<=args[keys[0]]<640 or not 0<=args[keys[1]]<360:raise RuntimeError('tool arguments rejected before GUI')
     proposal=dict(action='click',x=args['x'],y=args['y']) if spec['variant']=='A' else dict(operation='pointer_select',horizontal=args['horizontal'],vertical=args['vertical']);save(O/'proposal.json',proposal);record['dynamic_calls']=1;record['tool_request']=obj
     raw=wait_path(O/'raw.json',native,10)
     if raw['errors'] or raw['receipt']['status']!='completed':raise RuntimeError('native first outcome failed')
     final=raw['final']['artifact'];final_path=O/'images'/pathlib.Path(final['path']).name;data=final_path.read_bytes()
     if hashlib.sha256(data).hexdigest()!=final['sha256']:raise RuntimeError('feedback PNG identity')
     record['model_feedback_png_sha256']=final['sha256'];send(dict(id=obj['id'],result=dict(success=True,contentItems=[dict(type='inputText',text='The guarded native click completed and physical input was released. Inspect this exact feedback screenshot.'),dict(type='inputImage',imageUrl='data:image/png;base64,'+base64.b64encode(data).decode())])))
    if method=='turn/completed':
     record['turn_completed']=params
     if params['turn']['status']!='completed' or record['dynamic_calls']!=1:raise RuntimeError('turn completion/tool count')
     usage=[v['params']['tokenUsage'] for v in record['received'] if v.get('method')=='thread/tokenUsage/updated']
     if not usage:raise RuntimeError('actual token usage absent')
     record['usage']=usage[-1]['total'];record['usage_updates']=len(usage);break
  record['native_exit']=native.wait(timeout=15)
  if record['native_exit']:raise RuntimeError('native exit nonzero')
 except Exception:
  record['errors'].append(traceback.format_exc());stopped=subprocess.run([W,'stop',name],capture_output=True,timeout=15);(O/'stop.stdout.txt').write_bytes(stopped.stdout);(O/'stop.stderr.txt').write_bytes(stopped.stderr)
  try:record['native_exit']=native.wait(timeout=10)
  except subprocess.TimeoutExpired:record['native_exit_unknown']=True
 finally:
  if app:
   app.stdin.close()
   try:record['app_server_exit']=app.wait(timeout=10)
   except subprocess.TimeoutExpired:app.terminate();record['app_server_forced_terminate']=True;record['app_server_exit']=app.wait(timeout=5)
   while not q.empty():record['received'].append(q.get())
  if appErr:appErr.close()
  f.close();e.close();record['ended_wall_ns']=time.time_ns();save(O/'HOST_RECORD.json',record);inspection=subprocess.run([W,'inspect',name],capture_output=True,timeout=15);(O/'container-terminal.json').write_bytes(inspection.stdout);(O/'inspect.stderr.txt').write_bytes(inspection.stderr);summary.append(dict(index=i,errors=record['errors'],usage=record.get('usage'),dynamic_calls=record['dynamic_calls']));print(json.dumps(summary[-1]),flush=True)
 if record['errors']:break
save(R/('EXECUTION.json' if sys.argv[1]=='formal' else 'DIAGNOSTIC.json'),dict(rows=summary,status='STOP_FIRST_OUTCOME' if summary[-1]['errors'] else 'RETURNED',application_retries=0));sys.exit(bool(summary[-1]['errors']))
