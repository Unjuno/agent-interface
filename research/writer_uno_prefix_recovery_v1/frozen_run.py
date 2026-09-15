from __future__ import annotations
import argparse,json,os,subprocess,time
from pathlib import Path
from odf.opendocument import OpenDocumentText
from odf.text import P
from Xlib import X,XK,display
from Xlib.ext import xtest
from candidate import Observation,precheck_bound,suffix_from_text,final_focus_guard
from binding_base import uno,bind_document,active_focus
HERE=Path(__file__).resolve().parent
DESIRED='bookkeeperoffice'; A0='book'; B0='bookk'; MAX_AGE_NS=500_000_000

def mkdoc(path,text):
 d=OpenDocumentText(); d.text.addElement(P(text=text)); d.save(str(path))
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
  except Exception: pass
  time.sleep(.05)
 raise RuntimeError('docs unavailable')
def row(rows,url):
 m=[r for r in rows if r['url']==url]
 if len(m)!=1:raise RuntimeError('row mismatch')
 return m[0]
def code(d,name):
 c=d.keysym_to_keycode(XK.string_to_keysym(name))
 if not c:raise RuntimeError(name)
 return c
def key(d,c,down):xtest.fake_input(d,X.KeyPress if down else X.KeyRelease,c);d.sync()
def chord(d,names):
 cs=[code(d,n) for n in names]
 for c in cs:key(d,c,True)
 for c in reversed(cs):key(d,c,False)
def text(d,s):
 for ch in s:
  c=code(d,ch);key(d,c,True);key(d,c,False);time.sleep(.012)
def phys(d):
 bits=d.query_keymap(); keys=[k for k in range(8,256) if bits[k//8]&(1<<(k%8))]
 return keys,int(d.screen().root.query_pointer().mask)
def focus(d,xid):
 w=d.create_resource_object('window',xid);w.set_input_focus(X.RevertToParent,X.CurrentTime);d.sync();time.sleep(.03)

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--display',required=True);ap.add_argument('--pipe',required=True);ap.add_argument('--policy',choices=['weak','bound'],required=True);ap.add_argument('--condition',choices=['fresh','stale_uid','wrong_doc','focus_drift','stale_age','text_changed'],required=True);a=ap.parse_args()
 out=a.out.resolve();out.mkdir(parents=True,exist_ok=False);A=out/'a-target.odt';B=out/'b-sidecar.odt';mkdoc(A,A0);mkdoc(B,B0)
 auth=out/'Xauthority';auth.write_bytes(b'');env=os.environ.copy();env.update(DISPLAY=a.display,XAUTHORITY=str(auth));os.environ.update(DISPLAY=a.display,XAUTHORITY=str(auth))
 xv=subprocess.Popen(['Xvfb',a.display,'-screen','0','1024x768x24','-nolisten','tcp','-ac'],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);ob=lo=None
 try:
  wait_display(env,a.display);ob=subprocess.Popen(['openbox'],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  lo=subprocess.Popen(['libreoffice',f'-env:UserInstallation={(out/"profile").resolve().as_uri()}','--nologo','--nodefault','--nofirststartwizard','--norestore',f'--accept=pipe,name={a.pipe};urp;StarOffice.ServiceManager',str(A),str(B)],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  target=A.resolve().as_uri();other=B.resolve().as_uri();rows=wait_docs(env,a.pipe);ar=row(rows,target);br=row(rows,other)
  orow=br if a.condition=='wrong_doc' else ar;obs=Observation(orow['url'],orow['uid'],orow['text'],time.monotonic_ns())
  if a.condition=='stale_uid':uno(env,HERE/'uno_helper.py',a.pipe,'close_reopen',url=target,uid=ar['uid']);time.sleep(.08)
  if a.condition=='text_changed':uno(env,HERE/'uno_helper.py',a.pipe,'set_text',url=target,text='boox')
  if a.condition=='stale_age':time.sleep(.65)
  cur=row(wait_docs(env,a.pipe),target);d=display.Display(a.display);accepted=False;error=None;suffix='';bound=None
  if a.policy=='weak':dec=suffix_from_text(DESIRED,obs.text)
  else:dec=precheck_bound(obs,desired=DESIRED,target_url=target,current_row=cur,now_ns=time.monotonic_ns(),max_age_ns=MAX_AGE_NS)
  accepted,error,suffix=dec.accepted,dec.error,dec.suffix
  if accepted:
   uid=cur['uid'] if a.policy=='weak' else obs.uid
   bound=bind_document(env,HERE/'uno_helper.py',a.pipe,target,uid,a.display)
  if accepted and a.condition=='focus_drift':uno(env,HERE/'uno_helper.py',a.pipe,'activate',url=other,uid=br['uid']);time.sleep(.05)
  emissions=0
  if accepted and a.policy=='bound':
   active,fx=active_focus(d);e=final_focus_guard(bound['xid'],active,fx);rr=row(uno(env,HERE/'uno_helper.py',a.pipe,'list'),target)
   if e is None and (rr['uid']!=obs.uid or rr['text']!=obs.text):e='FINAL_DOCUMENT_CHANGED'
   if e is None and time.monotonic_ns()-obs.observed_ns>MAX_AGE_NS:e='STALE_OBSERVATION_FINAL'
   if e is not None:accepted=False;error=e
  if accepted:
   if a.policy=='weak' and a.condition!='focus_drift':focus(d,bound['xid'])
   chord(d,['Control_L','End']);emissions+=4;text(d,suffix);emissions+=2*len(suffix);time.sleep(.12)
  keys,mask=phys(d);d.close();final=uno(env,HERE/'uno_helper.py',a.pipe,'list');fa=row(final,target);fb=row(final,other)
  if a.policy=='bound':
   gate=(fa['text']==DESIRED and fb['text']==B0 and emissions>0) if a.condition=='fresh' else (not accepted and emissions==0 and fa['text'] in (A0,'boox') and fb['text']==B0)
  elif a.condition=='fresh':gate=fa['text']==DESIRED and fb['text']==B0 and emissions>0
  elif a.condition in ('stale_uid','stale_age'):gate=accepted and emissions>0
  else:gate=accepted and emissions>0 and not (fa['text']==DESIRED and fb['text']==B0)
  result={'policy':a.policy,'condition':a.condition,'observation':obs.__dict__,'current_before':cur,'accepted':accepted,'error':error,'suffix':suffix,'binding':bound,'emissions':emissions,'final_a':fa,'final_b':fb,'release':{'keys':keys,'mask':mask,'empty':not keys and mask==0},'gate_pass':bool(gate and not keys and mask==0)}
  (out/'report.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n');print(json.dumps(result,ensure_ascii=False));return 0 if result['gate_pass'] else 1
 finally:
  for p in (lo,ob,xv):
   if p and p.poll() is None:p.terminate()
  for p in (lo,ob,xv):
   if p:
    try:p.wait(timeout=2)
    except Exception:p.kill()
if __name__=='__main__':raise SystemExit(main())
