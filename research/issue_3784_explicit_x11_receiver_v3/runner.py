"""Issue #3796 formal-03: whitespace-safe map gates before candidate delivery."""
from __future__ import annotations
import hashlib, importlib.util, json, os, re, subprocess, sys, time
from pathlib import Path
from Xlib import X, XK, display

ALLOCATION="issue3784-explicit-x11-receiver-formal-03"
BASE="1355ff9c0e89e04887e7dd3a08aaa93c7b650df0"
IMAGE="agent-interface-2972@sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27"
FORMULA="=B2*A2";UNSUPPORTED="=B2*A2€";ROOT=Path(__file__).resolve().parent
def sha(b):return hashlib.sha256(b).hexdigest()
def blob(b):return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def fp(m):return sha(json.dumps(m,sort_keys=True,separators=(",",":")).encode())
def helpers(source):
    path=source/"research/issue_3784_explicit_x11_receiver_v1/runner.py"
    spec=importlib.util.spec_from_file_location("issue3784_shared_x11_helpers",path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
def map_now(name):
    d=display.Display(name)
    try:
        i=d.display.info;r=d.get_keyboard_mapping(i.min_keycode,i.max_keycode-i.min_keycode+1)
        return {"min_keycode":int(i.min_keycode),"max_keycode":int(i.max_keycode),"rows":[[int(v) for v in row] for row in r]}
    finally:d.close()
def capture(name,layout):
    q=subprocess.run(["setxkbmap","-query","-display",name],capture_output=True,text=True)
    x=subprocess.run(["xkbcomp","-xkb",name,"-"],capture_output=True,text=True);m=map_now(name)
    return {"query":{"argv":["setxkbmap","-query","-display",name],"exit":q.returncode,"stdout":q.stdout,"stderr":q.stderr},
      "dump_exit":x.returncode,"dump":x.stdout,"dump_sha256":sha(x.stdout.encode()),"map":m,"map_sha256":fp(m),
      "layout_ok":bool(re.search(r"(?m)^layout:\s+"+re.escape(layout)+r"\s*$",q.stdout))}
def identity(pid):
    try:return Path(f"/proc/{pid}/stat").read_text().split()[21]
    except (OSError,IndexError):return None
def start_xvfb(name,folder):
    log=(folder/"xvfb.log").open("wb")
    argv=["/usr/bin/Xvfb",name,"-screen","0","800x600x24","-nolisten","tcp","+extension","XKEYBOARD","+extension","XTEST","-noreset"]
    proc=subprocess.Popen(argv,stdout=log,stderr=subprocess.STDOUT)
    end=time.monotonic()+8;d=None
    while time.monotonic()<end:
        if proc.poll() is not None:break
        try:d=display.Display(name);break
        except Exception:time.sleep(.05)
    return proc,log,d,argv
def close_xvfb(proc,log,d,lookup,backend):
    if backend:
        try:backend.close()
        except Exception:pass
    if lookup:
        try:lookup.close()
        except Exception:pass
    if d:
        try:d.close()
        except Exception:pass
    if proc.poll() is None:proc.terminate()
    try:rc=proc.wait(timeout=4)
    except subprocess.TimeoutExpired:proc.kill();rc=proc.wait(timeout=4)
    log.close();return {"returncode":rc,"reaped":proc.poll() is not None}

def construction_case(name,layout,mutate,helper):
    """Complete construction-only receiver + US-to-DE map transition gate."""
    import tempfile
    os.environ["DISPLAY"]=name
    with tempfile.TemporaryDirectory() as temp:
        folder=Path(temp);proc,log,d,argv=start_xvfb(name,folder);lookup=backend=None
        result={"display":name,"layout":layout,"xvfb_argv":argv,"xvfb_pid":proc.pid,"xvfb_start_ticks":identity(proc.pid)}
        try:
            if d is None:raise RuntimeError("STOP_XVFB_CONNECT")
            win=d.screen().root.create_window(0,0,1,1,0,X.CopyFromParent,X.InputOnly,X.CopyFromParent,event_mask=X.KeyPressMask|X.KeyReleaseMask)
            win.map();win.set_input_focus(X.RevertToParent,X.CurrentTime);d.sync();focus=d.get_input_focus().focus
            result["focus_ok"]=getattr(focus,"id",None)==win.id
            lookup=helper.Lookup();code=d.keysym_to_keycode(XK.string_to_keysym("a"))
            from Xlib.ext import xtest
            xtest.fake_input(d,X.KeyPress,code);d.sync();xtest.fake_input(d,X.KeyRelease,code);d.sync()
            ev=helper.drain(d,lookup)
            result["control"]=[(e["type"],e["keycode"],e["keysym"],e["lookup_text"]) for e in ev]
            result["control_ok"]=result["control"]==[("KeyPress",code,97,"a"),("KeyRelease",code,97,"a")]
            before=capture(name,"us");result["baseline"]={k:v for k,v in before.items() if k!="dump"}
            if not result["focus_ok"] or not result["control_ok"] or not before["layout_ok"] or before["dump_exit"]!=0:
                result["status"]="STOP_CONSTRUCTION_BASELINE";return result
            if mutate:
                p=subprocess.run(["setxkbmap","-layout","de"],capture_output=True,text=True)
                result["apply"]={"argv":["setxkbmap","-layout","de"],"exit":p.returncode,"stderr":p.stderr}
            else:result["apply"]={"argv":None,"exit":0}
            time.sleep(.2);after=capture(name,layout);result["after"]={k:v for k,v in after.items() if k!="dump"}
            changed=before["dump_sha256"]!=after["dump_sha256"] and before["map_sha256"]!=after["map_sha256"]
            result["map_gate_ok"]=after["layout_ok"] and after["dump_exit"]==0 and (changed if mutate else not changed)
            result["status"]="PASS_CONSTRUCTION" if result["map_gate_ok"] and result["apply"]["exit"]==0 else "STOP_CONSTRUCTION_MAP"
            return result
        finally:result["cleanup"]=close_xvfb(proc,log,d,lookup,backend)

def formal_row(cid,layout,index,source,out,h):
    name=f":{221+index}";os.environ["DISPLAY"]=name;os.environ["PYTHONPATH"]=str(source)
    folder=out/"cases"/cid;folder.mkdir(parents=True);proc,log,d,argv=start_xvfb(name,folder);lookup=backend=None
    row={"case_id":cid,"layout":layout,"xvfb_argv":argv,"xvfb_pid":proc.pid,"xvfb_start_ticks":identity(proc.pid),"status":"STOP_SETUP"}
    try:
        if d is None:row["status"]="STOP_XVFB_CONNECT";return row
        win=d.screen().root.create_window(0,0,1,1,0,X.CopyFromParent,X.InputOnly,X.CopyFromParent,event_mask=X.KeyPressMask|X.KeyReleaseMask)
        win.map();win.set_input_focus(X.RevertToParent,X.CurrentTime);d.sync();focus=d.get_input_focus().focus
        row["receiver"]={"window_id":int(win.id),"class":"InputOnly","mapped":True,"event_mask":3,"focus_window_id":int(getattr(focus,"id",0))}
        row["focus_verified"]=getattr(focus,"id",None)==win.id
        lookup=h.Lookup();code=d.keysym_to_keycode(XK.string_to_keysym("a"));from Xlib.ext import xtest
        xtest.fake_input(d,X.KeyPress,code);d.sync();xtest.fake_input(d,X.KeyRelease,code);d.sync();control=h.drain(d,lookup)
        row["receiver_control"]=control
        row["receiver_control_ok"]=(len(control)==2 and [(e["type"],e["keycode"],e["keysym"],e["lookup_text"]) for e in control]==[("KeyPress",code,97,"a"),("KeyRelease",code,97,"a")])
        if not row["focus_verified"] or not row["receiver_control_ok"]:row["status"]="STOP_RECEIVER_CONTROL";return row
        base=capture(name,"us");row["baseline"]=base
        if not base["layout_ok"] or base["dump_exit"]!=0:row["status"]="STOP_BASELINE";return row
        if layout=="de":
            p=subprocess.run(["setxkbmap","-layout","de"],capture_output=True,text=True)
            row["apply"]={"argv":["setxkbmap","-layout","de"],"exit":p.returncode,"stdout":p.stdout,"stderr":p.stderr}
        else:row["apply"]={"argv":None,"exit":0}
        time.sleep(.2);after=capture(name,layout);row["after"]=after
        change=layout=="de";row["map_gate"]={"query_layout":after["layout_ok"],"dump_changed":base["dump_sha256"]!=after["dump_sha256"],"fresh_map_changed":base["map_sha256"]!=after["map_sha256"]}
        if after["dump_exit"]!=0 or not after["layout_ok"] or row["map_gate"]["dump_changed"]!=change or row["map_gate"]["fresh_map_changed"]!=change or row["apply"]["exit"]!=0:
            row["status"]="STOP_ACTIVE_MAP";return row
        lookup.close();lookup=h.Lookup()
        from runtime.backends.x11_v1.backend import X11Backend
        backend=X11Backend(name,{"receiver":int(win.id)})
        pre= h.drain(d,lookup,timeout=.25,quiet=.1);error=None
        try:backend._text_plan(UNSUPPORTED)
        except Exception as e:error=str(e)
        post=h.drain(d,lookup,timeout=.25,quiet=.1)
        row["unsupported"]={"error":error,"before_events":pre,"after_events":post,"emissions":backend.emissions,
                             "refused_zero_event":bool(error and "U+20AC" in error and not pre and not post and backend.emissions==0)}
        if not row["unsupported"]["refused_zero_event"]:row["status"]="FAIL_UNSUPPORTED_PREFLIGHT";return row
        plan=backend._text_plan(FORMULA);codes=[[backend._keycode(k) for k in chord] for chord in plan]
        row["plan_keycodes"]=codes;backend.focus("receiver");backend.text(FORMULA);events=h.drain(d,lookup,timeout=4,quiet=.25)
        row["events"]=events;row["typed"]="".join(e["lookup_text"] for e in events if e["type"]=="KeyPress");row["emissions"]=backend.emissions
        row["release"]=backend.release_all();expected=[]
        for chord in codes:expected += [("KeyPress",k) for k in chord]+[("KeyRelease",k) for k in reversed(chord)]
        actual=[(e["type"],e["keycode"]) for e in events]
        row["event_trace_matches_plan"]=actual==expected
        row["status"]="PASS_ROW" if row["typed"]==FORMULA and actual==expected and row["emissions"]==len(expected) and row["release"].get("verified") else "FAIL_DELIVERY"
        return row
    except Exception as e:row["status"]="STOP_EXCEPTION";row["error"]=repr(e);return row
    finally:row["xvfb_cleanup"]=close_xvfb(proc,log,d,lookup,backend)

def main():
    if len(sys.argv)!=3:raise SystemExit("usage runner.py SOURCE OUTPUT")
    source,out=map(lambda p:Path(p).resolve(),sys.argv[1:]);out.mkdir(parents=True,exist_ok=True)
    if any(out.iterdir()):raise SystemExit("STOP_OUTPUT_NOT_EMPTY")
    manifestb=(ROOT/"source_manifest.json").read_bytes();manifest=json.loads(manifestb)
    if manifest.get("base_commit")!=BASE:raise SystemExit("STOP_BASE")
    for path,expected in manifest["files"].items():
        data=(source/path).read_bytes()
        if sha(data)!=expected["sha256"] or blob(data)!=expected["git_blob_sha1"]:raise SystemExit("STOP_SOURCE_HASH:"+path)
    h=helpers(source)
    construction=[construction_case(":217","de",True,h),construction_case(":218","us",False,h)]
    (out/"construction.json").write_text(json.dumps(construction,sort_keys=True,indent=2)+"\n")
    if any(x.get("status")!="PASS_CONSTRUCTION" for x in construction):
        raw={"allocation":ALLOCATION,"base_commit":BASE,"image":IMAGE,"runner_sha256":sha(Path(__file__).read_bytes()),"source_manifest_sha256":sha(manifestb),"construction":construction,"rows":[],"disposition":"STOP_CONSTRUCTION_GATE"}
        raw["artifact_sha256"]={p.relative_to(out).as_posix():sha(p.read_bytes()) for p in sorted(out.rglob("*")) if p.is_file() and p.name!="raw.json"}
        (out/"raw.json").write_text(json.dumps(raw,sort_keys=True,indent=2)+"\n");print(json.dumps({"disposition":raw["disposition"],"construction":[x["status"] for x in construction]}));return 1
    rows=[formal_row("de-01","de",0,source,out,h),formal_row("de-02","de",1,source,out,h),formal_row("de-03","de",2,source,out,h),formal_row("us-control","us",3,source,out,h)]
    for r in rows:
        case=out/"cases"/r["case_id"];case.mkdir(parents=True,exist_ok=True);(case/"row.json").write_text(json.dumps(r,sort_keys=True,indent=2,ensure_ascii=False)+"\n")
        for phase in ("baseline","after"):
            if phase in r:
                (case/(phase+".xkb")).write_text(r[phase]["dump"]);(case/(phase+".map.json")).write_text(json.dumps(r[phase]["map"],sort_keys=True)+"\n")
    disp="PASS_GERMAN_FORMULA_DELIVERY" if all(r["status"]=="PASS_ROW" for r in rows) else "FAIL_GERMAN_FORMULA_DELIVERY" if any(r["status"].startswith("FAIL_") for r in rows) else "STOP_GERMAN_FORMULA_DELIVERY"
    raw={"allocation":ALLOCATION,"base_commit":BASE,"image":IMAGE,"runner_sha256":sha(Path(__file__).read_bytes()),"source_manifest_sha256":sha(manifestb),"construction":construction,"rows":rows,"disposition":disp}
    raw["artifact_sha256"]={p.relative_to(out).as_posix():sha(p.read_bytes()) for p in sorted(out.rglob("*")) if p.is_file() and p.name!="raw.json"}
    (out/"raw.json").write_text(json.dumps(raw,sort_keys=True,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({"disposition":disp,"construction":[x["status"] for x in construction],"rows":[(r["case_id"],r["status"],r.get("typed")) for r in rows]},ensure_ascii=False));return 0 if disp.startswith("PASS_") else 1
if __name__=="__main__":raise SystemExit(main())
