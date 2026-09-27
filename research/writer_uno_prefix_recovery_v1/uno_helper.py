#!/usr/bin/python3
from __future__ import annotations
import argparse,json,time,uno

def connect(pipe):
    local=uno.getComponentContext(); sm=local.ServiceManager
    resolver=sm.createInstanceWithContext('com.sun.star.bridge.UnoUrlResolver',local)
    last=None
    for _ in range(250):
        try:return resolver.resolve(f'uno:pipe,name={pipe};urp;StarOffice.ComponentContext')
        except Exception as e:last=e;time.sleep(.02)
    raise RuntimeError(f'UNO connect failed {last!r}')

def get_desktop(ctx): return ctx.ServiceManager.createInstanceWithContext('com.sun.star.frame.Desktop',ctx)
def rows(desktop):
    out=[]
    for c in desktop.Components:
        try: out.append({'url':str(c.URL),'title':str(c.Title),'uid':str(c.RuntimeUID),'text':str(c.Text.String)})
        except Exception: pass
    return out

def find(desktop,url,uid=None):
    matches=[]
    for c in desktop.Components:
        try:
            if str(c.URL)==url and (uid is None or str(c.RuntimeUID)==uid): matches.append(c)
        except Exception: pass
    if len(matches)!=1: raise RuntimeError(f'identity mismatch {url} {uid} count={len(matches)}')
    return matches[0]

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--pipe',required=True);ap.add_argument('cmd',choices=['list','activate','close_reopen','set_text']);ap.add_argument('--url');ap.add_argument('--uid');ap.add_argument('--text');a=ap.parse_args()
    ctx=connect(a.pipe); desktop=get_desktop(ctx)
    if a.cmd=='list': print(json.dumps(rows(desktop),ensure_ascii=False));return 0
    c=find(desktop,a.url,a.uid if a.cmd in ('activate','close_reopen') else None)
    if a.cmd=='activate':
        fr=c.CurrentController.Frame;fr.activate();fr.ContainerWindow.setFocus();time.sleep(.05)
        print(json.dumps({'ok':True,'url':str(c.URL),'uid':str(c.RuntimeUID),'text':str(c.Text.String),'active':bool(fr.isActive())},ensure_ascii=False));return 0
    if a.cmd=='set_text':
        c.Text.String=a.text;time.sleep(.03);print(json.dumps({'ok':True,'url':str(c.URL),'uid':str(c.RuntimeUID),'text':str(c.Text.String)},ensure_ascii=False));return 0
    old=str(c.RuntimeUID); url=str(c.URL); c.close(True); time.sleep(.08)
    n=desktop.loadComponentFromURL(url,'_blank',0,()); time.sleep(.15)
    print(json.dumps({'ok':True,'url':str(n.URL),'old_uid':old,'new_uid':str(n.RuntimeUID),'text':str(n.Text.String)},ensure_ascii=False)); return 0
if __name__=='__main__': raise SystemExit(main())
