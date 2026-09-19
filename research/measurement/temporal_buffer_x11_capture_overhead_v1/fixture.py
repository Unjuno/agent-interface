import argparse,json,time,tkinter as tk
from pathlib import Path
ap=argparse.ArgumentParser(); ap.add_argument('--ready'); ap.add_argument('--start'); ap.add_argument('--stop'); ap.add_argument('--out'); args=ap.parse_args()
ready,startf,stopf,out=map(Path,[args.ready,args.start,args.stop,args.out])
root=tk.Tk(); root.overrideredirect(True); root.geometry('320x240+0+0'); root.configure(bg='black')
cv=tk.Canvas(root,width=320,height=240,bg='black',highlightthickness=0); cv.pack(fill='both',expand=True)
rect=cv.create_rectangle(20,100,60,140,fill='red',outline='white')
root.update_idletasks(); root.update(); ready.write_text(str(time.perf_counter_ns()))
measure_start=None; times=[]; tick_count=0; x=20; dx=3

def finish():
    gaps=[b-a for a,b in zip(times,times[1:])]
    out.write_text(json.dumps({'times_ns':times,'tick_count':len(times),'all_ticks':tick_count,'geometry':[root.winfo_width(),root.winfo_height()]},sort_keys=True))
    root.destroy()

def tick():
    global measure_start,tick_count,x,dx
    now=time.perf_counter_ns(); tick_count+=1
    if measure_start is None and startf.exists():
        try: measure_start=int(startf.read_text().strip())
        except Exception: pass
    if measure_start is not None and now>=measure_start: times.append(now)
    if stopf.exists(): finish(); return
    x += dx
    if x<0 or x>260: dx=-dx; x+=dx
    cv.coords(rect,x,100,x+40,140)
    root.after(16,tick)
root.after(0,tick); root.mainloop()
