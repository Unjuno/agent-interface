#!/usr/bin/env python3
"""Model-free startup diagnostic for Issue #2821; no GUI input or model/network calls."""
import json, os, shutil, subprocess, tempfile, time
DISPLAY = ":141"
def main():
    root = tempfile.mkdtemp(prefix="mixed-startup-2821-")
    env = os.environ.copy()
    env["DISPLAY"] = DISPLAY
    env["XAUTHORITY"] = os.path.join(root, "Xauthority")
    open(env["XAUTHORITY"], "a").close()
    os.chmod(env["XAUTHORITY"], 0o600)
    procs, checks, errors = [], [], []
    try:
        xvfb = subprocess.Popen(["Xvfb", DISPLAY, "-screen", "0", "1600x1000x24", "-auth", env["XAUTHORITY"]], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        procs.append(xvfb); time.sleep(1)
        checks.append({"name":"xvfb_alive","ok":xvfb.poll() is None})
        specs = [
            ("inkscape", ["inkscape","--no-splash","--new"]),
            ("libreoffice", ["libreoffice","--norestore","--nodefault","--nolockcheck","--calc"]),
            ("chromium", ["chromium","--no-sandbox","--disable-gpu","--user-data-dir="+os.path.join(root,"chrome"),"about:blank"]),
        ]
        for name, argv in specs:
            found = shutil.which(argv[0]) is not None
            checks.append({"name":name+"_binary","ok":found})
            if not found: errors.append(name+"_binary_missing"); continue
            p = subprocess.Popen(argv, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
            procs.append(p); time.sleep(2)
            ok = p.poll() is None
            checks.append({"name":name+"_alive","ok":ok})
            if not ok: errors.append(name+"_exited")
        decision = "PASS_MIXED_APP_STARTUP_DIAGNOSTIC" if not errors and all(x["ok"] for x in checks) else "FAIL_MIXED_APP_STARTUP_DIAGNOSTIC"
        print(json.dumps({"decision":decision,"checks":checks,"errors":errors,"display":DISPLAY,"model_calls":0,"network_calls":0,"input_operations":0,"diagnostic_only":True}, sort_keys=True))
        return 0 if decision.startswith("PASS") else 1
    except Exception as exc:
        print(json.dumps({"decision":"STOP_MIXED_APP_STARTUP_DIAGNOSTIC","error":repr(exc),"diagnostic_only":True}, sort_keys=True)); return 1
    finally:
        for p in reversed(procs):
            if p.poll() is None: p.terminate()
        time.sleep(.2)
        for p in reversed(procs):
            if p.poll() is None: p.kill()
if __name__ == "__main__": raise SystemExit(main())
