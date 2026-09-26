from __future__ import annotations
import argparse, hashlib, json, os, secrets, shutil, subprocess, sys, tempfile, time
from pathlib import Path
from Xlib import X, display

WIDTH=120
HEIGHT=80
START=(20,20)
MOVED=(220,160)
POLICIES=("PINNED_SCREEN","REFRESH_SCREEN","WINDOW_CLIENT")
SCHEDULES=("STABLE","MOVE_BEFORE","MOVE_BETWEEN")
BASE_MAIN="3666992ab2b5e1b41b159b361d1c690d8e720fdf"
ISSUE=4439
AUTHORITY=False
TASK_SUCCESS=None

HERE=Path(__file__).resolve().parent
FIXTURE=HERE/"fixture.py"


def sha256_bytes(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()

def sha256_file(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1<<20),b""):
            h.update(chunk)
    return h.hexdigest()

def git_blob_sha(path:Path)->str:
    b=path.read_bytes(); return hashlib.sha1(f"blob {len(b)}\0".encode()+b).hexdigest()

def now_ns(): return time.monotonic_ns()

def image_bytes(reply):
    if reply is None: raise RuntimeError("capture_none")
    data=reply.data
    if isinstance(data,str): data=data.encode("latin1")
    return bytes(data)

def capture(source,x,y,w,h):
    t0=now_ns(); rep=source.get_image(x,y,w,h,X.ZPixmap,0xffffffff); t1=now_ns()
    b=image_bytes(rep)
    return b,{"started_ns":t0,"ended_ns":t1,"bytes":len(b),"sha256":sha256_bytes(b)}

def geom(root,win):
    t0=now_ns(); tr=root.translate_coords(win,0,0); g=win.get_geometry(); t1=now_ns()
    return {"x":int(tr.x),"y":int(tr.y),"w":int(g.width),"h":int(g.height),"started_ns":t0,"ended_ns":t1}

def app_cmd(app,obj):
    line=json.dumps(obj,separators=(",",":"),sort_keys=True)
    app.stdin.write(line+"\n"); app.stdin.flush()
    raw=app.stdout.readline()
    if not raw: raise RuntimeError(f"fixture_eof:{app.stderr.read()}")
    return line,json.loads(raw)

def start_display(case_dir:Path,display_num:int):
    auth=case_dir/"Xauthority"
    cookie=hashlib.sha256(f"q5t2-{display_num}-{case_dir.name}".encode()).hexdigest()[:32]
    subprocess.run(["xauth","-f",str(auth),"add",f":{display_num}","MIT-MAGIC-COOKIE-1",cookie],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True)
    argv=["Xvfb",f":{display_num}","-screen","0","400x300x24","-nolisten","tcp","-auth",str(auth)]
    xv=subprocess.Popen(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    sock=Path(f"/tmp/.X11-unix/X{display_num}")
    for _ in range(200):
        if sock.exists(): break
        if xv.poll() is not None: raise RuntimeError(f"xvfb_exit:{xv.returncode}:{xv.stderr.read()}")
        time.sleep(.005)
    if not sock.exists(): raise RuntimeError("xvfb_socket_timeout")
    env=os.environ.copy(); env["DISPLAY"]=f":{display_num}"; env["XAUTHORITY"]=str(auth)
    return xv,env,sock,argv

def run_case(out:Path,index:int,rep:int,policy:str,schedule:str,display_num:int):
    out.mkdir(parents=True,exist_ok=False)
    rec={"schema":"x11-region-frame-move-case-v1","case_index":index,"rep":rep,"policy":policy,"schedule":schedule,"issue":ISSUE,"base_main":BASE_MAIN,"authority":AUTHORITY,"task_success":TASK_SUCCESS,"events":[],"files":{},"process":{}}
    xv=app=d=None; sock=None
    oldenv=(os.environ.get("DISPLAY"),os.environ.get("XAUTHORITY"))
    try:
        xv,env,sock,xvargv=start_display(out,display_num)
        rec["process"]["xvfb_argv"]=xvargv; rec["process"]["xvfb_pid"]=xv.pid
        app=subprocess.Popen([sys.executable,"-S","-u",str(FIXTURE)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=env)
        rec["process"]["app_pid"]=app.pid; rec["process"]["app_argv"]=[sys.executable,"-S","-u",str(FIXTURE)]
        ready_raw=app.stdout.readline();
        if not ready_raw: raise RuntimeError(f"fixture_start_eof:{app.stderr.read()}")
        ready=json.loads(ready_raw); rec["events"].append({"kind":"fixture_ready","payload":ready,"observed_ns":now_ns()})
        if ready.get("type")!="READY": raise RuntimeError(f"bad_ready:{ready}")
        os.environ["DISPLAY"]=env["DISPLAY"]; os.environ["XAUTHORITY"]=env["XAUTHORITY"]
        d=display.Display(env["DISPLAY"]); root=d.screen().root; win=d.create_resource_object("window",int(ready["xid"])); d.sync()
        rec["target_xid_initial"]=int(ready["xid"])
        initial_geom=geom(root,win); rec["initial_geometry"]=initial_geom
        initial,imeta=capture(win,0,0,WIDTH,HEIGHT); (out/"initial_window.bin").write_bytes(initial); rec["files"]["initial_window.bin"]={"sha256":sha256_bytes(initial),"bytes":len(initial)}; rec["initial_capture"]=imeta
        pinned={k:initial_geom[k] for k in ("x","y","w","h")}
        moved=False
        def do_move(label):
            nonlocal moved
            req,resp=app_cmd(app,{"cmd":"move","x":MOVED[0],"y":MOVED[1]}); moved=True; d.sync(); rec["events"].append({"kind":label,"request":req,"response":resp,"observed_ns":now_ns()}); return resp
        if schedule=="MOVE_BEFORE": do_move("move_before")
        resolved=None
        if policy=="PINNED_SCREEN":
            resolved=dict(pinned); rec["events"].append({"kind":"use_pinned_geometry","geometry":resolved,"observed_ns":now_ns()})
        elif policy=="REFRESH_SCREEN":
            resolved=geom(root,win); rec["events"].append({"kind":"refresh_geometry","geometry":resolved,"observed_ns":now_ns()})
        elif policy=="WINDOW_CLIENT":
            rec["events"].append({"kind":"window_client_prepare","observed_ns":now_ns()})
        else: raise RuntimeError(policy)
        if schedule=="MOVE_BETWEEN": do_move("move_between")
        if policy in {"PINNED_SCREEN","REFRESH_SCREEN"}:
            candidate,cmeta=capture(root,int(resolved["x"]),int(resolved["y"]),WIDTH,HEIGHT)
            rec["candidate_source"]="root"; rec["candidate_screen_geometry"]={k:int(resolved[k]) for k in ("x","y","w","h")}
        else:
            candidate,cmeta=capture(win,0,0,WIDTH,HEIGHT); rec["candidate_source"]="window"; rec["candidate_screen_geometry"]=None
        (out/"candidate.bin").write_bytes(candidate); rec["files"]["candidate.bin"]={"sha256":sha256_bytes(candidate),"bytes":len(candidate)}; rec["candidate_capture"]=cmeta
        final_geom=geom(root,win); rec["final_geometry"]=final_geom
        scorer_window,swmeta=capture(win,0,0,WIDTH,HEIGHT); (out/"scorer_window.bin").write_bytes(scorer_window); rec["files"]["scorer_window.bin"]={"sha256":sha256_bytes(scorer_window),"bytes":len(scorer_window)}; rec["scorer_window_capture"]=swmeta
        scorer_root,srmeta=capture(root,int(final_geom["x"]),int(final_geom["y"]),WIDTH,HEIGHT); (out/"scorer_root.bin").write_bytes(scorer_root); rec["files"]["scorer_root.bin"]={"sha256":sha256_bytes(scorer_root),"bytes":len(scorer_root)}; rec["scorer_root_capture"]=srmeta
        rec["candidate_matches_current_window"]=candidate==scorer_window
        rec["scorer_window_matches_current_root"]=scorer_window==scorer_root
        rec["target_pixels_unchanged"]=initial==scorer_window
        req,state=app_cmd(app,{"cmd":"state"}); rec["events"].append({"kind":"fixture_final_state","request":req,"response":state,"observed_ns":now_ns()}); rec["target_xid_final"]=int(state["xid"])
        if rec["candidate_screen_geometry"] is not None:
            cg=rec["candidate_screen_geometry"]
            rec["stale_coordinate_witness"]=(cg["x"]!=final_geom["x"] or cg["y"]!=final_geom["y"]) and not rec["candidate_matches_current_window"]
        else: rec["stale_coordinate_witness"]=False
        req,closed=app_cmd(app,{"cmd":"close"}); rec["events"].append({"kind":"fixture_close","request":req,"response":closed,"observed_ns":now_ns()})
        app.wait(timeout=2); rec["process"]["app_exit"]=app.returncode; rec["process"]["app_stderr"]=app.stderr.read()
        d.close(); d=None
        xv.terminate(); xv.wait(timeout=2); rec["process"]["xvfb_exit"]=xv.returncode; rec["process"]["xvfb_stderr"]=xv.stderr.read(); xv=None
        time.sleep(.01); rec["process"]["socket_absent_after_cleanup"]=not sock.exists()
        rec["complete"]=True
    except Exception as exc:
        rec["complete"]=False; rec["error"]=repr(exc)
        raise
    finally:
        if d is not None:
            try:d.close()
            except Exception:pass
        if app is not None and app.poll() is None:
            try:app.kill();app.wait(timeout=1)
            except Exception:pass
        if xv is not None and xv.poll() is None:
            try:xv.kill();xv.wait(timeout=1)
            except Exception:pass
        if oldenv[0] is None: os.environ.pop("DISPLAY",None)
        else: os.environ["DISPLAY"]=oldenv[0]
        if oldenv[1] is None: os.environ.pop("XAUTHORITY",None)
        else: os.environ["XAUTHORITY"]=oldenv[1]
        rec["source_hashes"]={p.name:sha256_file(p) for p in sorted(HERE.glob("*.py"))}
        rec["source_git_blobs"]={p.name:git_blob_sha(p) for p in sorted(HERE.glob("*.py"))}
        (out/"CASE.json").write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n")
    return rec

def matrix(rep):
    # Rotate policy order across repetitions while preserving all 9 cells.
    order=list(POLICIES[rep%3:]+POLICIES[:rep%3])
    return [(p,s) for s in SCHEDULES for p in order]

def run_batch(root:Path,rep:int,construction=False):
    root.mkdir(parents=True,exist_ok=True)
    batch=root/f"batch-{rep}"
    if batch.exists(): raise RuntimeError(f"batch_exists:{batch}")
    batch.mkdir()
    rows=[]; started=now_ns()
    for j,(policy,schedule) in enumerate(matrix(rep)):
        idx=rep*9+j
        display_num=220+(idx%60)
        rows.append(run_case(batch/f"case-{idx:03d}",idx,rep,policy,schedule,display_num))
    end={"schema":"x11-region-frame-move-batch-v1","rep":rep,"construction":construction,"case_count":len(rows),"started_ns":started,"ended_ns":now_ns(),"cases":[r["case_index"] for r in rows],"complete":all(r.get("complete") for r in rows)}
    (batch/"END.json").write_text(json.dumps(end,indent=2,sort_keys=True)+"\n")
    return end

def main():
    ap=argparse.ArgumentParser(); sp=ap.add_subparsers(dest="cmd",required=True)
    rb=sp.add_parser("run-batch"); rb.add_argument("--root",required=True); rb.add_argument("--rep",type=int,required=True); rb.add_argument("--construction",action="store_true")
    args=ap.parse_args()
    if args.cmd=="run-batch":
        if args.rep not in (0,1,2): raise SystemExit("rep must be 0..2")
        print(json.dumps(run_batch(Path(args.root),args.rep,args.construction),sort_keys=True))
if __name__=="__main__": main()
