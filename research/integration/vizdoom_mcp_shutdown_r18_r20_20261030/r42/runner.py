import json,os,secrets,signal,subprocess,time,tempfile,threading
from pathlib import Path
from Xlib import X,XK,display
from Xlib.ext import xtest,record
from Xlib.protocol import rq
E=Path('/evidence')
def state(pid):
 s=Path('/proc',str(pid),'stat').read_text();return s[s.rfind(')')+1:].split()[0]
def start(auth):
 p=subprocess.Popen(['Xvfb',':93','-screen','0','640x480x24','-nolisten','tcp','-nolisten','unix','-auth',str(auth)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);fd=os.pidfd_open(p.pid,0);os.environ['XAUTHORITY']=str(auth);end=time.monotonic()+4
 while time.monotonic()<end:
  if p.poll() is not None:raise RuntimeError('Xvfb exited before ready')
  try:return p,fd,display.Display(':93')
  except Exception:time.sleep(.03)
 raise RuntimeError('Xvfb unavailable')
def run():
 ps=[];fds=[];ds=[];rc=None;rd=None;ctx=None;thread=None;r={'checks':{},'times':{}}
 try:
  with tempfile.TemporaryDirectory() as tmp:
   a=Path(tmp)/'old';b=Path(tmp)/'new';a.touch();b.touch()
   for f in (a,b):subprocess.run(['xauth','-f',str(f),'add',':93','MIT-MAGIC-COOKIE-1',secrets.token_hex(16)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=True)
   oldp,oldfd,old=start(a);ps.append(oldp);fds.append(oldfd);ds.append(old);key=old.keysym_to_keycode(XK.string_to_keysym('b'));xtest.fake_input(old,X.KeyPress,detail=key,time=3000);old.flush();r['times']['old_queued']=time.monotonic_ns()
   signal.pidfd_send_signal(oldfd,signal.SIGSTOP);end=time.monotonic()+1
   while time.monotonic()<end and state(oldp.pid) not in ('T','t'):time.sleep(.005)
   stopped=state(oldp.pid) in ('T','t');signal.pidfd_send_signal(oldfd,signal.SIGKILL);oldp.wait(timeout=2);r['times']['old_exit']=time.monotonic_ns()
   newp,newfd,fresh=start(b);ps.append(newp);fds.append(newfd);ds.append(fresh);r['times']['fresh_started']=time.monotonic_ns()
   try:old.sync();old_error=None
   except Exception as e:old_error=type(e).__name__
   os.environ['XAUTHORITY']=str(a)
   try:unauthorized=display.Display(':93');unauthorized.close();old_auth_denied=False;auth_error=None
   except Exception as e:old_auth_denied=True;auth_error=type(e).__name__
   os.environ['XAUTHORITY']=str(b);rc=display.Display(':93');rd=display.Display(':93');events=[];errors=[];ready=threading.Event();ctx=rd.record_create_context(0,[record.AllClients],[{'core_requests':(0,0),'core_replies':(0,0),'ext_requests':(0,0,0,0),'ext_replies':(0,0,0,0),'delivered_events':(0,0),'device_events':(X.KeyPress,X.KeyRelease),'errors':(0,0),'client_started':False,'client_died':False}])
   def callback(reply):
    if reply.category==record.StartOfData:ready.set();return
    if reply.category!=record.FromServer or reply.client_swapped:return
    data=reply.data
    while data:
     event,data=rq.EventField(None).parse_binary_value(data,rd.display,None,None)
     if event.type in (X.KeyPress,X.KeyRelease):events.append({'type':event.type,'detail':event.detail,'ns':time.monotonic_ns()})
   def run_rec():
    try:rd.record_enable_context(ctx,callback)
    except BaseException as e:errors.append(type(e).__name__);ready.set()
   thread=threading.Thread(target=run_rec,daemon=True);thread.start()
   if not ready.wait(3) or errors:raise RuntimeError('record unavailable')
   r['times']['recorder_ready']=time.monotonic_ns();w=fresh.keysym_to_keycode(XK.string_to_keysym('w'));xtest.fake_input(fresh,X.KeyPress,detail=w);xtest.fake_input(fresh,X.KeyRelease,detail=w);fresh.sync()
   time.sleep(max(0,(r['times']['old_queued']+3_500_000_000-time.monotonic_ns())/1e9));r['times']['horizon_end']=time.monotonic_ns();nb=fresh.keysym_to_keycode(XK.string_to_keysym('b'));xtest.fake_input(fresh,X.KeyPress,detail=nb);xtest.fake_input(fresh,X.KeyRelease,detail=nb);fresh.sync();time.sleep(.3);rc.record_disable_context(ctx);rc.sync();thread.join(timeout=2)
   r['events']=events;r['checks']={'old_stopped':stopped,'old_exited':oldp.returncode is not None,'distinct_pid':oldp.pid!=newp.pid,'new_same_display_before_delay':r['times']['fresh_started']<r['times']['old_queued']+3_000_000_000,'old_connection_closed':old_error=='ConnectionClosedError','old_cookie_denied':old_auth_denied and auth_error=='DisplayConnectionError','recorder_covers_old_delay':r['times']['recorder_ready']<r['times']['old_queued']+3_000_000_000<r['times']['horizon_end'] and not errors and not thread.is_alive(),'new_w_press_release':all(any(e['type']==t and e['detail']==w for e in events) for t in (X.KeyPress,X.KeyRelease)),'no_b_before_horizon':not any(e['type']==X.KeyPress and e['detail']==nb and e['ns']<r['times']['horizon_end'] for e in events),'b_positive_after':any(e['type']==X.KeyPress and e['detail']==nb and e['ns']>=r['times']['horizon_end'] for e in events)};r.update(status='PASS' if all(r['checks'].values()) else 'FAIL',old_error=old_error,old_auth_error=auth_error)
 except BaseException as e:r.update(status='FAIL',error_type=type(e).__name__,error=str(e))
 finally:
  if rc is not None and ctx is not None and thread is not None and thread.is_alive():
   try:rc.record_disable_context(ctx);rc.sync();thread.join(timeout=2)
   except Exception:pass
  for d in [rd,rc]+ds:
   if d is not None:
    try:d.close()
    except Exception:pass
  for p in ps:
   if p.poll() is None:p.terminate();p.wait(timeout=3)
  for fd in fds:os.close(fd)
 (E/'result.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r));return 0 if r['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(run())
