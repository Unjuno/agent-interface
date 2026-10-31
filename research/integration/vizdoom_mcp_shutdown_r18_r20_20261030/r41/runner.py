import json,os,secrets,signal,subprocess,time,tempfile,threading
from pathlib import Path
from Xlib import X,XK,display
from Xlib.ext import xtest,record
from Xlib.protocol import rq
E=Path('/evidence')
def state(pid):
 s=Path('/proc',str(pid),'stat').read_text();return s[s.rfind(')')+1:].split()[0]
def down(d,k):
 c=d.keysym_to_keycode(XK.string_to_keysym(k));m=d.query_keymap();return bool(m[c//8] & (1<<(c%8)))
def run():
 ps=[];fds=[];ds=[];rc=None;rd=None;ctx=None;thread=None;r={'checks':{},'times':{}}
 try:
  with tempfile.TemporaryDirectory() as tmp:
   auth=Path(tmp)/'auth';auth.touch()
   for n in (93,94):subprocess.run(['xauth','-f',str(auth),'add',':'+str(n),'MIT-MAGIC-COOKIE-1',secrets.token_hex(16)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=True)
   os.environ['XAUTHORITY']=str(auth)
   for n in (93,94):
    p=subprocess.Popen(['Xvfb',':'+str(n),'-screen','0','640x480x24','-nolisten','tcp','-nolisten','unix','-auth',str(auth)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);ps.append(p);fds.append(os.pidfd_open(p.pid,0));d=None;deadline=time.monotonic()+4
    while time.monotonic()<deadline:
     if p.poll() is not None:raise RuntimeError('Xvfb exited')
     try:d=display.Display(':'+str(n));break
     except Exception:time.sleep(.03)
    if d is None:raise RuntimeError('display unavailable')
    ds.append(d)
   rc=display.Display(':94');rd=display.Display(':94');events=[];errors=[];ready=threading.Event()
   ctx=rd.record_create_context(0,[record.AllClients],[{'core_requests':(0,0),'core_replies':(0,0),'ext_requests':(0,0,0,0),'ext_replies':(0,0,0,0),'delivered_events':(0,0),'device_events':(X.KeyPress,X.KeyRelease),'errors':(0,0),'client_started':False,'client_died':False}])
   def callback(reply):
    if reply.category==record.StartOfData:ready.set();return
    if reply.category!=record.FromServer or reply.client_swapped:return
    data=reply.data
    while data:
     event,data=rq.EventField(None).parse_binary_value(data,rd.display,None,None)
     if event.type in (X.KeyPress,X.KeyRelease):events.append({'type':event.type,'detail':event.detail,'ns':time.monotonic_ns()})
   def record_events():
    try:rd.record_enable_context(ctx,callback)
    except BaseException as e:errors.append(type(e).__name__);ready.set()
   thread=threading.Thread(target=record_events,daemon=True);thread.start()
   if not ready.wait(3) or errors:raise RuntimeError('recorder unavailable')
   r['times']['record_ready']=time.monotonic_ns()
   old,fresh=ds;old_b=old.keysym_to_keycode(XK.string_to_keysym('b'));xtest.fake_input(old,X.KeyPress,detail=old_b,time=3000);old.flush();r['times']['old_b_queued']=time.monotonic_ns()
   signal.pidfd_send_signal(fds[0],signal.SIGSTOP);end=time.monotonic()+1
   while time.monotonic()<end and state(ps[0].pid) not in ('T','t'):time.sleep(.005)
   stopped=state(ps[0].pid) in ('T','t');signal.pidfd_send_signal(fds[0],signal.SIGKILL);ps[0].wait(timeout=2);r['times']['old_exit']=time.monotonic_ns()
   try:old.sync();old_error=None
   except Exception as e:old_error=type(e).__name__
   w=fresh.keysym_to_keycode(XK.string_to_keysym('w'));xtest.fake_input(fresh,X.KeyPress,detail=w);fresh.sync();wdown=down(fresh,'w');xtest.fake_input(fresh,X.KeyRelease,detail=w);fresh.sync();wup=not down(fresh,'w')
   wait=max(0,(r['times']['old_b_queued']+3_500_000_000-time.monotonic_ns())/1e9);time.sleep(wait);bup=not down(fresh,'b');r['times']['horizon_end']=time.monotonic_ns()
   fb=fresh.keysym_to_keycode(XK.string_to_keysym('b'));xtest.fake_input(fresh,X.KeyPress,detail=fb);xtest.fake_input(fresh,X.KeyRelease,detail=fb);fresh.sync();time.sleep(.3)
   rc.record_disable_context(ctx);rc.sync();thread.join(timeout=2);r['events']=events;r['recorder_errors']=errors;r['recorder_thread_alive']=thread.is_alive()
   r['checks']={'old_server_stopped':stopped,'old_exact_process_exited':ps[0].returncode is not None,'old_connection_failed':old_error is not None,'fresh_server_alive':ps[1].poll() is None,'fresh_w_down':wdown,'fresh_w_up':wup,'fresh_b_up_at_horizon':bup,'horizon_after_old_delay':r['times']['horizon_end']>=r['times']['old_b_queued']+3_000_000_000,'record_covers_horizon':r['times']['record_ready']<r['times']['old_b_queued'] and not errors and not thread.is_alive(),'no_fresh_b_before_horizon':not any(e['type']==X.KeyPress and e['detail']==fb and e['ns']<r['times']['horizon_end'] for e in events),'positive_b_after_horizon':any(e['type']==X.KeyPress and e['detail']==fb and e['ns']>=r['times']['horizon_end'] for e in events)};r.update(status='PASS' if all(r['checks'].values()) else 'FAIL',old_error_type=old_error,old_exitcode=ps[0].returncode)
 except BaseException as e:r.update(status='FAIL',error_type=type(e).__name__,error=str(e))
 finally:
  if rc is not None and ctx is not None and thread is not None and thread.is_alive():
   try:rc.record_disable_context(ctx);rc.sync();thread.join(timeout=2)
   except Exception:pass
  if rd is not None:rd.close()
  if rc is not None:rc.close()
  for d in ds:
   try:d.close()
   except Exception:pass
  for p in ps:
   if p.poll() is None:p.terminate();p.wait(timeout=3)
  for fd in fds:os.close(fd)
 (E/'result.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r));return 0 if r['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(run())
