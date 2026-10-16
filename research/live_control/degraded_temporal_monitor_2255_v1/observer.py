#!/usr/bin/env python3
import json, os, sys, time
from Xlib import X, display

dpy=display.Display(sys.argv[1])
xid=int(sys.argv[2]); expected=int(sys.argv[3])
win=dpy.create_resource_object('window',xid)
while True:
    tree=win.query_tree()
    if tree.parent.id == tree.root.id:
        break
    win=tree.parent
atom=dpy.intern_atom('WM_NAME')
win.change_attributes(event_mask=X.PropertyChangeMask)
dpy.sync()
print(json.dumps({'kind':'observer_ready','pid':os.getpid(),'expected':expected,'source_xid':xid,'target_xid':win.id,'mono_ns':time.monotonic_ns()}),flush=True)
seen=0
while seen<expected:
    ev=dpy.next_event()
    if ev.type != X.PropertyNotify or ev.window.id != win.id or ev.atom != atom:
        continue
    before=time.monotonic_ns()
    prop=win.get_full_property(atom, X.AnyPropertyType)
    after=time.monotonic_ns()
    if prop is None:
        raw=b''
    elif isinstance(prop.value, str):
        raw=prop.value.encode('utf-8')
    else:
        raw=bytes(prop.value)
    text=raw.decode('utf-8','replace')
    parts=text.split(':')
    if len(parts)!=3:
        continue
    epoch=int(parts[0]); phase=parts[1]; tag=int(parts[2])
    print(json.dumps({'kind':'event','ordinal':seen,'epoch':epoch,'phase':phase,'tag':tag,'server_ms':int(ev.time),'clock_domain':'xserver','read_before_ns':before,'read_after_ns':after,'raw_hex':raw.hex()}),flush=True)
    seen+=1
print(json.dumps({'kind':'observer_done','events':seen,'mono_ns':time.monotonic_ns()}),flush=True)
dpy.close()
