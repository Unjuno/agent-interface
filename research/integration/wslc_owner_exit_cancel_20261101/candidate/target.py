"""Independent X client: record received key events and an application value."""
import json,os,pathlib,time
from Xlib import X,XK,display
out=pathlib.Path(os.environ.get('TARGET_OUT','/out'));d=display.Display(os.environ.get('TEST_DISPLAY',':195'));root=d.screen().root
w=root.create_window(10,10,200,120,0,d.screen().root_depth,X.InputOutput,X.CopyFromParent,
 background_pixel=0x224466,event_mask=X.KeyPressMask|X.KeyReleaseMask|X.ExposureMask)
w.map();d.sync()
gc=w.create_gc(foreground=0xeeeeee)
def paint():
 w.fill_rectangle(gc,18,18,4,4);d.sync()
paint()
(out/'target-ready.json').write_text(json.dumps({'xid':w.id,'pid':os.getpid()})+'\n')
events=[];value='';end=time.monotonic()+20
while time.monotonic()<end:
 while d.pending_events():
  e=d.next_event()
  if e.type==X.Expose:paint()
  if e.type in (X.KeyPress,X.KeyRelease):
   sym=d.keycode_to_keysym(e.detail,0);name=XK.keysym_to_string(sym)
   events.append({'type':'press' if e.type==X.KeyPress else 'release','key':name,'host_ns':time.monotonic_ns()})
   if e.type==X.KeyPress and name=='a':value+='a'
   (out/'target-events.json').write_text(json.dumps({'value':value,'events':events},indent=2)+'\n')
 if (out/'target-stop').exists():break
 time.sleep(.01)
d.close()
