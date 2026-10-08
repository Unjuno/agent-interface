import hashlib,json,pathlib,subprocess,time,traceback
R=pathlib.Path(__file__).resolve().parent;P=json.loads((R/'PLAN.json').read_text(encoding='utf-8'));W=r'C:\Program Files\WSL\wslc.exe';rows=[]
for spec in P['rows']:
 O=R/'runs'/('row'+str(spec['index']+1));O.mkdir(parents=True,exist_ok=False);name='calc-keyboard-reference-v2-4d74-'+O.name
 argv=[W,'run','--name',name,'--pull','never','--network','none','--cpus','1','--memory','512m','--user','65534:65534','--tmpfs','/tmp:rw,size=64m,mode=1777','--env','PYTHONDONTWRITEBYTECODE=1','--env','PYTHONPATH=/src/sources','--volume',str(R)+':/src:ro','--volume',str(O)+':/out','--workdir','/src',P['image'],'timeout','--signal=TERM','--kill-after=3s','45s','python3','-B','producer.py',str(spec['index'])]
 record=dict(spec=spec,argv=argv,started_wall_ns=time.time_ns(),errors=[],model_calls=0);p=None;f=e=None
 try:
  for n,h in P['source_hashes'].items():
   if hashlib.sha256((R/n).read_bytes()).hexdigest()!=h:raise RuntimeError('source pin '+n)
  f=(O/'host.stdout.txt').open('wb');e=(O/'host.stderr.txt').open('wb');p=subprocess.Popen(argv,stdout=f,stderr=e);record['client_pid']=p.pid;record['exit_code']=p.wait(60)
  if record['exit_code']:raise RuntimeError('native infrastructure/prime/receipt failure')
 except Exception:
  record['errors'].append(traceback.format_exc())
  if p and p.poll() is None:
   s=subprocess.run([W,'stop',name],capture_output=True,timeout=15);(O/'stop.stdout.txt').write_bytes(s.stdout);(O/'stop.stderr.txt').write_bytes(s.stderr);record['exit_code']=p.wait(10)
 finally:
  if f:f.close()
  if e:e.close()
  record['ended_wall_ns']=time.time_ns();(O/'HOST_RECEIPT.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');s=subprocess.run([W,'inspect',name],capture_output=True,timeout=15);(O/'CONTAINER_TERMINAL.txt').write_bytes(s.stdout);rows.append(record);(R/'EXECUTION.json').write_text(json.dumps(dict(rows=rows,retries=0),indent=2)+'\n',encoding='utf-8')
 print(json.dumps(dict(index=spec['index'],wait_ms=spec['click_wait_ms'],exit=record.get('exit_code'),errors=record['errors'])),flush=True)
 if record['errors']:break
raise SystemExit(bool(rows[-1]['errors']))
