"""Excluded construction-only GTK/X11 startup and teardown check; sends no input."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time

from Xlib import display

DISPLAY = ":154"
env = {"PATH": "/usr/bin:/bin", "HOME": "/tmp", "LANG": "C.UTF-8", "DISPLAY": DISPLAY,
       "PYTHONPATH": "/repo"}
with tempfile.TemporaryDirectory(prefix="issue3166-construction-") as tmp:
    root = Path(tmp)
    xvfb = subprocess.Popen(["Xvfb", DISPLAY, "-screen", "0", "800x600x24", "-nolisten", "tcp", "-ac"],
                            env={"PATH": "/usr/bin:/bin", "HOME": "/tmp"},
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    app = None
    try:
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            try:
                dpy = display.Display(DISPLAY)
                dpy.close()
                break
            except Exception:
                time.sleep(0.05)
        else:
            raise SystemExit("CONSTRUCTION_STOP_XVFB_NOT_READY")
        meta = root / "meta.json"
        app = subprocess.Popen(["/usr/bin/python3", "/repo/research/integration/golden_v3_second_domain_2246_v1/gtk_fixture_app.py",
                               "--mode", "useful", "--meta", str(meta), "--effect", str(root / "effect.json")],
                              env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline and app.poll() is None and not meta.exists():
            time.sleep(0.02)
        if not meta.exists() or app.poll() is not None:
            raise SystemExit(f"CONSTRUCTION_STOP_FIXTURE_START_{app.poll()}")
        window_id = int(json.loads(meta.read_text())["window_id"])
        dpy = display.Display(DISPLAY)
        dpy.create_resource_object("window", window_id).destroy()
        dpy.sync()
        dpy.close()
        app.wait(timeout=3)
        if app.returncode != 0:
            raise SystemExit(f"CONSTRUCTION_STOP_FIXTURE_CLEANUP_{app.returncode}")
        print(json.dumps({"result": "CONSTRUCTION_GTK_X11_STARTUP_TEARDOWN_PASS",
                          "window_id_observed": True, "input_emissions": 0,
                          "effect_file_created": (root / "effect.json").exists()}))
    finally:
        if app is not None and app.poll() is None:
            app.terminate()
            app.wait(timeout=2)
        if xvfb.poll() is None:
            xvfb.terminate()
            xvfb.wait(timeout=2)
