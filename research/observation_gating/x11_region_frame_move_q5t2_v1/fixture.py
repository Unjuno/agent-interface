from __future__ import annotations
import json, sys, tkinter as tk

WIDTH=120
HEIGHT=80
START=(20,20)

root=tk.Tk()
root.overrideredirect(True)
root.geometry(f"{WIDTH}x{HEIGHT}+{START[0]}+{START[1]}")
root.configure(bg="#112233")
canvas=tk.Canvas(root,width=WIDTH,height=HEIGHT,borderwidth=0,highlightthickness=0,bg="#112233")
canvas.pack(fill="both",expand=True)
canvas.create_rectangle(0,0,39,79,fill="#ff0000",outline="")
canvas.create_rectangle(40,0,79,79,fill="#00ff00",outline="")
canvas.create_rectangle(80,0,119,79,fill="#0000ff",outline="")
canvas.create_rectangle(20,20,99,59,outline="#ffffff",width=3)
canvas.create_rectangle(50,30,69,49,fill="#000000",outline="#ffffff",width=1)
root.update()

def state():
    root.update()
    return {"xid":int(root.winfo_id()),"x":int(root.winfo_rootx()),"y":int(root.winfo_rooty()),"w":int(root.winfo_width()),"h":int(root.winfo_height())}

print(json.dumps({"type":"READY",**state()},sort_keys=True),flush=True)
for raw in sys.stdin:
    try:
        req=json.loads(raw)
        cmd=req.get("cmd")
        if cmd=="move":
            root.geometry(f"{WIDTH}x{HEIGHT}+{int(req['x'])}+{int(req['y'])}")
            root.update()
            print(json.dumps({"type":"MOVED",**state()},sort_keys=True),flush=True)
        elif cmd=="state":
            print(json.dumps({"type":"STATE",**state()},sort_keys=True),flush=True)
        elif cmd=="close":
            root.destroy()
            print(json.dumps({"type":"CLOSED"},sort_keys=True),flush=True)
            break
        else:
            print(json.dumps({"type":"ERROR","error":"unknown_command"},sort_keys=True),flush=True)
    except Exception as exc:
        print(json.dumps({"type":"ERROR","error":repr(exc)},sort_keys=True),flush=True)
