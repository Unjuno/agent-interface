import hashlib,importlib.util,json,re,shutil,subprocess,sys,time,uuid
from pathlib import Path
root=Path(sys.argv[1]);helper_source=Path(sys.argv[2]);helper=root/'wslc_cleanup.py';shutil.copyfile(helper_source,helper)
spec=importlib.util.spec_from_file_location('frozen_wslc_cleanup',helper);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
run=uuid.uuid4().hex;cidfile=root/'container.cid';image='sha256:6150a4f3c779a51b3ac6a7d93bc1d0450803325efb7ab38ade8b1aaf79c33e25'
result={'status':'UNKNOWN','run_id':run,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'payload_sha256':hashlib.sha256((root/'payload.py').read_bytes()).hexdigest(),'helper_sha256':hashlib.sha256(helper.read_bytes()).hexdigest(),'started_ns':time.monotonic_ns()};cid=None;last=None

def cmd(name,args,timeout=8):
 (root/(name+'.command.json')).write_text(json.dumps(args,indent=2),encoding='utf-8');start=time.monotonic_ns()
 try:
  p=subprocess.run(args,capture_output=True,timeout=timeout);info={'start_ns':start,'end_ns':time.monotonic_ns(),'exit':p.returncode}
  (root/(name+'.stdout')).write_bytes(p.stdout);(root/(name+'.stderr')).write_bytes(p.stderr);(root/(name+'.result.json')).write_text(json.dumps(info),encoding='utf-8');return p
 except subprocess.TimeoutExpired as e:
  (root/(name+'.stdout')).write_bytes(e.stdout or b'');(root/(name+'.stderr')).write_bytes(e.stderr or b'');(root/(name+'.result.json')).write_text(json.dumps({'start_ns':start,'end_ns':time.monotonic_ns(),'timeout':True}),encoding='utf-8');raise
try:
 payload=(root/'payload.py').read_text(encoding='utf-8-sig')
 args=['wslc','run','--detach','--name','ai-r581-'+run[:16],'--label','agent-interface.run-id='+run,'--cidfile',str(cidfile),'--network','none','--cpus','1','--memory','1g','--pull','never','--entrypoint','python3',image,'-c',payload]
 p=cmd('launch',args,15)
 if p.returncode:raise RuntimeError('launch failed')
 deadline=time.monotonic()+6
 while time.monotonic()<deadline:
  if cid is None and cidfile.exists():
   candidate=cidfile.read_text(encoding='ascii').strip()
   if re.fullmatch('[0-9a-f]{64}',candidate):cid=candidate;result['cid']=cid
  if cid:
   p=cmd('inspect-%03d'%result.get('polls',0),['wslc','container','inspect',cid,'--format','json'])
   result['polls']=result.get('polls',0)+1
   if p.returncode or p.stderr:raise RuntimeError('inspect failed')
   rows=json.loads(p.stdout)
   if len(rows)!=1 or rows[0].get('Id')!=cid or rows[0].get('Config',{}).get('Labels',{}).get('agent-interface.run-id')!=run:raise RuntimeError('identity mismatch')
   last=rows[0]['State']
   if last.get('Running') is False and last.get('Status')=='exited' and type(last.get('ExitCode')) is int:break
  time.sleep(.25)
 else:raise TimeoutError('container deadline')
 result['exit_code']=last['ExitCode']
 for filename in ('calc-smoke.json','calc-smoke.png'):
  p=cmd('copy-'+filename,['wslc','container','cp',cid+':/tmp/'+filename,str(root/filename)])
  if p.returncode:raise RuntimeError('artifact copy failed: '+filename)
 report=json.loads((root/'calc-smoke.json').read_text(encoding='utf-8'))
 result['payload_status']=report.get('status');result['screenshot_hash_matches']=hashlib.sha256((root/'calc-smoke.png').read_bytes()).hexdigest()==report.get('screenshot_sha256')
 if result['exit_code']==0 and result['payload_status']=='window_observed' and result['screenshot_hash_matches']:result['status']='payload_observed'
except BaseException as exc:result['error_type']=type(exc).__name__;result['error']=str(exc)
finally:
 if cid:
  try:
   if last is None or last.get('Running') is True:
    result['stop_receipt']=module.cleanup_owned(cid,run,timeout_s=12,journal_path=root/'stop.jsonl')
   for filename in ('calc-ready.json','calc-smoke.png'):
    try: cmd('after-stop-copy-'+filename,['wslc','container','cp',cid+':/tmp/'+filename,str(root/filename)])
    except BaseException: pass
   result['cleanup_receipt']=module.cleanup_owned(cid,run,timeout_s=12,journal_path=root/'remove.jsonl',remove_exited=True)
  except BaseException as exc:result['cleanup_error_type']=type(exc).__name__
 if result.get('cleanup_receipt',{}).get('status')!='observed_absent':result['status']='UNKNOWN'
 result['ended_ns']=time.monotonic_ns();(root/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'status':result['status'],'exit_code':result.get('exit_code'),'payload_status':result.get('payload_status'),'cleanup':result.get('cleanup_receipt',{}).get('status'),'error':result.get('error'),'cleanup_error':result.get('cleanup_error_type')}))
