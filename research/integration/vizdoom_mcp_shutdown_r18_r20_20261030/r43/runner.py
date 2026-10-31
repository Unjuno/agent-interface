import json,os,secrets,signal,subprocess,tempfile,time
from pathlib import Path
from Xlib import X,XK,display
from Xlib.ext import xtest
E=Path('/evidence')
def state(pid):
 s=Path('/proc',str(pid),'stat').read_text();return s[s.rfind(')')+1:].split()[0]
def down(d,k):
 c=d.keysym_to_keycode(XK.string_to_keysym(k));m=d.query_keymap();return bool(m[c//8] & (1<<(c%8)))
def run():
 r={'checks':{},'times':{}};old=None;new=None;fd=None;d=None
 try:
  with tempfile.TemporaryDirectory() as tmp:
   auth=Path(tmp)/'auth';auth.touch();subprocess.run(['xauth','-f',str(auth),'add',':93','MIT-MAGIC-COOKIE-1',secrets.token_hex(16)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=True);os.environ['XAUTHORITY']=str(auth)
   args=['Xvfb',':93','-screen','0','640x480x24','-nolisten','tcp','-nolisten','unix','-auth',str(auth)];old=subprocess.Popen(args,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);fd=os.pidfd_open(old.pid,0);end=time.monotonic()+4
   while time.monotonic()<end:
    if old.poll() is not None:raise RuntimeError('old server exited')
    try:d=display.Display(':93');break
    except Exception:time.sleep(.03)
   if d is None:raise RuntimeError('old server unavailable')
   signal.pidfd_send_signal(fd,signal.SIGSTOP);end=time.monotonic()+1
   while time.monotonic()<end and state(old.pid) not in ('T','t'):time.sleep(.005)
   r['old_stopped']=state(old.pid) in ('T','t');r['times']['old_stopped']=time.monotonic_ns()
   new=subprocess.Popen(args,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);new_exit=new.wait(timeout=3);r['times']['new_exited']=time.monotonic_ns();old_still_stopped=old.poll() is None and state(old.pid) in ('T','t')
   signal.pidfd_send_signal(fd,signal.SIGCONT);r['times']['old_resumed']=time.monotonic_ns();key=d.keysym_to_keycode(XK.string_to_keysym('w'));xtest.fake_input(d,X.KeyPress,detail=key);d.sync();wdown=down(d,'w');xtest.fake_input(d,X.KeyRelease,detail=key);d.sync();wup=not down(d,'w')
   r['checks']={'old_stopped':r['old_stopped'],'replacement_rejected':new_exit!=0,'old_alive_stopped_after_rejection':old_still_stopped,'old_connection_w_down':wdown,'old_connection_w_up':wup};r.update(status='PASS' if all(r['checks'].values()) else 'FAIL',new_exitcode=new_exit)
 except BaseException as e:r.update(status='FAIL',error_type=type(e).__name__,error=str(e))
 finally:
  if old is not None and old.poll() is None and fd is not None:
   try:signal.pidfd_send_signal(fd,signal.SIGCONT)
   except ProcessLookupError:pass
  if d is not None:
   try:d.close()
   except Exception:pass
  for p in (new,old):
   if p is not None and p.poll() is None:p.terminate();p.wait(timeout=3)
  if fd is not None:os.close(fd)
 (E/'result.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r));return 0 if r['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(run())
