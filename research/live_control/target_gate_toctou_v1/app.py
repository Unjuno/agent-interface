from __future__ import annotations
import argparse, json, time, tkinter as tk
from pathlib import Path

p=argparse.ArgumentParser(); p.add_argument('--control',required=True); p.add_argument('--ready',required=True); p.add_argument('--mutated',required=True); p.add_argument('--events',required=True)
a=p.parse_args(); control=Path(a.control); ready=Path(a.ready); mutated=Path(a.mutated); events=Path(a.events)
root=tk.Tk(); root.title('TOCTOU Fixture'); root.geometry('420x260+80+70'); root.configure(bg='white')
canvas=tk.Canvas(root,width=400,height=220,bg='white',highlightthickness=0); canvas.pack(padx=10,pady=10)
A=(120,110); B=(280,110); R=34
roles={'A':'task-target','B':'decoy'}; colors={'task-target':'#f000b0','decoy':'#00d8e8'}; items={}

def draw():
    for key,(x,y) in [('A',A),('B',B)]:
        if key in items: canvas.delete(items[key])
        items[key]=canvas.create_oval(x-R,y-R,x+R,y+R,fill=colors[roles[key]],outline='#202020',width=2)
    root.update_idletasks()

def emit(obj):
    with events.open('a') as f: f.write(json.dumps(obj,sort_keys=True)+'\n')

def on_click(ev):
    slot=None
    for key,(x,y) in [('A',A),('B',B)]:
        if (ev.x-x)**2+(ev.y-y)**2 <= R**2: slot=key; break
    emit({'event':'click','time_ns':time.perf_counter_ns(),'slot':slot,'role':roles.get(slot) if slot else None,'x':ev.x,'y':ev.y})
canvas.bind('<Button-1>',on_click)
draw(); root.update(); root.focus_force(); root.update()
ready.write_text(json.dumps({'time_ns':time.perf_counter_ns(),'window_id':root.winfo_id(),'canvas_root_x':canvas.winfo_rootx(),'canvas_root_y':canvas.winfo_rooty(),'A':[canvas.winfo_rootx()+A[0],canvas.winfo_rooty()+A[1]],'B':[canvas.winfo_rootx()+B[0],canvas.winfo_rooty()+B[1]],'roles':roles},sort_keys=True))

def poll():
    if control.exists() and control.read_text().strip()=='swap' and not mutated.exists():
        roles['A'],roles['B']=roles['B'],roles['A']; draw(); root.update_idletasks(); root.update()
        t=time.perf_counter_ns(); emit({'event':'mutation','time_ns':t,'roles':dict(roles)}); mutated.write_text(json.dumps({'time_ns':t,'roles':roles},sort_keys=True))
    root.after(5,poll)
root.after(5,poll); root.mainloop()
