"""Model-free live identity preflight for the #2499 fixture.

This is strictly a discovery gate. It does not send input, call a model,
infer an effect, or claim the integrated long-session result.
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


def visible_records(env):
    q = run(["xdotool", "search", "--onlyvisible", "--name", ".*"], env)
    records = []
    for raw in q.stdout.splitlines():
        wid = raw.strip()
        if not wid.isdigit():
            continue
        name = run(["xdotool", "getwindowname", wid], env).stdout.strip()
        pid_text = run(["xdotool", "getwindowpid", wid], env).stdout.strip()
        wm = run(["xprop", "-id", wid, "WM_CLASS"], env).stdout.strip()
        if (pid_text.isdigit() and int(pid_text) > 0 and name and wm
                and "not found" not in wm.lower()):
            records.append({"window_id": int(wid), "pid": int(pid_text),
                            "title": name, "wm_class": wm,
                            "display": env["DISPLAY"]})
    return records


def wait_for_records(env, minimum=3, timeout=15):
    deadline = time.monotonic() + timeout
    last = []
    while time.monotonic() < deadline:
        last = visible_records(env)
        if len(last) >= minimum:
            return last
        time.sleep(0.5)
    return last


def main():
    root = Path(tempfile.mkdtemp(prefix="identity-2666-"))
    env = os.environ.copy()
    env.update(DISPLAY=":141", XAUTHORITY=str(root / "Xauthority"),
               HOME=str(root / "home"), XDG_CONFIG_HOME=str(root / "config"),
               XDG_CACHE_HOME=str(root / "cache"),
               XDG_RUNTIME_DIR=str(root / "runtime"))
    for directory in ("home", "config", "cache", "runtime"):
        (root / directory).mkdir(mode=0o700)
    (root / "Xauthority").touch(mode=0o600)
    procs = []
    out = {"display": env["DISPLAY"], "input_operations": 0,
           "model_calls": 0, "network_calls": 0, "apps": list(APPS)}
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
                cmd = [app, "--norestore", "--nodefault", "--nolockcheck",
                       f"-env:UserInstallation=file://{root / 'lo-profile'}",
                       "--calc"]
            else:
                cmd = [app, "--no-sandbox", "--disable-gpu", "--no-first-run",
                       "--no-default-browser-check", "--disable-session-crashed-bubble",
                       "--user-data-dir=" + str(root / "chrome-profile"),
                       "about:blank"]
            proc = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, text=True)
            procs.append((app, proc))
            time.sleep(1.0)
        first = wait_for_records(env)
        time.sleep(0.4)
        second = visible_records(env)
        keys = {(r["window_id"], r["pid"]) for r in first}
        out.update({"first_records": first, "second_records": second,
                    "record_count": len(first), "stable": first == second,
                    "distinct_window_pid": len(keys) == len(first),
                    "nonempty_titles": all(r["title"] for r in first),
                    "all_apps_observed": len(first) >= 3,
                    "process_states": {app: {"returncode": proc.poll()}
                                       for app, proc in procs},
                    "launch_diagnostics": {
                        app: (proc.stderr.read(400) if proc.poll() is not None else "")
                        for app, proc in procs},
                    "decision": "PASS_IDENTITY_DISCOVERY_SCOPED"
                    if first == second and len(keys) == len(first) and len(first) >= 3
                    else "HOLD_IDENTITY_DISCOVERY"})
        print(json.dumps(out, sort_keys=True))
        raise SystemExit(0 if out["decision"].startswith("PASS") else 1)
    finally:
        for _, proc in reversed(procs):
            if proc.poll() is None:
                proc.send_signal(signal.SIGTERM)
        if xvfb.poll() is None:
            xvfb.send_signal(signal.SIGTERM)


if __name__ == "__main__":
    main()
