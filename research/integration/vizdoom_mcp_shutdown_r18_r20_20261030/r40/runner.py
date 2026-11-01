import json,os,secrets,signal,subprocess,time,tempfile
from pathlib import Path
from Xlib import X,XK,display
from Xlib.ext import xtest
E=Path('/evidence')
def state(pid):
 s=Path('/proc',str(pid),'stat').read_text();return s[s.rfind(')')+1:].split()[0]
def down(d,k):
 c=d.keysym_to_keycode(XK.string_to_keysym(k));m=d.query_keymap();return bool(m[c//8] & (1<<(c%8)))
def run():
 ps=[];fds=[];ds=[];r={'checks':{},'times':{}}
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
   old,fresh=ds;old_b=old.keysym_to_keycode(XK.string_to_keysym('b'));xtest.fake_input(old,X.KeyPress,detail=old_b,time=3000);old.flush();r['times']['old_b_queued']=time.monotonic_ns()
   signal.pidfd_send_signal(fds[0],signal.SIGSTOP);end=time.monotonic()+1
   while time.monotonic()<end and state(ps[0].pid) not in ('T','t'):time.sleep(.005)
   stopped=state(ps[0].pid) in ('T','t');signal.pidfd_send_signal(fds[0],signal.SIGKILL);ps[0].wait(timeout=2);r['times']['old_exit']=time.monotonic_ns()
   try:old.sync();old_error=None
   except Exception as e:old_error=type(e).__name__
   w=fresh.keysym_to_keycode(XK.string_to_keysym('w'));xtest.fake_input(fresh,X.KeyPress,detail=w);fresh.sync();wdown=down(fresh,'w');xtest.fake_input(fresh,X.KeyRelease,detail=w);fresh.sync();wup=not down(fresh,'w')
   wait=max(0,(r['times']['old_b_queued']+3_500_000_000-time.monotonic_ns())/1e9);time.sleep(wait);bup=not down(fresh,'b');r['times']['horizon_end']=time.monotonic_ns()
   r['checks']={'old_server_stopped':stopped,'old_exact_process_exited':ps[0].returncode is not None,'old_connection_failed':old_error is not None,'fresh_server_alive':ps[1].poll() is None,'fresh_w_down':wdown,'fresh_w_up':wup,'fresh_b_up_at_horizon':bup,'horizon_after_old_delay':r['times']['horizon_end']>=r['times']['old_b_queued']+3_000_000_000};r.update(status='PASS' if all(r['checks'].values()) else 'FAIL',old_error_type=old_error,old_exitcode=ps[0].returncode)
 except BaseException as e:r.update(status='FAIL',error_type=type(e).__name__,error=str(e))
 finally:
  for d in ds:
   try:d.close()
   except Exception:pass
  for p in ps:
   if p.poll() is None:p.terminate();p.wait(timeout=3)
  for fd in fds:os.close(fd)
 (E/'result.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r));return 0 if r['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(run())
