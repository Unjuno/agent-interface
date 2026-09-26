#!/usr/bin/env python3
import json, os, select, sys, time
from Xlib import X, display
xid=int(sys.argv[1],0); epoch=sys.argv[2]; out=sys.argv[3]
d=display.Display(); w=d.create_resource_object('window',xid)
w.change_attributes(event_mask=X.KeyPressMask|X.KeyReleaseMask); d.sync()
km=d.query_keymap()
bootstrap={'epoch':epoch,'mono_ns':time.monotonic_ns(),'keymap_hex':bytes(km).hex()}
print(json.dumps({'ready':True,'pid':os.getpid(),'epoch':epoch,'bootstrap':bootstrap},sort_keys=True),flush=True)
fdx=d.fileno(); fdi=sys.stdin.fileno(); seq=0
with open(out,'a',buffering=1) as f:
    while True:
        r,_,_=select.select([fdx,fdi],[],[],0.2)
        if fdi in r:
            line=sys.stdin.readline()
            if not line: break
            cmd=line.strip()
            if cmd=='stop': break
            if cmd=='drain':
                d.sync()
                while d.pending_events():
                    e=d.next_event(); seq+=1
                    if e.type in (X.KeyPress,X.KeyRelease):
                        f.write(json.dumps({'seq':seq,'epoch':epoch,'kind':'KeyPress' if e.type==X.KeyPress else 'KeyRelease','detail':int(e.detail),'state':int(e.state),'time':int(e.time),'mono_ns':time.monotonic_ns()},sort_keys=True)+'\n')
                print(json.dumps({'drained':True,'seq':seq},sort_keys=True),flush=True)
        if fdx in r:
            while d.pending_events():
                e=d.next_event(); seq+=1
                if e.type in (X.KeyPress,X.KeyRelease):
                    f.write(json.dumps({'seq':seq,'epoch':epoch,'kind':'KeyPress' if e.type==X.KeyPress else 'KeyRelease','detail':int(e.detail),'state':int(e.state),'time':int(e.time),'mono_ns':time.monotonic_ns()},sort_keys=True)+'\n')
d.close()
