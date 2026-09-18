#!/usr/bin/env python3
import argparse, json, os, time, tkinter as tk
from pathlib import Path
p=argparse.ArgumentParser(); p.add_argument('--ready',required=True); p.add_argument('--events',required=True); p.add_argument('--delay-ms',type=float,required=True); p.add_argument('--stop',required=True); p.add_argument('--effect-enabled',type=int,choices=[0,1],required=True); a=p.parse_args()
ready=Path(a.ready); events=Path(a.events); stop=Path(a.stop)
def log(kind,**kw):
 row={'kind':kind,'t_ns':time.perf_counter_ns(),**kw}
 with events.open('a',encoding='utf-8') as f: f.write(json.dumps(row,sort_keys=True)+'\n'); f.flush(); os.fsync(f.fileno())
root=tk.Tk(); root.overrideredirect(True); root.geometry('320x240+0+0'); root.configure(bg='black')
canvas=tk.Canvas(root,width=320,height=240,bg='black',highlightthickness=0); canvas.pack(fill='both',expand=True)
rect=canvas.create_rectangle(40,100,80,140,fill='red',outline='red'); state={'effect':False}
def effect():
 if state['effect'] or not a.effect_enabled: return
 state['effect']=True; canvas.coords(rect,220,100,260,140); canvas.update_idletasks(); log('effect_callback')
def press(e): log('key_press',keysym=e.keysym,keycode=e.keycode)
def release(e):
 log('key_release',keysym=e.keysym,keycode=e.keycode)
 if a.effect_enabled:
  delay=max(0,int(round(a.delay_ms))); root.after(delay,effect) if delay else root.after_idle(effect)
root.bind('<KeyPress-F8>',press); root.bind('<KeyRelease-F8>',release)
root.update_idletasks(); root.update(); root.focus_force(); root.update()
ready.write_text(json.dumps({'window_id':root.winfo_id(),'pid':os.getpid(),'delay_ms':a.delay_ms,'effect_enabled':bool(a.effect_enabled)}),encoding='utf-8'); log('ready',window_id=root.winfo_id())
def poll_stop():
 if stop.exists(): log('stop'); root.destroy(); return
 root.after(5,poll_stop)
root.after(5,poll_stop); root.mainloop()
