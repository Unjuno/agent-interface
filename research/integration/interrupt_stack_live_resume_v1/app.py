#!/usr/bin/env python3
import json, os, socket, sys, time, tkinter as tk, uuid
from pathlib import Path

sock_path=sys.argv[1]
root=tk.Tk(); root.title('interrupt-stack-live'); root.geometry('500x220+30+30')
state={
 'session_id':str(uuid.uuid4()), 'task_active':True, 'interrupt_resolved':True,
 'source_epoch':1, 'source_fresh':True, 'queue_version':1,
 'pending_result':'NONE', 'target_generation':1,
}
labA=tk.Label(root,text='A'); labA.place(x=30,y=45)
labB=tk.Label(root,text='B'); labB.place(x=30,y=95)
entryA=tk.Entry(root,name='entrya',width=24); entryA.place(x=70,y=45,width=220,height=28)
entryB=tk.Entry(root,name='entryb',width=24); entryB.place(x=70,y=95,width=220,height=28)
modal=None
journal=[]

def log(kind, **kw):
    row={'kind':kind,'t_ns':time.monotonic_ns(),**kw}; journal.append(row)

def target_id(): return f"A:{state['target_generation']}:{int(entryA.winfo_id())}"
def snap():
    return {
      **state, 'target_id':target_id(), 'a':entryA.get(), 'b':entryB.get(),
      'focus_xid':int(root.focus_get().winfo_id()) if root.focus_get() else None,
      'root_xid':int(root.winfo_id()), 'a_xid':int(entryA.winfo_id()), 'b_xid':int(entryB.winfo_id()),
      'a_center':[entryA.winfo_rootx()+entryA.winfo_width()//2, entryA.winfo_rooty()+entryA.winfo_height()//2],
      'journal':list(journal), 'interrupt_open':modal is not None,
    }

def show_interrupt():
    global modal
    if modal is not None: return
    modal=tk.Toplevel(root); modal.title('Save confirmation'); modal.geometry('260x120+120+80')
    tk.Label(modal,text='Interruption: confirm before resume').pack(pady=16)
    modal.transient(root); modal.grab_set(); modal.focus_force()
    state['interrupt_resolved']=False; log('interrupt_open')

def close_interrupt():
    global modal
    if modal is not None:
        try: modal.grab_release()
        except Exception: pass
        modal.destroy(); modal=None
    state['interrupt_resolved']=True
    root.focus_force(); entryA.focus_force(); log('interrupt_close')

def replace_target():
    global entryA
    old_id=target_id(); old=entryA
    old.destroy(); root.update_idletasks()
    state['target_generation'] += 1
    entryA=tk.Entry(root,name=f"entrya{state['target_generation']}",width=24)
    entryA.place(x=70,y=45,width=220,height=28); root.update_idletasks()
    log('target_replace',old_target=old_id,new_target=target_id())

def handle(req):
    cmd=req.get('cmd')
    if cmd=='snapshot': return {'ok':True,'snapshot':snap()}
    if cmd=='show_interrupt': show_interrupt(); return {'ok':True,'snapshot':snap()}
    if cmd=='close_interrupt': close_interrupt(); return {'ok':True,'snapshot':snap()}
    if cmd=='replace_target': replace_target(); return {'ok':True,'snapshot':snap()}
    if cmd=='queue_changed': state['queue_version']+=1; log('queue_changed',version=state['queue_version']); return {'ok':True,'snapshot':snap()}
    if cmd=='source_stale': state['source_fresh']=False; state['source_epoch']+=1; log('source_stale',epoch=state['source_epoch']); return {'ok':True,'snapshot':snap()}
    if cmd=='pending_unknown': state['pending_result']='UNKNOWN'; log('pending_unknown'); return {'ok':True,'snapshot':snap()}
    if cmd=='task_cancel': state['task_active']=False; log('task_cancel'); return {'ok':True,'snapshot':snap()}
    if cmd=='close':
        resp={'ok':True,'snapshot':snap()}; root.after(10,root.destroy); return resp
    return {'ok':False,'error':'unknown_command'}

Path(sock_path).unlink(missing_ok=True)
srv=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM); srv.bind(sock_path); srv.listen(1); srv.setblocking(False)
root.update_idletasks(); root.deiconify(); root.focus_force(); entryA.focus_force(); root.update()
print(json.dumps({'type':'READY','pid':os.getpid(),'socket':sock_path,'snapshot':snap()},sort_keys=True),flush=True)
clients=[]

def poll():
    try:
        while True:
            try: c,_=srv.accept(); c.setblocking(False); clients.append((c,b''))
            except BlockingIOError: break
        new=[]
        for c,buf in clients:
            try:
                data=c.recv(65536)
                if data: buf+=data
                else: c.close(); continue
            except BlockingIOError: pass
            while b'\n' in buf:
                line,buf=buf.split(b'\n',1)
                if line:
                    try: resp=handle(json.loads(line))
                    except Exception as e: resp={'ok':False,'error':type(e).__name__+':'+str(e)}
                    c.sendall((json.dumps(resp,sort_keys=True)+'\n').encode())
            new.append((c,buf))
        clients[:] = new
    finally:
        if root.winfo_exists(): root.after(5,poll)
root.after(5,poll)
try: root.mainloop()
finally:
    for c,_ in clients:
        try:c.close()
        except:pass
    srv.close(); Path(sock_path).unlink(missing_ok=True)
