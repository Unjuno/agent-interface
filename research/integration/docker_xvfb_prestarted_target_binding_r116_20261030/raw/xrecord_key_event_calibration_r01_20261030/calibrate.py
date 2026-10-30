import json,os,subprocess,threading,time,traceback
from pathlib import Path
from Xlib import X,XK,display
from Xlib.ext import record,xtest
from Xlib.protocol import rq
ROOT=Path('/evidence')
def main():
 r={'status':'RUNNING','checks':{},'events':[],'target_events':[]};x=None;control=None;target=None;rec=None;ctx=None;thread=None
 try:
  os.environ['DISPLAY']=':91';x=subprocess.Popen(['Xvfb',':91','-screen','0','800x600x24','-nolisten','tcp'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  for _ in range(150):
   try:control=display.Display(':91');break
   except Exception:time.sleep(.02)
  if control is None:raise RuntimeError('Xvfb unavailable')
  if not control.has_extension('RECORD'):raise RuntimeError('RECORD extension unavailable')
  target=display.Display(':91');rec=display.Display(':91');w=target.screen().root.create_window(20,20,160,100,0,X.CopyFromParent,X.InputOutput,X.CopyFromParent,event_mask=X.KeyPressMask|X.KeyReleaseMask);w.map();w.set_input_focus(X.RevertToParent,X.CurrentTime);target.sync()
  ctx=rec.record_create_context(0,[record.AllClients],[{'core_requests':(0,0),'core_replies':(0,0),'ext_requests':(0,0,0,0),'ext_replies':(0,0,0,0),'delivered_events':(0,0),'device_events':(X.KeyPress,X.KeyRelease),'errors':(0,0),'client_started':False,'client_died':False}])
  ready=threading.Event(); errors=[]
  def cb(reply):
   if reply.category==record.StartOfData:ready.set();return
   if reply.category!=record.FromServer or reply.client_swapped:return
   data=reply.data
   while len(data):
    event,data=rq.EventField(None).parse_binary_value(data,rec.display,None,None)
    if event.type in (X.KeyPress,X.KeyRelease):r['events'].append({'type':event.type,'detail':event.detail,'ns':time.monotonic_ns()})
  def run():
   try:rec.record_enable_context(ctx,cb)
   except BaseException as e:errors.append(repr(e));ready.set()
  thread=threading.Thread(target=run,daemon=True);thread.start()
  if not ready.wait(3) or errors:raise RuntimeError('record not ready: '+repr(errors))
  code=control.keysym_to_keycode(XK.string_to_keysym('b'));r['keycode']=code
  for _ in range(2):
   xtest.fake_input(control,X.KeyPress,code);control.sync();xtest.fake_input(control,X.KeyRelease,code);control.sync();time.sleep(.05)
  deadline=time.monotonic()+2
  while time.monotonic()<deadline:
   while target.pending_events():
    e=target.next_event()
    if e.type in (X.KeyPress,X.KeyRelease):r['target_events'].append({'type':e.type,'detail':e.detail,'ns':time.monotonic_ns()})
   if len(r['events'])>=4 and len(r['target_events'])>=4:break
   time.sleep(.01)
  control.record_disable_context(ctx);control.sync();thread.join(timeout=2)
  m=control.query_keymap();r['key_down_after']=bool(m[code//8]&(1<<(code%8)))
  expected=[(X.KeyPress,code),(X.KeyRelease,code)]*2
  r['checks']={'record_exact_sequence':[(e['type'],e['detail']) for e in r['events']]==expected,'target_exact_sequence':[(e['type'],e['detail']) for e in r['target_events']]==expected,'key_up':not r['key_down_after'],'record_thread_exited':not thread.is_alive(),'no_recorder_error':not errors}
  r['status']='PASS' if all(r['checks'].values()) else 'FAIL'
 except BaseException as e:r.update(status='FAIL',error_type=type(e).__name__,error=str(e),traceback=traceback.format_exc())
 finally:
  if control is not None and ctx is not None:
   try:control.record_disable_context(ctx);control.sync()
   except Exception:pass
  if thread is not None:thread.join(timeout=2)
  if rec is not None:
   try:rec.close()
   except Exception:pass
  if target is not None:target.close()
  if control is not None:control.close()
  if x is not None:
   if x.poll() is None:x.terminate()
   try:x.wait(timeout=3)
   except subprocess.TimeoutExpired:x.kill();x.wait()
   r['xvfb_exitcode']=x.returncode
  (ROOT/'result.json').write_text(json.dumps(r,indent=2)+'\n')
 print(json.dumps(r));return 0 if r['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
