#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, socket, tkinter as tk
from pathlib import Path

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--socket',type=Path,required=True); ap.add_argument('--ready',type=Path,required=True); a=ap.parse_args()
    if a.socket.exists(): a.socket.unlink()
    root=tk.Tk(); root.title('agent-interface-text-observation-binding')
    entries={}; events={'a':[],'b':[]}
    for name in ('a','b'):
        e=tk.Entry(root,width=80); e.pack(padx=20,pady=8); entries[name]=e
        e.bind('<KeyPress>', lambda ev,n=name: events[n].append({'char':ev.char or '', 'keysym':ev.keysym}))
    entries['a'].focus_set(); root.update_idletasks(); root.update()
    xids={n:e.winfo_id() for n,e in entries.items()}
    srv=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM); srv.bind(str(a.socket)); srv.listen(16); srv.setblocking(False)
    a.ready.write_text(json.dumps({'xids':xids})+'\n')
    def target_name():
        f=root.focus_get()
        for n,e in entries.items():
            if f == e: return n
        return None
    def handle(q):
        cmd=q.get('cmd'); n=q.get('target','a')
        if cmd=='get': return {'ok':True,'text':entries[n].get(),'events':list(events[n]),'xid':xids[n],'focus':target_name()}
        if cmd=='reset':
            for k,e in entries.items(): e.delete(0,tk.END); events[k]=[]
            entries['a'].focus_set(); return {'ok':True}
        if cmd=='set': entries[n].delete(0,tk.END); entries[n].insert(0,str(q.get('text',''))); return {'ok':True,'text':entries[n].get()}
        if cmd=='focus': entries[n].focus_set(); root.update_idletasks(); return {'ok':True,'focus':target_name()}
        if cmd=='shutdown': root.after(1,root.destroy); return {'ok':True}
        return {'ok':False,'error':'unknown'}
    def poll():
        try:
            while True:
                c,_=srv.accept()
                with c:
                    raw=b''
                    while b'\n' not in raw:
                        p=c.recv(65536)
                        if not p: break
                        raw+=p
                    try: res=handle(json.loads(raw.split(b'\n',1)[0].decode()))
                    except Exception as exc: res={'ok':False,'error':type(exc).__name__+':'+str(exc)}
                    c.sendall((json.dumps(res,ensure_ascii=False)+'\n').encode())
        except BlockingIOError: pass
        if root.winfo_exists(): root.after(5,poll)
    root.after(5,poll)
    try: root.mainloop()
    finally:
        srv.close()
        if a.socket.exists(): a.socket.unlink()
    return 0
if __name__=='__main__': raise SystemExit(main())
