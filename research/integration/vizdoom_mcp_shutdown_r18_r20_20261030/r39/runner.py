import json,os,secrets,subprocess,sys,tempfile,time
from pathlib import Path
from Xlib import X,XK,display
from Xlib.ext import xtest
E=Path('/evidence')
def down(d,k):
 c=d.keysym_to_keycode(XK.string_to_keysym(k));m=d.query_keymap();return bool(m[c//8] & (1<<(c%8)))
def probe(auth):
 env=dict(os.environ,DISPLAY=':93',XAUTHORITY=str(auth))
 code="""import json
from Xlib import display
try:
 d=display.Display();d.sync();d.close();print(json.dumps({'status':'connected'}))
except Exception as e:
 m=str(e).lower();print(json.dumps({'status':'error','type':type(e).__name__,'denial_marker':any(x in m for x in ('authorization','authentication','cookie'))}))
"""
 p=subprocess.run([sys.executable,'-c',code],env=env,capture_output=True,text=True,timeout=5)
 try:return json.loads(p.stdout)
 except ValueError:return {'status':'unparseable','exit':p.returncode}
def run():
 with tempfile.TemporaryDirectory() as tmp:
  auth=Path(tmp)/'auth';auth.touch();subprocess.run(['xauth','-f',str(auth),'add',':93','MIT-MAGIC-COOKIE-1',secrets.token_hex(16)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=True)
  p=subprocess.Popen(['Xvfb',':93','-screen','0','640x480x24','-nolisten','tcp','-nolisten','unix','-auth',str(auth)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);old=None;monitor=None
  try:
   end=time.monotonic()+4
   while time.monotonic()<end:
    if p.poll() is not None:raise RuntimeError('Xvfb exited')
    if probe(auth).get('status')=='connected':break
    time.sleep(.05)
   else:raise RuntimeError('authorized probe unavailable')
   os.environ['DISPLAY']=':93';os.environ['XAUTHORITY']=str(auth);old=display.Display(':93');monitor=display.Display(':93');old.sync();monitor.sync()
   auth.unlink();new=probe(auth);code=old.keysym_to_keycode(XK.string_to_keysym('w'));xtest.fake_input(old,X.KeyPress,detail=code);old.sync();observed_down=down(monitor,'w');xtest.fake_input(old,X.KeyRelease,detail=code);old.sync();observed_up=not down(monitor,'w')
   checks={'new_connection_refused':new.get('status')=='error' and new.get('type')=='DisplayConnectionError' and new.get('denial_marker') is True,'existing_connection_sends_w':observed_down,'existing_connection_releases_w':observed_up}
   report={'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'new_probe':new,'old_connection_action':'W press/release','scope':'pre-existing authorized X11 connection after client authority file removed; no server-side revocation attempted'};(E/'result.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report));return 0 if report['status']=='PASS' else 1
  finally:
   if old is not None:old.close()
   if monitor is not None:monitor.close()
   if p.poll() is None:p.terminate();p.wait(timeout=3)
if __name__=='__main__':raise SystemExit(run())
