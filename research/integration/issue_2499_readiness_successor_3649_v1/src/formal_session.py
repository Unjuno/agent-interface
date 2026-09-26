"""One frozen, model-free mixed-app session for successor Issue #2499.

The ledger is intentionally independent of Agent Interface implementation. It
records the OS-visible identities and the admission decisions needed to audit
the four transitions; it does not claim model quality or product support.
"""
import hashlib, json, os, re, signal, subprocess, tempfile, time, traceback
from pathlib import Path
from readiness import resolve_candidates

DISPLAY = ":159"
FAILED_LAUNCHES=[]

def cmd(argv, env, timeout=15):
    return subprocess.run(argv, env=env, text=True, capture_output=True,
                          timeout=timeout, check=False)

def windows(env):
    q = cmd(["xdotool", "search", "--onlyvisible", "--name", ".*"], env)
    return sorted({x.strip() for x in q.stdout.splitlines() if x.strip()}, key=int)

def active(env):
    q = cmd(["xdotool", "getactivewindow"], env)
    return q.stdout.strip() if q.returncode == 0 else None

def geom(env, wid):
    if not isinstance(wid, str) or not wid.strip():
        raise RuntimeError("STOP_IDENTITY_MISSING")
    q = cmd(["xdotool", "getwindowgeometry", wid], env)
    if q.returncode != 0 or not q.stdout.strip():
        raise RuntimeError("STOP_IDENTITY_NOT_GEOMETRIZABLE")
    return q.stdout.strip()

def event(ledger, kind, **fields):
    row = {"seq": len(ledger), "kind": kind, **fields}
    row["hash"] = hashlib.sha256(json.dumps(row, sort_keys=True).encode()).hexdigest()
    ledger.append(row)

def setup_xauthority(env, authority):
    result=subprocess.run(["xauth","-f",str(authority),"add",DISPLAY,".","0123456789abcdef0123456789abcdef"],
                          env=env,text=True,capture_output=True,timeout=10,check=False)
    if result.returncode != 0:
        raise RuntimeError("STOP_XAUTH_COOKIE_SETUP:"+result.stderr[-500:])

def wait_window(env, pid=None, before=None, timeout=20, allow_libreoffice=False):
    end = time.time() + timeout
    before = set(before or [])
    while time.time() < end:
        now = windows(env)
        candidates = [x for x in now if x not in before] if pid is None else [x for x in now if x not in before] + [x for x in now if x in before]
        for wid in reversed(candidates):
            props = cmd(["xprop", "-id", wid, "_NET_WM_PID", "WM_CLASS"], env)
            try: geometry = geom(env, wid)
            except RuntimeError: continue
            libre_ok = (allow_libreoffice and "libreoffice-calc" in props.stdout
                        and "Tip of the Day" not in props.stdout
                        and "Untitled" in props.stdout)
            if (pid is None or str(pid) in props.stdout or libre_ok) and geometry and "Geometry: 1x1" not in geometry:
                return wid
        time.sleep(.25)
    return None

def role_candidates(env, role):
    rows=[]
    for wid in windows(env):
        q=cmd(["xprop","-id",wid,"_NET_WM_PID","WM_CLASS","WM_NAME"],env)
        if q.returncode==0: rows.append({"window":wid,"raw":q.stdout})
    return resolve_candidates(role,rows)

def wait_role_window(env, role, before, timeout=25):
    end=time.time()+timeout
    last={"status":"STOP_IDENTITY_MISSING","matches":[]}
    while time.time()<end:
        last=role_candidates(env,role)
        if last["status"]=="READY":
            wid=last["matches"][0]["window"]
            if wid not in before: return wid,last
        elif last["status"]=="STOP_IDENTITY_AMBIGUOUS":
            raise RuntimeError("STOP_IDENTITY_AMBIGUOUS:"+role)
        time.sleep(.25)
    raise RuntimeError(last["status"]+":"+role)

def launch(cmdline, env, role):
    before=set(windows(env))
    p = subprocess.Popen(cmdline, env=env, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, start_new_session=True)
    try:
        wid,identity=wait_role_window(env,role,before)
        geometry=geom(env,wid)
        match=re.search(r"Geometry:\s*(\d+)x(\d+)",geometry)
        if not match or int(match.group(1))<400 or int(match.group(2))<300:
            raise RuntimeError("STOP_IDENTITY_NOT_GEOMETRIZABLE:"+role)
        return p,wid,identity
    except Exception:
        failed_cleanup=stop_process_group(p)
        FAILED_LAUNCHES.append({"role":role,"pid":p.pid,"cleanup":failed_cleanup})
        raise

def stop_process_group(proc):
    if proc is None: return None
    try:
        os.killpg(proc.pid, signal.SIGTERM)
    except ProcessLookupError: pass
    try: returncode=proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        try: os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError: pass
        returncode=proc.wait(timeout=5)
    remaining=[]; deadline=time.time()+2
    while time.time()<deadline:
        ps=subprocess.run(["ps","-eo","pid=,pgid=,stat="],text=True,capture_output=True,check=False)
        remaining=[int(p) for p,g,s in (line.split(None,2) for line in ps.stdout.splitlines() if len(line.split(None,2))==3)
                   if int(g)==proc.pid and not s.startswith("Z")]
        if not remaining: break
        time.sleep(.05)
    if remaining:
        try: os.killpg(proc.pid,signal.SIGKILL)
        except ProcessLookupError: pass
        time.sleep(.1)
        ps=subprocess.run(["ps","-eo","pid=,pgid=,stat="],text=True,capture_output=True,check=False)
        remaining=[int(p) for p,g,s in (line.split(None,2) for line in ps.stdout.splitlines() if len(line.split(None,2))==3)
                   if int(g)==proc.pid and not s.startswith("Z")]
    return {"pid":proc.pid,"returncode":returncode,"remaining_pids":remaining}

def main():
    root = Path(tempfile.mkdtemp(prefix="mixed-formal-2499-3649-"))
    for name in ("home","config","cache","runtime"):
        (root/name).mkdir(mode=0o700)
    authority=root/"Xauthority"
    authority.touch(mode=0o600)
    env = os.environ.copy(); env.update(DISPLAY=DISPLAY,
        HOME=str(root/"home"), XDG_CONFIG_HOME=str(root/"config"),
        XDG_CACHE_HOME=str(root/"cache"), XDG_RUNTIME_DIR=str(root/"runtime"),
        XAUTHORITY=str(authority), SAL_USE_VCLPLUGIN="gen", GDK_BACKEND="x11")
    xvfb=None; wm=None
    procs=[]; ledger=[]; apps={}; checks=[]; input_ops=0; out=None; exit_code=1
    try:
        setup_xauthority(env,authority)
        xvfb = subprocess.Popen(["Xvfb", DISPLAY, "-screen", "0", "1600x1000x24", "-auth",str(authority)], env=env,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,start_new_session=True)
        wm = subprocess.Popen(["openbox", "--replace"], env=env,
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,start_new_session=True)
        time.sleep(.7); event(ledger, "session_setup", display=DISPLAY,
                              xauthority_mode="cookie_auth_file", xauthority_cookie_added=True)
        inkscape, iw, ident = launch(["inkscape"], env,"inkscape")
        procs.append(inkscape); apps["inkscape"]={"pid":inkscape.pid,"window":iw,"identity":ident,"surface_generation":1}
        calc, cw, ident = launch(["libreoffice","--norestore","--nodefault","--nolockcheck","--nofirststartwizard","--calc",
                                  "-env:UserInstallation=file://"+str(root/"lo-profile")], env,"calc")
        procs.append(calc); apps["calc"]={"pid":calc.pid,"window":cw,"identity":ident,"surface_generation":1}
        chrome, hw, ident = launch(["chromium", "--no-sandbox", "--disable-gpu",
                             "--user-data-dir="+str(root/"chrome-profile"),
                             "about:blank"], env,"chromium")
        procs.append(chrome); apps["chromium"]={"pid":chrome.pid,"window":hw,"identity":ident,"surface_generation":1}
        for name, info in apps.items():
            event(ledger, "observe", app=name, window=info["window"],
                  surface_generation=info["surface_generation"],
                  geometry=geom(env, info["window"]))
        # 1. Focus drift: old Calc capability becomes stale, no input emitted.
        old_calc = apps["calc"].copy(); cmd(["xdotool","windowactivate",apps["inkscape"]["window"]],env)
        event(ledger,"focus_drift",from_app="calc",to_app="inkscape",active=active(env),input_emitted=False)
        denied = active(env) != old_calc["window"]
        event(ledger,"stale_admission",app="calc",old_window=old_calc["window"],disposition="refused",input_emitted=False)
        checks.append(denied)
        # 2. Same-app modal: open Calc file chooser then observe/close, no action.
        modal_before = windows(env)
        cmd(["xdotool","windowactivate",apps["calc"]["window"],"key","ctrl+o"],env); input_ops += 1; time.sleep(1)
        modal = wait_window(env, None, modal_before, 8)
        event(ledger,"modal_transition",app="calc",parent=apps["calc"]["window"],modal=modal,input_emitted=True)
        cmd(["xdotool","key","Escape"],env); input_ops += 1; time.sleep(.5)
        event(ledger,"modal_recovery",app="calc",modal=modal,disposition="observe_only",input_emitted=True)
        checks.append(modal is not None)
        # 3. Geometry transition on current Calc surface; old geometry is stale.
        before_geom=geom(env,apps["calc"]["window"])
        cmd(["wmctrl", "-i", "-r", apps["calc"]["window"], "-b", "remove,maximized_vert,maximized_horz"], env)
        cmd(["xdotool","windowsize",apps["calc"]["window"],"1200","700"],env); input_ops += 1; time.sleep(.5)
        after_geom=geom(env,apps["calc"]["window"]); apps["calc"]["surface_generation"] += 1
        event(ledger,"geometry_transition",app="calc",old_geometry=before_geom,new_geometry=after_geom,surface_generation=apps["calc"]["surface_generation"])
        event(ledger,"stale_geometry_admission",app="calc",disposition="refused",input_emitted=False)
        checks.append(before_geom != after_geom)
        # 4. Window replacement: replace Chromium and require new identity.
        old_chrome=apps["chromium"].copy(); old_chrome_cleanup=stop_process_group(chrome)
        procs.remove(chrome)
        cmd(["xdotool", "windowclose", old_chrome["window"]], env)
        end = time.time() + 8
        while old_chrome["window"] in windows(env) and time.time() < end:
            time.sleep(.25)
        old_gone = old_chrome["window"] not in windows(env)
        if not old_gone:
            raise RuntimeError("STOP_OLD_CHROMIUM_WINDOW_REMAINS")
        replacement, new_hw, new_identity = launch(["chromium","--no-sandbox","--disable-gpu",
                                      "--user-data-dir="+str(root/"chrome-profile-2"),"about:blank"],env,"chromium"); procs.append(replacement)
        apps["chromium"]={"pid":replacement.pid,"window":new_hw,"identity":new_identity,"surface_generation":old_chrome["surface_generation"]+1}
        replacement_identity = {"window": new_hw, "pid": replacement.pid,
                                "surface_generation": apps["chromium"]["surface_generation"]}
        event(ledger,"window_replacement",app="chromium",old_window=old_chrome["window"],new_window=new_hw,
              old_pid=old_chrome["pid"],new_pid=replacement.pid,
              identity_reused=(new_hw == old_chrome["window"]),
              typed_identity=replacement_identity,
              surface_generation=apps["chromium"]["surface_generation"],old_process_cleanup=old_chrome_cleanup)
        event(ledger,"stale_window_admission",app="chromium",old_window=old_chrome["window"],disposition="refused",input_emitted=False)
        checks.append(new_hw is not None and replacement.pid != old_chrome["pid"] and old_gone)
        # Return to earlier Calc: fresh identity/generation is required.
        cmd(["xdotool","windowactivate",apps["calc"]["window"]],env); time.sleep(.3)
        event(ledger,"return_to_earlier_app",app="calc",window=apps["calc"]["window"],surface_generation=apps["calc"]["surface_generation"],fresh_validation=True)
        event(ledger,"stable_control",app="calc",action_dispatched=False,independent_task_effect_scored=False)
        checks.append(active(env) == apps["calc"]["window"])
        transitions_ok=all(checks)
        out={"decision":"HOLD_TASK_EFFECT_UNTESTED",
             "transition_gate":"PASS_MIXED_APP_READINESS_TRANSITIONS_SCOPED" if transitions_ok else "FAIL_MIXED_APP_READINESS_TRANSITIONS",
             "session_complete":True,"event_count":len(ledger),"checks":checks,
             "input_operations":input_ops,"model_calls":0,"network_calls":0,
             "independent_task_effect_scored":False,"apps":apps,"ledger":ledger}
        exit_code=0 if transitions_ok else 1
    except Exception as exc:
        event(ledger,"stop",reason=repr(exc))
        out={"decision":"STOP_MIXED_APP_READINESS_SUCCESSOR","transition_gate":"NOT_RUN_OR_INCOMPLETE",
             "session_complete":False,"event_count":len(ledger),"input_operations":input_ops,
             "model_calls":0,"network_calls":0,"independent_task_effect_scored":False,
             "apps":apps,"ledger":ledger,"failed_launches":FAILED_LAUNCHES,
             "error":repr(exc),"traceback":traceback.format_exc()}
    finally:
        cleanup=[stop_process_group(p) for p in reversed(procs)]
        cleanup.extend(stop_process_group(p) for p in (wm,xvfb))
        if out is None:
            out={"decision":"STOP_MIXED_APP_READINESS_SUCCESSOR","transition_gate":"NOT_RUN_OR_INCOMPLETE",
                 "session_complete":False,"model_calls":0,"network_calls":0,"ledger":ledger}
        out["cleanup_processes"]=cleanup
        out["cleanup_complete"]=all(x is not None and x["returncode"] is not None and not x["remaining_pids"] for x in cleanup)
        out["xvfb_socket_disappeared"]=not Path("/tmp/.X11-unix/X159").exists()
        out["cleanup_complete"] = out["cleanup_complete"] and out["xvfb_socket_disappeared"]
        out["terminal_input_state"]="not_independently_measured"
        out["failed_launches"]=FAILED_LAUNCHES
        out.update({"allocation_id":"issue2499-readiness-successor-3649-formal-01","issue":3649,
                    "formal_invocations":1,"retries":0,
                    "source_commit":os.environ.get("FROZEN_SOURCE_COMMIT"),
                    "source_manifest_sha256":os.environ.get("SOURCE_MANIFEST_SHA256"),
                    "preregistration_sha256":os.environ.get("PREREGISTRATION_SHA256"),
                    "freeze_sha256":os.environ.get("FREEZE_SHA256"),
                    "image_id":os.environ.get("PINNED_IMAGE_ID"),"platform":"linux/arm64"})
        event(ledger,"process_cleanup",processes=cleanup,complete=out["cleanup_complete"])
        out["ledger"]=ledger; out["event_count"]=len(ledger)
        evidence_path=os.environ.get("EVIDENCE_PATH")
        if evidence_path:
            Path(evidence_path).write_text(json.dumps(out,sort_keys=True,indent=2)+"\n")
        print(json.dumps(out,sort_keys=True))
    raise SystemExit(exit_code)

if __name__ == "__main__": main()
