#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,os,subprocess,sys,time
from pathlib import Path
from Xlib import display
HERE=Path(__file__).resolve().parent
def wait_display(env,name):
 for _ in range(100):
  if subprocess.run(['xdpyinfo','-display',name],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0:return
  time.sleep(.04)
 raise RuntimeError('display')
def find_window(name,kind,timeout=12):
 end=time.monotonic()+timeout
 while time.monotonic()<end:
  d=display.Display(name)
  def walk(w):
   try:k=w.query_tree().children
   except:return None
   for c in k:
    try:cl=c.get_wm_class()
    except:cl=None
    needle='libreoffice-writer' if kind=='writer' else 'libreoffice-calc'
    if cl and any(needle in str(x).lower() for x in cl):return c.id
    z=walk(c)
    if z:return z
  z=walk(d.screen().root);d.close()
  if z:return z
  time.sleep(.05)
 raise RuntimeError('window')
def selection_owner(name):
 d=display.Display(name);o=d.get_selection_owner(d.intern_atom('CLIPBOARD'));i=getattr(o,'id',None);d.close();return i
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--app',choices=['writer','calc'],required=True);ap.add_argument('--display',required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False);auth=a.out/'Xauthority';auth.write_bytes(b'');env=os.environ.copy();env.update({'DISPLAY':a.display,'XAUTHORITY':str(auth)});os.environ.update({'DISPLAY':a.display,'XAUTHORITY':str(auth)})
 if a.app=='writer':
  from odf.opendocument import OpenDocumentText
  from odf.text import P
  art=a.out/'task.odt';doc=OpenDocumentText();doc.text.addElement(P(text='old placeholder'));doc.save(str(art))
 else:
  import openpyxl
  art=a.out/'task.xlsx';wb=openpyxl.Workbook();wb.active['A1']='old placeholder';wb.save(art)
 inp=hashlib.sha256(art.read_bytes()).hexdigest();xv=subprocess.Popen(['Xvfb',a.display,'-screen','0','1024x768x24','-nolisten','tcp','-ac'],env=env,stdout=(a.out/'xvfb.stdout').open('w'),stderr=(a.out/'xvfb.stderr').open('w'));ob=owner=lo=None
 try:
  wait_display(env,a.display);ob=subprocess.Popen(['openbox'],env=env,stdout=(a.out/'openbox.stdout').open('w'),stderr=(a.out/'openbox.stderr').open('w'))
  ready=a.out/'clipboard-owner.json';owner=subprocess.Popen([sys.executable,str(HERE/'clipboard_owner.py'),'--display',a.display,'--text','PREVIOUS-αβ','--ready',str(ready)],env=env,stdout=(a.out/'owner.stdout').open('w'),stderr=(a.out/'owner.stderr').open('w'))
  for _ in range(100):
   if ready.exists():break
   time.sleep(.03)
  owner_before=selection_owner(a.display)
  profile=a.out/'profile';lo=subprocess.Popen(['libreoffice',f'-env:UserInstallation=file://{profile}','--nologo','--nodefault','--nofirststartwizard','--norestore',str(art)],env=env,stdout=(a.out/'libreoffice.stdout').open('w'),stderr=(a.out/'libreoffice.stderr').open('w'));wid=find_window(a.display,a.app);time.sleep(.5)
  child=env.copy();child['AGENT_INTERFACE_PORTABLE_ORACLE']=os.environ['AGENT_INTERFACE_PORTABLE_ORACLE'];exdir=a.out/'execution';e=subprocess.run([sys.executable,str(HERE/'executor.py'),'--display',a.display,'--window-id',str(wid),'--app',a.app,'--out',str(exdir)],env=child,text=True,capture_output=True);(a.out/'executor.stdout').write_text(e.stdout);(a.out/'executor.stderr').write_text(e.stderr);(a.out/'executor.exitcode').write_text(str(e.returncode)+'\n');time.sleep(.6)
  s=subprocess.run([sys.executable,str(HERE/'score.py'),'--app',a.app,'--artifact',str(art),'--out',str(a.out/'score.json')],text=True,capture_output=True);(a.out/'scorer.stdout').write_text(s.stdout);(a.out/'scorer.stderr').write_text(s.stderr);(a.out/'scorer.exitcode').write_text(str(s.returncode)+'\n')
  ex=json.loads((exdir/'execution.json').read_text());score=json.loads((a.out/'score.json').read_text());rep={'schema':'agent-interface/x11-unicode-clipboard-arm-v1','app':a.app,'owner_before':owner_before,'input_sha256':inp,'output_sha256':hashlib.sha256(art.read_bytes()).hexdigest(),'executor_exitcode':e.returncode,'scorer_exitcode':s.returncode,'semantic_exact':score['exact'],'transport_pass':ex['passed_transport'],'owner_identity_restored':ex['clipboard']['owner_identity_restored'],'owner_reclaimed_after_close':ex['clipboard']['owner_reclaimed_after_close'],'passed_scoped':e.returncode==0 and s.returncode==0 and score['exact'] and ex['passed_transport']};(a.out/'report.json').write_text(json.dumps(rep,indent=2)+'\n');print(json.dumps(rep,indent=2));return 0 if rep['passed_scoped'] else 1
 finally:
  if lo and lo.poll() is None:lo.terminate()
  if lo:
   try:lo.wait(2)
   except:lo.kill()
  if owner and owner.poll() is None:owner.terminate()
  if ob and ob.poll() is None:ob.terminate()
  xv.terminate()
if __name__=='__main__':raise SystemExit(main())
