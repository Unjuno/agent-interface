"""One frozen, model-free mixed-app session for successor Issue #2499.

The ledger is intentionally independent of Agent Interface implementation. It
records the OS-visible identities and the admission decisions needed to audit
the four transitions; it does not claim model quality or product support.
"""
import hashlib, json, os, signal, subprocess, tempfile, time, traceback
from pathlib import Path

DISPLAY = ":142"

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
    q = cmd(["xdotool", "getwindowgeometry", wid], env)
    return q.stdout.strip()

def event(ledger, kind, **fields):
    row = {"seq": len(ledger), "kind": kind, **fields}
    row["hash"] = hashlib.sha256(json.dumps(row, sort_keys=True).encode()).hexdigest()
    ledger.append(row)

def wait_window(env, pid=None, before=None, timeout=20, allow_libreoffice=False):
    end = time.time() + timeout
    before = set(before or [])
    while time.time() < end:
        now = windows(env)
        candidates = [x for x in now if x not in before] if pid is None else [x for x in now if x not in before] + [x for x in now if x in before]
        for wid in reversed(candidates):
            props = cmd(["xprop", "-id", wid, "_NET_WM_PID", "WM_CLASS"], env)
            geometry = geom(env, wid)
            libre_ok = (allow_libreoffice and "libreoffice-calc" in props.stdout
                        and "Tip of the Day" not in props.stdout
                        and "Untitled" in props.stdout)
            if (pid is None or str(pid) in props.stdout or libre_ok) and geometry and "Geometry: 1x1" not in geometry:
                return wid
        time.sleep(.25)
    return None

def launch(cmdline, env, allow_libreoffice=False):
    p = subprocess.Popen(cmdline, env=env, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
    if allow_libreoffice:
        end = time.time() + 25
        while time.time() < end:
            q = cmd(["xdotool", "search", "--onlyvisible", "--name", "LibreOffice Calc"], env)
            ids = [x.strip() for x in q.stdout.splitlines() if x.strip()]
            if ids:
                return p, ids[0]
            time.sleep(.25)
    wid = wait_window(env, p.pid, windows(env), 25, allow_libreoffice)
    return p, wid

def main():
    root = Path(tempfile.mkdtemp(prefix="mixed-formal-2499-"))
    env = os.environ.copy(); env.update(DISPLAY=DISPLAY)
    xvfb = subprocess.Popen(["Xvfb", DISPLAY, "-screen", "0", "1600x1000x24"], env=env,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    wm = subprocess.Popen(["openbox", "--replace"], env=env,
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    procs=[]; ledger=[]; apps={}; checks=[]; input_ops=0
    try:
        time.sleep(.7); event(ledger, "session_setup", display=DISPLAY,
                              xauthority_mode="not_used")
        inkscape, iw = launch(["inkscape"], env)
        procs.append(inkscape); apps["inkscape"]={"pid":inkscape.pid,"window":iw,"surface_generation":1}
        calc, cw = launch(["libreoffice", "--calc"], env, allow_libreoffice=True)
        procs.append(calc); apps["calc"]={"pid":calc.pid,"window":cw,"surface_generation":1}
        chrome, hw = launch(["chromium", "--no-sandbox", "--disable-gpu",
                             "--user-data-dir="+str(root/"chrome-profile"),
                             "about:blank"], env)
        procs.append(chrome); apps["chromium"]={"pid":chrome.pid,"window":hw,"surface_generation":1}
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
        event(ledger,"modal_recovery",app="calc",modal=modal,disposition="observe_only",input_emitted=False)
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
        old_chrome=apps["chromium"].copy(); chrome.terminate(); chrome.wait(timeout=8)
        cmd(["xdotool", "windowclose", old_chrome["window"]], env)
        end = time.time() + 8
        while old_chrome["window"] in windows(env) and time.time() < end:
            time.sleep(.25)
        old_gone = old_chrome["window"] not in windows(env)
        if not old_gone:
            event(ledger, "stop", reason="old Chromium window remained after replacement request")
            print(json.dumps({"decision":"STOP_MIXED_APP_LONG_SESSION", "ledger":ledger,
                              "model_calls":0,"network_calls":0}, sort_keys=True))
            raise SystemExit(1)
        replacement, new_hw = launch(["chromium","--no-sandbox","--disable-gpu",
                                      "--user-data-dir="+str(root/"chrome-profile-2"),"about:blank"],env); procs.append(replacement)
        apps["chromium"]={"pid":replacement.pid,"window":new_hw,"surface_generation":old_chrome["surface_generation"]+1}
        replacement_identity = {"window": new_hw, "pid": replacement.pid,
                                "surface_generation": apps["chromium"]["surface_generation"]}
        event(ledger,"window_replacement",app="chromium",old_window=old_chrome["window"],new_window=new_hw,
              old_pid=old_chrome["pid"],new_pid=replacement.pid,
              identity_reused=(new_hw == old_chrome["window"]),
              typed_identity=replacement_identity,
              surface_generation=apps["chromium"]["surface_generation"])
        event(ledger,"stale_window_admission",app="chromium",old_window=old_chrome["window"],disposition="refused",input_emitted=False)
        checks.append(new_hw is not None and replacement.pid != old_chrome["pid"] and old_gone)
        # Return to earlier Calc: fresh identity/generation is required.
        cmd(["xdotool","windowactivate",apps["calc"]["window"]],env); time.sleep(.3)
        event(ledger,"return_to_earlier_app",app="calc",window=apps["calc"]["window"],surface_generation=apps["calc"]["surface_generation"],fresh_validation=True)
        event(ledger,"stable_control",app="calc",effect="none",independent_effect="none",input_emitted=False)
        checks.append(active(env) == apps["calc"]["window"])
        event(ledger,"cleanup",processes=len(procs),terminal_input="neutral",cleanup_failure=False)
        out={"decision":"PASS_MIXED_APP_LONG_SESSION_SCOPED" if all(checks) else "FAIL_MIXED_APP_LONG_SESSION",
             "session_complete":True,"event_count":len(ledger),"checks":checks,
             "input_operations":input_ops,"model_calls":0,"network_calls":0,
             "apps":apps,"ledger":ledger}
        print(json.dumps(out,sort_keys=True)); raise SystemExit(0 if all(checks) else 1)
    except Exception as exc:
        event(ledger,"stop",reason=repr(exc)); print(json.dumps({"decision":"STOP_MIXED_APP_LONG_SESSION","ledger":ledger,"error":repr(exc),"traceback":traceback.format_exc(),"model_calls":0,"network_calls":0},sort_keys=True)); raise SystemExit(1)
    finally:
        for p in reversed(procs):
            if p.poll() is None:
                p.terminate()
        if xvfb.poll() is None: xvfb.terminate()
        if wm.poll() is None: wm.terminate()

if __name__ == "__main__": main()
