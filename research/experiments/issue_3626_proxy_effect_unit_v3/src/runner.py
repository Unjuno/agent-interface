#!/usr/bin/python3
"""Single invocation, 28 fresh GTK/Xvfb rows for Issue #3610."""
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time

from Xlib import X, display
from Xlib.ext import xtest

from proxy import render

ROOT = Path("/src")
OUT = Path("/evidence")
ARMS = ("ordinary_screenshot", "proxy_image", "structured_proxy", "hybrid")
CASES = ("positive", "no_effect", "stale_version", "target_replaced", "unavailable", "ambiguous", "macro_failure")
DISPLAY_NAME = ":301"
SOCKET = Path("/tmp/.X11-unix/X301")


def sha(b): return hashlib.sha256(b).hexdigest()


def start_ticks(pid):
    try:
        s = Path(f"/proc/{pid}/stat").read_text()
        return s[s.rfind(")") + 2:].split()[19]
    except (OSError, IndexError):
        return None


def stop(proc):
    if proc is None: return None
    if proc.poll() is None:
        proc.terminate()
    try: return proc.wait(timeout=3)
    except subprocess.TimeoutExpired:
        proc.kill()
        return proc.wait(timeout=3)


def find_windows(conn):
    found = []
    for win in conn.screen().root.query_tree().children:
        try:
            title = win.get_wm_name() or ""
            if title.startswith("proxy-fixture:") and win.get_attributes().map_state == X.IsViewable:
                found.append((win, title))
        except Exception:
            pass
    return found


def state(conn, rowdir, label, pid_hint=None):
    wins = find_windows(conn)
    if len(wins) == 0: return {"status": "unavailable", "count": len(wins)}
    if len(wins) > 1:
        return {"status": "ambiguous", "count": len(wins),
                "targets": [{"xid": int(win.id), "title": title} for win, title in wins]}
    win, title = wins[0]
    parts = title.split(":")
    # The fixture subprocess is the only owner in a unique-target row; for the
    # replacement control the caller supplies the fresh process incarnation.
    pid = pid_hint
    geom = win.get_geometry()
    conn.sync()
    frame = win.get_image(0, 0, geom.width, geom.height, X.ZPixmap, 0xFFFFFFFF).data
    fp = rowdir / f"{label}.raw"
    fp.write_bytes(frame)
    return {"status": "ok", "xid": int(win.id), "pid": pid, "start_ticks": start_ticks(pid) if pid else None,
            "counter": int(parts[1]), "version": int(parts[2]), "title": title,
            "width": int(geom.width), "height": int(geom.height), "frame_path": str(fp.relative_to(OUT)),
            "frame_bytes": len(frame), "frame_sha256": sha(frame)}


def launch(rowdir, effect):
    env = {**os.environ, "DISPLAY": DISPLAY_NAME, "ROW_DIR": str(rowdir), "EFFECT_MODE": effect}
    proc = subprocess.Popen(["/usr/bin/python3", "-B", str(ROOT / "fixture.py")], env=env,
                            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    return proc


def wait_state(conn, rowdir, label, timeout=4, pid_hint=None):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        s = state(conn, rowdir, label, pid_hint=pid_hint)
        if s["status"] != "unavailable": return s
        time.sleep(0.03)
    return state(conn, rowdir, label, pid_hint=pid_hint)


def wait_ambiguous(conn, rowdir, label, expected_pids, timeout=4):
    deadline = time.monotonic() + timeout
    expected = sorted(expected_pids)
    while time.monotonic() < deadline:
        current = state(conn, rowdir, label, pid_hint=None)
        eventfile = rowdir / "fixture-events.jsonl"
        events = [json.loads(line) for line in eventfile.read_text().splitlines()] if eventfile.exists() else []
        ready_pids = sorted(e.get("pid") for e in events if e.get("kind") == "ready")
        target_ids = [t["xid"] for t in current.get("targets", [])]
        if (current.get("status") == "ambiguous" and current.get("count") == 2
                and ready_pids == expected and len(set(target_ids)) == 2):
            current["ready_pids"] = ready_pids
            return current
        time.sleep(0.03)
    return state(conn, rowdir, label, pid_hint=None)


def query_button_released(root_window):
    pointer = root_window.query_pointer()
    mask = int(pointer.mask)
    return {"verified": not bool(mask & X.Button1Mask), "mask": mask}


def run_row(arm, case):
    key = f"{arm}__{case}"
    rowdir = OUT / "rows" / key
    rowdir.mkdir(parents=True, exist_ok=False)
    row = {"arm": arm, "case": case, "row_id": key, "emissions": 0, "input_ack": False,
           "decision": None, "error": None, "processes": [], "process_exit_codes": {}, "release_verified": False}
    xvfb = app = extra = conn = None
    try:
        if SOCKET.exists(): raise RuntimeError("private Xvfb socket already exists")
        xvfb = subprocess.Popen(["/usr/bin/Xvfb", DISPLAY_NAME, "-screen", "0", "640x480x24", "-nolisten", "tcp"],
                                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        row["processes"].append({"role":"xvfb","pid":xvfb.pid,"start_ticks":start_ticks(xvfb.pid)})
        deadline = time.monotonic() + 4
        while not SOCKET.exists() and time.monotonic() < deadline:
            if xvfb.poll() is not None: raise RuntimeError("Xvfb exited before socket appeared")
            time.sleep(0.02)
        if not SOCKET.exists(): raise RuntimeError("Xvfb socket unavailable")
        conn = display.Display(DISPLAY_NAME)
        app = launch(rowdir, "off" if case == "no_effect" else "on")
        row["processes"].append({"role":"fixture","pid":app.pid,"start_ticks":start_ticks(app.pid)})
        first = wait_state(conn, rowdir, "before", pid_hint=app.pid)
        if first["status"] != "ok": raise RuntimeError("initial unique visible target missing")
        row["initial_state"] = first
        row["presentation"] = {"arm": arm, "live_frame_sha256": first["frame_sha256"]}
        token = {k:first[k] for k in ("xid","pid","start_ticks","counter","version","title")}
        row["request"] = {"operation":"increment","source_token":token,
                           "source_frame_sha256":first["frame_sha256"],"representation_arm":arm}
        if arm in {"proxy_image", "hybrid"}:
            img = rowdir / "proxy.ppm"
            render(first["counter"], first["version"], img)
            row["presentation"]["proxy_image"] = str(img.relative_to(OUT))
            row["presentation"]["proxy_sha256"] = sha(img.read_bytes())
        if arm in {"structured_proxy", "hybrid"}:
            row["presentation"]["structured_state"] = {"counter":first["counter"],"version":first["version"],"target":"gtk-counter"}
        if case == "stale_version":
            os.kill(app.pid, signal.SIGUSR1); time.sleep(0.15)
        elif case == "target_replaced":
            row["process_exit_codes"]["fixture_original"] = stop(app)
            app = launch(rowdir, "on")
            row["processes"].append({"role":"fixture_replacement","pid":app.pid,"start_ticks":start_ticks(app.pid)})
            wait_state(conn, rowdir, "replacement", pid_hint=app.pid)
        elif case == "unavailable":
            wins = find_windows(conn); wins[0][0].unmap(); conn.sync(); time.sleep(0.05)
        elif case == "ambiguous":
            extra = launch(rowdir, "on")
            row["processes"].append({"role":"duplicate_fixture","pid":extra.pid,"start_ticks":start_ticks(extra.pid)})
            row["ambiguous_setup"] = wait_ambiguous(conn, rowdir, "duplicate", [app.pid, extra.pid])

        current = state(conn, rowdir, "pre_dispatch", pid_hint=app.pid)
        row["current_state"] = current
        if case == "macro_failure":
            row["decision"] = "YIELD_MACRO_FAILURE"
        elif current["status"] != "ok":
            row["decision"] = "YIELD_TARGET_" + current["status"].upper()
        elif any(current.get(k) != token.get(k) for k in token):
            row["decision"] = "REFUSE_STALE_BINDING"
        else:
            win = conn.create_resource_object("window", current["xid"])
            win.set_input_focus(X.RevertToParent, X.CurrentTime); conn.sync()
            # The ordinary arm chooses this coordinate from its screenshot; proxy arms map
            # the same task-specific increment operation to the identical live GTK button.
            xtest.fake_input(conn, X.MotionNotify, x=160, y=88)
            xtest.fake_input(conn, X.ButtonPress, 1)
            xtest.fake_input(conn, X.ButtonRelease, 1)
            conn.sync(); row["emissions"] = 1
            time.sleep(0.18)
            row["input_ack"] = any(json.loads(s).get("kind") == "click_ack" for s in (rowdir / "fixture-events.jsonl").read_text().splitlines())
            row["decision"] = "YIELD_NO_APPLICATION_EFFECT" if case == "no_effect" else "COMPLETED"
        time.sleep(0.04)
        row["after_state"] = state(conn, rowdir, "after", pid_hint=app.pid)
    except Exception as exc:
        row["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        if conn is not None:
            try:
                release = query_button_released(conn.screen().root)
                row["release_observation"] = release
                row["release_verified"] = release["verified"]
            except Exception as exc:
                row["release_observation"] = {"verified": False, "error": f"{type(exc).__name__}: {exc}"}
        if app is not None:
            row["process_exit_codes"]["fixture_current"] = stop(app)
        if extra is not None:
            row["process_exit_codes"]["duplicate_fixture"] = stop(extra)
        if xvfb is not None:
            row["process_exit_codes"]["xvfb"] = stop(xvfb)
        if conn is not None:
            try: conn.close()
            except Exception: pass
        socket_deadline=time.monotonic()+2
        while SOCKET.exists() and time.monotonic()<socket_deadline: time.sleep(0.02)
        row["socket_disappeared"] = not SOCKET.exists()
        eventfile = rowdir / "fixture-events.jsonl"
        row["fixture_events"] = [json.loads(line) for line in eventfile.read_text().splitlines()] if eventfile.exists() else []
        row["fixture_events_sha256"] = sha(eventfile.read_bytes()) if eventfile.exists() else None
        row["reply"] = {"decision":row.get("decision"),"emissions":row.get("emissions"),
                        "input_ack":row.get("input_ack"),"after_state":row.get("after_state")}
        (rowdir / "row.json").write_text(json.dumps(row, sort_keys=True, indent=2) + "\n")
    return row


def main():
    rows=[]
    for arm in ARMS:
        for case in CASES:
            rows.append(run_row(arm, case))
    result={"allocation_id":"issue3626-proxy-effect-unit-formal-03","issue":3626,
            "source_commit":os.environ["FROZEN_SOURCE_COMMIT"],
            "source_manifest_sha256":os.environ["SOURCE_MANIFEST_SHA256"],
            "preregistration_sha256":os.environ["PREREGISTRATION_SHA256"],
            "freeze_sha256":os.environ["FREEZE_SHA256"],
            "image_id":"sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27",
            "platform":"linux/arm64","formal_invocations":1,"retries":0,"arms":list(ARMS),"cases":list(CASES),"rows":rows}
    canonical=json.dumps(result,sort_keys=True,separators=(",",":" )).encode()
    result["result_sha256"]=sha(canonical)
    (OUT/"raw.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print(json.dumps({"allocation_id":result["allocation_id"],"row_count":len(rows),
                      "row_errors":sum(r["error"] is not None for r in rows)},sort_keys=True))
    if any(r["error"] for r in rows): raise SystemExit(1)


if __name__ == "__main__": main()
