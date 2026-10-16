from __future__ import annotations
import argparse,json,os,queue,socket,threading,time
from pathlib import Path
import tkinter as tk
from Xlib import Xatom,display
from common import LOCAL_ATOM,EFFECT_ATOM,GLOBAL_ATOM


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--display',required=True);ap.add_argument('--name',required=True);ap.add_argument('--sock',required=True);ap.add_argument('--ready',required=True);ap.add_argument('--geom',required=True);args=ap.parse_args()
    os.environ['DISPLAY']=args.display
    root=tk.Tk();root.title('AI-'+args.name);root.geometry(args.geom)
    label=tk.StringVar(value=args.name+':NONE');tk.Label(root,textvariable=label,width=28,height=4).pack(expand=True,fill='both')
    root.update_idletasks();root.update();xid=root.winfo_id()
    xd=display.Display(args.display); win=xd.create_resource_object('window',xid); xroot=xd.screen().root
    a_local=xd.intern_atom(LOCAL_ATOM);a_effect=xd.intern_atom(EFFECT_ATOM);a_global=xd.intern_atom(GLOBAL_ATOM)
    local_gen=0
    win.change_property(a_local,Xatom.CARDINAL,32,[0]);win.change_property(a_effect,Xatom.STRING,8,b'NONE');xd.sync()
    q=queue.Queue(); sock_path=Path(args.sock)
    if sock_path.exists():sock_path.unlink()
    srv=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);srv.bind(str(sock_path));srv.listen(8)
    running=True
    ledger=[]
    def accept_loop():
        while running:
            try: conn,_=srv.accept()
            except OSError: break
            try:
                data=b''
                while b'\n' not in data:
                    part=conn.recv(65536)
                    if not part: break
                    data+=part
                cmd=json.loads(data.split(b'\n',1)[0]);q.put((conn,cmd))
            except Exception as e:
                try:conn.sendall((json.dumps({'ok':False,'error':repr(e)})+'\n').encode());conn.close()
                except Exception:pass
    t=threading.Thread(target=accept_loop,daemon=True);t.start()
    Path(args.ready).write_text(json.dumps({'name':args.name,'xid':xid,'socket':str(sock_path)},sort_keys=True)+'\n')
    def apply_one(conn,cmd):
        nonlocal local_gen,running
        try:
            delay=float(cmd.get('delay_ms',0))/1000
            if delay>0: time.sleep(delay)
            op=cmd['op']; applied=time.perf_counter_ns()
            if op=='set_effect':
                value=str(cmd['value']);win.change_property(a_effect,Xatom.STRING,8,value.encode());label.set(args.name+':'+value);xd.sync()
            elif op=='bump_local':
                local_gen+=1;win.change_property(a_local,Xatom.CARDINAL,32,[local_gen]);xd.sync()
            elif op=='set_global':
                value=int(cmd['value']);xroot.change_property(a_global,Xatom.CARDINAL,32,[value]);xd.sync()
            elif op=='state':
                pass
            elif op=='shutdown':
                running=False
            else: raise ValueError(op)
            row={'op':op,'value':cmd.get('value'),'applied_ns':applied};ledger.append(row)
            resp={'ok':True,**row,'local_gen':local_gen,'ledger_len':len(ledger)}
            conn.sendall((json.dumps(resp,sort_keys=True)+'\n').encode());conn.close()
            if op=='shutdown': root.after(10,root.destroy)
        except Exception as e:
            try:conn.sendall((json.dumps({'ok':False,'error':repr(e)})+'\n').encode());conn.close()
            except Exception:pass
    def poll():
        for _ in range(20):
            try: item=q.get_nowait()
            except queue.Empty: break
            apply_one(*item)
        if running:root.after(1,poll)
    root.after(1,poll);root.mainloop()
    try:srv.close()
    except Exception:pass
    try:sock_path.unlink()
    except FileNotFoundError:pass
    xd.close()

if __name__=='__main__':main()
