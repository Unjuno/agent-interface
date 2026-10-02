import json, sys, tkinter as tk
from pathlib import Path
from Xlib import display
out=Path(sys.argv[1]); token=sys.argv[2]; changed=sys.argv[3]=='changed'
r=tk.Tk(); r.geometry('480x260+0+0'); r.title('Compiled GUI private fixture')
tk.Label(r,text='Value: enter '+token).place(x=40,y=35)
v=tk.StringVar(); e=tk.Entry(r,textvariable=v); e.place(x=40,y=75,width=390,height=40)
c=tk.Canvas(r,width=480,height=100,highlightthickness=0,bg='white'); c.place(x=0,y=140)
c.create_rectangle(40,12,160,65,fill='#5064b4',outline='black',tags='badge')
c.create_text(100,38,text='EMPTY',fill='white',tags='state')
c.create_rectangle(290,12,430,65,fill='white',outline='black',width=2,tags='save')
c.create_text(360,38,text='Save',fill='black',tags='save_label')
saved=False
(out/'events.jsonl').write_text('')
def record(row):
    with (out/'events.jsonl').open('a') as f: f.write(json.dumps(row)+'\n')
def updated(*args):
    if saved: return
    valid=v.get()==token
    c.itemconfigure('badge',fill='#28b43c' if valid else '#5064b4')
    c.itemconfigure('state',text='ACCEPTED' if valid else 'EMPTY')
    record({'event':'value_changed','value':v.get()})
    if changed and valid:
        c.itemconfigure('save',fill='#a00000'); c.itemconfigure('save_label',text='Removed',fill='white')
def click(event):
    global saved
    if 290<=event.x<=430 and 12<=event.y<=65:
        record({'event':'save','value':v.get(),'eligible':not changed and v.get()==token})
        if not changed and v.get()==token:
            saved=True; c.itemconfigure('badge',fill='#1e6e3c'); c.itemconfigure('state',text='SAVED')
v.trace_add('write',updated); c.bind('<ButtonPress-1>',click)
r.update(); r.focus_force(); e.focus_set(); r.update()
d=display.Display(); window=d.create_resource_object('window',r.winfo_id()).query_tree().parent.id; d.close()
(out/'ready.json').write_text(json.dumps({'window':window}))
r.mainloop()
