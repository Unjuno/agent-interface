#!/usr/bin/env python3
import json,os,queue,socket,sys,threading,time,tkinter as tk
path=sys.argv[1]
try: os.unlink(path)
except FileNotFoundError: pass
root=tk.Tk();root.title('server-grab-keymap-receiver');root.geometry('500x120+80+80')
value=tk.StringVar();entry=tk.Entry(root,textvariable=value,font=('monospace',18));entry.pack(fill='both',expand=True);entry.focus_force();root.update_idletasks();q=queue.Queue();events=[];shadow='';lock=threading.Lock()
def on_press(e):
 with lock: events.append({'kind':'press','callback_ns':time.monotonic_ns(),'keycode':int(e.keycode),'keysym':str(e.keysym),'char':str(e.char)})
def on_release(e):
 global shadow
 with lock:
  shadow=value.get();events.append({'kind':'release','callback_ns':time.monotonic_ns(),'keycode':int(e.keycode),'keysym':str(e.keysym),'char':str(e.char),'shadow':shadow})
entry.bind('<KeyPress>',on_press,add='+');entry.bind('<KeyRelease>',on_release,add='+')
def server():
 s=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);s.bind(path);s.listen(8)
 while True:
  c,_=s.accept();data=b''
  while not data.endswith(b'\n'):
   z=c.recv(65536)
   if not z:break
   data+=z
  req=json.loads(data.decode())
  if req.get('op')=='peek_shadow':
   with lock: box={'ok':True,'shadow':shadow,'events':list(events),'reply_ns':time.monotonic_ns()}
   c.sendall((json.dumps(box,ensure_ascii=False)+'\n').encode());c.close();continue
  box={};ev=threading.Event();q.put((req,box,ev));ev.wait(3);c.sendall((json.dumps(box,ensure_ascii=False)+'\n').encode());c.close()
threading.Thread(target=server,daemon=True).start()
def poll():
 global events,shadow
 try:
  while True:
   req,box,ev=q.get_nowait();op=req.get('op')
   if op=='reset':
    value.set('');entry.icursor(0);entry.focus_force()
    with lock:events=[];shadow=''
    box['ok']=True
   elif op=='get':
    with lock:box.update(ok=True,text=value.get(),shadow=shadow,events=list(events))
   elif op=='quit':box['ok']=True;ev.set();root.after(20,root.destroy);return
   else:box['error']='bad_op'
   ev.set()
 except queue.Empty:pass
 root.after(2,poll)
root.after(2,poll);print(json.dumps({'xid':root.winfo_id()}),flush=True);root.mainloop()
