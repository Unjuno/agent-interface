from __future__ import annotations
import argparse,json,os,subprocess,time
from pathlib import Path
from odf.opendocument import OpenDocumentText
from odf.text import P
from Xlib import X,XK,display
from Xlib.ext import xtest
from binding_base import uno,bind_document,active_focus
HERE=Path(__file__).resolve().parent
DESIRED='bookkeeperoffice'; A0='book'; B0='bookk'; SUFFIX='keeperoffice'; MAX_AGE_NS=500_000_000

def mkdoc(path,text):
 d=OpenDocumentText();d.text.addElement(P(text=text));d.save(str(path))
def wait_display(env,name):
 for _ in range(120):
  if subprocess.run(['xdpyinfo','-display',name],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0:return
  time.sleep(.03)
 raise RuntimeError('display unavailable')
def wait_docs(env,pipe):
 end=time.monotonic()+7
 while time.monotonic()<end:
  try:
   rows=uno(env,HERE/'uno_helper.py',pipe,'list')
   if len(rows)>=2:return rows
  except Exception:pass
  time.sleep(.05)
 raise RuntimeError('docs unavailable')
def row(rows,url):
 m=[r for r in rows if r['url']==url]
 if len(m)!=1:raise RuntimeError('row mismatch')
 return m[0]
def keycode(d,name):
 c=d.keysym_to_keycode(XK.string_to_keysym(name))
 if not c:raise RuntimeError(name)
 return c
def send(d,c,down):xtest.fake_input(d,X.KeyPress if down else X.KeyRelease,c);d.sync()
def chord(d,names):
 cs=[keycode(d,n) for n in names]
 for c in cs:send(d,c,True)
 for c in reversed(cs):send(d,c,False)
def text(d,s):
 for ch in s:
  c=keycode(d,ch);send(d,c,True);send(d,c,False);time.sleep(.012)
def phys(d):
 bits=d.query_keymap();keys=[k for k in range(8,256) if bits[k//8]&(1<<(k%8))]
 return keys,int(d.screen().root.query_pointer().mask)

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--display',required=True);ap.add_argument('--pipe',required=True);ap.add_argument('--fault',choices=['none','focus','text'],required=True);a=ap.parse_args()
 out=a.out.resolve();out.mkdir(parents=True,exist_ok=False);A=out/'a.odt';B=out/'b.odt';mkdoc(A,A0);mkdoc(B,B0)
 auth=out/'Xauthority';auth.write_bytes(b'');env=os.environ.copy();env.update(DISPLAY=a.display,XAUTHORITY=str(auth));os.environ.update(DISPLAY=a.display,XAUTHORITY=str(auth))
 xv=subprocess.Popen(['Xvfb',a.display,'-screen','0','1024x768x24','-nolisten','tcp','-ac'],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);ob=lo=None
 try:
  wait_display(env,a.display);ob=subprocess.Popen(['openbox'],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  lo=subprocess.Popen(['libreoffice',f'-env:UserInstallation={(out/"profile").resolve().as_uri()}','--nologo','--nodefault','--nofirststartwizard','--norestore',f'--accept=pipe,name={a.pipe};urp;StarOffice.ServiceManager',str(A),str(B)],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  target=A.resolve().as_uri();other=B.resolve().as_uri();rows=wait_docs(env,a.pipe);ar=row(rows,target);br=row(rows,other);observed_ns=time.monotonic_ns()
  bound=bind_document(env,HERE/'uno_helper.py',a.pipe,target,ar['uid'],a.display)
  d=display.Display(a.display);active,fx=active_focus(d);rr=row(uno(env,HERE/'uno_helper.py',a.pipe,'list'),target)
  guard_ok=(active==bound['xid']==fx and rr['uid']==ar['uid'] and rr['text']==A0 and time.monotonic_ns()-observed_ns<=MAX_AGE_NS)
  if not guard_ok:raise RuntimeError('pre-injection guard failed')
  guard_completed_ns=time.monotonic_ns();fault_injected_ns=None
  if a.fault=='focus':
   uno(env,HERE/'uno_helper.py',a.pipe,'activate',url=other,uid=br['uid']);fault_injected_ns=time.monotonic_ns();time.sleep(.05)
  elif a.fault=='text':
   uno(env,HERE/'uno_helper.py',a.pipe,'set_text',url=target,text='boox');fault_injected_ns=time.monotonic_ns();time.sleep(.03)
  first_input_ns=time.monotonic_ns();chord(d,['Control_L','End']);text(d,SUFFIX);time.sleep(.12)
  keys,mask=phys(d);d.close();final=uno(env,HERE/'uno_helper.py',a.pipe,'list');fa=row(final,target);fb=row(final,other)
  if a.fault=='none':gate=fa['text']==DESIRED and fb['text']==B0
  elif a.fault=='focus':gate=fa['text']==A0 and fb['text']=='bookkkeeperoffice'
  else:gate=fa['text']=='booxkeeperoffice' and fb['text']==B0
  order_ok=guard_completed_ns<first_input_ns and (fault_injected_ns is None or guard_completed_ns<fault_injected_ns<first_input_ns)
  result={'fault':a.fault,'guard_ok':guard_ok,'guard_completed_ns':guard_completed_ns,'fault_injected_ns':fault_injected_ns,'first_input_ns':first_input_ns,'order_ok':order_ok,'bound':bound,'final_a':fa,'final_b':fb,'release':{'keys':keys,'mask':mask,'empty':not keys and mask==0},'gate_pass':bool(gate and order_ok and not keys and mask==0)}
  (out/'report.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n');print(json.dumps(result,ensure_ascii=False));return 0 if result['gate_pass'] else 1
 finally:
  for p in (lo,ob,xv):
   if p and p.poll() is None:p.terminate()
  for p in (lo,ob,xv):
   if p:
    try:p.wait(timeout=2)
    except Exception:p.kill()
if __name__=='__main__':raise SystemExit(main())
