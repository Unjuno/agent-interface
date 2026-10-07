"""One construction: eight fresh no-input apps on owned private Xvfb."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def main(output):
    out = Path(output)
    if out.exists() and any(out.iterdir()):
        raise FileExistsError("occupied construction output")
    out.mkdir(parents=True, exist_ok=True)
    if os.environ.get("DISPLAY") != ":97":
        raise RuntimeError("wrong private display")
    xvfb_log = (out / "xvfb.log").open("wb")
    wm_log = (out / "openbox.log").open("wb")
    xvfb = wm = None
    rows = []
    try:
        xvfb = subprocess.Popen(["Xvfb", ":97", "-screen", "0", "1024x768x24",
            "-nolisten", "tcp", "-ac"], stdout=xvfb_log, stderr=subprocess.STDOUT)
        time.sleep(0.4)
        if xvfb.poll() is not None:
            raise RuntimeError("Xvfb exited")
        wm = subprocess.Popen(["openbox", "--sm-disable"], stdout=wm_log, stderr=subprocess.STDOUT)
        time.sleep(0.4)
        if wm.poll() is not None:
            raise RuntimeError("Openbox exited")
        keymap = subprocess.run(["setxkbmap", "-layout", "us"], capture_output=True)
        if keymap.returncode:
            raise RuntimeError("keymap setup failed")
        for replicate in range(4):
            modes = ("LEGACY", "FIXED") if replicate % 2 == 0 else ("FIXED", "LEGACY")
            for mode in modes:
                index = len(rows)
                rowdir = out / f"row-{index:02d}"
                rowdir.mkdir()
                proc = subprocess.Popen([sys.executable, "-B", "/experiment/probe_app.py",
                    mode, str(rowdir)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                first_observer_read = None
                deadline = time.monotonic() + 10
                timed_out = False
                while proc.poll() is None:
                    ready = rowdir / "ready.json"
                    if ready.is_file() and first_observer_read is None:
                        first_observer_read = json.loads(ready.read_bytes())
                    if time.monotonic() >= deadline:
                        timed_out = True
                        proc.kill()  # Only this probe's own disposable child.
                        break
                    time.sleep(0.005)
                stdout, stderr = proc.communicate()
                (rowdir / "stdout.bin").write_bytes(stdout)
                (rowdir / "stderr.bin").write_bytes(stderr)
                if timed_out or proc.returncode:
                    (rowdir / "stop.json").write_text(json.dumps({
                        "status": "STOP_CHILD_TIMEOUT_OR_EXIT", "timed_out": timed_out,
                        "pid": proc.pid, "exit": proc.returncode,
                        "first_observer_read": first_observer_read}) + "\n", encoding="utf-8")
                    raise RuntimeError("probe child failed; first streams retained")
                app = json.loads(stdout)
                rows.append({"index": index, "mode": mode, "replicate": replicate,
                    "pid": proc.pid, "exit": proc.returncode,
                    "stdout": stdout.decode(), "stderr": stderr.decode(),
                    "first_observer_read": first_observer_read,
                    "final_ready_file": json.loads((rowdir / "ready.json").read_bytes()),
                    "app": app})
    finally:
        for proc in (wm, xvfb):
            if proc is not None and proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()
        wm_log.close()
        xvfb_log.close()
    raw = {"schema": "5260-a03-epoch-construction01-v1",
        "allocation": "5260-a03-wslc-no-input-construction01-20261003",
        "status": "CONSTRUCTION_ONLY_NO_INPUT", "rows": rows,
        "image_id": os.environ.get("EXPERIMENT_IMAGE_ID"),
        "python": sys.version, "tk": __import__("tkinter").TkVersion,
        "xvfb_exit": xvfb.returncode, "openbox_exit": wm.returncode,
        "source_sha256": {name: hashlib.sha256((Path("/experiment") / name).read_bytes()).hexdigest()
            for name in ("readiness_once.py", "probe_app.py", "probe_epoch.py")}}
    (out / "raw.json").write_text(json.dumps(raw, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"rows": len(rows), "input_events": sum(r["app"]["input_events"] for r in rows)}))


if __name__ == "__main__":
    main(sys.argv[1])
