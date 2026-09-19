from __future__ import annotations
import json, sys, tkinter as tk

W,H=320,200
CY=100.0
RW,RH=12.0,24.0

root=tk.Tk()
root.overrideredirect(True)
root.geometry(f"{W}x{H}+0+0")
root.configure(bg="black")
canvas=tk.Canvas(root,width=W,height=H,bg="black",highlightthickness=0,bd=0)
canvas.pack(fill="both",expand=True)
rect=canvas.create_rectangle(94,88,106,112,fill="#ff0000",outline="")
root.update_idletasks(); root.update()
print(json.dumps({"kind":"ready","rootx":root.winfo_rootx(),"rooty":root.winfo_rooty(),"w":root.winfo_width(),"h":root.winfo_height()}),flush=True)

for line in sys.stdin:
    line=line.strip()
    if not line:
        continue
    msg=json.loads(line)
    if msg.get("cmd")=="set":
        xc=float(msg["x"])
        canvas.coords(rect,xc-RW/2,CY-RH/2,xc+RW/2,CY+RH/2)
        root.update_idletasks(); root.update()
        print(json.dumps({"kind":"ack","x":xc,"rootx":root.winfo_rootx(),"rooty":root.winfo_rooty()}),flush=True)
    elif msg.get("cmd")=="quit":
        print(json.dumps({"kind":"bye"}),flush=True)
        break
root.destroy()
