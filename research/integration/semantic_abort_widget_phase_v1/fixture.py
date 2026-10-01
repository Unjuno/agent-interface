"""Private application fixture. Only standard widget bindings cause effects."""
import argparse
import json
import os
from pathlib import Path
import sys
import time
import tkinter as tk
from tkinter import ttk


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--kind', choices=['button', 'scale'], required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--session', required=True)
    a = p.parse_args()
    events = (a.out / 'app_events.jsonl').open('x', encoding='utf-8')
    effects = (a.out / 'effects.jsonl').open('x', encoding='utf-8')
    root = tk.Tk()
    root.geometry('640x360+0+0')
    root.title(a.session)
    root.resizable(False, False)
    state = {'effect_count': 0, 'button_value': 0, 'presses': 0, 'releases': 0}

    def journal(f, row):
        row = dict(row, session=a.session, pid=os.getpid(), mono_ns=time.monotonic_ns())
        f.write(json.dumps(row, sort_keys=True) + '\n')
        f.flush()
        os.fsync(f.fileno())

    def effect(value=None):
        state['effect_count'] += 1
        if a.kind == 'button':
            state['button_value'] += 1
            value = state['button_value']
        else:
            value = float(value)
        journal(effects, {'event': 'effect', 'index': state['effect_count'], 'value': value})

    if a.kind == 'button':
        widget = ttk.Button(root, text='Apply', command=effect)
        widget.place(x=80, y=70, width=240, height=60)
    else:
        widget = tk.Scale(root, from_=0, to=100, orient='horizontal',
                          showvalue=False, resolution=1, repeatdelay=100000,
                          repeatinterval=100000, sliderlength=30)
        widget.place(x=80, y=130, width=400, height=60)
        widget.set(0)  # Initial condition only; no programmatic changes after ready.
    root.update()
    if a.kind == 'scale':
        widget.configure(command=effect)

    def event_record(e, name):
        if name == 'press':
            state['presses'] += 1
        if name == 'release':
            state['releases'] += 1
        journal(events, {'event': name, 'x': e.x, 'y': e.y, 'state': e.state,
                         'server_time_ms': e.time, 'serial': e.serial})

    for seq, name in [('<ButtonPress-1>', 'press'), ('<ButtonRelease-1>', 'release'),
                      ('<Enter>', 'enter'), ('<Leave>', 'leave'), ('<Motion>', 'motion')]:
        widget.bind(seq, lambda e, n=name: event_record(e, n), add='+')
    root.lift()
    root.focus_force()
    root.update()
    geo = [widget.winfo_rootx(), widget.winfo_rooty(), widget.winfo_width(), widget.winfo_height()]
    local = [geo[2] // 2, geo[3] // 2] if a.kind == 'button' else list(widget.coords(75))
    klass = widget.winfo_class()
    binding_sequences = root.tk.splitlist(root.tk.call('bind', klass))
    bindings = {s: str(root.tk.call('bind', klass, s)) for s in binding_sequences}
    receipt = {'session': a.session, 'epoch': 1, 'widget_class': klass,
               'widget_xid': widget.winfo_id(), 'root_xid': root.winfo_id(),
               'recipe': 'MOVE_AWAY_CANCEL', 'abort_without_effect': a.kind == 'button'}
    ready = {'event': 'ready', 'session': a.session, 'pid': os.getpid(), 'kind': a.kind,
             'geometry': geo, 'point': [geo[0] + local[0], geo[1] + local[1]],
             'point_method': 'widget_center' if a.kind == 'button' else 'read_only_scale_coords_75',
             'away': [560, 300], 'identified_part': str(widget.identify(*local)),
             'tk_patchlevel': str(root.tk.call('info', 'patchlevel')),
             'theme': ttk.Style().theme_use(), 'bindtags': list(widget.bindtags()),
             'class_bindings': bindings, 'receipt': receipt, 'baseline_value': 0}

    def respond(row):
        print(json.dumps(dict(row, session=a.session, pid=os.getpid(),
                              mono_ns=time.monotonic_ns()), sort_keys=True), flush=True)

    def snapshot(req):
        respond({'event': 'snapshot', 'request_id': req['id'], **state,
                 'value': state['button_value'] if a.kind == 'button' else widget.get()})

    def read_command(fd, mask):
        line = sys.stdin.readline()
        if not line:
            root.destroy()
            return
        req = json.loads(line)
        if req['op'] == 'snapshot':
            root.after(20, lambda: snapshot(req))
        elif req['op'] == 'close':
            respond({'event': 'closing', 'request_id': req['id'], **state})
            root.after_idle(root.destroy)
        else:
            raise ValueError('unsupported read-only command')

    root.createfilehandler(sys.stdin, tk.READABLE, read_command)
    respond(ready)
    try:
        root.mainloop()
    finally:
        events.close()
        effects.close()


if __name__ == '__main__':
    main()
