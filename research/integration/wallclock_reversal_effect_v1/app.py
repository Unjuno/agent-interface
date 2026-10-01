#!/usr/bin/env python3
import json, select, sys, time
from Xlib import X, XK, display


def emit(obj):
    print(json.dumps(obj,sort_keys=True),flush=True)


def main():
    d=display.Display(); s=d.screen(); root=s.root
    win=root.create_window(40,40,280,100,0,s.root_depth,X.InputOutput,X.CopyFromParent,
                           background_pixel=s.white_pixel,event_mask=X.KeyPressMask|X.KeyReleaseMask|X.StructureNotifyMask)
    win.map(); d.sync(); time.sleep(.03)
    win.set_input_focus(X.RevertToParent,X.CurrentTime); d.sync()
    effect=0; journal=[]
    emit({'event':'ready','window_id':int(win.id),'pid':__import__('os').getpid()})
    while True:
        ready,_,_=select.select([d.fileno(),sys.stdin],[],[],0.1)
        if d.fileno() in ready:
            while d.pending_events():
                ev=d.next_event()
                if ev.type not in (X.KeyPress,X.KeyRelease):
                    continue
                ks=d.keycode_to_keysym(ev.detail,0)
                if ks == XK.string_to_keysym('Left'):
                    name='Left'
                elif ks == XK.string_to_keysym('Right'):
                    name='Right'
                else:
                    name=XK.keysym_to_string(ks) or str(ks)
                kind='press' if ev.type==X.KeyPress else 'release'
                rec={'event':'key','kind':kind,'key':name,'keycode':int(ev.detail),'app_ns':time.perf_counter_ns()}
                journal.append(rec)
                if kind=='press' and name=='Left': effect-=1
                if kind=='press' and name=='Right': effect+=1
        if sys.stdin in ready:
            line=sys.stdin.readline()
            if not line: break
            req=json.loads(line)
            if req.get('op')=='snapshot':
                emit({'event':'snapshot','effect':effect,'journal':journal,'focus':int(d.get_input_focus().focus.id)})
            elif req.get('op')=='close':
                emit({'event':'closed','effect':effect,'journal':journal}); break
            else: raise SystemExit('bad op')
    win.destroy(); d.sync(); d.close(); return 0
if __name__=='__main__': raise SystemExit(main())
