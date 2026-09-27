from __future__ import annotations
import hashlib,json,os,platform,secrets,subprocess,sys,time
from pathlib import Path
from Xlib import X,display
import Xlib
from capture_slice import CaptureAdapter
from policy import assess

IMAGE_ID="sha256:acf83a1dfafd43c44d81e2f28f85fc844fa43dc73f36b689a862dd924f9235d0"
ALLOCATION="capture-visibility-docker-4365-20260927-01"
PARENT=(43,57,120,80)
PARENT_PIXEL=0x204060
CHILD_PIXEL=0xE0A040
SIBLING_PIXEL=0x20C0E0
CONDITIONS=("CLEAR","SIBLING_HALF","SIBLING_FULL","CHILD_HALF","CHILD_FULL","RESTORED")

def write_json(path,obj):
    path.write_text(json.dumps(obj,sort_keys=True,indent=2,allow_nan=False)+"\n",encoding="utf-8",newline="\n")
def event_states(d,parent):
    result=[]
    while d.pending_events():
        e=d.next_event()
        if e.type==X.VisibilityNotify and getattr(e,"window",None) is not None and e.window.id==parent.id:
            result.append(int(e.state))
    return result
class RawSink:
    def __init__(self,root,prefix): self.root=root; self.prefix=prefix
    def write(self,raw,w,h,**meta):
        name=self.prefix+".raw"; p=self.root/"raw"/name
        p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(raw)
        return {"path":"raw/"+name,"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw),
                "depth":int(meta["depth"]),"bits_per_pixel":int(meta["bits_per_pixel"]),
                "scanline_pad":int(meta["scanline_pad"]),"byte_order":int(meta["byte_order"]),
                "masks":[int(v) for v in meta["masks"]],"true_color":bool(meta["true_color"])}
def run_case(out,index,condition,rep):
    display_number=140+index
    disp=f":{display_number}"
    auth=Path("/tmp")/f"xauth-{index}.db"
    cookie=secrets.token_hex(16)
    xlog=out/"logs"/f"{index:02d}_{condition.lower()}_xvfb.log"; xlog.parent.mkdir(parents=True,exist_ok=True)
    log=xlog.open("wb")
    server=None; d=None; windows=[]
    previous_display=os.environ.get("DISPLAY"); previous_auth=os.environ.get("XAUTHORITY")
    row={"case_index":index,"condition":condition,"replicate":rep,
       "display":disp,"allocation":ALLOCATION,"attempted":True}
    try:
        ax=subprocess.run(["xauth","-f",str(auth),"add",disp,"MIT-MAGIC-COOKIE-1",cookie],capture_output=True,text=True)
        row["xauth_exit"]=ax.returncode
        if ax.returncode!=0: raise RuntimeError("XAUTH_SETUP_FAILED:"+ax.stderr[-300:])
        os.chmod(auth,0o600)
        os.environ["DISPLAY"]=disp; os.environ["XAUTHORITY"]=str(auth)
        env={**os.environ,"DISPLAY":disp,"XAUTHORITY":str(auth),"PYTHONDONTWRITEBYTECODE":"1"}
        server=subprocess.Popen(["Xvfb",disp,"-screen","0","640x480x24","-nolisten","tcp","-auth",str(auth),"-noreset"],
                                 env=env,stdout=log,stderr=subprocess.STDOUT)
        deadline=time.monotonic()+8
        while True:
            if server.poll() is not None: raise RuntimeError("XVFB_EXITED:"+str(server.returncode))
            try:
                d=display.Display(disp); break
            except Exception:
                if time.monotonic()>=deadline: raise RuntimeError("XVFB_READINESS_TIMEOUT")
                time.sleep(.05)
        scr=d.screen(); root=scr.root
        x,y,w,h=PARENT
        parent=root.create_window(x,y,w,h,0,X.CopyFromParent,X.InputOutput,X.CopyFromParent,
             background_pixel=PARENT_PIXEL,border_pixel=0,event_mask=X.VisibilityChangeMask|X.StructureNotifyMask,
             override_redirect=1)
        windows.append(parent); parent.map(); d.sync()
        child=None; sibling=None
        if condition in ("CHILD_HALF","CHILD_FULL","RESTORED"):
            cx,cy,cw,ch=(60,0,60,80) if condition=="CHILD_HALF" else (0,0,120,80)
            child=parent.create_window(cx,cy,cw,ch,0,X.CopyFromParent,X.InputOutput,X.CopyFromParent,
                         background_pixel=CHILD_PIXEL,border_pixel=0,override_redirect=1)
            windows.append(child); child.map(); d.sync()
            if condition=="RESTORED": child.unmap(); d.sync()
        if condition in ("SIBLING_HALF","SIBLING_FULL"):
            sx,sy,sw,sh=(x+60,y,60,80) if condition=="SIBLING_HALF" else (x,y,120,80)
            sibling=root.create_window(sx,sy,sw,sh,0,X.CopyFromParent,X.InputOutput,X.CopyFromParent,
                         background_pixel=SIBLING_PIXEL,border_pixel=0,override_redirect=1)
            windows.append(sibling); sibling.map(); d.sync()
        time.sleep(.04)
        states=event_states(d,parent)
        attrs=parent.get_attributes(); tree=parent.query_tree()
        child_rows=[]
        for chwin in tree.children:
            ca=chwin.get_attributes(); cg=chwin.get_geometry()
            child_rows.append({"xid":int(chwin.id),"map_state":int(ca.map_state),"class":int(getattr(ca,"class")),
                               "rect":[int(cg.x),int(cg.y),int(cg.width),int(cg.height)]})
        visibility=states[-1] if states else None
        evidence={"map_state":int(attrs.map_state),"visibility":visibility,"region":[0,0,w,h],
                  "children":[{"map_state":a["map_state"],"class":a["class"],"rect":a["rect"]} for a in child_rows],
                  "coverage_complete":True}
        policy_result=assess(evidence)
        row.update({"parent_xid":int(parent.id),"parent_geometry":[x,y,w,h],"map_state":int(attrs.map_state),
                    "visibility_events":states,"visibility":visibility,"children":child_rows,
                    "coverage_complete":True,"assessment_input":evidence,"assessment":policy_result,
                    "screen_geometry":[int(scr.width_in_pixels),int(scr.height_in_pixels)]})
        frame_results=[]
        for frame,rx,ry in [("screen_physical_px",x,y),("window_client",0,0)]:
            sink=RawSink(out,f"{index:02d}_{condition.lower()}_{frame}")
            adapter=CaptureAdapter(d,parent,sink)
            try:
                got=adapter.capture("target",frame,rx,ry,w,h)
                frame_results.append({"frame":frame,"status":"CAPTURED",**got})
            except Exception as exc:
                frame_results.append({"frame":frame,"status":"ERROR","error_type":type(exc).__name__,
                                      "error_repr":repr(exc)})
        row["captures"]=frame_results
        d.sync()
        row["server_alive_before_cleanup"]=server.poll() is None
        row["container_expected_image_id"]=IMAGE_ID
        row["status"]="COMPLETE"
    except Exception as exc:
        row.update({"status":"STOP_CASE","error_type":type(exc).__name__,"error_repr":repr(exc)})
    finally:
        if d is not None:
            try:
                for win in reversed(windows):
                    try: win.destroy()
                    except Exception: pass
                d.sync(); d.close()
            except Exception: pass
        if server is not None:
            if server.poll() is None:
                server.terminate()
                try: server.wait(timeout=4)
                except subprocess.TimeoutExpired:
                    server.kill(); server.wait(timeout=4)
            row["xvfb_exit_code"]=server.returncode
        row["x_socket_absent_after_cleanup"]=not Path(f"/tmp/.X11-unix/X{display_number}").exists()
        try: auth.unlink()
        except FileNotFoundError: pass
        if previous_display is None: os.environ.pop("DISPLAY",None)
        else: os.environ["DISPLAY"]=previous_display
        if previous_auth is None: os.environ.pop("XAUTHORITY",None)
        else: os.environ["XAUTHORITY"]=previous_auth
        row["xauthority_removed_after_cleanup"]=not auth.exists()
        log.close()
        row["xvfb_log_path"]="logs/"+xlog.name
    return row

def main():
    if len(sys.argv)!=2: raise SystemExit("usage: runner.py OUT_DIR")
    out=Path(sys.argv[1])
    if out.exists() and any(out.iterdir()): raise SystemExit("STOP_OUTPUT_NOT_FRESH")
    out.mkdir(parents=True,exist_ok=True)
    write_json(out/"environment.json",{"allocation":ALLOCATION,"image_id":IMAGE_ID,"python":platform.python_version(),
        "architecture":platform.machine(),"python_xlib":getattr(Xlib,"__version__","unknown"),
        "xvfb_binary_sha256":hashlib.sha256(Path("/usr/bin/Xvfb").read_bytes()).hexdigest(),
        "network_expected":"none","gpu_used":False,"host_display_used":False,"input_emitted":False,
        "formal_sessions":12,"capture_attempts_expected":24})
    rows=[]
    for idx,(condition,rep) in enumerate((c,r) for r in (1,2) for c in CONDITIONS):
        row=run_case(out,idx,condition,rep); rows.append(row)
        with (out/"cases.jsonl").open("a",encoding="utf-8",newline="\n") as f:
            f.write(json.dumps(row,sort_keys=True,separators=(",",":"),allow_nan=False)+"\n")
    complete=sum(r["status"]=="COMPLETE" for r in rows)
    covered={"SIBLING_HALF","SIBLING_FULL","CHILD_HALF","CHILD_FULL"}
    clear={"CLEAR","RESTORED"}
    assess_clear=sum(r.get("assessment",{}).get("status")=="CLEAR_PARENT_REGION_SCOPED" for r in rows)
    assess_unknown=sum(r.get("assessment",{}).get("status")=="UNKNOWN" for r in rows)
    capture_attempts=[c for r in rows for c in r.get("captures",[])]
    raw_errors=[c for c in capture_attempts if c["status"]=="ERROR"]
    allowed_errors=all(r.get("condition")=="SIBLING_FULL" and e.get("frame")=="window_client" and e["error_type"]=="TypeError" for r in rows for e in r.get("captures",[]) if e["status"]=="ERROR")
    expected_pass=(complete==12 and assess_clear==4 and assess_unknown==8 and allowed_errors and
                   all(r.get("x_socket_absent_after_cleanup") and r.get("xauthority_removed_after_cleanup") for r in rows))
    result={"schema":"capture-visibility-docker-4827-result-v1","allocation":ALLOCATION,
            "image_id":IMAGE_ID,"conditions":list(CONDITIONS),"sessions_total":len(rows),
            "sessions_complete":complete,"assessor_clear":assess_clear,"assessor_unknown":assess_unknown,
            "capture_attempts":len(capture_attempts),"capture_errors":len(raw_errors),
            "allowed_capture_error_gate":allowed_errors,"producer_gate_candidate":expected_pass,
            "rows":rows}
    write_json(out/"result.json",result)
    print(json.dumps({k:v for k,v in result.items() if k!="rows"},sort_keys=True,indent=2))
    return 0 if complete==12 else 2
if __name__=="__main__": raise SystemExit(main())
