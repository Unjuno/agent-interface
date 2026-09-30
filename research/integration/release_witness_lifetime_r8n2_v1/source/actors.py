"""Cooperative private-X11 recipient and read-only single-key witness."""
from __future__ import annotations
import argparse
import json
import os
import select
import sys
import time
from pathlib import Path
from Xlib import X, XK, display


def run() -> None:
    p = argparse.ArgumentParser()
    p.add_argument('role', choices=['recipient', 'witness'])
    p.add_argument('directory')
    p.add_argument('epoch')
    p.add_argument('actuation')
    a = p.parse_args()
    d = display.Display()
    out = Path(a.directory)
    log = (out / (a.role + '.jsonl')).open('x', encoding='utf-8')
    seq = 0
    key = d.keysym_to_keycode(XK.string_to_keysym('F8'))
    win = None
    events: list[dict] = []
    if a.role == 'recipient':
        win = d.screen().root.create_window(20, 20, 160, 100, 0,
            d.screen().root_depth, X.InputOutput, X.CopyFromParent,
            background_pixel=0x335577,
            event_mask=X.KeyPressMask | X.KeyReleaseMask | X.StructureNotifyMask | X.FocusChangeMask)
        win.set_wm_name('ReleaseWitness-' + a.epoch)
        win.map()
        d.sync()
    identity = dict(epoch=a.epoch, actuation=a.actuation, pid=os.getpid(), keycode=key)

    def record(kind: str, **extra) -> dict:
        nonlocal seq
        seq += 1
        row = dict(identity, seq=seq, kind=kind, time_ns=time.monotonic_ns(), **extra)
        log.write(json.dumps(row, sort_keys=True) + '\n')
        log.flush()
        return row

    def send(row: dict) -> None:
        print(json.dumps(row, sort_keys=True), flush=True)

    def drain() -> None:
        while d.pending_events():
            e = d.next_event()
            if e.type in (X.KeyPress, X.KeyRelease):
                events.append(record('key_event', event_type=int(e.type),
                    event_keycode=int(e.detail), server_time_ms=int(e.time),
                    window=int(e.window.id), send_event=bool(e.send_event)))
            elif e.type in (X.DestroyNotify, X.FocusIn, X.FocusOut, X.MapNotify):
                record('lifecycle', event_type=int(e.type), window=int(e.window.id))

    send(record('ready', window=win.id if win else None))
    try:
        while True:
            drain()
            ready, _, _ = select.select([sys.stdin, d.fileno()], [], [], 2)
            if sys.stdin not in ready:
                continue
            line = sys.stdin.readline()
            if not line:
                break
            request = json.loads(line)
            record('request', request=request)
            cmd = request['command']
            if cmd == 'exit':
                send(record('exit_ack', request_id=request['id']))
                break
            if cmd == 'sample' and a.role == 'witness':
                start = time.monotonic_ns()
                keymap = list(d.query_keymap())
                end = time.monotonic_ns()
                send(record('sample', request_id=request['id'],
                    query_start_ns=start, query_end_ns=end,
                    key_down=bool(keymap[key // 8] & (1 << (key % 8))),
                    keymap=keymap))
            elif cmd == 'snapshot' and a.role == 'recipient':
                d.sync()
                drain()
                send(record('snapshot', request_id=request['id'], events=list(events),
                    window_alive=win is not None))
            elif cmd == 'destroy' and a.role == 'recipient' and win is not None:
                start = time.monotonic_ns()
                wid = win.id
                win.destroy()
                d.sync()
                win = None
                drain()
                send(record('destroyed', request_id=request['id'], window=wid,
                    destroy_start_ns=start, destroy_end_ns=time.monotonic_ns()))
            else:
                raise ValueError('unsupported cooperative command')
    finally:
        d.close()
        record('closed')
        log.close()


if __name__ == '__main__':
    run()
