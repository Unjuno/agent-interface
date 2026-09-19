import json, os, sys, time, tkinter as tk
out = sys.argv[1]
root = tk.Tk(); root.geometry('320x140+20+20'); root.title('safety-watchdog-receipt-recovery')
log=[]
def record(kind,e):
    log.append({'kind':kind,'keysym':e.keysym,'time_ns':time.monotonic_ns()})
    with open(out,'w') as f:
        json.dump(log,f,sort_keys=True); f.flush(); os.fsync(f.fileno())
root.bind('<KeyPress-F8>', lambda e: record('press',e))
root.bind('<KeyRelease-F8>', lambda e: record('release',e))
def ready():
    root.focus_force(); root.update_idletasks(); print(root.winfo_id(), flush=True)
root.after(80, ready)
root.mainloop()
