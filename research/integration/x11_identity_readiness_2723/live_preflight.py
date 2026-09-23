"""Read-only X11 readiness preflight for successor #2723."""
from __future__ import annotations
import json
import os
import signal
import subprocess
import tempfile
import time
from pathlib import Path

APPS = ("inkscape", "libreoffice", "chromium")

def run(cmd, env, timeout=5):
    return subprocess.run(cmd, env=env, text=True, capture_output=True, timeout=timeout, check=False)

def records(env):
    q = run(["xdotool", "search", "--onlyvisible", "--name", ".*"], env)
    out = []
    for raw in q.stdout.splitlines():
        if not raw.strip().isdigit():
            continue
        wid = raw.strip()
        title = run(["xdotool", "getwindowname", wid], env).stdout.strip()
        pid = run(["xdotool", "getwindowpid", wid], env).stdout.strip()
        wm = run(["xprop", "-id", wid, "WM_CLASS"], env).stdout.strip()
        if pid.isdigit() and int(pid) > 0 and title and wm and "not found" not in wm.lower():
            out.append({"window_id": int(wid), "pid": int(pid), "title": title, "wm_class": wm, "display": env["DISPLAY"]})
    return out

def app_seen(row, app):
    text = (row["title"] + " " + row["wm_class"]).lower()
    return ("inkscape" in text if app == "inkscape" else "libreoffice" in text or "calc" in text if app == "libreoffice" else "chrom" in text)

def wait_until(env, procs, timeout=25):
    deadline = time.monotonic() + timeout
    last = []
    while time.monotonic() < deadline:
        last = records(env)
        if all(any(app_seen(row, app) for row in last) for app in APPS):
            return last
        time.sleep(0.5)
    return last

def main():
    root = Path(tempfile.mkdtemp(prefix="identity-2723-"))
    env = os.environ.copy()
    env.update(DISPLAY=":142", XAUTHORITY=str(root / "Xauthority"), HOME=str(root / "home"), XDG_CONFIG_HOME=str(root / "config"), XDG_CACHE_HOME=str(root / "cache"), XDG_RUNTIME_DIR=str(root / "runtime"))
    for name in ("home", "config", "cache", "runtime"):
        (root / name).mkdir(mode=0o700)
    (root / "Xauthority").touch(mode=0o600)
    procs = []
    result = {"display": env["DISPLAY"], "apps": list(APPS), "input_operations": 0, "model_calls": 0, "network_calls": 0}
    xvfb = subprocess.Popen(["Xvfb", env["DISPLAY"], "-screen", "0", "1600x1000x24", "-auth", env["XAUTHORITY"]], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        time.sleep(1)
        for app in APPS:
            if app == "inkscape":
                cmd = [app, "--no-splash", "--new"]
            elif app == "libreoffice":
                cmd = [app, "--norestore", "--nodefault", "--nolockcheck", "-env:UserInstallation=file://" + str(root / "lo-profile"), "--calc"]
            else:
                cmd = [app, "--no-sandbox", "--disable-gpu", "--no-first-run", "--no-default-browser-check", "--user-data-dir=" + str(root / "chrome-profile"), "about:blank"]
            procs.append((app, subprocess.Popen(cmd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)))
        first = wait_until(env, procs)
        time.sleep(1)
        second = records(env)
        first_apps = {app for app in APPS if any(app_seen(row, app) for row in first)}
        second_apps = {app for app in APPS if any(app_seen(row, app) for row in second)}
        pairs = [(row["window_id"], row["pid"]) for row in first]
        result.update({"first_records": first, "second_records": second, "first_apps": sorted(first_apps), "second_apps": sorted(second_apps), "stable": first == second, "distinct_window_pid": len(pairs) == len(set(pairs)), "all_apps_observed": first_apps == set(APPS) and second_apps == set(APPS), "process_states": {app: proc.poll() for app, proc in procs}})
        result["decision"] = "PASS_IDENTITY_READINESS" if result["all_apps_observed"] and result["stable"] and result["distinct_window_pid"] else "HOLD_IDENTITY_DISCOVERY"
        print(json.dumps(result, sort_keys=True))
        raise SystemExit(0 if result["decision"] == "PASS_IDENTITY_READINESS" else 1)
    finally:
        for _, proc in reversed(procs):
            if proc.poll() is None:
                proc.send_signal(signal.SIGTERM)
        if xvfb.poll() is None:
            xvfb.send_signal(signal.SIGTERM)

if __name__ == "__main__":
    main()
