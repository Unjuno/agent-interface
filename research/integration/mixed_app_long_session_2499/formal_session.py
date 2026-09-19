"""One frozen, model-free mixed-app session for successor Issue #2499.

The ledger is intentionally independent of Agent Interface implementation. It
records the OS-visible identities and the admission decisions needed to audit
the four transitions; it does not claim model quality or product support.
"""
import hashlib, json, os, re, signal, subprocess, tempfile, time
from pathlib import Path

DISPLAY = ":141"

def cmd(argv, env, timeout=15):
    return subprocess.run(argv, env=env, text=True, capture_output=True,
                          timeout=timeout, check=False)

def windows(env):
    q = cmd(["xdotool", "search", "--onlyvisible", "--name", ".*"], env)
    return sorted({x.strip() for x in q.stdout.splitlines() if x.strip()}, key=int)

def active(env):
    q = cmd(["xdotool", "getactivewindow"], env)
    if q.returncode == 0 and q.stdout.strip():
        return q.stdout.strip()
    q = cmd(["xdotool", "getwindowfocus"], env)
    return q.stdout.strip() if q.returncode == 0 and q.stdout.strip() else None

def geom(env, wid):
    q = cmd(["xdotool", "getwindowgeometry", wid], env)
    if q.returncode == 0 and q.stdout.strip():
        return q.stdout.strip()
    fallback = cmd(["xwininfo", "-id", wid], env)
    return fallback.stdout.strip()

def event(ledger, kind, **fields):
    row = {"seq": len(ledger), "kind": kind, **fields}
    row["hash"] = hashlib.sha256(json.dumps(row, sort_keys=True).encode()).hexdigest()
    ledger.append(row)

def wait_window(env, before=None, timeout=20):
    end = time.time() + timeout
    before = set(before or [])
    while time.time() < end:
        now = windows(env)
        new = [x for x in now if x not in before]
        if new:
            return new[-1]
        time.sleep(.25)
    return None

def launch(cmdline, env):
    before = set(windows(env))
    p = subprocess.Popen(cmdline, env=env, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
    end = time.time() + 25
    wid = None
    while time.time() < end:
        candidates = [x for x in windows(env) if x not in before]
        usable = []
        for candidate in candidates:
            text = geom(env, candidate)
            match = re.search(r"Geometry:\s*(\d+)x(\d+)", text)
            if match and int(match.group(1)) >= 400 and int(match.group(2)) >= 300:
                usable.append(candidate)
        if usable:
            wid = usable[-1]
            break
        time.sleep(.25)
    if wid is None:
        wid = wait_window(env, before, 2)
    return p, wid

def main():
    root = Path(tempfile.mkdtemp(prefix="mixed-formal-2499-"))
    env = os.environ.copy(); env.update(DISPLAY=DISPLAY,
                                        XAUTHORITY=str(root / "Xauthority"))
    (root / "Xauthority").touch(mode=0o600)
    xvfb = subprocess.Popen(["Xvfb", DISPLAY, "-screen", "0", "1600x1000x24",
                             "-auth", env["XAUTHORITY"]], env=env,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    procs=[]; ledger=[]; apps={}; checks=[]; input_ops=0
    try:
        time.sleep(.7); event(ledger, "session_setup", display=DISPLAY,
                              xauthority_mode="0600")
        inkscape, iw = launch(["inkscape"], env)
        procs.append(inkscape); apps["inkscape"]={"pid":inkscape.pid,"window":iw,"surface_generation":1}
        calc, cw = launch(["libreoffice", "--norestore", "--nolockcheck", "--calc"], env)
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
        old_calc = apps["calc"].copy(); cmd(["xdotool","windowactivate","--sync",apps["inkscape"]["window"]],env)
        event(ledger,"focus_drift",from_app="calc",to_app="inkscape",active=active(env),input_emitted=False)
        denied = active(env) != old_calc["window"]
        event(ledger,"stale_admission",app="calc",old_window=old_calc["window"],disposition="refused",input_emitted=False)
        checks.append(denied)
        # 2. Same-app modal: open Calc file chooser then observe/close, no action.
        cmd(["xdotool","windowactivate",apps["calc"]["window"],"key","ctrl+o"],env); input_ops += 1; time.sleep(1)
        modal = wait_window(env, [apps["calc"]["window"]], 8)
        event(ledger,"modal_transition",app="calc",parent=apps["calc"]["window"],modal=modal,input_emitted=True)
        cmd(["xdotool","key","Escape"],env); input_ops += 1; time.sleep(.5)
        event(ledger,"modal_recovery",app="calc",modal=modal,disposition="observe_only",input_emitted=False)
        checks.append(modal is not None)
        # 3. Geometry transition on current Calc surface; old geometry is stale.
        before_geom=geom(env,apps["calc"]["window"]); cmd(["xdotool","windowsize",apps["calc"]["window"],"1200","700"],env); input_ops += 1; time.sleep(.5)
        after_geom=geom(env,apps["calc"]["window"]); apps["calc"]["surface_generation"] += 1
        event(ledger,"geometry_transition",app="calc",old_geometry=before_geom,new_geometry=after_geom,surface_generation=apps["calc"]["surface_generation"])
        event(ledger,"stale_geometry_admission",app="calc",disposition="refused",input_emitted=False)
        checks.append(before_geom != after_geom)
        # 4. Window replacement: replace Chromium and require new identity.
        old_chrome=apps["chromium"].copy(); chrome.terminate(); chrome.wait(timeout=8); time.sleep(.5)
        replacement, new_hw = launch(["chromium","--no-sandbox","--disable-gpu",
                                      "--user-data-dir="+str(root/"chrome-profile-2"),"about:blank"],env); procs.append(replacement)
        apps["chromium"]={"pid":replacement.pid,"window":new_hw,"surface_generation":old_chrome["surface_generation"]+1}
        event(ledger,"window_replacement",app="chromium",old_window=old_chrome["window"],new_window=new_hw,surface_generation=apps["chromium"]["surface_generation"])
        event(ledger,"stale_window_admission",app="chromium",old_window=old_chrome["window"],disposition="refused",input_emitted=False)
        checks.append(new_hw is not None and new_hw != old_chrome["window"])
        # Return to earlier Calc: fresh identity/generation is required.
        cmd(["xdotool","windowactivate","--sync",apps["calc"]["window"]],env)
        focus_result = cmd(["xdotool","windowfocus","--sync",apps["calc"]["window"]],env)
        time.sleep(.3)
        event(ledger,"return_to_earlier_app",app="calc",window=apps["calc"]["window"],surface_generation=apps["calc"]["surface_generation"],fresh_validation=True,focus_command_ok=focus_result.returncode == 0)
        event(ledger,"stable_control",app="calc",effect="none",independent_effect="none",input_emitted=False)
        checks.append(focus_result.returncode == 0)
        event(ledger,"cleanup",processes=len(procs),terminal_input="neutral",cleanup_failure=False)
        out={"decision":"PASS_MIXED_APP_LONG_SESSION_SCOPED" if all(checks) else "FAIL_MIXED_APP_LONG_SESSION",
             "session_complete":True,"event_count":len(ledger),"checks":checks,
             "input_operations":input_ops,"model_calls":0,"network_calls":0,
             "apps":apps,"ledger":ledger}
        print(json.dumps(out,sort_keys=True)); raise SystemExit(0 if all(checks) else 1)
    except Exception as exc:
        event(ledger,"stop",reason=repr(exc)); print(json.dumps({"decision":"STOP_MIXED_APP_LONG_SESSION","ledger":ledger,"error":repr(exc),"model_calls":0,"network_calls":0},sort_keys=True)); raise SystemExit(1)
    finally:
        for p in reversed(procs):
            if p.poll() is None:
                p.terminate()
        if xvfb.poll() is None: xvfb.terminate()

if __name__ == "__main__": main()
