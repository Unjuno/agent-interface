"""Execute one frozen private-Xvfb first-character GUI allocation."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from schedule import schedule


def file_sha(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(131072), b""):
            digest.update(block)
    return digest.hexdigest()


def worker_code(duration):
    return ("import json,time; start=time.monotonic_ns(); "
            f"deadline=time.monotonic()+{duration!r}; x=1\n"
            "while time.monotonic()<deadline: x=(x*1664525+1013904223)&0xffffffff\n"
            "print(json.dumps({'start_ns':start,'end_ns':time.monotonic_ns()}),flush=True)")


def write_json(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as stream:
        stream.write(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def wait_for(path, proc, timeout, label):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        if proc.poll() is not None:
            raise RuntimeError(f"app exited before {label}: {proc.returncode}")
        time.sleep(0.005)
    raise TimeoutError(f"timeout waiting for {label}")


def click_and_type(ready, row, fixture, out_dir):
    from Xlib import X, display
    from Xlib.ext import xtest
    g = ready["geometry"]
    if row["coordinate_method"] == "CHILD_ROOT_COORD":
        x = g["target_root_x"] + g["target_width"] // 2
        y = g["target_root_y"] + g["target_height"] // 2
        addressed_id = g["target_id"]
    else:
        x = g["root_x"] + g["target_x"] + g["target_width"] // 2
        y = g["root_y"] + g["target_y"] + g["target_height"] // 2
        addressed_id = g["root_id"]
    start = time.monotonic_ns()
    xd = display.Display()
    xtest.fake_input(xd, X.MotionNotify, x=x, y=y)
    xtest.fake_input(xd, X.ButtonPress, detail=1, x=x, y=y)
    xtest.fake_input(xd, X.ButtonRelease, detail=1, x=x, y=y)
    xd.sync()
    click_sync = time.monotonic_ns()
    time.sleep(row["first_key_delay_ms"] / 1000)
    key_requests = []
    for index, char in enumerate(fixture["payload"]):
        if index:
            time.sleep(fixture["inter_key_gap_ms"] / 1000)
        request_start = time.monotonic_ns()
        keycode = xd.keysym_to_keycode(ord(char))
        xtest.fake_input(xd, X.KeyPress, detail=keycode)
        xtest.fake_input(xd, X.KeyRelease, detail=keycode)
        xd.sync()
        request_end = time.monotonic_ns()
        key_requests.append({"index": index, "char": char, "keycode": keycode,
                             "request_started_ns": request_start, "sync_returned_ns": request_end})
    last_key_sync = key_requests[-1]["sync_returned_ns"]
    time.sleep(fixture["save_delay_after_last_key_ms"] / 1000)
    save_x = g["save_root_x"] + g["save_width"] // 2
    save_y = g["save_root_y"] + g["save_height"] // 2
    save_start = time.monotonic_ns()
    xtest.fake_input(xd, X.MotionNotify, x=save_x, y=save_y)
    xtest.fake_input(xd, X.ButtonPress, detail=1, x=save_x, y=save_y)
    xtest.fake_input(xd, X.ButtonRelease, detail=1, x=save_x, y=save_y)
    xd.sync()
    save_sync = time.monotonic_ns()
    xd.close()
    return {"addressed_id": addressed_id, "x": x, "y": y, "click_started_ns": start,
            "click_sync_returned_ns": click_sync, "first_key_delay_ms": row["first_key_delay_ms"],
            "key_requests": key_requests, "last_key_sync_returned_ns": last_key_sync,
            "save_x": save_x, "save_y": save_y, "save_started_ns": save_start,
            "save_sync_returned_ns": save_sync}


def run(fixture_path, out_path):
    fixture = json.loads(Path(fixture_path).read_text(encoding="utf-8"))
    out = Path(out_path)
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"formal output is not empty: {out}")
    out.mkdir(parents=True, exist_ok=True)
    display_name = fixture["private_display"]
    if os.environ.get("DISPLAY") != display_name:
        raise RuntimeError("DISPLAY is not the frozen private Xvfb")
    xvfb_log = (out / "xvfb.log").open("wb")
    wm_log = (out / "openbox.log").open("wb")
    xvfb = wm = None
    rows = []
    try:
        xvfb = subprocess.Popen(["Xvfb", display_name, "-screen", "0", fixture["screen"], "-nolisten", "tcp", "-ac"],
                                stdout=xvfb_log, stderr=subprocess.STDOUT)
        time.sleep(0.4)
        if xvfb.poll() is not None:
            raise RuntimeError(f"Xvfb startup exit {xvfb.returncode}")
        wm = subprocess.Popen(["openbox", "--sm-disable"], stdout=wm_log, stderr=subprocess.STDOUT)
        time.sleep(0.4)
        if wm.poll() is not None:
            raise RuntimeError(f"Openbox startup exit {wm.returncode}")
        keymap_set = subprocess.run(["setxkbmap", "-layout", "us"], capture_output=True, text=True)
        keymap_query = subprocess.run(["setxkbmap", "-query"], capture_output=True, text=True)
        if keymap_set.returncode or keymap_query.returncode or "us" not in keymap_query.stdout:
            raise RuntimeError("US keymap setup/query failed")

        for index, plan in enumerate(schedule(fixture)):
            row_dir = out / f"row-{index:03d}"
            row_dir.mkdir()
            worker = None
            worker_record = {"pid": None, "exit": None}
            if plan["load"] == "cpu_busy":
                duration = fixture["busy_worker_duration_ms"] / 1000
                worker = subprocess.Popen([sys.executable, "-c", worker_code(duration)],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                worker_record["pid"] = worker.pid
            app = subprocess.Popen([sys.executable, "/experiment/app.py", str(row_dir)],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            app_start = time.monotonic_ns()
            try:
                ready = wait_for(row_dir / "ready.json", app, 5, "map/configure barrier")
                injection = click_and_type(ready, plan, fixture, row_dir)
                app_stdout, app_stderr = app.communicate(timeout=8)
                app_exit = app.returncode
            except Exception as exc:
                app.kill()
                app_stdout, app_stderr = app.communicate()
                app_exit = app.returncode
                rows.append({"index": index, **plan, "app_pid": app.pid, "app_exit": app_exit,
                    "app_stdout": app_stdout, "app_stderr": app_stderr,
                    "runner_error": type(exc).__name__ + ": " + str(exc)})
                if worker is not None:
                    worker_record["exit"] = worker.wait(timeout=3)
                break
            app_end = time.monotonic_ns()
            if worker is not None:
                worker_record["exit"] = worker.wait(timeout=3)
                worker_stderr = worker.stderr.read().decode("utf-8", "replace")
                worker_record.update(json.loads(worker.stdout.read().decode("utf-8")))
            else:
                worker_stderr = ""
            try:
                app_record = json.loads(app_stdout.strip().splitlines()[-1])
                parse_error = None
            except Exception as exc:
                app_record = None
                parse_error = type(exc).__name__ + ": " + str(exc)
            rows.append({"index": index, **plan, "app_pid": app.pid, "app_exit": app_exit,
                "app_stdout": app_stdout, "app_stderr": app_stderr,
                "app_start_ns": app_start, "app_end_ns": app_end,
                "app_parse_error": parse_error, "app": app_record,
                "ready": ready, "injection": injection,
                "worker": worker_record, "worker_stderr": worker_stderr})
    finally:
        for proc, log in ((wm, wm_log), (xvfb, xvfb_log)):
            if proc is not None and proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()
            log.close()
    raw = {"schema": fixture["schema"], "allocation": fixture["allocation"],
           "fixture": fixture, "schedule": schedule(fixture),
           "environment": {"display": display_name, "screen": fixture["screen"],
             "python": sys.version, "tk": __import__("tkinter").TkVersion,
             "packages": subprocess.run(["dpkg-query", "-W", "python3", "python3-tk",
                 "python3-xlib", "xvfb", "openbox", "x11-apps"], capture_output=True, text=True).stdout,
             "keymap_set": {"exit": keymap_set.returncode, "stdout": keymap_set.stdout, "stderr": keymap_set.stderr},
             "keymap_query": {"exit": keymap_query.returncode, "stdout": keymap_query.stdout, "stderr": keymap_query.stderr},
             "image_id": os.environ.get("EXPERIMENT_IMAGE_ID"), "container_id": os.environ.get("HOSTNAME"),
             "xvfb_exit": xvfb.returncode if xvfb else None, "openbox_exit": wm.returncode if wm else None},
           "source_sha256": {name: file_sha(Path("/experiment") / name) for name in
               ("candidate.py", "app.py", "schedule.py", "fixture.json", "audit.py")},
           "freeze_sha256": file_sha("/experiment/FREEZE.json"),
           "fixture_sha256": file_sha(fixture_path),
           "rows": rows, "row_count": len(rows), "rows_completed": sum(1 for r in rows if r.get("app") is not None)}
    write_json(out / "candidate_stdout.json", raw)
    (out / "candidate_exit.txt").write_text("0\n" if len(rows) == len(raw["schedule"]) and raw["rows_completed"] == len(rows) else "1\n", encoding="utf-8")
    return 0 if (out / "candidate_exit.txt").read_text().strip() == "0" else 1


if __name__ == "__main__":
    raise SystemExit(run(sys.argv[1], sys.argv[2]))
