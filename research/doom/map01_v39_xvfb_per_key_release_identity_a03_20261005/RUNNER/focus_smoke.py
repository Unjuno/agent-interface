"""One-shot pre-candidate check of Python-Xlib focus-call argument order."""
import json
import os
import subprocess
import time

from Xlib import X, display

proc = subprocess.Popen(
    ["Xvfb", ":118", "-screen", "0", "320x240x24", "-nolisten", "tcp", "-noreset", "-ac"],
    env={**os.environ, "DISPLAY": ":118"}, stdin=subprocess.DEVNULL,
    stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
)
observer = None
window = None
result = {"status": "STOP", "display": ":118"}
try:
    deadline = time.monotonic() + 5
    last_error = None
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            last_error = proc.stderr.read().decode("utf-8", "replace")
            raise RuntimeError("focus-smoke Xvfb exited: " + last_error)
        try:
            observer = display.Display(":118")
            break
        except Exception as exc:
            last_error = repr(exc)
            time.sleep(.05)
    if observer is None:
        raise TimeoutError("focus-smoke display unavailable: " + str(last_error))
    screen = observer.screen()
    window = screen.root.create_window(
        10, 10, 100, 80, 0, screen.root_depth, X.InputOutput,
        X.CopyFromParent, event_mask=X.KeyPressMask | X.KeyReleaseMask,
    )
    window.map()
    observer.sync()
    observer.set_input_focus(window, X.RevertToParent, X.CurrentTime)
    observer.sync()
    focus = observer.get_input_focus().focus
    result.update({"window": int(window.id), "focus": int(focus.id),
                   "focus_matches": focus.id == window.id, "status": "PASS"})
    if not result["focus_matches"]:
        result["status"] = "FAIL"
finally:
    if observer is not None:
        observer.close()
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5)
    result["xvfb_exit"] = proc.returncode
    result["xvfb_stopped"] = proc.poll() is not None
    if not result["xvfb_stopped"]:
        result["status"] = "FAIL"
print(json.dumps(result, sort_keys=True))
raise SystemExit(0 if result.get("status") == "PASS" and result.get("xvfb_stopped") else 1)
