#!/usr/bin/python3
from __future__ import annotations
import argparse,json,time,uno

def connect(pipe):
    local=uno.getComponentContext(); sm=local.ServiceManager
    resolver=sm.createInstanceWithContext('com.sun.star.bridge.UnoUrlResolver',local)
    last=None
    for _ in range(300):
        try:return resolver.resolve(f'uno:pipe,name={pipe};urp;StarOffice.ComponentContext')
        except Exception as e:last=e;time.sleep(.02)
    raise RuntimeError(f'UNO connect failed {last!r}')
def desktop(ctx): return ctx.ServiceManager.createInstanceWithContext('com.sun.star.frame.Desktop',ctx)
def rows(d):
    out=[]
    for c in d.Components:
        try: out.append({'url':str(c.URL),'title':str(c.Title),'uid':str(c.RuntimeUID),'text':str(c.Text.String)})
        except Exception: pass
    return out
def find(d,url,uid=None):
    m=[]
    for c in d.Components:
        try:
            if str(c.URL)==url and (uid is None or str(c.RuntimeUID)==uid):m.append(c)
        except Exception:pass
    if len(m)!=1:raise RuntimeError(f'identity mismatch {url} {uid} count={len(m)}')
    return m[0]
def main():
    p=argparse.ArgumentParser();p.add_argument('--pipe',required=True);p.add_argument('cmd',choices=['list','activate','close_reopen','set_text','store']);p.add_argument('--url');p.add_argument('--uid');p.add_argument('--text');a=p.parse_args()
    d=desktop(connect(a.pipe))
    if a.cmd=='list': print(json.dumps(rows(d),ensure_ascii=False));return 0
    c=find(d,a.url,a.uid if a.cmd in ('activate','close_reopen','store') else None)
    if a.cmd=='activate':
        f=c.CurrentController.Frame; f.activate(); f.ContainerWindow.setFocus(); time.sleep(.05)
        print(json.dumps({'ok':True,'url':str(c.URL),'uid':str(c.RuntimeUID),'text':str(c.Text.String),'active':bool(f.isActive())},ensure_ascii=False));return 0
    if a.cmd=='set_text':
        c.Text.String=a.text;time.sleep(.03);print(json.dumps({'ok':True,'url':str(c.URL),'uid':str(c.RuntimeUID),'text':str(c.Text.String)},ensure_ascii=False));return 0
    if a.cmd=='store':
        c.store();time.sleep(.12);print(json.dumps({'ok':True,'url':str(c.URL),'uid':str(c.RuntimeUID),'text':str(c.Text.String),'modified':bool(c.isModified())},ensure_ascii=False));return 0
    old=str(c.RuntimeUID);url=str(c.URL);c.close(True);time.sleep(.08);n=d.loadComponentFromURL(url,'_blank',0,());time.sleep(.18)
    print(json.dumps({'ok':True,'url':str(n.URL),'old_uid':old,'new_uid':str(n.RuntimeUID),'text':str(n.Text.String)},ensure_ascii=False));return 0
if __name__=='__main__': raise SystemExit(main())
