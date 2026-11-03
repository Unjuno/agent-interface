import json
import os
from pathlib import Path
import time
from Xlib import X, XK, display

out = Path(os.environ['TARGET_OUT'])
d = display.Display(os.environ['DISPLAY'])
w = d.screen().root.create_window(10, 10, 200, 120, 0, d.screen().root_depth,
    X.InputOutput, X.CopyFromParent, background_pixel=0x224466,
    event_mask=X.KeyPressMask | X.KeyReleaseMask | X.ExposureMask)
w.map()
d.sync()
gc = w.create_gc(foreground=0xeeeeee)
w.fill_rectangle(gc, 18, 18, 4, 4)
d.sync()
(out/'target-ready.json').write_text(json.dumps({'xid':w.id, 'pid':os.getpid()}))
events = []
count = 0
(out/'target-state.json').write_text(json.dumps({'count':count}))
end = time.monotonic()+25
while time.monotonic() < end and not (out/'target-stop').exists():
    while d.pending_events():
        event = d.next_event()
        if event.type == X.Expose:
            w.fill_rectangle(gc, 18, 18, 4, 4)
            d.sync()
        elif event.type in (X.KeyPress, X.KeyRelease):
            events.append({'type':'press' if event.type == X.KeyPress else 'release',
                           'key':XK.keysym_to_string(d.keycode_to_keysym(event.detail, 0)),
                           'ns':time.monotonic_ns()})
            if event.type == X.KeyPress and XK.keysym_to_string(d.keycode_to_keysym(event.detail, 0)) == 'a':
                count += 1
                state_tmp=out/'target-state.tmp'
                state_tmp.write_text(json.dumps({'count':count}))
                os.replace(state_tmp,out/'target-state.json')
            temporary=out/'target-events.tmp'
            temporary.write_text(json.dumps(events))
            os.replace(temporary,out/'target-events.json')
    time.sleep(.01)
d.close()

