#!/usr/bin/env python3
import json, sys, time
from Xlib import display, X, XK
from Xlib.ext import xtest
mode=sys.argv[1]
if mode not in ('baseline','global_off','key_off'):
    raise SystemExit(2)
d=display.Display(); screen=d.screen(); root=screen.root
key=d.keysym_to_keycode(XK.string_to_keysym('a'))
if mode=='global_off':
    d.change_keyboard_control(auto_repeat_mode=X.AutoRepeatModeOff)
elif mode=='key_off':
    d.change_keyboard_control(key=key, auto_repeat_mode=X.AutoRepeatModeOff)
d.sync(); control=d.get_keyboard_control()
window=root.create_window(0,0,160,80,0,screen.root_depth,X.InputOutput,
                          X.CopyFromParent,event_mask=(X.KeyPressMask|X.KeyReleaseMask))
window.map(); d.sync(); window.set_input_focus(X.RevertToParent,X.CurrentTime); d.sync()
# Drain map/focus notifications before the single measured input.
while d.pending_events(): d.next_event()
xtest.fake_input(d,X.KeyPress,detail=key); d.sync(); time.sleep(1.2)
xtest.fake_input(d,X.KeyRelease,detail=key); d.sync(); time.sleep(.1)
events=[]
while d.pending_events():
    e=d.next_event()
    if getattr(e,'detail',None)==key and e.type in (X.KeyPress,X.KeyRelease):
        events.append({'type':int(e.type),'time':int(e.time)})
reader=display.Display(); keymap=reader.query_keymap(); down=bool(keymap[key>>3] & (1<<(key&7)))
mask=1<<(key&7)
row={'mode':mode,'keycode':int(key),'global_auto_repeat':int(control.global_auto_repeat),
     'per_key_repeat_enabled':bool(control.auto_repeats[key>>3]&mask),
     'hold_ms':1200,'keypress_count':sum(e['type']==X.KeyPress for e in events),
     'keyrelease_count':sum(e['type']==X.KeyRelease for e in events),
     'events':events,'independent_keymap_down_after_release':down}
print(json.dumps(row,sort_keys=True))
reader.close(); window.destroy(); d.sync(); d.close()