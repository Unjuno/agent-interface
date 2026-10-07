"""Private controlled review stimulus; no model access, Save or recovery."""
import json
import os
from pathlib import Path
import sys
import time
import tkinter as tk
out=Path(sys.argv[1]);case=json.loads(sys.argv[2]);token=sys.argv[3]
root=tk.Tk();root.title('Private text review');root.geometry(case['geometry'])
font=('DejaVu Sans',22)
tk.Label(root,text='Requested text: '+case['wanted'],font=font).pack(pady=12)
tk.Label(root,text='DECOY',font=('DejaVu Sans',14)).pack()
decoy=tk.Entry(root,font=font,width=18);decoy.pack()
tk.Label(root,text='TARGET',font=('DejaVu Sans',14)).pack()
target=tk.Entry(root,font=font,width=18);target.pack()
tk.Label(root,text='Review only - no automatic repair',font=('DejaVu Sans',12)).pack(pady=10)
events=[];started=time.monotonic_ns()
def mark(kind,widget,event=None):
    events.append(dict(kind=kind,widget=widget,char=getattr(event,'char',''),ns=time.monotonic_ns()))
for name,widget in (('target',target),('decoy',decoy)):
    widget.bind('<KeyPress>',lambda e,n=name:mark('KeyPress',n,e))
    widget.bind('<FocusIn>',lambda e,n=name:mark('FocusIn',n,e))
    widget.bind('<FocusOut>',lambda e,n=name:mark('FocusOut',n,e))
def ready():
    root.focus_force();decoy.focus_set();root.update_idletasks()
    def geometry(w):return dict(x=w.winfo_rootx(),y=w.winfo_rooty(),width=w.winfo_width(),height=w.winfo_height(),id=w.winfo_id())
    data=dict(token=token,pid=os.getpid(),root=geometry(root),target=geometry(target),decoy=geometry(decoy),ready_ns=time.monotonic_ns())
    (out/'ready.json').write_text(json.dumps(data),encoding='utf-8')
    poll()
def poll():
    if (out/'finish.flag').exists():
        value=dict(token=token,pid=os.getpid(),started_ns=started,ended_ns=time.monotonic_ns(),target=target.get(),decoy=decoy.get(),events=events,save_count=0)
        (out/'app_result.json').write_text(json.dumps(value),encoding='utf-8')
        print(json.dumps(value),flush=True);root.destroy()
    elif time.monotonic_ns()-started>8_000_000_000:
        raise RuntimeError('construction/row deadline')
    else:root.after(10,poll)
root.after(150,ready);root.mainloop()
