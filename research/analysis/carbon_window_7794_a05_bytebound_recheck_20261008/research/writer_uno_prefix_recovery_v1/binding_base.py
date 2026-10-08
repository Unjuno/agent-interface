from __future__ import annotations
import json,subprocess,time
from pathlib import Path
from Xlib import X,display,protocol

def uno(env, helper:Path, pipe:str, command:str, **kw):
    cmd=['/usr/bin/python3',str(helper),'--pipe',pipe,command]
    for k,v in kw.items():cmd += ['--'+k.replace('_','-'),str(v)]
    p=subprocess.run(cmd,env=env,text=True,capture_output=True)
    if p.returncode: raise RuntimeError(f'UNO {command} failed {p.returncode}: {p.stdout} {p.stderr}')
    return json.loads(p.stdout)

def title(d,wid:int):
    w=d.create_resource_object('window',wid)
    for name in ('_NET_WM_NAME','WM_NAME'):
        try:
            q=w.get_full_property(d.intern_atom(name),X.AnyPropertyType)
            if q:
                v=q.value;return v.decode('utf-8','replace') if isinstance(v,bytes) else str(v)
        except Exception:pass
    return ''

def writer_windows(d):
    root=d.screen().root;atom=d.intern_atom('_NET_CLIENT_LIST');q=root.get_full_property(atom,X.AnyPropertyType);out=[]
    if q:
        for raw in q.value:
            wid=int(raw);w=d.create_resource_object('window',wid)
            try:cls=w.get_wm_class() or ()
            except Exception:continue
            if any('libreoffice-writer' in str(x).lower() for x in cls):out.append({'xid':wid,'title':title(d,wid)})
    return out

def active_focus(d):
    root=d.screen().root;atom=d.intern_atom('_NET_ACTIVE_WINDOW');q=root.get_full_property(atom,X.AnyPropertyType);active=int(q.value[0]) if q is not None and len(q.value) else 0
    f=d.get_input_focus().focus;fid=int(getattr(f,'id',0) or 0)
    return active,fid

def bind_document(env,helper,pipe,url,uid,display_name):
    act=uno(env,helper,pipe,'activate',url=url,uid=uid)
    d=display.Display(display_name)
    stable=[];deadline=time.monotonic()+1.5
    while time.monotonic()<deadline:
        a,f=active_focus(d)
        stable.append((a,f))
        if len(stable)>=3 and len(set(stable[-3:]))==1 and a and a==f:break
        time.sleep(.02)
    a,f=active_focus(d);t=title(d,a) if a else '';d.close()
    rows=uno(env,helper,pipe,'list')
    matches=[r for r in rows if r['url']==url and r['uid']==uid]
    if not act.get('ok') or len(matches)!=1 or not a or a!=f: raise RuntimeError('binding verification failed')
    return {'url':url,'uid':uid,'xid':a,'title':t,'active_xid':a,'focus_xid':f,'document_after':matches[0]}
