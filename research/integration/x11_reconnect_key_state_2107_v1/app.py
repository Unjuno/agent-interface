#!/usr/bin/env python3
import json, os, sys, time, tkinter as tk
from pathlib import Path
out=Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
state=out/'state.json'; events=out/'app_events.jsonl'
root=tk.Tk(); root.geometry('360x120+40+40'); root.title('reconnect-key-state')
var=tk.StringVar(value='')
ent=tk.Entry(root,textvariable=var,font=('TkFixedFont',18)); ent.pack(fill='both',expand=True,padx=10,pady=10)
def atomic(path,obj):
    tmp=path.with_suffix(path.suffix+'.tmp'); tmp.write_text(json.dumps(obj,sort_keys=True)); os.replace(tmp,path)
def snap(reason):
    root.update_idletasks(); atomic(state, {'pid':os.getpid(),'root_xid':root.winfo_id(),'entry_xid':ent.winfo_id(),'value':var.get(),'focus_widget':str(root.focus_get()),'reason':reason,'mono_ns':time.monotonic_ns()})
def ev(kind,e):
    rec={'kind':kind,'keysym':e.keysym,'keycode':e.keycode,'state':e.state,'time':e.time,'mono_ns':time.monotonic_ns(),'value':var.get()}
    with events.open('a') as f: f.write(json.dumps(rec,sort_keys=True)+'\n')
    root.after_idle(lambda:snap('event'))
ent.bind('<KeyPress>',lambda e:ev('KeyPress',e), add='+')
ent.bind('<KeyRelease>',lambda e:ev('KeyRelease',e), add='+')
var.trace_add('write',lambda *_:root.after_idle(lambda:snap('trace')))
root.after(100, lambda:(ent.focus_force(), snap('ready')))
root.protocol('WM_DELETE_WINDOW',root.destroy)
try: root.mainloop()
finally:
    try: snap('closing')
    except Exception: pass
