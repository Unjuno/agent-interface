import hashlib,json,re,subprocess,sys,time,uuid
from pathlib import Path
root=Path(sys.argv[1]); run=uuid.uuid4().hex; cidfile=root/'container.cid'
image='sha256:6150a4f3c779a51b3ac6a7d93bc1d0450803325efb7ab38ade8b1aaf79c33e25'
result={'status':'UNKNOWN','run_id':run,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'started_ns':time.monotonic_ns()}
def cmd(name,args,timeout=8):
 (root/(name+'.command.json')).write_text(json.dumps(args,indent=2),encoding='utf-8')
 start=time.monotonic_ns()
 try:
  p=subprocess.run(args,capture_output=True,timeout=timeout)
  info={'start_ns':start,'end_ns':time.monotonic_ns(),'exit':p.returncode}
  (root/(name+'.stdout')).write_bytes(p.stdout);(root/(name+'.stderr')).write_bytes(p.stderr)
  (root/(name+'.result.json')).write_text(json.dumps(info),encoding='utf-8')
  return p
 except subprocess.TimeoutExpired as e:
  (root/(name+'.stdout')).write_bytes(e.stdout or b'');(root/(name+'.stderr')).write_bytes(e.stderr or b'')
  (root/(name+'.result.json')).write_text(json.dumps({'start_ns':start,'end_ns':time.monotonic_ns(),'timeout':True}),encoding='utf-8');raise
try:
 args=['wslc','run','--detach','--name','ai-r579-'+run[:16],'--label','agent-interface.run-id='+run,'--cidfile',str(cidfile),'--network','none','--cpus','1','--memory','1g','--pull','never','--entrypoint','python3',image,'-c','import time,sys; time.sleep(3); sys.exit(7)']
 p=cmd('launch',args,15)
 if p.returncode:raise RuntimeError('launch failed')
 deadline=time.monotonic()+8;cid=None
 while time.monotonic()<deadline:
  if cidfile.exists():
   s=cidfile.read_text(encoding='ascii').strip()
   if re.fullmatch('[0-9a-f]{64}',s):cid=s;break
  time.sleep(.05)
 if not cid:raise RuntimeError('full CID unavailable')
 result['cid']=cid
 for n in range(20):
  p=cmd('inspect-%02d'%n,['wslc','container','inspect',cid,'--format','json'])
  if p.returncode or p.stderr:raise RuntimeError('inspect failed')
  rows=json.loads(p.stdout)
  if len(rows)!=1 or rows[0].get('Id')!=cid or rows[0].get('Config',{}).get('Labels',{}).get('agent-interface.run-id')!=run:raise RuntimeError('identity mismatch')
  state=rows[0].get('State',{})
  if state.get('Running') is False and state.get('Status')=='exited' and type(state.get('ExitCode')) is int:break
  time.sleep(.25)
 else:raise RuntimeError('stopped state unavailable')
 result['observed_exit_code']=state['ExitCode']
 p=cmd('remove',['wslc','container','remove',cid])
 if p.returncode or p.stderr or p.stdout.strip()!=cid.encode():raise RuntimeError('remove not confirmed')
 p=cmd('post-list',['wslc','container','list','--all','--filter','id='+cid,'--format','json','--no-trunc'])
 if p.returncode or p.stderr or p.stdout.strip():raise RuntimeError('post list not empty')
 result['status']='observed_exit_and_removal'
except BaseException as e:result['error_type']=type(e).__name__;result['error']=str(e)
finally:
 result['ended_ns']=time.monotonic_ns();(root/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({'status':result['status'],'exit_code':result.get('observed_exit_code'),'error':result.get('error')}))
