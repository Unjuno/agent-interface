"""Model-free construction gate for the #2499 mixed-app session.

This only verifies that three disposable applications can coexist in one
private X11 session and that window identities can be observed. It does not
claim the preregistered four-transition formal result.
"""
import json, os, signal, subprocess, tempfile, time
from pathlib import Path

APPS = ("inkscape", "libreoffice", "chromium")

def run(cmd, env, timeout=20):
    return subprocess.run(cmd, env=env, text=True, capture_output=True,
                          timeout=timeout, check=False)

def main():
    root = Path(tempfile.mkdtemp(prefix="mixed-2499-"))
    env = os.environ.copy()
    env.update(DISPLAY=":140", XAUTHORITY=str(root / "Xauthority"))
    (root / "Xauthority").touch(mode=0o600)
    procs = []
    out = {"apps": [], "input_operations": 0, "model_calls": 0,
           "network_calls": 0, "display": env["DISPLAY"]}
    xvfb = subprocess.Popen(["Xvfb", env["DISPLAY"], "-screen", "0",
                             "1600x1000x24", "-auth", env["XAUTHORITY"]],
                            env=env, stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL)
    try:
        time.sleep(0.7)
        for app in APPS:
            if app == "inkscape":
                cmd = [app, "--no-splash", "--new"]
            elif app == "libreoffice":
                cmd = [app, "--norestore", "--nodefault", "--nolockcheck",
                       "--calc"]
            else:
                cmd = [app, "--no-sandbox", "--disable-gpu",
                       "--user-data-dir=" + str(root / "chrome-profile"),
                       "about:blank"]
            p = subprocess.Popen(cmd, env=env, stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL)
            procs.append(p)
            time.sleep(2.0)
            q = run(["xdotool", "search", "--onlyvisible", "--name", ".*"], env)
            windows = [x for x in q.stdout.splitlines() if x.strip()]
            out["apps"].append({"app": app, "pid": p.pid,
                                "window_count": len(windows),
                                "windows": windows[:20],
                                "observed": bool(windows)})
        out["decision"] = ("PASS_MIXED_APP_CONSTRUCTION_READY"
                            if all(x["observed"] for x in out["apps"])
                            else "HOLD_MIXED_APP_CONSTRUCTION")
        print(json.dumps(out, sort_keys=True))
        raise SystemExit(0 if out["decision"].startswith("PASS") else 1)
    finally:
        for p in reversed(procs):
            if p.poll() is None:
                p.send_signal(signal.SIGTERM)
        if xvfb.poll() is None:
            xvfb.send_signal(signal.SIGTERM)

if __name__ == "__main__":
    main()
