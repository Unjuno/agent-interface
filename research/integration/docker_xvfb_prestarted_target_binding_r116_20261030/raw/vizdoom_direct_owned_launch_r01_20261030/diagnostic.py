import json, os, subprocess, time, traceback
from pathlib import Path
from Xlib import display
import vizdoom as vd
from runtime.guarded_x11_v1.owned_target_process import OwnedTargetProcess
root=Path('/evidence'); result={'status':'RUNNING','input_sent':False}; xvfb=None; d=None; owner=None
try:
 os.environ['DISPLAY']=':91';os.environ['XDG_CACHE_HOME']='/tmp/cache'
 xvfb=subprocess.Popen(['Xvfb',':91','-screen','0','1280x1024x24','-cc','4','-nolisten','tcp'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 for _ in range(150):
  try:d=display.Display(':91');break
  except Exception:time.sleep(.02)
 if d is None:raise RuntimeError('Xvfb unavailable')
 pkg=Path(vd.__file__).resolve().parent;argv=[str(pkg/'vizdoom'),'-iwad',str(pkg/'freedoom2.wad'),'-warp','1','-window','-nosound','-nojoy','-width','640','-height','480']
 owner=OwnedTargetProcess.launch(argv,disposable=True,env=os.environ.copy()); result['launched_pid']=owner.pid
 windows=[]
 for _ in range(200):
  if not owner.running:break
  windows=[]
  for w in d.screen().root.query_tree().children:
   title=w.get_wm_name()
   if title and ('DOOM' in title.upper()) and w.get_attributes().map_state==2:windows.append((w,title))
  if len(windows)==1:break
  time.sleep(.02)
 if len(windows)!=1:raise RuntimeError('no unique visible Doom window; count='+str(len(windows))+' exit='+str(owner._process.poll()))
 w,title=windows[0];result['window']={'xid':w.id,'title':title}
 result['binding']=owner.bind_x11_target_supervised(':91',w.id,timeout_s=1.0)
 if result['binding'].get('status')!='bound':raise RuntimeError('XRes binding refused: '+str(result['binding']))
 result['retirement']=owner.retire_bound_target()
 if result['retirement'].get('process_exit_verified') is not True:raise RuntimeError('target exit unconfirmed')
 result['status']='PASS'
except BaseException as e:result.update(status='FAIL',error_type=type(e).__name__,error=str(e),traceback=traceback.format_exc())
finally:
 if owner is not None:
  if owner.running:
   import signal
   signal.pidfd_send_signal(owner._pidfd,signal.SIGKILL)
   try:owner._process.wait(timeout=2)
   except subprocess.TimeoutExpired:result['cleanup_error']='target did not exit'
  try:owner.close()
  except Exception as e:result['handle_close_error']=repr(e)
 if d is not None:d.close()
 if xvfb is not None:
  if xvfb.poll() is None:xvfb.terminate()
  try:xvfb.wait(timeout=3)
  except subprocess.TimeoutExpired:xvfb.kill();xvfb.wait()
  result['xvfb_exitcode']=xvfb.returncode
 (root/'result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result));raise SystemExit(0 if result['status']=='PASS' else 1)
