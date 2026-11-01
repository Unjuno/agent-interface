import json,os,secrets,subprocess,sys,tempfile,time
from pathlib import Path
from Xlib import display
E=Path('/evidence')
def probe(disp,auth):
 env=dict(os.environ,DISPLAY=disp,XAUTHORITY=str(auth))
 code = """import json
from Xlib import display
try:
 d=display.Display();d.sync();d.close();print(json.dumps({'status':'connected'}))
except Exception as e:
 print(json.dumps({'status':'error','type':type(e).__name__,'message':str(e)}))
"""
 p=subprocess.run([sys.executable,'-c',code],env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=5,text=True)
 try: payload=json.loads(p.stdout)
 except (ValueError,TypeError):payload={'status':'unparseable'}
 # Retain only exception class and explicit protocol denial markers; no raw auth data.
 message=payload.pop('message','');payload['protocol_denial_marker']=('authorization' in message.lower() or 'authentication' in message.lower() or 'cookie' in message.lower());payload['exit']=p.returncode
 return payload
def run():
 with tempfile.TemporaryDirectory() as tmp:
  root=Path(tmp); good=root/'good';wrong=root/'wrong';good.touch();wrong.touch()
  # Create authority entries without exposing the generated cookies in output.
  for path in (good,wrong):subprocess.run(['xauth','-f',str(path),'add',':93','MIT-MAGIC-COOKIE-1',secrets.token_hex(16)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=True)
  results={}
  for mode in ('access_control_off','cookie_enforced'):
   args=['Xvfb',':93','-screen','0','640x480x24','-nolisten','tcp','-nolisten','unix']+(['-ac'] if mode=='access_control_off' else ['-auth',str(good)])
   p=subprocess.Popen(args,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
   try:
    end=time.monotonic()+4
    while time.monotonic()<end:
     if p.poll() is not None:raise RuntimeError('Xvfb exited')
     r=probe(':93',good)
     if r['status']=='connected':break
     time.sleep(.05)
    else:raise RuntimeError('authorized probe unavailable')
    results[mode]={'good':probe(':93',good),'wrong':probe(':93',wrong)}
   finally:
    if p.poll() is None:p.terminate();p.wait(timeout=3)
  checks={'noauth_wrong_accepted':results['access_control_off']['wrong']['status']=='connected','auth_good_accepted':results['cookie_enforced']['good']['status']=='connected','auth_wrong_rejected':results['cookie_enforced']['wrong']['status']=='error' and results['cookie_enforced']['wrong']['type']=='DisplayConnectionError' and results['cookie_enforced']['wrong']['protocol_denial_marker']}
  report={'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'results':results,'limits':'same container and UID; cookie secrecy not tested; no process generation fencing'};(E/'result.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report));return 0 if report['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(run())
