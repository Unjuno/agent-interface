import json, os, sys, time, tkinter as tk
from pathlib import Path
log_path=Path(sys.argv[1]); stop_path=Path(sys.argv[2])
root=tk.Tk(); root.geometry('240x120+20+20'); root.title('ai-exp4167')
entry=tk.Entry(root); entry.pack(fill='x', padx=20, pady=30); entry.focus_force(); root.update()
f=log_path.open('a', buffering=1)
def rec(kind, ev):
    f.write(json.dumps({'event':kind,'keysym':ev.keysym,'keycode':ev.keycode,'ts_ns':time.monotonic_ns()})+'\n')
entry.bind('<KeyPress>', lambda e: rec('KeyPress',e))
entry.bind('<KeyRelease>', lambda e: rec('KeyRelease',e))
print(json.dumps({'event':'READY','pid':os.getpid(),'xid':entry.winfo_id(),'ts_ns':time.monotonic_ns()}), flush=True)
def tick():
    if stop_path.exists():
        f.close(); root.destroy(); return
    root.after(2,tick)
root.after(2,tick); root.mainloop()
