"""Private Tk Entry observer: no command inserts or clears task text."""
import json
import os
import sys
import time
import tkinter as tk

root = tk.Tk()
root.geometry('360x100+0+0')
value = tk.StringVar()
entry = tk.Entry(root, textvariable=value, width=24)
entry.pack(padx=8, pady=8)
events = []
changes = []


def key(event):
    events.append({'kind': str(event.type), 'keycode': event.keycode,
                   'keysym': event.keysym, 'char': event.char, 'state': event.state,
                   'ns': time.monotonic_ns()})


entry.bind('<KeyPress>', key, add='+')
entry.bind('<KeyRelease>', key, add='+')
value.trace_add('write', lambda *_: changes.append({'value': value.get(), 'ns': time.monotonic_ns()}))


def reply(tag):
    print(json.dumps({'tag': tag, 'pid': os.getpid(), 'ns': time.monotonic_ns(),
                      'entry': entry.winfo_id(), 'root': root.winfo_id(),
                      'value': value.get(), 'events': events, 'changes': changes,
                      'tk': root.tk.call('info', 'patchlevel')}, sort_keys=True), flush=True)
    if tag == 'finish':
        root.quit()


def command(_fd, _mask):
    line = sys.stdin.readline()
    if not line:
        root.quit()
        return
    row = json.loads(line)
    if set(row) != {'op'} or row['op'] not in ('snapshot', 'finish'):
        raise ValueError('unsupported app command')
    # Diagnostic settling only; no latency claim. Ordinary Tk event processing continues.
    root.after(25, reply, row['op'])


root.createfilehandler(sys.stdin, tk.READABLE, command)
root.update_idletasks()
entry.focus_force()
root.after(50, reply, 'ready')
root.mainloop()
root.destroy()
