from __future__ import annotations
import argparse,json,os,subprocess,sys,time,hashlib
from pathlib import Path
from PIL import ImageGrab
from Xlib import X,display
from Xlib.ext import xtest
RADIUS=5;MAX_PIXEL_ERROR=8.0
p=argparse.ArgumentParser();p.add_argument('--case-id',required=True);p.add_argument('--state',choices=['stable','swap'],required=True);p.add_argument('--policy',choices=['no_revalidation','revalidate'],required=True);p.add_argument('--display-num',type=int,required=True);p.add_argument('--out',required=True)
a=p.parse_args();out=Path(a.out);out.mkdir(parents=True,exist_ok=False)
name=f':{a.display_num}';xauth=out/'empty.Xauthority';xauth.write_bytes(b'');env=os.environ.copy();env['DISPLAY']=name;env['XAUTHORITY']=str(xauth);os.environ.update({'DISPLAY':name,'XAUTHORITY':str(xauth)})
xvlog=(out/'xvfb.log').open('wb');xv=subprocess.Popen(['Xvfb',name,'-screen','0','640x480x24','-ac'],stdout=xvlog,stderr=subprocess.STDOUT,env=env)
def wait_display():
 end=time.monotonic()+3;last=None
 while time.monotonic()<end:
  try:return display.Display(name)
  except Exception as exc:last=exc;time.sleep(.02)
 raise RuntimeError(repr(last))
def patchdiff(a,b,x,y):
 r=RADIUS;ab=a.crop((x-r,y-r,x+r+1,y+r+1)).tobytes();bb=b.crop((x-r,y-r,x+r+1,y+r+1)).tobytes();return max(abs(q-w) for q,w in zip(ab,bb))
def rgbsha(im):return hashlib.sha256(im.convert('RGB').tobytes()).hexdigest()
d=wait_display();control=out/'control';ready=out/'ready.json';mutated=out/'mutated.json';events=out/'events.jsonl';ao=(out/'app.stdout').open('wb');ae=(out/'app.stderr').open('wb')
app=subprocess.Popen([sys.executable,str(Path(__file__).with_name('app.py')),'--control',str(control),'--ready',str(ready),'--mutated',str(mutated),'--events',str(events)],env=env,stdout=ao,stderr=ae)
try:
 end=time.monotonic()+4
 while not ready.exists() and time.monotonic()<end:
  if app.poll() is not None:raise RuntimeError('app exited')
  time.sleep(.01)
 if not ready.exists():raise RuntimeError('ready timeout')
 info=json.loads(ready.read_text());x,y=info['A'];time.sleep(.05)
 ref=ImageGrab.grab(xdisplay=name).convert('RGB');ref.save(out/'reference.png');time.sleep(.03);pre=ImageGrab.grab(xdisplay=name).convert('RGB');pre.save(out/'pre.png')
 initial_diff=patchdiff(ref,pre,x,y);gated_ns=time.perf_counter_ns()
 if initial_diff>MAX_PIXEL_ERROR:raise RuntimeError('initial gate false')
 mutation=None
 if a.state=='swap':
  control.write_text('swap');end=time.monotonic()+3
  while not mutated.exists() and time.monotonic()<end:time.sleep(.005)
  if not mutated.exists():raise RuntimeError('mutation timeout')
  mutation=json.loads(mutated.read_text())
 revalidation=None;disposition='NOT_REVALIDATED';input_allowed=True
 if a.policy=='revalidate':
  rs=time.perf_counter_ns();cur=ImageGrab.grab(xdisplay=name).convert('RGB');rd=time.perf_counter_ns();cur.save(out/'preinput.png');d2=patchdiff(pre,cur,x,y);revalidation={'capture_started_ns':rs,'capture_done_ns':rd,'patch_diff':d2,'rgb_sha256':rgbsha(cur)}
  input_allowed=d2<=MAX_PIXEL_ERROR;disposition='CURRENT_TARGET' if input_allowed else 'STALE_TARGET'
 click_started=None;click_done=None
 if input_allowed:
  click_started=time.perf_counter_ns();xtest.fake_input(d,X.MotionNotify,x=x,y=y);d.sync();xtest.fake_input(d,X.ButtonPress,1);d.sync();xtest.fake_input(d,X.ButtonRelease,1);d.sync();click_done=time.perf_counter_ns()
 time.sleep(.08);final=ImageGrab.grab(xdisplay=name).convert('RGB');final.save(out/'final.png');rows=[json.loads(s) for s in events.read_text().splitlines() if s.strip()] if events.exists() else [];clicks=[z for z in rows if z['event']=='click'];mask=d.screen().root.query_pointer().mask
 result={'case_id':a.case_id,'state':a.state,'policy':a.policy,'gate_contract':{'radius':5,'max_pixel_error_le':8.0},'initial_gate_diff':initial_diff,'initial_gate_eligible':True,'gated_ns':gated_ns,'mutation':mutation,'revalidation':revalidation,'disposition':disposition,'input_allowed':input_allowed,'click_started_ns':click_started,'click_done_ns':click_done,'events':rows,'clicks':clicks,'button1_down_terminal':bool(mask&X.Button1Mask),'pre_rgb_sha256':rgbsha(pre),'final_rgb_sha256':rgbsha(final),'final_patch_diff_from_gated':patchdiff(pre,final,x,y)}
 (out/'result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'state':a.state,'policy':a.policy,'disposition':disposition,'clicks':len(clicks),'role':clicks[0]['role'] if clicks else None,'reval_diff':(revalidation or {}).get('patch_diff')},sort_keys=True))
finally:
 if app.poll() is None:app.terminate()
 try:app.wait(timeout=1)
 except:app.kill()
 d.close();xv.terminate()
 try:xv.wait(timeout=1)
 except:xv.kill()
 ao.close();ae.close();xvlog.close()
