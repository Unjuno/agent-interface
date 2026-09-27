#!/usr/bin/python3
from __future__ import annotations
import argparse,json,os,time,uno

def connect(pipe):
 local=uno.getComponentContext(); sm=local.ServiceManager
 r=sm.createInstanceWithContext('com.sun.star.bridge.UnoUrlResolver',local); last=None
 for _ in range(300):
  try:return r.resolve(f'uno:pipe,name={pipe};urp;StarOffice.ComponentContext')
  except Exception as e:last=e;time.sleep(.02)
 raise RuntimeError(last)
def desk(ctx):return ctx.ServiceManager.createInstanceWithContext('com.sun.star.frame.Desktop',ctx)
def find(d,url,uid=None):
 m=[]
 for c in d.Components:
  try:
   if str(c.URL)==url:m.append(c)
  except Exception:pass
 if len(m)!=1:return None,'URL_COUNT_'+str(len(m))
 c=m[0]
 if uid is not None and str(c.RuntimeUID)!=uid:return None,'STALE_DOCUMENT_ID'
 return c,None
def touch(p):
 if p:open(p,'w').close()
def wait(p):
 if not p:return
 for _ in range(5000):
  if os.path.exists(p):return
  time.sleep(.001)
 raise RuntimeError('barrier timeout')
def stamp():return time.monotonic_ns()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--pipe',required=True);ap.add_argument('--url',required=True);ap.add_argument('--uid');ap.add_argument('cmd');ap.add_argument('--text');ap.add_argument('--ready');ap.add_argument('--go');ap.add_argument('--delay-us',type=int,default=0);a=ap.parse_args()
 ctx=connect(a.pipe);d=desk(ctx);c,err=find(d,a.url,a.uid)
 if err:
  print(json.dumps({'ok':False,'error':err,'refused':True}));return 3
 if a.cmd=='get':print(json.dumps({'ok':True,'text':str(c.Text.String),'uid':str(c.RuntimeUID)}));return 0
 if a.cmd=='set':c.Text.String=a.text;print(json.dumps({'ok':True,'text':str(c.Text.String)}));return 0
 if a.cmd=='close_reopen':
  old=str(c.RuntimeUID);c.close(True);time.sleep(.05);n=d.loadComponentFromURL(a.url,'_blank',0,());time.sleep(.12);print(json.dumps({'ok':True,'old_uid':old,'new_uid':str(n.RuntimeUID),'text':str(n.Text.String)}));return 0
 if a.cmd=='append':
  touch(a.ready);wait(a.go)
  if a.delay_us:time.sleep(a.delay_us/1_000_000)
  t0=stamp();cur=c.Text.createTextCursor();cur.gotoEnd(False);c.Text.insertString(cur,a.text or 'x',False);t1=stamp()
  print(json.dumps({'ok':True,'call_start_ns':t0,'call_end_ns':t1,'text':str(c.Text.String)}));return 0
 if a.cmd=='baseline':
  before=str(c.Text.String);matched=before=='book';read_ns=stamp();touch(a.ready);wait(a.go)
  if a.delay_us:time.sleep(a.delay_us/1_000_000)
  t0=stamp()
  if matched:c.Text.String=a.text
  t1=stamp();print(json.dumps({'ok':True,'read_ns':read_ns,'matched':matched,'call_start_ns':t0,'call_end_ns':t1,'text':str(c.Text.String)}));return 0
 if a.cmd=='replace':
  rd=c.createReplaceDescriptor();rd.SearchString='^book$';rd.ReplaceString=a.text;rd.SearchRegularExpression=True
  touch(a.ready);wait(a.go)
  if a.delay_us:time.sleep(a.delay_us/1_000_000)
  t0=stamp();n=c.replaceAll(rd);t1=stamp();print(json.dumps({'ok':True,'count':int(n),'call_start_ns':t0,'call_end_ns':t1,'text':str(c.Text.String)}));return 0
 raise RuntimeError('bad cmd')
raise SystemExit(main())
