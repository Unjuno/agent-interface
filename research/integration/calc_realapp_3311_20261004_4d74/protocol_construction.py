import json,pathlib,subprocess,time,traceback
from saved_oracle import score_done
R=pathlib.Path(__file__).resolve().parent;P=json.loads((R/'PLAN.json').read_text(encoding='utf-8'));O=R/'runs/protocol04';O.mkdir(exist_ok=False);W=r'C:\Program Files\WSL\wslc.exe';name='calc3311-4d74-protocol04'
argv=[W,'run','--name',name,'--pull','never','--network','none','--cpus','1','--memory','512m','--user','65534:65534','--tmpfs','/tmp:rw,size=64m,mode=1777','--env','PYTHONDONTWRITEBYTECODE=1','--env','PYTHONPATH=/src/sources','--volume',str(R)+':/src:ro','--volume',str(O)+':/out','--workdir','/src',P['image'],'timeout','--signal=TERM','--kill-after=3s','60s','python3','-B','native_sequence.py','0']
f=(O/'stdout.txt').open('wb');e=(O/'stderr.txt').open('wb');p=subprocess.Popen(argv,stdout=f,stderr=e);record=dict(argv=argv,native_pid=p.pid,model_calls=0,scope='new model-free broker construction; host-authored coordinates from previously viewed original Calc images',tasks=[],errors=[]);cache=None
try:
 for task in P['tasks']:
  label='task'+str(task['index']);end=time.monotonic()+20;ready=O/(label+'.READY.json')
  while not ready.exists():
   if p.poll() is not None or time.monotonic()>end:raise RuntimeError('ready unavailable')
   time.sleep(.02)
  view=json.loads(ready.read_text(encoding='utf-8'))
  if cache is None:cache=dict(x=80,y=168,binding=view['geometry'])
  (O/(label+'.proposal.json')).write_text(json.dumps(cache),encoding='utf-8');end=time.monotonic()+10
  while not (O/(label+'.DONE.json')).exists():
   refused=O/(label+'.REFUSED.json');repair=O/(label+'-repair.proposal.json')
   if refused.exists() and not repair.exists():
    r=json.loads(refused.read_text(encoding='utf-8'))
    if task['index']!=3 or r['decision']!='STALE_GEOMETRY' or r['input_dispatches']!=0:raise RuntimeError('unexpected refusal')
    cache=dict(x=160,y=204,binding=r['geometry']);repair.write_text(json.dumps(cache),encoding='utf-8');record['stale_refusal']=r
   if p.poll() is not None or time.monotonic()>end:raise RuntimeError('done unavailable')
   time.sleep(.02)
  done=json.loads((O/(label+'.DONE.json')).read_text(encoding='utf-8'));score=score_done(O,done);record['tasks'].append(dict(index=task['index'],score=score))
  if score['errors']:raise RuntimeError('saved-effect failure')
 record['native_exit']=p.wait(10)
 if record['native_exit']:raise RuntimeError('native exit nonzero')
except Exception:
 record['errors'].append(traceback.format_exc())
 if p.poll() is None:subprocess.run([W,'stop',name],capture_output=True,timeout=15);record['native_exit']=p.wait(10)
finally:
 f.close();e.close();(O/'HOST_RECORD.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');inspection=subprocess.run([W,'inspect',name],capture_output=True,timeout=15);(O/'CONTAINER_TERMINAL.txt').write_bytes(inspection.stdout)
print(json.dumps(dict(errors=record['errors'],tasks=len(record['tasks']),model_calls=0,native_exit=record.get('native_exit'))));raise SystemExit(bool(record['errors']))
