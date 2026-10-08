import json, os, sys, time, tkinter as tk
from pathlib import Path

allocation, display, out_arg = sys.argv[1:4]
out = Path(out_arg).resolve()
if os.environ.get('DISPLAY') != display or out.exists():
    raise SystemExit(20)
root = tk.Tk(); root.title('5296-map'); root.geometry('420x180+80+70')
entry = tk.Entry(root, width=32); entry.pack(padx=12, pady=12)
events = {'Map': None, 'Configure': None}
def sample():
    return {'id': entry.winfo_id(), 'x': entry.winfo_rootx(), 'y': entry.winfo_rooty(),
      'w': entry.winfo_width(), 'h': entry.winfo_height(), 'mapped': entry.winfo_ismapped(),
      'root': [root.winfo_rootx(), root.winfo_rooty(), root.winfo_width(), root.winfo_height()],
      't': time.monotonic_ns()}
raw = {'schema':'tk-map-barrier-v1','allocation':allocation,
       'pre':sample()}
entry.bind('<Map>', lambda e: events.__setitem__('Map', time.monotonic_ns()), add='+')
entry.bind('<Configure>', lambda e: events.__setitem__('Configure', time.monotonic_ns()), add='+')
def poll(deadline):
    if all(v is not None for v in events.values()):
        raw.update(events=events, post=sample(), app_exit=0); root.destroy()
    elif time.monotonic_ns() >= deadline:
        raw.update(events=events, post=sample(), app_exit=20); root.destroy()
    else: root.after(10, poll, deadline)
root.after(0, poll, time.monotonic_ns()+2_000_000_000); root.mainloop()
out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps(raw, sort_keys=True)+'\n')
print(json.dumps({'rows':1,'app_exit':raw['app_exit'],'output':str(out)})); raise SystemExit(raw['app_exit'])
