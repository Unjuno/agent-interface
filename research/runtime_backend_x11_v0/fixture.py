#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, time
from pathlib import Path
from Xlib import X, XK, display


def dump_line(path: Path, row: dict) -> None:
    with path.open('a', encoding='utf-8', newline='\n') as f:
        f.write(json.dumps(row, sort_keys=True) + '\n')
        f.flush()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--display', required=True)
    ap.add_argument('--events', type=Path, required=True)
    args = ap.parse_args()
    args.events.parent.mkdir(parents=True, exist_ok=True)
    d = display.Display(args.display)
    root = d.screen().root
    win = root.create_window(
        80, 90, 360, 240, 0, d.screen().root_depth,
        X.InputOutput, X.CopyFromParent,
        background_pixel=d.screen().white_pixel,
        event_mask=(X.ExposureMask | X.KeyPressMask | X.KeyReleaseMask |
                    X.ButtonPressMask | X.ButtonReleaseMask | X.PointerMotionMask |
                    X.FocusChangeMask),
    )
    gc = win.create_gc(foreground=d.screen().black_pixel, background=d.screen().white_pixel)
    win.set_wm_name('agent-interface-x11-fixture')
    win.map()
    d.sync()
    print(json.dumps({'window_id': win.id, 'width': 360, 'height': 240}), flush=True)
    effect_count = 0
    running = True
    while running:
        event = d.next_event()
        now = time.monotonic_ns()
        row = {'monotonic_ns': now, 'type': event.__class__.__name__}
        if event.type in (X.KeyPress, X.KeyRelease):
            keysym = d.keycode_to_keysym(event.detail, 0)
            row.update({'kind': 'key_press' if event.type == X.KeyPress else 'key_release',
                        'keycode': event.detail,
                        'keysym': ({65507:'Control_L',65505:'Shift_L',65513:'Alt_L'}.get(keysym) or XK.keysym_to_string(keysym) or str(keysym))})
            if event.type == X.KeyPress:
                effect_count += 1
        elif event.type in (X.ButtonPress, X.ButtonRelease):
            row.update({'kind': 'button_press' if event.type == X.ButtonPress else 'button_release',
                        'button': event.detail, 'x': event.event_x, 'y': event.event_y})
            if event.type == X.ButtonPress:
                effect_count += 1
        elif event.type == X.MotionNotify:
            row.update({'kind': 'motion', 'x': event.event_x, 'y': event.event_y})
        elif event.type == X.FocusIn:
            row['kind'] = 'focus_in'
        elif event.type == X.FocusOut:
            row['kind'] = 'focus_out'
        elif event.type == X.Expose:
            row['kind'] = 'expose'
        else:
            row['kind'] = 'other'
        if row['kind'] != 'expose':
            dump_line(args.events, row)
        # Paint a deterministic visible marker after delivered press effects.
        if row['kind'] in {'key_press', 'button_press'}:
            x = 10 + (effect_count * 17) % 300
            y = 10 + (effect_count * 23) % 180
            win.fill_rectangle(gc, x, y, 12, 12)
            d.flush()
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
