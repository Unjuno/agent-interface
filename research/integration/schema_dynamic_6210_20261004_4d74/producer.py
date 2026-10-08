import base64,hashlib,json,os,pathlib,signal,subprocess,sys,time,traceback
from Xlib import X,display
from runtime.backends.x11_v1.backend import X11Backend
from runtime.backends.x11_v1.session import X11RuntimeSession
from surface import decode,program
R=pathlib.Path('/src');O=pathlib.Path('/out');plan=json.loads((R/'PLAN.json').read_text());index=int(sys.argv[1]);spec=plan['rows'][index] if index>=0 else dict(index=-1,variant='A',target='GREEN',diagnostic=True);raw=dict(spec=spec,errors=[],started_ns=time.monotonic_ns(),source_hashes={p:hashlib.sha256((R/p).read_bytes()).hexdigest() for p in plan['source_hashes']},cgroups={p:pathlib.Path('/sys/fs/cgroup/'+p).read_text().strip() if pathlib.Path('/sys/fs/cgroup/'+p).exists() else None for p in ['cpu.max','memory.max','pids.max']});actors=[];handles=[];b=d=None
def save(n,obj):(O/n).write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n')
def spawn(n,args):
 h=(O/(n+'.log')).open('wb');handles.append(h);p=subprocess.Popen(args,env=dict(os.environ,DISPLAY=':161'),stdout=h,stderr=h,start_new_session=True);actors.append((n,p));return p
def wait_file(p,seconds):
 end=time.monotonic()+seconds
 while not p.exists():
  if time.monotonic()>end:raise RuntimeError('file deadline '+p.name)
  time.sleep(.02)
 return json.loads(p.read_text())
try:
 if raw['source_hashes']!=plan['source_hashes']:raise RuntimeError('source drift')
 spawn('Xvfb',['Xvfb',':161','-screen','0','640x360x24','-nolisten','tcp','-ac']);end=time.monotonic()+3
 while d is None:
  try:d=display.Display(':161')
  except Exception:
   if time.monotonic()>end:raise
   time.sleep(.02)
 spawn('fixture',['python3','-B','/src/fixture.py']);ready=wait_file(O/'fixture-ready.json',5);time.sleep(.2)
 b=X11Backend(':161',{'owned':ready['window']});b.configure_capture_artifacts(O/'images');raw['initial']=b.observe_read_only('owned','screen_physical_px',[0,0,640,360]);save('initial.json',raw['initial']);raw['initial_effect']=json.loads((O/'effect.json').read_text())
 if index<0:response={'action':'click','x':170,'y':180}
 else:
  stage='row'+str(index+1).zfill(2);image_name=pathlib.Path(raw['initial']['artifact']['path']).name
  save('READY_FOR_MODEL.json',dict(image=raw['initial'],target=spec['target'],variant=spec['variant']));response=wait_file(O/'proposal.json',150)
 raw['proposal']=response;x,y=decode(response,spec['variant']);raw['canonical_program']=program(x,y,time.monotonic_ns()+5_000_000_000);raw['dispatch_start_ns']=time.monotonic_ns();raw['receipt']=X11RuntimeSession(b).dispatch(raw['canonical_program'],current_observation_seq=1,current_binding_revision=1);raw['dispatch_end_ns']=time.monotonic_ns();time.sleep(.1);raw['effect']=json.loads((O/'effect.json').read_text());raw['final']=b.observe_read_only('owned','screen_physical_px',[0,0,640,360]);raw['physical_keys']=list(d.query_keymap());raw['physical_button_mask']=int(d.screen().root.query_pointer().mask)&(X.Button1Mask|X.Button2Mask|X.Button3Mask)
 if raw['receipt']['status']!='completed':raise RuntimeError('public admission/execution did not complete')
except Exception:raw['errors'].append(traceback.format_exc())
finally:
 if b:
  try:raw['cleanup_release']=b.release_all();b.close()
  except Exception:raw['errors'].append(traceback.format_exc())
 if d:d.close()
 for n,p in reversed(actors):
  if p.poll() is None:os.killpg(p.pid,signal.SIGTERM)
  try:code=p.wait(3)
  except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);code=p.wait(2);raw['errors'].append('forced kill '+n)
  raw.setdefault('terminal',[]).append(dict(name=n,pid=p.pid,exit_code=code))
 for h in handles:h.close()
 raw['ended_ns']=time.monotonic_ns();save('raw.json',raw)
print(json.dumps(dict(index=index,errors=raw['errors'],effect=raw.get('effect'))));sys.exit(2 if raw['errors'] else 0)
