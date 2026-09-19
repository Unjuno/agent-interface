"""Model-free construction gate for the #2499 mixed-app session.

This only verifies that three disposable applications can coexist in one
private X11 session and that visible windows are observable. It does not
claim the preregistered four-transition formal result.
"""
import json
import os
import signal
import subprocess
import tempfile
import time
from pathlib import Path

APPS = ("inkscape", "libreoffice", "chromium")


def run(cmd, env, timeout=20):
    return subprocess.run(cmd, env=env, text=True, capture_output=True,
                          timeout=timeout, check=False)


def visible_windows(env):
    q = run(["xdotool", "search", "--onlyvisible", "--name", ".*"], env)
    return [x for x in q.stdout.splitlines() if x.strip()]


def main():
    root = Path(tempfile.mkdtemp(prefix="mixed-2499-"))
    env = os.environ.copy()
    env.update(DISPLAY=":140", XAUTHORITY=str(root / "Xauthority"),
               HOME=str(root / "home"), XDG_CONFIG_HOME=str(root / "config"),
               XDG_CACHE_HOME=str(root / "cache"),
               XDG_RUNTIME_DIR=str(root / "runtime"),
               SAL_USE_VCLPLUGIN="gen", GDK_BACKEND="x11")
    for directory in ("home", "config", "cache", "runtime"):
        (root / directory).mkdir(mode=0o700)
    (root / "Xauthority").touch(mode=0o600)
    procs = []
    out = {"apps": [], "input_operations": 0, "model_calls": 0,
           "network_calls": 0, "display": env["DISPLAY"]}
    xvfb = subprocess.Popen(
        ["Xvfb", env["DISPLAY"], "-screen", "0", "1600x1000x24",
         "-auth", env["XAUTHORITY"]],
        env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        time.sleep(0.7)
        for app in APPS:
            if app == "inkscape":
                cmd = [app]
            elif app == "libreoffice":
                cmd = [app, "--norestore", "--nolockcheck",
                       f"-env:UserInstallation=file://{root / 'lo-profile'}",
                       "--calc"]
            else:
                cmd = [app, "--no-sandbox", "--disable-gpu", "--no-first-run",
                       "--no-default-browser-check", "--disable-session-crashed-bubble",
                       "--user-data-dir=" + str(root / "chrome-profile"),
                       "about:blank"]
            p = subprocess.Popen(cmd, env=env, stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL)
            procs.append(p)
            deadline = time.monotonic() + 15
            windows = []
            while time.monotonic() < deadline:
                windows = visible_windows(env)
                if windows:
                    break
                time.sleep(0.5)
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
