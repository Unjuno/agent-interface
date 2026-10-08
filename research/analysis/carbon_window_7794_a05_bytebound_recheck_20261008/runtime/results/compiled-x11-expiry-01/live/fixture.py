import tkinter as tk, json, sys
from pathlib import Path
p=Path(sys.argv[1]); r=tk.Tk(); r.geometry('420x220+0+0'); r.title('Deadline fixture')
e=tk.Entry(r); e.place(x=40,y=80,width=320,height=40)
def event(ev):
    with (p/'events.jsonl').open('a') as f: f.write(json.dumps({'type':ev.type.name,'keysym':getattr(ev,'keysym',None)})+'\n')
e.bind('<ButtonPress>',event); e.bind('<KeyPress>',event)
r.update(); e.focus_force(); r.update()
(p/'ready.json').write_text(json.dumps({'window':r.winfo_id(),'point':[200,100]}))
r.mainloop()
