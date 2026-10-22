"""One-key Xvfb run through the exact release-batch backend raw/publish methods."""
import json, os, select, subprocess, sys, time, threading, traceback, types
from pathlib import Path
from Xlib import X, XK, display
HERE=Path(__file__).resolve().parent
LIVE=HERE.parent/'live_control'
sys.path.insert(0,str(LIVE)); sys.path.insert(0,str(HERE))
from lease import Lease
from input_transition_owner_v4 import InputOwner
from analyze_map01_direct_retained_input_v2 import analyze
# The adapter's actual per-step init/execute lifecycle requires VizDoom; this test
# injects only the abstract parent module and exercises its unmodified raw and
# release-batch methods against the real V4/V12 owner and Xvfb.
stub=types.ModuleType('doom_typed_release_backend_v2')
class BaseBackend: pass
stub.Backend=BaseBackend; stub.suite=object()
sys.modules['doom_typed_release_backend_v2']=stub
from doom_owner_thread_release_batch_backend_v1 import Backend
OUT=Path('/out/raw.json')
def wait_event(d,typ,timeout=2):
 end=time.monotonic()+timeout; seen=[]
 while time.monotonic()<end:
  if d.pending_events():
   e=d.next_event()
   if e.type in (X.KeyPress,X.KeyRelease):
    row={'type':e.type,'detail':e.detail,'window':e.window.id if hasattr(e.window,'id') else e.window,'observed_ns':time.perf_counter_ns()}
    seen.append(row)
    if e.type==typ:return seen
   continue
  ready,_,_=select.select([d.fileno()],[],[],max(0,end-time.monotonic()))
  if not ready:break
 raise TimeoutError(f'event {typ} not observed: {seen!r}')
def down(d,code):
 m=d.query_keymap();return bool(m[code//8]&(1<<(code%8)))
def main():
 raw={'schema':'map01-backend-xvfb-adapter-a24-v1','events':[],'client_events':[],'keymap':{},'error':None}
 xvfb=subprocess.Popen(['Xvfb','-displayfd','1','-screen','0','1024x768x24','-ac','-nolisten','tcp'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
 client=None; backend=None
 try:
  ready,_,_=select.select([xvfb.stdout],[],[],5)
  if not ready:raise TimeoutError('Xvfb startup timed out')
  n=xvfb.stdout.readline().strip()
  if not n.isdigit():raise RuntimeError(f'invalid display number {n!r}')
  display_name=':'+n;os.environ['DISPLAY']=display_name
  client=display.Display(display_name);screen=client.screen()
  win=screen.root.create_window(20,20,320,160,0,screen.root_depth,X.InputOutput,X.CopyFromParent,event_mask=X.KeyPressMask|X.KeyReleaseMask)
  win.map();client.sync();win.set_input_focus(X.RevertToParent,X.CurrentTime);client.sync()
  focus=client.get_input_focus().focus;focus_id=focus.id if hasattr(focus,'id') else focus
  if focus_id!=win.id:raise RuntimeError('focus did not bind to observer window')
  owner=InputOwner(display_name)
  lease=Lease(time.perf_counter_ns()+10_000_000_000);lease.intent_token='a24-backend-token';lease.expected_focus=win.id;lease.focus_invalid=False
  backend=Backend.__new__(Backend);backend.owner=owner;backend.lease=lease;backend.held=set();backend._input_event_context=('a24-probe',0);backend._release_batch=threading.local();backend._last_release_batch_delivery=None;backend._admission_receipts={}
  backend._release_batch.context={'rows':[],'identifier':'a24-probe','step':0,'pending_ups':[]}
  def emit(row):
   saved=dict(row);saved['emit_ns']=time.perf_counter_ns();raw['events'].append(saved)
  backend.emit=emit
  code=client.keysym_to_keycode(XK.string_to_keysym('w'));raw.update({'display':display_name,'window':win.id,'focus':focus_id,'keycode':code})
  backend.raw('w',True);raw['client_events'].extend(wait_event(client,X.KeyPress));raw['keymap']['while_held']=down(client,code)
  backend.raw('w',False);raw['client_events'].extend(wait_event(client,X.KeyRelease));raw['keymap']['after_explicit_up']=down(client,code)
  raw['owner_records_before_close']=owner.records
  raw['analyzer']=analyze(raw['events'])
  owner.close()
 except BaseException as e:raw['error']={'type':type(e).__name__,'message':str(e),'traceback':traceback.format_exc()}
 finally:
  if backend is not None:
   try:
    if not backend.owner._inner.closed:backend.owner.close()
   except BaseException as e:raw['cleanup_error']=repr(e)
   raw['owner_cleanup']={'closed':backend.owner._inner.closed,'stopped':backend.owner._inner.stopped.is_set(),'thread_alive':backend.owner._inner.thread.is_alive(),'records':backend.owner.records}
  if client is not None:client.close()
  if xvfb.poll() is None:xvfb.terminate()
  try:raw['xvfb_exit']=xvfb.wait(timeout=3)
  except subprocess.TimeoutExpired:xvfb.kill();raw['xvfb_exit']=xvfb.wait()
  raw['xvfb_stderr']=xvfb.stderr.read();OUT.write_text(json.dumps(raw,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'error':raw['error'],'event_types':[r['type'] for r in raw['client_events']],'keymap':raw['keymap'],'analyzer_ready':(raw.get('analyzer') or {}).get('measurement_ready'),'holds':(raw.get('analyzer') or {}).get('hold_count'),'xvfb_exit':raw.get('xvfb_exit')},sort_keys=True))
if __name__=='__main__':main()
