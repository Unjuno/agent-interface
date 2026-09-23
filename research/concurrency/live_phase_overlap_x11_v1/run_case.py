import argparse, json, threading, time
from Xlib import X, Xatom, XK, display
from Xlib.ext import xtest

ap=argparse.ArgumentParser()
ap.add_argument('--arm',choices=['serial_independent','overlap_independent','serial_shared','overlap_shared'],required=True)
ap.add_argument('--delay-ms',type=int,default=150)
a=ap.parse_args()

D=display.Display(); screen=D.screen(); root=D.screen().root
colors={'idle':0x202020,'A':0xff0000,'B':0x0000ff}
windows={}; centers={}; rev={}
for name,x in [('A',80),('B',420)]:
    w=root.create_window(x,100,220,140,0,screen.root_depth,X.InputOutput,X.CopyFromParent,
                         background_pixel=colors['idle'],event_mask=X.KeyPressMask|X.ExposureMask)
    w.map(); windows[name]=w; rev[w.id]=name; centers[name]=(x+110,170)
D.sync()

slot_atom=D.intern_atom('_AI_SHARED_SLOT')
logs=[]; effects={}; pending=[]; done=False; lock=threading.Lock(); ready=threading.Event()

def log(kind,**kw):
    with lock:
        logs.append({'t_ns':time.monotonic_ns(),'kind':kind,**kw})

def write_slot(name):
    root.change_property(slot_atom,Xatom.STRING,8,name.encode('ascii'),X.PropModeReplace); D.sync()
    log('shared_write',surface=name,value=name)

def read_slot():
    p=root.get_full_property(slot_atom,Xatom.STRING)
    if p is None: return ''
    v=p.value
    if isinstance(v,str): return v
    if isinstance(v,bytes): return v.decode('ascii')
    return bytes(v).decode('ascii')

def set_effect(surface,value):
    effects[surface]=value
    w=windows[surface]
    w.change_attributes(background_pixel=colors.get(value,0x00ff00)); w.clear_area(); D.sync()
    log('effect',surface=surface,value=value)

def fixture_loop():
    global done
    ready.set()
    delay_ns=a.delay_ms*1_000_000
    while not done:
        now=time.monotonic_ns()
        while D.pending_events():
            e=D.next_event()
            if e.type==X.KeyPress and e.window.id in rev:
                s=rev[e.window.id]
                log('keypress',surface=s,keycode=e.detail)
                if 'shared' in a.arm: write_slot(s)
                pending.append((now+delay_ns,s))
        i=0
        while i<len(pending):
            due,s=pending[i]
            if now>=due:
                value=read_slot() if 'shared' in a.arm else s
                if 'shared' in a.arm: log('shared_read',surface=s,value=value)
                set_effect(s,value)
                pending.pop(i)
            else:
                i+=1
        time.sleep(0.0005)

thread=threading.Thread(target=fixture_loop,daemon=True); thread.start(); ready.wait()
C=display.Display(); space=C.keysym_to_keycode(XK.string_to_keysym('space'))

def send(surface):
    w=C.create_resource_object('window',windows[surface].id)
    C.set_input_focus(w,X.RevertToParent,X.CurrentTime); C.sync()
    log('focus',surface=surface,window=w.id)
    xtest.fake_input(C,X.KeyPress,space); xtest.fake_input(C,X.KeyRelease,space); C.sync()
    log('inject',surface=surface)

def wait_pred(fn,timeout=2.0):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        with lock: ok=fn()
        if ok:return True
        time.sleep(0.0005)
    return False

def pixel(x,y):
    im=root.get_image(x,y,1,1,X.ZPixmap,0xffffffff)
    raw=im.data.encode('latin1') if isinstance(im.data,str) else im.data
    v=int.from_bytes(raw[:4],'little')
    return [(v>>16)&255,(v>>8)&255,v&255]

def key_is_down(keycode):
    raw=C.query_keymap()
    if isinstance(raw,str): raw=raw.encode('latin1')
    return bool(raw[keycode//8] & (1 << (keycode % 8)))

time.sleep(0.03)
start=time.monotonic_ns(); log('start')
send('A')
if not wait_pred(lambda:any(e['kind']=='keypress' and e.get('surface')=='A' for e in logs)):
    raise RuntimeError('A KeyPress not observed')
if a.arm.startswith('serial_'):
    if not wait_pred(lambda:'A' in effects): raise RuntimeError('A effect timeout')
send('B')
if not wait_pred(lambda:any(e['kind']=='keypress' and e.get('surface')=='B' for e in logs)):
    raise RuntimeError('B KeyPress not observed')
if not wait_pred(lambda:len(effects)==2): raise RuntimeError('effects timeout')
end=time.monotonic_ns(); log('end')
done=True; thread.join(timeout=1)
if thread.is_alive(): raise RuntimeError('fixture thread did not stop')
pixels={s:pixel(*centers[s]) for s in ['A','B']}
expected={'A':[255,0,0],'B':[0,0,255]}
pixel_correct=all(pixels[s]==expected[s] for s in expected)
space_neutral=not key_is_down(space)
with lock: ev=list(logs)
keypress_counts={s:sum(1 for e in ev if e['kind']=='keypress' and e.get('surface')==s) for s in ['A','B']}
# Exact order diagnostics
kp={s:next(e['t_ns'] for e in ev if e['kind']=='keypress' and e.get('surface')==s) for s in ['A','B']}
eff={s:next(e['t_ns'] for e in ev if e['kind']=='effect' and e.get('surface')==s) for s in ['A','B']}
out={
 'arm':a.arm,'delay_ms':a.delay_ms,'wall_ms':(end-start)/1e6,'effects':effects,
 'pixels':pixels,'pixel_correct':pixel_correct,'space_neutral':space_neutral,
 'keypress_counts':keypress_counts,
 'b_keypress_before_a_effect':kp['B'] < eff['A'],
 'a_effect_before_b_keypress':eff['A'] < kp['B'],
 'a_effect_delay_ms':(eff['A']-kp['A'])/1e6,
 'b_effect_delay_ms':(eff['B']-kp['B'])/1e6,
 'events':ev,
}
print(json.dumps(out,sort_keys=True))
for w in windows.values(): w.destroy()
D.sync(); C.close(); D.close()
