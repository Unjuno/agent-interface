#!/usr/bin/env python3
import json,os,queue,socket,sys,threading,tkinter as tk
from Xlib import display
path=sys.argv[1]
try:os.unlink(path)
except FileNotFoundError:pass
root=tk.Tk();root.withdraw();q=queue.Queue();state={'version':0,'text':None}
def owner_id():
 d=display.Display(os.environ['DISPLAY']);o=d.get_selection_owner(d.intern_atom('CLIPBOARD'));oid=getattr(o,'id',None);d.close();return oid
def server():
 s=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);s.bind(path);s.listen(8)
 while True:
  c,_=s.accept();data=b''
  while not data.endswith(b'\n'):
   z=c.recv(65536)
   if not z:break
   data+=z
  req=json.loads(data.decode());box={};ev=threading.Event();q.put((req,box,ev));ev.wait(3);c.sendall((json.dumps(box,ensure_ascii=False)+'\n').encode());c.close()
threading.Thread(target=server,daemon=True).start()
def poll():
 try:
  while True:
   req,box,ev=q.get_nowait();op=req.get('op')
   if op=='set':
    text=req['text'];root.clipboard_clear();root.clipboard_append(text);root.update();state['version']+=1;state['text']=text;box.update(ok=True,version=state['version'],owner_id=owner_id())
   elif op=='status':box.update(ok=True,version=state['version'],text=state['text'],owner_id=owner_id())
   elif op=='quit':box['ok']=True;ev.set();root.after(20,root.destroy);return
   else:box['error']='bad_op'
   ev.set()
 except queue.Empty:pass
 root.after(3,poll)
root.after(3,poll);print(json.dumps({'ready':True}),flush=True);root.mainloop()
