#!/usr/bin/env python3
import json, threading, time
from Xlib import display, X, XK
from Xlib.ext import xtest
owner=display.Display(); screen=owner.screen(); root=screen.root
ka=owner.keysym_to_keycode(XK.string_to_keysym('a'))
kb=owner.keysym_to_keycode(XK.string_to_keysym('b'))
owner.change_keyboard_control(key=ka,auto_repeat_mode=X.AutoRepeatModeOff); owner.sync()
ctl=owner.get_keyboard_control(); amask=1<<(ka&7)
win=root.create_window(0,0,180,100,0,screen.root_depth,X.InputOutput,X.CopyFromParent)
win.map(); owner.sync(); win.set_input_focus(X.RevertToParent,X.CurrentTime); owner.sync()
observer=display.Display(); owner.sync()
events=[]; stop=threading.Event()
def collect():
    while not stop.is_set():
        while observer.pending_events():
            e=observer.next_event()
            if getattr(e,'detail',None) in (ka,kb) and e.type in (X.KeyPress,X.KeyRelease):
                events.append({'detail':int(e.detail),'type':int(e.type),'time':int(e.time),'monotonic_ns':time.monotonic_ns()})
        time.sleep(.001)
t=threading.Thread(target=collect,daemon=True); t.start()
# The separate observer selects the shared target window.
observer_window=observer.create_resource_object('window', win.id)
observer_window.change_attributes(event_mask=X.KeyPressMask|X.KeyReleaseMask)
owner.sync(); observer.sync()
xtest.fake_input(owner,X.KeyPress,detail=ka); owner.sync()
queue_start=time.monotonic_ns()
xtest.fake_input(owner,X.KeyPress,detail=kb,time=2000); owner.flush()
xtest.fake_input(owner,X.KeyRelease,detail=ka); owner.flush()
owner.sync(); delayed_sync_end=time.monotonic_ns()
xtest.fake_input(owner,X.KeyRelease,detail=kb); owner.sync(); time.sleep(.1)
stop.set(); t.join(timeout=1)
check=display.Display(); keymap=check.query_keymap(); a_down=bool(keymap[ka>>3]&(1<<(ka&7))); b_down=bool(keymap[kb>>3]&(1<<(kb&7)))
row={'global_auto_repeat':int(ctl.global_auto_repeat),'a_keycode':int(ka),'a_per_key_repeat_enabled':bool(ctl.auto_repeats[ka>>3]&amask),'b_keycode':int(kb),'delay_ms':2000,'delayed_sync_elapsed_ms':round((delayed_sync_end-queue_start)/1e6,2),'a_keypress_count':sum(e['detail']==ka and e['type']==X.KeyPress for e in events),'a_keyrelease_count':sum(e['detail']==ka and e['type']==X.KeyRelease for e in events),'b_keypress_count':sum(e['detail']==kb and e['type']==X.KeyPress for e in events),'events':events,'final_keymap':{'a_down':a_down,'b_down':b_down}}
print(json.dumps(row,sort_keys=True))
check.close(); observer.close(); win.destroy(); owner.sync(); owner.close()
