#!/usr/bin/env python3
import hashlib, json, sys, time
from Xlib import X, display

W,H=240,160
X0,Y0=90,90

def emit(obj):
    print(json.dumps(obj, sort_keys=True), flush=True)

def drain(d, win_id):
    rows=[]
    d.sync()
    while d.pending_events():
        e=d.next_event()
        wid=getattr(getattr(e,'window',None),'id',None)
        if e.type in (X.ButtonPress, X.ButtonRelease) and wid==win_id:
            rows.append({'type':int(e.type),'detail':int(getattr(e,'detail',0)),
                         'event_x':int(getattr(e,'event_x',-1)), 'event_y':int(getattr(e,'event_y',-1))})
    return rows

def snapshot(win):
    geo=win.get_geometry()
    img=win.get_image(0,0,geo.width,geo.height,X.ZPixmap,0xffffffff)
    raw=bytes(img.data)
    return {'width':int(geo.width),'height':int(geo.height),'bytes':len(raw),
            'sha256':hashlib.sha256(raw).hexdigest()}

def wait_viewable(win, d, timeout=3.0):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        try:
            attrs=win.get_attributes()
            if int(attrs.map_state)==X.IsViewable:
                return
        except Exception:
            pass
        d.sync(); time.sleep(0.02)
    raise TimeoutError('WINDOW_NOT_VIEWABLE')

def create_window(d, reuse=None):
    root=d.screen().root
    if reuse is not None:
        # Xlib allocates from last_resource_id if that ID is currently free.
        d.display.last_resource_id = int(reuse) & int(d.display.info.resource_id_mask)
    win=root.create_window(X0,Y0,W,H,0,d.screen().root_depth,X.InputOutput,X.CopyFromParent,
                           background_pixel=d.screen().black_pixel,
                           event_mask=X.ExposureMask|X.ButtonPressMask|X.ButtonReleaseMask|X.StructureNotifyMask)
    win.set_wm_name('issue4221-native-review')
    win.set_wm_class('issue4221','Issue4221')
    win.map(); d.sync(); time.sleep(0.05)
    # Non-flat, deterministic content around the click/mint location.
    gc1=win.create_gc(foreground=0x202040); gc2=win.create_gc(foreground=0xcc3030); gc3=win.create_gc(foreground=0x30cc50)
    win.fill_rectangle(gc1,0,0,W,H)
    win.fill_rectangle(gc2,84,52,36,56)
    win.fill_rectangle(gc3,120,52,36,56)
    for i in range(0,160,16):
        win.fill_rectangle(gc2 if (i//16)%2==0 else gc3,20+i%180,20+(i*3)%110,8,8)
    d.sync(); time.sleep(0.08)
    time.sleep(0.03)
    return win

def main():
    d=display.Display()
    win=None; old_id=None; effects=[]
    emit({'ready':True,'display':d.get_display_name()})
    for line in sys.stdin:
        if not line.strip(): continue
        cmd=json.loads(line)
        op=cmd['op']
        try:
            if op=='create':
                win=create_window(d,cmd.get('reuse_xid'))
                old_id=win.id
                effects=[]
                emit({'ok':True,'op':op,'xid':int(win.id)})
            elif op=='focus':
                win.set_input_focus(X.RevertToParent,X.CurrentTime); d.sync(); time.sleep(0.03)
                f=d.get_input_focus().focus
                emit({'ok':True,'op':op,'focus':int(getattr(f,'id',0))})
            elif op=='snapshot':
                emit({'ok':True,'op':op,'xid':int(win.id),'snapshot':snapshot(win)})
            elif op=='effects':
                effects.extend(drain(d,win.id))
                emit({'ok':True,'op':op,'xid':int(win.id),'button_presses':sum(r['type']==X.ButtonPress for r in effects),'events':effects})
            elif op=='destroy':
                xid=int(win.id); win.destroy(); d.sync(); time.sleep(0.08); win=None
                emit({'ok':True,'op':op,'xid':xid})
            elif op=='create_reuse':
                win=create_window(d,old_id)
                effects=[]
                emit({'ok':True,'op':op,'xid':int(win.id),'requested_xid':int(old_id)})
            elif op=='close':
                if win is not None:
                    try: win.destroy(); d.sync()
                    except Exception: pass
                emit({'ok':True,'op':op}); break
            else:
                raise ValueError(op)
        except Exception as e:
            emit({'ok':False,'op':op,'error':repr(e)}); break
    d.close()
if __name__=='__main__': main()
