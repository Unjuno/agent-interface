from __future__ import annotations
import argparse,json,sys,time,tkinter as tk
from pathlib import Path

ap=argparse.ArgumentParser(); ap.add_argument('--ready',required=True); ap.add_argument('--log',required=True); args=ap.parse_args()
ready=Path(args.ready); log=Path(args.log)
root=tk.Tk(); root.overrideredirect(True); root.geometry('320x240+0+0'); root.configure(bg='black')
cv=tk.Canvas(root,width=320,height=240,bg='black',highlightthickness=0); cv.pack(fill='both',expand=True)
rect=cv.create_rectangle(140,100,180,140,fill='#ff0000',outline='#ffffff')
root.update_idletasks(); root.update(); ready.write_text(str(time.perf_counter_ns()))

def record(row):
    with log.open('a') as f: f.write(json.dumps(row,sort_keys=True)+'\n')

def handle(line):
    cmd=json.loads(line); seq=int(cmd['seq']); phase=cmd['phase']; x=int(cmd['x']); authored=cmd.get('authored',{})
    cv.coords(rect,x,100,x+40,140); root.update_idletasks(); root.update()
    now=time.perf_counter_ns()
    row={'seq':seq,'phase':phase,'actual_x':x,'ack_ns':now,'authored':authored}
    record(row); print(json.dumps(row,sort_keys=True),flush=True)

for line in sys.stdin:
    if not line.strip(): continue
    cmd=json.loads(line)
    if cmd.get('op')=='close': break
    handle(line)
root.destroy()
