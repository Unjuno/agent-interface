from __future__ import annotations
import argparse,json,time,tkinter as tk
from pathlib import Path

ap=argparse.ArgumentParser(); ap.add_argument('--ready',required=True); ap.add_argument('--log',required=True); ap.add_argument('--control',required=True); args=ap.parse_args()
ready=Path(args.ready); log=Path(args.log); control=Path(args.control)
root=tk.Tk(); root.overrideredirect(True); root.geometry('320x240+0+0'); root.configure(bg='black')
cv=tk.Canvas(root,width=320,height=240,bg='black',highlightthickness=0); cv.pack(fill='both',expand=True)
x=140.0; width=40; y0=100
rect=cv.create_rectangle(int(x),y0,int(x)+width,y0+40,fill='#ff0000',outline='#ffffff')
root.update_idletasks(); root.update(); ready.write_text(str(time.perf_counter_ns()))
state={'configured':False,'score_start_ns':None,'motion_start_ns':None,'rev_target_ns':None,'end_ns':None,'dir':None,'last_ns':None,'reversed':False}
speed_px_per_ns=180.0/1e9

def emit(row):
    with log.open('a') as f:
        f.write(json.dumps(row,sort_keys=True)+'\n'); f.flush()

def configure_if_ready():
    if state['configured'] or not control.exists(): return
    cfg=json.loads(control.read_text())
    state['score_start_ns']=int(cfg['score_start_ns']); state['motion_start_ns']=state['score_start_ns']-150_000_000
    off=cfg.get('reversal_offset_ms')
    state['rev_target_ns']=None if off is None else state['score_start_ns']+int(off)*1_000_000
    state['end_ns']=state['score_start_ns']+240_000_000; state['dir']=int(cfg['initial_dir']); state['configured']=True
    emit({'kind':'configured','t_ns':time.perf_counter_ns(),**cfg})

def tick():
    global x
    now=time.perf_counter_ns(); configure_if_ready()
    if state['configured'] and now>=state['motion_start_ns']:
        if state['last_ns'] is None:
            state['last_ns']=now; emit({'kind':'motion_start','t_ns':now,'x':x,'dir':state['dir']})
        else:
            if state['rev_target_ns'] is not None and (not state['reversed']) and now>=state['rev_target_ns']:
                state['dir']=-state['dir']; state['reversed']=True
                emit({'kind':'reversal_applied','t_ns':now,'target_ns':state['rev_target_ns'],'x':x,'dir':state['dir']})
            dt=max(0,now-state['last_ns']); x += state['dir']*speed_px_per_ns*dt
            x=max(20.0,min(260.0,x)); cv.coords(rect,int(round(x)),y0,int(round(x))+width,y0+40); state['last_ns']=now
            emit({'kind':'tick','t_ns':now,'x':x,'dir':state['dir']})
        if now>=state['end_ns']:
            emit({'kind':'done','t_ns':now,'x':x,'dir':state['dir']}); root.destroy(); return
    root.after(2,tick)
root.after(0,tick); root.mainloop()
