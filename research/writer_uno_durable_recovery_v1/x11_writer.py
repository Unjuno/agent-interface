from __future__ import annotations
import json,subprocess,time
from pathlib import Path
from odf.opendocument import OpenDocumentText
from odf.text import P
from Xlib import X,XK,display
from Xlib.ext import xtest

def mk(path,text): d=OpenDocumentText();d.text.addElement(P(text=text));d.save(str(path))
def uno(env,helper:Path,pipe,cmd,**kw):
 c=['/usr/bin/python3',str(helper),'--pipe',pipe,cmd]
 for k,v in kw.items():c+=['--'+k.replace('_','-'),str(v)]
 p=subprocess.run(c,env=env,text=True,capture_output=True)
 if p.returncode:raise RuntimeError(f'UNO {cmd}: {p.stdout} {p.stderr}')
 return json.loads(p.stdout)
def row(rows,url):
 m=[r for r in rows if r['url']==url]
 if len(m)!=1:raise RuntimeError(f'row mismatch {url}: {m}')
 return m[0]
def wait_display(env,name):
 for _ in range(150):
  if subprocess.run(['xdpyinfo','-display',name],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0:return
  time.sleep(.03)
 raise RuntimeError('display unavailable')
def wait_docs(env,helper,pipe):
 for _ in range(200):
  try:
   r=uno(env,helper,pipe,'list')
   if len(r)>=2:return r
  except Exception:pass
  time.sleep(.03)
 raise RuntimeError('docs unavaile')
def active_focus(d):
 q=d.screen().root.get_full_property(d.intern_atom('_NET_ACTIVE_WINDOW'),X.AnyPropertyType);a=int(q.value[0]) if q is not None and len(q.value) else 0
 f=d.get_input_focus().focus;return a,int(getattr(f,'id',0) or 0)
def bind(env,helper,pipe,url,uid,dname):
 act=uno(env,helper,pipe,'activate',url=url,uid=uid);d=display.Display(dname);hist=[];end=time.monotonic()+1.5
 while time.monotonic()<end:
  af=active_focus(d);hist.append(af)
  if len(hist)>=3 and len(set(hist[-3:]))==1 and af[0] and af[0]==af[1]:break
  time.sleep(.02)
 a,f=active_focus(d);d.close();r=row(uno(env,helper,pipe,'list'),url)
 if not act.get('ok') or r['uid']!=uid or not a or a!=f:raise RuntimeError('binding verification failed')
 return a
def code(d,name):
 c=d.keysym_to_keycode(XK.string_to_keysym(name))
 if not c:raise RuntimeError(name)
 return c
def key(d,c,down):xtest.fake_input(d,X.KeyPress if down else X.KeyRelease,c);d.sync()
def chord(d,names):
 cs=[code(d,n) for n in names]
 for c in cs:key(d,c,True)
 for c in reversed(cs):key(d,c,False)
def type_text(d,s):
 for ch in s:
  c=code(d,ch);key(d,c,True);key(d,c,False);time.sleep(.012)
def phys(d):
 bits=d.query_keymap();ks=[k for k in range(8,256) if bits[k//8]&(1<<(k%8))]
 return ks,int(d.screen().root.query_pointer().mask)
