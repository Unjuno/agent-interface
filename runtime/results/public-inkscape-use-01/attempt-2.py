import os,json,time,sys,subprocess,select,hashlib
from pathlib import Path
from Xlib import display
from runtime.cli_v1.api import dispatch
from runtime.cli_v1.observe import observe
from runtime.cli_v1.review import review_bytes
from runtime.core_v1.contract import SCHEMA_PROGRAM
out=Path('results-local/public-inkscape-use-02').resolve();out.mkdir(exist_ok=False)
name=':147';number='147'
assert not Path('/tmp/.X11-unix/X147').exists() and not Path('/tmp/.X147-lock').exists()
assert '@/tmp/.X11-unix/X147' not in Path('/proc/net/unix').read_text()
svg=out/'shape.svg'
svg.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300" viewBox="0 0 400 300"><rect id="target" x="80" y="80" width="120" height="80" fill="#25a876"/></svg>')
processes=[];d=None
try:
 def launch(args,env=None):
  process=subprocess.Popen(args,env=env,stdout=(out/(Path(args[0]).name+'.stdout.log')).open('wb'),stderr=(out/(Path(args[0]).name+'.stderr.log')).open('wb'));processes.append(process);return process
 server=launch(['Xvfb',name,'-screen','0','1024x768x24','-nolisten','tcp','-nolisten','unix'])
 for _ in range(100):
  if server.poll() is not None:raise RuntimeError('Xvfb exited')
  if '@/tmp/.X11-unix/X147' in Path('/proc/net/unix').read_text():break
  time.sleep(.05)
 else:raise RuntimeError('Xvfb timeout')
 env=dict(os.environ,DISPLAY=name,XDG_CONFIG_HOME=str(out/'config'),XDG_CACHE_HOME=str(out/'cache'),INKSCAPE_PROFILE_DIR=str(out/'inkscape-profile'))
 env.pop('WAYLAND_DISPLAY',None)
 launch(['openbox'],env)
 app=launch(['inkscape','--app-id-tag=AgentInterfacePublic02',str(svg)],env)
 d=display.Display(name);assert (d.screen().width_in_pixels,d.screen().height_in_pixels)==(1024,768)
 window=None
 def scan(win):
  for child in win.query_tree().children:
   try:
    if 'shape.svg' in (child.get_wm_name() or ''):return child
    found=scan(child)
    if found:return found
   except Exception:pass
 for _ in range(200):
  window=scan(d.screen().root)
  if window:break
  if app.poll() is not None:raise RuntimeError('app exited')
  time.sleep(.05)
 if window is None:raise RuntimeError('window timeout')
 targets={'inkscape':window.id};index=0
 (out/'target.json').write_text(json.dumps({'targets':targets,'display':name,'title':window.get_wm_name()}))
 def present(row):
  global index
  index+=1
  data=json.dumps(row).encode();(out/f'result-{index}.json').write_bytes(data)
  reviewed=review_bytes(data,out);(out/f'review-{index}.json').write_text(json.dumps(reviewed))
  print(json.dumps({'index':index,'status':row['status'],'image_status':reviewed['image_status'],'image_reference':reviewed.get('image_reference')}),flush=True)
 geom=window.get_geometry()
 present(observe(targets,target='inkscape',frame='window_client',region=[0,0,geom.width,geom.height],capture_directory=str(out/'images'),display_name=name))
 while True:
  ready,_,_=select.select([sys.stdin],[],[],180)
  if not ready:raise RuntimeError('primary decision timeout')
  line=sys.stdin.readline()
  if not line:break
  request=json.loads(line)
  (out/f'decision-{index}.json').write_text(json.dumps(request))
  if request.get('finish'):break
  geom=window.get_geometry()
  if request.get('observe'):
   row=observe(targets,target='inkscape',frame='window_client',region=[0,0,geom.width,geom.height],capture_directory=str(out/'images'),display_name=name)
  else:
   program={'schema':SCHEMA_PROGRAM,'program_id':f'primary-{index}','source':{'observation_seq':index,'binding_revision':0},'authority':{'lease_id':'owned-primary','expires_at_ns':time.monotonic_ns()+5_000_000_000},'terminal':{'release_all_required':True},'ops':[{'op':'focus','target':'inkscape'},*request['ops'],{'op':'observe','frame':'window_client','x':0,'y':0,'w':geom.width,'h':geom.height},{'op':'release_all'}]}
   (out/f'program-{index}.json').write_text(json.dumps(program))
   row=dispatch(program,targets,current_observation_seq=index,current_binding_revision=0,capture_directory=str(out/'images'),display_name=name)
  present(row)
finally:
 if d is not None:d.close()
 cleanup=[]
 for proc in reversed(processes):
  if proc.poll() is None:proc.terminate()
  try:proc.wait(timeout=10)
  except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=5)
  cleanup.append({'pid':proc.pid,'exit':proc.returncode})
 (out/'cleanup.json').write_text(json.dumps(cleanup))
