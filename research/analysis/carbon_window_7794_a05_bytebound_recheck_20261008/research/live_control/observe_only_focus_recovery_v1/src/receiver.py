import json, os, sys, tkinter as tk
from pathlib import Path
out=Path(sys.argv[1]); out.mkdir(parents=True,exist_ok=True)
root=tk.Tk(); root.title('TASK_A'); root.geometry('260x160+80+80')
b=tk.Toplevel(root); b.title('OTHER_B'); b.geometry('260x160+420+80')
for w,name in [(root,'A'),(b,'B')]:
    lab=tk.Label(w,text=name,font=('Sans',30)); lab.pack(expand=True,fill='both')
    for ev in ('<KeyPress>','<KeyRelease>','<ButtonPress>','<ButtonRelease>'):
        w.bind_all(ev, lambda e, ev=ev: (out/'events.jsonl').open('a').write(json.dumps({'event':ev,'keysym':getattr(e,'keysym',None),'num':getattr(e,'num',None)})+'\n'))
root.update_idletasks(); root.update()
(out/'windows.json').write_text(json.dumps({'A':root.winfo_id(),'B':b.winfo_id()}))
(out/'ready').write_text('ok')
try: root.mainloop()
finally: pass
