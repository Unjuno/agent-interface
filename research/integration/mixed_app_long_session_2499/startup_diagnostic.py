#!/usr/bin/env python3
"""Startup prerequisite diagnostic for #2821 v6.

v6 fixes the v5 Inkscape invocation and records Chromium shim failures
separately from a runnable browser. It performs no GUI input, model call, or
network operation.
"""
import json, os, shutil, subprocess, tempfile, time
DISPLAY = ":141"

def resolve(name, extra=()):
    return shutil.which(name) or next((p for p in extra if os.path.exists(p)), None)

def main():
    root = tempfile.mkdtemp(prefix="mixed-startup-2821-v6-")
    env = os.environ.copy()
    env.update(DISPLAY=DISPLAY, XAUTHORITY=os.path.join(root, "Xauthority"))
    open(env["XAUTHORITY"], "a").close()
    os.chmod(env["XAUTHORITY"], 0o600)
    procs, checks, errors = [], [], []
    try:
        xvfb = subprocess.Popen(
            ["Xvfb", DISPLAY, "-screen", "0", "1600x1000x24", "-auth", env["XAUTHORITY"]],
            env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        procs.append(xvfb)
        time.sleep(1)
        checks.append({"name": "xvfb_alive", "ok": xvfb.poll() is None})
        specs = [
            ("inkscape", resolve("inkscape"), ["--new"]),
            ("libreoffice", resolve("libreoffice"),
             ["--norestore", "--nolockcheck", "--calc"]),
            ("chromium", resolve("chromium", (
                "/usr/lib/chromium/chromium",
                "/usr/lib/chromium-browser/chromium-browser",
                "/usr/bin/chromium-browser",
            )), ["--no-sandbox", "--disable-gpu",
                  "--user-data-dir=" + os.path.join(root, "chrome"), "about:blank"]),
        ]
        for name, binary, args in specs:
            checks.append({"name": name + "_resolved", "ok": binary is not None, "path": binary})
            if binary is None:
                errors.append(name + "_binary_missing")
                continue
            p = subprocess.Popen([binary, *args], env=env,
                                 stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
            procs.append(p)
            time.sleep(2)
            ok = p.poll() is None
            detail = "" if ok else (p.stderr.read()[-1000:] if p.stderr else "")
            checks.append({"name": name + "_alive", "ok": ok, "exit_code": p.poll(),
                           "stderr_tail": detail})
            if not ok:
                errors.append(name + "_exited")
                if name == "chromium" and "snap" in detail.lower():
                    errors.append("chromium_snap_shim")
        decision = ("PASS_MIXED_APP_STARTUP_DIAGNOSTIC"
                    if not errors and all(c["ok"] for c in checks)
                    else "FAIL_MIXED_APP_STARTUP_DIAGNOSTIC")
        print(json.dumps({
            "decision": decision, "checks": checks, "errors": errors,
            "display": DISPLAY, "model_calls": 0, "network_calls": 0,
            "input_operations": 0, "diagnostic_only": True,
        }, sort_keys=True))
        return 0 if decision.startswith("PASS") else 1
    except Exception as exc:
        print(json.dumps({"decision": "STOP_MIXED_APP_STARTUP_DIAGNOSTIC",
                          "error": repr(exc), "diagnostic_only": True}, sort_keys=True))
        return 1
    finally:
        for p in reversed(procs):
            if p.poll() is None:
                p.terminate()
        time.sleep(.2)
        for p in reversed(procs):
            if p.poll() is None:
                p.kill()

if __name__ == "__main__":
    raise SystemExit(main())
