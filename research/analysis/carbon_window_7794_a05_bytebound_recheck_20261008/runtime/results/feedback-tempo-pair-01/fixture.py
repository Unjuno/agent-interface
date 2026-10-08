import json,sys,time,tkinter as tk
from pathlib import Path
from Xlib import display
out=Path(sys.argv[1]); mode=sys.argv[2]
r=tk.Tk();r.geometry('480x260+0+0');r.title('READY-1001072')
tk.Label(r,text='Save token t1001072; delayed acknowledgment').place(x=30,y=35)
c=tk.Canvas(r,width=480,height=180,highlightthickness=0,bg='white');c.place(x=0,y=70)
c.create_rectangle(290,70,430,135,fill='white',outline='black',width=2)
c.create_text(360,102,text='Save t1001072')
c.create_text(110,102,text='READY',tags='state')
def record(row):
    with (out/'events.jsonl').open('a') as f:f.write(json.dumps(dict(row,ns=time.monotonic_ns()))+'\n')
def finish():
    status='REJECTED' if mode=='rejected' else 'SAVED'
    r.title(status+'-1001072');c.itemconfigure('state',text=status)
    record({'event':'app_ack','status':status})
def click(e):
    if 290<=e.x<=430 and 70<=e.y<=135:
        record({'event':'save','token':'t1001072'})
        r.title('PENDING-1001072');c.itemconfigure('state',text='PENDING')
        r.after(3000,finish)
c.bind('<ButtonPress-1>',click);r.update();r.focus_force();r.update()
d=display.Display();window=d.create_resource_object('window',r.winfo_id()).query_tree().parent.id;d.close()
(out/'ready.json').write_text(json.dumps({'window':window}))
r.mainloop()
