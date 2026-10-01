from __future__ import annotations
import argparse, json, os, select, sys, time, tkinter as tk
from pathlib import Path

ap=argparse.ArgumentParser()
ap.add_argument('--journal', required=True)
ap.add_argument('--session', required=True)
args=ap.parse_args()
journal=Path(args.journal)
journal.parent.mkdir(parents=True, exist_ok=True)
count=0
root=tk.Tk()
root.title('agent-interface-recommit-fixture')
root.geometry('320x180+120+120')
root.resizable(False, False)
button=None

def emit(obj):
    sys.stdout.write(json.dumps(obj, sort_keys=True, separators=(',',':'))+'\n'); sys.stdout.flush()

def make_button():
    global button
    if button is not None:
        button.destroy()
    def on_click():
        global count
        count += 1
        row={'event':'effect','count':count,'session':args.session,
             'surface_id':int(root.winfo_id()),'target_id':int(button.winfo_id()),
             'monotonic_ns':time.monotonic_ns()}
        with journal.open('a', encoding='utf-8') as f:
            f.write(json.dumps(row,sort_keys=True,separators=(',',':'))+'\n'); f.flush(); os.fsync(f.fileno())
    button=tk.Button(root,text='Apply',command=on_click,width=12,height=3)
    button.place(x=100,y=55,width=120,height=70)
    root.update_idletasks()

def snapshot(event):
    root.update_idletasks()
    return {'event':event,'session':args.session,'surface_id':int(root.winfo_id()),
            'target_id':int(button.winfo_id()),'x':int(button.winfo_rootx()+button.winfo_width()//2),
            'y':int(button.winfo_rooty()+button.winfo_height()//2),'count':count,
            'monotonic_ns':time.monotonic_ns()}

make_button(); emit(snapshot('ready'))
os.set_blocking(sys.stdin.fileno(), False)
buf=''

def poll():
    global buf
    try:
        data=os.read(sys.stdin.fileno(),65536)
        if data:
            buf += data.decode('utf-8')
    except BlockingIOError:
        pass
    except OSError:
        root.destroy(); return
    while '\n' in buf:
        line,buf=buf.split('\n',1)
        if not line.strip(): continue
        try: cmd=json.loads(line)
        except Exception as e:
            emit({'event':'error','error':'bad_json','detail':repr(e)}); continue
        op=cmd.get('op')
        if op=='state': emit(snapshot('state'))
        elif op=='replace_target':
            make_button(); emit(snapshot('replaced'))
        elif op=='close':
            emit(snapshot('closing')); root.after(1,root.destroy); return
        else: emit({'event':'error','error':'bad_op','op':op})
    root.after(5,poll)
root.after(5,poll)
root.mainloop()
