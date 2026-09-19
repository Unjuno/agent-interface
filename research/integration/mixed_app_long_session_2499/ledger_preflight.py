"""Model-free, no-input transition ledger for successor #2499.

This is a bounded preflight, not the formal four-transition result. It records
identity, focus, geometry, replacement, and return observations in one X11
session. Modal transition is deliberately reported as HOLD until a typed,
owned modal fixture exists.
"""
import json, os, signal, subprocess, tempfile, time
from pathlib import Path

APPS = ("inkscape", "libreoffice", "chromium")


def run(cmd, env):
    return subprocess.run(cmd, env=env, text=True, capture_output=True,
                          timeout=20, check=False)


def windows(env):
    result = run(["xdotool", "search", "--onlyvisible", "--name", ".*"], env)
    return [x for x in result.stdout.splitlines() if x.strip()]


def pid_tree(root):
    result = run(["ps", "-eo", "pid=,ppid="], os.environ)
    children = {}
    for row in result.stdout.splitlines():
        fields = row.split()
        if len(fields) == 2:
            children.setdefault(int(fields[1]), []).append(int(fields[0]))
    seen, stack = {root}, [root]
    while stack:
        parent = stack.pop()
        for child in children.get(parent, []):
            if child not in seen:
                seen.add(child)
                stack.append(child)
    return seen


def owned(env, baseline, root):
    result = []
    tree = pid_tree(root)
    for window in windows(env):
        if window in baseline:
            continue
        try:
            pid = int(run(["xdotool", "getwindowpid", window], env).stdout.strip())
        except ValueError:
            continue
        if pid in tree:
            result.append(window)
    return result


def focus(env, window):
    return run(["xdotool", "windowfocus", window], env).returncode == 0


def geometry(env, window, width, height):
    return run(["xdotool", "windowsize", window, str(width), str(height)],
               env).returncode == 0


def launch(app, root, env):
    if app == "inkscape":
        cmd = [app]
    elif app == "libreoffice":
        cmd = [app, "--norestore", "--nolockcheck",
               f"-env:UserInstallation=file://{root / 'lo-profile'}", "--calc"]
    else:
        cmd = [app, "--no-sandbox", "--disable-gpu", "--no-first-run",
               "--no-default-browser-check",
               "--disable-session-crashed-bubble",
               "--user-data-dir=" + str(root / "chrome-profile"),
               "about:blank"]
    return subprocess.Popen(cmd, env=env, stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL)


def main():
    root = Path(tempfile.mkdtemp(prefix="mixed-2499-ledger-"))
    env = os.environ.copy()
    env.update(DISPLAY=":140", XAUTHORITY=str(root / "Xauthority"),
               HOME=str(root / "home"), XDG_CONFIG_HOME=str(root / "config"),
               XDG_CACHE_HOME=str(root / "cache"),
               XDG_RUNTIME_DIR=str(root / "runtime"),
               SAL_USE_VCLPLUGIN="gen", GDK_BACKEND="x11")
    for name in ("home", "config", "cache", "runtime"):
        (root / name).mkdir(mode=0o700)
    (root / "Xauthority").touch(mode=0o600)
    processes, ledger = [], []
    out = {"session": {"display": env["DISPLAY"], "persistent": True,
                       "input_operations": 0, "model_calls": 0,
                       "network_calls": 0},
           "events": [], "decision": "HOLD_MIXED_APP_LONG_SESSION"}
    xvfb = subprocess.Popen(
        ["Xvfb", env["DISPLAY"], "-screen", "0", "1600x1000x24",
         "-auth", env["XAUTHORITY"]],
        env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        time.sleep(0.7)
        records = {}
        for app in APPS:
            baseline = set(windows(env))
            process = launch(app, root, env)
            processes.append(process)
            deadline, found = time.monotonic() + 15, []
            while time.monotonic() < deadline:
                found = owned(env, baseline, process.pid)
                if found:
                    break
                time.sleep(0.5)
            records[app] = {"pid": process.pid, "windows": found[:10],
                            "generation": 1, "observed": bool(found),
                            "owner_bound": bool(found)}
        ledger.append({"event": "identity_ready", "records": records})
        ordered = [records[app]["windows"][0] for app in APPS
                   if records[app]["windows"]]
        focus_ok = all(focus(env, window) for window in ordered)
        ledger.append({"event": "focus_drift", "focus_receipts": len(ordered),
                       "ok": focus_ok})
        geometry_ok = bool(ordered) and geometry(env, ordered[0], 800, 600)
        ledger.append({"event": "geometry_change", "ok": geometry_ok,
                       "window": ordered[0] if ordered else None})
        old = records["chromium"]["windows"][0] if records["chromium"]["windows"] else None
        if processes[-1].poll() is None:
            processes[-1].send_signal(signal.SIGTERM)
            processes[-1].wait(timeout=10)
        records["chromium"]["generation"] += 1
        replacement = launch("chromium", root, env)
        processes.append(replacement)
        baseline = set(windows(env))
        new = []
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            new = owned(env, baseline, replacement.pid)
            if new:
                break
            time.sleep(0.5)
        replacement_ok = bool(new) and replacement.pid != records["chromium"]["pid"]
        ledger.append({"event": "window_replacement", "old_window": old,
                       "old_pid": records["chromium"]["pid"],
                       "new_pid": replacement.pid,
                       "new_windows": new[:10],
                       "generation": records["chromium"]["generation"],
                       "ok": replacement_ok})
        return_ok = bool(ordered) and focus(env, ordered[0])
        ledger.append({"event": "return_to_earlier_app", "window": ordered[0]
                       if ordered else None, "ok": return_ok})
        ledger.append({"event": "modal_transition", "ok": False,
                       "disposition": "HOLD_NO_TYPED_MODAL_FIXTURE"})
        out["events"] = ledger
        out["decision"] = (
            "PASS_MIXED_APP_LONG_SESSION_PREFLIGHT"
            if all(event.get("ok", True) for event in ledger)
            and records["inkscape"]["observed"]
            and records["libreoffice"]["observed"]
            and records["chromium"]["observed"]
            else "HOLD_MIXED_APP_LONG_SESSION")
        print(json.dumps(out, sort_keys=True))
        raise SystemExit(0 if out["decision"].startswith("PASS") else 1)
    finally:
        for process in reversed(processes):
            if process.poll() is None:
                process.send_signal(signal.SIGTERM)
        if xvfb.poll() is None:
            xvfb.send_signal(signal.SIGTERM)


if __name__ == "__main__":
    main()
