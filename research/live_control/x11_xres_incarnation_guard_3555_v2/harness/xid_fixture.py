from __future__ import annotations

import os
from pathlib import Path
import time

from Xlib import X, display


TARGET_GEOMETRY = (80, 80, 240, 160)
EFFECT_ATOM = "OBSTAC_EFFECT_LOG"


def process_start_ticks(pid: int) -> str:
    fields = Path(f"/proc/{pid}/stat").read_text(encoding="ascii").split()
    return fields[21]


def fixture(conn, stop):
    """One shared construction/formal app fixture; map before drawing."""
    d = display.Display()
    screen = d.screen()
    root = screen.root
    x, y, width, height = TARGET_GEOMETRY
    window = root.create_window(
        x, y, width, height, 0, screen.root_depth, X.InputOutput,
        X.CopyFromParent, background_pixel=0xeeeeee,
        event_mask=X.ExposureMask | X.ButtonPressMask,
    )
    window.set_wm_name("OBSTAC-XID-fixture")
    effect_atom = d.intern_atom(EFFECT_ATOM)
    card = d.intern_atom("CARDINAL")
    window.change_property(effect_atom, card, 32, [0, 0, 0])
    window.map()
    d.sync()

    gc = window.create_gc(foreground=0x152b42)
    window.fill_rectangle(gc, 17, 19, 24, 38)
    gc.change(foreground=0xe58b31)
    window.fill_rectangle(gc, 20, 22, 7, 6)
    gc.change(foreground=0x368b65)
    window.fill_rectangle(gc, 32, 41, 5, 11)
    gc.change(foreground=0x243b52)
    window.fill_rectangle(gc, 120, 19, 24, 38)
    gc.change(foreground=0xd35454)
    window.fill_rectangle(gc, 123, 22, 9, 5)
    gc.change(foreground=0xe0c45a)
    window.fill_rectangle(gc, 137, 37, 4, 15)
    window.set_input_focus(X.RevertToParent, X.CurrentTime)
    d.sync()

    conn.send({"pid": os.getpid(), "pid_start_ticks": process_start_ticks(os.getpid()),
               "xid": window.id, "geometry": list(TARGET_GEOMETRY)})
    count = 0
    while not stop.is_set():
        if d.pending_events():
            event = d.next_event()
            if event.type == X.ButtonPress:
                count += 1
                window.change_property(effect_atom, card, 32,
                                       [count, int(event.root_x), int(event.root_y)])
                d.sync()
        else:
            time.sleep(0.002)
    window.destroy()
    d.sync()
    d.close()
