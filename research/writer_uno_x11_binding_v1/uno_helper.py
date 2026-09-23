#!/usr/bin/python3
from __future__ import annotations
import argparse,json,time,uno

def connect(pipe):
    local=uno.getComponentContext()
    resolver=local.ServiceManager.createInstanceWithContext('com.sun.star.bridge.UnoUrlResolver',local)
    last=None
    for _ in range(200):
        try:return resolver.resolve(f'uno:pipe,name={pipe};urp;StarOffice.ComponentContext')
        except Exception as e:last=e;time.sleep(.02)
    raise RuntimeError(f'UNO connect failed: {last!r}')

def docs(ctx):
    desktop=ctx.ServiceManager.createInstanceWithContext('com.sun.star.frame.Desktop',ctx)
    out=[]
    for c in desktop.Components:
        try:
            out.append({'url':str(c.URL),'title':str(c.Title),'uid':str(c.RuntimeUID),'text':str(c.Text.String)})
        except Exception:
            pass
    return desktop,out

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--pipe',required=True);ap.add_argument('command',choices=['list','activate']);ap.add_argument('--url');ap.add_argument('--uid');a=ap.parse_args()
    ctx=connect(a.pipe);desktop,rows=docs(ctx)
    if a.command=='list':print(json.dumps(rows,ensure_ascii=False));return 0
    match=[]
    for c in desktop.Components:
        try:
            if str(c.URL)==a.url and str(c.RuntimeUID)==a.uid:match.append(c)
        except Exception:pass
    if len(match)!=1:
        print(json.dumps({'ok':False,'error':'identity_mismatch','count':len(match)}));return 2
    c=match[0];fr=c.CurrentController.Frame;fr.activate();fr.ContainerWindow.setFocus();time.sleep(.05)
    print(json.dumps({'ok':True,'url':str(c.URL),'title':str(c.Title),'uid':str(c.RuntimeUID),'text':str(c.Text.String),'frame_active':bool(fr.isActive())},ensure_ascii=False));return 0
if __name__=='__main__':raise SystemExit(main())
