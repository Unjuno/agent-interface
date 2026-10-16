#!/usr/bin/env python3
import json, os, select, sys, time, tkinter as tk
root=tk.Tk()
root.geometry('300x120+5+5')
root.title('INIT')
value=tk.StringVar(value='INIT')
label=tk.Label(root,textvariable=value,font=('TkDefaultFont',20))
label.pack(expand=True,fill='both')
root.update()
print(json.dumps({'kind':'ready','xid':root.winfo_id(),'pid':os.getpid(),'mono_ns':time.monotonic_ns()}),flush=True)
while True:
    root.update()
    r,_,_=select.select([sys.stdin],[],[],0.01)
    if not r:
        continue
    line=sys.stdin.readline()
    if not line:
        break
    cmd=json.loads(line)
    op=cmd['op']
    if op=='set':
        text=f"{cmd['epoch']}:{cmd['phase']}:{cmd.get('tag',0)}"
        value.set(text); root.title(text); root.update_idletasks(); root.update()
        print(json.dumps({'kind':'set_ack','text':text,'mono_ns':time.monotonic_ns()}),flush=True)
    elif op=='snapshot':
        root.update()
        print(json.dumps({'kind':'snapshot','text':value.get(),'title':root.title(),'xid':root.winfo_id(),'mono_ns':time.monotonic_ns()}),flush=True)
    elif op=='close':
        print(json.dumps({'kind':'closing','mono_ns':time.monotonic_ns()}),flush=True)
        root.destroy(); break
    else:
        raise SystemExit('bad op')
