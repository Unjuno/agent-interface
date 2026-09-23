#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,os,subprocess,sys,time
from pathlib import Path
from odf.opendocument import OpenDocumentText
from odf.text import P
from Xlib import display
HERE=Path(__file__).resolve().parent
def wait_display(env,name):
 for _ in range(100):
  if subprocess.run(['xdpyinfo','-display',name],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0:return
  time.sleep(.04)
 raise RuntimeError('Xvfb not ready')
def find_writer(name,timeout=12):
 end=time.monotonic()+timeout
 while time.monotonic()<end:
  d=display.Display(name)
  def walk(w):
   try:kids=w.query_tree().children
   except:return None
   for c in kids:
    try:cls=c.get_wm_class()
    except:cls=None
    if cls and any('libreoffice-writer' in str(x).lower() for x in cls):return c.id
    z=walk(c)
    if z:return z
   return None
  f=walk(d.screen().root); d.close()
  if f:return f
  time.sleep(.05)
 raise RuntimeError('Writer window not found')
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--out',type=Path,required=True); ap.add_argument('--display',required=True); ap.add_argument('--pacing-ms',type=float,required=True); a=ap.parse_args(); a.out.mkdir(parents=True,exist_ok=False)
 odt=a.out/'task.odt'; doc=OpenDocumentText(); doc.text.addElement(P(text='old placeholder')); doc.save(str(odt)); input_sha=hashlib.sha256(odt.read_bytes()).hexdigest(); auth=a.out/'Xauthority'; auth.write_bytes(b''); env=os.environ.copy(); env.update({'DISPLAY':a.display,'XAUTHORITY':str(auth)}); os.environ.update({'DISPLAY':a.display,'XAUTHORITY':str(auth)})
 xv=subprocess.Popen(['Xvfb',a.display,'-screen','0','1024x768x24','-nolisten','tcp','-ac'],env=env,stdout=(a.out/'xvfb.stdout').open('w'),stderr=(a.out/'xvfb.stderr').open('w')); ob=lo=None
 try:
  wait_display(env,a.display); ob=subprocess.Popen(['openbox'],env=env,stdout=(a.out/'openbox.stdout').open('w'),stderr=(a.out/'openbox.stderr').open('w')); lo=subprocess.Popen(['libreoffice',f'-env:UserInstallation=file://{a.out}/profile','--nologo','--nodefault','--nofirststartwizard','--norestore',str(odt)],env=env,stdout=(a.out/'libreoffice.stdout').open('w'),stderr=(a.out/'libreoffice.stderr').open('w')); wid=find_writer(a.display); time.sleep(.5)
  child=env.copy(); child.update({k:os.environ[k] for k in ['AGENT_INTERFACE_PORTABLE_ORACLE','AGENT_INTERFACE_X11_BACKEND','AGENT_INTERFACE_OFFICE_V0']}); exdir=a.out/'execution'; r=subprocess.run([sys.executable,str(HERE/'experiment.py'),'--display',a.display,'--window-id',str(wid),'--pacing-ms',str(a.pacing_ms),'--out',str(exdir)],env=child,text=True,capture_output=True); (a.out/'executor.stdout').write_text(r.stdout); (a.out/'executor.stderr').write_text(r.stderr); (a.out/'executor.exitcode').write_text(str(r.returncode)+'\n'); time.sleep(.8); s=subprocess.run([sys.executable,str(HERE/'score_odt.py'),'--odt',str(odt),'--out',str(a.out/'score.json')],text=True,capture_output=True); (a.out/'scorer.stdout').write_text(s.stdout); (a.out/'scorer.stderr').write_text(s.stderr); (a.out/'scorer.exitcode').write_text(str(s.returncode)+'\n'); rep={'schema':'agent-interface/writer-x11-pacing-arm-v1','pacing_ms':a.pacing_ms,'window_id':wid,'input_sha256':input_sha,'output_sha256':hashlib.sha256(odt.read_bytes()).hexdigest(),'executor_exitcode':r.returncode,'scorer_exitcode':s.returncode,'passed':r.returncode==0 and s.returncode==0}; (a.out/'report.json').write_text(json.dumps(rep,indent=2)+'\n'); print(json.dumps(rep,indent=2)); return 0 if rep['passed'] else 1
 finally:
  if lo and lo.poll() is None: lo.terminate()
  if lo:
   try:lo.wait(timeout=2)
   except:lo.kill()
  if ob and ob.poll() is None: ob.terminate()
  xv.terminate()
if __name__=='__main__': raise SystemExit(main())
