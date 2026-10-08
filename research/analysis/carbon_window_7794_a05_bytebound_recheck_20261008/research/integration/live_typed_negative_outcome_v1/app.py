from __future__ import annotations
import json, os, sys, time, tkinter as tk
mode=sys.argv[1]
root=tk.Tk(); root.geometry('320x180+20+20'); root.title('typed-outcome-fixture')
journal=[]; hidden_effect=False; seq=0; closing=False
btn=None
status=tk.StringVar(value='READY')
label=tk.Label(root,textvariable=status); label.pack(pady=18)
def emit(kind,**kw):
    global seq
    seq+=1; journal.append({'seq':seq,'kind':kind,'t_ns':time.monotonic_ns(),**kw})
def click():
    global hidden_effect
    emit('REQUEST_SEEN',request_id='req-1')
    if mode=='SUCCESS':
        hidden_effect=True; emit('EFFECT',request_id='req-1',value='DONE'); status.set('DONE')
    elif mode=='IN_PROGRESS':
        emit('PENDING',request_id='req-1')
        def later():
            global hidden_effect
            hidden_effect=True; emit('EFFECT',request_id='req-1',value='DONE'); status.set('DONE')
        root.after(300,later)
    elif mode=='FAILED_UNKNOWN':
        hidden_effect=True; status.set('HIDDEN_DONE')  # deliberately no public effect receipt
    elif mode=='CONFLICT':
        emit('EFFECT',request_id='req-1',value='DONE')
        emit('EFFECT',request_id='req-1',value='NOT_DONE')
        status.set('CONFLICT')
    else:
        emit('UNEXPECTED_INPUT',mode=mode)
if mode!='TARGET_NOT_FOUND':
    btn=tk.Button(root,text='Apply',command=click,width=12); btn.pack(pady=12)
modal=None
if mode=='BLOCKED':
    modal=tk.Toplevel(root); modal.geometry('220x90+70+60'); modal.title('blocking'); tk.Label(modal,text='Modal blocker').pack(pady=20); modal.grab_set()
root.update_idletasks(); root.update()
def snapshot():
    if btn is not None and btn.winfo_exists():
        x=btn.winfo_rootx()+btn.winfo_width()//2; y=btn.winfo_rooty()+btn.winfo_height()//2
        xid=btn.winfo_id()
    else: x=y=xid=None
    return {'root_xid':root.winfo_id(),'target_xid':xid,'target_center':[x,y] if x is not None else None,'target_present':bool(xid),'journal':list(journal),'hidden_effect':hidden_effect,'status':status.get(),'mode':mode}
print(json.dumps({'ready':True,'snapshot':snapshot()}),flush=True)
root.tk.createfilehandler(sys.stdin,tk.READABLE,lambda f,m: on_stdin())
def on_stdin():
    global closing
    line=sys.stdin.readline()
    if not line: root.quit(); return
    q=json.loads(line)
    if q['cmd']=='snapshot': print(json.dumps(snapshot()),flush=True)
    elif q['cmd']=='close': print(json.dumps({'closing':True,'snapshot':snapshot()}),flush=True); closing=True
while not closing:
    try: root.update()
    except tk.TclError: break
    time.sleep(0.002)
