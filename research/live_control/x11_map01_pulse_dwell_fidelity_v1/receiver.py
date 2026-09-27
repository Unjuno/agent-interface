import json, os, pathlib, time, tkinter as tk

out = pathlib.Path(os.environ['OUT'])
root = tk.Tk()
root.geometry('320x120+20+20')
root.title('x11-pulse-dwell-receiver')
records = []

def record(kind, event):
    records.append({
        'kind': kind,
        'keysym': event.keysym,
        'keycode': int(event.keycode),
        'x_time_ms': int(event.time),
        'callback_ns': time.monotonic_ns(),
    })

root.bind('<KeyPress>', lambda e: record('press', e))
root.bind('<KeyRelease>', lambda e: record('release', e))
root.update_idletasks()
root.update()
root.focus_force()
root.update()
(out / 'window_id.txt').write_text(str(root.winfo_id()) + '\n')

def dump():
    (out / 'events.json').write_text(json.dumps(records, indent=2, sort_keys=True) + '\n')
    root.after(20, dump)

def ready():
    (out / 'ready').write_text('event-loop-active\n')

root.after(50, ready)
root.after(20, dump)
root.mainloop()
