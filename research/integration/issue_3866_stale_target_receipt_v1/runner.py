#!/usr/bin/python3
"""Six-session Calc stale-target diagnostic; no agent/provider/network calls."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time
import traceback

import openpyxl
import uno


SCHEDULE = [("A", 1), ("B", 1), ("B", 2),
            ("A", 2), ("A", 3), ("B", 3)]
TARGET = "$Sheet1.$A$1"


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024*1024), b""):
            h.update(block)
    return h.hexdigest()


def run(args, env, timeout=15):
    return subprocess.run(args, env=env, text=True, capture_output=True,
                          check=True, timeout=timeout)


def wait_for(fn, timeout=30, interval=0.1):
    deadline = time.monotonic()+timeout
    while time.monotonic() < deadline:
        value = fn()
        if value:
            return value
        time.sleep(interval)
    raise TimeoutError("bounded fixture readiness timed out")


def selection(port):
    local = uno.getComponentContext()
    resolver = local.ServiceManager.createInstanceWithContext(
        "com.sun.star.bridge.UnoUrlResolver", local)
    ctx = resolver.resolve(
        f"uno:socket,host=127.0.0.1,port={port};urp;StarOffice.ComponentContext")
    desktop = ctx.ServiceManager.createInstanceWithContext(
        "com.sun.star.frame.Desktop", ctx)
    doc = desktop.getCurrentComponent()
    if doc is None:
        raise RuntimeError("UNO current component missing")
    sel = doc.CurrentController.Selection
    return {"absolute_name": sel.AbsoluteName,
            "implementation": sel.ImplementationName}


def app_window(env, title):
    p = subprocess.run(["xdotool", "search", "--onlyvisible", "--name", title],
                       env=env, text=True, capture_output=True)
    ids = [int(x) for x in p.stdout.split() if x.isdigit()]
    return ids[-1] if ids else None


def window_identity(env, wid):
    listing = run(["wmctrl", "-lpGx"], env).stdout
    row = next((line for line in listing.splitlines()
                if line.split() and int(line.split()[0], 16) == wid), None)
    if row is None:
        raise RuntimeError("window missing from wmctrl list")
    cols = row.split(None, 9)
    return {"window_id": wid, "pid": int(cols[2]), "geometry": cols[3:7],
            "wm_class": cols[7], "host": cols[8] if len(cols) > 8 else "",
            "title": cols[9] if len(cols) > 9 else "",
            "list_row": row}


def xrecord_counts(path):
    counts = {"key_press": 0, "key_release": 0,
              "button_press": 0, "button_release": 0}
    names = {2: "key_press", 3: "key_release", 4: "button_press", 5: "button_release"}
    if Path(path).exists():
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            event = json.loads(line)
            key = names.get(event["type"])
            if key:
                counts[key] += 1
    return counts


def process_rows(marker):
    text = subprocess.run(["ps", "-eo", "pid=,ppid=,stat=,args="],
                          text=True, capture_output=True, check=True).stdout
    result = []
    for line in text.splitlines():
        if marker not in line:
            continue
        cols = line.strip().split(None, 3)
        if len(cols) == 4:
            result.append({"pid": int(cols[0]), "ppid": int(cols[1]),
                           "state": cols[2], "args": cols[3]})
    return result


def terminate(proc, timeout=4):
    if proc is None or proc.poll() is not None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=timeout)


def one_session(root, mode, block, display_no, allow_task_input=True):
    label = f"run-{mode}{block}"
    out = root/label
    out.mkdir(parents=True, exist_ok=False)
    display = f":{display_no}"
    port = 22000+display_no
    env = dict(os.environ, DISPLAY=display, HOME=f"/tmp/home-{label}",
               XDG_CONFIG_HOME=f"/tmp/home-{label}/.config",
               XDG_CACHE_HOME=f"/tmp/home-{label}/.cache")
    Path(env["HOME"]).mkdir(parents=True, exist_ok=True)
    procs = []
    row = {"mode": mode, "block": block, "display": display,
           "screen": "1280x800x24", "point": [89, 200],
           "task_input_attempted": False, "decision": "INCOMPLETE"}
    try:
        xvfb = subprocess.Popen(["Xvfb", display, "-screen", "0", "1280x800x24",
                                 "-nolisten", "tcp", "-ac"], env=env,
                                stdout=(out/"xvfb.log").open("w"),
                                stderr=subprocess.STDOUT)
        procs.append(("xvfb", xvfb))
        wait_for(lambda: Path(f"/tmp/.X11-unix/X{display_no}").exists(), 10)
        wm = subprocess.Popen(["openbox"], env=env,
                              stdout=(out/"openbox.log").open("w"),
                              stderr=subprocess.STDOUT)
        procs.append(("openbox", wm))
        time.sleep(0.3)

        workbook = out/"workbook.xlsx"
        wb = openpyxl.Workbook()
        wb.active.title = "Sheet1"
        wb.save(workbook)
        row["workbook_pre_sha256"] = digest(workbook)
        profile = Path(f"/tmp/lo-profile-{label}").as_uri()
        lo = subprocess.Popen([
            "libreoffice", "--calc", "--nologo", "--nodefault",
            "--nofirststartwizard", "--norestore",
            f"-env:UserInstallation={profile}",
            f"--accept=socket,host=127.0.0.1,port={port};urp;StarOffice.ServiceManager",
            str(workbook.resolve())], env=env,
            stdout=(out/"libreoffice.log").open("w"),
            stderr=subprocess.STDOUT)
        procs.append(("libreoffice_launcher", lo))
        title = "workbook.xlsx"
        wid = wait_for(lambda: app_window(env, title), 45)
        run(["wmctrl", "-ir", str(wid), "-b", "add,maximized_vert,maximized_horz"], env)
        run(["wmctrl", "-ia", str(wid)], env)
        row["window"] = window_identity(env, wid)
        row["libreoffice_processes_live"] = process_rows(f"/tmp/lo-profile-{label}")
        row["window_pid_bound_to_profile"] = any(
            p["pid"] == row["window"]["pid"]
            for p in row["libreoffice_processes_live"])
        row["selection_before_click"] = wait_for(lambda: selection(port), 30)
        focus0 = int(run(["xdotool", "getwindowfocus"], env).stdout.strip())
        row["focus_before_click"] = focus0

        monitor_events = out/"xrecord.jsonl"
        ready_file = out/"xrecord-state.json"
        stop_file = out/"stop-xrecord"
        monitor = subprocess.Popen([
            "/usr/bin/python3", "/src/record_monitor.py", "--display", display,
            "--events", str(monitor_events), "--ready", str(ready_file),
            "--stop", str(stop_file)], env=env,
            stdout=(out/"xrecord-monitor.stdout").open("w"),
            stderr=(out/"xrecord-monitor.stderr").open("w"))
        procs.append(("xrecord", monitor))
        wait_for(lambda: ready_file.exists() and
                 json.loads(ready_file.read_text()).get("ready"), 10)
        row["xrecord_started"] = True

        run(["xdotool", "mousemove", "--sync", "89", "200", "click", "1"], env)
        row["selection_after_click"] = selection(port)
        row["focus_after_click"] = int(run(["xdotool", "getwindowfocus"], env).stdout.strip())
        row["window_after_click"] = window_identity(env, wid)

        if mode == "B":
            observations = []
            first = time.monotonic()
            while time.monotonic()-first < 3.0:
                current = {"selection": selection(port),
                           "focus": int(run(["xdotool", "getwindowfocus"], env).stdout.strip()),
                           "window_pid": window_identity(env, wid)["pid"]}
                observations.append(current)
                if (current["selection"].get("absolute_name") != TARGET or
                        current["focus"] != wid or
                        current["window_pid"] != row["window"]["pid"]):
                    row["gate"] = {"allowed": False, "reason": "selection_or_focus_mismatch",
                                   "observations": observations}
                    break
                if time.monotonic()-first >= 0.3:
                    row["gate"] = {"allowed": True, "stable_ms": 300,
                                   "observations": observations}
                    break
                time.sleep(0.05)
            if "gate" not in row:
                row["gate"] = {"allowed": False, "reason": "readiness_timeout",
                               "observations": observations}
        else:
            row["gate"] = {"allowed": "not_applied", "reason": "coordinate_only"}

        should_send = (mode == "A" or row["gate"].get("allowed") is True)
        if should_send and allow_task_input:
            row["task_input_attempted"] = True
            row["task_input_start_monotonic"] = time.monotonic()
            run(["xdotool", "type", "--clearmodifiers", "--delay", "2", "116"], env)
            run(["xdotool", "key", "Return"], env)
            run(["xdotool", "type", "--clearmodifiers", "--delay", "2", "476"], env)
            run(["xdotool", "key", "Return"], env)
            run(["xdotool", "key", "ctrl+s"], env)
            time.sleep(0.5)
            run(["xdotool", "key", "Return"], env)
            time.sleep(0.5)
            row["selection_after_action"] = selection(port)
            row["task_input_end_monotonic"] = time.monotonic()
            row["saved_file_before_close"] = {"size": workbook.stat().st_size,
                                               "mtime_ns": workbook.stat().st_mtime_ns,
                                               "sha256": digest(workbook)}
        elif should_send:
            row["task_input_attempted"] = False
            row["decision"] = "CONSTRUCTION_GATE_ALLOWED_NO_INPUT"
        else:
            row["task_input_attempted"] = False
            row["decision"] = "REFUSED_STALE_SELECTION"

        stop_file.write_text("stop\n", encoding="ascii")
        try:
            monitor.wait(timeout=7)
        except subprocess.TimeoutExpired:
            row["xrecord_stop_timeout"] = True
            terminate(monitor)
        row["xrecord_counts"] = xrecord_counts(monitor_events)
        row["xrecord_exit"] = monitor.returncode

        # Score a separate disk artifact only after the GUI owner is closed.
        subprocess.run(["wmctrl", "-ic", str(wid)], env=env,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(0.6)
        profile_marker = f"/tmp/lo-profile-{label}"
        row["libreoffice_processes_after_window_close"] = process_rows(profile_marker)
        active = [p for p in row["libreoffice_processes_after_window_close"]
                  if not p["state"].startswith("Z")]
        for p in active:
            try:
                os.kill(p["pid"], signal.SIGTERM)
            except ProcessLookupError:
                pass
        deadline = time.monotonic() + 3.0
        while time.monotonic() < deadline:
            remaining = [p for p in process_rows(profile_marker)
                         if not p["state"].startswith("Z")]
            if not remaining:
                break
            time.sleep(0.1)
        for p in remaining:
            try:
                os.kill(p["pid"], signal.SIGKILL)
            except ProcessLookupError:
                pass
        time.sleep(0.2)
        row["libreoffice_processes_after_cleanup"] = process_rows(profile_marker)
        for name, proc in reversed(procs):
            if name == "xvfb":
                continue
            terminate(proc)
        time.sleep(0.3)
        row["workbook_post_sha256"] = digest(workbook)
        score = openpyxl.load_workbook(workbook, data_only=True, read_only=True)
        sheet = score["Sheet1"]
        row["scored_cells"] = {f"A{i}": sheet[f"A{i}"].value for i in range(1, 6)}
        score.close()
        if allow_task_input:
            row["decision"] = ("CONTROL_WRONG_TARGET_WRITE" if mode == "A" else
                               ("GATE_ALLOWED" if row["gate"].get("allowed") is True
                                else "GATE_REFUSED"))
    except Exception:
        row["error"] = traceback.format_exc()
        raise
    finally:
        for name, proc in reversed(procs):
            terminate(proc)
        row["processes"] = [{"role": name, "pid": proc.pid,
                             "returncode": proc.poll()} for name, proc in procs]
        (out/"row.json").write_text(json.dumps(row, indent=2, sort_keys=True)+"\n",
                                      encoding="utf-8")
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--construction-only", action="store_true")
    args = ap.parse_args()
    root = args.out.resolve()
    root.mkdir(parents=True, exist_ok=False)
    result = {"allocation": "issue2704-stale-target-selection-receipt-formal01",
              "main_source": "688e45cb99af4af7cc71db77049b5a6135a2f36f",
              "schedule": [f"{m}{b}" for m, b in SCHEDULE],
              "formal_sessions": 6, "reruns": 0, "rows": []}
    if args.construction_only:
        row = one_session(root, "B", 0, 98, allow_task_input=False)
        result.update({"scope": "construction only; no task keyboard input",
                       "formal_sessions": 0,
                       "rows": [{"decision": row["decision"],
                                 "input_attempted": row["task_input_attempted"],
                                 "selection": row.get("selection_after_click"),
                                 "events": row.get("xrecord_counts")}]})
        (root/"result.json").write_text(json.dumps(result, indent=2,
                                                     sort_keys=True)+"\n",
                                         encoding="utf-8")
        print(json.dumps(result, indent=2, sort_keys=True), flush=True)
        return
    for i, (mode, block) in enumerate(SCHEDULE):
        row = one_session(root, mode, block, 91+i)
        result["rows"].append({"mode": mode, "block": block,
                               "decision": row["decision"],
                               "input_attempted": row["task_input_attempted"],
                               "selection": row.get("selection_after_click"),
                               "cells": row.get("scored_cells"),
                               "events": row.get("xrecord_counts")})
        (root/"result.json").write_text(json.dumps(result, indent=2,
                                                     sort_keys=True)+"\n",
                                         encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()

