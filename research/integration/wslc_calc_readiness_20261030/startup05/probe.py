import json,os,signal,subprocess,tempfile,time
from pathlib import Path
from Xlib import display
E=Path('/out');x=None;app=None;conn=None;result={}
try:
 x=subprocess.Popen(['Xvfb',':90','-screen','0','1024x768x24','-nolisten','tcp','-ac'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 os.environ['DISPLAY']=':90';deadline=time.monotonic()+5
 while time.monotonic()<deadline:
  if x.poll() is not None:raise RuntimeError('Xvfb exited')
  try:conn=display.Display(':90');break
  except Exception:time.sleep(.05)
 if conn is None:raise RuntimeError('Xvfb unavailable')
 with tempfile.TemporaryDirectory() as td, (E/'calc-stdout.bin').open('wb') as out, (E/'calc-stderr.bin').open('wb') as err:
  app=subprocess.Popen(['soffice','-env:UserInstallation=file://'+td+'/profile','--norestore','--nodefault','--calc'],cwd=td,stdout=out,stderr=err,start_new_session=True)
  started=time.monotonic();windows=[]
  while time.monotonic()-started<15:
   windows=[]
   for w in conn.screen().root.query_tree().children:
    try:windows.append({'title':w.get_wm_name(),'map_state':w.get_attributes().map_state})
    except Exception:pass
   if any(i['title'] and 'calc' in i['title'].lower() and i['map_state']==2 for i in windows):break
   if app.poll() is not None:break
   time.sleep(.05)
  result={'status':'mapped' if any(i['title'] and 'calc' in i['title'].lower() and i['map_state']==2 for i in windows) else 'not_mapped','windows':windows,'launcher_returncode':app.poll(),'elapsed_s':time.monotonic()-started}
  if app.poll() is None:
   os.killpg(app.pid,signal.SIGTERM)
   try:app.wait(timeout=3)
   except subprocess.TimeoutExpired:os.killpg(app.pid,signal.SIGKILL);app.wait(timeout=3)
except BaseException as e:result={'status':'error','error_type':type(e).__name__,'error':str(e)}
finally:
 if app is not None and app.poll() is None:os.killpg(app.pid,signal.SIGKILL);app.wait(timeout=3)
 if conn is not None:conn.close()
 if x is not None and x.poll() is None:x.terminate();x.wait(timeout=3)
 (E/'probe-result.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(result));raise SystemExit(0 if result.get('status')=='mapped' else 1)
