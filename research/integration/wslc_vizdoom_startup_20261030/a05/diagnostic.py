import json,os,secrets,signal,subprocess,tempfile,time
from pathlib import Path
from Xlib import display
import vizdoom as vd
import runtime.guarded_x11_v1.owned_target_process as mod
E=Path('/evidence'); result={'observations':[]}; server=None; owner=None; conn=None
try:
 with tempfile.TemporaryDirectory() as td:
  auth=Path(td)/'old';auth.touch()
  subprocess.run(['xauth','-f',str(auth),'add',':93','MIT-MAGIC-COOKIE-1',secrets.token_hex(16)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=True)
  server=subprocess.Popen(['Xvfb',':93','-screen','0','640x480x24','-nolisten','tcp','-nolisten','unix','-auth',str(auth)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  os.environ['XAUTHORITY']=str(auth);os.environ['DISPLAY']=':93';os.environ['XDG_CACHE_HOME']='/tmp/cache'
  end=time.monotonic()+4
  while time.monotonic()<end:
   if server.poll() is not None:raise RuntimeError('Xvfb exited before ready')
   try:conn=display.Display(':93');break
   except Exception:time.sleep(.03)
  if conn is None:raise RuntimeError('Xvfb not ready')
  pkg=Path(vd.__file__).resolve().parent;cfg=Path(td)/'old.ini';cfg.write_text('[Doom.Bindings]\nw=+forward\n')
  argv=[str(pkg/'vizdoom'),'-iwad',str(pkg/'freedoom2.wad'),'-config',str(cfg),'-warp','1','-window','-nosound','-nojoy','-width','640','-height','480']
  orig=mod.subprocess.Popen
  with (E/'target-stdout.bin').open('wb') as out,(E/'target-stderr.bin').open('wb') as err:
   def capture(*args,**kwargs):
    kwargs['stdout']=out;kwargs['stderr']=err
    return orig(*args,**kwargs)
   mod.subprocess.Popen=capture
   try:owner=mod.OwnedTargetProcess.launch(argv,disposable=True,env=os.environ.copy())
   finally:mod.subprocess.Popen=orig
   started=time.monotonic_ns();found=False
   for i in range(250):
    alive=owner.running; titles=[]
    for w in conn.screen().root.query_tree().children:
     try:titles.append({'title':w.get_wm_name(),'map_state':w.get_attributes().map_state})
     except Exception:pass
    if i%10==0 or not alive or any(x['title'] and 'DOOM' in x['title'].upper() and x['map_state']==2 for x in titles):
     result['observations'].append({'elapsed_ms':(time.monotonic_ns()-started)/1e6,'alive':alive,'returncode':owner._process.returncode,'windows':titles})
    found=any(x['title'] and 'DOOM' in x['title'].upper() and x['map_state']==2 for x in titles)
    if not alive or found:break
    time.sleep(.02)
   result.update(status='mapped' if found else 'not_mapped',returncode=owner._process.poll(),elapsed_ms=(time.monotonic_ns()-started)/1e6)
except BaseException as e:result.update(status='error',error_type=type(e).__name__,error=str(e))
finally:
 if owner is not None:
  if owner.running:
   signal.pidfd_send_signal(owner._pidfd,signal.SIGKILL);owner._process.wait(timeout=3)
  owner.close()
 if conn is not None:conn.close()
 if server is not None and server.poll() is None:server.terminate();server.wait(timeout=3)
 (E/'diagnostic-result.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(result))
