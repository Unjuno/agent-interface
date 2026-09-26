"""Private display actor or independent read-only state witness. No host display."""
from __future__ import annotations
import json,os,sys,time
from Xlib import X,XK,display
from Xlib.ext import xtest
role=sys.argv[1]
if role not in ('writer','witness'):raise SystemExit(64)
d=display.Display();code=d.keysym_to_keycode(XK.string_to_keysym('Shift_L'))
windows=[];held=False

def snap():
    a=time.monotonic_ns();m=bytes(d.query_keymap());f=d.get_input_focus();p=d.screen().root.query_pointer()
    return dict(before_ns=a,after_ns=time.monotonic_ns(),keymap=m.hex(),focus=f.focus.id if hasattr(f.focus,'id') else int(f.focus),pointer_mask=p.mask,keycode=code)
def emit(o):print(json.dumps(o,sort_keys=True),flush=True)
emit(dict(kind='ready',role=role,pid=os.getpid(),keycode=code))
try:
    for line in sys.stdin:
        req=json.loads(line);op=req['op'];a=time.monotonic_ns();result={}
        if op=='snapshot':result=snap()
        elif op=='new' and role=='writer':
            if held:raise RuntimeError('previous block still held')
            for w in windows:w.destroy()
            windows=[]
            for x in (20,260):
                w=d.screen().root.create_window(x,30,160,120,0,d.screen().root_depth,X.InputOutput,X.CopyFromParent,background_pixel=0,event_mask=X.KeyPressMask|X.KeyReleaseMask)
                w.map();windows.append(w)
            d.screen().root.warp_pointer(620,460);d.set_input_focus(windows[0],X.RevertToParent,X.CurrentTime);d.sync()
            result=dict(target=windows[0].id,away=windows[1].id,state=snap())
        elif op=='mutate' and role=='writer':
            ops=[]
            def key(down):
                global held
                before=time.monotonic_ns();xtest.fake_input(d,X.KeyPress if down else X.KeyRelease,code);d.sync();held=down
                ops.append(dict(kind='edge',keycode=code,down=down,before_ns=before,after_ns=time.monotonic_ns()))
            def focus(w):
                before=time.monotonic_ns();d.set_input_focus(w,X.RevertToParent,X.CurrentTime);d.sync()
                ops.append(dict(kind='focus',window=w.id,before_ns=before,after_ns=time.monotonic_ns()))
            kind=req['context']
            if kind=='UP':pass
            elif kind=='DOWN':key(True)
            elif kind=='EDGE_BURST':
                for i in range(8):key(True);key(False)
                key(True)
            elif kind=='FOCUS_RETURN':focus(windows[1]);key(True);focus(windows[0])
            else:raise ValueError('context')
            result=dict(operations=ops,state=snap())
        elif op=='release' and role=='writer':
            if held:xtest.fake_input(d,X.KeyRelease,code);d.sync();held=False
            result=snap()
        elif op=='close':
            emit(dict(id=req['id'],op=op,before_ns=a,after_ns=time.monotonic_ns(),result=snap()));break
        else:raise ValueError('unsupported actor command')
        emit(dict(id=req['id'],op=op,before_ns=a,after_ns=time.monotonic_ns(),result=result))
finally:
    if role=='writer':
        if held:xtest.fake_input(d,X.KeyRelease,code);d.sync()
        for w in windows:w.destroy()
        d.sync()
    d.close()
