"""One-shot formal-02 receiver and German text experiment for Issue #3791."""
from __future__ import annotations
import ctypes, hashlib, json, os, subprocess, sys, time
from pathlib import Path
from Xlib import X, XK, display
from Xlib.ext import xtest

ALLOCATION = "issue3784-explicit-x11-receiver-formal-02"
BASE = "f5f9ff842fd061e6e1eb2f43a17cc7785b807fc7"
IMAGE = "agent-interface-2972@sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27"
FORMULA, UNSUPPORTED = "=B2*A2", "=B2*A2€"
ROOT = Path(__file__).resolve().parent

def sha(b): return hashlib.sha256(b).hexdigest()
def blob(b): return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def fingerprint(m): return sha(json.dumps(m,sort_keys=True,separators=(",",":")).encode())

class XKeyEvent(ctypes.Structure):
    _fields_=[("type",ctypes.c_int),("serial",ctypes.c_ulong),("send_event",ctypes.c_int),
      ("display",ctypes.c_void_p),("window",ctypes.c_ulong),("root",ctypes.c_ulong),
      ("subwindow",ctypes.c_ulong),("time",ctypes.c_ulong),("x",ctypes.c_int),
      ("y",ctypes.c_int),("x_root",ctypes.c_int),("y_root",ctypes.c_int),
      ("state",ctypes.c_uint),("keycode",ctypes.c_uint),("same_screen",ctypes.c_int)]

class Lookup:
    def __init__(self):
        self.lib=ctypes.CDLL("libX11.so.6")
        self.lib.XOpenDisplay.argtypes=[ctypes.c_char_p]; self.lib.XOpenDisplay.restype=ctypes.c_void_p
        self.lib.XLookupString.argtypes=[ctypes.POINTER(XKeyEvent),ctypes.c_char_p,ctypes.c_int,ctypes.POINTER(ctypes.c_ulong),ctypes.c_void_p]
        self.lib.XLookupString.restype=ctypes.c_int
        self.ptr=self.lib.XOpenDisplay(os.environ["DISPLAY"].encode())
        if not self.ptr: raise RuntimeError("STOP_XLOOKUP_OPEN")
    def get(self,e):
        row=XKeyEvent(e.type,0,0,self.ptr,e.window.id,0,0,e.time,0,0,0,0,e.state,e.detail,1)
        out=ctypes.create_string_buffer(64); sym=ctypes.c_ulong()
        n=self.lib.XLookupString(ctypes.byref(row),out,64,ctypes.byref(sym),None)
        return {"keysym":int(sym.value),"lookup_hex":out.raw[:n].hex(),"lookup_text":out.raw[:n].decode("ascii","replace")}
    def close(self):
        self.lib.XCloseDisplay.argtypes=[ctypes.c_void_p]; self.lib.XCloseDisplay(self.ptr)

def drain(d, lookup, timeout=2, quiet=.15):
    result=[]; end=time.monotonic()+timeout; last=time.monotonic()
    while time.monotonic()<end:
        d.sync()
        while d.pending_events():
            e=d.next_event()
            if e.type in (X.KeyPress,X.KeyRelease):
                result.append({"type":"KeyPress" if e.type==X.KeyPress else "KeyRelease",
                    "keycode":int(e.detail),"state":int(e.state),**lookup.get(e)})
                last=time.monotonic()
        if result and time.monotonic()-last>=quiet: break
        time.sleep(.01)
    return result

def keymap(display_name):
    d=display.Display(display_name)
    try:
        info=d.display.info; rows=d.get_keyboard_mapping(info.min_keycode,info.max_keycode-info.min_keycode+1)
        return {"min_keycode":int(info.min_keycode),"max_keycode":int(info.max_keycode),"rows":[[int(v) for v in r] for r in rows]}
    finally: d.close()

def capture(display_name, layout):
    q=subprocess.run(["setxkbmap","-query","-display",display_name],capture_output=True,text=True)
    x=subprocess.run(["xkbcomp","-xkb",display_name,"-"],capture_output=True,text=True)
    m=keymap(display_name)
    return {"query":{"argv":["setxkbmap","-query","-display",display_name],"exit":q.returncode,"stdout":q.stdout,"stderr":q.stderr},
      "dump_exit":x.returncode,"dump":x.stdout,"dump_sha256":sha(x.stdout.encode()),"map":m,"map_sha256":fingerprint(m),
      "layout_ok":any(s.strip()=="layout: "+layout for s in q.stdout.splitlines())}

def ticks(pid):
    try:return Path(f"/proc/{pid}/stat").read_text().split()[21]
    except (OSError,IndexError):return None

def run_row(cid,layout,index,source,out):
    name=f":{211+index}"; os.environ["DISPLAY"]=name; os.environ["PYTHONPATH"]=str(source)
    folder=out/"cases"/cid; folder.mkdir(parents=True)
    log=(folder/"xvfb.log").open("wb")
    argv=["/usr/bin/Xvfb",name,"-screen","0","800x600x24","-nolisten","tcp","+extension","XKEYBOARD","+extension","XTEST","-noreset"]
    xvfb=subprocess.Popen(argv,stdout=log,stderr=subprocess.STDOUT)
    row={"case_id":cid,"layout":layout,"xvfb_argv":argv,"xvfb_pid":xvfb.pid,"xvfb_start_ticks":ticks(xvfb.pid),"status":"STOP_SETUP"}
    d=backend=lookup=None
    try:
        deadline=time.monotonic()+8
        while time.monotonic()<deadline:
            if xvfb.poll() is not None: raise RuntimeError("STOP_XVFB_EXIT:"+str(xvfb.returncode))
            try:d=display.Display(name); break
            except Exception:time.sleep(.05)
        if d is None: row["status"]="STOP_XVFB_CONNECT"; return row
        w=d.screen().root.create_window(0,0,1,1,0,X.CopyFromParent,X.InputOnly,X.CopyFromParent,
            event_mask=X.KeyPressMask|X.KeyReleaseMask)
        w.map(); w.set_input_focus(X.RevertToParent,X.CurrentTime); d.sync()
        focus=d.get_input_focus().focus
        row["receiver"]={"window_id":int(w.id),"class":"InputOnly","mapped":True,"event_mask":3,
                         "focus_window_id":int(getattr(focus,"id",0))}
        row["focus_verified"]=getattr(focus,"id",None)==w.id
        if not row["focus_verified"]: row["status"]="STOP_FOCUS"; return row
        lookup=Lookup(); code=d.keysym_to_keycode(XK.string_to_keysym("a"))
        xtest.fake_input(d,X.KeyPress,code); d.sync(); xtest.fake_input(d,X.KeyRelease,code); d.sync()
        control=drain(d,lookup)
        row["receiver_control"]=control
        row["receiver_control_ok"]=(len(control)==2 and [(e["type"],e["keycode"],e["keysym"],e["lookup_text"]) for e in control]
            ==[("KeyPress",code,97,"a"),("KeyRelease",code,97,"a")])
        if not row["receiver_control_ok"]: row["status"]="STOP_RECEIVER_CONTROL"; return row

        row["baseline"]=capture(name,"us")
        if not row["baseline"]["layout_ok"] or row["baseline"]["dump_exit"]!=0:
            row["status"]="STOP_BASELINE"; return row
        if layout=="de":
            p=subprocess.run(["setxkbmap","-layout","de"],capture_output=True,text=True)
            row["apply"]={"argv":["setxkbmap","-layout","de"],"exit":p.returncode,"stdout":p.stdout,"stderr":p.stderr}
        else: row["apply"]={"argv":None,"exit":0,"stdout":"US control","stderr":""}
        time.sleep(.2); row["after"]=capture(name,layout)
        row["map_gate"]={"query_layout":row["after"]["layout_ok"],
          "dump_changed":row["baseline"]["dump_sha256"]!=row["after"]["dump_sha256"],
          "fresh_map_changed":row["baseline"]["map_sha256"]!=row["after"]["map_sha256"]}
        change=layout=="de"
        if (row["after"]["dump_exit"]!=0 or not row["map_gate"]["query_layout"] or
            row["map_gate"]["dump_changed"]!=change or row["map_gate"]["fresh_map_changed"]!=change or row["apply"]["exit"]!=0):
            row["status"]="STOP_ACTIVE_MAP"; return row
        lookup.close(); lookup=Lookup()
        from runtime.backends.x11_v1.backend import X11Backend
        backend=X11Backend(name,{"receiver":int(w.id)})
        before=drain(d,lookup,timeout=.25,quiet=.1)
        refusal=None
        try:backend._text_plan(UNSUPPORTED)
        except Exception as e:refusal=str(e)
        after=drain(d,lookup,timeout=.25,quiet=.1)
        row["unsupported"]={"error":refusal,"before_events":before,"after_events":after,"emissions":backend.emissions,
          "refused_zero_event":refusal is not None and "U+20AC" in refusal and not before and not after and backend.emissions==0}
        if not row["unsupported"]["refused_zero_event"]: row["status"]="FAIL_UNSUPPORTED_PREFLIGHT"; return row
        plan=backend._text_plan(FORMULA); codes=[[backend._keycode(k) for k in chord] for chord in plan]
        row["plan_keycodes"]=codes; backend.focus("receiver"); backend.text(FORMULA)
        events=drain(d,lookup,timeout=4,quiet=.25); row["events"]=events
        row["typed"]="".join(e["lookup_text"] for e in events if e["type"]=="KeyPress")
        row["emissions"]=backend.emissions; row["release"]=backend.release_all()
        expected=[]
        for chord in codes:
            expected += [("KeyPress",c) for c in chord]+[("KeyRelease",c) for c in reversed(chord)]
        actual=[(e["type"],e["keycode"]) for e in events]
        row["event_trace_matches_plan"]=actual==expected
        row["status"]="PASS_ROW" if row["typed"]==FORMULA and actual==expected and backend.emissions==len(expected) and row["release"].get("verified") else "FAIL_DELIVERY"
        return row
    except Exception as e:
        row["status"]="STOP_EXCEPTION"; row["error"]=repr(e); return row
    finally:
        if backend:
            try:backend.close()
            except Exception:pass
        if lookup:
            try:lookup.close()
            except Exception:pass
        if d:
            try:d.close()
            except Exception:pass
        if xvfb.poll() is None:xvfb.terminate()
        try:rc=xvfb.wait(timeout=4)
        except subprocess.TimeoutExpired:xvfb.kill(); rc=xvfb.wait(timeout=4)
        row["xvfb_cleanup"]={"returncode":rc,"reaped":xvfb.poll() is not None}; log.close()

def main():
    if len(sys.argv)!=3:raise SystemExit("usage runner.py SOURCE OUTPUT")
    source,out=map(lambda p:Path(p).resolve(),sys.argv[1:]); out.mkdir(parents=True,exist_ok=True)
    if any(out.iterdir()):raise SystemExit("STOP_OUTPUT_NOT_EMPTY")
    mb=(ROOT/"source_manifest.json").read_bytes(); manifest=json.loads(mb)
    if manifest.get("base_commit")!=BASE:raise SystemExit("STOP_MANIFEST_BASE")
    for p,e in manifest["files"].items():
        data=(source/p).read_bytes()
        if sha(data)!=e["sha256"] or blob(data)!=e["git_blob_sha1"]:raise SystemExit("STOP_SOURCE_HASH:"+p)
    rows=[run_row("de-01","de",0,source,out),run_row("de-02","de",1,source,out),run_row("de-03","de",2,source,out),run_row("us-control","us",3,source,out)]
    for r in rows:
        d=out/"cases"/r["case_id"]; d.mkdir(parents=True,exist_ok=True)
        (d/"row.json").write_text(json.dumps(r,sort_keys=True,indent=2,ensure_ascii=False)+"\n")
        for phase in ("baseline","after"):
            if phase in r:
                (d/(phase+".xkb")).write_text(r[phase]["dump"])
                (d/(phase+".map.json")).write_text(json.dumps(r[phase]["map"],sort_keys=True)+"\n")
    artifacts={p.relative_to(out).as_posix():sha(p.read_bytes()) for p in sorted(out.rglob("*")) if p.is_file() and p.name!="raw.json"}
    disp="PASS_GERMAN_FORMULA_DELIVERY" if all(r["status"]=="PASS_ROW" for r in rows) else "FAIL_GERMAN_FORMULA_DELIVERY" if any(r["status"].startswith("FAIL_") for r in rows) else "STOP_GERMAN_FORMULA_DELIVERY"
    raw={"schema":"agent-interface/issue3784-formal02-raw-v1","allocation":ALLOCATION,"base_commit":BASE,"image":IMAGE,
      "runner_sha256":sha(Path(__file__).read_bytes()),"source_manifest_sha256":sha(mb),"rows":rows,"artifact_sha256":artifacts,"disposition":disp}
    (out/"raw.json").write_text(json.dumps(raw,sort_keys=True,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({"disposition":disp,"rows":[(r["case_id"],r["status"],r.get("typed"),len(r.get("events",[]))) for r in rows]}))
    return 0 if disp.startswith("PASS_") else 1
if __name__=="__main__":raise SystemExit(main())
