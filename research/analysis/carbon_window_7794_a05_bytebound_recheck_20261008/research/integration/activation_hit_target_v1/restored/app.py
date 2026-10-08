"""Cooperative private fixture. Input effects use ordinary Tk class bindings."""
import json,os,sys,time,tkinter as tk
from pathlib import Path
ROOT=Path(sys.argv[1]); SESSION=sys.argv[2]
root=tk.Tk(); root.title('Private activation observation'); root.geometry('560x300+20+20'); root.overrideredirect(True)
root.configure(background='#dddddd')
va=tk.StringVar(); vb=tk.StringVar(); count=0; serial=0; journal=[]
a=tk.Entry(root,name='a',textvariable=va,exportselection=False,font=('TkFixedFont',14)); a.place(x=40,y=40,width=200,height=40)
b=tk.Entry(root,name='b',textvariable=vb,exportselection=False,font=('TkFixedFont',14)); b.place(x=40,y=120,width=200,height=40)
marker=tk.Frame(root,name='marker',background='#112233'); marker.place(x=480,y=40,width=20,height=20)
status=tk.Label(root,name='status',text='counter=0'); status.place(x=350,y=110,width=170,height=30)
logfile=(ROOT/'app-events.jsonl').open('x')
def write(row):
    global serial
    serial+=1; row=dict(row,seq=serial,monotonic_ns=time.monotonic_ns(),session=SESSION)
    journal.append(row); logfile.write(json.dumps(row,sort_keys=True)+'\n'); logfile.flush()
def clicked():
    global count
    count+=1; marker.configure(background='#55aa33'); status.configure(text=f'counter={count}')
    write({'kind':'callback','widget':'.cover','counter':count,'a':va.get(),'b':vb.get()})
cover=tk.Button(root,name='cover',text='local counter',command=clicked,takefocus=False)
for var,name in ((va,'a'),(vb,'b')):
    var.trace_add('write',lambda *_,v=var,n=name:write({'kind':'value','field':n,'value':v.get()}))
def event(e):
    write({'kind':'native','event':str(e.type),'widget':str(e.widget),'xid':e.widget.winfo_id(),
           'keysym':str(e.keysym),'keycode':str(e.keycode),'num':str(e.num),
           'server_time':str(e.time),'a':va.get(),'b':vb.get(),'counter':count})
for pat in ('<ButtonPress>','<ButtonRelease>','<KeyPress>','<KeyRelease>','<FocusIn>','<FocusOut>','<Enter>','<Leave>'):
    root.bind_all(pat,event,add='+')
def snapshot():
    root.update_idletasks(); f=root.focus_get(); x=a.winfo_rootx()+a.winfo_width()//2; y=a.winfo_rooty()+a.winfo_height()//2
    hit=root.winfo_containing(x,y)
    return {'session':SESSION,'pid':os.getpid(),'captured_ns':time.monotonic_ns(),'a':va.get(),'b':vb.get(),
        'counter':count,'focus':f.winfo_id() if f else None,'focus_path':str(f) if f else None,
        'hit':hit.winfo_id() if hit else None,'hit_path':str(hit) if hit else None,
        'ids':{'root':root.winfo_id(),'a':a.winfo_id(),'b':b.winfo_id(),'cover':cover.winfo_id()},
        'geometry':{'x':a.winfo_rootx(),'y':a.winfo_rooty(),'width':a.winfo_width(),'height':a.winfo_height()},
        'marker_xy':[marker.winfo_rootx()+5,marker.winfo_rooty()+5],
        'cover_mapped':bool(cover.winfo_ismapped()),'events':len(journal),
        'native_counts':{k:sum(r.get('kind')=='native' and r.get('event')==k for r in journal) for k in ('2','3','4','5')}}
def emit(obj): print(json.dumps(obj,sort_keys=True),flush=True)
def respond(req):
    op=req['op']
    if op=='cover':
        mode=req['mode']
        if mode=='target': cover.place(x=40,y=40,width=200,height=40); cover.lift()
        elif mode=='unrelated': cover.place(x=300,y=200,width=200,height=40); cover.lift()
        elif mode=='none': cover.place_forget()
        else: raise ValueError(mode)
        root.update_idletasks(); write({'kind':'fixture','operation':'cover','mode':mode})
    if op=='wait':
        deadline=time.monotonic()+2
        def ready():
            snap=snapshot()
            if all(snap['native_counts'][k]>=v for k,v in req['counts'].items()):
                emit({'id':req['id'],'snapshot':snap}); return
            if time.monotonic()>=deadline:
                emit({'id':req['id'],'error':'native_event_timeout','snapshot':snap}); return
            root.after(1,ready)
        ready(); return
    if op not in ('snapshot','cover','close'): raise ValueError(op)
    snap=snapshot(); emit({'id':req['id'],'snapshot':snap})
    if op=='close':
        (ROOT/'app-final.json').write_text(json.dumps(snap,sort_keys=True)+'\n')
        logfile.flush(); logfile.close(); root.after_idle(root.destroy)
def readable(fd,mask):
    line=sys.stdin.readline()
    if not line: root.destroy(); return
    req=json.loads(line); write({'kind':'rpc','request':req})
    # A distinct event-loop turn allows earlier native events to dispatch.
    root.after(10,lambda:respond(req))
root.createfilehandler(sys.stdin,tk.READABLE,readable)
root.update(); b.focus_force(); root.update()
(ROOT/'tk-bindings.json').write_text(json.dumps({c:{p:root.tk.call('bind',c,p) for p in ('<Button-1>','<ButtonRelease-1>','<KeyPress>')} for c in ('Entry','Button')},sort_keys=True)+'\n')
write({'kind':'ready','tk':root.tk.call('info','patchlevel'),'snapshot':snapshot()})
emit({'ready':snapshot(),'tk':root.tk.call('info','patchlevel')})
root.after(12000,lambda: (write({'kind':'watchdog'}),root.destroy()))
root.mainloop()
