#!/usr/bin/env python3
"""Private-Xvfb UI-redress recipient experiment for Issue #5692."""
from __future__ import annotations
import argparse, base64, hashlib, json, os, subprocess, sys, tempfile, time
from pathlib import Path
from Xlib import X, display

ENTRY = (110, 140, 260, 42)
CLICK = (140, 160)
OBSERVE = 0.35

def write_json(path, value):
    Path(path).write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")

def button_event_record(ev, overlay_window_id):
    """Normalize Python-Xlib ButtonPress/Release using its actual field names."""
    return {"type":"ButtonPress" if ev.type==X.ButtonPress else "ButtonRelease",
            "window_id":int(overlay_window_id), "event_window":int(ev.window.id),
            "root_x":int(ev.root_x), "root_y":int(ev.root_y), "button":int(ev.detail)}

def target_process(ready_path, event_path):
    import tkinter as tk
    root = tk.Tk(); root.title("private-target"); root.geometry("360x180+80+80"); root.configure(bg="#e8e8e8")
    entry = tk.Entry(root, width=32, insertwidth=0, relief="solid", borderwidth=1)
    entry.place(x=30, y=60, width=260, height=42); entry.insert(0, "intended target")
    events = []
    def pressed(event):
        events.append({"type":"ButtonPress", "widget_id":int(entry.winfo_id()), "x_root":int(event.x_root), "y_root":int(event.y_root), "button":int(event.num)})
        write_json(event_path, events)
    def released(event):
        events.append({"type":"ButtonRelease", "widget_id":int(entry.winfo_id()), "x_root":int(event.x_root), "y_root":int(event.y_root), "button":int(event.num)})
        write_json(event_path, events)
    entry.bind("<ButtonPress-1>", pressed); entry.bind("<ButtonRelease-1>", released)
    root.update_idletasks(); root.update()
    write_json(ready_path, {"pid":os.getpid(), "window_id":int(root.winfo_id()), "entry_id":int(entry.winfo_id()),
                            "entry_root_x":int(entry.winfo_rootx()), "entry_root_y":int(entry.winfo_rooty()),
                            "entry_width":int(entry.winfo_width()), "entry_height":int(entry.winfo_height())})
    end=time.monotonic()+1.4
    while time.monotonic()<end:
        root.update(); time.sleep(.004)
    root.destroy(); write_json(event_path, events)

def overlay_process(mode, geometry, ready_path, event_path, wait_path=None):
    from Xlib.ext import shape
    d=display.Display(); root=d.screen().root; x,y,wid,hei=geometry; events=[]
    if mode=="visible":
        w=root.create_window(x,y,wid,hei,0,X.CopyFromParent,X.InputOutput,X.CopyFromParent,
            override_redirect=1,background_pixel=0x00ff0000,event_mask=X.ButtonPressMask|X.ButtonReleaseMask)
    else:
        w=root.create_window(x,y,wid,hei,0,0,X.InputOnly,X.CopyFromParent,
            override_redirect=1,event_mask=X.ButtonPressMask|X.ButtonReleaseMask)
        if mode=="empty-input": w.shape_rectangles(shape.SO.Set,shape.SK.Input,X.YXBanded,0,0,[])
    if wait_path:
        write_json(ready_path,{"pid":os.getpid(),"window_id":int(w.id),"mode":mode,"geometry":list(geometry),
                               "input_shape":mode!="empty-input","mapped":False})
        deadline=time.monotonic()+5
        while not Path(wait_path).exists() and time.monotonic()<deadline: time.sleep(.002)
        if not Path(wait_path).exists(): raise TimeoutError("race click barrier not released")
    d.sync(); w.map(); w.configure(stack_mode=X.Above); d.sync()
    write_json(ready_path,{"pid":os.getpid(),"window_id":int(w.id),"mode":mode,"geometry":list(geometry),
                           "input_shape":mode!="empty-input","mapped":bool(w.get_attributes().map_state==X.IsViewable)})
    end=time.monotonic()+OBSERVE
    while time.monotonic()<end:
        while d.pending_events():
            ev=d.next_event()
            if ev.type in (X.ButtonPress,X.ButtonRelease):
                events.append(button_event_record(ev, w.id))
                write_json(event_path,events)
        time.sleep(.002)
    write_json(event_path,events); w.destroy(); d.sync(); d.close()

def capture_crop(d):
    x,y,wid,hei=ENTRY; data=bytes(d.screen().root.get_image(x,y,wid,hei,X.ZPixmap,0xffffffff).data)
    return {"width":wid,"height":hei,"format":"X11_ZPixmap_raw","sha256":hashlib.sha256(data).hexdigest(),
            "base64":base64.b64encode(data).decode("ascii")}

def wait_json(path,timeout=4,require_mapped=False):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        if path.exists():
            try:
                v=json.loads(path.read_text(encoding="utf-8"))
                if not require_mapped or v.get("mapped") is True: return v
            except (json.JSONDecodeError,OSError): pass
        time.sleep(.01)
    raise TimeoutError(f"readiness missing: {path.name}")

def query_child(d,x,y):
    root=d.screen().root; d.xtest_fake_input(X.MotionNotify,root=root,x=x,y=y); d.sync()
    q=root.query_pointer(); return int(q.child.id) if q.child else 0

def click(d,x,y):
    root=d.screen().root
    d.xtest_fake_input(X.MotionNotify,root=root,x=x,y=y)
    d.xtest_fake_input(X.ButtonPress,detail=1,root=root,x=x,y=y)
    d.xtest_fake_input(X.ButtonRelease,detail=1,root=root,x=x,y=y); d.sync()

def run_trial(condition,policy,race=False):
    with tempfile.TemporaryDirectory(prefix="ui-redress-") as td:
        p=Path(td); tr=p/"target-ready.json"; te=p/"target-events.json"; ore=p/"overlay-ready.json"; oe=p/"overlay-events.json"; barrier=p/"race-go"
        target=subprocess.Popen([sys.executable,__file__,"--target",str(tr),str(te)]); overlay=None
        try:
            target_info=wait_json(tr); d=display.Display(); before=capture_crop(d)
            om={"visible":"visible","transparent-input":"input","input-transparent":"empty-input","race-after-check":"input"}.get(condition)
            overlay_info=None
            if om:
                args=[sys.executable,__file__,"--overlay",om,json.dumps([ENTRY[0],ENTRY[1],ENTRY[2],ENTRY[3]]),str(ore),str(oe)]
                if race: args.append(str(barrier))
                overlay=subprocess.Popen(args); overlay_info=wait_json(ore)
            after=capture_crop(d); visual_same=before["sha256"]==after["sha256"]
            child=query_child(d,*CLICK); is_target=child==int(target_info["window_id"])
            if policy=="SCREENSHOT_GEOMETRY": admitted=visual_same
            elif policy=="RECIPIENT_PRECHECK": admitted=is_target
            elif policy=="DIAGNOSTIC_FORCE_CLICK": admitted=True
            else: raise ValueError(policy)
            refusal=None if admitted else ("BLOCKED_VISUAL_CHANGE" if policy=="SCREENSHOT_GEOMETRY" else "BLOCKED_RECIPIENT_MISMATCH")
            if race and admitted:
                barrier.write_text("checked\n",encoding="ascii"); overlay_info=wait_json(ore,require_mapped=True); time.sleep(.03)
            if admitted: click(d,*CLICK)
            time.sleep(OBSERVE+.08); target.wait(timeout=2)
            if overlay: overlay.wait(timeout=2)
            d.close()
            tl=json.loads(te.read_text(encoding="utf-8")) if te.exists() else []
            ol=json.loads(oe.read_text(encoding="utf-8")) if oe.exists() else []
            return {"condition":condition,"policy":policy,"race":race,"target":target_info,"overlay":overlay_info,
                    "before_crop":before,"after_crop":after,"visual_same":visual_same,"precheck_child_id":child,
                    "recipient_is_target_at_precheck":is_target,"admitted":admitted,"refusal":refusal,
                    "click_delivered":bool(admitted),"target_events":tl,"overlay_events":ol,"candidate_pid":os.getpid()}
        finally:
            for proc in (overlay,target):
                if proc and proc.poll() is None:
                    proc.terminate()
                    try: proc.wait(timeout=1)
                    except subprocess.TimeoutExpired: proc.kill(); proc.wait()

def main():
    p=argparse.ArgumentParser(); p.add_argument("--out"); p.add_argument("--target",nargs=2); p.add_argument("--overlay",nargs="+"); a=p.parse_args()
    if a.target: target_process(*a.target); return 0
    if a.overlay:
        mode,g,r,e,*tail=a.overlay; overlay_process(mode,tuple(json.loads(g)),r,e,tail[0] if tail else None); return 0
    rows=[]
    for condition in ("clear","visible","transparent-input","input-transparent"):
        for policy in ("SCREENSHOT_GEOMETRY","RECIPIENT_PRECHECK"): rows.append(run_trial(condition,policy))
    rows.append(run_trial("visible","DIAGNOSTIC_FORCE_CLICK"))
    rows.append(run_trial("race-after-check","RECIPIENT_PRECHECK",race=True))
    out={"schema":"ui-redress-5692-t0-raw-v1","rows":rows,"candidate_exit":0,"row_count":len(rows),
         "platform":"Ubuntu WSL2 / private Xvfb","display":os.environ.get("DISPLAY"),"python":sys.version}
    text=json.dumps(out,sort_keys=True,separators=(",",":"))+"\n"
    if a.out: Path(a.out).write_text(text,encoding="utf-8")
    print(text,end=""); return 0

if __name__=="__main__": raise SystemExit(main())
