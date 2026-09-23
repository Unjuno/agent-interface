#!/usr/bin/python3
from __future__ import annotations
import time,uno

def connect(pipe: str):
    local=uno.getComponentContext(); sm=local.ServiceManager
    r=sm.createInstanceWithContext('com.sun.star.bridge.UnoUrlResolver',local)
    last=None
    for _ in range(300):
        try:return r.resolve(f'uno:pipe,name={pipe};urp;StarOffice.ComponentContext')
        except Exception as e:last=e;time.sleep(.02)
    raise RuntimeError(f'UNO connect failed: {last!r}')

def document(pipe: str, url: str):
    ctx=connect(pipe); d=ctx.ServiceManager.createInstanceWithContext('com.sun.star.frame.Desktop',ctx)
    matches=[]
    for c in d.Components:
        try:
            if str(c.URL)==url: matches.append(c)
        except Exception: pass
    if len(matches)!=1: raise RuntimeError(f'document identity mismatch count={len(matches)} url={url}')
    return matches[0]
