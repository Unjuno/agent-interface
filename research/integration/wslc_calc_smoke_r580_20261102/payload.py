import hashlib, json, os, signal, subprocess, time, traceback
from pathlib import Path
from Xlib import X, display
from PIL import Image
report={'status':'UNKNOWN','started_ns':time.monotonic_ns()}; actors=[]; d=None
os.environ.update(DISPLAY=':153', HOME='/tmp', SAL_USE_VCLPLUGIN='gen')
def alarm(*_):raise TimeoutError('payload deadline')
signal.signal(signal.SIGALRM,alarm);signal.alarm(25)
try:
 def spawn(args):
  p=subprocess.Popen(args,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);actors.append(p);return p
 spawn(['Xvfb',':153','-screen','0','1280x800x24','-nolisten','tcp','-ac'])
 until=time.monotonic()+8
 while True:
  try:d=display.Display(':153');break
  except Exception:
   if time.monotonic()>=until:raise TimeoutError('Xvfb unavailable')
   time.sleep(.05)
 spawn(['openbox','--sm-disable'])
 lo=spawn(['libreoffice','-env:UserInstallation=file:///tmp/calc-smoke-profile','--calc','--nologo','--norestore','--nofirststartwizard'])
 def walk(w,depth=0):
  out=[]
  if depth>6:return out
  for child in w.query_tree().children:
   try:
    title=child.get_wm_name();title=title.decode(errors='replace') if isinstance(title,bytes) else str(title or '')
    if 'calc' in title.lower() and child.get_attributes().map_state==X.IsViewable:out.append({'id':child.id,'title':title})
    out.extend(walk(child,depth+1))
   except Exception:pass
  return out
 until=time.monotonic()+15
 while True:
  found=walk(d.screen().root)
  if len(found)==1:break
  if len(found)>1:raise RuntimeError('ambiguous Calc window')
  if lo.poll() is not None:raise RuntimeError('Calc launcher exited')
  if time.monotonic()>=until:raise TimeoutError('Calc window unavailable')
  time.sleep(.1)
 time.sleep(.5); image=d.screen().root.get_image(0,0,1280,800,X.ZPixmap,0xffffffff)
 im=Image.frombytes('RGB',(1280,800),image.data,'raw','BGRX');im.save('/tmp/calc-smoke.png')
 report.update(status='window_observed',window=found[0],screenshot_sha256=hashlib.sha256(Path('/tmp/calc-smoke.png').read_bytes()).hexdigest())
except BaseException as e:
 report.update(error_type=type(e).__name__,error=str(e))
finally:
 signal.alarm(0)
 if d is not None:d.close()
 for p in reversed(actors):
  if p.poll() is None:
   p.terminate()
   try:p.wait(timeout=2)
   except subprocess.TimeoutExpired:p.kill();p.wait(timeout=2)
 report['ended_ns']=time.monotonic_ns()
 Path('/tmp/calc-smoke.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
raise SystemExit(0 if report['status']=='window_observed' else 1)
