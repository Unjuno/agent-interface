"""Private deterministic X11 surface. All state changes are explicit DRAW commands."""
import json
import os
import sys
import time
from Xlib import X, display


def emit(value):
    print(json.dumps(value, sort_keys=True), flush=True)


def main():
    d = display.Display()
    s = d.screen()
    win = s.root.create_window(1, 1, 64, 48, 0, s.root_depth, X.InputOutput,
                               X.CopyFromParent, background_pixel=0,
                               override_redirect=1,
                               event_mask=X.KeyPressMask | X.KeyReleaseMask |
                               X.ButtonPressMask | X.ButtonReleaseMask)
    gc = win.create_gc()
    win.map()
    d.sync()
    state, inputs = 0, []
    emit({'kind': 'READY', 'pid': os.getpid(), 'surface': win.id})
    for line in sys.stdin:
        cmd = json.loads(line)
        if cmd['op'] == 'DRAW':
            state = cmd['state']
            gc.change(foreground=state * 0x111111)
            win.fill_rectangle(gc, 0, 0, 64, 48)
            gc.change(foreground=state * 0x220000)
            win.fill_rectangle(gc, 32, 8, 16, 16)
        d.sync()
        while d.pending_events():
            e = d.next_event()
            inputs.append({'type': e.type, 'detail': int(e.detail)})
        emit({'kind': cmd['op'], 'state': state, 'input_events': inputs[:],
              'surface': win.id, 'at_ns': time.monotonic_ns()})
        if cmd['op'] == 'CLOSE':
            break
    gc.free()
    win.destroy()
    d.sync()
    d.close()


if __name__ == '__main__':
    main()
